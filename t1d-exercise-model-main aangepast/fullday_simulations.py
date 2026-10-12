# **********************************************************************************************************************
#  Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai,
#  Hans-Michael Kaltenbach; D-BSSE; CSB Group
#  All rights reserved. This program and the accompanying materials are made available under the terms of the BSD-3
#  Clause License which accompanies this distribution, and is available at
#  https://gitlab.com/csb.ethz/t1d-exercise-model/-/blob/main/LICENSE
# **********************************************************************************************************************

# This script is used to generate glucose data in full-day simulations using a model of glucose-insulin regulation
# including exercise, meal intake and insulin injections.
# It generates the data for Figure 4 of the following manuscript:
#
# Title:   New model of glucose-insulin regulation characterizes effects of physical activity and facilitates
#          personalized treatment evaluation in children and adults with type 1 diabetes
# Authors: Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach*
# *Corresponding author:
#          michael.kaltenbach@bsse.ethz.ch
#
# Date:    March 17, 2022
# Author:  Julia Deichmann <julia.deichmann@bsse.ethz.ch>



# Glucoseprediction
 
import functions.PAmodel as GIM
import functions.plot_fct as plot
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

 
''' Define basal values '''

Gb = 120                                    # basal glucose level [mg/dl]
Ib = 12                                     # basal insulin level [muU/ml]
weight = 70                                 # weight [kg]
 

''' Define scenarios '''

intensity = {'rest': 0, 'active': 4317, 'highly active': 6539}  # Intensity in AC counts: 2095 = 30%, 4317 = 60%, 6539 = 90% VO2max 
duration = [30, 60, 90]                                         # PA duration [min]
pa_start = 600                                                  # timing of PA start [min]

t_meal = [60, 420, 780]                     # timing of meals [min]
D = [4e4, 6e4, 5e4]                         # CHO amount [mg]

 
''' Parameters '''

params = pd.read_csv('parameters/params_standard.csv', header=None,
                     dtype={0: str}, delimiter=';').set_index(0).squeeze().to_dict()


''' Define model input '''

t_sim = 1441                                # simulation duration [min]
t = np.arange(t_sim)                        # create time points

meal = np.zeros(t_sim)                      # define meal input [mg/min]
meal[t_meal] = D


''' Compute glucose profile '''  
 
def simulate(duration, ac_level, extra_carbs_mg=0.0):
    """Simulate one day with a run of 'duration' minutes at 'ac_level' counts/min
    optionally adds a snack (mg CHO) 10 min before the run. 
    Returns glucose over time [mg/dl]"""
    u = np.zeros(t_sim)                              # insulin input [muU/min]
    AC = np.zeros(t_sim)                             # AC input [counts/min]
    AC[pa_start:pa_start + duration] = ac_level

    m = meal.copy()
    if extra_carbs_mg > 0:
        m[pa_start - 10] += extra_carbs_mg
    # NOTE: if bolus_calc=True also boluses for the snack, the snack's effect is
    # underestimated. Check how PAmodel handles this.       
    model = GIM.compute_glucose_simulation(params, [Gb, Ib], weight, AC, m, u=u,
                                           bolus_calc=True)
    return np.asarray(model['G'])
 
 
def simulate_all():
    """Simulate every duration x intensity combination.
 
    Returns {duration: {intensity_label: glucose_array}}.
    """
    return {dur: {label: simulate(dur, ac) for label, ac in intensity.items()}
            for dur in duration}
 
 
def plot_scenarios(results):
    """One figure per duration, one line per intensity."""
    for dur, curves in results.items():
        plot.plot_simulation(list(curves.values()), labels=list(curves.keys()),
                             colors=[plt.cm.PuBu(0.85)] + list(plt.cm.Reds(np.linspace(0.5, 0.9, 2))),
                             pa=[pa_start, pa_start + dur])
        plt.title(f'Running {dur} min')
        plt.show()
 
 
if __name__ == '__main__':
    plot_scenarios(simulate_all())