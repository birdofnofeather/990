#!/usr/bin/env python3
"""Merge parsed XML data + FY2019 ProPublica extract -> verify -> inject into dashboard template."""
import json, sys

xml = json.load(open('parsed_xml.json'))

# FY2019 (FYE 2019-06-30, paper-filed; IRS-extracted structured data via ProPublica API, tax_prd 201906)
fy2019 = {
 'contributions':8706512,'interest':0,'dividends':23651135,'gross_rents':349120,
 'net_gain_assets':275215048,'gross_profit':11367185,'other_income':72844697,
 'total_revenue':392133697,'comp_officers':7476079,'other_salaries':None,'pension_benefits':None,
 'legal_fees':None,'accounting_fees':None,'other_prof_fees':None,'interest_exp':None,'taxes':None,
 'depreciation':None,'occupancy':None,'travel_conf':None,'printing_publications':None,'other_expenses':None,
 'total_operating':307822113,'grants_paid':15903064,'total_expenses':323725177,
 'excess_revenue':68408520,'net_investment_income':460637430,'adjusted_net_income':0,
 'total_disburse_charitable':238726771,'operating_disburse_charitable':None,
 'fmv_assets':13418017359,'total_assets_eoy':11002762921,'total_assets_boy':None,
 'total_liabilities_eoy':927412012,'net_assets_eoy':10075350909,
 'min_investment_return':360148962,'distributable_amount':None,'qualifying_distributions':None,
 'mortgages_payable':581125000,'source':'pp','tax_period_end':'2019-06-30'
}

years = []
for fy, d in xml.items():
    d = dict(d); d['fy'] = int(fy); d['source'] = 'xml'
    d.pop('officers', None)
    years.append(d)
fy2019['fy'] = 2019
years.append(fy2019)
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

print('ERRORS:', len(errors)); [print('  !!', e) for e in errors]
print('WARNINGS:', len(warns)); [print('  ~', w) for w in warns]
if errors: sys.exit(1)

# officers FY2024 (top by comp)
off = [o for o in xml['2024']['officers'] if o.get('comp') is not None]
off.sort(key=lambda o: -o['comp'])
officers2024 = off[:12]

PP = 'https://projects.propublica.org/nonprofits/download-filing?path='
archive = [
 {'fy':2001,'url':PP+'2002_03_PF%2F95-1790021_990PF_200106.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2002,'url':PP+'2003_06_PF%2F95-1790021_990PF_200206.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2003,'url':PP+'2004_06_PF%2F95-1790021_990PF_200306.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2004,'url':PP+'2005_06_PF%2F95-1790021_990PF_200406.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2005,'url':PP+'2007_01_PF%2F95-1790021_990PF_200506.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2006,'url':PP+'2007_06_PF%2F95-1790021_990PF_200606.pdf','tag':'scan — unverified','cls':'unv'},
 {'fy':2007,'url':PP+'2009_01_PF%2F95-1790021_990PF_200706.pdf','tag':'e-file text — extraction pending'},
 {'fy':2008,'url':PP+'2009_06_PF%2F95-1790021_990PF_200806.pdf','tag':'e-file text — extraction pending'},
 {'fy':2009,'url':PP+'2010_06_PF%2F95-1790021_990PF_200906.pdf','tag':'e-file text — extraction pending'},
 {'fy':2010,'url':PP+'2011_06_PF%2F95-1790021_990PF_201006.pdf','tag':'in dashboard (XML)'},
 {'fy':2011,'url':PP+'2012_07_PF%2F95-1790021_990PF_201106.pdf','tag':'in dashboard (XML)'},
 {'fy':2012,'url':PP+'2013_10_PF%2F95-1790021_990PF_201206.pdf','tag':'in dashboard (XML)'},
 {'fy':2013,'url':PP+'2014_07_PF%2F95-1790021_990PF_201306.pdf','tag':'in dashboard (XML)'},
 {'fy':2014,'url':PP+'2015_07_PF%2F95-1790021_990PF_201406.pdf','tag':'in dashboard (XML)'},
 {'fy':2015,'url':PP+'2016_07_PF%2F95-1790021_990PF_201506.pdf','tag':'in dashboard (XML)'},
 {'fy':2016,'url':PP+'IRS%2F951790021_201606_990PF_2017100214790468.pdf','tag':'in dashboard (XML)'},
 {'fy':2017,'url':PP+'05_2018_prefixes_94-99%2F951790021_201706_990PF_2018052915349719.pdf','tag':'in dashboard (XML)'},
 {'fy':2018,'url':PP+'06_2019_prefixes_88-95%2F951790021_201806_990PF_2019060716392273.pdf','tag':'in dashboard (XML)'},
 {'fy':2019,'url':PP+'download990pdf_10_2021_prefixes_84-99%2F951790021_201906_990PF_2021102019108054.pdf','tag':'in dashboard (IRS extract)'},
 {'fy':2020,'url':'https://projects.propublica.org/nonprofits/download-xml?object_id=202141379349101464','tag':'in dashboard (XML)'},
 {'fy':2021,'url':PP+'download990pdf_07_2022_prefixes_94-99%2F951790021_202106_990PF_2022071120198236.pdf','tag':'in dashboard (XML)'},
 {'fy':2022,'url':PP+'IRS%2F951790021_202206_990PF_2023060821406436.pdf','tag':'in dashboard (XML)'},
 {'fy':2023,'url':'https://projects.propublica.org/nonprofits/download-xml?object_id=202421359349106107','tag':'in dashboard (XML)'},
 {'fy':2024,'url':'https://projects.propublica.org/nonprofits/organizations/951790021/202531359349102323/full','tag':'in dashboard (XML)'},
]

data = {'years': years, 'officers2024': officers2024, 'archive': archive}
json.dump(data, open('dataset.json','w'), indent=1)

tpl = open('dashboard_template.html', encoding='utf-8').read()
html = tpl.replace('__DATA__', json.dumps(data, separators=(',',':')))
open('Getty_Trust_Financial_Dashboard.html','w',encoding='utf-8').write(html)
print('OK: dashboard written,', len(years), 'years,', len(officers2024), 'officers')
