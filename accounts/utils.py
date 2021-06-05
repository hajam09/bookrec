from django.contrib.auth.models import User
from faker import Faker
import random
from book.models import Book
from book.models import BookReview

# CONSTANT VALUES
EMAIL_DOMAINS = ["@yahoo", "@gmail", "@outlook", "@hotmail"]
DOMAINS = [".co.uk", ".com", ".co.in", ".net", ".us"]
RATINGS = [1, 2, 3, 4, 5]

def createUser():
	print("start create user")

	if User.objects.all().count() > 100:
		print("sufficient users")
		return

	for __ in range(100):
		fake = Faker('en_GB')
		first_name = fake.unique.first_name()
		last_name = fake.unique.last_name()
		email = first_name.lower() + '.' + last_name.lower() + random.choice(EMAIL_DOMAINS) + random.choice(DOMAINS)
		password = 'RanDomPasWord56'

		user = User( username=email, email=email, password=password, first_name=first_name, last_name=last_name )
		user.save()

	print("complete create user")

def createBookReview():
	print("start create book review")

	ALL_USERS = User.objects.all().exclude(is_superuser=True)
	fake = Faker('en_GB')

	for book in Book.objects.all():
		bookReviews = BookReview.objects.filter(book=book)

		if bookReviews.count()>50:
			continue

		# newBookReviewList = [
		# 	BookReview(
		# 		book = book,
		# 		creator = random.choice(ALL_USERS),
		# 		description = fake.text(),
		# 		rating = random.choice(RATINGS),
		# 	)
		# 	for __ in range(55)
		# ]

		sumOfThisRatings = 0
		newBookReviewList = []

		for __ in range(55):
			thisRating = random.choice(RATINGS)
			sumOfThisRatings += thisRating

			newBookReviewList.append(
				BookReview(
					book = book,
					creator = random.choice(ALL_USERS),
					description = fake.text(),
					rating = thisRating,
				)
			)

		print("Created 55 book reviews for book ", book)

		newRatingsCount = book.cleanData['ratingsCount'] + 55
		newRatingPointsSum = book.cleanData['ratingsCount']*book.cleanData['averageRating'] + sumOfThisRatings
		newAverageRating = round(newRatingPointsSum/newRatingsCount, 1)

		book.cleanData['ratingsCount'] = newRatingsCount
		book.unCleanData['ratingsCount'] = newRatingsCount

		book.cleanData['averageRating'] = newAverageRating
		book.unCleanData['averageRating'] = newAverageRating
		book.save()

		BookReview.objects.bulk_create(newBookReviewList)

	print("complete create book review")