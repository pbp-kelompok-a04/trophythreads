import os
import sys
import django
import csv
import uuid
from pathlib import Path
from datetime import datetime
from django.conf import settings
from django.db import transaction

# === Setup Django ===
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = Path(__file__).resolve().parent

sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "trophythreads.settings")

try:
    django.setup()
except Exception as e:
    sys.exit(1)

try:
    from django.contrib.auth.models import User
    from merchandiseApp.models import Merchandise
    from reviewproduct.models import Review
except ImportError:
    sys.exit(1)


# === Lokasi File CSV ===
REVIEW_CSV_FILE = APP_DIR / "reviews_data.csv"


def import_reviews():
    """Import data review dari CSV ke database."""
    if not REVIEW_CSV_FILE.exists():
        sys.exit(1)


    usernames = set()
    with open(REVIEW_CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            usernames.add(row["user_username"])

    # Buat user jika belum ada
    users_map = {}
    for username in usernames:
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"password": settings.SECRET_KEY[:16], "is_active": True},
        )
        users_map[username] = user

    review_objects = []
    with open(REVIEW_CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            merchandise_name = row["merchandise_name"].strip()
            user = users_map.get(row["user_username"])

            try:
                merchandise = Merchandise.objects.get(name=merchandise_name)
            except Merchandise.DoesNotExist:
                continue

            try:
                created_at = datetime.strptime(row["created_at"], "%Y-%m-%d")
            except Exception:
                created_at = datetime.now()

            review = Review(
                id=uuid.uuid4(),
                product=merchandise,
                user=user,
                rating=int(row["rating"]),
                body=row["body"].strip(),
                created_at=created_at,
                updated_at=created_at,
                deleted=False,
            )
            review_objects.append(review)


    with transaction.atomic():
        Review.objects.bulk_create(review_objects, ignore_conflicts=True)


if __name__ == "__main__":
    import_reviews()
    print("✅ Import dataset review selesai.")
