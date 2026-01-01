from http import HTTPStatus

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, FloatField, Func, F
from django.db.models import Exists, OuterRef
from django.db.models.functions import Greatest, Cast
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookrec.operations import (
    emailOperations,
    generalOperations,
    logOperations
)
from core.models import (
    Book,
    BookReview,
    Profile,
    UserActivityLog
)
from core.serializers import (
    BookReviewSerializerV1,
    BookReviewSerializerV3,
    BookReviewSerializerV4,
    BookSerializerV3,
    UserAndProfileSerializer,
    UserActivityLogSerializer,
    BasicUserActivityLogSerializer,
    UserActivityFilterSerializer,
)


class RequestAccountDeleteCodeApiVersion1(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        emailOperations.sendEmailForAccountDeletionCode(self.request.user)
        logOperations.log(self.request, UserActivityLog.Action.REQUEST_ACCOUNT_DELETE_CODE)
        response = {
            'success': True,
            'data': {
                'type': 'success',
                'message': 'Check your email for the code.'
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def delete(self, request, *args, **kwargs):
        prtg = PasswordResetTokenGenerator()
        if not prtg.check_token(self.request.user, self.request.data.get('code')):
            response = {
                'success': False,
                'data': {
                    'type': 'danger',
                    'message': 'Account delete code is incorrect.'
                }
            }
            return Response(response, status=HTTPStatus.BAD_REQUEST)

        generalOperations.redactUserData(self.request.user)
        logOperations.log(self.request, UserActivityLog.Action.DELETE_ACCOUNT)
        response = {
            'success': True,
            'data': {
                'type': 'success',
                'message': 'Account deleted successfully.'
            }
        }
        return Response(response, status=HTTPStatus.OK)


class BookReviewActionApiVersion1(APIView):
    class CustomIsAuthenticated(IsAuthenticated):
        def has_permission(self, request, view):
            if request.method in ['POST', 'PUT', 'DELETE']:
                return super().has_permission(request, view)
            return True

    permission_classes = [CustomIsAuthenticated]

    def post(self, request, *args, **kwargs):
        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        bookReview, created = BookReview.objects.get_or_create(
            book=book,
            creator=self.request.user,
            defaults={
                'comment': request.data.get('comment'),
                'rating': int(request.data.get('rating')),
            }
        )

        data = {'book-isbn13': kwargs.get('isbn13'), 'book-title': book.title}

        if not created:
            bookReview.comment = request.data.get('comment')
            bookReview.rating = int(request.data.get('rating'))
            bookReview.edited = True
            bookReview.save(update_fields=['comment', 'rating', 'edited'])
            logOperations.log(request, UserActivityLog.Action.EDIT_COMMENT, data)
        else:
            logOperations.log(request, UserActivityLog.Action.ADD_COMMENT, data)

        bookReview.likes.add(self.request.user)
        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})
        response = {
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

        serializer = BookReviewSerializerV1(bookReviews.object_list, many=True, context={'request': self.request})

        response = {
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
            creator=self.request.user
        )
        bookReview.comment = request.data.get('comment')
        bookReview.edited = True
        bookReview.save(update_fields=['comment', 'edited'])
        logOperations.log(
            request,
            UserActivityLog.Action.EDIT_COMMENT,
            {'book-isbn13': kwargs.get('isbn13'), 'book-title': bookReview.book.title}
        )

        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})
        response = {
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def delete(self, request, *args, **kwargs):
        bookReview = get_object_or_404(
            BookReview.objects.select_related('book'),
            id=request.data.get('id'),
            book__isbn13=kwargs.get('isbn13'),
            creator=self.request.user
        )

        logOperations.log(
            request,
            UserActivityLog.Action.DELETE_COMMENT,
            {'book-isbn13': kwargs.get('isbn13'), 'book-title': bookReview.book.title}
        )
        bookReview.delete()

        response = {
            'success': True,
        }
        return Response(response, status=HTTPStatus.OK)


class UserReadingInfoApiVersion1(APIView):
    permission_classes = [IsAuthenticated]
    LOG_ACTIONS = {
        'favouriteRead': {
            'add': UserActivityLog.Action.ADD_TO_FAVOURITES,
            'remove': UserActivityLog.Action.REMOVE_FROM_FAVOURITES,
        },
        'readingNow': {
            'add': UserActivityLog.Action.ADD_TO_READING_NOW,
            'remove': UserActivityLog.Action.REMOVE_FROM_READING_NOW,
        },
        'toRead': {
            'add': UserActivityLog.Action.ADD_TO_TO_READ,
            'remove': UserActivityLog.Action.REMOVE_FROM_TO_READ,
        },
        'haveRead': {
            'add': UserActivityLog.Action.ADD_TO_HAVE_READ,
            'remove': UserActivityLog.Action.REMOVE_FROM_HAVE_READ,
        }
    }

    def get(self, request, *args, **kwargs):
        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).annotate(
            isInFavouriteRead=Exists(Book.objects.filter(favouriteRead=self.request.user, pk=OuterRef('pk'))),
            isInReadingNow=Exists(Book.objects.filter(readingNow=self.request.user, pk=OuterRef('pk'))),
            isInToRead=Exists(Book.objects.filter(toRead=self.request.user, pk=OuterRef('pk'))),
            isInHaveRead=Exists(Book.objects.filter(haveRead=self.request.user, pk=OuterRef('pk'))),
        ).first()
        response = {
            'success': True,
            'data': {
                'isInFavouriteRead': book.isInFavouriteRead,
                'isInReadingNow': book.isInReadingNow,
                'isInToRead': book.isInToRead,
                'isInHasRead': book.isInHaveRead,
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
                logOperations.log(
                    request,
                    self.LOG_ACTIONS[field][action],
                    {'book-isbn13': kwargs.get('isbn13'), 'book-title': book.title}
                )
            except (TypeError, AttributeError):
                raise Exception('Invalid field: {} or action: {}'.format(field, action))

        response = {
            'success': True
        }
        return Response(response, status=HTTPStatus.OK)


class BookReviewVotingApiVersion1(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, *args, **kwargs):
        bookReview = BookReview.objects.select_related('creator').prefetch_related('likes', 'dislikes').get(
            id=request.data.get('id')
        )
        data = {'book-title': bookReview.book.title, 'book-isbn13': bookReview.book.isbn13}

        if request.data.get('direction') == 'UP':
            if self.request.user not in bookReview.likes.all():
                bookReview.likes.add(self.request.user)
                logOperations.log(request, UserActivityLog.Action.ADD_LIKE_TO_COMMENT, data)
            else:
                bookReview.likes.remove(self.request.user)
                logOperations.log(request, UserActivityLog.Action.REMOVE_LIKE_FROM_COMMENT, data)

            if self.request.user in bookReview.dislikes.all():
                bookReview.dislikes.remove(self.request.user)
        elif request.data.get('direction') == 'DOWN':
            if self.request.user not in bookReview.dislikes.all():
                bookReview.dislikes.add(self.request.user)
                logOperations.log(request, UserActivityLog.Action.ADD_DISLIKE_TO_COMMENT, data)
            else:
                bookReview.dislikes.remove(self.request.user)
                logOperations.log(request, UserActivityLog.Action.REMOVE_DISLIKE_FROM_COMMENT, data)

            if self.request.user in bookReview.likes.all():
                bookReview.likes.remove(self.request.user)
        else:
            raise Exception('Invalid direction')

        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})

        response = {
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)


class UserActivityApiVersion1(APIView):
    permission_classes = [IsAuthenticated]

    class UserActivityPagination(PageNumberPagination):
        page_size = 20

    def get(self, request, *args, **kwargs):
        data = request.GET.copy()
        if 'sort-by' in data:
            data['sort_by'] = data.get('sort-by')

        serializer = UserActivityFilterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        sortBy = serializer.validated_data['sort_by']

        activities = UserActivityLog.objects.filter(user=request.user)
        if sortBy == 'new':
            activities = activities.order_by('-timeStamp')
        else:
            activities = activities.order_by('timeStamp')

        paginator = self.UserActivityPagination()
        page = paginator.paginate_queryset(activities, request)
        serializer = UserActivityLogSerializer(page, many=True)
        return paginator.get_paginated_response({
            'success': True,
            'activities': serializer.data,
        })


class UserDataBaseApi:
    def getUserData(self):
        user = getattr(getattr(self, 'request'), 'user')

        profile = Profile.objects.select_related('user').get(user=user)
        userAndProfileSerializer = UserAndProfileSerializer(profile)
        favouriteReadBooks = Book.objects.filter(favouriteRead=user).distinct()
        favouriteReadSerializer = BookSerializerV3(favouriteReadBooks, many=True)
        readingNowBooks = Book.objects.filter(readingNow=user).distinct()
        readingNowSerializer = BookSerializerV3(readingNowBooks, many=True)
        toReadBooks = Book.objects.filter(toRead=user).distinct()
        toReadSerializer = BookSerializerV3(toReadBooks, many=True)
        haveReadBooks = Book.objects.filter(haveRead=user).distinct()
        haveReadSerializer = BookSerializerV3(haveReadBooks, many=True)
        bookReviews = BookReview.objects.filter(creator=user).select_related('book').prefetch_related(
            'likes', 'dislikes'
        ).distinct()
        bookReviewsSerializer = BookReviewSerializerV3(bookReviews, many=True)

        likedBookReviews = BookReview.objects.filter(likes=user).select_related('book').distinct()
        likedBookReviewsSerializer = BookReviewSerializerV4(likedBookReviews, many=True)
        dislikedBookReviews = BookReview.objects.filter(dislikes=user).select_related('book').distinct()
        dislikedBookReviewsSerializer = BookReviewSerializerV4(dislikedBookReviews, many=True)

        activities = UserActivityLog.objects.filter(user=user)
        activitiesSerializer = BasicUserActivityLogSerializer(activities, many=True)

        data = {
            'userAndProfileSerializer': userAndProfileSerializer,
            'favouriteReadSerializer': favouriteReadSerializer,
            'readingNowSerializer': readingNowSerializer,
            'toReadSerializer': toReadSerializer,
            'haveReadSerializer': haveReadSerializer,
            'bookReviewsSerializer': bookReviewsSerializer,
            'likedBookReviewsSerializer': likedBookReviewsSerializer,
            'dislikedBookReviewsSerializer': dislikedBookReviewsSerializer,
            'activitiesSerializer': activitiesSerializer,
        }
        return data


class UserDataJsonApiVersion1(UserDataBaseApi, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        data = self.getUserData()
        userData = {
            'profile': {
                'header': 'Your profile info we have in Bookrec.',
                'body': data.get('userAndProfileSerializer').data
            },
            'favouriteBooks': {
                'header': 'Your favourite books we have in Bookrec.',
                'body': data.get('favouriteReadSerializer').data
            },
            'readingNowBooks': {
                'header': 'Your reading now books we have in Bookrec.',
                'body': data.get('readingNowSerializer').data
            },
            'toReadBooks': {
                'header': 'Your to read books we have in Bookrec.',
                'body': data.get('toReadSerializer').data
            },
            'haveReadBooks': {
                'header': 'Your have read books we have in Bookrec.',
                'body': data.get('haveReadSerializer').data
            },
            'ratingAndReviewedBooks': {
                'header': 'Books that you have rated and commented on in Bookrec.',
                'body': data.get('bookReviewsSerializer').data
            },
            'likedBookReviews': {
                'header': 'Book reviews you have liked.',
                'body': data.get('likedBookReviewsSerializer').data
            },
            'dislikedBookReviews': {
                'header': 'Book reviews you have disliked.',
                'body': data.get('dislikedBookReviewsSerializer').data
            },
            'activities': {
                'header': 'Activities you\'ve performed',
                'body': data.get('activitiesSerializer').data
            }
        }

        emailOperations.sendEmailForUserDataAsJson(self.request.user, userData)
        logOperations.log(self.request, UserActivityLog.Action.REQUEST_DATA)
        response = {
            'success': True,
            'data': {
                'alert': {
                    'type': 'success',
                    'message': 'A copy of your data will be sent to your email.',
                }
            }
        }
        return Response(response, status=HTTPStatus.OK)
