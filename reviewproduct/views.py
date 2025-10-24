from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Q
from django.contrib.auth.models import User
from .models import Merchandise, Review, Purchase 


# ---------- Views ----------
def product_reviews(request, product_id):
    """Halaman list review untuk satu produk."""
    product = get_object_or_404(Merchandise, pk=product_id)

    stars = request.GET.get("stars", "all")  # filter rating
    base_qs = Review.objects.filter(product=product).select_related("user").order_by("-created_at")

    # filter by rating (1–5)
    if stars in {"1", "2", "3", "4", "5"}:
        base_qs = base_qs.filter(rating=int(stars))

    stats = base_qs.aggregate(
        total=Count("id"),
        c1=Count("id", filter=Q(rating=1)),
        c2=Count("id", filter=Q(rating=2)),
        c3=Count("id", filter=Q(rating=3)),
        c4=Count("id", filter=Q(rating=4)),
        c5=Count("id", filter=Q(rating=5)),
    )
    counts = {i: stats[f"c{i}"] for i in range(1, 6)}

    # Cek apakah user sudah pernah review
    can_review = False
    if request.user.is_authenticated:
        # Cek apakah user pernah order produk ini
        has_ordered = Purchase.objects.filter(order__user=request.user, product=product).exists()
        already_reviewed = Review.objects.filter(product=product, user=request.user).exists()
        can_review = not already_reviewed

    context = {
        "product": product,
        "reviews": base_qs,
        "stars": stars,
        "counts": counts,
        "total": stats["total"],
        "can_review": can_review,
        #"has_ordered": has_ordered if request.user.is_authenticated else False,
    }
    return render(request, "main_review.html", context)


@login_required
def add_review(request, product_id):
    """Halaman + form tambah review."""
    product = get_object_or_404(Merchandise, pk=product_id)


    # pastikan user pernah order produk ini
    has_ordered = Purchase.objects.filter(order__user=request.user, product=product).exists()
    if not has_ordered:
        return JsonResponse({"error": "Kamu hanya bisa review produk yang sudah kamu beli."}, status=403)

    # kalau sudah pernah review, tolak
    if Review.objects.filter(product=product, user=request.user).exists():
        messages.warning(request, "Kamu sudah pernah memberikan review untuk produk ini.")
        return redirect("reviewproduct:product_reviews", product_id=product.id)

    if request.method == "POST":
        rating = int(request.POST.get("rating") or 0)
        comment = (request.POST.get("comment") or "").strip()

        if not (1 <= rating <= 5):
            messages.error(request, "Rating harus antara 1 dan 5.")
            return redirect(request.path)
        if not comment:
            messages.error(request, "Komentar tidak boleh kosong.")
            return redirect(request.path)

        Review.objects.create(
            product=product,
            user=request.user,
            rating=rating,
            body=comment
        )
        messages.success(request, "Review berhasil ditambahkan!")
        return redirect("reviewproduct:product_reviews", product_id=product.id)

    # render halaman add_review.html
    return render(request, "add_review.html", {"product": product})



@login_required
def edit_review(request, pk):
    """Edit review (hanya milik sendiri)."""
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        rating = int(request.POST.get("rating") or review.rating)
        comment = (request.POST.get("comment") or "").strip()

        if not (1 <= rating <= 5):
            return JsonResponse({"error": "Rating tidak valid."}, status=400)

        review.rating = rating
        if comment:
            review.body = comment
        review.save()

        return JsonResponse({"message": "Review berhasil diperbarui!"}, status=200)

    return JsonResponse({"error": "Metode tidak diizinkan."}, status=405)


@login_required
def delete_review(request, pk):
    """Hapus review milik sendiri."""
    review = get_object_or_404(Review, pk=pk, user=request.user)

    if request.method == "POST":
        review.delete()
        return JsonResponse({"message": "Review berhasil dihapus!"}, status=200)

    return JsonResponse({"error": "Metode tidak diizinkan."}, status=405)
