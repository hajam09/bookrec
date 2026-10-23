from decimal import Decimal

from django.contrib.auth.models import User
from django.db import models
from django.db.models import SET_NULL
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', unique=True, db_index=True)
    favouriteGenres = models.JSONField(default=list, blank=True)
    profilePicture = models.ImageField(upload_to='profile-picture', blank=True, null=True)


class Book(models.Model):
    title = models.CharField(max_length=1024)
    authors = models.JSONField(default=list, blank=True)
    publisher = models.CharField(max_length=1024, blank=True, null=True)
    publishedDate = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    isbn13 = models.CharField(max_length=13, unique=True)
    categories = models.JSONField(default=list, blank=True)
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
        ratingsCount = int(self.ratingsCount or 0)
        averageRating = Decimal(self.averageRating or 0)
        totalRatings = averageRating * ratingsCount + Decimal(newRating)
        ratingsCount += 1
        self.ratingsCount = ratingsCount
        self.averageRating = totalRatings / Decimal(ratingsCount)
        self.save(update_fields=['ratingsCount', 'averageRating'])

    def decreaseAverageRatingAndRatingsCount(self, givenRating):
        ratingsCount = int(self.ratingsCount or 0)
        averageRating = Decimal(self.averageRating or 0)
        totalRatings = averageRating * ratingsCount - Decimal(givenRating)
        ratingsCount -= 1
        self.ratingsCount = ratingsCount
        self.averageRating = Decimal(totalRatings) / Decimal(ratingsCount) if ratingsCount > 0 else Decimal(0)
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
        isCreate = self._state.adding
        previousRating = None
        if not isCreate and self.pk:
            previousRating = (
                BookReview.objects.filter(pk=self.pk).values_list('rating', flat=True).first()
            )

        super().save(*args, **kwargs)

        if isCreate:
            self.book.increaseAverageRatingAndRatingsCount(self.rating)
            return

        if previousRating is None or int(previousRating) == int(self.rating):
            return

        # Adjust average without changing ratingsCount (review count unchanged)
        book = self.book
        ratingsCount = int(book.ratingsCount or 0)
        if ratingsCount <= 0:
            # Defensive: if data got corrupted, fall back to recalculation.
            total = BookReview.objects.filter(book=book).aggregate(
                avg=models.Avg('rating'),
                cnt=models.Count('id'),
            )
            book.ratingsCount = int(total['cnt'] or 0)
            book.averageRating = Decimal(str(total['avg'] or 0))
            book.save(update_fields=['ratingsCount', 'averageRating'])
            return

        averageRating = Decimal(book.averageRating or 0)
        totalRatings = averageRating * Decimal(ratingsCount)
        totalRatings = totalRatings - Decimal(previousRating) + Decimal(self.rating)
        book.averageRating = totalRatings / Decimal(ratingsCount)
        book.save(update_fields=['averageRating'])

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

    user = models.ForeignKey(User, on_delete=SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=64, blank=True, null=True, choices=Action.choices)
    ipAddress = models.GenericIPAddressField(blank=True, null=True)
    userAgent = models.CharField(max_length=255, blank=True, null=True)
    timeStamp = models.DateTimeField(default=timezone.now)
    data = models.JSONField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'timeStamp'], name='idx-user-timestamp'),
        ]


class PrecomputedRecommendation(models.Model):
    class Type(models.TextChoices):
        BASED_ON_RATING = 'BASED_ON_RATING', _('Based on Rating')
        OTHER_USERS_FAVOURITE = 'OTHER_USERS_FAVOURITE', _('Other Users Favourite')

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='precomputedRecommendations')
    recommendationType = models.CharField(max_length=64, choices=Type.choices, db_index=True)
    isbns = models.JSONField(default=list, blank=True)
    generatedAt = models.DateTimeField(default=timezone.now)
    updatedAt = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'recommendationType'], name='uniq-user-recommendation-type')
        ]
        indexes = [
            models.Index(fields=['user', 'recommendationType'], name='idx-user-rec-type'),
            models.Index(fields=['generatedAt'], name='idx-rec-generated-at'),
        ]
