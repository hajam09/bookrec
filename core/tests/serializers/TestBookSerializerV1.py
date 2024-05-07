from django.test import TestCase

from core.serializers import BookSerializerV1


class BookSerializerV1Test(TestCase):
    def setUp(self):
        self.book_data = {
            'title': 'Test Book',
            'description': 'This is a test book',
            'isbn13': '9780123456789',
            'averageRating': 4.5,
            'categories': ['Fiction', 'Sci-Fi']
        }

    def test_valid_serializer_data(self):
        serializer = BookSerializerV1(data=self.book_data)
        self.assertTrue(serializer.is_valid())

    def test_invalid_serializer_data_missing_fields(self):
        # Removing required fields to make serializer data invalid
        del self.book_data['title']
        serializer = BookSerializerV1(data=self.book_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def test_invalid_serializer_data_invalid_rating(self):
        # Providing invalid averageRating (not a float)
        self.book_data['averageRating'] = 'not_a_float'
        serializer = BookSerializerV1(data=self.book_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('averageRating', serializer.errors)

    def test_invalid_serializer_data_invalid_categories(self):
        # Providing invalid categories (not a list)
        self.book_data['categories'] = 'Fiction'
        serializer = BookSerializerV1(data=self.book_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('categories', serializer.errors)
