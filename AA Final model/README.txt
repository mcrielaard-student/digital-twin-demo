## T1D Running Advisor (alpha release)

A prototype that predicts the glucose response of a person with type 1 diabetes (T1D) to a run, 
and gives simple running advice based on those predictions. The prediction is made with the 
glucose-insulin model of ETH Zurich (Deichmann et al., 2022). adapted to simulate runs of 
30, 60 and 90 minutes at three intensities (rest, low, moderate) and translate the 
predicted glucose curves into advice before, during and shortly after the run. As user interface a Streamlit 
app is used.

Disclaimer: this is a student project. The advice is not medical advice. 

---

Table of contents

1. [Project status]
2. [Repository structure]
3. [Usage]
4. [How the parameter estimation works]
5. [How the prediction works]
6. [How the advice works]
7. [Data processing (T1D-UoM dataset)]
8. [Known limitations]

---

Project status

Glucose prediction (`fullday_simulations.py`) | Working, for one virtual person
Advice (`advice.py`) | Working, rule-based on the simulated glucose curves
Streamlit app | Prototype: input form works, the advice and plot shown are still demo output
Processing of real data (T1D-UoM) | Working up to linking glucose, insulin and carbohydrates to runs
Running the model on the real data | **Not working yet** (see [Known limitations])

---

Repository structure

```
AA Final model/
├── data/
│	├── processed/
│	│	├── data_patients/					 
│	│	│	└── patient2301/                 	 
│	│	└── day_overviews/                    	  
├── data processing/
│	├── _pycache_/							 
│	├── data_cleaning.py
│	├── data_laden.py
│	├── data_quality.py
│	├── Processing_2301_22nov.py
│	└── trial_preprocessing_2301.py    	 
├── glucose prediction/					 
│	├── functions/
│	│	├── _pycache_/							 
│	│	├── bolus_calc.py
│	│	├── compute_Ra.py
│	│	├── compute_ub.py
│	│	├── PAmodel.py
│	│	└── plot_fct.py
│	├── advice.py
│	└── fullday_simulations.py                     	 
├── parameter fitting/
│	└── fit_patient.py
├── parameters/
│	└── meal_parameters/
├── user-interface/
│	└── app.py
└── README.txt
---
