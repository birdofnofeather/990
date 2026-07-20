# J. Paul Getty Trust — 990-PF Financial Dashboard

Interactive dashboard of the Getty Trust's IRS Form 990-PF filings, EIN 95-1790021,
fiscal years ending June 30, 2010–2024. Live at: https://birdofnofeather.github.io/990/

**Data sources (as-filed, verified only — no OCR):**
- IRS e-file XML via GivingTuesday 990 Data Lake (FY2010–2018, FY2020–2024)
- IRS-extracted structured data via ProPublica Nonprofit Explorer API (FY2019, paper-filed)

Every overlapping value is cross-checked between the two sources; year-over-year
balance-sheet chains are verified. FY2007–2009 (clean e-file text PDFs) pending
verified extraction; FY2001–2006 are scans and are linked but never charted.

`pipeline/` contains the extraction/verification/build scripts.
