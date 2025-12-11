# Confluence Finalized Definitions Scraper

A Python script that extracts **finalized concept definitions** from a Confluence HTML space export and converts them into a clean, structured **CSV**

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
