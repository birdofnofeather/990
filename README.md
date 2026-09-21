# J. Paul Getty Trust — 990-PF Financial Dashboard

Interactive dashboard of the Getty Trust's IRS Form 990-PF filings, EIN 95-1790021,
fiscal years ending June 30, 2007–2025. Live at: https://birdofnofeather.github.io/990/

**Data sources (as-filed, verified only — no OCR):**
- IRS e-file XML via GivingTuesday 990 Data Lake (FY2010–2018, FY2020–2023)
- IRS e-file XML direct from the IRS TEOS bulk releases at
  `apps.irs.gov/pub/epostcard/990/xml/<year>/` (FY2024–2025). ProPublica's
  `download-xml` endpoint now sits behind a bot check, so the filing is located by EIN in
  that year's `index_<year>.csv`, and the single `<object_id>_public.xml` member is pulled
  out of the batch zip. Those zips use Deflate64, which Python's stdlib `zipfile` cannot
  decompress — `pip install zipfile-deflate64` first.
- IRS-extracted structured data via ProPublica Nonprofit Explorer API (FY2019, paper-filed)

Every overlapping value is cross-checked between the two sources; year-over-year
balance-sheet chains are verified. FY2024 and FY2025 predate ProPublica's summary-data
extract, so they are instead checked against the as-filed XML's own printed subtotals
(revenue lines 1–11 = line 12, expense lines 13–23 = line 24, 24 + 25 = 26,
revenue − expenses = line 27a, assets − liabilities = net assets) and against the
balance-sheet chain. FY2001–2006 are scans and are linked but never charted.

`pipeline/` contains the extraction/verification/build scripts. `build_dashboard.py`
exits non-zero if any verification check fails.

**Latest filing tracked:** FY2025 (FYE 2025-06-30), IRS object_id 202611279349102996,
filed 2026-05-07.
