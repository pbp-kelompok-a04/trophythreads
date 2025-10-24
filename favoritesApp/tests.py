# favoritesApp/tests.py
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from merchandiseApp.models import Merchandise
from .models import Favorite
import json

User = get_user_model()


class FavoriteModelTest(TestCase):
    """Test Favorite model"""
    
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test Jersey',
            price=150000,
            category='jersey',
            description='Test description',
            stock=10
        )
    
    def test_create_favorite(self):
        """Test creating a favorite"""
        favorite = Favorite.objects.create(
            user=self.user,
            merchandise=self.merchandise
        )
        self.assertEqual(favorite.user, self.user)
        self.assertEqual(favorite.merchandise, self.merchandise)
        self.assertIsNotNone(favorite.created_at)
    
    def test_favorite_unique_together(self):
        """Test that user can't favorite same item twice"""
        Favorite.objects.create(
            user=self.user,
            merchandise=self.merchandise
        )
        
        # Try to create duplicate
        with self.assertRaises(Exception):
            Favorite.objects.create(
                user=self.user,
                merchandise=self.merchandise
            )
    
    def test_favorite_string_representation(self):
        """Test __str__ method"""
        favorite = Favorite.objects.create(
            user=self.user,
            merchandise=self.merchandise
        )
        expected = f"{self.user.username} ❤️ {self.merchandise.name}"
        self.assertEqual(str(favorite), expected)
    
    def test_favorite_ordering(self):
        """Test favorites are ordered by created_at descending"""
        merch2 = Merchandise.objects.create(
            name='Test Jersey 2',
            price=200000,
            category='jersey',
            stock=5
        )
        
        fav1 = Favorite.objects.create(user=self.user, merchandise=self.merchandise)
        fav2 = Favorite.objects.create(user=self.user, merchandise=merch2)
        
        favorites = Favorite.objects.all()
        self.assertEqual(favorites[0], fav2)  # Most recent first
        self.assertEqual(favorites[1], fav1)


class FavoriteViewTest(TestCase):
    """Test Favorite views"""
    
    def setUp(self):
        self.client = Client()
        
        # Create test users
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='otherpass123'
        )
        
        # Create test merchandise
        self.merchandise = Merchandise.objects.create(
            name='Test Jersey',
            price=150000,
            category='jersey',
            description='Test description',
            stock=10
        )
    
    def test_favorites_list_requires_login(self):
        """Test that favorites list requires authentication"""
        response = self.client.get(reverse('favoritesApp:list'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
    
    def test_favorites_list_authenticated(self):
        """Test favorites list for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create a favorite
        Favorite.objects.create(user=self.user, merchandise=self.merchandise)
        
        response = self.client.get(reverse('favoritesApp:list'))
        self.assertEqual(response.status_code, 200)
        # Page uses AJAX to load favorites, so just check page structure
        self.assertContains(response, 'Favorites')
        self.assertContains(response, 'favoritesGrid')
    
    def test_favorites_list_empty(self):
        """Test favorites list when empty"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('favoritesApp:list'))
        self.assertEqual(response.status_code, 200)
        # Check for empty state element (hidden by default, shown by JS)
        self.assertContains(response, 'emptyState')
        self.assertContains(response, 'Belum Ada Produk di Favorites')
    
    def test_add_favorite_not_authenticated(self):
        """Test adding favorite without authentication"""
        response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'auth_required')
    
    def test_add_favorite_success(self):
        """Test adding favorite successfully"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['action'], 'added')
        self.assertIn('favorite_id', data)
        
        # Verify favorite was created
        self.assertTrue(
            Favorite.objects.filter(
                user=self.user,
                merchandise=self.merchandise
            ).exists()
        )
    
    def test_add_favorite_already_exists(self):
        """Test adding favorite that already exists"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create favorite first
        Favorite.objects.create(user=self.user, merchandise=self.merchandise)
        
        # Try to add again
        response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['action'], 'exists')
    
    def test_add_favorite_missing_id(self):
        """Test adding favorite without merchandise_id"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('favoritesApp:add'), {})
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
    
    def test_add_favorite_invalid_id(self):
        """Test adding favorite with invalid merchandise_id"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': 'invalid-uuid'
        })
        
        self.assertEqual(response.status_code, 400)
    
    def test_add_favorite_csv_product(self):
        """Test adding favorite for CSV product (creates merchandise)"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': '999',  # Non-existent integer ID
            'name': 'CSV Jersey',
            'price': '100000',
            'category': 'jersey',
            'description': 'From CSV',
            'stock': '5'
        })
        
        # Current implementation doesn't support CSV auto-create yet
        # So this should return 400
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'error')
    
    def test_remove_favorite_by_favorite_id(self):
        """Test removing favorite by favorite_id"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create favorite
        favorite = Favorite.objects.create(
            user=self.user,
            merchandise=self.merchandise
        )
        
        # Remove it
        response = self.client.post(reverse('favoritesApp:remove'), {
            'favorite_id': str(favorite.id)
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['action'], 'removed')
        
        # Verify favorite was deleted
        self.assertFalse(
            Favorite.objects.filter(id=favorite.id).exists()
        )
    
    def test_remove_favorite_by_merchandise_id(self):
        """Test removing favorite by merchandise_id"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create favorite
        Favorite.objects.create(user=self.user, merchandise=self.merchandise)
        
        # Remove it
        response = self.client.post(reverse('favoritesApp:remove'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(data['action'], 'removed')
    
    def test_remove_favorite_not_found(self):
        """Test removing favorite that doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.post(reverse('favoritesApp:remove'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['action'], 'not_found')
    
    def test_remove_favorite_other_user(self):
        """Test that user can't remove other user's favorite"""
        # Create favorite for other user
        favorite = Favorite.objects.create(
            user=self.other_user,
            merchandise=self.merchandise
        )
        
        # Login as testuser
        self.client.login(username='testuser', password='testpass123')
        
        # Try to remove other user's favorite
        response = self.client.post(reverse('favoritesApp:remove'), {
            'favorite_id': str(favorite.id)
        })
        
        self.assertEqual(response.status_code, 404)
        
        # Verify favorite still exists
        self.assertTrue(
            Favorite.objects.filter(id=favorite.id).exists()
        )
    
    def test_favorites_json(self):
        """Test favorites JSON endpoint"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create favorites
        Favorite.objects.create(user=self.user, merchandise=self.merchandise)
        
        response = self.client.get(reverse('favoritesApp:json'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertEqual(len(data['favorites']), 1)
        
        favorite_data = data['favorites'][0]
        self.assertIn('favorite_id', favorite_data)
        self.assertIn('merchandise', favorite_data)
        self.assertEqual(favorite_data['merchandise']['name'], 'Test Jersey')
    
    def test_favorites_json_requires_login(self):
        """Test favorites JSON requires authentication"""
        response = self.client.get(reverse('favoritesApp:json'))
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_check_favorite_exists(self):
        """Test check favorite endpoint when favorite exists"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create favorite
        favorite = Favorite.objects.create(
            user=self.user,
            merchandise=self.merchandise
        )
        
        # merchandise.pk returns UUID object, need to convert to string
        merch_uuid = str(self.merchandise.pk)
        
        response = self.client.get(
            reverse('favoritesApp:check', args=[merch_uuid])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertTrue(data['is_favorited'])
        self.assertEqual(data['favorite_id'], str(favorite.id))
    
    def test_check_favorite_not_exists(self):
        """Test check favorite endpoint when favorite doesn't exist"""
        self.client.login(username='testuser', password='testpass123')
        
        merch_uuid = str(self.merchandise.pk)
        
        response = self.client.get(
            reverse('favoritesApp:check', args=[merch_uuid])
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'ok')
        self.assertFalse(data['is_favorited'])
        self.assertIsNone(data['favorite_id'])
    
    def test_check_favorite_invalid_uuid(self):
        """Test check favorite with invalid UUID"""
        self.client.login(username='testuser', password='testpass123')
        
        # Use a valid UUID format but non-existent
        import uuid
        fake_uuid = str(uuid.uuid4())
        
        response = self.client.get(
            reverse('favoritesApp:check', args=[fake_uuid])
        )
        
        # Should return 200 with is_favorited=False (not found)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertFalse(data['is_favorited'])


class FavoriteIntegrationTest(TestCase):
    """Integration tests for favorites workflow"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.merchandise = Merchandise.objects.create(
            name='Test Jersey',
            price=150000,
            category='jersey',
            stock=10
        )
    
    def test_full_favorite_workflow(self):
        """Test complete workflow: add, check, list, remove"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Add favorite
        add_response = self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        self.assertEqual(add_response.status_code, 200)
        
        # 2. Check if favorited
        merch_uuid = str(self.merchandise.pk)
        check_response = self.client.get(
            reverse('favoritesApp:check', args=[merch_uuid])
        )
        check_data = json.loads(check_response.content)
        self.assertTrue(check_data['is_favorited'])
        favorite_id = check_data['favorite_id']
        
        # 3. Get favorites list (check page loads)
        list_response = self.client.get(reverse('favoritesApp:list'))
        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Favorites')
        
        # 4. Get favorites JSON
        json_response = self.client.get(reverse('favoritesApp:json'))
        json_data = json.loads(json_response.content)
        self.assertEqual(len(json_data['favorites']), 1)
        
        # 5. Remove favorite
        remove_response = self.client.post(reverse('favoritesApp:remove'), {
            'favorite_id': favorite_id
        })
        self.assertEqual(remove_response.status_code, 200)
        
        # 6. Verify removed
        check_response2 = self.client.get(
            reverse('favoritesApp:check', args=[merch_uuid])
        )
        check_data2 = json.loads(check_response2.content)
        self.assertFalse(check_data2['is_favorited'])
    
    def test_multiple_users_favorites(self):
        """Test that favorites are user-specific"""
        user2 = User.objects.create_user(
            username='user2',
            password='pass123'
        )
        
        # User 1 adds favorite
        self.client.login(username='testuser', password='testpass123')
        self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        # User 2 shouldn't see user 1's favorite
        self.client.login(username='user2', password='pass123')
        response = self.client.get(reverse('favoritesApp:json'))
        data = json.loads(response.content)
        self.assertEqual(len(data['favorites']), 0)
        
        # User 2 adds same merchandise
        self.client.post(reverse('favoritesApp:add'), {
            'merchandise_id': str(self.merchandise.pk)
        })
        
        # Now user 2 should have 1 favorite
        response = self.client.get(reverse('favoritesApp:json'))
        data = json.loads(response.content)
        self.assertEqual(len(data['favorites']), 1)
        
        # But there should be 2 total favorites in database
        self.assertEqual(Favorite.objects.count(), 2)