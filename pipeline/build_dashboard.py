#!/usr/bin/env python3
"""Merge parsed XML data + FY2019 ProPublica extract -> verify -> inject into dashboard template."""
import json, sys

xml = json.load(open('parsed_xml.json'))

# FY2019 (FYE 2019-06-30, paper-filed; totals from IRS-extracted structured data via ProPublica API,
# tax_prd 201906). Salaries, pension/benefits, and qualifying distributions were transcribed by the
# user directly from the source PDF (ProPublica display_990 viewer, confirmed period 07/01/2018-
# 06/30/2019) since no XML or clean text layer exists for this filing; user confirmed the read-back
# values before they were entered here.
# FY2019 expense line items (legal/accounting/other prof fees, interest, taxes, depreciation, occupancy,
# travel, printing, other expenses) and salaries/pension/QD were transcribed by the user directly from
# the source PDF (ProPublica display_990 viewer, period 07/01/2018-06/30/2019; no XML or clean text
# layer exists for this paper filing) and confirmed. The ten expense line items plus comp_officers,
# other_salaries and pension_benefits sum to exactly 307,822,113 -- matching the filing's own printed
# line-24 total AND the independently-sourced ProPublica total_operating figure to the dollar.
fy2019 = {
 'contributions':8706512,'interest':0,'dividends':23651135,'gross_rents':349120,
 'net_gain_assets':275215048,'gross_profit':11367185,'other_income':72844697,
 'total_revenue':392133697,'comp_officers':7476079,'other_salaries':100116806,'pension_benefits':43373398,
 'legal_fees':3110798,'accounting_fees':812672,'other_prof_fees':1412464,'interest_exp':21248968,'taxes':144222,
 'depreciation':47577242,'occupancy':15526674,'travel_conf':7231962,'printing_publications':1318436,'other_expenses':58472392,
 'total_operating':307822113,'grants_paid':15903064,'total_expenses':323725177,
 'excess_revenue':68408520,'net_investment_income':460637430,'adjusted_net_income':0,
 'total_disburse_charitable':238726771,'operating_disburse_charitable':None,
 'fmv_assets':13418017359,'total_assets_eoy':11002762921,'total_assets_boy':None,
 'total_liabilities_eoy':927412012,'net_assets_eoy':10075350909,
 'min_investment_return':360148962,'distributable_amount':None,'qualifying_distributions':261122820,
 'mortgages_payable':581125000,'source':'pp+user-transcribed','tax_period_end':'2019-06-30'
}

# FY2007-2009: hand-verified line-by-line from IRS e-file text-layer PDFs (990s.foundationcenter.org
# archive; confirmed "As Filed Data" e-file marker on page 1, NOT scanned/OCR). Every value below was
# read directly from `pdftotext -layout` output and cross-checked: column sums equal the printed
# subtotals exactly (revenue lines 1-11 = line 12; expense lines 13-23 = line 24; 24+25=26), and the
# balance-sheet chain is unbroken through FY2009 EOY -> FY2010 XML BOY (7,892,039,339, exact match).
fy2007 = {
 'contributions':2412188,'interest':10599524,'dividends':53997881,'gross_rents':180234,
 'net_gain_assets':362683457,'gross_profit':10537329,'other_income':27484262,'total_revenue':467894875,
 'comp_officers':3618645,'other_salaries':82022458,'pension_benefits':45961519,
 'legal_fees':8381177,'accounting_fees':631370,'other_prof_fees':8822990,'interest_exp':24936570,
 'taxes':939815,'depreciation':47780443,'occupancy':11340711,'travel_conf':4699905,
 'printing_publications':4278649,'other_expenses':63078587,'total_operating':306492839,
 'grants_paid':12473734,'total_expenses':318966573,'excess_revenue':148928302,
 'net_investment_income':500538750,'adjusted_net_income':142594798,
 'total_disburse_charitable':210277025,'operating_disburse_charitable':192496860,
 'fmv_assets':11187006719,'total_assets_eoy':10009311136,'total_assets_boy':9022859457,
 'total_liabilities_eoy':1130101900,'net_assets_eoy':8879209236,
 'min_investment_return':289333461,'distributable_amount':None,'qualifying_distributions':282006488,
 'mortgages_payable':612638169,'source':'pdf-text','tax_period_end':'2007-06-30'}
fy2008 = {
 'contributions':4475309,'interest':11542703,'dividends':48956353,'gross_rents':234450,
 'net_gain_assets':338330805,'gross_profit':9004317,'other_income':31497787,'total_revenue':444041724,
 'comp_officers':3979144,'other_salaries':86161000,'pension_benefits':60146457,
 'legal_fees':4818837,'accounting_fees':584930,'other_prof_fees':11312274,'interest_exp':44568556,
 'taxes':801439,'depreciation':48230402,'occupancy':11863596,'travel_conf':4427785,
 'printing_publications':3867029,'other_expenses':69644395,'total_operating':350405844,
 'grants_paid':17146106,'total_expenses':367551950,'excess_revenue':76489774,
 'net_investment_income':523269094,'adjusted_net_income':94767793,
 'total_disburse_charitable':255252009,'operating_disburse_charitable':236492736,
 'fmv_assets':10837340620,'total_assets_eoy':9525252079,'total_assets_boy':10009311136,
 'total_liabilities_eoy':1098742386,'net_assets_eoy':8426509693,
 'min_investment_return':307526206,'distributable_amount':None,'qualifying_distributions':354181826,
 'mortgages_payable':630555000,'source':'pdf-text','tax_period_end':'2008-06-30'}
fy2009 = {
 'contributions':5006626,'interest':1920370,'dividends':29851084,'gross_rents':386737,
 'net_gain_assets':-249044122,'gross_profit':7939274,'other_income':28326076,'total_revenue':-175613955,
 'comp_officers':3501872,'other_salaries':86219142,'pension_benefits':34197842,
 'legal_fees':1828727,'accounting_fees':313249,'other_prof_fees':7289497,'interest_exp':24347611,
 'taxes':631079,'depreciation':47888624,'occupancy':12007770,'travel_conf':5112564,
 'printing_publications':2692109,'other_expenses':55434080,'total_operating':281464166,
 'grants_paid':13109320,'total_expenses':294573486,'excess_revenue':-470187441,
 'net_investment_income':42079555,'adjusted_net_income':13367085,
 'total_disburse_charitable':198572362,'operating_disburse_charitable':183798338,
 'fmv_assets':9339172138,'total_assets_eoy':7892039339,'total_assets_boy':9525252079,
 'total_liabilities_eoy':1050239178,'net_assets_eoy':6841800161,
 'min_investment_return':238891497,'distributable_amount':None,'qualifying_distributions':240737201,
 'mortgages_payable':626630000,'source':'pdf-text','tax_period_end':'2009-06-30'}

years = []
for fy, d in xml.items():
    d = dict(d); d['fy'] = int(fy); d['source'] = 'xml'
    d.pop('officers', None)
    years.append(d)
fy2019['fy'] = 2019
years.append(fy2019)
for fy, d in [(2007,fy2007),(2008,fy2008),(2009,fy2009)]:
    d = dict(d); d['fy'] = fy
    years.append(d)
years.sort(key=lambda d: d['fy'])

# ---------------- VERIFICATION ----------------
errors, warns = [], []
# 1) ProPublica cross-check (independent IRS extract) for overlapping years
pp = {  # fy: (totrevenue, totfuncexpns, totassetsend, totliabend)
 2011:(366280341,267851965,8913772900,999085563),
 2012:(257277551,278565542,8768624413,1234304865),
 2013:(469390127,281926505,9339563278,1149956125),
 2014:(698652649,283270012,10135664990,1125514300),
 2015:(503553641,279216928,10063978609,985530702),
 2019:(392133697,323725177,11002762921,927412012),
 2020:(291491248,352049160,10778929123,1046202396),
 2021:(648647741,307435519,13099579161,878880105),
 2022:(929678117,344395565,12542871508,814148383),
 2023:(370248983,394655685,12546290001,781000778)}
# GivingTuesday index headline cross-check
gt = {2016:(455223615,298288309,9814366918,1132278218),
      2017:(518547043,307031929,10391324503,884003267),
      2018:(642552640,324582190,10991862987,915610943)}
by = {d['fy']: d for d in years}
for fy,(r,e,a,l) in {**pp, **gt}.items():
    d = by[fy]
    for k, v in [('total_revenue',r),('total_expenses',e),('total_assets_eoy',a),('total_liabilities_eoy',l)]:
        if d.get(k) != v: errors.append(f'FY{fy} {k}: ours {d.get(k)} vs independent {v}')
# 2) balance chain: BOY(y) == EOY(y-1) book assets
for i in range(1, len(years)):
    prev, cur = years[i-1], years[i]
    if cur.get('total_assets_boy') is not None and prev.get('total_assets_eoy') is not None:
        if cur['total_assets_boy'] != prev['total_assets_eoy']:
            errors.append(f"FY{cur['fy']} assets BOY {cur['total_assets_boy']} != FY{prev['fy']} EOY {prev['total_assets_eoy']}")
# 3) internal consistency: operating + grants == total expenses; components <= totals
for d in years:
    if all(d.get(k) is not None for k in ('total_operating','grants_paid','total_expenses')):
        if d['total_operating'] + d['grants_paid'] != d['total_expenses']:
            errors.append(f"FY{d['fy']} operating+grants != total expenses ({d['total_operating']}+{d['grants_paid']} vs {d['total_expenses']})")
    if all(d.get(k) is not None for k in ('total_assets_eoy','total_liabilities_eoy','net_assets_eoy')):
        if abs(d['total_assets_eoy'] - d['total_liabilities_eoy'] - d['net_assets_eoy']) > 1:
            errors.append(f"FY{d['fy']} assets-liab != net assets")
    # revenue components
    comp = [d.get(k) for k in ('contributions','interest','dividends','gross_rents','net_gain_assets','gross_profit','other_income')]
    if all(c is not None for c in comp) and d.get('total_revenue') is not None:
        if abs(sum(comp) - d['total_revenue']) > 2:
            warns.append(f"FY{d['fy']} revenue components sum {sum(comp)} vs total {d['total_revenue']} (diff {sum(comp)-d['total_revenue']})")

# 4) hand-verified sum checks for FY2007-2009 (belt-and-suspenders vs. the numbers above)
_checks = [
 (2007, dict(rev=[2412188,10599524,53997881,180234,362683457,10537329,27484262], exp13_23=[3618645,82022458,45961519,8381177,631370,8822990,24936570,939815,47780443,11340711,4699905,4278649,63078587])),
 (2008, dict(rev=[4475309,11542703,48956353,234450,338330805,9004317,31497787], exp13_23=[3979144,86161000,60146457,4818837,584930,11312274,44568556,801439,48230402,11863596,4427785,3867029,69644395])),
 (2009, dict(rev=[5006626,1920370,29851084,386737,-249044122,7939274,28326076], exp13_23=[3501872,86219142,34197842,1828727,313249,7289497,24347611,631079,47888624,12007770,5112564,2692109,55434080])),
 (2019, dict(rev=None, exp13_23=[7476079,100116806,43373398,3110798,812672,1412464,21248968,144222,47577242,15526674,7231962,1318436,58472392])),
]
for fy, c in _checks:
    d = by[fy]
    if c['rev'] is not None and sum(c['rev']) != d['total_revenue']: errors.append(f"FY{fy} hand-sum revenue {sum(c['rev'])} != {d['total_revenue']}")
    if sum(c['exp13_23']) != d['total_operating']: errors.append(f"FY{fy} hand-sum operating {sum(c['exp13_23'])} != {d['total_operating']}")

print('ERRORS:', len(errors)); [print('  !!', e) for e in errors]
print('WARNINGS:', len(warns)); [print('  ~', w) for w in warns]
if errors: sys.exit(1)

# officers FY2024 (top by comp)
off = [o for o in xml['2024']['officers'] if o.get('comp') is not None]
off.sort(key=lambda o: -o['comp'])
officers2024 = off[:12]

PP = 'https://projects.propublica.org/nonprofits/download-filing?path='
archive = [
 {'fy':2007,'url':PP+'2009_01_PF%2F95-1790021_990PF_200706.pdf','tag':'e-file text'},
 {'fy':2008,'url':PP+'2009_06_PF%2F95-1790021_990PF_200806.pdf','tag':'e-file text'},
 {'fy':2009,'url':PP+'2010_06_PF%2F95-1790021_990PF_200906.pdf','tag':'e-file text'},
 {'fy':2010,'url':PP+'2011_06_PF%2F95-1790021_990PF_201006.pdf','tag':'XML'},
 {'fy':2011,'url':PP+'2012_07_PF%2F95-1790021_990PF_201106.pdf','tag':'XML'},
 {'fy':2012,'url':PP+'2013_10_PF%2F95-1790021_990PF_201206.pdf','tag':'XML'},
 {'fy':2013,'url':PP+'2014_07_PF%2F95-1790021_990PF_201306.pdf','tag':'XML'},
 {'fy':2014,'url':PP+'2015_07_PF%2F95-1790021_990PF_201406.pdf','tag':'XML'},
 {'fy':2015,'url':PP+'2016_07_PF%2F95-1790021_990PF_201506.pdf','tag':'XML'},
 {'fy':2016,'url':PP+'IRS%2F951790021_201606_990PF_2017100214790468.pdf','tag':'XML'},
 {'fy':2017,'url':PP+'05_2018_prefixes_94-99%2F951790021_201706_990PF_2018052915349719.pdf','tag':'XML'},
 {'fy':2018,'url':PP+'06_2019_prefixes_88-95%2F951790021_201806_990PF_2019060716392273.pdf','tag':'XML'},
 {'fy':2019,'url':PP+'download990pdf_10_2021_prefixes_84-99%2F951790021_201906_990PF_2021102019108054.pdf','tag':'IRS extract + transcribed'},
 {'fy':2020,'url':'https://projects.propublica.org/nonprofits/download-xml?object_id=202141379349101464','tag':'XML'},
 {'fy':2021,'url':PP+'download990pdf_07_2022_prefixes_94-99%2F951790021_202106_990PF_2022071120198236.pdf','tag':'XML'},
 {'fy':2022,'url':PP+'IRS%2F951790021_202206_990PF_2023060821406436.pdf','tag':'XML'},
 {'fy':2023,'url':'https://projects.propublica.org/nonprofits/download-xml?object_id=202421359349106107','tag':'XML'},
 {'fy':2024,'url':'https://projects.propublica.org/nonprofits/organizations/951790021/202531359349102323/full','tag':'XML'},
]

# Schedule B donor/contributor lists (public for private foundations). Covers years with source XML
# only (FY2010-2018, FY2020-2024) via extract_donors.py; FY2007-2009 (PDF text) and FY2019 (no XML)
# are intentionally absent and flagged as unavailable in the UI rather than guessed at.
try:
    donors = json.load(open('donors.json'))
except FileNotFoundError:
    donors = {}

data = {'years': years, 'officers2024': officers2024, 'archive': archive, 'donors': donors}
json.dump(data, open('dataset.json','w'), indent=1)

tpl = open('dashboard_template.html', encoding='utf-8').read()
html = tpl.replace('__DATA__', json.dumps(data, separators=(',',':')))
open('Getty_Trust_Financial_Dashboard.html','w',encoding='utf-8').write(html)
print('OK: dashboard written,', len(years), 'years,', len(officers2024), 'officers,', len(donors), 'donor-list years')
