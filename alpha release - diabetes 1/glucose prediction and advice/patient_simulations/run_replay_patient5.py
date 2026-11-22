# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs replay simulations for patient #5 and generates the corresponding figures (Fig. 6b-d) of the
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

params = pd.read_csv('parameters/params_patient5.csv', header=None,
                     dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()
meal_params = pd.read_csv('parameters/meal_params/meal_params_patient5_day2.csv', delimiter=',')
f = meal_params['f'].to_list()
tau_m = meal_params['tau_m'].to_list()


''' Import data '''

input = pd.read_csv('data_patients/input_patient5_day2.csv')
info = pd.read_csv('data_patients/info_patient5_day2.csv')


''' Extract input  '''

Gb, Ib = info[['Gb', 'Ib']].iloc[0]
G0 = info['G0'].iloc[0]
w = info['w'].iloc[0]
pa = info[['PA_start', 'PA_end']].iloc[0].to_list()

t = np.array(input['time'])

AC = np.array(input['AC'])
PA = np.array(input['PA'])

u = np.array(input['u'])
ub = np.array(input['ub'])

meal = np.array(input['meal'])


''' Compute glucose profile '''

AC = np.zeros(len(t))
AC[pa[0]:pa[1]] = 4996

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G = model['G']


''' Replay with altered pre-PA meal size or insulin dose '''

# 40g CHO, 0U
t_meal = np.where(meal != 0)[0]
t_replay = t_meal[2]

meal_adj = np.copy(meal)
meal_adj[t_replay] = 40e3

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal_adj, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_D_adj = model['G']

# 55g CHO, 1.5U
u_adj = np.copy(u)
u_adj[t_replay] = 1.5e6

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u=u_adj, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_u_adj = model['G']

# plot
G_all = [G_D_adj, G_u_adj, G]
labels = ['40g, 0U', '55g, 1.5U', '55g, 0U']
colors = 2 * [plt.cm.inferno(0.6)] + [plt.cm.PuBu(0.85)]
ls = [(0, (5, 3)), (0, ()), (0, ())]

plot.plot_replay(G_all, labels, colors, ls)
plt.show()


''' Replay with altered PA intensities '''

# 55% VO2max
AC_55 = np.zeros(len(t))
AC_55[pa[0]:pa[1]] = 3946

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC_55, meal, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_AC_55 = model['G']

# 40% VO2max
AC_40 = np.zeros(len(t))
AC_40[pa[0]:pa[1]] = 2835

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC_40, meal, u=u, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_AC_40 = model['G']

# plot
G_all = [G_AC_40, G_AC_55, G]
labels = ['40% VO$_2^{max}$', '55% VO$_2^{max}$', '70% VO$_2^{max}$']
colors = 2 * [plt.cm.inferno(0.6)] + [plt.cm.PuBu(0.85)]
ls = [(0, (5, 3)), (0, ()), (0, ())]

plot.plot_replay(G_all, labels, colors, ls)
plt.show()


''' Replay with altered PA duration '''

# time of post-PA meal and insulin
t_meal = np.where(meal != 0)[0]
t_replay = t_meal[3]

# PA duration: 21 min
AC_21 = np.zeros(len(t))
AC_21[pa[0]:pa[1]-20] = 4996

meal_21 = np.copy(meal)
meal_21[t_replay-20] = meal_21[t_replay]
meal_21[t_replay] = 0

u_21 = np.copy(u)
u_21[t_replay-20] = u_21[t_replay]
u_21[t_replay] = 0

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC_21, meal_21, u=u_21, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_PA_dur21 = model['G']

# PA duration: 61 min
AC_61 = np.zeros(len(t))
AC_61[pa[0]:pa[1]+20] = 4996

meal_61 = np.copy(meal)
meal_61[t_replay+20] = meal_61[t_replay]
meal_61[t_replay] = 0

u_61 = np.copy(u)
u_61[t_replay+20] = u_61[t_replay]
u_61[t_replay] = 0

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC_61, meal_61, u=u_61, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_PA_dur61 = model['G']

# PA duration: 81 min
AC_81 = np.zeros(len(t))
AC_81[pa[0]:pa[1]+40] = 4996

meal_81 = np.copy(meal)
meal_81[t_replay+40] = meal_81[t_replay]
meal_81[t_replay] = 0

u_81 = np.copy(u)
u_81[t_replay+40] = u_81[t_replay]
u_81[t_replay] = 0

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC_81, meal_81, u=u_81, ub=ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})
G_PA_dur81 = model['G']

# plot
G_all = [G_PA_dur21, G_PA_dur61, G_PA_dur81, G]
labels = ['21min', '61min', '81min', '41min']
colors = 3 * [plt.cm.inferno(0.6)] + [plt.cm.PuBu(0.85)]
ls = [(0, (5, 3)), (0, (1, 1)), (0, ()), (0, ())]

plot.plot_replay(G_all, labels, colors, ls)
plt.show()
