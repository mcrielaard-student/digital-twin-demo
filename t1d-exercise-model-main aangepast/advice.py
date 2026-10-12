# Simple running advice based on the glucose predictions from fullday_simulations.py

from fullday_simulations import simulate_all, plot_scenarios, pa_start

HYPO = 3.9 * 18.0182                   # <3.9: hypo
RISK_HYPO_MAX = 6.0 * 18.0182          # 3.9-6: increased hypo risk
OK_MAX = 12.0 * 18.0182                # 6-12: ok to exercise
MODERATE_MAX = 15.0 * 18.0182          # 12-15: moderate intensity only; >15: postpone
POST_WINDOW = 60                       # minutes after the run we keep monitoring glucose


def start_advice(g):                            # g = glucosewaarde
    """Advice before the run, based on start glucose [mg/dl]."""
    if g < HYPO:
        return 'Hypo: postpone exercise and treat the hypo.'
    if g < RISK_HYPO_MAX:
        return 'Increased hypo risk: consider extra carbohydrates and keep monitoring glucose.'
    if g < OK_MAX:
        return 'Exercise is possible.'
    if g <= MODERATE_MAX:
        return 'Elevated glucose: moderate intensity only.'
    return 'Hyperglycaemia: postpone exercise and treat the hyper.'


def run_advice(G, dur):                                      # G = glucosecurve of the whole day; dur = duration of the run
    """Warnings during and shortly after the run."""
    window = G[pa_start:pa_start + dur + POST_WINDOW]           
    g_min, g_max = window.min(), window.max()                # Takes max and min from the window^

    if g_min < HYPO:
        return f'Hypo predicted (min {g_min / 18.0182:.1f} mmol/L): eat carbohydrates before the run and keep monitoring glucose.'   # in one decimal (:.1f)
    if g_min < RISK_HYPO_MAX:
        return f'Increased hypo risk (min {g_min / 18.0182:.1f} mmol/L): carry fast carbohydrates on your run.'
    if g_max > MODERATE_MAX:
        return f'Glucose rises to {g_max / 18.0182:.1f} mmol/L: monitor.'
    return 'No problems predicted.'


if __name__ == '__main__':          # This block runs only if you start this file directly, not if another file imports it.
    results = simulate_all()

    first = next(iter(results.values()))['rest']
    print(f'Start glucose: {first[pa_start] / 18.0182:.1f} mmol/L')
    print(f'Advice: {start_advice(first[pa_start])}')

    for dur, curves in results.items():
        for label, G in curves.items():
            print(f'{dur} min, {label}: {run_advice(G, dur)}')

    plot_scenarios(results)