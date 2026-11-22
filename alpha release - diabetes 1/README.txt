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
alpha release - diabetes 1/
├── data/
│   ├── raw/T1D-UOM/                  	 # dataset (not changed)
│   └── processed/                    	 # files per run (run_003, run_005, run_007)
├── data processing/
│   └── trial_preprocessing_2...      	 # notebook that processes the T1D-UoM data
├── glucose prediction and advice/
│   ├── data/							 # 
│   ├── data_patients/					 # patient data gathered by Deichmann et al.
│   ├── functions/                    	 # ETH Zurich model (PAmodel.py, bolus_calc.py, ...)
│   ├── parameters/                   	 # model parameters (params_standard.csv, ...)
│   ├── patient_simulations
│   ├── fit_patient.py         		 # patient-specific parameter estimation for patients in data_patients
│   ├── fullday_simulations.py        	 # simulates glucose for every duration x intensity
│   ├── advice.py                     	 # turns the predictions into advice
├── results/                       		 # saved figures from model output
└── user-interface/
    └── app.py                         	 # Streamlit app (user interface)
---

Usage

1. Parameter estimation

Run from inside the folder `glucose prediction and advice`, because the ETH code reads `parameters/...` and `data_patients/...` relative to the working directory.

```bash
cd "glucose prediction and advice"
python fit_patient.py
```

This shows one figure per day with p1 and p3 fixed on the FIT_DAY and other parameters refitted on VALIDATION_DAY.

```bash
cd "glucose prediction and advice"
python fit_patient.py --per-meal.py
```

This shows one figure per day with p1 and p3 fixed on the FIT_DAY and other parameters refitted on VALIDATION_DAY. Meal parameters f and tau_m are fitted per meal.

```bash
cd "glucose prediction and advice"
python fit_patient.py --free-day2.py
```

This shows one figure per day with p1 and p3 fixed on the FIT_DAY and other parameters refitted on VALIDATION_DAY. An additional line shows p1 and p3 refitted for VALIDATION_DAY.
The figures can be found in `results/`.

2. Glucose prediction

Run from inside the folder `glucose prediction and advice`, because the ETH code reads `parameters/...` relative to the working directory.

```bash
cd "glucose prediction and advice"
python fullday_simulations.py
```

This shows one figure per run duration (30, 60, 90 min) with one line per intensity.
The figures can be found in `results/`.

3. Advice

```bash
python advice.py
```

Prints the advice for the start glucose and for each combination of duration and intensity, 
and shows the same plots as in "glucose prediction and advice".

4. Streamlit app

```bash
streamlit run app.py
```

The app asks for personal information (age, sex, height, weight) and the current glucose (value and trend). 
And gives demo advice for now.

---

How the parameter estimation works

`fit_patient.py` fits the model to patient data and estimates the patient's parameters:

|   p1:		(init = 0.0126)
|   p3:		(init = 2.78e-05)
|   Gb:		(init = 120)
|   f:		(init = 1)
|   tau_m:	(init = 40)

Initialization is done with respect to the population-average values in `parameters/params_standard.csv`.

The parameters are changed to achieve the best fit of the model onto the data. The program uses the least squares method and minimizes the sum of squared differences.

---

How the prediction works

`fullday_simulations.py` simulates one day (1440 min, one value per minute) for a virtual person:

| Setting               | Value                                                       |
|        ---            |    ---                                                      |
| Basal glucose `Gb`    | 120 mg/dl                                                   |
| Basal insulin `Ib`    | 12 muU/ml                                                   |
| Weight                | 70 kg                                                       |
| Meals                 | 40 g, 60 g and 50 g carbohydrates at 01:00, 07:00 and 13:00 |
| Start of the run      | minute 600 (10:00)                                          |
| Durations             | 30, 60, 90 min                                              |

The intensity of the run is given in activity counts (AC) per minute, the measure of physical activity used by the model:

| Label              | AC per minute | Approximate intensity |
|---                 |---            |---                    |
| rest               | 0             | no run                |
| low intensity      | 2095          | 30% VO2max            |
| moderate intensity | 4317          | 60% VO2max            |

The model calculates the insulin bolus for each meal (`bolus_calc=True`). 
The output of `simulate_all()` is a dictionary in a dictionary: `results[duration][intensity]` 
is the glucose curve of the day in mg/dl, for example `results[30]['rest']`.

---

How the advice works

`advice.py` imports the predictions and compares them to the thresholds below. The model works in mg/dl; 
the thresholds are given in mmol/L and converted with 1 mmol/L = 18.0182 mg/dl.

| Glucose (mmol/L) | Meaning             | Advice                                           |
|---               |---                  |---                                               |
| < 3.9            | Hypo                | Postpone exercise and treat the hypo             |
| 3.9 - 6          | Increased hypo risk | Consider extra carbohydrates and monitor glucose |
| 6 - 12           | Ok                  | Exercise is possible                             |
| 12 - 15          | Elevated glucose    | Moderate intensity only                          |
| > 15             | Hyperglycaemia      | Postpone exercise                                |

There are two functions:

- `start_advice(g)`: advice before the run, based on the glucose at the start.
- `run_advice(G, dur)`: looks at the lowest and highest predicted glucose from the start of the run until 60 minutes after the end of the run, 
and warns for a hypo, an increased hypo risk or a high glucose.

---

Data processing (T1D-UoM dataset)

The notebook in `data processing/` prepares the real data of the T1D-UoM dataset (running registrations, glucose, insulin and carbohydrates) 
for use with the model. It is tested on participant UoM2301. Steps:

1. **Demographics**: combines BMI and participant metadata.
2. **Activity**: selects registrations of type RUNNING, groups registrations less than 15 minutes apart into one session (`run_001`, `run_002`, ...) and keeps sessions with at least 10 minutes of active time.
3. **Glucose**: removes missing values and duplicates, removes timestamps with conflicting values.
4. **Insulin and carbohydrates**: cleans basal insulin, bolus insulin and meal data.
5. **Linking**: for each run, selects the data from 30 minutes before to 120 minutes after the run.
6. **Example**: a table per minute for `run_003` with glucose, insulin and carbohydrates.
7. **Demo files**: for `run_003`, `run_005` and `run_007`, Excel files (`_data`, `_info`, `_input`) are written to `data/processed/` in the format of the ETH model.

---

Known limitations

- **Real data cannot be used by the model yet.** The generated Excel files could not be read by the ETH code, 
    so they are not usable as demo data yet.
- **The activity intensity is a rough estimate.** The T1D-UoM dataset does not contain activity counts. 
    In the demo files, steps per minute are multiplied by 50 to get "AC".
- **`Gb`, `G0` and `Ib` are not determined correctly.** In the demo files, `Gb` and `G0` are the first available
    glucose value and `Ib` is a fixed value, instead of values determined according to the requirements of the model.
- **The prediction is for one virtual person** (fixed basal values and weight), so the advice is not personal yet.
- **The app output is a placeholder**: the advice text and the plot are fixed demo conten, so not yet connected to 
    the glucose prediction.