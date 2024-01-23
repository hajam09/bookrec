from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Book(models.Model):
    title = models.CharField(max_length=1024)
    authors = ArrayField(models.CharField(max_length=1024), blank=True)
    publisher = models.CharField(max_length=1024, blank=True, null=True)
    publishedDate = models.DateField()
    description = models.TextField(blank=True, null=True)
    isbn13 = models.CharField(max_length=13)
    categories = ArrayField(models.CharField(max_length=2048), blank=True)
    thumbnail = models.URLField(max_length=8192)
    selfLink = models.URLField(max_length=1024)
    isFavourite = models.ManyToManyField(User, related_name='isFavourite')
    readingNow = models.ManyToManyField(User, related_name='readingNow')
    toRead = models.ManyToManyField(User, related_name='toRead')
    haveRead = models.ManyToManyField(User, related_name='haveRead')
    averageRating = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    ratingCount = models.PositiveIntegerField(default=0, blank=True, null=True)# change to ratingsCount todo

    def getAuthors(self):
        return ', '.join(self.authors)

    def getCategories(self):
        return ', '.join(self.categories)

    def getUrl(self):
        return reverse('core:book-detail-view', kwargs={'isbn13': self.isbn13})

    def getAverageRating(self):
        return str(self.averageRating)


class BookReview(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookReviews')
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField(max_length=1024)
    rating = models.IntegerField()
    createdDateTime = models.DateTimeField(default=timezone.now)
    modifiedDateTime = models.DateTimeField(auto_now=True)
    edited = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='bookReviewLikes')
    dislikes = models.ManyToManyField(User, related_name='bookReviewDislikes')


class Category(models.Model):
    name = models.CharField(max_length=1024)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
