"""
Personalize the Deichmann T1D exercise model with lmfit, following the protocol of the paper:

    Day 1:  fit p1, p3, Gb and the meal parameters f and tau_m.
    Day 2:  keep p1 and p3 from day 1; re-estimate Gb and the meal parameters for that day.

Input:   
Per day and patient, three CSV files are expected in data_patients:
    data_patient<N>_day<M>.csv   columns: time [min], Glc [mg/dl]
    input_patient<N>_day<M>.csv  columns: time, u [muU/min], ub [muU/min], AC [counts/min], PA, meal [mg/min]
    info_patient<N>_day<M>.csv   columns: w [kg], Gb [mg/dl], Ib [muU/ml], G0 [mg/dl]

Usage:
    python fit_patient.py                  # one shared f and tau_m per day; p1 and p3 fixed on day 2
    python fit_patient.py --per-meal       # f and tau_m estimated for every meal
    python fit_patient.py --free-day2      # additionally fit day 2 with p1 and p3 free (best-case reference)

Output:
For now an output file in the same format as params_standard.csv is outputted with only p1 and p3 changed (day 1 fit):
    fitted_params_patient<N>.csv    columns: Parameter name, Parameter value
"""

import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from lmfit import Parameters, minimize, fit_report

import functions.PAmodel as GIM

# Settings
PATIENT = 1                                         # patient 1-5
FIT_DAY, VALIDATION_DAY = 1,2                       # study day 1-2
OUTPUT_FILE = 'fitted_params_patient'+ str(PATIENT) +'.csv'

# Time windows [min] that are left out of the fit (e.g. unexplained glucose excursions), per day.
EXCLUDE = {}

STD_GB = 120.0                                      # basal glucose of the standard model [mg/dl]
STD_MEAL = {'f': 1.0, 'tau_m': 40.0}                # default meal parameters of the original model

# lmfit bounds: (min, max) for each fitted parameter
BOUNDS = {
    'Gb': (20, 250),                                # basal glucose [mg/dl]
    'f': (0.1, 3.0),                                # CHO fraction absorbed [-] (scaling factor)
    'tau_m': (10, 150),                             # time of maximum glucose appearance [min]
}
REL_BOUNDS_P = (0.1, 10.0)                          # p1, p3 allowed between 0.1x and 10x their standard/previous value
MAX_NFEV = 40                                       # max. number of iterations per fit (is only used in case of per-meal fits)

# Data handling
def load_params(path):
    # Standard function for reading the csv files
    return pd.read_csv(path, header=None, dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()

def Ib_from_ub(ub, weight, params_ins):
    # Basal plasma insulin Ib [muU/ml] from basal infusion rate ub [muU/min] (inverse of compute_ub).
    k2, k3, k4, Vi = (params_ins[k] for k in ('k2', 'k3', 'k4', 'Vi'))
    return ub * k2 / ((k2 + k3) * k4 * Vi * weight)

def load_day(patient, day, params_ins):
    # Load glucose data, model inputs and patient info of a single day into a dictionary
    data = pd.read_csv('data_patients/data_patient' + str(patient) + '_day' + str(day) + '.csv')
    input = pd.read_csv('data_patients/input_patient' + str(patient) + '_day' + str(day) + '.csv')
    info = pd.read_csv('data_patients/info_patient' + str(patient) + '_day' + str(day) + '.csv').iloc[0]

    t_all = data['time'].round().astype(int).values
    assert t_all.max() < len(input), 'glucose data extends beyond the input vectors'

    mask = np.ones(len(t_all), dtype=bool)          # Data points used for fitting
    for start, end in EXCLUDE.get(day, []):
        mask &= ~((t_all >= start) & (t_all < end)) # Exclusion of outliers

    weight = float(info['w'])
    Ib_check = Ib_from_ub(input['ub'].values[0], weight, params_ins)
    if abs(Ib_check - info['Ib']) > 0.01 * info['Ib']:
        print(f"WARNING day {day}: Ib in info file ({info['Ib']:.2f}) differs from Ib computed from ub ({Ib_check:.2f})")

    return {
        'day': day, 'data': data, 't_all': t_all, 'mask': mask,
        't_idx': t_all[mask], 'G_obs': data['Glc'].values[mask],
        'AC': input['AC'].values, 'PA': input['PA'].values,
        'meal': input['meal'].values, 'u': input['u'].values,
        'ub': input['ub'].values, 'weight': weight,
        'Ib': float(info['Ib']), 'G0': float(info['G0']),
        'n_meals': int(np.count_nonzero(input['meal'].values)),
    }

# Model wrapper
def meal_names(n_meals, per_meal):
    # Names of the meal parameters
    # Depends on parameters per day ('f', 'tau_m') or parameters per meal ('f_1', ..., 'tau_m_1', ...).
    if per_meal:
        return [f'f_{i + 1}' for i in range(n_meals)], [f'tau_m_{i + 1}' for i in range(n_meals)]
    return ['f'], ['tau_m']

def simulate(values, day, params_std, per_meal):
    # Run the model on one day
    # `values`: lmfit Parameters or dictionary with p1, p3, Gb, f and tau_m
    v = values.valuesdict() if hasattr(values, 'valuesdict') else values
    params = dict(params_std)
    params['p1'] = v['p1']
    params['p3'] = v['p3']
    f_names, tau_names = meal_names(day['n_meals'], per_meal)
    params_meal = {'f': [v[k] for k in f_names], 'tau_m': [v[k] for k in tau_names]}
    return GIM.compute_glucose_replay(
        params, [v['Gb'], day['Ib']], day['weight'], day['AC'], day['meal'], day['u'], day['ub'], G0=day['G0'],
        params_meal=params_meal)

def standard_values(params_std, day, per_meal):
    f_names, tau_names = meal_names(day['n_meals'], per_meal)
    v = {'p1': params_std['p1'], 'p3': params_std['p3'], 'Gb': STD_GB}
    v.update({k: STD_MEAL['f'] for k in f_names})
    v.update({k: STD_MEAL['tau_m'] for k in tau_names})
    return v

# Fitting
def make_parameters(params_std, day, per_meal, fixed_p=None):
    # Build the lmfit Parameters. Bounds are set with add(name, value=..., min=..., max=...)
    # fixed_p: dictionary with p1 and p3, which are kept constant after day 1 if vary=False 
    pars = Parameters()
    for name in ['p1', 'p3']:
        if fixed_p is None:
            pars.add(name, value=params_std[name], min=REL_BOUNDS_P[0] * params_std[name],
                     max=REL_BOUNDS_P[1] * params_std[name])
        else:
            pars.add(name, value=fixed_p[name], vary=False)

    pars.add('Gb', value=STD_GB, min=BOUNDS['Gb'][0], max=BOUNDS['Gb'][1])

    f_names, tau_names = meal_names(day['n_meals'], per_meal)
    for k in f_names:
        pars.add(k, value=STD_MEAL['f'], min=BOUNDS['f'][0], max=BOUNDS['f'][1])
    for k in tau_names:
        pars.add(k, value=STD_MEAL['tau_m'], min=BOUNDS['tau_m'][0], max=BOUNDS['tau_m'][1])
    return pars

def residual(pars, day, params_std, per_meal):
    G_model = simulate(pars, day, params_std, per_meal)['G'].values[day['t_idx']]
    res = G_model - day['G_obs']
    if not np.all(np.isfinite(res)):                # keep the optimizer alive if the ODE solver fails
        res = np.full_like(res, 1e6)
    return res

def fit_day(day, params_std, per_meal, fixed_p=None):
    # diff_step: ODE solver noise makes very small finite-difference steps unreliable
    # x_scale='jac': parameters differ by orders of magnitude (p3 ~ 1e-5, Gb ~ 100)
    pars = make_parameters(params_std, day, per_meal, fixed_p)
    return minimize(residual, pars, args=(day, params_std, per_meal),
                    method='least_squares', diff_step=1e-3, x_scale='jac', max_nfev=MAX_NFEV)

def rmse(values, day, params_std, per_meal):
    # Root means square error over the data points used for fitting
    G = simulate(values, day, params_std, per_meal)['G'].values
    return G, np.sqrt(np.mean((G[day['t_idx']] - day['G_obs']) ** 2))

def warn_bounds(result, label):
    for name, p in result.params.items():
        if p.vary and (p.value <= p.min + 1e-3 * abs(p.min) or p.value >= p.max - 1e-3 * abs(p.max)):
            print(f'WARNING ({label}): {name} = {p.value:.4g} is at a bound')

def result_rows(result, label):
    return [(label, n, p.value) for n, p in result.params.items()]

# Plotting
def exercise_periods(day):
    # Marks continuous exercise periods
    pa = (day['PA'] == 1).astype(int)
    edges = np.diff(np.r_[0, pa, 0])
    return list(zip(np.where(edges == 1)[0], np.where(edges == -1)[0]))

def plot_days(panels):
    # panels: list of (title, day, [(label, G, linestyle, color), ...])
    fig, axes = plt.subplots(len(panels), 1, figsize=(7.5, 3.2 * len(panels)), squeeze=False)
    for ax, (title, day, curves) in zip(axes[:, 0], panels):
        for label, G, ls, c in curves:
            ax.plot(np.arange(len(G)), G, ls=ls, color=c, label=label)
        d = day['data']
        ax.scatter(d['time'][day['mask']], d['Glc'][day['mask']], s=8, color='C3', label='data', zorder=5)
        if (~day['mask']).any():
            ax.scatter(d['time'][~day['mask']], d['Glc'][~day['mask']], s=8, color='lightgrey',
                       label='excluded', zorder=4)
        ax.vlines(np.where(day['meal'] != 0)[0], 0, 20, color='k', lw=1, label='meal')
        for i, (start, end) in enumerate(exercise_periods(day)):
            ax.axvspan(start, end, color='lightgreen', alpha=0.4, zorder=0,
                label='exercise' if i == 0 else None)
            ax.axvline(start, color='limegreen', lw=1)
            ax.axvline(end, color='limegreen', lw=1)
        ax.set_title(title, fontsize=9)
        ax.set_ylabel('glucose [mg/dl]')
        ax.legend(fontsize=7, ncol=2)
    axes[-1, 0].set_xlabel('time [min]')
    plt.tight_layout()
    plt.show()

# ___________________________________________________________________________________________________________________________________________
def main(per_meal=False, free_day2=False):
    params_std = load_params('parameters/params_standard.csv')  # Standard
    params_ins = load_params('parameters/params_insulin.csv')   # Insulin
    d1 = load_day(PATIENT, FIT_DAY, params_ins)
    d2 = load_day(PATIENT, VALIDATION_DAY, params_ins)
    print(f'Meals: day {FIT_DAY}: {d1["n_meals"]}, day {VALIDATION_DAY}: {d2["n_meals"]} '
          f'| per-meal fitting: {per_meal}')

    table = []

    # Reference: standard parameters, no fitting
    G1_std, e = rmse(standard_values(params_std, d1, per_meal), d1, params_std, per_meal)
    table.append((FIT_DAY, 'standard parameters, no fit', e))
    G2_std, e = rmse(standard_values(params_std, d2, per_meal), d2, params_std, per_meal)
    table.append((VALIDATION_DAY, 'standard parameters, no fit', e))

    # Day 1 fit for p1, p3, Gb, f and tau_m
    res1 = fit_day(d1, params_std, per_meal)
    print(f'\n--- Day {FIT_DAY}: p1, p3, Gb, f and tau_m ---')
    print(fit_report(res1))
    warn_bounds(res1, f'day {FIT_DAY}')
    G1_fit, e = rmse(res1.params.valuesdict(), d1, params_std, per_meal)
    table.append((FIT_DAY, 'fit (p1, p3, Gb, meal free)', e))
    p_personal = {'p1': res1.params['p1'].value, 'p3': res1.params['p3'].value}

    # Day 2 fit for Gb, f and tau_m; p1 and p3 from day 1 fit
    res2 = fit_day(d2, params_std, per_meal, fixed_p=p_personal)
    print(f'\n--- Day {VALIDATION_DAY}: p1, p3 from day {FIT_DAY} (fixed); Gb, f and tau_m parameters free ---')
    print(fit_report(res2))
    warn_bounds(res2, f'day {VALIDATION_DAY}')
    G2_pers, e = rmse(res2.params.valuesdict(), d2, params_std, per_meal)
    table.append((VALIDATION_DAY, f'p1, p3 from day {FIT_DAY}; Gb, meal refit', e))

    curves2 = [('standard, no fit', G2_std, '--', 'grey'),
               (f'p1,p3 from day {FIT_DAY}; Gb+meal refit', G2_pers, '-', 'C0')]

    # Optional: Day 2 fit for p1, p3, Gb, f and tau_m (p1 and p3 are not fixed)
    if free_day2:
        res2f = fit_day(d2, params_std, per_meal)
        print(f'\n--- Day {VALIDATION_DAY}: everything free (best case) ---')
        print(fit_report(res2f))
        G2_free, e = rmse(res2f.params.valuesdict(), d2, params_std, per_meal)
        table.append((VALIDATION_DAY, 'all free (p1 and p3 too)', e))
        curves2.append(('all free', G2_free, '-', 'C1'))

    summary = pd.DataFrame(table, columns=['day', 'setup', 'RMSE [mg/dl]'])
    summary['RMSE [mg/dl]'] = summary['RMSE [mg/dl]'].round(1)
    print('\n' + summary.to_string(index=False))

    params_standard = pd.read_csv('parameters/params_standard.csv',sep=";",header=None,names=["parameter", "value"],dtype={"parameter": str})
    # Replace the values of standard parameters with the personalized parameters (only p1 and p3 for now)
    for name, value in res2.params.valuesdict().items():
        mask = params_standard["parameter"] == name

        if not mask.any():
            print(f"Parameter '{name}' not found in params_standard.csv, skipping.")
        continue        # For now, parameters Gb, f and tau_m are not saved to this file due to their varying locations
        """
        Gb is saved in data_patients/info_patient<N>_day<M>.csv
        f and tau_m are saved in parameter/meal_params/meal_params_patient<N>_day<M>.csv
        The Digital Twin should not follow this structure of data saving
        """
        params_standard.loc[mask, "value"] = value

    # Save in the same format as params_standard.csv
    params_standard.to_csv(OUTPUT_FILE, sep=";", header=False, index=False)
    print(f'\nSaved all fitted parameters to {OUTPUT_FILE}')

    plot_days([(f'Day {FIT_DAY}', d1, [('standard, no fit', G1_std, '--', 'grey'),
                                       ('fit', G1_fit, '-', 'C0')]),
               (f'Day {VALIDATION_DAY}', d2, curves2)])

if __name__ == '__main__':
    # Function for optional additions to the current fitting model
    ap = argparse.ArgumentParser()
    ap.add_argument('--per-meal', action='store_true', help='estimate f and tau_m for every meal')
    ap.add_argument('--free-day2', action='store_true', help='also fit day 2 with p1 and p3 free')
    args = ap.parse_args()
    main(per_meal=args.per_meal, free_day2=args.free_day2)
