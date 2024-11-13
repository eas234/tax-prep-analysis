from linearmodels.iv import IV2SLS # for two-stage least squares regressions 
import os
import pandas as pd
import yaml

def set_working_dir():

    '''
    Sets working directory as directory of this script.

    inputs: None
    outputs: None
    '''

    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

    return None

def load_config(file_path='../config/data.yaml'):

    '''
    loads config file into memory for data cleaning, assigning
    config file to object 'out'

    inputs: 
        file_path: path to yaml file with data config settings
    outputs: 
        out: object containing yaml contents
    '''

    with open(file_path, 'r') as stream:
        out = yaml.safe_load(stream)

    return out

def get_paid_prep_count(state='ak', year='2017'):

    '''
    Converts raw state-level IRS data files containing lists of preparer names and addresses
    into total count of preparers by zipcode for that state.

    inputs: 
        state: desired U.S. state of data to load 
        year: desired year of data to load. valid options are '2017', '2021' 

    outputs: 
        counts: dataframe with count of tax preparers by zipcode for the specified state and year.
    '''
    
    if year == '2017':
        df = pd.read_csv('../data/raw/paid_preparers/' + year + '/' + state + '/var/IRS/data/scripts/efile/downloadNew/' + state + '.txt', 
          sep="|", encoding='ISO-8859-1')
        
    elif year == '2021':
        df = pd.read_csv('../data/raw/paid_preparers/' + year + '/var/IRS/data/scripts/efile/downloadNew/' + state + '.txt', 
          sep="|", encoding='ISO-8859-1')
    
    df.columns=['name', 'addr1', 'addr2', 'city', 'state', 'zip', 'zip4', 'fname', 'mi', 'lname', 'phone', 'bk1', 'bk2', 'bk3', 'bk4']
    
    counts = df.zip.value_counts().rename_axis('zip').reset_index(name='counts_'+year)
    counts.zip = counts.zip.apply(pd.to_numeric, errors='coerce')

    counts.dropna(inplace=True)
    
    return counts

def zip_to_county(df, year='2017'):

    '''
    function which takes as input a dataframe with zipcode-level count data
    and outputs a dataframe with county-level count data. In cases where zipcodes
    span multiple counties, the function divides the counted object equally across
    counties.

    NOTE: Connecticut and Alaska changed some or all of their county definitions during the
    sample period. While SOI data have been updated to reflect these new definitions, most 
    other data sources used in this project have not been updated, compromising my ability to 
    reliably link them. This code drops the affected counties from the data.  

    inputs: 
        df: zipcode-level data
        year: calendar year assocaited with zipcode-level data

    outputs:
        df: county-level data
    '''
    
    # dedupe zip level data
    df = df.groupby('zip').sum().reset_index()
    
    # read in zip-county crosswalk
    zip_cty = pd.read_csv('../data/raw/zip_county_xwalk/ZIP_COUNTY_03'+year+'.csv', usecols = ['ZIP', 'COUNTY'])
   
    # standardize colnames and dtypes
    zip_cty = zip_cty.rename(columns={'ZIP': 'zip'})
    zip_cty['zip'] = zip_cty['zip'].astype(int)
    
    # merge zip/county data, using zip_county crosswalk as left dataset (not all zipcodes have preparers)
    df = zip_cty.merge(df, how='left', on='zip', validate='m:1')
    
    df['counts_'+year] = df['counts_'+year].fillna(0)
    
    # create duplicate column for groupby
    df['zip_dupe'] = df['zip']
    
    # merge in grouped zip data
    df = df.merge(df[['zip', 'zip_dupe']].groupby('zip').count().reset_index().rename(columns={'zip_dupe': 'zip_count'}), how='left')
    
    # allocate preparers evenly across zipcodes that span multiple counties
    df['counts_'+year] = df['counts_'+year] / df['zip_count']
    
    # group data by county and sum
    df = df[['COUNTY', 'counts_'+year]].groupby('COUNTY').sum().reset_index()

    df = df.rename(columns={'COUNTY': 'county'})

    ct_ak_drops = [2261, 9110, 9120, 9130, 9140, 9150, 9160, 9170, 9180, 9190]

    print('total counties in ' + str(year) + ':', df.shape[0])
    print('dropping ' + str(len(ct_ak_drops)) + ' counties if found in data')

    df = df[df.county.isin(ct_ak_drops) == False]

    print('total counties in ' + str(year) + ' after drops:', df.shape[0])

    return df

def merge_metro(df):
    
    '''
    Function which takes as input a dataframe with county FIPS codes and outputs
    a dataframe designating each county as urban or not based on USDA 2023 rural-urban
    continuum codes.

    input: 
        df: dataframe with column called "county" containing county FIPS codes
    output:
        df: dataframe with USDA rural-urban continuum codes stored as column 'RUCC_2023', 
        along with binary classification of county as "urban" or not based on these 
        continuum codes. 
    '''

    metro = pd.read_excel("../data/raw/urban_rural/Ruralurbancontinuumcodes2023.xlsx", usecols=['FIPS', 'RUCC_2023'])
    
    metro = metro.rename(columns={"FIPS": 'county'})
    
    metro['urban'] = [1 if x==1 or x==2 or x==3 else 0 for x in metro.RUCC_2023]
    
    df = df.merge(metro, how='left', on='county')
    
    return df

def merge_demog(df):
    
    '''
    Function that merges county-level demographic data from the Census 2021 5-year ACS
    into existing dataframe.

    input:
        df: dataframe with county-level FIPS codes stored as column 'county'

    output:
        df: dataframe with following columns:
            'county': 5-digit FIPS county code
            'share_black': percent share of total county residents who are black
            'maj_black': 1-0 indicator of whether total county is majority black
            'share_hisp': percent share of total county residents who are hispanic
            'maj_hisp': 1-0 indicator of whether total county is majority hispanic
            'share_male': percentage share of total county residents who are male
            'adult_pop': number of county residents who are over the age of 20
            'tot_pop': total county population
            'share_elderly': percentage share of county residents over 65
            'child_pop': number of county residents under the age of 20
            'share_college': percentage share of county residents 18+ with bachelor's degree
            'r_lfp': share of county residents 16+ in labor force
            'r_unemp': share of civilian workforce 16+ who are unemployed
            'median_hh_inc': median county-level household income in 2021 dollars
            'r_marriage': percentage share of county residents 15+ who are married
            'hh_inc_pct': percentile rankings of median hh income for in-sample counties

    '''

    # load Census ACS files
    demog = pd.read_csv('../data/raw/census/census_5yr_acs_2021.csv', skiprows=[0])
    econ = pd.read_csv('../data/raw/census/census_econ_2021.csv', skiprows=[0])
    educ = pd.read_csv('../data/raw/census/census_educ_2021.csv', skiprows=[0])
    marriage = pd.read_csv('../data/raw/census/census_marriage_2021.csv', skiprows=[0])

    # clean/standardize Census 'county' labels
    demog['county'] = [x[-5:] for x in demog.Geography]
    demog.county = demog.county.astype(int)

    econ['county'] = [x[-5:] for x in econ.Geography]
    econ.county = econ.county.astype(int)

    educ['county'] = [x[-5:] for x in educ.Geography]
    educ.county = educ.county.astype(int)

    marriage['county'] = [x[-5:] for x in marriage.Geography]
    marriage.county = marriage.county.astype(int)

    # define demographic variables
    demog['share_black'] = demog["Estimate!!Race alone or in combination with one or more other races!!Total population!!Black or African American"]/demog['Estimate!!SEX AND AGE!!Total population']
    demog['maj_black'] = [1 if x > 0.5 else 0 for x in demog.share_black]
    demog['share_hisp'] = demog["Percent!!HISPANIC OR LATINO AND RACE!!Total population!!Hispanic or Latino (of any race)"]
    demog['maj_hisp'] = [1 if x > 0.5 else 0 for x in demog.share_hisp]
    demog['share_male'] = demog["Percent!!SEX AND AGE!!Total population!!Male"]
    demog['adult_pop'] = demog["Estimate!!SEX AND AGE!!Total population!!20 to 24 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!25 to 34 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!35 to 44 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!45 to 54 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!55 to 59 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!60 to 64 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!65 to 74 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!75 to 84 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!85 years and over"]
    demog['tot_pop'] = demog['Estimate!!SEX AND AGE!!Total population']
    demog['share_elderly'] = (demog["Estimate!!SEX AND AGE!!Total population!!65 to 74 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!75 to 84 years"]+ demog["Estimate!!SEX AND AGE!!Total population!!85 years and over"]) / demog['tot_pop']
    demog['child_pop'] = demog['tot_pop'] - demog['adult_pop']

    # merge demographic variables to output dataframe
    df = df.merge(demog[['county', 'share_black', 'maj_black', 'share_hisp', 'maj_hisp', 'share_male', 'adult_pop', 'tot_pop', 'share_elderly', 'child_pop']], on='county', how='left', validate='1:1')

    # define education variables
    educ['share_college'] = (educ["Estimate!!Total!!AGE BY EDUCATIONAL ATTAINMENT!!Population 18 to 24 years!!Bachelor's degree or higher"] + educ["Estimate!!Total!!AGE BY EDUCATIONAL ATTAINMENT!!Population 25 years and over!!Bachelor's degree or higher"]) / (educ['Estimate!!Total!!AGE BY EDUCATIONAL ATTAINMENT!!Population 18 to 24 years'] + educ['Estimate!!Total!!AGE BY EDUCATIONAL ATTAINMENT!!Population 25 years and over']) 

    # merge education variables to output dataframe
    df = df.merge(educ[['county', 'share_college']], on='county', how='left', validate='1:1')

    # define economic variables
    econ['r_lfp'] = econ["Percent!!EMPLOYMENT STATUS!!Population 16 years and over!!In labor force"]
    econ['r_unemp'] = econ["Percent!!EMPLOYMENT STATUS!!Population 16 years and over!!In labor force!!Civilian labor force!!Unemployed"]
    econ['median_hh_inc'] = econ["Estimate!!INCOME AND BENEFITS (IN 2021 INFLATION-ADJUSTED DOLLARS)!!Total households!!Median household income (dollars)"]

    # merge economic variables to output dataframe
    df = df.merge(econ[['county', 'r_lfp', 'r_unemp', 'median_hh_inc']], on='county', how='left', validate='1:1')

    # define marriage variables
    marriage['r_marriage'] = marriage["Estimate!!Now married (except separated)!!Population 15 years and over"]/100

    # merge marriage variables to output dataframe
    df = df.merge(marriage[['county', 'r_marriage']], on='county', how='left', validate='1:1')

    # final data cleaning/feature generation
    df.median_hh_inc = pd.to_numeric(df.median_hh_inc, errors='coerce')
    df['hh_inc_pct'] = df.median_hh_inc.rank(pct=True)

    return df  

def get_cfips(df):

    '''
    function that converts 2-digit state FIPS and 3-digit county FIPS code columns into a single
    column containing 5-digit county FIPS codes. 

    input:
        df: dataframe with separate columns STATEFIPS and COUNTYFIPS that may be stored as 
        strings, floats, or integers.
    output: 
        df: dataframe with column 'county' containing 5-digit county FIPS codes stored as integers.
    '''
    
    df.STATEFIPS =[x.zfill(2) for x in df.STATEFIPS.astype(str)]
    df.COUNTYFIPS = [x.zfill(3) for x in df.COUNTYFIPS.astype(str)]
    df['county'] = [x + y for x, y in zip(df.STATEFIPS.astype(str), df.COUNTYFIPS.astype(str))]
    df.county = df.county.astype(int)
    
    return df

def merge_soi(df):

    '''
    Function that merges county-level filing data from SOI into existing dataframe.

    input:
        df: dataframe with county-level FIPS codes stored as column 'county'
        (and possibly other variables, 'county' is the minimum requirement)
    output:
        df_overall: dataframe with the following columns (plus any other columns
        included in input dataframe):
            'county': five-digit county FIPS code
            'share_eip': share of filers reporting <=$200k AGI claiming EIP in TY21
            'mean_eip': per-county average EIP claim amount
            'eip_amount': total EIP spend per county
            'share_eitc_lt_75k(_17)': share of filers reporting <=$75k AGI claiming EITC
            'mean_eitc(_17)': per-county average EITC claim amount
            'tot_eitc(_17)': total EITC spend per county
            'share_ctc(_17)': share of filers claiming CTC
            'mean_ctc(_17)': per-county average CTC claim amount 
            'tot_ctc(_17)': total CTC spend per county
            'share_using_pp(_17)': share of returns filed using paid preparer
            'share_ctc_dif': First difference of share of tps claiming CTC between TY21, TY17
            'mean_ctc_dif': First difference of mean CTC claim amts between TY21, TY17
            'share_eitc_dif': First difference of share of tps claiming EITC between TY21, TY17
            'mean_eitc_dif': First difference of mean EITC claim amts between TY21, TY17
    '''

    # load data config file
    out = load_config()
      
    # load aggregate and agi-level SOI data
    overall = pd.read_csv('../data/raw/SOI/21incyallnoagi.csv', encoding='latin-1')
    overall_17 = pd.read_csv('../data/raw/SOI/17incyallnoagi.csv', encoding='latin-1')
    agi = pd.read_csv('../data/raw/SOI/21incyallagi.csv', encoding='latin-1')
    agi_17 = pd.read_csv('../data/raw/SOI/17incyallagi.csv', encoding='latin-1')

    # get 5-digit county code from state/county fips
    for df in [overall, overall_17, agi, agi_17]:
        df = df.loc[df.COUNTYFIPS != 0]
        df = get_cfips(df)
    
    # generate aggregate filing data for agi-restricted tax credits (EITC, EIP)
    for df in [agi, agi_17]:

        if df == agi:
            year=""
        elif df == agi_17:
            year='_17'

        if df == agi: 
            agi_temp = df.loc[df.agi_stub<=7]
            agi_temp = agi_temp['county', 'N1', 'N10971'].groupby('county').sum()
            agi_temp = agi_temp.reset_index()

            agi_temp['share_eip'] = agi_temp.N10971/agi_temp.N1

        df = df.loc[df.agi_stub<=5]
        df = df[['county', 'N1', 'N59660', 'A59660', 'RAC']].groupby('county').sum()
        df = df.reset_index()

        df['share_eitc_lt_75k'+year] = df.N59660 / df.N1
        df['mean_eitc'+year] = (df.A59660 / df.N59660) * 1000
        df['tot_eitc'+year] = df.A59660

    # generate aggregate data for all households
    for df in [overall, overall_17]:
        if df == overall:
            year=""
            df['eip_amount'] = df.A10971
            df['mean_eip'] = (df.eip_amount / df.N10971) * 1000
        elif df == overall_17:
            year='_17'
    
        df['tot_ctc'+year] = df.A11070
        df['share_using_pp'+year] = df.PREP / df.N1
        df['share_ctc'+year] = df.N11070 / df.N1
        df['mean_ctc'+year] = (df.A11070 / df.N11070) * 1000

    # merge overall features with features for filers with less than $75K agi
    overall = overall[['county', 'STATEFIPS', 'tot_ctc', 'eip_amount', 'share_using_pp', 'share_ctc', 'mean_eip', 'mean_ctc']].merge(agi[['county', 'share_eitc_lt_75k', 'mean_eitc', 'tot_eitc']], how='left', on='county', validate='1:1')
    
    overall = overall.merge(agi_17[['county', 'share_eitc_lt_75k_17', 'mean_eitc_17', 'tot_eitc_17']], how='left', on='county', validate='1:1')
    
    overall = overall.merge(agi_temp[['county', 'share_eip']], how='left', on='county', validate='1:1')

    overall = overall.merge(overall_17[['county', 'share_ctc_17', 'mean_ctc_17', 'tot_ctc_17', 'share_using_pp_17']], how='left', on='county', validate='1:1')

    # merge with base dataset
    df_overall = overall.merge(df, how='left', on='county', validate='1:1')

    # generate some final additional features
    df_overall['share_ctc_dif'] = df_overall.share_ctc - df_overall.share_ctc_17
    df_overall['mean_ctc_dif'] = (df_overall.mean_ctc - df_overall.mean_ctc_17*out['infl_mpl'])
    df_overall['share_eitc_dif'] = df_overall.share_eitc_lt_75k - df_overall.share_eitc_lt_75k_17
    df_overall['mean_eitc_dif'] = (df_overall.mean_eitc - df_overall.mean_eitc_17*out['infl_mpl'])

    # generate state indicators
    for state in df_overall.STATEFIPS.unique().tolist():
         df_overall['state_ind_' + str(state)] = [1 if x == state else 0 for x in df_overall.STATEFIPS]

    return df_overall

def clean_data():
    """
    Wrapper function that imports, cleans, and writes out data for analysis.

    inputs: None
    outputs: None
    """

    dat_dict = {}

    out = load_config()
    years=['2017', '2021']
    
    for year in years:    
    
        dat_dict[year] = pd.DataFrame(columns=['zip', 'counts_' + year])
    
        for state in out['states']:
            dat = get_paid_prep_count(state=state, year=year)
            dat_dict[year] = pd.concat([dat_dict[year], dat], ignore_index=True)
    
        dat_dict[year] = zip_to_county(dat_dict[year], year=year)

    df = pd.merge(dat_dict['2021'], dat_dict['2017'], how='left', on='county', validate='1:1')

    df = merge_metro(df)
    df = merge_demog(df)
    df, df_agi = merge_soi(df)

    df.to_csv('../data/clean/dat_clean.csv', index=False)
    df_agi.to_csv('../data/clean/dat_clean_agi.csv', index=False)
    
    return None

def make_2sls_table(df, 
                    outcome='share_eic',  # outcome of interest
    ):

    '''
    Generates table of 2SLS output, including parameter estimates,
    standard errors, indications of significance levels, and
    table caption formatted for LaTeX.

    inputs:
        df: dataframe with outcomes, instruments, endogenous variables, and controls
        outcome: outcome of interest
    outputs:
        formatted .tex file with regression output
    '''
    
    out = load_config()

    y = df[outcome]
    df["const"] = 1

    res_second1 = IV2SLS(y, df[out['spec_1_controls']], df[out['spec_1_endog']], df[out['spec_1_inst']]).fit(
        cov_type="robust"
    )
    print(res_second1)

    res_second2 = IV2SLS(y, df[out['spec_2_controls']], df[out['spec_2_endog']], df[out['spec_2_inst']]).fit(
        cov_type="robust"
    )
    print(res_second2)

    res_second3 = IV2SLS(y, df[out['spec_3_controls']], df[out['spec_3_endog']], df[out['spec_3_inst']]).fit(
        cov_type="robust"
    )
    print(res_second3)

    filename = '../results/tables/ss_'+ outcome +'.txt'

    with open(filename, mode='w') as output:

        print(r"\begin{table}[h!]", file=output)
        print(r"\begin{center}", file=output)
        print(r"\caption{Second-stage regression results: RESULT \label{tab:LABEL}}", file=output)
        print(r"\setlength\tabcolsep{0pt}", file=output)
        print(r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}} lccc }", file=output)

        print(r"Specification & (1) & (2) & (3)  \\", file=output)

        print(r"\hline", file=output)
        print(out['spec_1_inst'])

        print(r"Share using paid preparer & "
            + str(res_second1.params[out['spec_1_endog']].round(3))
            + (r"^{***}" if res_second1.pvalues[out['spec_1_endog']].round(3) < 0.01 else
                r"^{**}" if res_second1.pvalues[out['spec_1_endog']].round(3) < 0.05 else
                 r"^{*}" if res_second1.pvalues[out['spec_1_endog']].round(3) < 0.1 else
                  "")
            + r" & "
            + str(res_second2.params[out['spec_1_endog']].round(3))
            + (r"^{***}" if res_second2.pvalues[out['spec_1_endog']].round(3) < 0.01 else
                r"^{**}" if res_second2.pvalues[out['spec_1_endog']].round(3) < 0.05 else
                 r"^{*}" if res_second2.pvalues[out['spec_1_endog']].round(3) < 0.1 else
                  "")
            + r" & "
            + str(res_second3.params[out['spec_1_endog']].round(3))
            + (r"^{***}" if res_second3.pvalues[out['spec_1_endog']].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues[out['spec_1_endog']].round(3) < 0.05 else
                 r"^{*}" if res_second3.pvalues[out['spec_1_endog']].round(3) < 0.1 else
                  "")
            + r" \\",
            file=output
        )
        print(r"(instrumented) & ("
            + str(res_second1.std_errors[out['spec_1_endog']].round(3))
            + r") & ("
            + str(res_second2.std_errors[out['spec_1_endog']].round(3))
            + r") & ("
            + str(res_second3.std_errors[out['spec_1_endog']].round(3))
            + r") \\",
            file=output
        )

        print(r"Majority Black & "
            + r" & "
            + str(res_second2.params['maj_black'].round(3))
            + (r"^{***}" if res_second2.pvalues['maj_black'].round(3) < 0.01 else
                r"^{**}" if res_second2.pvalues['maj_black'].round(3) < 0.05 else
                r"^{*}" if res_second2.pvalues['maj_black'].round(3) < 0.1 else
                "")
            + r" & "
            + str(res_second3.params['maj_black'].round(3))
            + (r"^{***}" if res_second3.pvalues['maj_black'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['maj_black'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['maj_black'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r" & & ("
            + str(res_second2.std_errors['maj_black'].round(3))
            + r") & ("
            + str(res_second3.std_errors['maj_black'].round(3))
            + r") \\",
            file=output
        )

        print(r"Majority Hispanic & "
            + r" & "
            + str(res_second2.params['maj_hisp'].round(3))
            + (r"^{***}" if res_second2.pvalues['maj_hisp'].round(3) < 0.01 else
                r"^{**}" if res_second2.pvalues['maj_hisp'].round(3) < 0.05 else
                r"^{*}" if res_second2.pvalues['maj_hisp'].round(3) < 0.1 else
                "")
            + r" & "
            + str(res_second3.params['maj_hisp'].round(3))
            + (r"^{***}" if res_second3.pvalues['maj_hisp'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['maj_hisp'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['maj_hisp'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r" & & ("
            + str(res_second2.std_errors['maj_hisp'].round(3))
            + r") & ("
            + str(res_second3.std_errors['maj_hisp'].round(3))
            + r") \\",
            file=output
        )


        print(r"Urban & "
            + r" & "
            + str(res_second2.params['urban'].round(3))
            + (r"^{***}" if res_second2.pvalues['urban'].round(3) < 0.01 else
                r"^{**}" if res_second2.pvalues['urban'].round(3) < 0.05 else
                r"^{*}" if res_second2.pvalues['urban'].round(3) < 0.1 else
                "")
            + r" & "
            + str(res_second3.params['urban'].round(3))
            + (r"^{***}" if res_second3.pvalues['urban'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['urban'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['urban'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r" & & ("
            + str(res_second2.std_errors['urban'].round(3))
            + r") & ("
            + str(res_second3.std_errors['urban'].round(3))
            + r") \\",
            file=output
        )

        print(r"Share college educated & "
            + r" & "
            
            + r" & "
            + str(res_second3.params['share_college'].round(3))
            + (r"^{***}" if res_second3.pvalues['share_college'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['share_college'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['share_college'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r" & & & ("
            + str(res_second3.std_errors['share_college'].round(3))
            + r") \\",
            file=output
        )

        print(r"Median household income & "
            + r" & "
            
            + r" & "
            + str(res_second3.params['hh_inc_pct'].round(3))
            + (r"^{***}" if res_second3.pvalues['hh_inc_pct'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['hh_inc_pct'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['hh_inc_pct'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r"(percentiles) & & & ("
            + str(res_second3.std_errors['hh_inc_pct'].round(3))
            + r") \\",
            file=output
        )

        print(r"Marriage rate & "
            + r" & "
            
            + r" & "
            + str(res_second3.params['r_marriage'].round(3))
            + (r"^{***}" if res_second3.pvalues['r_marriage'].round(3) < 0.01 else
                r"^{**}" if res_second3.pvalues['r_marriage'].round(3) < 0.05 else
                r"^{*}" if res_second3.pvalues['r_marriage'].round(3) < 0.1 else
                "")
            + r" \\",
            file=output
        )
        print(r"(percentiles) & & & ("
            + str(res_second3.std_errors['r_marriage'].round(3))
            + r") \\",
            file=output
        )

        print(r"\hline", file=output)

        print(r"N & "
            + str(int(res_second1.nobs))
            + r" & "
            + str(int(res_second2.nobs))
            + r" & "
            + str(int(res_second3.nobs))
            + r" \\",
            file=output
        )

        print(r"\hline", file=output)
        print(r"\\", file=output)
        print(r"\end{tabular*}", file=output)
        print(r"\multicolumn{3}{p\linewidth}{\footnotesize{\emph{Notes:} The table displays the results \
             of second-stage instrumental variables regressions of the share of taxpayers using a paid \
            preparer on OUTCOME. Control variables include whether the county is majority Black, \
            majority hispanic, or urban; the share of county residents that are college educated;\
             percentiles of county-level median household income; and county-level marriage \
             rates. Counties are designated as urban if they are classified as a metro county under\
            the USDA 2023 rural-urban continuum codes, and rural otherwise. Percentiles of median household \
            income are derived as percentile rankings of county-level median household incomes reported \
            by the 2021 Census 5-year ACS, and take on values between 0 and 1. Heteroskedasticity-robust \
            standard errors are displayed in parentheses. \
            2017 dollar amounts are adjusted for inflation using the Bureau of Labor Statistics CPI \
                inflation calculator, indexed to December 2021. Stars correspond to p-values derived \
                    from two-sided hypothesis tests. ^*: P<.10; ^{**}: P<.05; ^{***}:P<.01.", file=output)
        print(r"}}", file=output)
        print(r"\end{center}", file=output)
        print(r"\end{table}", file=output)

    os.rename(filename, filename[:-3]+'tex')

    return None
