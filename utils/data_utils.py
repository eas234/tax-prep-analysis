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

def load_config(file_path='data.yaml'):

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
