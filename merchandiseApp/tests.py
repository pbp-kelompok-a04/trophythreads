from django.test import TestCase
from .models import YourModel  # Replace with your actual model

class YourModelTestCase(TestCase):
    def setUp(self):
        # Set up any initial data for your tests here
        YourModel.objects.create(field1='value1', field2='value2')  # Replace with actual fields

    def test_model_creation(self):
        """Test that the model is created correctly."""
        obj = YourModel.objects.get(field1='value1')
        self.assertEqual(obj.field2, 'value2')  # Replace with actual fields

    def test_model_str(self):
        """Test the string representation of the model."""
        obj = YourModel.objects.get(field1='value1')
        self.assertEqual(str(obj), 'Expected String Representation')  # Replace with actual expected value