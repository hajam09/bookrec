from rest_framework import serializers

from core.models import Book


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
