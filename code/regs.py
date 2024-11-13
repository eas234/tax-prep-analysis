import pandas as pd               # Pandas handles dataframes
from dateutil import *            # for parsing dates
import statsmodels.formula.api as smf  # for doing statistical regression
from linearmodels.iv import IV2SLS # for two-stage least squares regressions specifically
import statsmodels.api as sm       # access to the wider statsmodels library, including R datasets

from data_utils import *

set_working_dir()
out = load_config()

df = pd.read_csv('../data/clean/dat_clean.csv')
df = df.dropna(subset=['maj_black',
                  'maj_hisp',
                  'urban',
                  'share_college',
                  'hh_inc_pct',
                  'r_marriage',
                  'share_using_pp', 
                  'share_using_pp_17',
                  'share_eip', 
                  'mean_eip',
                  'share_ctc_dif',
                  'mean_ctc_dif',
                  'share_eitc_dif',
                  'mean_eitc_dif'])


### first stage regressions

y = df[out['fs_y']]

# Spec 1

X = df[out['fs_X_1']]
X = sm.add_constant(X)

model1 = sm.OLS(y, X)
results1 = model1.fit(cov_type='HC3')

# Spec 2

X = df[out['fs_X_2']]
X = sm.add_constant(X)

model2 = sm.OLS(y, X)
results2 = model2.fit(cov_type='HC3')

# Spec 3

X = df[out['fs_X_3']]
X = sm.add_constant(X)

model3 = sm.OLS(y, X)
results3 = model3.fit(cov_type='HC3')

with open('../results/tables/fs.txt', mode='w') as output:

    print(r"Specification & (1) & (2) & (3) \\", file=output)
    

    print(r"Demographic controls & & X & X  \\", file=output)
    print(r"Socioeconomic controls & &  & X  \\", file=output)

    print(r"\hline", file=output)
   
    print(r"Share using paid preparer (2017) & "
         + str(results1.params['share_using_pp_17'].round(3))
         + (r"^{***}" if results1.pvalues['share_using_pp_17'].round(3) < 0.01 else
                r"^{**}" if results1.pvalues['share_using_pp_17'].round(3) < 0.05 else
                 r"^{*}" if results1.pvalues['share_using_pp_17'].round(3) < 0.1 else
                  "")
         + r" & "
         + str(results2.params['share_using_pp_17'].round(3))
         + (r"^{***}" if results2.pvalues['share_using_pp_17'].round(3) < 0.01 else
                r"^{**}" if results2.pvalues['share_using_pp_17'].round(3) < 0.05 else
                 r"^{*}" if results2.pvalues['share_using_pp_17'].round(3) < 0.1 else
                  "")
         + r" & "
         + str(results3.params['share_using_pp_17'].round(3))
         + (r"^{***}" if results3.pvalues['share_using_pp_17'].round(3) < 0.01 else
                r"^{**}" if results3.pvalues['share_using_pp_17'].round(3) < 0.05 else
                 r"^{*}" if results3.pvalues['share_using_pp_17'].round(3) < 0.1 else
                  "")
         + r" \\",
         file=output
    )
    print(r" & ("
         + str(results1.HC3_se['share_using_pp_17'].round(0))
         + r") & ("
         + str(results2.HC3_se['share_using_pp_17'].round(0))
         + r") & ("
         + str(results3.HC3_se['share_using_pp_17'].round(0))
         + r") \\",
         file=output
    )

    print(r"\hline", file=output)

    print(r"N & "
         + str(int(results1.nobs))
         + r" & "
         + str(int(results2.nobs))
         + r" & "
         + str(int(results3.nobs))
         + r" \\",
         file=output
    )
   
    print(r"R-squared & "
         + str(results1.rsquared.round(3))
         + r" & "
         + str(results2.rsquared.round(3))
         + r" & "
         + str(results3.rsquared.round(3))
         + r" \\",
         file=output
    )

    print(r"F Statistic  &"
        + str(int(results1.fvalue))
        + r" & "
        + str(int(results2.fvalue))
        + r" & "
        + str(int(results3.fvalue))
        + r" \\",
        file=output
    )

### second-stage regressions

## eip

make_2sls_table(df, 
                    outcome='share_eip'
                    
)

make_2sls_table(df, 
                    outcome='mean_eip'
)

## ctc

make_2sls_table(df, 
                    outcome='share_ctc_dif'
)

make_2sls_table(df, 
                    outcome='mean_ctc_dif'
)



## eitc

make_2sls_table(df, 
                    outcome='share_eitc_dif'
)

make_2sls_table(df, 
                    outcome='mean_eitc_dif'
)
