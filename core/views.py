from django.http import Http404
from django.shortcuts import render

from bookrec.operations import bookOperations
from core.models import Category, Book, BookReview

from django.contrib.auth.decorators import login_required


def indexView(request):
    context = {
        'categories': Category.objects.all(),
        'recentlyAddedBooks': bookOperations.recentlyAddedBooks(),
        'booksBasedOnRatings': bookOperations.booksBasedOnRatings(),
        'booksBasedOnViewings': bookOperations.booksBasedOnViewings(request),
        'otherUsersFavouriteBooks': bookOperations.otherUsersFavouriteBooks(request),
    }
    return render(request, 'core/indexView.html', context)


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

    if request.user.is_authenticated:
        if 'history' not in request.session:
            request.session['history'] = []

        history = request.session['history']
        if isbn13 not in history:
            history.append(isbn13)
        request.session['history'] = history

    context = {
        'book': book,
        'similarBooks': bookOperations.similarBooks(book),
        'reviews': BookReview.objects.filter(book=book).order_by('-createdDateTime'),
    }
    return render(request, 'core/bookDetailView.html', context)


@login_required
def userShelfView(request):
    return render(request, 'core/userShelfView.html')
