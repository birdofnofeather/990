#!/usr/bin/env python3
"""Parse Getty Trust 990-PF XML filings (multiple IRS schema versions) into one JSON."""
import json, re, glob
import xml.etree.ElementTree as ET

def local(tag): return tag.split('}')[-1]

# candidate local-names per field (new-schema first, then legacy pre-2013 names)
FIELDS = {
    # Part I revenue (column a)
    'contributions': ['ContriRcvdRevAndExpnssAmt','ContriRcvdRevAndExpnss','ContriReceivedRevAndExpnss'],
    'interest': ['InterestOnSavRevAndExpnssAmt','InterestOnSavingsRevAndExpnss'],
    'dividends': ['DividendsRevAndExpnssAmt','DividendsRevAndExpnss'],
    'gross_rents': ['GrossRentsRevAndExpnssAmt','GrossRentsRevAndExpnss'],
    'net_gain_assets': ['NetGainSaleAstRevAndExpnssAmt','NetGainSaleAssetsRevAndExpnss'],
    'gross_profit': ['GrossProfitRevAndExpnssAmt','GrossProfitRevAndExpnss'],
    'other_income': ['OtherIncomeRevAndExpnssAmt','OtherIncomeRevAndExpnss'],
    'total_revenue': ['TotalRevAndExpnssAmt','TotalRevAndExpnss','TotalRevenueAndExpenses'],
    # Part I expenses (column a = per books)
    'comp_officers': ['CompOfcrDirTrstRevAndExpnssAmt','CompOfcrDirTrstRevAndExpnss'],
    'other_salaries': ['OthEmplSlrsWgsRevAndExpnssAmt','OthEmplSlrsWgsRevAndExpnss'],
    'pension_benefits': ['PensionEmplBnftRevAndExpnssAmt','PensionEmplBnftRevAndExpnss','PensionEmplBenefitsRevAndExpnss'],
    'legal_fees': ['LegalFeesRevAndExpnssAmt','LegalFeesRevAndExpnss'],
    'accounting_fees': ['AccountingFeesRevAndExpnssAmt','AccountingFeesRevAndExpnss'],
    'other_prof_fees': ['OtherProfFeesRevAndExpnssAmt','OtherProfFeesRevAndExpnss'],
    'interest_exp': ['InterestRevAndExpnssAmt','InterestRevAndExpnss'],
    'taxes': ['TaxesRevAndExpnssAmt','TaxesRevAndExpnss'],
    'depreciation': ['DepreciationRevAndExpnssAmt','DepreciationRevAndExpnss','DeprecAndDepletionRevAndExpnss'],
    'occupancy': ['OccupancyRevAndExpnssAmt','OccupancyRevAndExpnss'],
    'travel_conf': ['TravConfMeetingRevAndExpnssAmt','TravConfMeetingRevAndExpnss','TravelConfMeetingsRevAndExpnss'],
    'printing_publications': ['PrintingPublRevAndExpnssAmt','PrintingAndPubRevAndExpnss'],
    'other_expenses': ['OtherExpensesRevAndExpnssAmt','OtherExpensesRevAndExpnss'],
    'total_operating': ['TotOprExpensesRevAndExpnssAmt','TotOprExpensesRevAndExpnss'],
    'grants_paid': ['ContriPaidRevAndExpnssAmt','ContriGiftsPaidRevAndExpnss'],
    'total_expenses': ['TotalExpensesRevAndExpnssAmt','TotalExpensesRevAndExpnss'],
    'excess_revenue': ['ExcessRevenueOverExpensesAmt','ExcessOfRevenueOverExpenses'],
    'net_investment_income': ['NetInvestmentIncomeAmt','NetInvestmentIncome'],
    'adjusted_net_income': ['AdjNetIncomeAmt','AdjustedNetIncome'],
    # charitable-purpose disbursements (column d)
    'total_disburse_charitable': ['TotalExpensesDsbrsChrtblAmt','TotalExpensesDsbrsChrtbl','TotalExpensesDsbrsChrtblPrps'],
    'operating_disburse_charitable': ['TotOprExpensesDsbrsChrtblAmt','TotalOperatingExpensesDsbrsChrtbl','TotOperatingExpensesDsbrsChrtbl','TotOprExpensesDsbrsChrtblPrps'],
    # header / page 1
    'fmv_assets': ['FMVAssetsEOYAmt','FMVAssetsEOY'],
    # balance sheet EOY
    'total_assets_eoy': ['TotalAssetsEOYAmt','TotalAssetsEOY'],
    'total_liabilities_eoy': ['TotalLiabilitiesEOYAmt','TotalLiabilitiesEOY'],
    'net_assets_eoy': ['TotNetAstOrFundBalancesEOYAmt','TotalNetAssetsEOY','TotNetAstOrFundBalancesEOY'],
    'total_assets_boy': ['TotalAssetsBOYAmt','TotalAssetsBOY'],
    # Part V/X/XI/XII
    'min_investment_return': ['MinimumInvestmentReturnAmt','MinimumInvestmentReturn'],
    'distributable_amount': ['DistributableAmountAmt','DistributableAmountAsAdjusted','DistributableAmount'],
    'qualifying_distributions': ['QualifyingDistributionsAmt','QualifyingDistributions'],
    'mortgages_payable': ['MortgNotesPyblEOYAmt','MortgagesAndNotesPayableEOY','MortgNotesPyblEOY'],
}

def parse_file(path):
    tree = ET.parse(path)
    root = tree.getroot()
    # collect first occurrence of each localname within IRS990PF (and ReturnHeader for period)
    out = {}
    period = None
    for el in root.iter():
        ln = local(el.tag)
        if ln in ('TaxPeriodEndDt','TaxPeriodEndDate') and period is None:
            period = (el.text or '').strip()
    # find the 990PF subtree to avoid picking fields from 990T etc.
    pf = None
    for el in root.iter():
        if local(el.tag) == 'IRS990PF':
            pf = el; break
    scope = pf if pf is not None else root
    index = {}
    for el in scope.iter():
        ln = local(el.tag)
        if el.text and el.text.strip() and ln not in index:
            index[ln] = el.text.strip()
    for key, names in FIELDS.items():
        v = None
        for n in names:
            if n in index:
                try: v = int(index[n])
                except ValueError:
                    try: v = float(index[n])
                    except ValueError: v = index[n]
                break
        out[key] = v
    # officers list
    officers = []
    for el in scope.iter():
        ln = local(el.tag)
        if ln in ('OfficerDirTrstKeyEmplGrp','OfficerDirTrusteeEmplGrp','OfficerDirTrsteeEmplGrp','OfcrDirTrusteesOrKeyEmployee','OfficerDirectorTrusteeEmplGrp'):
            o = {}
            for c in el.iter():
                cl = local(c.tag)
                if c.text and c.text.strip():
                    if cl in ('PersonNm','PersonName','NamePerson'): o['name'] = c.text.strip()
                    elif cl in ('TitleTxt','Title'): o['title'] = c.text.strip()
                    elif cl in ('CompensationAmt','Compensation'): o['comp'] = int(c.text.strip())
                    elif cl in ('EmployeeBenefitProgramAmt','ContriToEmplBenefitPlansEtc','EmployeeBenefitsAmt'): o['benefits'] = int(c.text.strip())
            if o: officers.append(o)
    out['officers'] = officers
    out['tax_period_end'] = period
    return out

result = {}
for path in sorted(glob.glob('xml/fy*.xml')):
    fy = re.search(r'fy(\d{4})', path).group(1)
    try:
        result[fy] = parse_file(path)
    except Exception as e:
        result[fy] = {'error': str(e)}

with open('parsed_xml.json','w') as f:
    json.dump(result, f, indent=1)

# quick sanity table
hdr = ['fy','total_revenue','total_expenses','total_assets_eoy','net_assets_eoy','fmv_assets','qualifying_distributions','grants_paid','other_salaries']
print('\t'.join(hdr))
for fy, d in sorted(result.items()):
    print('\t'.join([fy] + [str(d.get(k)) for k in hdr[1:]]))
