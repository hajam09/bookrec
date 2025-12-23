from django.urls import reverse
from django.utils.timesince import timesince
from rest_framework import serializers

from core.models import (
    Book,
    BookReview,
    Profile,
    UserActivityLog
)


class UserAndProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='user.first_name', read_only=True)
    lastName = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    dateJoined = serializers.CharField(source='user.date_joined', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'firstName',
            'lastName',
            'email',
            'username',
            'dateJoined',
            'favouriteGenres',
            'profilePicture'
        ]


class BookSerializerV1(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'description',
            'isbn13',
            'averageRating',
            'categories',
        ]


class BookSerializerV2(serializers.ModelSerializer):
    favouriteReadCount = serializers.SerializerMethodField()
    averageRating = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'title',
            'isbn13',
            'averageRating',
            'ratingsCount',
            'favouriteReadCount'
        ]

    def get_favouriteReadCount(self, book):
        return book.favouriteRead.count()

    def get_averageRating(self, book):
        return float(book.averageRating)


class BookSerializerV3(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'isbn13',
            'title',
            'authors'
        ]


class BookReviewSerializerV1(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('_name')
    netVote = serializers.SerializerMethodField('_netVote')
    canEdit = serializers.SerializerMethodField('_canEdit')
    createdDateTime = serializers.SerializerMethodField('_createdDateTime')
    modifiedDateTime = serializers.SerializerMethodField('_modifiedDateTime')
    userVote = serializers.SerializerMethodField('_userVote')

    def _name(self, review):
        return review.creator.get_full_name()

    def _netVote(self, review):
        return review.likes.count() - review.dislikes.count()

    def _canEdit(self, review):
        return review.creator == self.context.get('request').user

    def _createdDateTime(self, review):
        return {
            'python': review.createdDateTime,
            'humanize': timesince(review.createdDateTime),
        }

    def _modifiedDateTime(self, review):
        return {
            'python': review.modifiedDateTime,
            'humanize': timesince(review.modifiedDateTime),
        }

    def _userVote(self, review):
        return {
            'upVoted': self.context.get('request').user in review.likes.all(),
            'downVoted': self.context.get('request').user in review.dislikes.all(),
        }

    class Meta:
        model = BookReview
        fields = [
            'id',
            'name',
            'edited',
            'comment',
            'netVote',
            'canEdit',
            'rating',
            'createdDateTime',
            'modifiedDateTime',
            'userVote',
        ]


class BookReviewSerializerV2(serializers.ModelSerializer):
    isbn13 = serializers.CharField(source='book.isbn13', read_only=True)
    title = serializers.CharField(source='book.title', read_only=True)
    categories = serializers.ListField(source='book.categories', read_only=True)

    class Meta:
        model = BookReview
        fields = [
            'id',
            'rating',
            'creator',
            'isbn13',
            'title',
            'categories',
            'comment',
        ]


class BookReviewSerializerV3(serializers.ModelSerializer):
    isbn13 = serializers.CharField(source='book.isbn13', read_only=True)
    title = serializers.CharField(source='book.title', read_only=True)
    likes = serializers.SerializerMethodField('_likes')
    dislikes = serializers.SerializerMethodField('_dislikes')

    def _likes(self, review):
        return review.likes.count()

    def _dislikes(self, review):
        return review.dislikes.count()

    class Meta:
        model = BookReview
        fields = [
            'isbn13',
            'title',
            'rating',
            'comment',
            'createdDateTime',
            'modifiedDateTime',
            'edited',
            'likes',
            'dislikes',
        ]


class BookReviewSerializerV4(serializers.ModelSerializer):
    isbn13 = serializers.CharField(source='book.isbn13', read_only=True)
    title = serializers.CharField(source='book.title', read_only=True)

    class Meta:
        model = BookReview
        fields = [
            'isbn13',
            'title'
        ]


class UserActivityLogSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()
    icon = serializers.SerializerMethodField()
    color = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = UserActivityLog
        fields = [
            'id',
            'timeStamp',
            'message',
            'icon',
            'color',
            'url',
        ]

    def get_icon(self, obj):
        # fa-exclamation-triangle
        ICONS = {
            'LOGIN': 'fa-sign-in-alt',
            'LOGOUT': 'fa-sign-out-alt',
            'VIEW_BOOK': 'fa-book',
            'UPDATE_PROFILE': 'fa-user-edit',
            'UPDATE_PASSWORD': 'fa-key',
            'REQUEST_DATA': 'fa-file-alt',
            'REQUEST_ACCOUNT_DELETE_CODE': 'fa-trash-alt',
            'DELETE_ACCOUNT': 'fa-user-slash',
            'ADD_TO_FAVOURITES': 'fa-heart',
            'REMOVE_FROM_FAVOURITES': 'fa-heart-broken',
            'ADD_TO_READING_NOW': 'fa-book-reader',
            'REMOVE_FROM_READING_NOW': 'fa-book',
            'ADD_TO_TO_READ': 'fa-bookmark',
            'REMOVE_FROM_TO_READ': 'fa-bookmark',
            'ADD_TO_HAVE_READ': 'fa-check',
            'REMOVE_FROM_HAVE_READ': 'fa-times',
            'ADD_COMMENT': 'fa-comment',
            'EDIT_COMMENT': 'fa-edit',
            'DELETE_COMMENT': 'fa-trash',
            'ADD_LIKE_TO_COMMENT': 'fa-thumbs-up',
            'REMOVE_LIKE_FROM_COMMENT': 'fa-thumbs-up',
            'ADD_DISLIKE_TO_COMMENT': 'fa-thumbs-down',
            'REMOVE_DISLIKE_FROM_COMMENT': 'fa-thumbs-down',
        }
        return ICONS.get(obj.action, 'fa-info-circle')

    def get_color(self, obj):
        COLORS = {
            'LOGIN': 'success',
            'LOGOUT': 'secondary',
            'VIEW_BOOK': 'info',
            'UPDATE_PROFILE': 'primary',
            'UPDATE_PASSWORD': 'warning',
            'REQUEST_DATA': 'info',
            'REQUEST_ACCOUNT_DELETE_CODE': 'warning',
            'DELETE_ACCOUNT': 'danger',
            'ADD_TO_FAVOURITES': 'danger',
            'REMOVE_FROM_FAVOURITES': 'secondary',
            'ADD_TO_READING_NOW': 'primary',
            'REMOVE_FROM_READING_NOW': 'secondary',
            'ADD_TO_TO_READ': 'info',
            'REMOVE_FROM_TO_READ': 'secondary',
            'ADD_TO_HAVE_READ': 'success',
            'REMOVE_FROM_HAVE_READ': 'secondary',
            'ADD_COMMENT': 'primary',
            'EDIT_COMMENT': 'warning',
            'DELETE_COMMENT': 'danger',
            'ADD_LIKE_TO_COMMENT': 'success',
            'REMOVE_LIKE_FROM_COMMENT': 'secondary',
            'ADD_DISLIKE_TO_COMMENT': 'warning',
            'REMOVE_DISLIKE_FROM_COMMENT': 'secondary',
        }
        return COLORS.get(obj.action, 'dark')

    def get_url(self, obj):
        if not obj.data:
            return None
        # Book-related actions
        if 'book-isbn13' in obj.data:
            return reverse('core:book-detail-view', kwargs={'isbn13': obj.data['book-isbn13']})
        return None

    def get_message(self, obj):
        data = obj.data or {}
        book_title = data.get('book-title')

        messages = {
            'LOGIN': f"You logged in from {obj.userAgent}",
            'LOGOUT': f"You logged out from {obj.userAgent}",
            'VIEW_BOOK': f'You viewed "{book_title}"',
            'UPDATE_PROFILE': "You updated your profile",
            'UPDATE_PASSWORD': "You updated your password",
            'REQUEST_DATA': "You requested your account data",
            'REQUEST_ACCOUNT_DELETE_CODE': f"You requested an account deletion code from ip {obj.ipAddress}",
            'DELETE_ACCOUNT': f"You deleted your account from ip {obj.ipAddress}",
            'ADD_TO_FAVOURITES': f'You added "{book_title}" to favourites',
            'REMOVE_FROM_FAVOURITES': f'You removed "{book_title}" from favourites',
            'ADD_TO_READING_NOW': f'You added "{book_title}" to your reading now list',
            'REMOVE_FROM_READING_NOW': f'You removed "{book_title}" from your reading now list',
            'ADD_TO_TO_READ': f'You added "{book_title}" to your to-read list',
            'REMOVE_FROM_TO_READ': f'You removed "{book_title}" from your to-read list',
            'ADD_TO_HAVE_READ': f'You added "{book_title}" to your have-read list',
            'REMOVE_FROM_HAVE_READ': f'You removed "{book_title}" from your have-read list',
            'ADD_COMMENT': f'You added a comment on "{book_title}"',
            'EDIT_COMMENT': f'You edited a comment on "{book_title}"',
            'DELETE_COMMENT': f'You deleted a comment on "{book_title}"',
            'ADD_LIKE_TO_COMMENT': f'You liked a comment on "{book_title}"',
            'REMOVE_LIKE_FROM_COMMENT': f'You removed a like from a comment on "{book_title}"',
            'ADD_DISLIKE_TO_COMMENT': f'You disliked a comment on "{book_title}"',
            'REMOVE_DISLIKE_FROM_COMMENT': f'You removed a dislike from a comment on "{book_title}"',
        }

        return messages.get(obj.action, f"You performed {obj.get_action_display()}")


class BasicUserActivityLogSerializer(UserActivityLogSerializer):
    class Meta:
        model = UserActivityLog
        fields = [
            'id',
            'ipAddress',
            'message',
            'userAgent',
            'timeStamp'
        ]


class UserActivityFilterSerializer(serializers.Serializer):
    sort_by = serializers.ChoiceField(
        choices=['new', 'old'],
        required=False,
        default='new'
    )
    page = serializers.IntegerField(min_value=1, required=False, default=1)
