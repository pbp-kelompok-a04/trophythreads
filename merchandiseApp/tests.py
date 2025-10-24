from django.test import TestCase
from .models import Merchandise

class MerchandiseTestCase(TestCase):
    def setUp(self):
        # Set up any initial data for your tests here
        Merchandise.objects.create(name='Test Merchandise', price=10.99, category='Test Category', stock=100, thumbnail='test.jpg', description='Test Description', is_featured=True)

    def test_model_creation(self):
        """Test that the model is created correctly."""
        obj = Merchandise.objects.get(name='Test Merchandise')
        self.assertEqual(obj.price, 10.99)

    def test_model_str(self):
        """Test the string representation of the model."""
        obj = Merchandise.objects.get(name='Test Merchandise')
        self.assertEqual(str(obj), 'Test Merchandise')
