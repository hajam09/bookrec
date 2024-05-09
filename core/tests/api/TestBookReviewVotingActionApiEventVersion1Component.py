from django.urls import reverse
from rest_framework.status import HTTP_200_OK

from bookrec.tests.BaseTestAjax import BaseTestAjax
from core.models import Book, BookReview


class BookReviewVotingActionApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('core:bookReviewVotingActionApiEventVersion1Component')) -> None:
        super(BookReviewVotingActionApiEventVersion1ComponentTest, self).setUp(path)
        self.login()

        self.book = Book.objects.create(
            title='Test Book',
            isbn13='1234567890123',
            authors=['Author 1'],
            categories=['Action']
        )

        self.review = BookReview.objects.create(
            book=self.book,
            creator=self.user,
            comment='Test comment',
            rating=4,
        )

    def testGivenUserHasNotUpVotedBeforeAndWantsToUpVote(self):
        self.assertFalse(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'UP'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testGivenUserHasNotDownVotedBeforeAndWantsToDownVote(self):
        self.assertFalse(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'DOWN'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertTrue(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testGivenUserHasUpVotedBeforeAndWantsToRemoveTheUpVote(self):
        self.review.likes.add(self.user)
        self.assertTrue(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'UP'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testGivenUserHasDownVotedBeforeAndWantsToRemoveTheDownVote(self):
        self.review.dislikes.add(self.user)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertTrue(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'DOWN'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testGivenUserHasUpVotedBeforeAndWantsToDownVoteNow(self):
        self.review.likes.add(self.user)
        self.assertTrue(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'DOWN'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertTrue(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testGivenUserHasDownVotedBeforeAndWantsToUpVoteNow(self):
        self.review.dislikes.add(self.user)
        self.assertFalse(self.user in self.review.likes.all())
        self.assertTrue(self.user in self.review.dislikes.all())

        data = {'id': self.review.id, 'direction': 'UP'}
        response = self.put(data)

        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertTrue(self.user in self.review.likes.all())
        self.assertFalse(self.user in self.review.dislikes.all())
        self.assertIn('review', response.data['data'])

    def testRaiseExceptionWhenInvalidDirectionIsPassed(self):
        with self.assertRaisesMessage(Exception, 'Invalid direction'):
            data = {'id': self.review.id, 'direction': 'NOTHING'}
            self.put(data)
