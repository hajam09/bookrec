import datetime
import operator
from functools import reduce

import numpy
import pandas
import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db.models import Q
from scipy.sparse import csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import sigmoid_kernel
from sklearn.preprocessing import MinMaxScaler

from core.models import (
    Book,
    BookReview,
    Category
)
from core.serializers import (
    BookSerializerV1,
    BookSerializerV2,
    BookReviewSerializerV2
)


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


def performComplexBookSearch(query):
    attributesToSearch = ['title', 'authors', 'publisher', 'description', 'isbn13', 'categories']
    filterList = [
        reduce(operator.or_, [Q(**{f'{a}__icontains': query}) for a in attributesToSearch])
    ]
    return Book.objects.filter(reduce(operator.and_, filterList)).distinct()


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
        baseCategories = [splitItem.strip() for category in categories for splitItem in category.split('/')]

        selfLink = item.get('selfLink')
        additionalData = requests.get(selfLink).json()

        categories = additionalData.get('volumeInfo').get('categories') or []
        additionalCategories = [splitItem.strip() for category in categories for splitItem in category.split('/')]

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
    newBooksIsbn = [book.isbn13 for book in Book.objects.bulk_create(newBooks)]
    newBooksQueryset = Book.objects.filter(isbn13__in=newBooksIsbn)
    return booksFromApiThatMatchDB.union(newBooksQueryset, performComplexBookSearch(query))


def recentlyAddedBooks():
    queryset = cache.get('recently-added-books')
    if queryset:
        return queryset

    books = Book.objects.order_by('-id').only('title', 'thumbnail', 'isbn13')[:20]
    queryset = [
        {
            'title': book.title,
            'thumbnail': book.thumbnail,
            'url': book.getUrl()
        }
        for book in books
    ]
    cache.set('recently-added-books', queryset, timeout=30)
    return queryset


def booksBasedOnRatings():
    queryset = cache.get('books-based-on-ratings')
    if queryset:
        return queryset

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
    finalResult = list(booksScoredFromDf[['isbn13']].head(20)['isbn13'])

    books = Book.objects.filter(isbn13__in=finalResult)
    queryset = [
        {
            'title': book.title,
            'thumbnail': book.thumbnail,
            'url': book.getUrl()
        }
        for book in books
    ]
    cache.set('books-based-on-ratings', queryset, timeout=30)
    return queryset


def booksBasedOnViewings(request):
    queryset = cache.get(f'books-based-on-ratings-{request.user.id}')
    if queryset:
        return queryset

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

    viewedBooks = Book.objects.filter(isbn13__in=history, description__isnull=False)
    combinedScores = pandas.Series(0, index=allBooksDf.index)
    for viewedBook in viewedBooks:
        try:
            idx = indices[viewedBook.title].iloc[0]
        except AttributeError:
            idx = indices[viewedBook.title]
        combinedScores += pandas.Series(sigmoidKernel[idx])

    viewedIndices = [
        indices[book.title].iloc[0]
        if hasattr(indices[book.title], 'iloc') else indices[book.title]
        for book in viewedBooks
    ]
    combinedScores.iloc[viewedIndices] = 0

    topIndices = combinedScores.sort_values(ascending=False).head(20).index
    topBooks = allBooksDf.iloc[topIndices]

    books = Book.objects.filter(isbn13__in=topBooks['isbn13']).distinct()
    queryset = [
        {
            'title': book.title,
            'thumbnail': book.thumbnail,
            'url': book.getUrl()
        }
        for book in books
    ]
    cache.set(f'books-based-on-ratings-{request.user.id}', queryset, timeout=30)
    return queryset


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
    Recommend top 20 books to the current user based on other users with similar favourite books.
    Uses a sparse user-book matrix and cosine similarity for scalable collaborative filtering.
    Exclude books the user has already favourited. Results are cached for performance.
    """
    if not request.user.is_authenticated:
        return []

    queryset = cache.get(f'other-users-favourite-books-{request.user.id}')
    if queryset:
        return queryset

    # Step 1: Get all user-book favourite relationships
    books = Book.objects.prefetch_related('favouriteRead')
    users = list(User.objects.values_list('id', flat=True))
    userIndex = {uid: i for i, uid in enumerate(users)}
    bookIds = [book.id for book in books]
    bookIndex = {bid: i for i, bid in enumerate(bookIds)}

    # Step 2: Build sparse user-book matrix
    row, col = [], []
    for book in books:
        for user in book.favouriteRead.all():
            row.append(userIndex[user.id])
            col.append(bookIndex[book.id])
    data = numpy.ones(len(row))
    userBookMatrix = csr_matrix((data, (row, col)), shape=(len(users), len(bookIds)))

    # Step 3: Compute similarity with current user
    userVec = userBookMatrix[userIndex[request.user.id]]
    similarities = cosine_similarity(userVec, userBookMatrix).flatten()

    # Step 4: Score all books by similarity of users who favourited them
    scores = userBookMatrix.T.dot(similarities)

    # Step 5: Remove books the user already has
    userBooksMask = userBookMatrix[userIndex[request.user.id]].toarray().flatten()
    scores[userBooksMask > 0] = 0

    # Step 6: Get top 20 books
    topIndices = numpy.argpartition(-scores, 20)[:20]
    topIndices = topIndices[numpy.argsort(-scores[topIndices])]

    recommendedBooks = [books[int(i)] for i in topIndices]
    queryset = [
        {
            'title': book.title,
            'thumbnail': book.thumbnail,
            'url': book.getUrl()
        }
        for book in recommendedBooks
    ]
    cache.set(f'other-users-favourite-books-{request.user.id}', queryset, timeout=30)
    return queryset


def similarBooks(book):
    """
    Content-Based Book Recommendation System:
    Given a Book instance, returns up to 12 similar books based on similarity
    of book descriptions, categories, authors, and publisher.
    Caches the results for 30 seconds to improve performance.
    """
    queryset = cache.get(f'content-based-recommendations-{book.id}')
    if queryset:
        return queryset

    allBooks = Book.objects.all()
    if allBooks.count() == 0:
        return []

    descriptions = [book.description or "" for book in allBooks]
    authors = [", ".join(book.authors) if book.authors else "" for book in allBooks]
    categories = [", ".join(book.categories) if book.categories else "" for book in allBooks]

    combinedFeatures = [
        desc + " " + authors + " " + categories
        for desc, authors, categories in zip(descriptions, authors, categories)
    ]

    tfv = TfidfVectorizer(
        min_df=3,
        max_features=None,
        strip_accents='unicode',
        analyzer='word',
        token_pattern=r'\w{1,}',
        ngram_range=(1, 3),
        stop_words='english'
    )
    tfvMatrix = tfv.fit_transform(combinedFeatures)

    bookDescription = book.description or ""
    bookAuthors = ", ".join(book.authors) if book.authors else ""
    bookCategories = ", ".join(book.categories) if book.categories else ""

    bookTransformed = tfv.transform([bookDescription + " " + bookAuthors + " " + bookCategories])
    similarities = cosine_similarity(bookTransformed, tfvMatrix).flatten()

    similarBooksIndices = similarities.argsort()[-12 - 1:-1][::-1]
    recommendedBooks = [allBooks[int(i)] for i in similarBooksIndices]

    queryset = [
        {
            'title': book.title,
            'thumbnail': book.thumbnail,
            'url': book.getUrl()
        }
        for book in recommendedBooks
    ]
    cache.set(f'content-based-recommendations-{book.id}', queryset, timeout=30)
    return queryset


def booksBasedOnFavouriteGenres(request):
    query = Q()
    for genre in request.user.profile.favouriteGenres:
        query |= Q(categories__contains=[genre])
    query &= Q(averageRating__gte=3)
    return Book.objects.filter(query)
