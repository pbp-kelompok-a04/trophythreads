import csv

# Nama file sumber dan file hasil
input_file = 'InformasiPertandingan/data/matches.csv'           # ganti sesuai nama CSV kamu
output_file = 'InformasiPertandingan/data/indonesia_matches.csv'

# Buka file input dan output
with open(input_file, mode='r', encoding='utf-8') as infile, \
     open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
    
    reader = csv.DictReader(infile)
    fieldnames = reader.fieldnames  # ambil nama kolom dari file asli
    writer = csv.DictWriter(outfile, fieldnames=fieldnames)

    # tulis header ke file baru
    writer.writeheader()

    # loop tiap baris dan filter
    for row in reader:
        home_team = row['home_team'].strip().lower()
        away_team = row['away_team'].strip().lower()

        if 'indonesia' in home_team or 'indonesia' in away_team:
            writer.writerow(row)

print("✅ Data pertandingan Indonesia berhasil disimpan ke:", output_file)