import json
from http import HTTPStatus
from json import JSONDecodeError

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, FloatField, Func, F
from django.db.models.functions import Greatest, Cast
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
            body = json.loads(self.request.body)
        except JSONDecodeError:
            body = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        if book is not None:
            try:
                getattr(getattr(book, body.get('field')), body.get('action'))(self.request.user)
            except TypeError:
                raise Exception('Invalid field: {} or action: {}'.format(body.get('field'), body.get('action')))

        response = {
            'version': '1.0.0',
            'success': True
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BookReviewActionApiEventVersion1Component(View):

    def get(self, *args, **kwargs):
        bookReviews = BookReview.objects.select_related('creator').prefetch_related('likes', 'dislikes').filter(
            book__isbn13=kwargs.get('isbn13')
        )
        sortBy = self.request.GET.get('sort-by')

        if sortBy == 'top':
            bookReviews = bookReviews.annotate(
                netVotes=Count('likes', distinct=True) - Count('dislikes', distinct=True)
            ).order_by('-netVotes')
        elif sortBy == 'bottom':
            bookReviews = bookReviews.annotate(
                netVotes=Count('dislikes', distinct=True) - Count('likes', distinct=True)
            ).order_by('-netVotes')
        elif sortBy == 'new':
            bookReviews = bookReviews.order_by('-createdDateTime')
        elif sortBy == 'old':
            bookReviews = bookReviews.order_by('createdDateTime')
        elif sortBy == 'controversial':
            bookReviews = bookReviews.annotate(
                likeCount=Count('likes', distinct=True),
                dislikesCount=Count('dislikes', distinct=True),
                netVotes=Func(F('likeCount') - F('dislikesCount'), function='abs'),
                maxOfVotes=Greatest(F('likeCount'), F('dislikesCount')),
                controversyScore=Cast(F('netVotes'), FloatField()) / Cast(F('maxOfVotes'), FloatField()) * 100
            ).order_by('controversyScore')
        else:
            raise Exception('Unknown sort by filter ', sortBy)

        paginator = Paginator(bookReviews, 10)
        page = self.request.GET.get('page')

        try:
            bookReviews = paginator.page(page)
        except PageNotAnInteger:
            bookReviews = paginator.page(1)
        except EmptyPage:
            bookReviews = paginator.page(paginator.num_pages)

        serializer = BookReviewSerializer(bookReviews.object_list, many=True, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'reviews': serializer.data,
                'hasMore': bookReviews.has_next()
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
        bookReview.likes.add(self.request.user)
        serializer = BookReviewSerializer(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def delete(self, *args, **kwargs):
        try:
            body = json.loads(self.request.body)
        except JSONDecodeError:
            body = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        BookReview.objects.filter(id=body.get('id'), creator=self.request.user).delete()
        response = {
            'version': '1.0.0',
            'success': True,
        }
        return JsonResponse(response, status=HTTPStatus.OK)

    def put(self, *args, **kwargs):
        try:
            body = json.loads(self.request.body)
        except JSONDecodeError:
            body = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        bookReview = BookReview.objects.get(id=body.get('id'), book__isbn13=kwargs.get('isbn13'))
        bookReview.description = body.get('comment')
        bookReview.edited = True
        bookReview.save()

        serializer = BookReviewSerializer(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)


class BookReviewVotingActionApiEventVersion1Component(View):

    def put(self, *args, **kwargs):
        try:
            body = json.loads(self.request.body)
        except JSONDecodeError:
            body = json.loads(self.request.body.decode().replace('"', "'").replace("'", '"'))

        bookReview = BookReview.objects.select_related('creator').prefetch_related('likes', 'dislikes').get(
            id=body.get('id')
        )

        if body.get('direction') == 'UP':
            if self.request.user not in bookReview.likes.all():
                bookReview.likes.add(self.request.user)
            else:
                bookReview.likes.remove(self.request.user)

            if self.request.user in bookReview.dislikes.all():
                bookReview.dislikes.remove(self.request.user)
        elif body.get('direction') == 'DOWN':
            if self.request.user not in bookReview.dislikes.all():
                bookReview.dislikes.add(self.request.user)
            else:
                bookReview.dislikes.remove(self.request.user)

            if self.request.user in bookReview.likes.all():
                bookReview.likes.remove(self.request.user)
        else:
            raise Exception('Invalid direction')

        serializer = BookReviewSerializer(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return JsonResponse(response, status=HTTPStatus.OK)
