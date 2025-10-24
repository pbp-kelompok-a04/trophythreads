from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Merchandise
from main.models import Profile
import json
import uuid

class MerchandiseModelTest(TestCase):
    def setUp(self):
        # Create user and profile
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.create(
            user=self.user,
            role='seller',
            phone_number='1234567890'
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            user=self.profile,
            name='Test Jersey',
            price=250000,
            category='jersey',
            stock=50,
            thumbnail='https://example.com/jersey.jpg',
            description='Test jersey description',
            product_views=10,
            is_featured=True
        )

    def test_merchandise_creation(self):
        """Test that merchandise is created correctly"""
        self.assertEqual(self.merchandise.name, 'Test Jersey')
        self.assertEqual(self.merchandise.price, 250000)
        self.assertEqual(self.merchandise.category, 'jersey')
        self.assertEqual(self.merchandise.stock, 50)
        self.assertEqual(self.merchandise.product_views, 10)
        self.assertTrue(self.merchandise.is_featured)

    def test_merchandise_str_method(self):
        """Test the string representation"""
        self.assertEqual(str(self.merchandise), 'Test Jersey')

    def test_increment_views(self):
        """Test increment_views method"""
        initial_views = self.merchandise.product_views
        self.merchandise.increment_views()
        self.assertEqual(self.merchandise.product_views, initial_views + 1)

    def test_is_product_hot_property(self):
        """Test is_product_hot property"""
        # Test when views <= 100
        self.assertFalse(self.merchandise.is_product_hot)
        
        # Test when views > 100
        self.merchandise.product_views = 150
        self.merchandise.save()
        self.assertTrue(self.merchandise.is_product_hot)

    def test_merchandise_category_choices(self):
        """Test category choices"""
        valid_categories = ['jersey', 'training jersey', 'top', 'jacket', 'hoodie', 
                           'sweatshirt', 'vest', 'socks', 'ball', 'bag', 'tumbler', 
                           'action figure', 'accessories', 'others']
        
        for category in valid_categories:
            with self.subTest(category=category):
                merchandise = Merchandise.objects.create(
                    user=self.profile,
                    name=f'Test {category}',
                    price=100000,
                    category=category,
                    stock=10,
                    description=f'Test {category} description'
                )
                self.assertEqual(merchandise.category, category)


class MerchandiseViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create users with different roles
        self.seller_user = User.objects.create_user(username='seller', password='testpass123')
        self.buyer_user = User.objects.create_user(username='buyer', password='testpass123')
        
        self.seller_profile = Profile.objects.create(
            user=self.seller_user,
            role='seller',
            phone_number='1234567890'
        )
        self.buyer_profile = Profile.objects.create(
            user=self.buyer_user,
            role='buyer',
            phone_number='0987654321'
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            user=self.seller_profile,
            name='Test Product',
            price=150000,
            category='jersey',
            stock=25,
            description='Test description',
            is_featured=False
        )

    def test_show_main_merchandise_view(self):
        """Test main merchandise page"""
        response = self.client.get(reverse('merchandiseApp:show_main'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'main_merchandise.html')
        self.assertContains(response, 'Support Your Nation')

    def test_show_merchandise_detail_view(self):
        """Test merchandise detail page"""
        url = reverse('merchandiseApp:show_merchandise', args=[self.merchandise.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'merchandise_detail.html')
        self.assertContains(response, 'Test Product')
        
        # Test that views are incremented
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.product_views, 1)

    def test_get_merchandise_json(self):
        """Test JSON API endpoint"""
        response = self.client.get(reverse('merchandiseApp:get_merchandise_json'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(isinstance(data, list))
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Product')

    def test_show_xml(self):
        """Test XML endpoint"""
        response = self.client.get(reverse('merchandiseApp:show_xml'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/xml', response['Content-Type'])

    def test_show_json(self):
        """Test JSON endpoint"""
        response = self.client.get(reverse('merchandiseApp:show_json'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])

    def test_show_json_by_id(self):
        """Test JSON by ID endpoint"""
        response = self.client.get(reverse('merchandiseApp:show_json_by_id', 
                                         args=[self.merchandise.id]))
        self.assertEqual(response.status_code, 200)

    def test_show_xml_by_id(self):
        """Test XML by ID endpoint"""
        response = self.client.get(reverse('merchandiseApp:show_xml_by_id', 
                                         args=[self.merchandise.id]))
        self.assertEqual(response.status_code, 200)


class MerchandiseAjaxViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create seller user
        self.seller_user = User.objects.create_user(username='seller', password='testpass123')
        self.seller_profile = Profile.objects.create(
            user=self.seller_user,
            role='seller',
            phone_number='1234567890'
        )
        
        # Create buyer user
        self.buyer_user = User.objects.create_user(username='buyer', password='testpass123')
        self.buyer_profile = Profile.objects.create(
            user=self.buyer_user,
            role='buyer',
            phone_number='0987654321'
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            user=self.seller_profile,
            name='Test Product',
            price=150000,
            category='jersey',
            stock=25,
            description='Test description'
        )

    def test_create_merchandise_ajax_authenticated_seller(self):
        """Test creating merchandise as authenticated seller"""
        self.client.login(username='seller', password='testpass123')
        
        data = {
            'name': 'New Jersey',
            'price': 300000,
            'category': 'jersey',
            'stock': 10,
            'thumbnail': 'https://example.com/new.jpg',
            'description': 'New jersey description',
            'is_featured': 'true'
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'Merchandise created successfully!')
        
        # Verify merchandise was created
        self.assertTrue(Merchandise.objects.filter(name='New Jersey').exists())

    def test_create_merchandise_ajax_unauthenticated(self):
        """Test creating merchandise without authentication"""
        data = {
            'name': 'New Jersey',
            'price': 300000,
            'category': 'jersey',
            'stock': 10
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 401)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'User not authenticated. Please login first.')

    def test_create_merchandise_ajax_buyer_role(self):
        """Test creating merchandise as buyer (should fail)"""
        self.client.login(username='buyer', password='testpass123')
        
        data = {
            'name': 'New Jersey',
            'price': 300000,
            'category': 'jersey',
            'stock': 10
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'Only seller can create merchandise.')

    def test_edit_merchandise_ajax_authenticated_seller(self):
        """Test editing merchandise as authenticated seller"""
        self.client.login(username='seller', password='testpass123')
        
        data = {
            'name': 'Updated Product',
            'price': 200000,
            'category': 'hoodie',
            'stock': 15,
            'description': 'Updated description',
            'thumbnail': 'https://example.com/updated.jpg',
            'is_featured': 'true'
        }
        
        response = self.client.post(
            reverse('merchandiseApp:edit_merchandise_ajax', args=[self.merchandise.id]),
            data
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'Merchandise updated successfully!')
        
        # Verify merchandise was updated
        self.merchandise.refresh_from_db()
        self.assertEqual(self.merchandise.name, 'Updated Product')
        self.assertEqual(self.merchandise.price, 200000)
        self.assertEqual(self.merchandise.category, 'hoodie')
        self.assertTrue(self.merchandise.is_featured)

    def test_delete_merchandise_ajax_authenticated_seller(self):
        """Test deleting merchandise as authenticated seller"""
        self.client.login(username='seller', password='testpass123')
        
        response = self.client.delete(
            reverse('merchandiseApp:delete_merchandise_ajax', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['message'], 'Merchandise deleted successfully!')
        
        # Verify merchandise was deleted
        self.assertFalse(Merchandise.objects.filter(id=self.merchandise.id).exists())

    def test_delete_merchandise_ajax_unauthorized_user(self):
        """Test deleting merchandise as unauthorized user"""
        # Create another seller
        other_seller = User.objects.create_user(username='otherseller', password='testpass123')
        other_profile = Profile.objects.create(
            user=other_seller,
            role='seller',
            phone_number='1111111111'
        )
        
        self.client.login(username='otherseller', password='testpass123')
        
        response = self.client.delete(
            reverse('merchandiseApp:delete_merchandise_ajax', args=[self.merchandise.id])
        )
        
        self.assertEqual(response.status_code, 403)
        response_data = json.loads(response.content)
        self.assertEqual(response_data['error'], 'You are not authorized to delete this merchandise')


class MerchandiseFormsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.profile = Profile.objects.create(
            user=self.user,
            role='seller',
            phone_number='1234567890'
        )

    def test_merchandise_form_valid_data(self):
        """Test merchandise form with valid data"""
        from .forms import MerchandiseForm
        
        form_data = {
            'name': 'Test Product',
            'price': 150000,
            'category': 'jersey',
            'stock': 10,
            'thumbnail': 'https://example.com/image.jpg',
            'description': 'Test description',
            'is_featured': True
        }
        
        form = MerchandiseForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_merchandise_form_invalid_data(self):
        """Test merchandise form with invalid data"""
        from .forms import MerchandiseForm
        
        form_data = {
            'name': '',  # Required field empty
            'price': -100,  # Negative price
            'category': 'invalid_category',  # Invalid choice
            'stock': -5,  # Negative stock
            'description': ''  # Required field empty
        }
        
        form = MerchandiseForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)
        self.assertIn('price', form.errors)
        self.assertIn('category', form.errors)
        self.assertIn('stock', form.errors)


class MerchandiseURLsTest(TestCase):
    def test_urls(self):
        """Test all URL patterns"""
        merchandise_id = uuid.uuid4()
        
        url_patterns = [
            ('merchandiseApp:show_main', [], '/'),
            ('merchandiseApp:show_merchandise', [merchandise_id], f'/{merchandise_id}/'),
            ('merchandiseApp:create_merchandise_ajax', [], '/create/'),
            ('merchandiseApp:edit_merchandise_ajax', [merchandise_id], f'/edit/{merchandise_id}/'),
            ('merchandiseApp:delete_merchandise_ajax', [merchandise_id], f'/delete/{merchandise_id}/'),
            ('merchandiseApp:get_merchandise_json', [], '/json/'),
            ('merchandiseApp:show_xml', [], '/xml/'),
            ('merchandiseApp:show_json', [], '/json/'),
            ('merchandiseApp:show_json_by_id', [merchandise_id], f'/json/{merchandise_id}/'),
            ('merchandiseApp:show_xml_by_id', [merchandise_id], f'/xml/{merchandise_id}/'),
            ('merchandiseApp:get_merchandise_json', [], '/get-merchandise/'),
        ]
        
        for url_name, args, expected_path in url_patterns:
            with self.subTest(url_name=url_name):
                try:
                    path = reverse(url_name, args=args)
                    self.assertEqual(path, expected_path)
                except Exception as e:
                    self.fail(f"Reverse for '{url_name}' failed: {e}")


class MerchandiseEdgeCasesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='seller', password='testpass123')
        self.profile = Profile.objects.create(
            user=self.user,
            role='seller',
            phone_number='1234567890'
        )

    def test_create_merchandise_without_thumbnail(self):
        """Test creating merchandise without thumbnail"""
        self.client.login(username='seller', password='testpass123')
        
        data = {
            'name': 'Product Without Thumbnail',
            'price': 100000,
            'category': 'jersey',
            'stock': 5,
            'description': 'No thumbnail product',
            'is_featured': 'false'
        }
        
        response = self.client.post(
            reverse('merchandiseApp:create_merchandise_ajax'),
            data
        )
        
        self.assertEqual(response.status_code, 201)
        
        # Verify merchandise was created with null thumbnail
        merchandise = Merchandise.objects.get(name='Product Without Thumbnail')
        self.assertIsNone(merchandise.thumbnail)

    def test_edit_nonexistent_merchandise(self):
        """Test editing non-existent merchandise"""
        self.client.login(username='seller', password='testpass123')
        
        non_existent_id = uuid.uuid4()
        data = {
            'name': 'Updated Name',
            'price': 200000,
            'category': 'jersey',
            'stock': 10
        }
        
        response = self.client.post(
            reverse('merchandiseApp:edit_merchandise_ajax', args=[non_existent_id]),
            data
        )
        
        self.assertEqual(response.status_code, 404)

    def test_delete_nonexistent_merchandise(self):
        """Test deleting non-existent merchandise"""
        self.client.login(username='seller', password='testpass123')
        
        non_existent_id = uuid.uuid4()
        
        response = self.client.delete(
            reverse('merchandiseApp:delete_merchandise_ajax', args=[non_existent_id])
        )
        
        self.assertEqual(response.status_code, 404)