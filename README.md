# tax-prep-analysis
Repository for "The Effect of Tax Peparers on the Distribution of COVID-19 Benefits Programs", working paper

## Overview of repository
The repository is structured as follows:

### code
#### /analysis
- **clean_data.py**: calls function 'clean_data()' which wraps all of the data cleaning functions defined in ../utils/data_utils.py. Generates cleaned data files '../data/clean/dat_clean.csv' and '../data/clean/data_clean_agi.csv'
- **plots.py**: generates the 2017-2021 EITC amounts plot (figure 1, '../../results/figures/eitc_amts.png') and the 2021 preparer use heatmap (figure 2, '../../results/figures/prep_use_21_heatmap.png')
- **regs.py**: runs all of the regressions included in the paper and writes regression output tables 2-8 as .tex files to '../../results/tables/'
- **summary_stats.py**: generates table of summary statistics (table 1, '../../results/tables/summ_stats.tex')
#### /config
- **data.yaml**: config file which defines a variety of state variables (e.g. inflation multiplier to convert 2017 dollars to 2021 dollars) as well as regression instruments, endogenous variables, and control variables.
#### /utils
- **data_utils.py**: defines all of the functions used in data cleaning and analysis. Function descriptions, inputs, and outputs are included in the file.

The following directories are not included in the repository, but are referenced: 

### data
#### /raw
Includes raw data files described in 'Data Sources' below
#### /clean
Includes clean data files:
- **'dat_clean.csv'**: cleaned data reported at the county level, generated by '../../code/analysis/clean_data.py'
- **'data_clean_agi.csv'**: cleaned data reported at the county-by-agi-bin level, generated by '../../code/analysis/clean_data.py'
- **'eitc_fig_data.csv'**: self-generated file containing eitc benefits amounts and income thresholds for tax years 2017 and 2021

### results
#### /tables
includes .tex and/or .txt files for tables 1-8, generated by '../../code/analysis/summary_stats.py' and '../../code/analysis/regs.py'
#### /figures
includes .png files for figures 1 and 2, generated by '../..code/analysis/plots.py'

## Requirements
python>=3.10.12\
dateutil>=2.9.0.post0\
geopandas>=1.0.1\
linearmodels>=6.0\
mapclassify>=2.8.0\
matplotlib>=3.9.0\
pandas>=2.2.2\
seaborn>=0.13.2\
statsmodels>=0.14.2

## Data Sources


## Data Dictionary
Below are descriptions of features included in the post-processed data file. For descriptions of features included in the raw data, please refer to the data sources linked above.

'county': 5-digit FIPS county code\
'share_black': percent share of total county residents who are black\
'maj_black': 1-0 indicator of whether total county is majority black\
'share_hisp': percent share of total county residents who are hispanic\
'maj_hisp': 1-0 indicator of whether total county is majority hispanic\
'share_male': percentage share of total county residents who are male\
'adult_pop': number of county residents who are over the age of 20\
'tot_pop': total county population\
'share_elderly': percentage share of county residents over 65\
'child_pop': number of county residents under the age of 20\
'share_college': percentage share of county residents 18+ with bachelor's degree\
'r_lfp': share of county residents 16+ in labor force\
'r_unemp': share of civilian workforce 16+ who are unemployed\
'median_hh_inc': median county-level household income in 2021 dollars\
'r_marriage': percentage share of county residents 15+ who are married\
'hh_inc_pct': percentile rankings of median hh income for in-sample counties\
'share_eip': share of filers reporting <=$200k AGI claiming EIP in TY21\
'mean_eip': per-county average EIP claim amount\
'eip_amount': total EIP spend per county\
'share_eitc_lt_75k(_17)': share of filers reporting <=$75k AGI claiming EITC\
'mean_eitc(_17)': per-county average EITC claim amount. 2021 or 2017 if '_17' is appended.\
'tot_eitc(_17)': total EITC spend per county. 2021 or 2017 if '_17' is appended.\
'share_ctc(_17)': share of filers claiming CTC. 2021 or 2017 if '_17' is appended.\
'tot_ctc(_17)': total CTC spend per county. 2021 or 2017 if '_17' is appended.\
'share_using_pp(_17)': share of returns filed using paid preparer\
'share_ctc_dif': First difference of share of tps claiming CTC between TY21, TY17\
'mean_ctc_dif': First difference of mean CTC claim amts between TY21, TY17\
'share_eitc_dif': First difference of share of tps claiming EITC between TY21, TY17\
'mean_eitc_dif': First difference of mean EITC claim amts between TY21, TY17
