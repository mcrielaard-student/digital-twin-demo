# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs a replay simulation for patient #3 and generates the corresponding figure (Fig. 6a) of the
# following manuscript:
#
# Title:   New model of glucose-insulin regulation characterizes effects of physical activity and facilitates
#          personalized treatment evaluation in children and adults with type 1 diabetes
# Authors: Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach*
# *Corresponding author:
#          michael.kaltenbach@bsse.ethz.ch
#
# Date:    November 22, 2022
# Author:  Julia Deichmann <julia.deichmann@bsse.ethz.ch>

import functions.PAmodel as GIM
import functions.plot_fct as plot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


''' Parameters '''

params = pd.read_csv('parameters/params_patient3.csv', header=None,
                     dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()
meal_params = pd.read_csv('parameters/meal_params/meal_params_patient3_day1.csv', delimiter=',')
f = meal_params['f'].to_list()
tau_m = meal_params['tau_m'].to_list()


''' Import data '''

input = pd.read_csv('data_patients/input_patient3_day1.csv')
info = pd.read_csv('data_patients/info_patient3_day1.csv')


''' Extract input  '''

Gb, Ib = info[['Gb', 'Ib']].iloc[0]
G0 = info['G0'].iloc[0]
w = info['w'].iloc[0]

t = np.array(input['time'])

AC = np.array(input['AC'].to_list())

u = np.array(input['u'])
ub = np.array(input['ub'])

meal = np.array(input['meal'])


''' Compute glucose profile '''

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G = model['G']


''' Replay with altered insulin bolus for lunch '''

# time of insulin bolus
t_u = np.where(u != 0)[0]
t_replay = t_u[2]

# glucose outcome with reduced bolus size
u_red = np.copy(u)
u_red[t_replay] = 0.5 * u_red[t_replay]

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u=u_red, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_u_red = model['G']

# glucose outcome for increased bolus size
u_inc = np.copy(u)
u_inc[t_replay] = 1.5 * u_inc[t_replay]

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u=u_inc, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_u_inc = model['G']


''' Replay with altered CHO content for lunch '''

# time of meal
t_meal = np.where(meal != 0)[0]
t_replay = t_meal[2]

# glucose outcome with reduced meal size
meal_red = np.copy(meal)
meal_red[t_replay] = 0.5 * meal_red[t_replay]

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal_red, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_D_red = model['G']

# glucose outcome with increased meal size
meal_inc = np.copy(meal)
meal_inc[t_replay] = 1.5 * meal_inc[t_replay]

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal_inc, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_D_inc = model['G']


''' Plot '''

G_all = [G_u_red, G_u_inc, G_D_red, G_D_inc, G]
labels = ['50% bolus', '150% bolus', '50% meal', '150% meal', 'original']
colors = 2 * [plt.cm.inferno(0.6)] + 2 * [plt.cm.viridis(0.62)] + [plt.cm.PuBu(0.85)]
ls = [(0, (5, 3)), (0, ()), (0, (5, 3)), (0, ()), (0, ())]

plot.plot_replay(G_all, labels, colors, ls)
plt.show()
