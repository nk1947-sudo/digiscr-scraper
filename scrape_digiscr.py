import os
import time
import sqlite3
import requests
import pandas as pd
from bs4 import BeautifulSoup

BASE_URL = "https://digiscr.sci.gov.in"
SESSION_COOKIE = "788788c9ifpf1tgm12b2t56tac"  # Update if expired

HEADERS = {
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
    "Origin": BASE_URL,
    "Referer": f"{BASE_URL}/",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
    "sec-ch-ua": '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}

COOKIES = {
    "PHPSESSID": SESSION_COOKIE
}

def setup_db():
    conn = sqlite3.connect("cases.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year TEXT,
            volume_number TEXT,
            part_number TEXT,
            title TEXT,
            citations TEXT,
            pdf_link TEXT,
            case_type TEXT,
            date TEXT,
            volume TEXT,
            judges TEXT,
            html_link TEXT,
            flip_link TEXT,
            split_link TEXT,
            UNIQUE(year, volume_number, part_number, title)
        )
    ''')
    conn.commit()
    return conn, cursor

def parse_card(card):
    try:
        title = card.select_one(".cite-data a").get_text(strip=True)
        citation_tags = card.select(".cititaion span")
        citations = " | ".join(c.get_text(strip=True) for c in citation_tags)

        civil_meta = card.select_one(".civil").find_all("p")
        case_type = civil_meta[0].get_text(strip=True) if len(civil_meta) > 0 else ""
        date = civil_meta[1].get_text(strip=True) if len(civil_meta) > 1 else ""

        judges = card.select_one(".entryjudgment").get_text(strip=True) if card.select_one(".entryjudgment") else ""

        pdf_link = html_link = flip_link = split_link = None
        for a in card.select(".split a[href]"):
            href = a["href"]
            full_link = BASE_URL + "/" + href.lstrip("/")
            if "pdf" in href.lower():
                pdf_link = full_link
            elif "html" in href.lower():
                html_link = full_link
            elif "flip" in href.lower():
                flip_link = full_link
            elif "split" in href.lower():
                split_link = full_link

        return {
            "title": title,
            "citations": citations,
            "pdf_link": pdf_link,
            "case_type": case_type,
            "date": date,
            "volume": "",
            "judges": judges,
            "html_link": html_link,
            "flip_link": flip_link,
            "split_link": split_link,
        }
    except Exception as e:
        print("⚠️ Parse error:", e)
        return None

def download_pdf(url, title):
    if not url:
        return
    if not os.path.exists("pdfs"):
        os.makedirs("pdfs")
    safe_title = "".join(c if c.isalnum() else "_" for c in title)[:100]
    filename = f"pdfs/{safe_title}.pdf"
    try:
        r = requests.get(url, headers=HEADERS, cookies=COOKIES)
        r.raise_for_status()
        with open(filename, "wb") as f:
            f.write(r.content)
        print(f"📥 Downloaded PDF: {filename}")
    except Exception as e:
        print(f"❌ Failed PDF for {title}: {e}")

def fetch_cases(year, volume, part):
    url = f"{BASE_URL}/fetch_judgement_ajax"
    payload = {"year": year, "volume": volume, "partno": part}
    try:
        res = requests.post(url, data=payload, headers=HEADERS, cookies=COOKIES)
        res.raise_for_status()
        html = res.text

        debug_dir = "debug_html"
        os.makedirs(debug_dir, exist_ok=True)
        with open(f"{debug_dir}/debug_{year}_{volume}_{part}.html", "w", encoding="utf-8") as f:
            f.write(html)

        soup = BeautifulSoup(html, "html.parser")
        return soup.select("ul.linking-section > li.linumbr")
    except Exception as e:
        print(f"❌ Fetch error for {year} Vol {volume} Pt {part}: {e}")
        return []

def scrape_with_year(year):
    conn, cursor = setup_db()
    all_data = []

    volumes = [str(v) for v in range(1, 10)]
    parts = [str(p) for p in range(1, 6)]

    for vol in volumes:
        for part in parts:
            print(f"📥 Fetching Year {year} - Volume {vol} - Part {part}")
            cards = fetch_cases(year, vol, part)
            print(f"   ➤ Found {len(cards)} card blocks")

            for card in cards:
                case = parse_card(card)
                if not case:
                    continue

                case["year"] = year
                case["volume_number"] = vol
                case["part_number"] = part
                all_data.append(case)

                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO cases (
                            year, volume_number, part_number, title, citations, pdf_link, case_type, date, volume,
                            judges, html_link, flip_link, split_link)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        year, vol, part, case["title"], case["citations"], case["pdf_link"], case["case_type"],
                        case["date"], case["volume"], case["judges"], case["html_link"],
                        case["flip_link"], case["split_link"]
                    ))
                except Exception as e:
                    print(f"⚠️ DB insert error for {case['title']}: {e}")

                if case["pdf_link"]:
                    download_pdf(case["pdf_link"], case["title"])

    conn.commit()
    cursor.close()
    conn.close()
    return all_data

def save_csv(data):
    df = pd.DataFrame(data)
    file_exists = os.path.exists("cases.csv")
    if file_exists:
        df.to_csv("cases.csv", mode='a', index=False, header=False)
        print("✅ Appended to cases.csv")
    else:
        df.to_csv("cases.csv", index=False)
        print("✅ Created and saved to cases.csv")

def main():
    year = input("Enter the year to scrape: ").strip()
    if not year.isdigit() or len(year) != 4:
        print("❌ Invalid year entered. Please enter a 4-digit year.")
        return

    data = scrape_with_year(year)
    save_csv(data)

if __name__ == "__main__":
    main()
