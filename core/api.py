import os
from datetime import datetime
from http import HTTPStatus

import pandas
from django.contrib.auth import authenticate, login
from django.core.cache import cache
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Count, FloatField, Func, F
from django.db.models.functions import Greatest, Cast
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from bookrec.operations import bookOperations, emailOperations, generalOperations
from core.models import Book, BookReview, Category, Profile
from core.serializers import (
    BookReviewSerializerV1, BookReviewSerializerV2, BookReviewSerializerV3,
    BookSerializerV1, BookSerializerV3,
    CategorySerializer, UserAndProfileSerializer
)


class AccountDeleteCodeApiEventVersion1Component(APIView):

    def get(self, request, *args, **kwargs):
        alerts = []
        if self.request.user.is_authenticated:
            if not self.request.session.session_key:
                self.request.session.save()

            emailOperations.sendEmailForAccountDeletionCode(self.request, self.request.user)
            success = True
            alerts.append({'alert': 'success', 'message': 'Check your email for the code.'})
            status = HTTPStatus.OK
        else:
            success = False
            alerts.append({'alert': 'danger', 'message': 'Login to request a code.'})
            status = HTTPStatus.UNAUTHORIZED

        response = {
            'version': '1.0.0',
            'success': success,
            'data': {
                'alerts': alerts
            }
        }
        return Response(response, status=status)

    def delete(self, request, *args, **kwargs):
        alerts = []
        if self.request.data.get('code') == self.request.session.session_key:
            generalOperations.redactUserData(self.request.user)
            alerts.append({'alert': 'success', 'message': 'Account deleted successfully.'})
            success = True
        else:
            alerts.append({'alert': 'danger', 'message': 'Account delete code is incorrect, please try again later.'})
            success = False

        response = {
            'version': '1.0.0',
            'success': success,
            'data': {
                'alerts': alerts
            }
        }
        return Response(response, status=HTTPStatus.OK)


class BookReviewActionApiEventVersion1Component(APIView):

    def post(self, request, *args, **kwargs):
        book = Book.objects.filter(isbn13=kwargs.get('isbn13')).first()
        bookReview, created = BookReview.objects.get_or_create(
            book=book,
            creator_id=self.request.user.id,
            defaults={
                'comment': request.data.get('comment'),
                'rating': int(request.data.get('rating')),
            }
        )

        if not created:
            bookReview.comment = request.data.get('comment')
            bookReview.rating = int(request.data.get('rating'))
            bookReview.edited = True
            bookReview.save(update_fields=['comment', 'rating', 'edited'])

        bookReview.likes.add(self.request.user)
        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def get(self, request, *args, **kwargs):
        # todo: write unit test for this method.
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
            creator=self.request.user
        )
        bookReview.comment = request.data.get('comment')
        bookReview.edited = True
        bookReview.save(update_fields=['comment', 'edited'])

        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def delete(self, request, *args, **kwargs):
        BookReview.objects.filter(
            id=request.data.get('id'),
            book__isbn13=kwargs.get('isbn13'),
            creator=self.request.user,
        ).delete()

        response = {
            'version': '1.0.0',
            'success': True,
        }
        return Response(response, status=HTTPStatus.OK)


class UserShelfApiEventVersion1Component(APIView):
    def get(self, request, *args, **kwargs):
        shelf = request.GET.get('shelf')
        cachedData = cache.get(f'user-shelf-{shelf}-{self.request.user.id}')

        if cachedData:
            data = cachedData
        elif shelf == 'ratedAndReviewed':
            reviews = BookReview.objects.filter(creator=self.request.user).select_related('book')
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
        if not cachedData:
            cache.set(f'user-shelf-{shelf}-{self.request.user.id}', data, timeout=30)
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
            except (TypeError, AttributeError):
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

        serializer = BookReviewSerializerV1(bookReview, context={'request': self.request})

        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'review': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)


class CategoryApiEventVersion1Component(ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def dispatch(self, request, *args, **kwargs):
        import warnings
        warnings.warn('This API endpoint is deprecated.', DeprecationWarning, stacklevel=2)
        return super().dispatch(request, *args, **kwargs)


class ProfileApiEventVersion1Component(APIView):

    def dispatch(self, request, *args, **kwargs):
        import warnings
        warnings.warn(
            'This API endpoint is deprecated. Replaced with native Django View.',
            DeprecationWarning,
            stacklevel=2
        )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        profile = Profile.objects.get(user=self.request.user)
        serializer = UserAndProfileSerializer(profile)
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'profile': serializer.data
            }
        }
        return Response(response, status=HTTPStatus.OK)

    def put(self, request, *args, **kwargs):
        profile = Profile.objects.get(user=self.request.user)
        profile.user.first_name = self.request.data.get('firstName')
        profile.user.last_name = self.request.data.get('lastName')
        profile.user.email = self.request.data.get('email')
        profile.favouriteGenres = self.request.data.get('genres')

        profile.save()
        profile.user.save()

        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'alerts': [
                    {'alert': 'success', 'message': 'Profile update successfully.'}
                ]
            }
        }
        return Response(response, status=HTTPStatus.OK)


class UserPasswordUpdateApiEventVersion1Component(APIView):

    def dispatch(self, request, *args, **kwargs):
        import warnings
        warnings.warn(
            'This API endpoint is deprecated. Replaced with native Django View.',
            DeprecationWarning,
            stacklevel=2
        )
        return super().dispatch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        currentPassword = self.request.data.get('currentPassword')
        newPassword = self.request.data.get('newPassword')
        repeatNewPassword = self.request.data.get('repeatNewPassword')

        alerts = []
        if currentPassword and not self.request.user.check_password(currentPassword):
            alerts.append(
                {'alert': 'danger', 'message': 'Your current password doesn\'t match the existing one.'}
            )

        if newPassword and repeatNewPassword:
            if newPassword != repeatNewPassword:
                alerts.append(
                    {'alert': 'danger', 'message': 'Your new password and confirm password does not match.'}
                )

            if not generalOperations.isPasswordStrong(newPassword):
                alerts.append(
                    {'alert': 'danger', 'message': 'Your new password is not strong enough.'}
                )

        if len(alerts) == 0:
            self.request.user.set_password(newPassword)
            self.request.user.save()

            user = authenticate(self.request, username=self.request.user.username, password=newPassword)
            if user:
                login(self.request, user)
                alerts.append(
                    {'alert': 'success', 'message': 'Password updated successfully.'}
                )
            else:
                alerts.append(
                    {'alert': 'warning', 'message': 'Something has occurred. Please try logging into the system again.'}
                )

        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'alerts': alerts
            }
        }
        return Response(response, status=HTTPStatus.OK)


class RequestCopyOfDataApiEventVersionCommon:
    def getUserData(self):
        user = getattr(getattr(self, 'request'), 'user')

        profile = Profile.objects.select_related('user').get(user=user)
        userAndProfileSerializer = UserAndProfileSerializer(profile)
        favouriteReadBooks = Book.objects.filter(favouriteRead__id=user.id)
        favouriteReadSerializer = BookSerializerV3(favouriteReadBooks, many=True)
        readingNowBooks = Book.objects.filter(readingNow__id=user.id)
        readingNowSerializer = BookSerializerV3(readingNowBooks, many=True)
        toReadBooks = Book.objects.filter(toRead__id=user.id)
        toReadSerializer = BookSerializerV3(toReadBooks, many=True)
        haveReadBooks = Book.objects.filter(haveRead__id=user.id)
        haveReadSerializer = BookSerializerV3(haveReadBooks, many=True)
        bookReviews = BookReview.objects.filter(creator=user).select_related('book')
        bookReviewsSerializer = BookReviewSerializerV3(bookReviews, many=True)

        data = {
            'userAndProfileSerializer': userAndProfileSerializer,
            'favouriteReadSerializer': favouriteReadSerializer,
            'readingNowSerializer': readingNowSerializer,
            'toReadSerializer': toReadSerializer,
            'haveReadSerializer': haveReadSerializer,
            'bookReviewsSerializer': bookReviewsSerializer,
        }
        return data


class RequestCopyOfDataApiEventVersion1Component(RequestCopyOfDataApiEventVersionCommon, APIView):

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
            }
        }

        emailOperations.sendEmailForUserDataAsJson(self.request.user, userData)
        alerts = [
            {'alert': 'success', 'message': 'A copy of your data will be sent to your email.'}
        ]
        response = {
            'version': '1.0.0',
            'success': True,
            'data': {
                'alerts': alerts
            }
        }
        return Response(response, status=HTTPStatus.OK)


class RequestCopyOfDataApiEventVersion2Component(RequestCopyOfDataApiEventVersionCommon, APIView):

    def get(self, request, *args, **kwargs):
        data = self.getUserData()

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        FILE_NAME = f'Bookrec_user_data_{self.request.user.id}-{timestamp}.xlsx'

        profileDf = pandas.DataFrame(data.get('userAndProfileSerializer').data)
        favouriteDf = pandas.DataFrame(data.get('favouriteReadSerializer').data)
        readingNowDf = pandas.DataFrame(data.get('readingNowSerializer').data)
        toReadDf = pandas.DataFrame(data.get('toReadSerializer').data)
        haveReadDf = pandas.DataFrame(data.get('haveReadSerializer').data)
        bookReviewsDf = pandas.DataFrame(data.get('bookReviewsSerializer').data)

        profileDf.to_excel(FILE_NAME, index=False, sheet_name='UserProfile')
        with pandas.ExcelWriter(FILE_NAME, mode='a') as writer:
            favouriteDf.to_excel(writer, index=False, sheet_name='FavouriteReadBooks')
            readingNowDf.to_excel(writer, index=False, sheet_name='ReadingNowBooks')
            toReadDf.to_excel(writer, index=False, sheet_name='ToReadBooks')
            haveReadDf.to_excel(writer, index=False, sheet_name='HaveReadBooks')
            bookReviewsDf.to_excel(writer, index=False, sheet_name='RatedAndCommentedBooks')

        emailOperations.sendEmailForUserDataAsXlsx(self.request.user, FILE_NAME)
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)

        alerts = [
            {'alert': 'success', 'message': 'A copy of your data will be sent to your email.'}
        ]
        response = {
            'version': '2.0.0',
            'success': True,
            'data': {
                'alerts': alerts
            }
        }
        return Response(response, status=HTTPStatus.OK)
