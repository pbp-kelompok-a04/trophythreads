from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.db.models import Count, Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Merchandise, Review, Purchase
import json


def _get_review_data(product_id, request):
    product = get_object_or_404(Merchandise, pk=product_id)
    stars = request.GET.get("stars", "all")

    reviews_all = Review.objects.filter(product=product, deleted=False)
    reviews_qs = reviews_all.order_by("-created_at")

    if stars in {"1", "2", "3", "4", "5"}:
        reviews_qs = reviews_qs.filter(rating=int(stars))

    stats = reviews_all.aggregate(
        total=Count("id"),
        c1=Count("id", filter=Q(rating=1)),
        c2=Count("id", filter=Q(rating=2)),
        c3=Count("id", filter=Q(rating=3)),
        c4=Count("id", filter=Q(rating=4)),
        c5=Count("id", filter=Q(rating=5)),
    )

    counts = {i: stats.get(f"c{i}", 0) for i in range(1, 6)}

    can_review = (
        request.user.is_authenticated
        and Purchase.objects.filter(user=request.user, product=product).exists()
        and not Review.objects.filter(product=product, user=request.user, deleted=False).exists()
    )

    return {
        "product": product,
        "reviews": reviews_qs,
        "counts": counts,
        "total": stats["total"],
        "stars": stars,
        "can_review": can_review,
    }


# ============ HTML VIEW (untuk web) ============
def product_reviews(request, product_id):
    """View HTML untuk ditampilkan di web browser"""
    ctx = _get_review_data(product_id, request)
    return render(request, "main_review.html", ctx)


# ============ JSON API (untuk Flutter) ============
@csrf_exempt  # Important: Tambahkan ini!
def review_page(request, product_id):
    """API JSON untuk Flutter - MUST return JsonResponse"""
    try:
        data = _get_review_data(product_id, request)

        response_data = {
            "product": {
                "id": str(data["product"].id),
                "name": data["product"].name,
            },
            "reviews": [
                {
                    "id": str(r.id),
                    "user": r.user.username,
                    "rating": r.rating,
                    "body": r.body,
                    "created_at": r.created_at.isoformat(),
                    "updated_at": r.updated_at.isoformat(),
                }
                for r in data["reviews"]
            ],
            "stars_filter": data["stars"],
            "counts": {str(k): v for k, v in data["counts"].items()},  # String keys!
            "total": data["total"],
            "can_review": data["can_review"],
        }
        
        print(f"✅ Sending JSON response for product {product_id}")
        return JsonResponse(response_data, safe=False)
        
    except Merchandise.DoesNotExist:
        return JsonResponse({
            "error": "Product not found",
            "product": None,
            "reviews": [],
            "stars_filter": "all",
            "counts": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "total": 0,
            "can_review": False,
        }, status=404)
    except Exception as e:
        print(f"❌ Error in review_page: {str(e)}")
        return JsonResponse({
            "error": str(e),
            "product": None,
            "reviews": [],
            "stars_filter": "all",
            "counts": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
            "total": 0,
            "can_review": False,
        }, status=500)


@csrf_exempt
@login_required
def add_review(request, product_id):
    """API untuk add review"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    try:
        body = json.loads(request.body)
    except:
        body = request.POST

    rating = int(body.get("rating", 0))
    comment = (body.get("comment") or "").strip()

    # Validasi
    if not (1 <= rating <= 5):
        return JsonResponse({"success": False, "error": "Rating harus 1–5."}, status=400)

    if not comment:
        return JsonResponse({"success": False, "error": "Komentar tidak boleh kosong."}, status=400)

    product = get_object_or_404(Merchandise, pk=product_id)

    # Cek purchase
    has_purchase = Purchase.objects.filter(user=request.user, product=product).exists()
    if not has_purchase:
        return JsonResponse({"success": False, "error": "Kamu hanya dapat review produk yang pernah dibeli."}, status=403)

    # Cek sudah review
    already_reviewed = Review.objects.filter(
        user=request.user,
        product=product,
        deleted=False
    ).exists()
    if already_reviewed:
        return JsonResponse({"success": False, "error": "Kamu sudah pernah memberikan review."}, status=400)

    # Simpan review
    review = Review.objects.create(
        product=product,
        user=request.user,
        rating=rating,
        body=comment,
    )

    return JsonResponse({
        "success": True,
        "message": "Review berhasil ditambahkan.",
        "review_id": str(review.id)
    }, status=201)


@csrf_exempt
@login_required
def edit_review(request, pk):
    """API untuk edit review"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    review = get_object_or_404(Review, pk=pk, user=request.user)

    try:
        data = json.loads(request.body)
    except:
        data = request.POST

    rating = int(data.get("rating", review.rating))
    comment = (data.get("comment") or review.body).strip()

    # Validasi
    if not (1 <= rating <= 5):
        return JsonResponse({"success": False, "error": "Rating harus 1–5."}, status=400)

    if not comment:
        return JsonResponse({"success": False, "error": "Komentar tidak boleh kosong."}, status=400)

    review.rating = rating
    review.body = comment
    review.save()

    return JsonResponse({"success": True, "message": "Review berhasil diperbarui."})


@csrf_exempt
@login_required
def delete_review(request, pk):
    """API untuk delete review"""
    if request.method not in ("POST", "DELETE"):
        return JsonResponse({"success": False, "error": "Invalid method"}, status=405)

    review = get_object_or_404(Review, pk=pk, user=request.user)
    review.delete()  # Soft delete

    return JsonResponse({"success": True, "message": "Review berhasil dihapus."})