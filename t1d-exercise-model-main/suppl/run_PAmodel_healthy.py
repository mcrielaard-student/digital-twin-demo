# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script runs the exercise model for studies with healthy participants used for model calibration (and validation
# for depletion) and generates the corresponding figures (Fig. S1 and S6f) of the following manuscript:
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
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


''' select study '''

# 0: Wolfe (1986)
# 1: Ahlborg (1982)
# 2: Ahlborg (1974)

idx = 0


''' Parameters '''

params = pd.read_csv('parameters/params_healthy.csv', header=None,
                     dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()

''' Data sets '''

study = ['Wolfe', 'Ahlborg82', 'Ahlborg74']


''' Import data '''

data = pd.read_csv('data/data_' + study[idx] + '.csv')
input = pd.read_csv('data/input_' + study[idx] + '.csv')
info = pd.read_csv('data/info_' + study[idx] + '.csv')


''' Compute glucose profile '''

Gb, Ib = info[['Gb', 'Ib']].iloc[0]
w = info['w'].iloc[0]
pa = info[['PA_start', 'PA_end']].iloc[0].to_list()
depl = info['depl'].iloc[0]

t = np.array(input['time'])
AC = np.array(input['AC'])
meal = np.array(input['meal'])
I = np.array(input['Ins'])

model = GIM.compute_glucose_data(params, [Gb, Ib], w, AC, meal, I=I)


''' Plot '''

if 'GU' in data.columns:
    plot.plot_model(t, model, [Gb, Ib], params, pa, depl=None, glc_data=data[['time', 'Glc']],
                    glc_sd=data['Glc_sd'], GU=data[['GU', 'GU_sd']], GP=data[['GP', 'GP_sd']])
    plt.show()
else:
    plot.plot_model(t, model, [Gb, Ib], params, pa, depl=depl, glc_data=data[['time', 'Glc']],
                    glc_sd=data['Glc_sd'])
    plt.show()
