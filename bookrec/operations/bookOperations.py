import datetime

import pandas
import requests
from sklearn.preprocessing import MinMaxScaler

from core.models import Book, Category
from core.serializers import BookSerializer


def getThumbnailForBook(additionalData):
    imageLinks = additionalData.get('volumeInfo').get('imageLinks')
    if imageLinks is not None:
        if imageLinks.get('extraLarge') is not None:
            return imageLinks.get('extraLarge')
        if imageLinks.get('large') is not None:
            return imageLinks.get('large')
        if imageLinks.get('medium') is not None:
            return imageLinks.get('medium')
        if imageLinks.get('small') is not None:
            return imageLinks.get('small')
        if imageLinks.get('thumbnail') is not None:
            return imageLinks.get('thumbnail')
        if imageLinks.get('smallThumbnail') is not None:
            return imageLinks.get('smallThumbnail')
    # TODO: change size.
    return 'https://dummyimage.com/1997x3101'


def handleMissingDate(isbn13, publishedDate):
    dateLen = len(publishedDate)
    if dateLen == 4:
        return datetime.datetime.strptime(publishedDate, '%Y')
    elif dateLen == 7:
        return datetime.datetime.strptime(publishedDate, '%Y-%m')
    elif dateLen == 10:
        return datetime.datetime.strptime(publishedDate, '%Y-%m-%d')
    raise Exception(f'Invalid date format: {publishedDate} for isbn13: {isbn13}')


def getRatingsCount(baseData, additionalData):
    if baseData.get('volumeInfo').get('averageRating') is not None:
        return baseData.get('volumeInfo').get('averageRating')
    if additionalData.get('volumeInfo').get('averageRating') is not None:
        return additionalData.get('volumeInfo').get('averageRating')
    return 0


def getAverageRatingCount(baseData, additionalData):
    if baseData.get('volumeInfo').get('ratingsCount') is not None:
        return baseData.get('volumeInfo').get('ratingsCount')
    if additionalData.get('volumeInfo').get('ratingsCount') is not None:
        return additionalData.get('volumeInfo').get('ratingsCount')
    return 0.0


def handleAuthor(baseData, additionalData):
    if baseData.get('volumeInfo').get('authors') is not None:
        return baseData.get('volumeInfo').get('authors')
    if additionalData.get('volumeInfo').get('authors') is not None:
        return additionalData.get('volumeInfo').get('authors')
    return []


class ApiBook:
    def __init__(self, title, authors, publisher, publishedDate, description, isbn13, categories, thumbnail, selfLink,
                 averageRating, ratingCount):
        self.title = title
        self.authors = authors
        self.publisher = publisher
        self.publishedDate = publishedDate
        self.description = description
        self.isbn13 = isbn13
        self.categories = categories
        self.thumbnail = thumbnail
        self.selfLink = selfLink
        self.averageRating = averageRating
        self.ratingCount = ratingCount


def googleBooksAPIRequests(query):
    response = requests.get('https://www.googleapis.com/books/v1/volumes?q=' + query)
    if response.json().get('totalItems') == 0:
        return []

    newBooks = []
    apiBooks = []
    combinedCategories = []

    for item in response.json()['items']:
        industryIdentifiers = item.get('volumeInfo').get('industryIdentifiers')
        if industryIdentifiers is None:
            continue

        isbn13 = next((i.get('identifier') for i in industryIdentifiers if i.get('type') == 'ISBN_13'), None)
        if isbn13 is None:
            continue

        categories = item.get('volumeInfo').get('categories') or []
        baseCategories = [splitItem.strip() for category in categories for splitItem in category.split("/")]

        selfLink = item.get('selfLink')
        additionalData = requests.get(selfLink).json()

        categories = additionalData.get('volumeInfo').get('categories') or []
        additionalCategories = [splitItem.strip() for category in categories for splitItem in category.split("/")]

        joinedCategories = list(set(baseCategories + additionalCategories))
        combinedCategories += joinedCategories

        apiBooks.append(
            ApiBook(
                title=item.get('volumeInfo').get('title'),
                authors=handleAuthor(item, additionalData),
                publisher=item.get('volumeInfo').get('publisher'),
                publishedDate=handleMissingDate(isbn13, item.get('volumeInfo').get('publishedDate')),
                description=item.get('volumeInfo').get('description'),
                isbn13=isbn13,
                categories=list(set(baseCategories + additionalCategories)),
                thumbnail=getThumbnailForBook(additionalData),
                selfLink=selfLink,
                averageRating=getAverageRatingCount(item, additionalData),
                ratingCount=getRatingsCount(item, additionalData)
            )
        )

    isbn13FromApi = [book.isbn13 for book in apiBooks]
    booksFromApiThatMatchDB = Book.objects.filter(isbn13__in=isbn13FromApi)
    booksFromApiThatMatchDBIsbn13 = list(booksFromApiThatMatchDB.values_list('isbn13', flat=True))

    for apiBook in apiBooks:
        if apiBook.isbn13 not in booksFromApiThatMatchDBIsbn13:
            newBooks.append(
                Book(
                    title=apiBook.title,
                    authors=apiBook.authors,
                    publisher=apiBook.publisher,
                    publishedDate=apiBook.publishedDate,
                    description=apiBook.description,
                    isbn13=apiBook.isbn13,
                    categories=apiBook.categories,
                    thumbnail=apiBook.thumbnail,
                    selfLink=apiBook.selfLink,
                    averageRating=apiBook.averageRating,
                    ratingCount=apiBook.ratingCount
                )
            )

    combinedCategoriesFromApi = list(set(combinedCategories))
    categoriesFromApiThatMatchDB = list(
        Category.objects.filter(name__in=combinedCategoriesFromApi).values_list('name', flat=True)
    )
    Category.objects.bulk_create(
        [
            Category(name=category) for category in combinedCategoriesFromApi
            if category.casefold() not in (name.casefold() for name in categoriesFromApiThatMatchDB)
        ]
    )
    return list(booksFromApiThatMatchDB) + Book.objects.bulk_create(newBooks)


def recentlyAddedBooks():
    allBooks = Book.objects.all()
    count = allBooks.count()
    return allBooks[count - 20:] if count > 20 else allBooks[:]


def booksBasedOnRatings():
    allBooks = Book.objects.all().prefetch_related('isFavourite')
    if allBooks.count() == 0:
        return []

    bookSerializer = BookSerializer(allBooks, many=True)

    # Implementing weighted average for each book's average rating // Non - personalized
    df = pandas.DataFrame(bookSerializer.data)
    v = df['ratingCount']
    R = df['averageRating']
    m = v.quantile(0.70)
    C = R.mean()

    df['weightedAverage'] = ((R * v) + (C * m)) / (v + m)

    # This is for recommending books to the users based on scaled weighting (50%) and favouritesCount (50%).
    scaling = MinMaxScaler()
    bookScaled = scaling.fit_transform(df[['weightedAverage', 'favouritesCount']])
    bookNormalized = pandas.DataFrame(bookScaled, columns=['weightedAverage', 'favouritesCount'])

    df[['normalizedWeightAverage', 'normalizedPopularity']] = bookNormalized
    df['score'] = df['normalizedWeightAverage'] * 0.5 + df['normalizedPopularity'] * 0.5
    booksScoredFromDf = df.sort_values(['score'], ascending=False)
    finalResult = list(booksScoredFromDf[['isbn13']].head(15)['isbn13'])

    return Book.objects.filter(isbn13__in=finalResult)


def booksBasedOnViewings():
    return []


def otherUsersFavouriteBooks(request):
    """
        Return list of other favourite books from similar user(s).
        Attributes to determine the similarity: list of favourite books from each user.
    """
    if not request.user.is_authenticated or request.user.is_superuser:
        return []
    return []


def similarBooks(book):
    """
        Make recommendations based on the books’s description.
    """
    return []
