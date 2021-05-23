from book.models import Book
from book.models import Category
import requests
import json
import re
import unidecode

def googleBooksAPIRequests(booksearch):
	response = requests.get("https://www.googleapis.com/books/v1/volumes?q="+booksearch)
	requestedBooks = []
	newBooks = []
	newCategory = []
	completeLoop = 0

	try:
		jsonResponse = response.json()["items"]
	except KeyError:
		return []

	for book in jsonResponse:
		completeLoop = completeLoop + 1
		try:
			if('industryIdentifiers' in book['volumeInfo'] and len(book['volumeInfo']['industryIdentifiers'])==2):
				uid = book['id']
				title = book['volumeInfo']['title']

				if('authors' in  book['volumeInfo']):
					authors = book['volumeInfo']['authors']
					authors.sort()
					authors = ",".join(authors)
				else:
					authors = None

				if('publisher' in book['volumeInfo']):
					publisher = book['volumeInfo']['publisher']
				else:
					publisher = None

				if('publishedDate' in book['volumeInfo']):
					publishedDate = book['volumeInfo']['publishedDate']
				else:
					publishedDate = None

				if('description' in book['volumeInfo']):
					description = book['volumeInfo']['description']
				else:
					description = None

				isbn13 = None
				isbn10 = None

				if(book['volumeInfo']['industryIdentifiers'][0]['type'] == "ISBN_10"):
					isbn10 = book['volumeInfo']['industryIdentifiers'][0]['identifier']
				elif(book['volumeInfo']['industryIdentifiers'][0]['type'] == "ISBN_13"):
					isbn13 = book['volumeInfo']['industryIdentifiers'][0]['identifier']

				if(book['volumeInfo']['industryIdentifiers'][1]['type'] == "ISBN_10"):
					isbn10 = book['volumeInfo']['industryIdentifiers'][1]['identifier']
				elif(book['volumeInfo']['industryIdentifiers'][1]['type'] == "ISBN_13"):
					isbn13 = book['volumeInfo']['industryIdentifiers'][1]['identifier']

				if('categories' in book['volumeInfo']):
					categories = book['volumeInfo']['categories']
					genre = [i.title().replace(",", " &").replace("  ", "") for i in categories]
					createNewCategories(genre, newCategory)
					genre.sort()
					genre = ",".join(genre)
				else:
					genre = None

				if('averageRating' in book['volumeInfo']):
					averageRating = book['volumeInfo']['averageRating']
				else:
					averageRating = 0.0
				averageRating = round(averageRating * 2) / 2

				if('ratingsCount' in book['volumeInfo']):
					ratingsCount = book['volumeInfo']['ratingsCount']
				else:
					ratingsCount = 0

				if('imageLinks' in book['volumeInfo'] and 'thumbnail' in book['volumeInfo']['imageLinks']):
					thumbnail = book['volumeInfo']['imageLinks']['thumbnail']
				else:
					thumbnail = None

				unCleanData = {
					"authors": authors,
					"averageRating": averageRating,
					"description": description,
					"genre": genre,
					"isbn10": isbn10,
					"isbn13": isbn13,
					"publishedDate": publishedDate,
					"publisher": publisher,
					"ratingsCount": ratingsCount,
					"thumbnail": thumbnail,
					"title": title,
					"uid": uid,
				}

				if authors != None:
					authors = authors.replace(",", " ").replace("-", " ").replace("–", " ")
					authors = ''.join(e for e in authors if e.isalnum() or e==" ")
					authors = re.sub(" +", " ", authors)
					authors = unidecode.unidecode(authors)

				if publisher != None:
					publisher = publisher.replace(",", " ").replace("-", " ").replace("–", " ")
					publisher = ''.join(e for e in publisher if e.isalnum() or e==" ")
					publisher = re.sub(" +", " ", publisher)
					publisher = unidecode.unidecode(publisher)

				title = title.replace(",", " ").replace("-", " ").replace("–", " ")
				title = ''.join(e for e in title if e.isalnum() or e==" ")
				title = re.sub(" +", " ", title)
				title = unidecode.unidecode(title)

				if description != None:
					description = description.replace(",", " ").replace("-", " ").replace("–", " ")
					description = ''.join(e for e in description if e.isalnum() or e==" ")
					description = re.sub(" +", " ", description)
					description = unidecode.unidecode(description)

				cleanData = {
					"authors": authors,
					"averageRating": averageRating,
					"description": description,
					"genre": genre,
					"isbn10": isbn10,
					"isbn13": isbn13,
					"publishedDate": publishedDate,
					"publisher": publisher,
					"ratingsCount": ratingsCount,
					"thumbnail": thumbnail,
					"title": title,
					"uid": uid,
				}

				try:
					requestedBooks.append(Book.objects.get(isbn13=isbn13))
				except Book.DoesNotExist:
					newBookObject = Book(
						isbn13 = isbn13,
						cleanData = cleanData,
						unCleanData = unCleanData
					)
					newBooks.append(newBookObject)
					requestedBooks.append(newBookObject)
					
		except KeyError:
			continue

	if len(newBooks) > 0:
		Book.objects.bulk_create(newBooks)

	if len(newCategory) > 0:
		Category.objects.bulk_create(newCategory)

	if completeLoop != len(jsonResponse):
		error_message='Iteration not complete for query {}. Length of response is {}, parsed {} books.\n'.format(booksearch, len(jsonResponse), completeLoop)
		f = open("apiErrorLogs.txt", "a")
		f.write(error_message)
		f.close()

	return requestedBooks

def createNewCategories(categories, newCategory):
	categoryDB = "".join(categories)
	categoryDB = categoryDB.split("&")

	for category in categoryDB:
		category = ''.join(e for e in category if e.isalnum() or e==" ")
		category = category.strip()
		category = re.sub(" +", " ", category)
		category = unidecode.unidecode(category)

		if not Category.objects.filter(name=category).exists() and notInNewCategories(category, newCategory):
			newCategory.append(
				Category(
					name = category
				)
			)

def notInNewCategories(category, newCategory):
	for c in newCategory:
		if c.name == category:
			return False
	return True