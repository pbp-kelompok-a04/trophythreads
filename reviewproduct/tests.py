# reviewproduct/tests.py
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.utils import timezone

from reviewproduct.models import Review, Merchandise, Purchase


class ReviewProductTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(username="alice", password="pw12345")
        cls.user2 = User.objects.create_user(username="bob", password="pw12345")

      
        cls.product = Merchandise.objects.create(
            name="Kaos Maroon",
            price=10000,
            stock=10,
            description="Kaos warna maroon",
        )
        cls.client = Client()

    def setUp(self):
        # Pastikan tabel review bersih di setiap test
        Review.objects.all().delete()

    # ---------- URLs ----------
    def test_urls_resolve(self):
        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        self.assertEqual(resolve(url).url_name, "product_reviews")

        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})
        self.assertEqual(resolve(url).url_name, "add_review")

        dummy = Review.objects.create(product=self.product, user=self.user, rating=5, body="ok")
        url = reverse("reviewproduct:edit_review", kwargs={"pk": str(dummy.pk)})
        self.assertEqual(resolve(url).url_name, "edit_review")

        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(dummy.pk)})
        self.assertEqual(resolve(url).url_name, "delete_review")

    # ---------- product_reviews ----------
    def test_product_reviews_list_counts_filters_and_template(self):
        r1 = Review.objects.create(product=self.product, user=self.user, rating=5, body="mantap")
        r2 = Review.objects.create(product=self.product, user=self.user2, rating=2, body="kurang")
        # soft delete salah satu review -> tidak muncul di list
        r2.delete()

        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "main_review.html")
        # context dasar
        self.assertIn("counts", resp.context)
        self.assertIn("total", resp.context)
        # hanya 1 review aktif (r1)
        reviews = list(resp.context["reviews"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].pk, r1.pk)

        # filter bintang
        resp2 = self.client.get(url + "?stars=5")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(list(resp2.context["reviews"])[0].rating, 5)

    def test_product_reviews_can_review_logic_with_deleted_flag(self):
        # belum login -> can_review False
        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        resp = self.client.get(url)
        self.assertFalse(resp.context["can_review"])

        # login tanpa purchase -> False
        self.client.login(username="alice", password="pw12345")
        resp = self.client.get(url)
        self.assertFalse(resp.context["can_review"])

        # sudah purchase -> True (belum pernah review aktif)
        Purchase.objects.create(user=self.user, product=self.product)
        resp = self.client.get(url)
        self.assertTrue(resp.context["can_review"])

        # sudah buat review aktif -> False
        Review.objects.create(product=self.product, user=self.user, rating=4, body="oke")
        resp = self.client.get(url)
        self.assertFalse(resp.context["can_review"])

        # soft delete review -> True lagi (karena deleted=False jadi syarat unik & can_review konsisten)
        Review.objects.filter(product=self.product, user=self.user).first().delete()
        resp = self.client.get(url)
        self.assertTrue(resp.context["can_review"])

    # ---------- add_review ----------
    def test_add_review_requires_purchase_then_unique_and_success(self):
        self.client.login(username="alice", password="pw12345")
        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})

        # belum purchase -> tolak
        resp = self.client.post(url, {"rating": "5", "comment": "top"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product, deleted=False).count(), 0)

        # purchase -> boleh tambah
        Purchase.objects.create(user=self.user, product=self.product)
        resp = self.client.post(url, {"rating": "5", "comment": "top"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product, deleted=False).count(), 1)

        # coba duplikat -> tetap 1 (ditolak oleh guard view/constraint)
        resp = self.client.post(url, {"rating": "4", "comment": "kedua"}, follow=True)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product, deleted=False).count(), 1)

    def test_add_review_validation_invalid_rating_and_empty_comment(self):
        self.client.login(username="alice", password="pw12345")
        Purchase.objects.create(user=self.user, product=self.product)
        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})

        # rating invalid
        resp = self.client.post(url, {"rating": "10", "comment": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

        # komentar kosong
        resp = self.client.post(url, {"rating": "3", "comment": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

    # ---------- edit_review ----------
    def test_edit_review_get_post_success_and_validations(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=3, body="awal")
        url = reverse("reviewproduct:edit_review", kwargs={"pk": str(r.pk)})

        # GET form
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")
        self.assertEqual(resp.context.get("mode"), "edit")

        # POST update valid
        resp = self.client.post(url, {"rating": "5", "comment": "update"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.rating, 5)
        self.assertEqual(r.body, "update")

        # POST rating invalid
        resp = self.client.post(url, {"rating": "0", "comment": "bad"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

        # POST comment kosong
        resp = self.client.post(url, {"rating": "4", "comment": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

    # ---------- delete_review ----------
    def test_delete_review_post_redirect_and_soft_delete(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=4, body="hapus")
        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(r.pk)})

        resp = self.client.post(url, follow=True)
        self.assertEqual(resp.status_code, 200)

        r.refresh_from_db()
        self.assertTrue(r.deleted)

    def test_delete_review_post_ajax_json(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=4, body="hapus-ajax")
        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(r.pk)})

        resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content.decode(), {"message": "Review berhasil dihapus!"})
        r.refresh_from_db()
        self.assertTrue(r.deleted)

    def test_delete_review_get_confirm_template(self):
        # GET harus menampilkan halaman konfirmasi (untuk cover cabang render konfirmasi)
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=3, body="xx")
        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(r.pk)})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_confirm_delete.html")

    # ---------- model: clean/save/delete/properties ----------
    def test_model_clean_ok_and_raises(self):
        r = Review(product=self.product, user=self.user, rating=4, body="ok")
        r.full_clean()  # tidak raise

        r_bad = Review(product=self.product, user=self.user, rating=10, body="xx")
        with self.assertRaises(Exception):
            r_bad.full_clean()

    def test_model_save_sets_purchased_at_and_soft_delete_and_props(self):
        # tanpa purchase -> purchased_at None
        r = Review(product=self.product, user=self.user, rating=3, body="x")
        r.save()
        self.assertIsNone(r.purchased_at)
        self.assertFalse(r.is_critical)  # 3 bukan <=2
        self.assertFalse(r.is_positive)  # 3 bukan >=4

        # buat purchase; hapus review aktif agar tidak bentrok constraint (deleted=False)
        Purchase.objects.create(user=self.user, product=self.product)
        r.delete()  # soft delete (deleted=True)


        r2 = Review(product=self.product, user=self.user, rating=5, body="y")
        r2.save()
        self.assertIsNotNone(r2.purchased_at)
        self.assertEqual(r2.purchased_at, timezone.now().date())
        self.assertTrue(r2.is_positive)
        self.assertFalse(r2.is_critical)


        self.assertEqual(
            Review.objects.filter(product=self.product, user=self.user, deleted=False).count(), 1
        )
