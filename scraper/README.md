# Recipe Scraper

Python-based scraper for extracting HelloFresh recipes from archive.org's Wayback Machine.

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python scrape.py --region en-US --max-recipes 1000
```

## Configuration

Edit `config.yaml` to customize:
- Wayback Machine snapshot date
- Rate limiting (be respectful!)
- Region selection
- Output database path
