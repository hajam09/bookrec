from unittest import skip

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from bookrec.tests.BaseTestAjax import BaseTestAjax
from core.models import Book, BookReview


class BookReviewActionApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self, path=None) -> None:
        path = reverse('core:bookReviewActionApiEventVersion1Component', kwargs={'isbn13': '1234567890123'})
        super(BookReviewActionApiEventVersion1ComponentTest, self).setUp(path)
        self.login()
        self.book = Book.objects.create(
            title='Test Book',
            isbn13='1234567890123',
            authors=['Author 1'],
            categories=['Action']
        )

    def testCreateBookReview(self):
        data = {
            'comment': 'This is a great book!',
            'rating': 4
        }
        response = self.post(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('review' in response.data['data'])
        self.assertEqual(response.data['data']['review']['comment'], data['comment'])
        self.assertEqual(response.data['data']['review']['id'], self.book.id)
        self.assertEqual(response.data['data']['review']['name'], 'Test User')
        self.assertFalse(response.data['data']['review']['edited'])
        self.assertEqual(response.data['data']['review']['comment'], 'This is a great book!')
        self.assertEqual(response.data['data']['review']['netVote'], 1)
        self.assertTrue(response.data['data']['review']['canEdit'])
        self.assertEqual(response.data['data']['review']['rating'], 4)
        self.assertTrue(response.data['data']['review']['userVote']['upVoted'])
        self.assertFalse(response.data['data']['review']['userVote']['downVoted'])
        self.assertTrue(BookReview.objects.filter(book=self.book, creator=self.user).exists())

    def testUpdateBookReview(self):
        BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Initial comment',
            rating=3
        )
        data = {
            'comment': 'Updated comment',
            'rating': 4
        }
        response = self.post(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('review' in response.data['data'])
        self.assertEqual(response.data['data']['review']['comment'], data['comment'])
        self.assertEqual(response.data['data']['review']['id'], self.book.id)
        self.assertEqual(response.data['data']['review']['name'], 'Test User')
        self.assertTrue(response.data['data']['review']['edited'])
        self.assertEqual(response.data['data']['review']['comment'], 'Updated comment')
        self.assertEqual(response.data['data']['review']['netVote'], 1)
        self.assertTrue(response.data['data']['review']['canEdit'])
        self.assertEqual(response.data['data']['review']['rating'], 4)
        self.assertTrue(response.data['data']['review']['userVote']['upVoted'])
        self.assertFalse(response.data['data']['review']['userVote']['downVoted'])
        self.assertTrue(BookReview.objects.filter(book=self.book, creator=self.user).exists())
        updatedReview = BookReview.objects.get(book=self.book, creator=self.user)
        self.assertEqual(updatedReview.comment, data['comment'])
        self.assertEqual(updatedReview.rating, data['rating'])
        self.assertTrue(updatedReview.edited)

    def testCreateDuplicateBookReview(self):
        BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Initial comment',
            rating=3
        )
        data = {
            'comment': 'Duplicate comment',
            'rating': 4
        }
        response = self.post(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['review']['id'], self.book.id)
        self.assertEqual(response.data['data']['review']['name'], 'Test User')
        self.assertTrue(response.data['data']['review']['edited'])
        self.assertEqual(response.data['data']['review']['comment'], 'Duplicate comment')
        self.assertEqual(response.data['data']['review']['netVote'], 1)
        self.assertTrue(response.data['data']['review']['canEdit'])
        self.assertEqual(response.data['data']['review']['rating'], 4)
        self.assertTrue(response.data['data']['review']['userVote']['upVoted'])
        self.assertFalse(response.data['data']['review']['userVote']['downVoted'])
        self.assertTrue(BookReview.objects.filter(book=self.book, creator=self.user).exists())

    def testUpdateBookReviewWithValidData(self):
        review = BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Initial comment',
            rating=4
        )
        review.likes.add(self.user)
        data = {
            'id': review.id,
            'comment': 'Updated comment',
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue('review' in response.data['data'])
        self.assertEqual(response.data['data']['review']['comment'], data['comment'])
        self.assertEqual(response.data['data']['review']['id'], self.book.id)
        self.assertEqual(response.data['data']['review']['name'], 'Test User')
        self.assertTrue(response.data['data']['review']['edited'])
        self.assertEqual(response.data['data']['review']['comment'], 'Updated comment')
        self.assertEqual(response.data['data']['review']['netVote'], 1)
        self.assertTrue(response.data['data']['review']['canEdit'])
        self.assertEqual(response.data['data']['review']['rating'], 4)
        self.assertTrue(response.data['data']['review']['userVote']['upVoted'])
        self.assertFalse(response.data['data']['review']['userVote']['downVoted'])
        updated_review = BookReview.objects.get(id=review.id)
        self.assertEqual(updated_review.comment, data['comment'])
        self.assertTrue(updated_review.edited)

    @skip('Not implemented')
    def testUpdateBookReviewWithInvalidData(self):
        review = BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Initial comment',
            rating=3
        )

        data = {
            'id': 999,  # Assuming no review exists with ID 999
            'comment': 'Updated comment',
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @skip('Not implemented')
    def testUpdateBookReviewOfOtherUser(self):
        otherUser = User.objects.create_user(username='otheruser', password='testpassword')
        review = BookReview.objects.create(
            book=self.book,
            creator=otherUser,  # Creating review with another user
            comment='Initial comment',
            rating=3
        )
        data = {
            'id': review.id,
            'comment': 'Updated comment',
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteBookReview(self):
        review = BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Test comment',
            rating=5
        )
        data = {
            'id': review.id,
        }
        response = self.delete(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(BookReview.objects.filter(id=review.id).exists())
        self.assertTrue('success' in response.data)
        self.assertTrue(response.data['success'])
