# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs the exercise model for validation studies (1)-(5) and generates the corresponding figures (Fig. 3
# and S6a-e) of the following manuscript:
#
# Title:   New model of glucose-insulin regulation characterizes effects of physical activity and facilitates
#          personalized treatment evaluation in children and adults with type 1 diabetes
# Authors: Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach*
# *Corresponding author:
#          michael.kaltenbach@bsse.ethz.ch
#
# Date:    March 17, 2022
# Author:  Julia Deichmann <julia.deichmann@bsse.ethz.ch>

import functions.PAmodel as GIM
import functions.plot_fct as plot
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


''' Parameters '''

pval = pd.read_csv('parameters/params_validation.csv', delimiter=';')
p_pred = pd.read_csv('parameters/params_T1D-V1_pred.csv', delimiter=';')


''' Studies '''

# (1) Rabasa-Lhoret (2001)
# (2) Maran (2010)
# (3) Iscoe and Riddell (2011)
# (4) Zaharieva (2017)
# (5) Dube (2013)

study = []
for i in range(8):
    study.append('RabasaLhoret_' + str(i+1))
study = study + ['Maran', 'Iscoe', 'Zaharieva', 'Dube1', 'Dube2']

title = ['Study (1): 25% VO$_2^{max}$, u: 100%',
         'Study (1): 25% VO$_2^{max}$, u: 50%',
         'Study (1): 50% VO$_2^{max}$, u: 50%',
         'Study (1): 50% VO$_2^{max}$, u: 25%',
         'Study (1): 50% VO$_2^{max}$, u: 100%',
         'Study (1): 50% VO$_2^{max}$, u: 50%',
         'Study (1): 75% VO$_2^{max}$, u: 100%',
         'Study (1): 75% VO$_2^{max}$, u: 25%',
         'Study (2)',
         'Study (3)',
         'Study (4)',
         'Study (5): no pre-PA CHO',
         'Study (5): pre-PA CHO']


for idx in range(len(study)):

    ''' Import data '''

    data = pd.read_csv('data/data_' + study[idx] + '.csv')
    input = pd.read_csv('data/input_' + study[idx] + '.csv')
    info = pd.read_csv('data/info_' + study[idx] + '.csv')

    ''' Define parameters '''

    params = pval.iloc[idx].to_dict()

    ''' Compute glucose profile '''

    Gb, Ib = info[['Gb', 'Ib']].iloc[0]
    w = info['w'].iloc[0]
    pa = info[['PA_start', 'PA_end']].iloc[0].to_list()

    t = np.array(input['time'])
    AC = np.array(input['AC'])
    meal = np.array(input['meal'])

    if (idx == 8) or (idx == 9):
        I = np.array(input['Ins'])
        model = GIM.compute_glucose_data(params, [Gb, Ib], w, AC, meal, I=I)
    elif idx == 10:
        u = np.array(input['u'])
        ub = np.array(input['ub'])
        model = GIM.compute_glucose_data(params, [Gb, Ib], w, AC, meal, u=u, ub=ub)
    else:
        u = np.array(input['u'])
        ub = np.array(input['ub'])
        if idx < 8:
            meal_params = pd.read_csv('parameters/meal_params/meal_params_RabasaLhoret.csv', delimiter=',')
        else:
            meal_params = pd.read_csv('parameters/meal_params/meal_params_Dube.csv', delimiter=',')
        f = meal_params['f'].to_list()
        tau_m = meal_params['tau_m'].to_list()
        model = GIM.compute_glucose_data(params, [Gb, Ib], w, AC, meal, u=u, ub=ub,
                                         params_meal={'f': f, 'tau_m': tau_m})

    ''' Compute prediction interval '''

    Gpred = np.genfromtxt('suppl/results_validation/BGpred_' + study[idx] + '.csv', delimiter=',')

    # if (idx == 8) or (idx == 9):
    #     I = np.array(input['Ins'])
    #     Gpred = GIM.compute_glucose_pred_interval(p_pred, [Gb, Ib], w, AC, meal, I=I)
    # elif idx == 10:
    #     u = np.array(input['u'])
    #     ub = np.array(input['ub'])
    #     Gpred = GIM.compute_glucose_pred_interval(p_pred, [Gb, Ib], w, AC, meal, u=u, ub=ub)
    # else:
    #     u = np.array(input['u'])
    #     ub = np.array(input['ub'])
    #     if idx < 8:
    #         meal_pred = pd.read_csv('parameters/meal_params/meal_params_RabasaLhoret_pred.csv', delimiter=';')
    #         f_pred = np.array(meal_pred['f']).reshape(meal_pred.shape[0], 1)
    #         tau_pred = np.array(meal_pred['tau_m']).reshape(meal_pred.shape[0], 1)
    #     else:
    #         meal_pred = pd.read_csv('parameters/meal_params/meal_params_Dube_pred.csv', delimiter=';')
    #         f_pred = np.array(meal_pred[['f1', 'f2']])
    #         tau_pred = np.array(meal_pred[['tau_m1', 'tau_m2']])
    #     Gpred = GIM.compute_glucose_pred_interval(p_pred, [Gb, Ib], w, AC, meal, u=u, ub=ub,
    #                                               params_meal={'f': f_pred, 'tau_m': tau_pred})

    ''' Plot '''

    if idx <= 10:
        plot.plot_glc(t, model['G'], Gb, pa, glc_data=data[['time', 'dG']], glc_sd=data['dG_sd'],
                      Gpred=Gpred, dG=True)
        plt.title(title[idx])
        plt.show()
    else:
        plot.plot_glc(t, model['G'], Gb, pa, glc_data=data[['time', 'Glc']], Gpred=Gpred)
        plt.title(title[idx])
        plt.show()
