from django.http import Http404
from django.shortcuts import render

from bookrec.operations import bookOperations
from core.models import Category, Book, BookReview


def indexView(request):
    context = {
        'categories': Category.objects.all(),
        'recentlyAddedBooks': bookOperations.recentlyAddedBooks(),
        'booksBasedOnRatings': bookOperations.booksBasedOnRatings(),
        'booksBasedOnViewings': bookOperations.booksBasedOnViewings(),
        'otherUsersFavouriteBooks': bookOperations.otherUsersFavouriteBooks(request),
    }
    return render(request, 'core/index.html', context)


def bookListView(request):
    books = bookOperations.googleBooksAPIRequests(request.GET.get('query'))
    context = {
        'books': books
    }
    return render(request, 'core/bookListView.html', context)


def bookDetailView(request, isbn13):
    try:
        book = Book.objects.get(isbn13=isbn13)
    except Book.DoesNotExist:
        raise Http404

    context = {
        'book': book,
        'reviews': BookReview.objects.filter(book=book).order_by('-createdDateTime'),
    }
    return render(request, 'core/bookDetailView.html', context)


def userShelfView(request):
    return render(request, 'core/userShelfView.html')
