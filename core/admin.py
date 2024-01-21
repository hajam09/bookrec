from django.contrib import admin

from core.models import Book, BookReview, Category, Profile

admin.site.register(Book)
admin.site.register(BookReview)
admin.site.register(Category)
admin.site.register(Profile)