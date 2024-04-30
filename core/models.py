from decimal import Decimal

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone


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

    def getAuthors(self):
        return ', '.join(self.authors)

    def getCategories(self):
        return ', '.join(self.categories)

    def getUrl(self):
        return reverse('core:book-detail-view', kwargs={'isbn13': self.isbn13})

    def getAverageRating(self):
        return str(self.averageRating)

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
        super().save(*args, **kwargs)
        self.book.decreaseAverageRatingAndRatingsCount(self.rating)


class Category(models.Model):
    name = models.CharField(max_length=1024)

    class Meta:
        ordering = ('name',)
        indexes = [
            models.Index(fields=['name'], name='idx-name'),
        ]

    def __str__(self):
        return self.name
