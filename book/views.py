from book.models import Book
from book.models import BookReview
from book.utils import googleBooksAPIRequests
from django.http import JsonResponse
from django.http import HttpResponse
from django.http import QueryDict
from django.shortcuts import render
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.preprocessing import MinMaxScaler
import pandas as pd
from django.contrib.humanize.templatetags.humanize import naturaltime
import json

def mainpage(request):
	if request.method == "POST":

		bookSearchQuery = request.POST["booksearch"]
		requestedBooks = googleBooksAPIRequests(bookSearchQuery)

		if len(requestedBooks) > 0:
			context = {
				"bookResults": requestedBooks,
				"bookSearchQuery": bookSearchQuery
			}
			return render(request, "book/mainpage.html", context)
		else:
			context = {
				"noResult": "Sorry, we could't find any results matching ' {} '".format(bookSearchQuery)
			}
		return render(request, "book/mainpage.html", context)

	context = {
		"recentlyAddedBooks": recentlyAddedBooks(),
		"booksBasedOnRatings": booksBasedOnRatings(),
		"favouriteBooksFromSimilarUsers": favouriteBooksFromSimilarUsers(request),
	}
	
	return render(request, "book/mainpage.html", context)

def bookPage(request, isbn_13):
	try:
		book = Book.objects.get(isbn13=isbn_13)
	except Book.DoesNotExist  as e:
		raise e

	shelf = {
		"inFavourites": True if request.user in book.isFavourite.all() else False,
		"inReadingNow": True if request.user in book.readingNow.all() else False,
		"inToRead": True if request.user in book.toRead.all() else False,
		"inHaveRead": True if request.user in book.haveRead.all() else False,
	}
	
	context = {
		"book": book,
		"shelf": shelf,
		"similarBooks": similarBooks(book),
	}
	return render(request, "book/bookPage.html", context)

def getBookReviews(request, *args, **kwargs):

	bookReviews = BookReview.objects.filter(book__isbn13=kwargs['isbn_13']).prefetch_related('likes', 'dislikes').select_related('creator')

	if kwargs['orderBy'] == 'NewestFirst':
		bookReviews = bookReviews.order_by('-createdTime')
		bookReviewsSplit = [bookReviews[i:i + 15] for i in range(0, len(bookReviews), 15)]

	elif kwargs['orderBy'] == 'OldestFirst':
		bookReviews = bookReviews.order_by('createdTime')
		bookReviewsSplit = [bookReviews[i:i + 15] for i in range(0, len(bookReviews), 15)]

	elif kwargs['orderBy'] == 'TopReview':
		bookReviews = sortBookCommentsByLike( bookReviews )
		bookReviewsSplit = [bookReviews[i:i + 15] for i in range(0, len(bookReviews), 15)]

	try:
		bookReviewsSplitList = bookReviewsSplit[int(kwargs['pagination'])]
	except IndexError:
		response = {
			"error": "IndexError"
		}
		return HttpResponse(json.dumps(response), content_type="application/json")

	newBookReviewsList = [
		{
			'pk': c.pk,
			'fullName': c.creator.get_full_name(),
			'edited': c.edited,
			'description': c.description,
			'likeCount': c.likes.count(),
			'dislikeCount': c.dislikes.count(),
			'canEdit': c.creator.pk == request.user.pk,
			'createdTime': 'c.createdTime',
			'elapsed': naturaltime(c.createdTime)
		}

		for c in bookReviewsSplitList
	]

	response = {
		'newBookReviewsList': newBookReviewsList
	}
	return JsonResponse(response, status=200)

def updateShelf(request, *args, **kwargs):
	"""
		User adds or removes book from their shelf.
	"""
	import time
	start_time = time.time()
	if not request.user.is_authenticated:
		response = {
			"action": False,
			"message": "Login to perform this action."
		}
		return JsonResponse(response, status=401)

	if not request.is_ajax() or kwargs['isbn_13'] == None or kwargs['shelf_type'] == None:
		response = {
			"action": False,
			"message": "Unable to perform action at this time."
		}
		return JsonResponse(response, status=400)

	book = Book.objects.get(isbn13=kwargs['isbn_13'])
	shelf = {}

	if request.is_ajax() and request.method == "POST":
		if kwargs['shelf_type'] == 'favourites':
			shelf['inFavourites'] = book.updateIsFavourite(request)
			
		elif kwargs['shelf_type'] == 'readingNow':
			shelf['inReadingNow'] = book.updateReadingNow(request)

		elif kwargs['shelf_type'] == 'toRead':
			shelf['inToRead'] = book.updateToRead(request)

		elif kwargs['shelf_type'] == 'haveRead':
			shelf['inHaveRead'] = book.updateHaveRead(request)

	response = {
		"action": True,
		"message": "",
		"shelf": shelf
	}
	print("--- %s seconds ---" % (time.time() - start_time))
	return JsonResponse(response, status=200)

def bookComment(request, *args, **kwargs):
	"""
		User can create, update and delete comments for a particular book.
	"""
	# TODO: if requests can be categorised in request.method then remove kwargs['action'] from url.
	if not request.user.is_authenticated:
		response = {
			"action": False,
			"message": "Login to perform this action."
		}
		return JsonResponse(response, status=401)

	if not request.is_ajax() or kwargs['isbn_13'] == None or kwargs['action'] == None:
		response = {
			"action": False,
			"message": "Unable to perform action at this time."
		}
		return JsonResponse(response, status=400)

	book = Book.objects.get(isbn13=kwargs['isbn_13'])

	if request.is_ajax() and request.method.lower() == "delete":
		body = QueryDict(request.body)
		commentId = body.get("commentId")
		BookReview.objects.filter(id=commentId).delete()

		response = {
			"action": True,
		}
		return JsonResponse(response, status=200)

	if request.is_ajax() and request.method == "PUT":
		body = QueryDict(request.body)
		commentId = body.get("commentId")
		functionality = body.get("functionality")

		bookReview = BookReview.objects.get(id=commentId)

		if functionality == 'likeComment':
			bookReview.likeBookReview(request)

		if functionality == 'dislikeComment':
			bookReview.dislikeBookReview(request)

		response = {
			"action": True,
			"likeCount": bookReview.likes.count(),
			"dislikeCount": bookReview.dislikes.count()
		}
		return JsonResponse(response, status=200)

	if request.is_ajax() and request.method == "POST":
		if kwargs['action'] == 'create':
			body = QueryDict(request.body)
			newComment = body.get("newComment")
			starCount = body.get("starCount")

			bookReview = BookReview.objects.create(
				book = book,
				creator = request.user,
				description = newComment,
				rating = starCount,
			)

			response = {
				"action": True,
				"bookReview": {
					'pk': bookReview.pk,
					'full_name': bookReview.creator.get_full_name(),
					'edited': bookReview.edited,
					'description': bookReview.description,
					'like_count': 0,
					'dislike_count': 0,
					'can_edit': True,
					'elapsed': naturaltime(bookReview.createdTime),
				},
			}
			return JsonResponse(response, status=200)

		elif kwargs['action'] == 'update':
			pass

		elif kwargs['action'] == 'delete':
			pass

	return JsonResponse({}, status=200)

def recentlyAddedBooks():
	allBooks = Book.objects.all()
	top20Books = allBooks[len(allBooks)-20:] if len(allBooks)>20 else allBooks[:]
	
	recentlyAddedBooks = [
		{
			"isbn13": i.isbn13,
			"title": i.unCleanData['title'],
			"thumbnail": i.unCleanData['thumbnail']
		}	
		for i in top20Books
	]
	return recentlyAddedBooks

def booksBasedOnRatings():
	allBooks = Book.objects.all().prefetch_related('isFavourite')

	if len(allBooks) == 0:
		return []

	dictBooks = {}
	for i in allBooks:

		dictBooks[i.unCleanData["isbn13"]] = {
			"isbn13": i.unCleanData["isbn13"],
			"title": i.unCleanData['title'],
			"thumbnail": i.unCleanData['thumbnail']
		}

		i.cleanData.pop("description")
		i.cleanData.pop("isbn10")
		i.cleanData.pop("thumbnail")
		i.cleanData.pop("uid")
		i.cleanData["favouritesCount"] = i.isFavourite.count()

	allBooksCleaned = [i.cleanData for i in allBooks]

	# Implementing weighted average for each book's average rating // Non - personalized

	df = pd.DataFrame(allBooksCleaned)

	v = df['ratingsCount']
	R = df['averageRating']
	C = df['averageRating'].mean()
	m = df['ratingsCount'].quantile(0.70)

	df['weightedAverage'] = ((R*v) + (C*m))/(v+m)

	# This is for recommending books to the users based on scaled weighting (50%) and favouritesCount (50%).
	scaling = MinMaxScaler()
	bookScaled = scaling.fit_transform(df[['weightedAverage', 'favouritesCount']])
	bookNormalized = pd.DataFrame(bookScaled, columns=['weightedAverage', 'favouritesCount'])

	df[['normalizedWeightAverage','normalizedPopularity']] = bookNormalized
	df['score'] = df['normalizedWeightAverage'] * 0.5 + df['normalizedPopularity'] * 0.5
	booksScoredFromDf = df.sort_values(['score'], ascending=False)
	finalResult = list(booksScoredFromDf[['isbn13']].head(15)['isbn13'])

	return [ dictBooks[isbn] for isbn in finalResult ]

def similarBooks(book):
	"""
		Make recommendations based on the books’s description.
	"""
	allBooks = Book.objects.all().prefetch_related('isFavourite')

	if len(allBooks) == 0 or not isinstance(book, Book):
		return []

	dictBooks = {}

	for i in allBooks:

		dictBooks[i.unCleanData["isbn13"]] = {
			"isbn13": i.unCleanData["isbn13"],
			"title": i.unCleanData['title'],
			"thumbnail": i.unCleanData['thumbnail']
		}

		i.cleanData.pop("authors")
		i.cleanData.pop("averageRating")
		i.cleanData.pop("genre")
		i.cleanData.pop("isbn10")
		i.cleanData.pop("publishedDate")
		i.cleanData.pop("publisher")
		i.cleanData.pop("ratingsCount")
		i.cleanData.pop("thumbnail")
		i.cleanData.pop("uid")

	allBooksCleaned = [i.cleanData for i in allBooks]

	df = pd.DataFrame(allBooksCleaned)

	tfidfVectorizer = TfidfVectorizer(
		min_df=3, 
		max_features=None,
		strip_accents='unicode',
		analyzer='word',
		token_pattern=r'\w{1,}',
		ngram_range=(1, 3),
		stop_words = 'english'
	)

	df['description'] = df['description'].fillna('')
	tfvMatrix = tfidfVectorizer.fit_transform(df['description'])
	sigmoid = sigmoid_kernel(tfvMatrix, tfvMatrix)
	indices = pd.Series(df.index, index=df['title']).drop_duplicates()

	def giveRecommendation(title, sigmoid=sigmoid):
	    try:
	        idx = indices[title].iloc[0]
	    except:
	    	# couldn't catch specific exception dur to 'numpy.int64' object has no attribute 'iloc'
	        idx = indices[title]

	    sigmoidScores = list(enumerate(sigmoid[idx]))
	    sigmoidScores = sorted(sigmoidScores, key=lambda x: x[1], reverse=True)
	    sigmoidScores = sigmoidScores[1:11]
	    bookIndices = [i[0] for i in sigmoidScores]
	    return df['isbn13'].iloc[bookIndices]

	finalResult = list(giveRecommendation(book.cleanData['title']))
	return [ dictBooks[isbn] for isbn in finalResult ]

def favouriteBooksFromSimilarUsers(request):
	if not request.user.is_authenticated or not request.user.is_superuser:
		return []
	return []

def sortBookCommentsByLike(bookReviews):
	"""
		Return the existing book review list by most popular comment made by a user.
		Attributes to determine the popularity:
			likes and dislikes
	"""

	if len(bookReviews) == 0:
		return []

	bookReviewsDict = [
		{
			'id': b.pk,
			'likeCount': b.likes.count(),
			'dislikeCount': b.dislikes.count(),
		}
		for b in bookReviews
	]

	df = pd.DataFrame(bookReviewsDict)
	scaling = MinMaxScaler()
	divedent = 100/2

	bookReviewsScaled = scaling.fit_transform(df[['likeCount', 'dislikeCount']])
	bookReivewNormalized = pd.DataFrame(bookReviewsScaled, columns=['likeCount', 'dislikeCount'])

	df[['normalizedlikeCount','normalizeddislikeCount']]= bookReivewNormalized
	df['score'] = df['normalizedlikeCount'] * divedent+ df['normalizeddislikeCount'] * divedent

	bookReviewDf = df.sort_values(['score'], ascending=False)
	bookReviewId = list(bookReviewDf['id'])
	return [j for i in bookReviewId for j in bookReviews if i == j.pk]