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
        Review.objects.all().delete()

   
    def test_urls_resolve(self):
        """Pastikan pola URL sesuai urls.py"""
        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        self.assertEqual(resolve(url).url_name, "product_reviews")

        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})
        self.assertEqual(resolve(url).url_name, "add_review")

      
        dummy = Review.objects.create(product=self.product, user=self.user, rating=5, body="ok")
        url = reverse("reviewproduct:edit_review", kwargs={"pk": str(dummy.pk)})
        self.assertEqual(resolve(url).url_name, "edit_review")

        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(dummy.pk)})
        self.assertEqual(resolve(url).url_name, "delete_review")

    
    def test_product_reviews_list_and_filters(self):
        r1 = Review.objects.create(product=self.product, user=self.user, rating=5, body="mantap")
        r2 = Review.objects.create(product=self.product, user=self.user2, rating=2, body="kurang")
        r2.delete() 

        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
  
        reviews = list(resp.context["reviews"])
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].pk, r1.pk)
        self.assertIn("counts", resp.context)
        self.assertIn("total", resp.context)
        self.assertFalse(resp.context["can_review"])
        self.assertTemplateUsed(resp, "main_review.html")

        
        resp2 = self.client.get(url + "?stars=5")
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(list(resp2.context["reviews"])[0].rating, 5)

    def test_product_reviews_can_review_logic(self):
        self.client.login(username="alice", password="pw12345")

        # Belum pernah beli -> can_review False
        url = reverse("reviewproduct:product_reviews", kwargs={"product_id": self.product.pk})
        resp = self.client.get(url)
        self.assertFalse(resp.context["can_review"])

        # Setelah beli -> can_review True (selama belum pernah review)
        Purchase.objects.create(user=self.user, product=self.product)
        resp = self.client.get(url)
        self.assertTrue(resp.context["can_review"])

        # Setelah user memberi review -> can_review False lagi
        Review.objects.create(product=self.product, user=self.user, rating=4, body="oke")
        resp = self.client.get(url)
        self.assertFalse(resp.context["can_review"])


    def test_add_review_requires_purchase_and_unique(self):
        self.client.login(username="alice", password="pw12345")
        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})

        # Belum beli -> ditolak & redirect
        resp = self.client.post(url, {"rating": "5", "comment": "top"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 0)

       
        Purchase.objects.create(user=self.user, product=self.product)
        resp = self.client.post(url, {"rating": "5", "comment": "top"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 1)

        
        resp = self.client.post(url, {"rating": "4", "comment": "kedua"}, follow=True)
        self.assertEqual(Review.objects.filter(user=self.user, product=self.product).count(), 1)

    def test_add_review_validation(self):
        self.client.login(username="alice", password="pw12345")
        Purchase.objects.create(user=self.user, product=self.product)
        url = reverse("reviewproduct:add_review", kwargs={"product_id": self.product.pk})

        # Rating invalid
        resp = self.client.post(url, {"rating": "10", "comment": "x"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

        # Komentar kosong
        resp = self.client.post(url, {"rating": "3", "comment": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

    
    def test_edit_review_get_and_post(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=3, body="awal")
        url = reverse("reviewproduct:edit_review", kwargs={"pk": str(r.pk)})

      
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")
        self.assertEqual(resp.context["mode"], "edit")

    
        resp = self.client.post(url, {"rating": "5", "comment": "update"}, follow=True)
        self.assertEqual(resp.status_code, 200)
        r.refresh_from_db()
        self.assertEqual(r.rating, 5)
        self.assertEqual(r.body, "update")

        resp = self.client.post(url, {"rating": "0", "comment": "bad"})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

      
        resp = self.client.post(url, {"rating": "4", "comment": ""})
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, "product_review_form.html")

   
    def test_delete_review_post_redirect_and_softdelete(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=4, body="hapus")
        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(r.pk)})

        resp = self.client.post(url, follow=True)  
        self.assertEqual(resp.status_code, 200)

        r.refresh_from_db()
        self.assertTrue(r.deleted)  

    def test_delete_review_ajax_json(self):
        self.client.login(username="alice", password="pw12345")
        r = Review.objects.create(product=self.product, user=self.user, rating=4, body="hapus-ajax")
        url = reverse("reviewproduct:delete_review", kwargs={"pk": str(r.pk)})

        resp = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(resp.status_code, 200)
        self.assertJSONEqual(resp.content.decode(), {"message": "Review berhasil dihapus!"})
        r.refresh_from_db()
        self.assertTrue(r.deleted)

   
    def test_model_clean_and_properties(self):
        r = Review(product=self.product, user=self.user, rating=4, body="ok")
        r.full_clean()  # tidak raise
        self.assertTrue(r.is_positive)
        self.assertFalse(r.is_critical)

        r2 = Review(product=self.product, user=self.user, rating=1, body="bad")
        r2.full_clean()
        self.assertFalse(r2.is_positive)
        self.assertTrue(r2.is_critical)

        r3 = Review(product=self.product, user=self.user, rating=10, body="xx")
        with self.assertRaises(Exception):
            r3.full_clean()

    def test_model_save_sets_purchased_at_when_user_has_purchase(self):
        r = Review(product=self.product, user=self.user, rating=3, body="x")
        r.save()
        self.assertIsNone(r.purchased_at)

        Purchase.objects.create(user=self.user, product=self.product)
        r2 = Review(product=self.product, user=self.user, rating=5, body="y")
        r2.save()
        self.assertIsNotNone(r2.purchased_at)
        self.assertEqual(r2.purchased_at, timezone.now().date())

    def test_model_soft_delete(self):
        r = Review.objects.create(product=self.product, user=self.user, rating=2, body="zz")
        r.delete()
        r.refresh_from_db()
        self.assertTrue(r.deleted)
