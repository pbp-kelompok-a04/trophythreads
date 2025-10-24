#!/usr/bin/env python3
"""
Import favorites from CSV, buat placeholder Merchandise bila perlu,
dan pastikan created_at disimpan sebagai timezone-aware datetime
(untuk project dengan USE_TZ = True).

Expected CSV header: id,user,merchandise,created_at
Put the CSV file next to this script or set CSV_FILE path below.
"""
import os
import django
import random
import uuid
from pathlib import Path
import sys
from datetime import datetime

# ----- CONFIG: sesuaikan jika perlu -----
BASE_DIR = Path(__file__).resolve().parent.parent  # project root (trophythreads/)
APP_DIR = Path(__file__).resolve().parent  # folder script berada
CSV_FILE = APP_DIR / 'favorites_timnas.csv'  # expected CSV path (change if needed)
DJANGO_SETTINGS = 'trophythreads.settings'
DATE_FORMATS = ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S']
# ----------------------------------------

# setup path & django
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', DJANGO_SETTINGS)

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Gagal setup Django. {e}")
    sys.exit(1)

# imports that require Django setup
from django.conf import settings
from django.utils import timezone

try:
    from django.contrib.auth import get_user_model
    from favoritesApp.models import Favorite
    from merchandiseApp.models import Merchandise
except Exception as e:
    print(f"ERROR: Gagal impor model. {e}")
    sys.exit(1)

User = get_user_model()


def parse_datetime(dt_str):
    if not dt_str:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(dt_str, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def make_aware_if_needed(dt):
    """Convert naive datetime to aware using current timezone if USE_TZ=True."""
    if not dt:
        return None
    try:
        if getattr(settings, 'USE_TZ', False) and dt.tzinfo is None:
            tz = timezone.get_current_timezone()
            return timezone.make_aware(dt, tz)
    except Exception:
        pass
    return dt


def get_or_create_user(username):
    if not username:
        return None
    try:
        user, created = User.objects.get_or_create(username=username)
        if created:
            try:
                user.set_unusable_password()
                user.save()
            except Exception:
                # ignore save issues for custom user models
                pass
        return user
    except Exception as e:
        print(f"[WARN] Gagal mendapatkan/membuat user '{username}': {e}")
        return None


def create_placeholder_merchandise(name):
    """
    Buat Merchandise placeholder dengan beberapa field safe.
    Isi beberapa field umum: name, price, stock, thumbnail jika tersedia.
    """
    if not name:
        return None
    name = name.strip()
    # try find first
    try:
        m = Merchandise.objects.filter(name__iexact=name).first()
        if m:
            return m
        m = Merchandise.objects.filter(name__icontains=name).first()
        if m:
            return m
    except Exception:
        pass

    # prepare kwargs depending on model fields
    create_kwargs = {'name': name}
    try:
        field_names = [f.name for f in Merchandise._meta.get_fields()]
    except Exception:
        field_names = []

    # sensible defaults
    if 'price' in field_names:
        create_kwargs['price'] = random.randint(50000, 350000)
    if 'stock' in field_names:
        create_kwargs['stock'] = random.randint(1, 100)
    if 'thumbnail' in field_names:
        create_kwargs['thumbnail'] = '/static/image/no-thumbnail.png'

    try:
        merch = Merchandise.objects.create(**create_kwargs)
        print(f"[MERCH CREATED] {merch.pk} - {merch.name}")
        return merch
    except Exception as e:
        print(f"[WARN] Gagal membuat placeholder Merchandise '{name}': {e}")
        return None


def import_favorites_from_csv(csv_path):
    if not csv_path.exists():
        print(f"ERROR: File '{csv_path}' tidak ditemukan. Pastikan path benar.")
        return

    created = 0
    skipped = 0
    updated_created_at = 0

    with open(csv_path, mode='r', encoding='utf-8') as f:
        header = f.readline().strip().split(',')
        header = [h.strip().lower() for h in header]
        for lineno, raw in enumerate(f, start=2):
            line = raw.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(',')]
            if len(parts) < 2:
                print(f"[SKIP] baris {lineno}: format tidak lengkap -> {line}")
                skipped += 1
                continue

            row = {}
            for i, col in enumerate(header):
                row[col] = parts[i] if i < len(parts) else ''

            user_name = row.get('user') or row.get('username') or ''
            merch_val = row.get('merchandise') or row.get('merch') or ''
            id_val = row.get('id') or ''
            created_at_val = row.get('created_at') or row.get('created') or ''

            # user
            user_obj = get_or_create_user(user_name)
            if user_obj is None:
                print(f"[SKIP] baris {lineno}: user '{user_name}' tidak dapat dibuat/ditemukan.")
                skipped += 1
                continue

            # merchandise: try pk -> name -> create placeholder
            merch_obj = None
            if merch_val:
                try:
                    possible_uuid = uuid.UUID(merch_val)
                    merch_obj = Merchandise.objects.filter(pk=possible_uuid).first()
                except Exception:
                    merch_obj = None

            if merch_obj is None:
                try:
                    merch_obj = Merchandise.objects.filter(name__iexact=merch_val).first()
                except Exception:
                    merch_obj = None

            if merch_obj is None:
                merch_obj = create_placeholder_merchandise(merch_val)
                if merch_obj is None:
                    print(f"[SKIP] baris {lineno}: gagal membuat/menemukan merchandise untuk '{merch_val}'.")
                    skipped += 1
                    continue

            # prepare favorite id (optional)
            fav_uuid = None
            if id_val:
                try:
                    fav_uuid = uuid.UUID(id_val)
                except Exception:
                    fav_uuid = None

            # create or get favorite
            try:
                fav_kwargs = {'user': user_obj, 'merchandise': merch_obj}
                favorite, created_new = Favorite.objects.get_or_create(**fav_kwargs, defaults={})
                # try set id if provided and we just created the instance
                if created_new and fav_uuid:
                    try:
                        Favorite.objects.filter(pk=favorite.pk).update(id=str(fav_uuid))
                        favorite = Favorite.objects.get(pk=str(fav_uuid))
                    except Exception:
                        pass

                # set created_at if provided (make aware if needed)
                if created_at_val:
                    dt = parse_datetime(created_at_val)
                    if dt:
                        dt = make_aware_if_needed(dt)
                        try:
                            Favorite.objects.filter(pk=favorite.pk).update(created_at=dt)
                            updated_created_at += 1
                        except Exception:
                            pass

                if created_new:
                    created += 1
                    print(f"[CREATED] baris {lineno}: Favorite {favorite.pk} (user={user_name}, merch={merch_obj.name})")
                else:
                    print(f"[EXIST] baris {lineno}: Favorite sudah ada (user={user_name}, merch={merch_obj.name})")
            except Exception as e:
                print(f"[ERROR] baris {lineno}: gagal membuat Favorite untuk user={user_name}, merch={merch_val}: {e}")
                skipped += 1
                continue

    print("=== Summary ===")
    print(f"Favorites created: {created}")
    print(f"Favorites updated created_at: {updated_created_at}")
    print(f"Skipped/Failed: {skipped}")


if __name__ == "__main__":
    import_favorites_from_csv(CSV_FILE)
