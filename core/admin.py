from django.contrib import admin

from core.models import (
    Book,
    BookReview,
    Category,
    Profile,
    UserActivityLog
)


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    pass


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    pass


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    pass
