from django.utils.timesince import timesince
from rest_framework import serializers

from core.models import Book, BookReview, Category, Profile


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
            'description',
            'isbn13',
            'averageRating',
            'ratingsCount',
            'favouriteReadCount'
        ]

    def get_favouriteReadCount(self, book):
        return book.favouriteRead.count()

    def get_averageRating(self, book):
        return float(book.averageRating)


class BookReviewSerializer(serializers.ModelSerializer):
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


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name'
        ]


class UserAndProfileSerializer(serializers.ModelSerializer):
    firstName = serializers.CharField(source='user.first_name', read_only=True)
    lastName = serializers.CharField(source='user.last_name', read_only=True)
    email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = Profile
        fields = [
            'firstName',
            'lastName',
            'email',
            'favouriteGenres',
            'profilePicture'
        ]
