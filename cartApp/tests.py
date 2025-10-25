# cartApp/tests.py
from django.test import TestCase, Client, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from unittest.mock import patch, mock_open, MagicMock
import json
import uuid
import os
import tempfile

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


class AfterCheckoutTest(TestCase):
    """Test after checkout page"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    def test_after_checkout_page(self):
        session = self.client.session
        session['just_ordered'] = True
        session['last_order_token'] = str(uuid.uuid4())
        session['last_order_summary'] = {'total': 100000, 'count': 2}
        session.save()
        
        response = self.client.get(reverse('cartApp:after_checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'after_checkout.html')
    
    def test_after_checkout_clears_session(self):
        session = self.client.session
        session['just_ordered'] = True
        session['last_order_token'] = str(uuid.uuid4())
        session.save()
        
        self.client.get(reverse('cartApp:after_checkout'))
        
        # Check session cleared
        self.assertNotIn('just_ordered', self.client.session)
        self.assertNotIn('last_order_token', self.client.session)


class LoadingViewTest(TestCase):
    """Test loading view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    def test_loading_page(self):
        response = self.client.get(reverse('cartApp:loading'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'loading.html')
    
    def test_loading_page_with_summary(self):
        session = self.client.session
        session['last_order_summary'] = {'total': 100000, 'count': 2}
        session.save()
        
        response = self.client.get(reverse('cartApp:loading'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('last_order_summary', response.context)


class BuyNowCheckoutFlowTest(TestCase):
    """Test buy now to checkout flow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=100000,
            stock=10
        )
    
    def test_buy_now_then_checkout_get(self):
        """Test buy now flow then accessing checkout page"""
        # First do buy now
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        
        # Then access checkout page
        response = self.client.get(reverse('cartApp:checkout'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context.get('is_buy_now', False))
        self.assertIn('items', response.context)
    
    def test_buy_now_checkout_post(self):
        """Test completing buy now checkout"""
        # Do buy now first
        self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 1
        })
        
        # Complete checkout
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('redirect_url', data)
    
    @patch('builtins.open', new_callable=mock_open, read_data='name,price,thumbnail,stock\nProduct,50000,img.jpg,2')
    @patch('os.path.exists', return_value=True)
    def test_buy_now_csv_insufficient_stock(self, mock_exists, mock_file):
        """Test buy now CSV product with insufficient stock"""
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': 'csv_0',
            'quantity': 10
        })
        self.assertEqual(response.status_code, 400)


class CartPageContextTest(TestCase):
    """Test cart page context data"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=50000,
            stock=10
        )
    
    def test_cart_page_with_selected_items(self):
        """Test cart page shows correct selected count"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=True)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=False)
        
        response = self.client.get(reverse('cartApp:cart_page'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_count'], 1)
        self.assertEqual(response.context['cart_count'], 2)
    
    def test_cart_page_clears_buy_now_session(self):
        """Test cart page clears buy now session data"""
        session = self.client.session
        session['buy_now'] = True
        session['last_order_token'] = 'test-token'
        session.save()
        
        self.client.get(reverse('cartApp:cart_page'))
        
        self.assertNotIn('buy_now', self.client.session)
        self.assertNotIn('last_order_token', self.client.session)


class UpdateCartItemEdgeCasesTest(TestCase):
    """Test edge cases for cart item updates"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=50000,
            stock=10
        )
    
    def test_update_cart_item_invalid_quantity_string(self):
        """Test updating cart item with invalid quantity string"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(cart=cart, product=self.product, quantity=2)
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'set', 'quantity': 'abc'}
        )
        self.assertEqual(response.status_code, 400)
    
    def test_update_cart_item_csv_product_increment(self):
        """Test incrementing CSV product quantity"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product_name='CSV Product',
            product_price=30000,
            product_stock=10,
            quantity=2
        )
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'inc'}
        )
        self.assertEqual(response.status_code, 200)
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)
    
    def test_update_cart_item_csv_product_exceeds_stock(self):
        """Test incrementing CSV product beyond stock"""
        cart = Cart.objects.create(user=self.user)
        item = CartItem.objects.create(
            cart=cart,
            product_name='CSV Product',
            product_price=30000,
            product_stock=5,
            quantity=5
        )
        
        response = self.client.post(
            reverse('cartApp:update_cart_item', args=[item.id]),
            {'action': 'inc'}
        )
        self.assertEqual(response.status_code, 400)


class CheckoutMixedProductsTest(TestCase):
    """Test checkout with mixed DB and CSV products"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='DB Product',
            price=100000,
            stock=10
        )
    
    def test_checkout_mixed_products(self):
        """Test checkout with both DB and CSV products"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=True)
        CartItem.objects.create(
            cart=cart,
            product_name='CSV Product',
            product_price=50000,
            quantity=2,
            selected=True
        )
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Purchase.objects.count(), 2)


class AddToCartEdgeCasesTest(TestCase):
    """Additional edge cases for add to cart"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    @patch('builtins.open', new_callable=mock_open, read_data='name,price,thumbnail,stock\nProduct,30000,img.jpg,5\nProduct2,40000,img2.jpg,3')
    @patch('os.path.exists', return_value=True)
    def test_add_to_cart_csv_existing_item(self, mock_exists, mock_file):
        """Test adding existing CSV product to cart"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(
            cart=cart,
            product_name='Product',
            product_price=30000,
            quantity=1
        )
        
        response = self.client.post(reverse('cartApp:add_to_cart'), {
            'product_id': 'csv_0',
            'quantity': 2
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 1)
        item = CartItem.objects.first()
        self.assertEqual(item.quantity, 3)


class CheckoutSessionHandlingTest(TestCase):
    """Test session handling in checkout"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=100000,
            stock=10
        )
    
    def test_checkout_get_clears_session(self):
        """Test GET checkout clears buy now session"""
        session = self.client.session
        session['buy_now'] = True
        session['last_order_token'] = str(uuid.uuid4())
        session.save()
        
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=1, selected=True)
        
        response = self.client.get(reverse('cartApp:checkout'))
        self.assertEqual(response.status_code, 200)
        # Session should be cleared on GET for regular cart checkout
        self.assertNotIn('buy_now', self.client.session)
    
    def test_checkout_sets_session_data(self):
        """Test checkout sets correct session data"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2, selected=True)
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        
        # Check session data
        self.assertTrue(self.client.session.get('just_ordered'))
        self.assertIsNotNone(self.client.session.get('last_order_token'))
        self.assertIn('last_order_summary', self.client.session)


class BuyNowSessionCleanupTest(TestCase):
    """Test buy now session cleanup"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=50000,
            stock=10
        )
    
    def test_buy_now_clears_previous_session(self):
        """Test buy now clears previous session data"""
        session = self.client.session
        session['buy_now'] = True
        session['last_order_token'] = 'old-token'
        session.save()
        
        response = self.client.post(reverse('cartApp:buy_now'), {
            'product_id': str(self.product.pk),
            'quantity': 1
        })
        self.assertEqual(response.status_code, 200)
        
        # New token should be different
        new_token = self.client.session.get('last_order_token')
        self.assertIsNotNone(new_token)
        self.assertNotEqual(new_token, 'old-token')


class CheckoutBuyNowNoProductsTest(TestCase):
    """Test buy now checkout when purchases don't exist"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
    
    def test_buy_now_checkout_no_purchases(self):
        """Test buy now checkout when no purchases exist"""
        session = self.client.session
        session['buy_now'] = True
        session['last_order_token'] = str(uuid.uuid4())
        session.save()
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 400)


class ProductStockFieldTest(TestCase):
    """Test products with and without sold field"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.product = Merchandise.objects.create(
            name='Test Product',
            price=100000,
            stock=10
        )
    
    def test_checkout_updates_sold_if_exists(self):
        """Test that checkout updates sold field if it exists"""
        cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=cart, product=self.product, quantity=2, selected=True)
        
        response = self.client.post(reverse('cartApp:checkout'), {
            'address': 'Test Address',
            'payment_method': 'gopay'
        })
        self.assertEqual(response.status_code, 200)
        
        self.product.refresh_from_db()
        if hasattr(self.product, 'sold'):
            self.assertEqual(self.product.sold, 2)
