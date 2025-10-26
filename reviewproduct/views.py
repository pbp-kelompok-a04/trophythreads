from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from .models import Merchandise, Review, Purchase
import logging
logger = logging.getLogger(__name__)


def product_reviews(request, product_id):
    product = get_object_or_404(Merchandise, pk=product_id)
    stars = request.GET.get("stars", "all")

    reviews_all = Review.objects.filter(product=product, deleted=False)
    reviews_qs = reviews_all.order_by("-created_at")
    if stars in {"1","2","3","4","5"}:
        reviews_qs = reviews_qs.filter(rating=int(stars))

    stats = reviews_all.aggregate(
        total=Count("id"),
        c1=Count("id", filter=Q(rating=1)),
        c2=Count("id", filter=Q(rating=2)),
        c3=Count("id", filter=Q(rating=3)),
        c4=Count("id", filter=Q(rating=4)),
        c5=Count("id", filter=Q(rating=5)),
    )
    counts = {i: stats.get(f"c{i}", 0) for i in range(1,6)}

    can_review = (
        request.user.is_authenticated
        and Purchase.objects.filter(user=request.user, product=product).exists()
        and not Review.objects.filter(product=product, user=request.user, deleted=False).exists()
    )


    return render(request, "main_review.html", {
        "product": product,
        "reviews": reviews_qs,
        "stars": stars,
        "counts": counts,
        "total": stats["total"],
        "can_review": can_review,
    })

@login_required
def add_review(request, product_id):
    """Tambah review - support form POST"""
    product = get_object_or_404(Merchandise, pk=product_id)

    # Cek sudah pernah beli
    has_ordered = Purchase.objects.filter(user=request.user, product=product).exists()
    if not has_ordered:
        messages.error(request, "Kamu hanya bisa review produk yang sudah dibeli.")
        return redirect("reviewproduct:product_reviews", product_id=product.id)

    # Cek sudah pernah review (hanya yang belum dihapus)
    if Review.objects.filter(product=product, user=request.user, deleted=False).exists():
        messages.warning(request, "Kamu sudah pernah memberikan review untuk produk ini.")
        return redirect("reviewproduct:product_reviews", product_id=product.id)

    if request.method == "POST":
        rating = int(request.POST.get("rating", 0))
        comment = (request.POST.get("comment") or "").strip()

        # Validasi
        if not (1 <= rating <= 5):
            messages.error(request, "Rating harus antara 1 dan 5.")
            return render(request, "product_review_form.html", {"product": product, "mode": "add"})

        if not comment:
            messages.error(request, "Komentar tidak boleh kosong.")
            return render(request, "product_review_form.html", {"product": product, "mode": "add"})

        # Simpan review
        Review.objects.create(product=product, user=request.user, rating=rating, body=comment)
        messages.success(request, "Review berhasil ditambahkan!")
        return redirect("reviewproduct:product_reviews", product_id=product.id)

    # GET request - tampilkan form
    return render(request, "product_review_form.html", {"product": product, "mode": "add"})


@login_required
def edit_review(request, pk):
    """Edit review - support form POST"""
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        rating = int(request.POST.get("rating", review.rating))
        comment = (request.POST.get("comment") or "").strip()

        # Validasi
        if not (1 <= rating <= 5):
            messages.error(request, "Rating tidak valid.")
            return render(request, "product_review_form.html", {
                "review": review, 
                "product": review.product, 
                "mode": "edit"
            })

        if not comment:
            messages.error(request, "Komentar tidak boleh kosong.")
            return render(request, "product_review_form.html", {
                "review": review, 
                "product": review.product, 
                "mode": "edit"
            })

        # Update review
        review.rating = rating
        review.body = comment
        review.save()
        
        logger.info(f"Review {pk} updated by user {request.user.username}")
        messages.success(request, "Review berhasil diperbarui!")
        return redirect("reviewproduct:product_reviews", product_id=review.product.id)

    # GET request - tampilkan form
    return render(request, "product_review_form.html", {
        "review": review, 
        "product": review.product, 
        "mode": "edit"
    })

@login_required
def delete_review(request, pk):
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method in ("POST", "DELETE"):
        product_id = review.product_id
        review.delete()

        if request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"message": "Review berhasil dihapus!"}, status=200)
        
        messages.success(request, "Review berhasil dihapus!")
        return redirect("reviewproduct:product_reviews", product_id=product_id)

    #Opsional
    return render(request, "product_review_confirm_delete.html", {"review": review}, status=200)