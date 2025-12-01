import os
import sys
import django
import csv
import uuid
from datetime import datetime
from django.db import transaction
from django.conf import settings

# === Setup Django ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # folder project
APP_DIR = os.path.dirname(os.path.abspath(__file__))  # folder app (reviewproduct)

# Tambahkan root project ke sys.path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Tentukan setting Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trophythreads.settings')

# Inisialisasi Django
try:
    django.setup()
except Exception as e:
    print(f"❌ Gagal setup Django: {e}")
    sys.exit(1)

# === Import Model ==
try:
    from django.contrib.auth.models import User
    from merchandiseApp.models import Merchandise
    from reviewproduct.models import Review
except ImportError as e:
    print(f"❌ Gagal import model: {e}")
    sys.exit(1)

# === Lokasi file CSV ===
REVIEW_CSV_FILE = os.path.join(APP_DIR, "reviews_data.csv")


def import_reviews():
    """Import data review dari CSV ke database Django."""
    if not os.path.exists(REVIEW_CSV_FILE):
        print(f"❌ File CSV tidak ditemukan di: {REVIEW_CSV_FILE}")
        sys.exit(1)

    # --- Siapkan user ---
    usernames = set()
    with open(REVIEW_CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            usernames.add(row["user_username"].strip())

    users_map = {}
    for username in usernames:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"password": settings.SECRET_KEY[:16], "is_active": True},
        )
        users_map[username] = user

    # --- Siapkan review ---
    review_objects = []
    with open(REVIEW_CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            merchandise_name = row["merchandise_name"].strip()
            user = users_map.get(row["user_username"].strip())

            try:
                merchandise = Merchandise.objects.get(name=merchandise_name)
            except Merchandise.DoesNotExist:
                print(f"⚠️ Merchandise '{merchandise_name}' tidak ditemukan.")
                continue

            try:
                created_at = datetime.strptime(row["created_at"], "%Y-%m-%d")
            except Exception:
                created_at = datetime.now()

            review_objects.append(
                Review(
                    id=uuid.uuid4(),
                    product=merchandise,
                    user=user,
                    rating=int(row["rating"]),
                    body=row["body"].strip(),
                    created_at=created_at,
                    updated_at=created_at,
                    deleted=False,
                )
            )

    # --- Bulk insert ke database ---
    with transaction.atomic():
        Review.objects.bulk_create(review_objects, ignore_conflicts=True)

    print(f"✅ Import selesai — {len(review_objects)} review berhasil ditambahkan.")


if __name__ == "__main__":
    import_reviews()
