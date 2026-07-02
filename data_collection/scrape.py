import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import json

def extract_text_from_encoded_html(raw_string):
    """
    Fungsi untuk men-decode JSON string dan membersihkan tag HTML 
    agar menjadi plain text yang rapi.
    """
    if not raw_string:
        return ""
    try:
        # Decode JSON string (contoh: '"<p>teks</p>"' menjadi '<p>teks</p>')
        html_content = json.loads(raw_string)
        
        # Parsing HTML dan ambil teksnya
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup.get_text(separator='\n', strip=True)
    except Exception:
        # Fallback jika terjadi error parsing
        return raw_string

def scrape_alodokter_topic(url, headers):
    """
    Fungsi khusus untuk melakukan ekstraksi komponen dari satu URL.
    Mengembalikan dictionary berisi topic, pertanyaan, dan doctorContainer.
    """
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"Gagal mengambil data dari {url} (Status: {response.status_code})")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 1. & 2. Mengambil Topik dan Pertanyaan dari tag <detail-topic>
    detail_topic = soup.find('detail-topic')
    topic = detail_topic.get('member-topic-title', '') if detail_topic else ''
    
    raw_question = detail_topic.get('member-topic-content', '') if detail_topic else ''
    question = extract_text_from_encoded_html(raw_question)
    
    # 3. Mengambil Jawaban Dokter dari tag <doctor-topic>
    doctor_topic = soup.find('doctor-topic')
    raw_answer = doctor_topic.get('doctor-topic-content', '') if doctor_topic else ''
    answer = extract_text_from_encoded_html(raw_answer)
    
    return {
        "topic": topic,
        "pertanyaan": question,
        "doctorContainer": {
            "jawaban": answer
        }
    }

def run_scraper(csv_file_path, output_json_path):
    """
    Fungsi utama (Application Layer) untuk membaca CSV, melakukan loop 
    dengan jeda 5 detik, dan menyimpan hasilnya.
    """
    print(f"Membaca file {csv_file_path}...")
    df = pd.read_csv(csv_file_path)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    scraped_results = []

    for index, row in df.iterrows():
        url = row['full_url']
        print(f"[{index + 1}/{len(df)}] Scraping: {url}")
        
        try:
            data = scrape_alodokter_topic(url, headers)
            if data:
                # Tambahkan URL ke hasil untuk tracking
                data['url'] = url
                scraped_results.append(data)
        except Exception as e:
            print(f"Terjadi error saat scraping {url}: {e}")
            
        # Jeda 5 detik setiap request sesuai kebutuhan
        print("Menunggu 5 detik sebelum request berikutnya...\n")
        time.sleep(5)
        
    # Menyimpan hasil akhir ke dalam file JSON
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(scraped_results, f, ensure_ascii=False, indent=4)
        
    print(f"Scraping selesai! Data berhasil disimpan di {output_json_path}")

# --- Entry Point ---
if __name__ == "__main__":
    INPUT_CSV = "alodokter_kehamilan_links.csv"
    OUTPUT_JSON = "hasil_scraping_alodokter.json"
    
    run_scraper(INPUT_CSV, OUTPUT_JSON)