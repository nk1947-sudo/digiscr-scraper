# DigiSCR Scraper

A Python scraper for the Digital Supreme Court Reports (DigiSCR) portal.

## Features

- Scrapes case details including titles, citations, and links
- Downloads associated PDF documents
- Stores data in both SQLite database and CSV format
- Handles pagination and error recovery

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/digiscr-scraper.git
cd digiscr-scraper
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
- Copy `.env.example` to `.env`
- Update the `SESSION_COOKIE` value in `.env`

## Usage

Run the scraper:
```bash
python scrape_digiscr.py
```

When prompted, enter the year you want to scrape (e.g., 2023).

## Output

- `cases.db`: SQLite database containing all scraped data
- `cases.csv`: CSV export of scraped data
- `pdfs/`: Directory containing downloaded PDF files
- `debug_html/`: Directory containing debug HTML files

## Data Structure

The scraper collects the following information:
- Year
- Volume Number
- Part Number
- Case Title
- Citations
- PDF Link
- Case Type
- Date
- Volume
- Judges
- HTML Link
- Flip Link
- Split Link

## License

MIT License - See LICENSE file for details