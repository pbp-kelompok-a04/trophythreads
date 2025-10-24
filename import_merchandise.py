import os
import django
import sys

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trophythreads.settings') 
django.setup()

import csv
from merchandiseApp.models import Merchandise
from main.models import Profile
from django.contrib.auth.models import User

def import_merchandise_data(csv_file_path):
    print("Memulai import data merchandise...")
    
    try:
        profile = Profile.objects.filter(role__in=['admin', 'seller']).first()
        if not profile:
            user, created = User.objects.get_or_create(
                username='merchandise_seller',
                defaults={
                    'email': 'seller@example.com',
                    'first_name': 'Merchandise',
                    'last_name': 'Seller'
                }
            )
            if created:
                user.set_password('password123')
                user.save()
            
            profile = Profile.objects.create(user=user, role='seller')
            print(f"Created default seller profile: {profile}")
    except Exception as e:
        print(f"Error getting profile: {e}")
        return

    success_count = 0
    error_count = 0

    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row_num, row in enumerate(reader, 2):
            try:
                name = row['name'].strip()
                price = int(row['price']) if row['price'].strip() else 0
                category = row['category'].strip().lower()
                stock = int(row['stock']) if row['stock'].strip() else 0
                thumbnail = row['thumbnail'].strip()
                description = row['description'].strip()

                if not name:
                    print(f"Row {row_num}: Skip - Nama kosong")
                    error_count += 1
                    continue

                # Cek duplikat
                if Merchandise.objects.filter(name=name).exists():
                    print(f"Row {row_num}: Skip - '{name}' sudah ada")
                    error_count += 1
                    continue

                # Buat merchandise
                merchandise = Merchandise(
                    user=profile,
                    name=name,
                    price=price,
                    category=category,
                    stock=stock,
                    thumbnail=thumbnail if thumbnail else None,
                    description=description
                )
                
                merchandise.save()
                success_count += 1
                print(f"✓ Row {row_num}: '{name}' - Rp{price:,}")

            except Exception as e:
                print(f"✗ Row {row_num}: Error - {e}")
                error_count += 1

    print(f"\n✅ Import selesai! Berhasil: {success_count}, Gagal: {error_count}")

if __name__ == '__main__':
    csv_file_path = 'merchandise.csv' 
    import_merchandise_data(csv_file_path)