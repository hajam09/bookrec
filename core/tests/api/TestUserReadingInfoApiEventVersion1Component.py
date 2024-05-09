from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from bookrec.tests.BaseTestAjax import BaseTestAjax
from core.models import Book


class UserReadingInfoApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self, path=None) -> None:
        path = reverse('core:userReadingInfoApiEventVersion1Component', kwargs={'isbn13': '1234567890123'})
        super(UserReadingInfoApiEventVersion1ComponentTest, self).setUp(path)
        self.login()
        self.book = Book.objects.create(
            title='Test Book',
            isbn13='1234567890123',
            authors=['Author 1'],
            categories=['Action']
        )
        self.book.favouriteRead.add(self.user)
        self.book.readingNow.add(self.user)
        self.book.toRead.add(self.user)
        self.book.haveRead.add(self.user)

    def testGetUserReadingInfo(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['version'], '1.0.0')
        self.assertTrue(response.data['success'])
        self.assertTrue(response.data['data']['isInFavouriteRead'])
        self.assertTrue(response.data['data']['isInReadingNow'])
        self.assertTrue(response.data['data']['isInToRead'])
        self.assertTrue(response.data['data']['isInHasRead'])

    def testCheckIfUserHasAddedToFavouriteRead(self):
        self.book.favouriteRead.remove(self.user)
        self.assertFalse(self.user in self.book.favouriteRead.all())
        data = {'field': 'favouriteRead', 'action': 'add'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.book.favouriteRead.all())

    def testCheckIfUserHasRemovedFromFavouriteRead(self):
        self.assertTrue(self.user in self.book.favouriteRead.all())
        data = {'field': 'favouriteRead', 'action': 'remove'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.book.favouriteRead.all())

    def testCheckIfUserHasAddedToReadingNow(self):
        self.book.readingNow.remove(self.user)
        self.assertFalse(self.user in self.book.readingNow.all())
        data = {'field': 'readingNow', 'action': 'add'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.book.readingNow.all())

    def testCheckIfUserHasRemovedFromReadingNow(self):
        self.assertTrue(self.user in self.book.readingNow.all())
        data = {'field': 'readingNow', 'action': 'remove'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.book.readingNow.all())

    def testCheckIfUserHasAddedToReadNow(self):
        self.book.toRead.remove(self.user)
        self.assertFalse(self.user in self.book.toRead.all())
        data = {'field': 'toRead', 'action': 'add'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.book.toRead.all())

    def testCheckIfUserHasRemovedFromToReadNow(self):
        self.assertTrue(self.user in self.book.toRead.all())
        data = {'field': 'toRead', 'action': 'remove'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.book.toRead.all())

    def testCheckIfUserHasAddedToHaveRead(self):
        self.book.haveRead.remove(self.user)
        self.assertFalse(self.user in self.book.haveRead.all())
        data = {'field': 'haveRead', 'action': 'add'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.book.haveRead.all())

    def testCheckIfUserHasRemovedFromHaveRead(self):
        self.assertTrue(self.user in self.book.haveRead.all())
        data = {'field': 'haveRead', 'action': 'remove'}
        response = self.put(data)
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.book.haveRead.all())

    def testRaiseExceptionWhenInvalidFieldOrActionPerformed(self):
        with self.assertRaisesMessage(Exception, 'Invalid field: invalid or action: invalid'):
            data = {'field': 'invalid', 'action': 'invalid'}
            self.put(data)
