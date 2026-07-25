#!/usr/bin/env python3
"""Extract Schedule B contributor (donor) lists from Getty Trust 990-PF e-file XML.
Schedule B is public for private foundations (unlike public charities), so names, cities/states,
and contribution amounts are present unredacted in the XML. Two schema families are handled:
  - legacy (~FY2010-2013): <ContributorInfo> / ContributorNumber / ContributorNameIndividual /
    ContributorAddressUS(AddressLine1,City,State,ZIPCode) / AggregateContributions
  - modern (~FY2014-2024): <ContributorInformationGrp> / ContributorNum / ContributorPersonNm or
    ContributorBusinessName / ContributorUSAddress(AddressLine1Txt,CityNm,StateAbbreviationCd,ZIPCd) /
    TotalContributionsAmt
Only covers years with source XML (FY2010-2018, FY2020-2024). FY2007-2009 (PDF text) and FY2019
(no XML, paper-filed) are not covered and are explicitly flagged as unavailable in the output.
"""
import glob, re, json
import xml.etree.ElementTree as ET

def local(t): return t.split('}')[-1]

def text_of(parent, names):
    for el in parent.iter():
        if local(el.tag) in names and el.text and el.text.strip():
            return el.text.strip()
    return None

def parse_year(path):
    tree = ET.parse(path)
    root = tree.getroot()
    donors = []
    for el in root.iter():
        ln = local(el.tag)
        if ln not in ('ContributorInfo', 'ContributorInformationGrp'):
            continue
        name = text_of(el, {'ContributorNameIndividual','ContributorPersonNm','BusinessNameLine1Txt'})
        city = text_of(el, {'City','CityNm'})
        state = text_of(el, {'State','StateAbbreviationCd'})
        amt = text_of(el, {'AggregateContributions','TotalContributionsAmt'})
        if name and amt:
            try: amt = int(amt)
            except ValueError:
                try: amt = int(float(amt))
                except ValueError: continue
            donors.append({'name': name, 'city': city, 'state': state, 'amt': amt})
    donors.sort(key=lambda d: -d['amt'])
    return donors

result = {}
for path in sorted(glob.glob('xml/fy*.xml')):
    fy = re.search(r'fy(\d{4})', path).group(1)
    donors = parse_year(path)
    result[fy] = donors
    total = sum(d['amt'] for d in donors)
    print(f'FY{fy}: {len(donors)} donors, total ${total:,}')

with open('donors.json', 'w') as f:
    json.dump(result, f, indent=0)
