from django.test import TestCase

from core.serializers import BookSerializerV1


class BookSerializerV1Test(TestCase):
    def setUp(self):
        self.bookData = {
            'title': 'Test Book',
            'description': 'This is a test book',
            'isbn13': '9780123456789',
            'averageRating': 4.5,
            'categories': ['Fiction', 'Sci-Fi']
        }

    def testValidSerializerData(self):
        serializer = BookSerializerV1(data=self.bookData)
        self.assertTrue(serializer.is_valid())

    def testInvalidSerializerDataMissingFields(self):
        # Removing required fields to make serializer data invalid
        del self.bookData['title']
        serializer = BookSerializerV1(data=self.bookData)
        self.assertFalse(serializer.is_valid())
        self.assertIn('title', serializer.errors)

    def testInvalidSerializerDataInvalidRating(self):
        # Providing invalid averageRating (not a float)
        self.bookData['averageRating'] = 'not_a_float'
        serializer = BookSerializerV1(data=self.bookData)
        self.assertFalse(serializer.is_valid())
        self.assertIn('averageRating', serializer.errors)

    def testInvalidSerializerDataInvalidCategories(self):
        # Providing invalid categories (not a list)
        self.bookData['categories'] = 'Fiction'
        serializer = BookSerializerV1(data=self.bookData)
        self.assertFalse(serializer.is_valid())
        self.assertIn('categories', serializer.errors)
