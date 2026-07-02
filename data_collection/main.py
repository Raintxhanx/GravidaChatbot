import csv
import time
import requests
from bs4 import BeautifulSoup

def scrape_alodokter_topics(max_pages=20, output_file="alodokter_kehamilan_links.csv"):
    base_url = "https://www.alodokter.com/komunitas/topic-tag/kehamilan"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # Siapkan file CSV
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        # Menulis header CSV
        writer.writerow(["title", "href", "full_url"])
        
        print(head := f"=== START SCRAPING ALODOKTER (1 - {max_pages} Pages) ===")
        
        for page in range(1, max_pages + 1):
            # Handle URL untuk page 1 dan seterusnya
            if page == 1:
                url = base_url
            else:
                url = f"{base_url}/page/{page}"
                
            print(f"Scraping Page {page}: {url} ...")
            
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code != 200:
                    print(f"[Warning] Gagal akses page {page}. Status Code: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Cari semua custom tag <card-topic> di dalam #topic-list
                topic_list_div = soup.find(id="topic-list")
                if not topic_list_div:
                    print(f"[Warning] '#topic-list' tidak ditemukan di page {page}")
                    continue
                    
                card_topics = topic_list_div.find_all("card-topic")
                
                if not card_topics:
                    print(f"[Info] Tidak ada data lagi di page {page}. Proses dihentikan.")
                    break
                
                rows_written = 0
                for card in card_topics:
                    # Mengambil data langsung dari attribute custom element
                    title = card.get("title", "").strip()
                    href = card.get("href", "").strip()
                    
                    if href:
                        full_url = f"https://www.alodokter.com{href}"
                        writer.writerow([title, href, full_url])
                        rows_written += 1
                
                print(f"[Success] Berhasil menyimpan {rows_written} topik dari page {page}.")
                
                # Antisipasi rate limiting (Sopan santun scraping)
                time.sleep(2)
                
            except Exception as e:
                print(f"[Error] Terjadi kesalahan pada page {page}: {str(e)}")
                
    print(f"\n=== SCRAPING SELESAI. Data disimpan di '{output_file}' ===")

if __name__ == "__main__":
    scrape_alodokter_topics(max_pages=20)