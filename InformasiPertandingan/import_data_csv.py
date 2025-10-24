import os
import django
import random
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent # folder trophythreads/
APP_DIR = Path(__file__).resolve().parent # folder InformasiPertandingan
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trophythreads.settings') 

# set up
try:
    django.setup()
except Exception as e:
    print(f"EROR: Gagal setup Django. {e}")
    exit()

# import model
try:
    from InformasiPertandingan.models import Country, Informasi
except ImportError:
    print("ERROR: Gagal impor model 'Country' atau 'Informasi'.")
    exit()

COUNTRY_CSV_FILE = APP_DIR / 'data' / 'country.csv' #InformasiPertandingan/data/country.csv 
MATCHES_CSV_FILE = APP_DIR / 'data' / 'matches.csv' #InformasiPertandingan/data/matches.csv

DUMMY_COUNTRY_NAME = "Tim Tidak Diketahui" # tim yang country nya tidak ada di daftar country.csv
DUMMY_COUNTRY_FLAG = "/static/image/no-flag.png" # flag untuk unknown tim (bendera yang tidak diketahui)

# impor country.csv
def import_countries():
    Country.objects.get_or_create(
        name=DUMMY_COUNTRY_NAME,
        defaults={'flag': DUMMY_COUNTRY_FLAG}
    )

    # baca file dan impor negara
    try:
        # buat setiap country jika belum ada
        with open(COUNTRY_CSV_FILE, mode='r', encoding='utf-8') as f:
            next(f)  # skip header
            for line in f:
                line = line.strip()
                if not line:  # skip baris kosong
                    continue
                kata = line.split(',')

                if len(kata) != 2:
                    continue # skip baris tidak valid
                nama, flag = kata
                Country.objects.get_or_create(name=nama, defaults={'flag': flag})
    except FileNotFoundError:
        print(f"ERROR: File '{COUNTRY_CSV_FILE}' tidak ditemukan. Pastikan path sudah benar.")
        exit()
    except Exception as e:
        print(f"ERROR saat impor negara: {e}")
        exit()

def import_matches():
    # membaca file matches.csv
    try:
        with open(MATCHES_CSV_FILE, mode='r', encoding='utf-8') as f:
            lines = f.readlines()
            header = lines[0].strip().split(',')
            # membaca dari baris kedua (baris pertama header)
            for _, line in enumerate(lines[1:], start=2):
                kata = line.strip().split(',')
                # baris tidak lengkap / invalid
                if len(kata) < 9:
                    continue
                date_str, home_team, away_team, home_score, away_score, title, city, country, _ = kata
                
                # mencari country untuk home team, kalau tidak ada buat baru
                home_team_obj,_ = Country.objects.get_or_create(
                    name=home_team,
                    defaults={'flag': DUMMY_COUNTRY_FLAG}
                )

                # mencari country untuk away team
                away_team_obj,_ = Country.objects.get_or_create(
                    name=away_team,
                    defaults={'flag': DUMMY_COUNTRY_FLAG}
                )

                # membuat object Informasi bila belum ada sebelumnya
                Informasi.objects.get_or_create(
                    date=date_str,
                    home_team=home_team_obj,
                    away_team=away_team_obj,
                    defaults={
                        'title': title,
                        'city': city,
                        'country': country,
                        'score_home_team': int(home_score),
                        'score_away_team': int(away_score),
                        'views': random.randint(0, 50)
                    }
                )
    except FileNotFoundError:
        print(f"ERROR: File '{MATCHES_CSV_FILE}' tidak ditemukan. Pastikan path sudah benar.")
        exit()
    except Exception as e:
        print(f"ERROR saat impor pertandingan: {e}")
        exit()

if __name__ == "__main__":
    import_countries()
    import_matches()