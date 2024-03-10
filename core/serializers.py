from rest_framework import serializers

from core.models import Book, BookReview


class BookSerializer(serializers.ModelSerializer):
    favouritesCount = serializers.SerializerMethodField()
    averageRating = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ['title', 'description', 'isbn13', 'averageRating', 'ratingCount', 'favouritesCount']

    def get_favouritesCount(self, book):
        return book.isFavourite.count()

    def get_averageRating(self, book):
        return float(book.averageRating)


class BookReviewSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField('_name')
    likesCount = serializers.SerializerMethodField('_likesCount')
    dislikesCount = serializers.SerializerMethodField('_dislikesCount')
    canEdit = serializers.SerializerMethodField('_canEdit')

    def _name(self, review):
        return review.creator.get_full_name()

    def _likesCount(self, review):
        return review.likes.count()

    def _dislikesCount(self, review):
        return review.dislikes.count()

    def _canEdit(self, review):
        return review.creator == self.context.get('request').user

    class Meta:
        model = BookReview
        fields = [
            'id',
            'name',
            'edited',
            'description',
            'likesCount',
            'dislikesCount',
            'canEdit',
            'createdDateTime',
            'modifiedDateTime',
        ]
