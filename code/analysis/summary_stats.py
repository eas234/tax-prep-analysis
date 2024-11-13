import os
import pandas as pd               
import sys
from dateutil import *

# set working directory as current directory
set_working_dir()

sys.path.insert(1, '../utils')
from data_utils import *

# load config file
out = load_config()

# import cleaned data
df = pd.read_csv('../data/clean/dat_clean.csv')

# generate table of summary statistics as .txt file
with open('../results/tables/summ_stats.txt', mode='w') as output:
     
      print(r"\begin{table}[h!]", file=output)
      print(r"\begin{center}", file=output)
      print(r"\caption{County-level Summary Statistics \label{tab:summ_stats}}", file=output)
      print(r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lccc}", file=output)
      print(r" &      &      & County-Level Mean\\", file=output)
      print(r" & 2021 & 2017 &  Difference \\", file=output)
      print(r"\hline", file=output)
      print(r"Share using paid preparer & "
            + str(df.share_using_pp.mean().round(3))
            + r" & "
            + str(df.share_using_pp_17.mean().round(3))
            + r" & "
            + str((df.share_using_pp - df.share_using_pp_17).mean().round(3))
            + r" \\",
            file=output)
      print(r" & ("
            + str(df.share_using_pp.std().round(3))
            + r") & ("
            + str(df.share_using_pp_17.std().round(3))
            + r") & ("
            + str((df.share_using_pp - df.share_using_pp_17).std().round(3))
            + r") \\",
            file=output)

      print(r"CTC & & & ", file=output)
      print(r" \\", file=output)
      print(r"\quad Claim rate & "
            + str(df.share_ctc.mean().round(3))
            + r" & "
            + str(df.share_ctc_17.mean().round(3))
            + r" & "
            + str((df.share_ctc - df.share_ctc_17).mean().round(3))
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str(df.share_ctc.std().round(3))
            + r") & ("
            + str(df.share_ctc_17.std().round(3))
            + r") & ("
            + str((df.share_ctc - df.share_ctc_17).std().round(3))
            + r") \\",
            file=output)
      
      print(r"\quad Average dollar amount of benefits per claim & "
            + str(int(df.mean_ctc.mean()))
            + r" & "
            + str(int(df.mean_ctc_17.mean()))
            + r" & "
            + str(int((df.mean_ctc - df.mean_ctc_17).mean()))
            + r" \\",
            file=output)
      print(r"\quad  & ("
            + str(df.mean_ctc.std().round(1))
            + r") & ("
            + str(df.mean_ctc_17.std().round(1))
            + r") & ("
            + str((df.mean_ctc - df.mean_ctc_17).std().round(1))
            + r") \\",
            file=output)
      
      print(r"\quad Total benefits (thousands) & "
            + str((df.tot_ctc/1000).mean().round(1))
            + r" & "
            + str((df.tot_ctc_17/1000).mean().round(1))
            + r" & "
            + str((df.tot_ctc/1000 - df.tot_ctc_17/1000).mean().round(1))
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str((df.tot_ctc/1000).std().round(3))
            + r") & ("
            + str((df.tot_ctc_17/1000).std().round(3))
            + r") & ("
            + str((df.tot_ctc/1000 - df.tot_ctc_17/1000).std().round(3))
            + r") \\",
            file=output)
      print(r"\\", file=output)

      print(r"EITC^{*} & & & ", file=output)
      print(r" \\", file=output)
      print(r"\quad Claim rate & "
            + str(df.share_eitc_lt_75k.mean().round(3))
            + r" & "
            + str(df.share_eitc_lt_75k_17.mean().round(3))
            + r" & "
            + str((df.share_eitc_lt_75k - df.share_eitc_lt_75k_17).mean().round(3))
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str(df.share_eitc_lt_75k.std().round(3))
            + r") & ("
            + str(df.share_eitc_lt_75k_17.std().round(3))
            + r") & ("
            + str((df.share_eitc_lt_75k - df.share_eitc_lt_75k_17).std().round(3))
            + r") \\",
            file=output)

      print(r"\quad Average dollar amount of benefits per claim & "
            + str(int(df.mean_eitc.mean()))
            + r" & "
            + str(int(df.mean_eitc_17.mean()))
            + r" & "
            + str(int((df.mean_eitc - df.mean_eitc_17).mean()))
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str(df.mean_eitc.std().round(1))
            + r") & ("
            + str(df.mean_eitc_17.std().round(1))
            + r") & ("
            + str((df.mean_eitc - df.mean_eitc_17).std().round(1))
            + r") \\",
            file=output)

      print(r"\quad Total benefits (thousands) & "
            + str((df.tot_eitc/1000).mean().round(1))
            + r" & "
            + str((df.tot_eitc_17/1000).mean().round(1))
            + r" & "
            + str((df.tot_eitc/1000 - df.tot_eitc_17/1000).mean().round(1))
            + r" \\",
            file=output)
      
      print(r"\quad & ("
            + str((df.tot_eitc/1000).std().round(3))
            + r") & ("
            + str((df.tot_eitc_17/1000).std().round(3))
            + r") & ("
            + str((df.tot_eitc/1000 - df.tot_eitc_17/1000).std().round(3))
            + r") \\",
            file=output)
      print(r"\\", file=output)


      print(r"EIP & & & ", file=output)
      print(r" \\", file=output)
      print(r"\quad Claim rate & "
            + str(df.share_eip.mean().round(3))
            + r" & & "
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str(df.share_eip.std().round(3))
            + r") & & "
            + r" \\",
            file=output)

      print(r"\quad Average dollar amount of benefits per claim & "
            + str(int(df.mean_eip.mean()))
            + r" & &  "
            + r" \\",
            file=output)
      print(r"\quad  & ("
            + str(df.mean_eip.std().round(1))
            + r") & & "
            + r" \\",
            file=output)

      print(r"\quad Total benefits (thousands) & "
            + str((df.eip_amount/1000).mean().round(1))
            + r" & & &"
            + r" \\",
            file=output)
      print(r"\quad & ("
            + str((df.eip_amount/1000).std().round(3))
            + r")"
            + r" & & &"
            + r" \\",
            file=output)

      print(r"\hline", file=output)
      print(r"\\", file=output)
      print(r"\end{tabular}", file=output)
      print(r"\multicolumn{3}{p\linewidth}{\footnotesize{\emph{Notes:} The table shows summary statistics for rates of preparer use and CTC, EITC, and EIP claims for U.S. counties for tax years 2017 and 2021. Reported values are county-level means. 2017 dollar amounts have been adjusted for inflation using the Bureau of Labor Statistics CPI inflation calculator, indexed to December 2021. Standard deviations are displayed in parentheses. The full sample includes 3,127 counties. Counties in Connecticut are excluded from the sample because the state of Connecticut changed its county definitions during the sample period. ", file=output)
      print(r"\newline * The denominator for the share of returns claiming EITC here and elsewhere in this paper is the total number of returns filed reporting less than \$75K in adjusted gross income. Returns reporting more than \$75K in adjusted gross income are not eligible for this credit. ", file=output)
      print(r"}}", file=output)
      print(r"\end{center}", file=output)
      print(r"\end{table}", file=output)

      os.rename('../results/tables/summ_stats.txt', '../results/tables/summ_stats.tex')
