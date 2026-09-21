#!/usr/bin/env python3
"""Fetch a Getty Trust 990-PF e-file XML straight from the IRS TEOS bulk releases.

ProPublica's /nonprofits/download-xml endpoint now answers with a bot-check page (HTTP 403),
and the old s3://irs-form-990 mirror stops at the pre-October-2021 releases, so recent filings
are pulled from the IRS's own bulk zips instead:

  https://apps.irs.gov/pub/epostcard/990/xml/<year>/index_<year>.csv   -- EIN -> OBJECT_ID
  https://apps.irs.gov/pub/epostcard/990/xml/<year>/<year>_TEOS_XML_NNx.zip

<year> is the IRS *release* year, not the fiscal year: a FYE-June-2025 return filed in
May 2026 lives in the 2026 release. The zips run 0.5 GB+, so rather than downloading one
whole, this walks the zip's central directory over HTTP range requests and inflates only
the single member wanted. The index's XML_BATCH_ID column is not always the zip the member
actually landed in, so candidate zips are probed in order until one holds it.

IRS bulk zips are written with Deflate64 (compression method 9), which the stdlib zipfile
cannot inflate:  pip install zipfile-deflate64

Usage:
    python3 fetch_irs_xml.py <release_year> <ein> [fiscal_year_label]
    python3 fetch_irs_xml.py 2026 951790021 2025      -> xml/fy2025.xml
"""
import io
import os
import re
import ssl
import sys
import csv
import urllib.request

import zipfile_deflate64  # noqa: F401  -- registers Deflate64 with zipfile
import zipfile

BASE = 'https://apps.irs.gov/pub/epostcard/990/xml'

_ctx = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt') \
    if os.path.exists('/root/.ccr/ca-bundle.crt') else ssl.create_default_context()
_handlers = [urllib.request.HTTPSHandler(context=_ctx)]
_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
if _proxy:
    _handlers.append(urllib.request.ProxyHandler({'https': _proxy, 'http': _proxy}))
_opener = urllib.request.build_opener(*_handlers)


class HttpFile(io.RawIOBase):
    """Seekable read-only file over HTTP range requests, so zipfile can read a remote zip."""

    def __init__(self, url):
        self.url = url
        self.pos = 0
        head = _opener.open(urllib.request.Request(url, method='HEAD'))
        self.size = int(head.headers['Content-Length'])

    def seekable(self): return True
    def readable(self): return True
    def tell(self): return self.pos

    def seek(self, off, whence=0):
        self.pos = off if whence == 0 else (self.pos + off if whence == 1 else self.size + off)
        return self.pos

    def readinto(self, buf):
        data = self.read(len(buf))
        buf[:len(data)] = data
        return len(data)

    def read(self, n=-1):
        if n is None or n < 0:
            n = self.size - self.pos
        if n == 0 or self.pos >= self.size:
            return b''
        end = min(self.pos + n, self.size) - 1
        req = urllib.request.Request(self.url, headers={'Range': f'bytes={self.pos}-{end}'})
        data = _opener.open(req).read()
        self.pos += len(data)
        return data


def find_filing(release_year, ein, return_type='990PF'):
    """Return (object_id, tax_period, batch_id) rows for this EIN in the release-year index."""
    url = f'{BASE}/{release_year}/index_{release_year}.csv'
    print(f'reading {url} ...', file=sys.stderr)
    text = _opener.open(url).read().decode('utf-8', 'replace')
    hits = []
    for row in csv.DictReader(io.StringIO(text)):
        if row['EIN'] == ein and row['RETURN_TYPE'] == return_type:
            hits.append((row['OBJECT_ID'], row['TAX_PERIOD'], row['XML_BATCH_ID']))
    return hits


def zip_candidates(release_year, batch_id):
    """Zip URLs to probe, starting with the batch the index names."""
    listing = _opener.open('https://www.irs.gov/charities-non-profits/form-990-series-downloads').read().decode('utf-8', 'replace')
    urls = sorted(set(re.findall(rf'{BASE}/{release_year}/[^"\']+\.zip', listing)))
    named = [u for u in urls if batch_id and u.endswith(f'{batch_id}.zip')]
    return named + [u for u in urls if u not in named]


def extract(object_id, urls, out_path):
    member = f'{object_id}_public.xml'
    for url in urls:
        zf = zipfile.ZipFile(io.BufferedReader(HttpFile(url), buffer_size=1 << 16))
        names = zf.namelist()
        print(f'  {url.rsplit("/", 1)[-1]}: {len(names)} members '
              f'({names[0]} .. {names[-1]})', file=sys.stderr)
        if member in names:
            os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
            with open(out_path, 'wb') as fh:
                fh.write(zf.read(member))
            print(f'wrote {out_path}', file=sys.stderr)
            return True
    return False


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    release_year, ein = sys.argv[1], sys.argv[2]
    hits = find_filing(release_year, ein)
    if not hits:
        sys.exit(f'no 990PF for EIN {ein} in the {release_year} release index')
    for object_id, tax_period, batch_id in hits:
        print(f'found object_id={object_id} tax_period={tax_period} batch={batch_id}', file=sys.stderr)
        label = sys.argv[3] if len(sys.argv) > 3 else tax_period[:4]
        out = os.path.join('xml', f'fy{label}.xml')
        if not extract(object_id, zip_candidates(release_year, batch_id), out):
            sys.exit(f'{object_id}_public.xml not found in any {release_year} zip')


if __name__ == '__main__':
    main()
