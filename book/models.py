from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
import jsonfield
from django.utils.html import format_html

class Book(models.Model):
	isbn13 = models.CharField(max_length=32)
	cleanData = jsonfield.JSONField()
	unCleanData = jsonfield.JSONField()
	isFavourite = models.ManyToManyField(User, related_name='isFavourite')
	readingNow = models.ManyToManyField(User, related_name='readingNow')
	toRead = models.ManyToManyField(User, related_name='toRead')
	haveRead = models.ManyToManyField(User, related_name='haveRead')

	def updateIsFavourite(self, request):
		if request.user not in self.isFavourite.all():
			self.isFavourite.add(request.user)
			return True
		else:
			self.isFavourite.remove(request.user)
			return False

	def updateReadingNow(self, request):
		if request.user not in self.readingNow.all():
			self.readingNow.add(request.user)
			return True
		else:
			self.readingNow.remove(request.user)
			return False

	def updateToRead(self, request):
		if request.user not in self.toRead.all():
			self.toRead.add(request.user)
			return True
		else:
			self.toRead.remove(request.user)
			return False

	def updateHaveRead(self, request):
		if request.user not in self.haveRead.all():
			self.haveRead.add(request.user)
			return True
		else:
			self.haveRead.remove(request.user)
			return False

	def getaverageRatingToStar(self):
		i = 0
		stars = ''
		for _ in range(int(self.unCleanData['averageRating'])):
			stars += '<i class="fas fa-star star-filled" style="font-size: 20px; color: blue;";></i>&nbsp;'
			i += 1

		for _ in range(i, 5, 1):
			stars += '<i class="fas fa-star star-filled" style="font-size: 20px; color: #c7c7c7;";></i>&nbsp;'

		return format_html( stars )

	def getaverageRatingToPercentage(self):
		return int(self.unCleanData['averageRating'] * 100 / 5)

class BookReview(models.Model):
	book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='bookReviews')
	creator = models.ForeignKey(User, on_delete=models.CASCADE)
	description = models.TextField(max_length=1024)
	rating = models.IntegerField()
	createdTime = models.DateTimeField(default=datetime.now)
	edited = models.BooleanField(default=False)
	likes = models.ManyToManyField(User, related_name='bookReviewLikes')
	dislikes = models.ManyToManyField(User, related_name='bookReviewDislikes')

	def likeBookReview(self, request):
		if request.user not in self.likes.all():
			self.likes.add(request.user)
		else:
			self.likes.remove(request.user)

		if request.user in self.dislikes.all():
			self.dislikes.remove(request.user)

	def dislikeBookReview(self, request):
		if request.user not in self.dislikes.all():
			self.dislikes.add(request.user)
		else:
			self.dislikes.remove(request.user)

		if request.user in self.likes.all():
			self.likes.remove(request.user)

	def getRatingToStar(self):
		i = 0
		stars = ''
		for _ in range(self.rating):
			stars += '<i class="fas fa-star star-filled" style="font-size: 15px; color: orange;";></i>&nbsp;'
			i += 1

		for _ in range(i, 5, 1):
			stars += '<i class="fas fa-star star-filled" style="font-size: 15px; color: #c7c7c7;";></i>&nbsp;'

		return format_html( stars )

class Category(models.Model):
	name = models.CharField(max_length=1000)

	def __str__ (self):
		return self.name

	class Meta:
		ordering = ('name',)