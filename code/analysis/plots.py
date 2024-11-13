import geopandas as gpd
import mapclassify
import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# set working directory to file location
set_working_dir()

sys.path.insert(1, '../utils')
from data_utils import *
from matplotlib import font_manager

# set font defaults for plots
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.sans-serif'] = ['Times_New_Roman']

### load data
# US counties shapefile
geo = gpd.read_file("../../data/raw/geography/cb_2018_us_county_500k.shp")
# cleaned data
stats=pd.read_csv("../../data/clean/dat_clean.csv")
# eitc amounts 
eitc = pd.read_csv('../../data/clean/eitc_fig_data.csv')

### merge 
geo['county'] = geo.GEOID.astype(int)

# drop geocodes from hawaii, alaska, guam, VI, and puerto rico
geo = geo.loc[geo.STATEFP != '02']
geo = geo.loc[geo.STATEFP != '15']
geo = geo.loc[geo.STATEFP != '66']
geo = geo.loc[geo.STATEFP != '72']
geo = geo.loc[geo.STATEFP != '78']

merged = pd.merge(geo[['county', 'geometry', 'NAME', 'STATEFP']], stats, how='left', on='county', validate='1:1')

#########################################################
#################### EITC amounts #######################
#########################################################

xs = [eitc.nc_17_inc, eitc.oc_17_inc, eitc.tc_17_inc, eitc.thc_17_inc, eitc.nc_21_inc, eitc.oc_21_inc, eitc.tc_21_inc, eitc.thc_21_inc]
ys = [eitc.nc_17_ben, eitc.oc_17_ben, eitc.tc_17_ben, eitc.thc_17_ben, eitc.nc_21_ben, eitc.oc_21_ben, eitc.tc_21_ben, eitc.thc_21_ben]

linestyles = ['dotted', 'dashed', 'dashdot', 'solid', 'dotted', 'dashed', 'dashdot', 'solid']
colors = ['cornflowerblue', 'cornflowerblue', 'cornflowerblue', 'cornflowerblue', 'firebrick', 'firebrick','firebrick','firebrick']
labels = ['No Children, TY17', 'One Child, TY17', 'Two Children, TY17', 'Three or More Children, TY17', 'No Children, TY21', 'One Child, TY21', 'Two Children, TY21', 'Three or More Children, TY21']

fig, ax = plt.subplots(figsize=(14,6))

for i in range(len(xs)):
    plt.plot(xs[i], ys[i], linestyle=linestyles[i], color=colors[i], label=labels[i], linewidth=2)

ax.set_xlabel('Earned Income ($)', fontsize=20)
ax.set_ylabel('Credit Amount ($)', fontsize=20)
plt.tick_params(bottom=True, top=False, right=False, left=True)
plt.xticks(fontsize=16)
plt.yticks(fontsize=16)
plt.subplots_adjust(bottom=0.15)
ax.legend(loc='upper right', fontsize=12.5)
ax.spines[['right', 'top']].set_visible(False)

plt.savefig('../../results/figures/eitc_amts.png')

#########################################################
######## 2021 Preparer Use Heatmap ##################
#########################################################

### set plot defaults
sns.set_theme(rc={'figure.figsize':(11.7*1.2,8.27*1.1)})
plt.rcParams['font.family'] = 'serif'

### generate percentile bins
print(merged[merged['share_using_pp'].isnull()]['county'])
merged.dropna(subset='share_using_pp', inplace=True)

### make plot
ax = merged.plot(
    column="share_using_pp",  # Data to plot
    scheme="UserDefined",  # Classification scheme
    classification_kwds={'bins': [.10,.20,.30,.40,.50,.60,.70,.80,.90,1]}, # User-defined classification bins
    cmap="Greens",  # Color palette
    edgecolor="k",  # Borderline color
    linewidth=0.1,
    legend=True,  # Add legend
    legend_kwds={"fmt": "{:.0f}"},  # Remove decimals in legend
)

sns.move_legend(
    ax, "lower left",
    bbox_to_anchor=(0.83, 0), # set legend location
    title='Rates of Paid Preparer Use, 2021', # set legend title
    frameon=False, # remove legend frame
    labels = ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%']
)

ax.set_axis_off()

plt.savefig('../../results/figures/prep_use_21_heatmap.png')
