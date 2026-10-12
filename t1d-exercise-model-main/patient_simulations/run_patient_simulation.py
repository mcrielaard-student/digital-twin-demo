# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs the exercise model for individual-subject data illustrating model personalization
# and generates the corresponding figures (Fig. 5 and S8) of the following manuscript:
#
# Title:   New model of glucose-insulin regulation characterizes effects of physical activity and facilitates
#          personalized treatment evaluation in children and adults with type 1 diabetes
# Authors: Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach*
# *Corresponding author:
#          michael.kaltenbach@bsse.ethz.ch
#
# Date:    November 22, 2022
# Author:  Julia Deichmann <julia.deichmann@bsse.ethz.ch>

import pandas as pd
import numpy as np
import functions.PAmodel as GIM
import functions.plot_fct as plot
import matplotlib.pyplot as plt

patient = 4             # 0-4: patient 1-5
day = 1                 # 0-1: study day 1-2


''' Import data '''

data = pd.read_csv('data_patients/data_patient' + str(patient+1) + '_day' + str(day+1) + '.csv')
input = pd.read_csv('data_patients/input_patient' + str(patient+1) + '_day' + str(day+1) + '.csv')
info = pd.read_csv('data_patients/info_patient' + str(patient+1) + '_day' + str(day+1) + '.csv')


''' Extract model inputs '''

Gb, Ib = info[['Gb', 'Ib']].iloc[0]
G0 = data['Glc'].iloc[0]
w = info['w'].iloc[0]

AC = np.array(input['AC'])
u = np.array(input['u'])
ub = np.array(input['ub'])
meal = np.array(input['meal'])


''' Run simulation '''

params = pd.read_csv('parameters/params_patient' + str(patient+1) + '.csv', header=None,
                     dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()
meal_params = pd.read_csv('parameters/meal_params/meal_params_patient' + str(patient+1) + '_day' + str(day+1) + '.csv',
                          delimiter=',')
f = meal_params['f'].to_list()
tau_m = meal_params['tau_m'].to_list()

model = GIM.compute_glucose_replay(params, [Gb, Ib], w, AC, meal, u, ub, G0=G0,
                                   params_meal={'f': f, 'tau_m': tau_m})

plot.plot_personalization(data, model, input)
plt.show()
