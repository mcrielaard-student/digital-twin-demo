## Information

This repository contains code to simulate glucose-insulin regulation during exercise in type 1 diabetes, presented in 
the following manuscript:

Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach (2023). 
**New model of glucose-insulin regulation characterizes effects of physical activity and facilitates personalized 
treatment evaluation in children and adults with type 1 diabetes**. PLOS Computational Biology, 19(2). 
doi: [10.1371/journal.pcbi.1010289](https://doi.org/10.1371/journal.pcbi.1010289)

\* Corresponding author: Hans-Michael Kaltenbach <michael.kaltenbach@bsse.ethz.ch>

## Content

Run the script `fullday_simulations.py` to perform full-day simulations including meals, insulin injections and exercise 
for a standard person with T1D. It generates the glucose trajectories and figures shown in Figure 4 of the manuscript
and can be used as a template to create and run other simulation scenarios.

The repository is structured into:

* `data`: Data used for model calibration and validation. Data were digitalized from previously published studies.  
    For calibration, we used:
    * Wolfe (1986). doi: [10.1172/JCI112388](http://doi.org/10.1172/JCI112388)
    * Ahlborg (1982). doi: [10.1172/JCI110440](http://doi.org/10.1172/JCI110440)
    * Romeres (2021). doi: [10.1152/ajpendo.00084.2021](http://doi.org/10.1152/ajpendo.00084.2021)
    * Romeres (2018). doi: [10.2337/db18-45-OR](http://doi.org/10.2337/db18-45-OR)
    * Jayawardene (2017). doi: [10.1089/dia.2016.0461](http://doi.org/10.1089/dia.2016.0461)  
For validation, we used:
    * Rabasa-Lhoret (2001). doi: [10.2337/diacare.24.4.625](http://doi.org/10.2337/diacare.24.4.625)
    * Maran (2010). doi: [10.1089/dia.2010.0038](http://doi.org/10.1089/dia.2010.0038)
    * Iscoe and Riddell (2011). doi: [10.1111/j.1464-5491.2011.03274.x](http://doi.org/10.1111/j.1464-5491.2011.03274.x)
    * Zaharieva (2017). doi: [10.1089/dia.2017.0010](http://doi.org/10.1089/dia.2017.0010)
    * Dube (2013). doi: [10.1249/MSS.0b013e31826c6ad3](http://doi.org/10.1249/MSS.0b013e31826c6ad3)
    * Ahlborg (1974). doi: [10.1172/JCI107645](http://doi.org/10.1172/JCI107645)
* `data_patients`: Patient data used for model personalization and replay simulations. Data are from the University 
Children's Hospital Basel (UKBB) and have been published in: \
S. Bachmann, M. Hess, E. Martin-Diener, K. Denhaerynck, U. Zumsteg (2016). Nocturnal hypoglycemia and physical 
activity in children with diabetes: New insights by continuous glucose monitoring and accelerometry. 
*Diabetes Care*, 39(7). doi: [10.2337/dc16-0411](http://doi.org/10.2337/dc16-0411) 
* `functions`: Functions required to run the model. 
* `parameters`: Model parameters for different study conditions.
* `patient_simulations`: Python scripts to run the (personalized) glucoregulatory model for patient data and perform 
replay simulations.
* `suppl`: Python scripts to run the glucoregulatory model for calibration and validation studies.

## Requirements

* Python (3.7)
* Python packages: numpy (1.19.2), scipy (1.5.0), pandas (1.3.2), matplotlib (3.2.2)

## Author

Julia Deichmann <julia.deichmann@bsse.ethz.ch>

## License

Source code licensed under BSD-3-Clause. Copyright © 2022 ETH Zurich, Julia Deichmann, Sara Bachmann, Marie-Anne Burckhardt, 
Marc Pfister, Gabor Szinnai, Hans-Michael Kaltenbach; D-BSSE; CSB Group. For details see LICENSE file.

Patient data are licensed under a <a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">Creative 
Commons Attribution-NonCommercial 4.0 International License</a>. <br />
<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/88x31.png" /></a>