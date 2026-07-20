#!/usr/bin/env python3
"""Extract key figures from FY2007-2009 990-PF PDFs (IRS e-file text renders, not OCR).
Text extracted with pdftotext -layout; values parsed by regex anchored to IRS line labels."""
import re, json, subprocess

NUM = r'-?[\d][\d ,\.]*[\d]'

def clean(s):
    s = s.replace(' ', '').replace(',', '')
    # trailing period is a decimal artifact only in OCR files; these are clean, but strip trailing '.'
    s = s.rstrip('.')
    neg = s.startswith('-') or (s.startswith('(') and s.endswith(')'))
    s = s.strip('()-')
    if not s.replace('.','').isdigit():
        return None
    v = int(float(s))
    return -v if neg else v

def nums_after(text, label_re, count=1, window=300):
    m = re.search(label_re, text)
    if not m: return [None]*count
    seg = text[m.end():m.end()+window]
    found = re.findall(r'-?\d[\d,]{2,}\d', seg)
    vals = [clean(x) for x in found[:count]]
    while len(vals) < count: vals.append(None)
    return vals

def extract(path):
    txt = subprocess.run(['pdftotext','-layout',path,'-'],capture_output=True,text=True).stdout
    # normalize spaces inside numbers like "11,187,006 ,719" -> "11,187,006,719"
    txt = re.sub(r'(\d)\s*,\s*(\d)', r'\1,\2', txt)
    t = txt
    d = {}
    d['fmv_assets'] = nums_after(t, r'line 16\s*\)\s*[x]?\s*\$?', 1, 80)[0]
    d['contributions'] = nums_after(t, r'Contributions\s*,? gifts\s*,? grants\s*,? etc\s*,? received')[0]
    d['interest'] = nums_after(t, r'Interest on savings and temporary cash investments')[0]
    d['dividends'] = nums_after(t, r'Dividends and interest from securities')[0]
    d['gross_rents'] = nums_after(t, r'Gross rents')[0]
    d['net_gain_assets'] = nums_after(t, r'Net gain or \(loss ?\) from sale of assets not on line 10')[0]
    d['gross_profit'] = nums_after(t, r'Gross profit or \(loss ?\) \(attach schedule ?\)')[0]
    d['other_income'] = nums_after(t, r'Other income \(attach schedule ?\)')[0]
    d['total_revenue'] = nums_after(t, r'Total\s*\.? Add lines 1 through 11')[0]
    d['comp_officers'] = nums_after(t, r'Compensation of officers\s*,? directors\s*,? trustees')[0]
    d['other_salaries'] = nums_after(t, r'Other employee salaries and wages')[0]
    d['pension_benefits'] = nums_after(t, r'Pension plans\s*,? employee benefits')[0]
    d['legal_fees'] = nums_after(t, r'Legal fees \(attach schedule ?\)')[0]
    d['accounting_fees'] = nums_after(t, r'Accounting fees \(attach schedule ?\)')[0]
    d['other_prof_fees'] = nums_after(t, r'Other professional fees \(attach schedule ?\)')[0]
    d['interest_exp'] = nums_after(t, r'\n\s*17\s+Interest\b')[0]
    d['taxes'] = nums_after(t, r'Taxes \(attach schedule ?\)')[0]
    d['depreciation'] = nums_after(t, r'Depreciation \(attach schedule ?\)')[0]
    d['occupancy'] = nums_after(t, r'\n\s*20\s+Occupancy')[0]
    d['travel_conf'] = nums_after(t, r'Travel,? conferences\s*,? and meetings')[0]
    d['printing_publications'] = nums_after(t, r'Printing and publications')[0]
    d['other_expenses'] = nums_after(t, r'Other expenses \(attach schedule ?\)')[0]
    # total operating: number appears after "Add lines 13 through 23"
    d['total_operating'] = nums_after(t, r'Add lines 1 ?3 through 23')[0]
    d['grants_paid'] = nums_after(t, r'Contributions\s*,? gifts,? grants paid')[0]
    te = nums_after(t, r'Total expenses and disbursements\s*\.? Add lines 24 and 25', 4)
    d['total_expenses'] = te[0]
    d['total_disburse_charitable'] = te[3]
    d['net_investment_income'] = nums_after(t, r'Net investment income \( ?if negative\s*,? enter -0- ?\)')[0]
    d['adjusted_net_income'] = nums_after(t, r'Adjusted net income \( ?if negative,? enter -0- ?\)')[0]
    ta = nums_after(t, r'Total assets \( to be completed by all filers', 3, 400)
    d['total_assets_boy'], d['total_assets_eoy'], d['fmv_check'] = ta
    tl = nums_after(t, r'Total liabilities \( ?add lines 17 through 22\s*\)', 2)
    d['total_liabilities_eoy'] = tl[1]
    tn = nums_after(t, r'Total net assets or fund balances \( ?see', 2, 400)
    d['net_assets_boy'], d['net_assets_eoy'] = tn
    mg = nums_after(t, r'Mortgages and other notes payable \( ?attach schedule ?\)', 2)
    d['mortgages_payable'] = mg[1]
    d['qualifying_distributions'] = nums_after(t, r'Qualifying distributions\s*\.? Add lines l?1?a through 3b', 2, 700)
    # last number on that line is the value; take max index non-null
    qd = [x for x in d['qualifying_distributions'] if x is not None]
    d['qualifying_distributions'] = qd[-1] if qd else None
    d['min_investment_return'] = nums_after(t, r'Minimum investment return', 1, 200)[0]
    # Part XIV: qualifying distributions for current + 3 prior years + total
    d['qd_partxiv_row'] = nums_after(t, r'Qualifying distributions from Part\s*\n?\s*XII,?\s*\n?\s*line 4 for each year listed', 5, 400)
    return d

out = {}
for fy, path in [('2007','pdf/fy200706.pdf'),('2008','pdf/fy200806.pdf'),('2009','pdf/fy2009.pdf')]:
    out[fy] = extract(path)

print(json.dumps(out, indent=1))
with open('parsed_pdf.json','w') as f:
    json.dump(out, f, indent=1)
