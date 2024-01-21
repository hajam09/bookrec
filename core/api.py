from http import HTTPStatus

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, FloatField, Func, F
from django.db.models.functions import Greatest, Cast
from rest_framework.response import Response
from rest_framework.views import APIView

from bookrec.operations import bookOperations
from core.models import Book, BookReview
from core.serializers import BookReviewSerializer, BookSerializerV1, BookReviewSerializerV2


class BookReviewActionApiEventVersion1Component(APIView):

    def post(self, request, *args, **kwargs):
        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        bookReview, created = BookReview.objects.get_or_create(
            book=book,
            creator_id=self.request.user.id,
            defaults={
                'comment': request.data.get('comment'),
                'rating': request.data.get('rating'),
            }
        )

        if not created:
            bookReview.comment = request.data.get('comment')
            bookReview.rating = request.data.get('rating')
            bookReview.edited = True
            bookReview.save(update_fields=['comment', 'rating', 'edited'])

        bookReview.likes.add(self.request.user)
        serializer = BookReviewSerializer(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def get(self, request, *args, **kwargs):
        bookReviews = BookReview.objects.select_related('creator').prefetch_related('likes', 'dislikes').filter(
            book__isbn13=kwargs.get('isbn13')
        )
        sortBy = request.GET.get('sort-by')

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
            raise Exception(f'Unknown sort by filter {sortBy}')

        paginator = Paginator(bookReviews, 10)
        page = request.GET.get('page')

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
        return Response(response, status=HTTPStatus.OK)

    def put(self, request, *args, **kwargs):
        bookReview = BookReview.objects.get(
            id=request.data.get('id'),
            book__isbn13=kwargs.get('isbn13'),
            creator_id=self.request.user.id
        )
        bookReview.comment = request.data.get('comment')
        bookReview.edited = True
        bookReview.save(update_fields=['comment', 'edited'])

        serializer = BookReviewSerializer(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def delete(self, request, *args, **kwargs):
        bookReview = BookReview.objects.filter(
            id=request.data.get('id'),
            book__isbn13=kwargs.get('isbn13'),
            creator_id=self.request.user.id,
        ).first()

        if bookReview is not None:
            bookReview.delete()

        response = {
            'version': '1.0.0',
            'success': True,
        }
        return Response(response, status=HTTPStatus.OK)


class UserShelfApiEventVersion1Component(APIView):
    def get(self, request, *args, **kwargs):
        shelf = request.GET.get('shelf')

        if shelf == 'ratedAndReviewed':
            reviews = BookReview.objects.filter(creator__id=self.request.user.id).select_related('book')
            data = BookReviewSerializerV2(reviews, many=True).data
        elif shelf == 'recentlyViewed':
            history = request.session.get('history', [])
            books = Book.objects.filter(isbn13__in=history)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'favouriteRead':
            books = Book.objects.filter(favouriteRead__id=self.request.user.id)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'readingNow':
            books = Book.objects.filter(readingNow__id=self.request.user.id)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'toRead':
            books = Book.objects.filter(toRead__id=self.request.user.id)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'haveRead':
            books = Book.objects.filter(haveRead__id=self.request.user.id)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'recommendedBooks':
            books = bookOperations.booksBasedOnRating(self.request)
            data = BookSerializerV1(books, many=True).data
        elif shelf == 'favouriteGenreBooks':
            books = bookOperations.booksBasedOnFavouriteGenres(self.request)
            data = BookSerializerV1(books, many=True).data
        else:
            raise Exception(f'Unknown shelf: {shelf}')
        response = {
            'version': '1.0.0',
            'success': True,
            'data': data,
        }
        return Response(response, status=HTTPStatus.OK)


class UserReadingInfoApiEventVersion1Component(APIView):

    def get(self, request, *args, **kwargs):
        favouriteRead = Book.objects.filter(favouriteRead=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInReadingNow = Book.objects.filter(readingNow=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInToRead = Book.objects.filter(toRead=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        isInHaveRead = Book.objects.filter(haveRead=self.request.user, isbn13=kwargs.get('isbn13')).exists()
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'isInFavouriteRead': favouriteRead,
                'isInReadingNow': isInReadingNow,
                'isInToRead': isInToRead,
                'isInHasRead': isInHaveRead
            }
        }
        return Response(response)

    def put(self, request, *args, **kwargs):
        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        if book is not None:
            field = request.data.get('field')
            action = request.data.get('action')
            try:
                getattr(getattr(book, field), action)(self.request.user)
            except TypeError:
                raise Exception('Invalid field: {} or action: {}'.format(field, action))

        response = {
            'version': '1.0.0',
            'success': True
        }
        return Response(response, status=HTTPStatus.OK)


class BookReviewVotingActionApiEventVersion1Component(APIView):
    def put(self, request, *args, **kwargs):
        bookReview = BookReview.objects.select_related('creator').prefetch_related('likes', 'dislikes').get(
            id=request.data.get('id')
        )

        if request.data.get('direction') == 'UP':
            if self.request.user not in bookReview.likes.all():
                bookReview.likes.add(self.request.user)
            else:
                bookReview.likes.remove(self.request.user)

            if self.request.user in bookReview.dislikes.all():
                bookReview.dislikes.remove(self.request.user)
        elif request.data.get('direction') == 'DOWN':
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
        return Response(response, status=HTTPStatus.OK)
