# cartApp/tests.py
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, mock_open, MagicMock
import json

from .models import Cart, CartItem, Purchase
from merchandiseApp.models import Merchandise

User = get_user_model()


class CartModelTest(TestCase):
    """Test Cart model methods and properties"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.cart = Cart.objects.create(user=self.user)
        
    def test_cart_string_representation_with_user(self):
        self.assertEqual(str(self.cart), f"Cart(user={self.user})")
    
    def test_cart_string_representation_with_session(self):
        cart = Cart.objects.create(session_key='test_session_123')
        self.assertEqual(str(cart), "Cart(session=test_session_123)")
    
    def test_total_items_empty_cart(self):
        self.assertEqual(self.cart.total_items(), 0)
    
    def test_total_items_with_items(self):
        product = Merchandise.objects.create(name='Test Product', price=10000, stock=10)
        CartItem.objects.create(cart=self.cart, product=product, quantity=3)
        CartItem.objects.create(cart=self.cart, product=product, quantity=2)
        self.assertEqual(self.cart.total_items(), 5)
    
    def test_subtotal_only_selected_items(self):
        product1 = Merchandise.objects.create(name='Product 1', price=10000, stock=10)
        product2 = Merchandise.objects.create(name='Product 2', price=20000, stock=5)
        CartItem.objects.create(cart=self.cart, product=product1, quantity=2, selected=True)
        CartItem.objects.create(cart=self.cart, product=product2, quantity=1, selected=False)
        self.assertEqual(self.cart.subtotal(), 20000)


class CartItemModelTest(TestCase):
    """Test CartItem model methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.cart = Cart.objects.create(user=self.user)
        self.product = Merchandise.objects.create(name='Test Product', price=15000, stock=10)
    
    def test_line_total_with_product(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=3)
        self.assertEqual(item.line_total(), 45000)
    
    def test_line_total_without_product(self):
        item = CartItem.objects.create(
            cart=self.cart, 
            product_name='CSV Product',
            product_price=12000,
            quantity=2
        )
        self.assertEqual(item.line_total(), 24000)
    
    def test_string_representation(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)
        self.assertEqual(str(item), "Test Product x2")
    
    def test_cart_item_default_selected(self):
        item = CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        self.assertTrue(item.selected)


class PurchaseModelTest(TestCase):
    """Test Purchase model methods"""
    
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(name='Test Product', price=25000, stock=10)
    
    def test_line_total_with_product(self):
        purchase = Purchase.objects.create(
            user=self.user,
            product=self.product,
            product_price=25000,
            quantity=3
        )
        self.assertEqual(purchase.line_total(), 75000)
    
    def test_line_total_without_product(self):
        purchase = Purchase.objects.create(
            user=self.user,
            product_name='CSV Product',
            product_price=30000,
            quantity=2
        )
        self.assertEqual(purchase.line_total(), 60000)
    
    def test_string_representation(self):
        purchase = Purchase.objects.create(
            user=self.user,
            product=self.product,
            product_name='Test Product',
            quantity=2
        )
        self.assertIn('Purchase', str(purchase))
    
    def test_order_token_auto_generated(self):
        purchase = Purchase.objects.create(
            user=self.user,
            product=self.product,
            product_price=25000,
            quantity=1
        )
        self.assertIsNotNone(purchase.order_token)


class CartViewsTest(TestCase):
    """Test cart views and AJAX endpoints"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=50000,
            stock=10
        )
    
    def test_cart_page_authenticated(self):
        response = self.client.get(reverse('cartApp:cart_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'cart.html')
    
    def test_cart_page_unauthenticated_redirect(self):
        self.client.logout()
        response = self.client.get(reverse('cartApp:cart_page'))
        self.assertEqual(response.status_code, 302)
    
    def test_add_to_cart_db_product(self):
        response = self.client.post(reverse('cartApp:add_to_cart'), {
            'product_id': str(self.product.pk),
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('message', data)
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 2)
        self.assertFalse(item.selected)
    
    def test_add_to_cart_existing_item(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        
        response = self.client.post(reverse('cartApp:add_to_cart'), {
            'product_id': str(self.product.pk),
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 3)
    
    @patch('builtins.open', new_callable=mock_open, read_data='name,price,thumbnail,stock\nCSV Product,30000,http://example.com/img.jpg,5')
    @patch('os.path.exists', return_value=True)
    def test_add_to_cart_csv_product(self, mock_exists, mock_file):
        response = self.client.post(reverse('cartApp:add_to_cart'), {
            'product_id': 'csv_0',
            'quantity': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.product_name, 'CSV Product')
        self.assertEqual(item.product_price, 30000)
    
    def test_add_to_cart_missing_product_id(self):
        response = self.client.post(reverse('cartApp:add_to_cart'), {
            'quantity': 1
        })
        self.assertEqual(response.status_code, 400)
    
    def test_update_cart_item_increment(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'inc'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
    
    def test_update_cart_item_increment_exceeds_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=10)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'inc'}
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)
    
    def test_update_cart_item_decrement(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=3)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'dec'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 2)
    
    def test_update_cart_item_decrement_deletes_at_one(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=1)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'dec'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)
    
    def test_update_cart_item_set_quantity(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'set', 'quantity': 5}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 5)
    
    def test_update_cart_item_set_zero_deletes(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'set', 'quantity': 0}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)
    
    def test_update_cart_item_set_exceeds_stock(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'set', 'quantity': 20}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_update_cart_item_invalid_action(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'invalid_action'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_toggle_select_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, selected=False)
        
        response = self.client.post(reverse('cartApp:toggle_select', args=[item.id]))
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertTrue(item.selected)
    
    def test_toggle_select_all(self):
        cart = Cart.objects.create(user=self.user)
        product2 = Merchandise.objects.create(name='Product 2', price=20000, stock=5)
        CartItem.objects.create(cart=cart, product=self.product, selected=False)
        CartItem.objects.create(cart=cart, product=product2, selected=False)
        
        response = self.client.post(
            reverse('cartApp:toggle_select_all'),
            {'selected': 'true'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.filter(selected=True).count(), 2)
    
    def test_delete_cart_item(self):
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product)
        
        response = self.client.post(reverse('cartApp:delete_item', args=[item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)


class CheckoutViewTest(TestCase):
    """Test checkout flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=100000,
            stock=10
        )
    
    def test_checkout_page_get(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2, selected=True)
        
        response = self.client.get(reverse('cartApp:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'checkout.html')
    
    def test_checkout_post_success(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2, selected=True)
        
        initial_stock = self.product.stock
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address 123',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('redirect_url', data)
        
        # Check stock updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)
        
        # Check if sold field exists and is updated
        if hasattr(self.product, 'sold'):
            self.assertEqual(self.product.sold, 2)
        
        # Check purchase created
        self.assertEqual(Purchase.objects.count(), 1)
        
        # Check cart item deleted
        self.assertEqual(CartItem.objects.count(), 0)
    
    def test_checkout_no_address(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=True)
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_checkout_no_selected_items(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=False)
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_checkout_insufficient_stock(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=15, selected=True)
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_checkout_with_csv_product(self):
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product_name='CSV Product',
            product_price=50000,
            quantity=1,
            selected=True
        )
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Purchase.objects.count(), 1)


class BuyNowTest(TestCase):
    """Test buy now functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=75000,
            stock=10
        )
    
    def test_buy_now_success(self):
        initial_stock = self.product.stock
        
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('redirect_url', data)
        
        # Check stock updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, initial_stock - 2)
        
        # Check if sold field exists and is updated
        if hasattr(self.product, 'sold'):
            self.assertEqual(self.product.sold, 2)
        
        # Check purchase created
        self.assertEqual(Purchase.objects.count(), 1)
        purchase = Purchase.objects.first()
        self.assertEqual(purchase.quantity, 2)
    
    def test_buy_now_insufficient_stock(self):
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 15
        })
        self.assertEqual(response.status_code, 400)
    
    def test_buy_now_invalid_quantity(self):
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 'invalid'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_buy_now_missing_product_id(self):
        response = self.client.post(reverse('cartApp:buy_now'), {
            'quantity': 1
        })
        self.assertEqual(response.status_code, 400)
    
    def test_buy_now_zero_quantity(self):
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 0
        })
        self.assertEqual(response.status_code, 400)
    
    @patch('builtins.open', new_callable=mock_open, read_data='name,price,thumbnail,stock\nCSV Product,40000,http://example.com/img.jpg,8')
    @patch('os.path.exists', return_value=True)
    def test_buy_now_csv_product(self, mock_exists, mock_file):
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': 'csv_0',
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Purchase.objects.count(), 1)