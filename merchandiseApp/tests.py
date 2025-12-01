# test.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Merchandise
import uuid
import json

class MerchandiseModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
        )
        self.merchandise = Merchandise.objects.create(
            user=self.user,
            name='Test Jersey',
            price=150000,
            category='jersey',
            stock=10,
            thumbnail='https://example.com/jersey.jpg',
            description='Test description',
            product_views=5,
            is_featured=True
        )

    def test_merchandise_creation(self):
        """Test bahwa merchandise dapat dibuat dengan benar"""
        self.assertEqual(self.merchandise.name, 'Test Jersey')
        self.assertEqual(self.merchandise.price, 150000)
        self.assertEqual(self.merchandise.category, 'jersey')
        self.assertEqual(self.merchandise.stock, 10)
        self.assertTrue(self.merchandise.is_featured)
        self.assertEqual(self.merchandise.product_views, 5)

    def test_merchandise_str_method(self):
        """Test method __str__"""
        self.assertEqual(str(self.merchandise), 'Test Jersey')

    def test_is_product_hot_property(self):
        """Test property is_product_hot"""
        # Test ketika product_views <= 100
        self.assertFalse(self.merchandise.is_product_hot)
        
        # Test ketika product_views > 100
        self.merchandise.product_views = 150
        self.merchandise.save()
        self.assertTrue(self.merchandise.is_product_hot)

    def test_increment_views_method(self):
        """Test method increment_views"""
        initial_views = self.merchandise.product_views
        self.merchandise.increment_views()
        self.assertEqual(self.merchandise.product_views, initial_views + 1)

    def test_merchandise_uuid(self):
        """Test bahwa UUID di-generate dengan benar"""
        self.assertIsInstance(self.merchandise.id, uuid.UUID)
        self.assertEqual(len(str(self.merchandise.id)), 36)

class MerchandiseViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.merchandise = Merchandise.objects.create(
            user=self.user,
            name='Test Product',
            price=100000,
            category='jersey',
            stock=5,
            thumbnail='https://example.com/product.jpg',
            description='Test description'
        )

    def test_show_main_merchandise_view(self):
        """Test view show_main_merchandise"""
        response = self.client.get(reverse('merchandiseApp:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_merchandise.html')
        self.assertContains(response, 'Latest Products')

    def test_show_merchandise_detail_view(self):
        """Test view show_merchandise"""
        url = reverse('merchandiseApp:show_merchandise', args=[self.merchandise.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchandise_detail.html')
        self.assertContains(response, 'Test Product')

    def test_show_merchandise_detail_increments_views(self):
        """Test bahwa melihat detail merchandise menambah product_views"""
        initial_views = self.merchandise.product_views
        url = reverse('merchandiseApp:show_merchandise', args=[self.merchandise.id])
        response = self.client.get(url)
        
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.product_views, initial_views + 1)

    def test_show_merchandise_detail_not_found(self):
        """Test view show_merchandise dengan ID yang tidak ada"""
        invalid_id = uuid.uuid4()
        url = reverse('merchandiseApp:show_merchandise', args=[invalid_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_get_merchandise_json(self):
        """Test API get_merchandise_json"""
        response = self.client.get(reverse('merchandiseApp:get_merchandise_json'))
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Product')
        self.assertEqual(data[0]['price'], 100000)

    def test_show_json_view(self):
        """Test view show_json"""
        response = self.client.get(reverse('merchandiseApp:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_show_xml_view(self):
        """Test view show_xml"""
        response = self.client.get(reverse('merchandiseApp:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

    def test_show_json_by_id(self):
        """Test view show_json_by_id"""
        url = reverse('merchandiseApp:show_json_by_id', args=[self.merchandise.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_show_xml_by_id(self):
        """Test view show_xml_by_id"""
        url = reverse('merchandiseApp:show_xml_by_id', args=[self.merchandise.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/xml')

class MerchandiseAjaxViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='selleruser',
            password='testpass123'
        )
        
        try:
            from main.models import Profile
            Profile.objects.create(user=self.user, role='seller')
        except ImportError:
            # Fallback jika model Profile tidak ada
            pass

        self.merchandise = Merchandise.objects.create(
            user=self.user,
            name='Existing Product',
            price=200000,
            category='hoodie',
            stock=3,
            description='Existing description'
        )

    def test_create_merchandise_ajax_authenticated(self):
        """Test create merchandise dengan user terautentikasi"""
        self.client.login(username='selleruser', password='testpass123')
        
        data = {
            'name': 'New Ajax Product',
            'price': 120000,
            'category': 'socks',
            'stock': 15,
            'thumbnail': 'https://example.com/socks.jpg',
            'description': 'New product via AJAX',
            'is_featured': 'true'
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'Merchandise created successfully!')
        
        # Verifikasi merchandise dibuat di database
        self.assertTrue(Merchandise.objects.filter(name='New Ajax Product').exists())

    def test_create_merchandise_ajax_unauthenticated(self):
        """Test create merchandise tanpa autentikasi"""
        data = {
            'name': 'New Product',
            'price': 120000,
            'category': 'socks',
            'stock': 15,
            'description': 'New product'
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 401)

    def test_edit_merchandise_ajax(self):
        """Test edit merchandise via AJAX"""
        self.client.login(username='selleruser', password='testpass123')
        
        data = {
            'name': 'Updated Product',
            'price': 250000,
            'category': 'jacket',
            'stock': 8,
            'thumbnail': 'https://example.com/updated.jpg',
            'description': 'Updated description',
            'is_featured': 'false'
        }
        
        url = reverse('merchandiseApp:edit_merchandise_ajax', args=[self.merchandise.id])
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, 200)
        
        # Refresh dari database dan verifikasi perubahan
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.name, 'Updated Product')
        self.assertEqual(self.merchandise.price, 250000)
        self.assertEqual(self.merchandise.category, 'jacket')
        self.assertFalse(self.merchandise.is_featured)

    def test_delete_merchandise_ajax(self):
        """Test delete merchandise via AJAX"""
        self.client.login(username='selleruser', password='testpass123')
        
        merchandise_id = self.merchandise.id
        
        url = reverse('merchandiseApp:delete_merchandise_ajax', args=[merchandise_id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Verifikasi merchandise dihapus dari database
        self.assertFalse(Merchandise.objects.filter(id=merchandise_id).exists())

    def test_delete_merchandise_ajax_unauthenticated(self):
        """Test delete merchandise tanpa autentikasi"""
        url = reverse('merchandiseApp:delete_merchandise_ajax', args=[self.merchandise.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, 401)

class MerchandiseFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_merchandise_form_valid_data(self):
        """Test form dengan data valid"""
        from .forms import MerchandiseForm
        
        form_data = {
            'name': 'Form Test Product',
            'price': 175000,
            'category': 'ball',
            'stock': 20,
            'thumbnail': 'https://example.com/ball.jpg',
            'description': 'Test product from form',
            'is_featured': True
        }
        
        form = MerchandiseForm(data=form_data)
        self.assertTrue(form.is_valid())

class MerchandiseCategoryTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_category_choices(self):
        """Test bahwa kategori yang valid dapat disimpan"""
        valid_categories = [
            'jersey', 'training jersey', 'top', 'jacket', 'hoodie',
            'sweatshirt', 'vest', 'socks', 'ball', 'bag', 'tumbler',
            'action figure', 'accessories', 'others'
        ]
        
        for category in valid_categories:
            merchandise = Merchandise.objects.create(
                user=self.user,
                name=f'Test {category}',
                price=100000,
                category=category,
                stock=10,
                description=f'Test {category} product'
            )
            self.assertEqual(merchandise.category, category)

class MerchandiseURLTest(TestCase):
    def test_urls(self):
        """Test bahwa semua URL resolve dengan benar"""
        merchandise = Merchandise.objects.create(
            user=User.objects.create_user(username='temp', password='temp'),
            name='URL Test',
            price=100000,
            category='jersey',
            stock=1,
            description='Test'
        )
        
        # Test URL patterns
        url = reverse('merchandiseApp:show_main')
        self.assertEqual(url, '/merchandise/')
        
        url = reverse('merchandiseApp:show_merchandise', args=[merchandise.id])
        self.assertEqual(url, f'/merchandise/{merchandise.id}/')
        
        url = reverse('merchandiseApp:create_merchandise_ajax')
        self.assertEqual(url, '/merchandise/create/')
        
        url = reverse('merchandiseApp:get_merchandise_json')
        self.assertEqual(url, '/merchandise/get-merchandise/')

if __name__ == '__main__':
    # Untuk menjalankan tes secara manual
    import django
    from django.conf import settings
    
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'main',  
                'merchandiseApp',
            ],
            USE_TZ=True,
        )
        django.setup()
    
    import unittest
    unittest.main()