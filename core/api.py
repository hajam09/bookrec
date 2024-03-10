import json
from http import HTTPStatus
from json import JSONDecodeError

from django.http import JsonResponse
from django.views import View

from core.models import Book, BookReview
from core.serializers import BookReviewSerializer


class UserReadingInfoApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        isInFavourite = Book.objects.filter(isFavourite=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInReadingNow = Book.objects.filter(readingNow=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInToRead = Book.objects.filter(toRead=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInHaveRead = Book.objects.filter(haveRead=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'isInFavourite': isInFavourite,
                'isInReadingNow': isInReadingNow,
                'isInToRead': isInToRead,
                'isInHasRead': isInHaveRead
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        try:
            put = json.loads(self.request.body)
        except JSONDecodeError:
            put = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        if book is not None:
            try:
                getattr(getattr(book, put.get('field')), put.get('action'))(self.request.user)
            except TypeError:
                raise Exception('Invalid field: {} or action: {}'.format(put.get('field'), put.get('action')))

        response = {
            'success': True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BookReviewActionApiEventVersion1Component(View):
    def get(self, *args, **kwargs):
        bookReviews = BookReview.objects.filter(book__isbn13=kwargs.get('isbn13'))
        bookReviewSerializer = BookReviewSerializer(bookReviews, many=True, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'reviews': bookReviewSerializer.data
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def post(self, *args, **kwargs):

        try:
            post = json.loads(self.request.body)
        except JSONDecodeError:
            post = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()

        bookReview = BookReview.objects.create(
            book=book,
            creator_id=self.request.user.id,
            description=post.get('comment'),
            rating=1,
        )

        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)
