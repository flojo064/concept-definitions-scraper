# Confluence Finalized Definitions Scraper

A Python script that extracts **finalized concept definitions** from a Confluence HTML space export and converts them into a clean, structured **CSV** for downstream use (data catalogs, governance tools, audits, etc.).

This tool is purpose-built for Confluence spaces that use **Page Status** to control content lifecycle and ensures that **only approved (“Confluence Page Finalized”) pages** are exported.

---

## Features

- ✅ Parses Confluence **HTML space exports**
- ✅ Filters pages by **Page Status = Confluence Page Finalized**
- ✅ Extracts clean, **plain-text definitions** (HTML removed)
- ✅ Pulls resource links from:
  - Definition Logic  
  - Related Codesets  
  - References
- ✅ Detects and logs invalid links:
  - Local or internal files  
  - Broken URLs  
  - Link text that matches the URL
- ✅ Outputs CSV files ready for ingestion

---

## Output Files

The script produces two CSV files:

### `scraped-finalized-definitions.csv`
Main output containing finalized definitions in a structured format.

### `invalid-links.csv`
Log of detected link issues, including:
- Page name
- Link text
- URL
- Location (Description or Resources)
- Issue type

---

## How It Works

1. Reads each HTML file from the Confluence export `/CD` directory  
2. Detects **Page Status** using multiple fallback strategies (handles different export layouts)  
3. Skips all pages not marked as **Confluence Page Finalized**  
4. Extracts and cleans definition text  
5. Writes results directly to CSV  

---

## Requirements

- Python 3.8+
- `beautifulsoup4`

Install dependencies:

```bash
pip install beautifulsoup4
```bash
pip install beautifulsoup4
