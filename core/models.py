from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', unique=True, db_index=True)
    favouriteGenres = ArrayField(models.CharField(max_length=8192), blank=True)
    profilePicture = models.ImageField(upload_to='profile-picture', blank=True, null=True)


class Book(models.Model):
    title = models.CharField(max_length=1024)
    authors = ArrayField(models.CharField(max_length=1024), blank=True)
    publisher = models.CharField(max_length=1024, blank=True, null=True)
    publishedDate = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    isbn13 = models.CharField(max_length=13, unique=True)
    categories = ArrayField(models.CharField(max_length=2048), blank=True)
    thumbnail = models.URLField(max_length=8192)
    selfLink = models.URLField(max_length=1024)
    favouriteRead = models.ManyToManyField(User, related_name='favouriteRead')
    readingNow = models.ManyToManyField(User, related_name='readingNow')
    toRead = models.ManyToManyField(User, related_name='toRead')
    haveRead = models.ManyToManyField(User, related_name='haveRead')
    averageRating = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    ratingsCount = models.PositiveIntegerField(default=0, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['isbn13'], name='idx-isbn13'),
            models.Index(fields=['title'], name='idx-title'),
        ]

    def getUrl(self):
        return reverse('core:book-detail-view', kwargs={'isbn13': self.isbn13})

    def increaseAverageRatingAndRatingsCount(self, newRating):
        totalRatings = self.averageRating * self.ratingsCount + newRating
        self.ratingsCount += 1
        self.averageRating = totalRatings / self.ratingsCount
        self.save(update_fields=['ratingsCount', 'averageRating'])

    def decreaseAverageRatingAndRatingsCount(self, givenRating):
        totalRatings = self.averageRating * self.ratingsCount - givenRating
        self.ratingsCount -= 1
        self.averageRating = Decimal(totalRatings) / Decimal(self.ratingsCount) if self.ratingsCount > 0 else Decimal(0)
        self.save(update_fields=['ratingsCount', 'averageRating'])

    def __str__(self):
        return self.isbn13


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookReviews')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField(max_length=1024)
    rating = models.IntegerField()
    createdDateTime = models.DateTimeField(default=timezone.now)
    modifiedDateTime = models.DateTimeField(auto_now=True)
    edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='bookReviewLikes')
    dislikes = models.ManyToManyField(User, related_name='bookReviewDislikes')

    class Meta:
        indexes = [
            models.Index(fields=['book'], name='idx-book'),
            models.Index(fields=['creator'], name='idx-creator'),
            models.Index(fields=['book', 'creator'], name='idx-book-creator'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['book', 'creator'], name='unique-book-creator')
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.book.increaseAverageRatingAndRatingsCount(self.rating)

    def delete(self, *args, **kwargs):
        self.book.decreaseAverageRatingAndRatingsCount(self.rating)
        super().delete(*args, **kwargs)


class Category(models.Model):
    name = models.CharField(max_length=1024, unique=True, db_index=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class UserActivityLog(models.Model):
    class Action(models.TextChoices):
        LOGIN = 'LOGIN', _('Login')
        LOGOUT = 'LOGOUT', _('Logout')
        VIEW_BOOK = 'VIEW_BOOK', _('View Book')
        UPDATE_PROFILE = 'UPDATE_PROFILE', _('Update Profile')
        UPDATE_PASSWORD = 'UPDATE_PASSWORD', _('Update Password')
        REQUEST_DATA = 'REQUEST_DATA', _('Request Data')
        REQUEST_ACCOUNT_DELETE_CODE = 'REQUEST_ACCOUNT_DELETE_CODE', _('Request account delete code')
        DELETE_ACCOUNT = 'DELETE_ACCOUNT', _('Delete Account')
        ADD_TO_FAVOURITES = 'ADD_TO_FAVOURITES', _('Add to Favourites')
        REMOVE_FROM_FAVOURITES = 'REMOVE_FROM_FAVOURITES', _('Remove from Favourites')
        ADD_TO_READING_NOW = 'ADD_TO_READING_NOW', _('Add to Reading Now')
        REMOVE_FROM_READING_NOW = 'REMOVE_FROM_READING_NOW', _('Remove from Reading Now')
        ADD_TO_TO_READ = 'ADD_TO_TO_READ', _('Add to To Read')
        REMOVE_FROM_TO_READ = 'REMOVE_FROM_TO_READ', _('Remove from To Read')
        ADD_TO_HAVE_READ = 'ADD_TO_HAVE_READ', _('Add to Have Read')
        REMOVE_FROM_HAVE_READ = 'REMOVE_FROM_HAVE_READ', _('Remove from Have Read')
        ADD_COMMENT = 'ADD_COMMENT', _('Add Comment')
        EDIT_COMMENT = 'EDIT_COMMENT', _('Edit Comment')
        DELETE_COMMENT = 'DELETE_COMMENT', _('Delete Comment')
        ADD_LIKE_TO_COMMENT = 'ADD_LIKE_TO_COMMENT', _('Add Like to Comment')
        REMOVE_LIKE_FROM_COMMENT = 'REMOVE_LIKE_FROM_COMMENT', _('Remove Like from Comment')
        ADD_DISLIKE_TO_COMMENT = 'ADD_DISLIKE_TO_COMMENT', _('Add Dislike to Comment')
        REMOVE_DISLIKE_FROM_COMMENT = 'REMOVE_DISLIKE_FROM_COMMENT', _('Remove Dislike from Comment')

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=64, blank=True, null=True, choices=Action.choices)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)
    userAgent = models.CharField(max_length=255, blank=True, null=True)
    timeStamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timeStamp'], name='idx-user-timestamp'),
        ]
