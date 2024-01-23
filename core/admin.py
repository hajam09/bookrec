from django.contrib import admin

from core.models import Book, BookReview, Category

admin.site.register(Book)
admin.site.register(BookReview)
admin.site.register(Category)
