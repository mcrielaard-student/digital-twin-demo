# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs the exercise model for the study by Romeres et al (2021, 2018) used to adjust the model parameters to
# type 1 diabetes and generates the corresponding figure (Fig. S2) of the following manuscript:

# Title:   New model of glucose-insulin regulation characterizes effects of physical activity and facilitates
#          personalized treatment evaluation in children and adults with type 1 diabetes
# Authors: Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach*
# *Corresponding author:
#          michael.kaltenbach@bsse.ethz.ch

# Date:    March 17, 2022
# Author:  Julia Deichmann <julia.deichmann@bsse.ethz.ch>

import pandas as pd
import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
plt.style.use('seaborn-paper')
plt.rcParams.update({'font.size': 8})
plt.rcParams['errorbar.capsize'] = 3


''' select condition '''

# 0: V1 - euglycemia - low insulin
# 1: V2 - euglycemia - high insulin
# 2: V3 - hyperglycemia - low insulin

idx = 0


''' Import parameters and data '''

condition = ['V1', 'V2', 'V3']

params = (pd.read_csv('parameters/params_T1D-' + condition[idx] + '.csv', header=None,
                      dtype={0: str}, delimiter=';')[1]).to_list()
params = params[:14] + [params[21]] + [params[24]]

data = pd.read_csv('data/data_Romeres' + condition[idx] + '.csv')
input = pd.read_csv('data/input_Romeres' + condition[idx] + '.csv')
info = pd.read_csv('data/info_Romeres' + condition[idx] + '.csv')


''' Extract inputs '''

Gb, Ib = info[['Gb', 'Ib']].iloc[0]
w = info['w'].iloc[0]
pa = info[['PA_start', 'PA_end']].iloc[0].to_list()

t = input['time'].to_list()
AC = input['AC']
meal = input['meal']
G = input['Glc']
I = input['Ins']


''' Model '''

def PAmodel(y, t, params, Q1, AC, I):

    p1, p2, p3, p4, p5, Vg, tau_AC, b, tau_Z, alpha, q1, q2, q3, q4, aY, n1 = params

    X, Q2, Y, Z, GU, GP = y

    fY = (Y / aY) ** n1 / (1 + (Y / aY) ** n1)

    glc_dyn = [- p2 * X + p3 * I,
               p4 * Q1 - p5 * Q2,

               - 1 / tau_AC * Y + 1 / tau_AC * AC,
               b * fY * Y - (1 - fY) / tau_Z * Z,

               q1 * fY * Y - q2 * GU,
               q3 * fY * Y - q4 * GP
               ]

    return glc_dyn


''' Compute GU and GP rates '''

p1, p2, p3, p4, p5, Vg, tau_AC, b, tau_Z, alpha, q1, q2, q3, q4, aY, n1 = params

Q1 = G * Vg
Qb = Gb * Vg
Xb = p3 / p2 * Ib

y0 = [Xb, p4/p5 * Qb, 0, 0, 0, 0]
model = np.zeros((len(t), len(y0)))
model[0, :] = y0

for i in range(len(t)-1):
    sol = odeint(PAmodel, model[i, :], [0, 1], args=(params, Q1[i], AC[i], I[i]))
    model[i+1, :] = sol[1]

GU = (1 - alpha) * (p1 + (1 + model[:, 3]) * model[:, 0]) * Q1 + model[:, 4] * Q1
GU_rest = (1 - alpha) * (p1 + model[:, 0]) * Q1
GU_id = GU_rest + (1 - alpha) * model[:, 3] * model[:, 0] * Q1

GP = (p1 + p3/p2 * Ib) * Qb - alpha * (p1 + (1 + model[:, 3]) * model[:, 0]) * Q1 + model[:, 5] * Q1
GP_rest = (p1 + p3/p2 * Ib) * Qb - alpha * (p1 + model[:, 0]) * Q1
GP_id = GP_rest - alpha * model[:, 3] * model[:, 0] * Q1


''' Plot '''

colors = [plt.cm.PuBu(0.85), plt.cm.inferno(0.6)]

fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(2.7, 2.5))

ax1.scatter(data['time'], data['GU'], color=colors[1], zorder=10, s=7, label='data')
ax1.plot(t, GU, linewidth=1.5, label='PA', zorder=9, color=colors[0])
ax1.plot(t, GU_rest, linewidth=1, label='rest', color=colors[0], linestyle='--')
ax1.plot(t, GU_id, linewidth=.75, color='black')
ax1.fill_between(t, GU_rest, GU_id, alpha=0, hatch='//', zorder=8)
ax1.fill_between(t, GU_id, GU, alpha=0.3, color='grey', zorder=7)
ax1.vlines(pa, 0, 18.015, color='black', linewidth=.5)
ax1.set_xlim(-3, 302)
ax1.set_ylim(0, 18.015)
ax1.set_ylabel('GU \n[mg/kg/min]')
ax1.legend(loc=2, bbox_to_anchor=(-0.02, 1.07), framealpha=0)

ax2.scatter(data['time'], data['GP'], color=colors[1], zorder=10, s=7)
ax2.plot(t, GP, linewidth=1.5, zorder=9, color=colors[0])
ax2.plot(t, GP_rest, linewidth=1, color=colors[0], linestyle='--')
ax2.plot(t, GP_id, linewidth=.75, color='black')
ax2.fill_between(t, GP_rest, GP_id, alpha=0, hatch='//', label='id', zorder=8)
ax2.fill_between(t, GP_id, GP, alpha=0.3, color='grey', label='ii', zorder=7)
ax2.vlines(pa, 0, 5.86, color='black', linewidth=.5)
ax2.set_ylim(0, 5.86)
ax2.set_xlabel('time [min]')
ax2.set_ylabel('GP \n[mg/kg/min]')
ax2.legend(loc=2, bbox_to_anchor=(0.02, 1.04), framealpha=0)

plt.tight_layout()
plt.show()
