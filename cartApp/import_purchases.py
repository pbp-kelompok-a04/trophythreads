import os
import django
import csv
import uuid
from pathlib import Path
import sys

# ---- sesuaikan jika perlu ----
BASE_DIR = Path(__file__).resolve().parent.parent   # asumsi: project root (folder yang berisi manage.py)
APP_DIR = Path(__file__).resolve().parent            # asumsi: file ini berada di dalam app (mis. cartApp/)
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trophythreads.settings')
# ------------------------------

# set up Django
try:
    django.setup()
except Exception as e:
    print(f"ERROR: Gagal setup Django. {e}")
    exit(1)

# import model (sesuaikan app / model jika lokasi berbeda)
try:
    from cartApp.models import Purchase
    from django.contrib.auth import get_user_model
    from merchandiseApp.models import Merchandise
except ImportError as e:
    print(f"ERROR: Gagal impor model. {e}")
    exit(1)

User = get_user_model()

# path CSV (sesuaikan)
PURCHASES_CSV_FILE = APP_DIR / "purchases.csv"  # contoh: cartApp/data/purchases.csv

# helper untuk konversi
def parse_int(val, default=0):
    try:
        if val is None or val == "":
            return default
        return int(float(val))
    except Exception:
        return default

def parse_uuid(val):
    try:
        return uuid.UUID(val)
    except Exception:
        return None

def get_user_by_id(uid):
    if uid in (None, "", "None"):
        return None
    try:
        # csv mungkin berisi string; coba konversi ke int dulu
        pk = int(uid)
        return User.objects.filter(pk=pk).first()
    except Exception:
        return None

def get_product_by_id(pid):
    if pid in (None, "", "None"):
        return None
    try:
        pk = int(pid)
        return Merchandise.objects.filter(pk=pk).first()
    except Exception:
        return None

def import_purchases(dry_run=False):
    created = 0
    updated = 0
    skipped = 0

    if not PURCHASES_CSV_FILE.exists():
        print(f"ERROR: File '{PURCHASES_CSV_FILE}' tidak ditemukan. Pastikan path benar.")
        exit(1)

    with open(PURCHASES_CSV_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            # harapkan header seperti: order_token,user_id,product_id,product_name,product_price,quantity,line_total
            order_token_raw = row.get("order_token") or row.get("order") or row.get("order_token")
            user_id_raw = row.get("user_id")
            product_id_raw = row.get("product_id")
            product_name = (row.get("product_name") or "").strip()
            product_price_raw = row.get("product_price") or row.get("price") or "0"
            quantity_raw = row.get("quantity") or "1"

            # parse
            order_token = parse_uuid(order_token_raw) or uuid.uuid4()
            user_obj = get_user_by_id(user_id_raw)
            product_obj = get_product_by_id(product_id_raw)
            product_price = parse_int(product_price_raw, default=0)
            quantity = parse_int(quantity_raw, default=1)

            defaults = {
                "user": user_obj,
                "product": product_obj,
                "product_name": product_name,
                "product_price": product_price,
                "quantity": quantity
            }

            try:
                if dry_run:
                    # hanya tampilkan apa yang akan dibuat
                    print(f"[DRY RUN] Row {row_num}: token={order_token} user={getattr(user_obj,'pk',None)} product={getattr(product_obj,'pk',None)} name='{product_name}' price={product_price} qty={quantity}")
                    created += 1
                    continue

                # coba get_or_create berdasarkan order_token + product(optional)
                # jika ingin mencegah duplikat jelas, ubah lookup sesuai kebutuhan.
                purchase, was_created = Purchase.objects.get_or_create(
                    order_token=order_token,
                    defaults=defaults
                )

                if was_created:
                    created += 1
                else:
                    # update nilai jika ada perbedaan
                    changed = False
                    for k, v in defaults.items():
                        if getattr(purchase, k) != v:
                            setattr(purchase, k, v)
                            changed = True
                    if changed:
                        purchase.save()
                        updated += 1
                    else:
                        skipped += 1

            except Exception as e:
                print(f"ERROR saat memproses baris {row_num}: {e}")
                continue

    print("Selesai import purchases.csv")
    if dry_run:
        print(f"[DRY RUN] Baris yang akan diproses: {created}")
    else:
        print(f"Created: {created}, Updated: {updated}, Skipped (no change): {skipped}")

if __name__ == "__main__":
    # ubah ke True jika mau cek tanpa menulis ke DB
    DRY_RUN = False
    import_purchases(dry_run=DRY_RUN)
