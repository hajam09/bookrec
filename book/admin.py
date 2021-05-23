from django.contrib import admin
from book.models import Book
from book.models import Category
from book.models import BookReview

admin.site.register(Book)
admin.site.register(BookReview)
admin.site.register(Category)