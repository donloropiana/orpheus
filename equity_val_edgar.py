__author__ = "Max Bushala"
__copyright__ = "Copyright 2024, Project Orpheus"
__credits__ = ["Max Bushala", "Billy Nichols", "Noah Perlmulter", "Dasha Malaya"]
__version__ = "0.0.1"
__maintainer__ = "Max Bushala"
__email__ = "maxbushala@gmail.com"
__status__ = "Production"

# from IPython.core.display import display, HTML
# install fuzzywuzzy
# pip install python-Levenshtein (speeds up fuzzywuzzy)

import requests
import json
import pandas as pd
import xmltodict
from bs4 import BeautifulSoup
from fuzzywuzzy import process
import os, shutil
from lxml import etree

# Look at accounting statements in SEC EDGAR
# Don't use a 10K unless it's the new year and that the 10K is recently printed. You'll want to take the last four quarter reports (10Qs) (trailing twelves months, last twelve months [LTM])
# Go with trailing twelve month numbers

headers = {
    'User-Agent' : 'maxbushala@gmail.com'
    }

company_ticker = "AMZN" #VZ, AMZN, WMG

def get_CIKs() -> dict:
    """
    Companies are indexed by CIK number on SEC's EDGAR.

    get_CIKs retrieves all company CIKs from SEC's EDGAR

    Returns:
        dict: company CIKs from the SEC's EDGAR.
        "Failed to retrieve data" (str): returns error string if CIK data could not be accessed with HTTP request.
    """
    
    tickers_url = 'https://www.sec.gov/files/company_tickers.json'

    cik_response = requests.get(tickers_url, headers = headers)

    if cik_response.status_code == 200:
        companyTickers = cik_response.json()
        return companyTickers
    else:
        return "Failed to retrieve data."
    
def get_company_CIK(company_ticker, sec_CIKs):
    """
    get_company_CIK retrieves a specific company's CIK using the company's ticker to search CIK from the list of CIKs in EDGAR.

    CIKs are 10 digit identifiers with leading 0s in the number. Company CIKs in the dictionary are missing leading 0s so we add them back.

    Params:
        company_ticker (str): company ticker to search
        sec_CIKs (dict): company CIKs for all companies listed in SEC's EDGAR
    
    Returns:
        company_CIK_adjusted (str): company CIK for the company being searched
        "No CIK found for {company_ticker}" (str): returns error string if company ticker is not listed in EDGAR.
    """
    sec_CIKs_length = len(sec_CIKs) - 1
    for i in range(0, sec_CIKs_length):
        if sec_CIKs[str(i)]['ticker'].lower() == company_ticker.lower():
            # add leading 0s
            company_CIK_adjusted = str(sec_CIKs[str(i)]['cik_str']).zfill(10)
            return company_CIK_adjusted
    return f"No CIK found for {company_ticker}"

sec_CIKs = get_CIKs()
company_CIK = get_company_CIK(company_ticker, sec_CIKs)

print("company_CIK:\n" + company_CIK)

def get_filing_data(company_CIK):
    """
    get_filing_data retrieves company filings for the company being searched.

    Params:
        company_CIK (str): CIK of the company being searched in EDGAR
    
    Returns:
        filingMetadata ()
    """
    filingMetadata = requests.get(f'https://data.sec.gov/submissions/CIK{company_CIK}.json', headers=headers)
    if filingMetadata.status_code == 200:
        return filingMetadata.json()
    return "Failed to retrieve data."

filingData = get_filing_data(company_CIK)

def companyFacts(company_CIK):
    """
    companyFacts retrieves XBRL company facts for the company being searched.

    Params:
        company_CIK (str): CIK of the company being searched in EDGAR
    
    Returns:
        dict: JSON response containing XBRL company facts.
    """
    companyFacts = requests.get(f'https://data.sec.gov/api/xbrl/companyfacts/CIK{company_CIK}.json', headers=headers).json()
    return companyFacts

company_facts = companyFacts(company_CIK)['facts']['us-gaap']

filing_dataframe = pd.DataFrame.from_dict(filingData['filings']['recent'])

#! Switch this to 10Qs and sum four for annual report 
def get_10K(filings_df):
    """
    get_10K filters a filings DataFrame for the most recent 10-K filing.

    Params:
        filings_df (pd.DataFrame): DataFrame containing filings data
    
    Returns:
        pd.Series: A pandas Series for the most recent 10-K filing.
    """
    df_10K = filings_df[filings_df['form'] == '10-K']
    most_recent_10K = df_10K.sort_values(by='filingDate', ascending=False).head(1)
    print()
    print(most_recent_10K)
    return most_recent_10K.iloc[0]

def get_accession_number(most_recent_10K) -> str:
    """
    get_accession_number extracts the accession number from a Series representing the most recent 10-K filing.

    Params:
        most_recent_10K (pd.Series): A pandas Series representing the most recent 10-K filing.
    
    Returns:
        str: Accession number of the most recent 10-K filing.
    """
    return most_recent_10K['accessionNumber']

def get_primaryDocument(most_recent_10K):
    """
    get_primaryDocument gets the primary document for the most recent 10K.

    """
    return most_recent_10K['primaryDocument']

def get_filing_date(most_recent_10K):
    return most_recent_10K['filingDate']

current_10K = get_10K(filing_dataframe)

accession_number = get_accession_number(current_10K).replace('-', '')
primaryDocument = get_primaryDocument(current_10K)
filing_date = get_filing_date(current_10K)

print("\naccession_number:")
print(accession_number)
print("\nprimaryDocument:")
print(primaryDocument)
print("\nfiling_date:")
print(filing_date)

primaryDocument_no_extension = str(primaryDocument).split('.')[0]

form10K_url = f"https://www.sec.gov/Archives/edgar/data/{company_CIK}/{accession_number}/{primaryDocument_no_extension}_htm.xml"
print("\nForm 10K URL:\n" + form10K_url)
#form10K_url = f"https://www.sec.gov/ixviewer/ix.html?doc=/Archives/edgar/data/{company_CIK}/{accession_number}/{primaryDocument}.htm"

def xml_to_dict(url):
    """
    Converts XML data from a specified URL to a JSON-like dictionary.
    
    Parameters:
    - url (str): The URL string of the XML data to be fetched and converted.
    
    Returns:
    - dict: A dictionary representing the parsed XML data. The structure of the dictionary
            matches the structure of the original XML, with tags as keys and tag contents
            as values.
    - None: Returns None if the request to the URL does not succeed (i.e., the HTTP status
            code is not 200).
    """
    xml_response = requests.get(url, headers=headers)
    if xml_response.status_code == 200:
        xml_content = xml_response.content
        # xml_json = json.dumps(xmltodict.parse(xml_content))
        xml_dict = xmltodict.parse(xml_content)
        return xml_dict
    return None

xml_parsed = xml_to_dict(form10K_url)

financialdata = xml_parsed['xbrl']
# print(financialdata.keys())

# usgaap_financials = {k: v for k, v in xml_parsed['xbrl'].items() if k.startswith('us-gaap')}
# print("\nUS-GAAP Financial Statements:\n")
# print(usgaap_financials.keys())

target_variables = ['industry', 'revenues', 'operating income', 'EBIT', 'book value of equity', 'book value of debt', 'operating leases', 'cash and cross holdings', 'non-operating assets', 'minority interest', 'shares outstanding', 'effective tax rate', 'marginal tax rate', '5 year CAGR', 'target pre-tax operating income margin (EBIT as percent of sales in year 10)', 'sales to capital ratio']
target_statements = ['income statement', 'balance sheet', 'footnotes', 'statement of cash flows', 'statement of operations', 'consolidated revenues']

def save_doc(k, v, location):
    html_file = open(f"{location}/{k}.html", "w")
    try:
        print(f"Wrote {k} to html file.")
        # print(f"{type(v)}")
        if(type(v) is list):
            for i in v:
                if(k=='dei:SecurityExchangeName'):
                    print(i)
                html_file.write(str(i))
        elif(type(v) is dict):
            if(k=='000'):
                print(str(v['#text']))
            html_file.write(str(v['#text']))
        if(k=='000'):
            print(f"{v}")
    except:
        print(f"\nError writing html for {k}.")
        print(f"{type(v)}")
        print(f"{v}")
        html_file.close()
        os.remove(f"{location}/{k}.html")
    html_file.close()
    return

def save_data(financialdata):
    root_path = os.path.expanduser('~')
    print(root_path)
    location = f'{root_path}/Downloads/{company_ticker}FinancialData'

    # Open folder
    if not os.path.exists(location):
        os.makedirs(location)
        print(f"\nFolder '{location}' created.")
    else:
        print(f"\nFolder '{location}' already exists.")
        shutil.rmtree(f'{location}')
        print(f"\nFolder '{location}' deleted.")
        os.makedirs(location)
        print(f"\nFolder '{location}' created.")

    # Save HTML files with financial data to the folder
    for k, v in financialdata.items():
        save_doc(k, v, location)
    return None

print(f"\n{financialdata.keys()}")

# print(financialdata['us-gaap:SegmentReportingDisclosureTextBlock'])

# save_data(financialdata)

# SOLUTION: fuzzy matching

# https://www.msci.com/our-solutions/indexes/gics

# ask Aswath to scrape his website

# file:///Users/maxbushala/Downloads/WMGFinancialData/us-gaap:ScheduleOfRevenuesFromExternalCustomersAndLongLivedAssetsByGeographicalAreasTableTextBlock.html