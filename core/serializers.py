from django.utils.timesince import timesince
from rest_framework import serializers

from core.models import Book, BookReview


class BookSerializer(serializers.ModelSerializer):
    favouritesCount = serializers.SerializerMethodField()
    averageRating = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'title',
            'description',
            'isbn13',
            'averageRating',
            'ratingCount',
            'favouritesCount'
        ]

    def get_favouritesCount(self, book):
        return book.isFavourite.count()

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
            'description',
            'netVote',
            'canEdit',
            'rating',
            'createdDateTime',
            'modifiedDateTime',
            'userVote',
        ]
