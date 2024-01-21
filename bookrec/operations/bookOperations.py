import datetime
import re

import pandas
import requests
import unidecode
from django.contrib.auth.models import User
from django.db.models import Q
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.preprocessing import MinMaxScaler

from core.models import Book, Category, BookReview
from core.serializers import BookSerializerV2, BookReviewSerializerV2, BookSerializerV1


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
    if publishedDate is None:
        return None
    dateLen = len(publishedDate)
    if dateLen == 4:
        return datetime.datetime.strptime(publishedDate, '%Y')
    elif dateLen == 7:
        return datetime.datetime.strptime(publishedDate, '%Y-%m')
    elif dateLen == 10:
        return datetime.datetime.strptime(publishedDate, '%Y-%m-%d')
    raise Exception(f'Invalid date format: {publishedDate} for isbn13: {isbn13}')


def getRatingsCountValue(baseData, additionalData):
    if baseData.get('volumeInfo').get('ratingsCount') is not None:
        return baseData.get('volumeInfo').get('ratingsCount')
    if additionalData.get('volumeInfo').get('ratingsCount') is not None:
        return additionalData.get('volumeInfo').get('ratingsCount')
    return 0


def getAverageRatingValue(baseData, additionalData):
    if baseData.get('volumeInfo').get('averageRating') is not None:
        return baseData.get('volumeInfo').get('averageRating')
    if additionalData.get('volumeInfo').get('averageRating') is not None:
        return additionalData.get('volumeInfo').get('averageRating')
    return 0.0


def handleAuthor(baseData, additionalData):
    if baseData.get('volumeInfo').get('authors') is not None:
        return baseData.get('volumeInfo').get('authors')
    if additionalData.get('volumeInfo').get('authors') is not None:
        return additionalData.get('volumeInfo').get('authors')
    return []


class ApiBook:
    def __init__(self, title, authors, publisher, publishedDate, description, isbn13, categories, thumbnail, selfLink,
                 averageRating, ratingsCount):
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
        self.ratingsCount = ratingsCount


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
                averageRating=getAverageRatingValue(item, additionalData),
                ratingsCount=getRatingsCountValue(item, additionalData)
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
                    ratingsCount=apiBook.ratingsCount
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
    allBooks = Book.objects.all().prefetch_related('favouriteRead')
    if allBooks.count() == 0:
        return []

    bookSerializer = BookSerializerV2(allBooks, many=True)

    # Implementing weighted average for each book's average rating // Non - personalized
    df = pandas.DataFrame(bookSerializer.data)
    v = df['ratingsCount']
    R = df['averageRating']
    m = v.quantile(0.70)
    C = R.mean()

    df['weightedAverage'] = ((R * v) + (C * m)) / (v + m)

    # This is for recommending books to the users based on scaled weighting (50%) and favouritesCount (50%).
    scaling = MinMaxScaler()
    bookScaled = scaling.fit_transform(df[['weightedAverage', 'favouriteReadCount']])
    bookNormalized = pandas.DataFrame(bookScaled, columns=['weightedAverage', 'favouriteReadCount'])

    df[['normalizedWeightAverage', 'normalizedPopularity']] = bookNormalized
    df['score'] = df['normalizedWeightAverage'] * 0.5 + df['normalizedPopularity'] * 0.5
    booksScoredFromDf = df.sort_values(['score'], ascending=False)
    finalResult = list(booksScoredFromDf[['isbn13']].head(15)['isbn13'])

    return Book.objects.filter(isbn13__in=finalResult)


def booksBasedOnViewings(request):
    history = request.session.get('history', [])
    if not history:
        return []

    allBooks = Book.objects.filter(description__isnull=False)
    allBooksSerializer = BookSerializerV1(allBooks, many=True)
    allBooksDf = pandas.DataFrame(allBooksSerializer.data)

    tfv = TfidfVectorizer(
        max_features=None,
        strip_accents='unicode',
        analyzer='word',
        token_pattern=r'\w{1,}',
        ngram_range=(1, 3),
        stop_words='english'
    )

    tfvMatrix = tfv.fit_transform(allBooksDf['description'])
    sigmoidKernel = sigmoid_kernel(tfvMatrix, tfvMatrix)
    indices = pandas.Series(allBooksDf.index, index=allBooksDf['title']).drop_duplicates()

    def giveRecommendation(book):
        try:
            idx = indices[book.title].iloc[0]
        except AttributeError as e:
            print(f'Exception triggered for Content Based Recommendation System for isbn13: {book.isbn13} with: {e}')
            idx = indices[book.title]

        sigmoidScores = list(enumerate(sigmoidKernel[idx]))
        sigmoidScores = sorted(sigmoidScores, key=lambda x: x[1], reverse=True)
        sigmoidScores = sigmoidScores[1:11]
        bookIndices = [i[0] for i in sigmoidScores]
        return allBooksDf['title'].iloc[bookIndices]

    isbn13List2D = [
        list(allBooksDf[allBooksDf.title.isin(list(giveRecommendation(viewedBook)))]['isbn13'])
        for viewedBook in Book.objects.filter(isbn13__in=history, description__isnull=False)
    ]
    flattenedIsbn13 = [item for subList in isbn13List2D for item in subList]
    return Book.objects.filter(isbn13__in=flattenedIsbn13).distinct()


def booksBasedOnRating(request):
    """
        pearson correlation collaborative filtering - Make recommendations based on user ratings.
    """
    books = BookSerializerV1(Book.objects.all(), many=True).data
    ratings = BookReviewSerializerV2(
        BookReview.objects.all().select_related('book'), many=True, context={'request': request}
    ).data
    if books == [] or ratings == []:
        return []

    booksDataFrame = pandas.DataFrame(books)[['isbn13', 'title']]
    ratingsDataFrame = pandas.DataFrame(ratings)[['creator', 'isbn13', 'rating']]
    booksAndRating = pandas.merge(booksDataFrame, ratingsDataFrame)
    userRatings = booksAndRating.pivot_table(index=['creator'], columns=['title'], values='rating')

    # Fixing books that have less than 10 user ratings. Uncomment this in the future
    # userRatings = userRatings.dropna(thresh=10, axis=1).fillna(0, axis=1)
    corrMatrix = userRatings.corr(method='pearson')

    def fetchSimilarBooksByTitle(bookName, _rating):
        similarRatings = corrMatrix[bookName] * (_rating - 2.5)
        return similarRatings.sort_values(ascending=False)

    # Getting user's top-rated books
    topRatedBookReviews = BookReview.objects.filter(creator=request.user, rating__gte=4).select_related(
        'book'
    ).order_by('-rating')[:20]
    miningBooks = [(review.book.title, 2.0 * review.rating) for review in topRatedBookReviews]

    similarBook = pandas.DataFrame()
    for book, rating in miningBooks:
        similarBooksByTitle = fetchSimilarBooksByTitle(book, rating)
        similarBook = pandas.concat([similarBook, pandas.DataFrame([similarBooksByTitle])], ignore_index=True)

    topRecommendedBooks = similarBook.sum().sort_values(ascending=False).head(20)
    topBookTitles = [topRecommendedBooks[topRecommendedBooks == i].index[0] for i in topRecommendedBooks]
    return Book.objects.filter(title__in=topBookTitles, averageRating__gte=3)


def otherUsersFavouriteBooks(request):
    """
        Return list of other favourite books from similar user(s).
        Attributes to determine the similarity: list of favourite books from each user.
    """
    if not request.user.is_authenticated:
        return []
    favouriteBooks = Book.objects.filter(favouriteRead__id=request.user.id).values_list('id', flat=True)
    otherUsers = User.objects.filter(
        favouriteRead__id__in=favouriteBooks
    ).exclude(id=request.user.id).values_list('id', flat=True)
    return Book.objects.filter(favouriteRead__in=otherUsers).order_by('-averageRating').distinct()[:10]


def similarBooks(book):
    """
        Content Based Recommendation System - Make recommendations based on the book's description.
    """
    allBooks = Book.objects.all().prefetch_related('favouriteRead')
    if allBooks.count() == 0:
        return []

    tfv = TfidfVectorizer(
        min_df=3,
        max_features=None,
        strip_accents='unicode',
        analyzer='word',
        token_pattern=r'\w{1,}',
        ngram_range=(1, 3),
        stop_words='english'
    )

    bookSerializer = BookSerializerV2(allBooks, many=True)
    df = pandas.DataFrame(bookSerializer.data)
    df['description'] = df['description'].fillna('')

    tfvMatrix = tfv.fit_transform(df['description'])
    sigmoidKernel = sigmoid_kernel(tfvMatrix, tfvMatrix)
    indices = pandas.Series(df.index, index=df['title']).drop_duplicates()

    bookTitle = book.title.replace(',', '').replace('-', '').replace('–', '')
    bookTitle = ''.join(e for e in bookTitle if e.isalnum() or e == ' ')
    bookTitle = re.sub(' +', ' ', bookTitle)
    bookTitle = unidecode.unidecode(bookTitle)

    def giveRecommendation():
        try:
            idx = indices[bookTitle].iloc[0]
        except AttributeError as e:
            print(f'Exception triggered for Content Based Recommendation System for isbn13: {book.isbn13} with: {e}')
            idx = indices[bookTitle]
        sigmoidScores = list(enumerate(sigmoidKernel[idx]))
        sigmoidScores = sorted(sigmoidScores, key=lambda x: x[1], reverse=True)
        sigmoidScores = sigmoidScores[1:11]
        bookIndices = [i[0] for i in sigmoidScores]
        return df['title'].iloc[bookIndices]

    originalTable = giveRecommendation()
    df = df[df.title.isin(list(originalTable))]
    return Book.objects.filter(isbn13__in=list(df['isbn13']))


def booksBasedOnFavouriteGenres(request):
    # todo: for each favouriteGenres, find similar categories that match string using similarity and use those.
    query = Q()
    for genre in request.user.profile.favouriteGenres:
        query |= Q(categories__contains=[genre])
    query &= Q(averageRating__gte=3)
    return Book.objects.filter(query)
