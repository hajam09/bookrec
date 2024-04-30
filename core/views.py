from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.cache import cache
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.encoding import force_str, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode

from bookrec.operations import bookOperations, emailOperations
from core.forms import LoginForm, PasswordUpdateForm, RegistrationForm
from core.models import Category, Book, BookReview


def loginView(request):
    if request.user.is_authenticated:
        return redirect('core:index-view')

    if not request.session.session_key:
        request.session.save()

    if request.method == 'POST':
        uniqueVisitorId = request.session.session_key

        if cache.get(uniqueVisitorId) is not None and cache.get(uniqueVisitorId) > 3:
            cache.set(uniqueVisitorId, cache.get(uniqueVisitorId), 600)

            messages.error(
                request, 'Your account has been temporarily locked out because of too many failed login attempts.'
            )
            return redirect('core:login-view')

        form = LoginForm(request, request.POST)

        if form.is_valid():
            cache.delete(uniqueVisitorId)
            redirectUrl = request.GET.get('next')
            if redirectUrl:
                return redirect(redirectUrl)
            return redirect('core:index-view')

        if cache.get(uniqueVisitorId) is None:
            cache.set(uniqueVisitorId, 1)
        else:
            cache.incr(uniqueVisitorId, 1)

    else:
        form = LoginForm(request)

    context = {
        'form': form
    }
    return render(request, 'core/loginView.html', context)


def logoutView(request):
    logout(request)

    previousUrl = request.META.get('HTTP_REFERER')
    if previousUrl:
        return redirect(previousUrl)

    return redirect('core:index-view')


def registrationView(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            newUser = form.save()
            emailOperations.sendEmailToActivateAccount(request, newUser)

            messages.info(
                request, 'We\'ve sent you an activation link. Please check your email.'
            )
            return redirect('core:login-view')
    else:
        form = RegistrationForm()

    context = {
        'form': form
    }
    return render(request, 'core/registrationView.html', context)


def accountActivationRequest(request, base64, token):
    try:
        uid = force_str(urlsafe_base64_decode(base64))
        user = User.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist):
        user = None

    passwordResetTokenGenerator = PasswordResetTokenGenerator()

    if user is not None and passwordResetTokenGenerator.check_token(user, token):
        user.is_active = True
        user.save()

        messages.success(
            request,
            'Account activated successfully'
        )
        return redirect('core:login-view')

    return render(request, 'core/linkFailedTemplate.html', status=HTTPStatus.UNAUTHORIZED)


def passwordChangeRequest(request):
    if request.method == 'POST':
        try:
            user = User.objects.get(username=request.POST['email'])
        except User.DoesNotExist:
            user = None

        if user is not None:
            emailOperations.sendEmailToChangePassword(request, user)

        messages.info(
            request, 'Check your email for a password change link.'
        )

    return render(request, 'core/passwordChangeRequest.html')


def passwordUpdateRequest(request, base64, token):
    try:
        uid = force_str(urlsafe_base64_decode(base64))
        user = User.objects.get(pk=uid)
    except (DjangoUnicodeDecodeError, ValueError, User.DoesNotExist):
        user = None

    passwordResetTokenGenerator = PasswordResetTokenGenerator()
    verifyToken = passwordResetTokenGenerator.check_token(user, token)

    if request.method == 'POST' and user is not None and verifyToken:
        form = PasswordUpdateForm(request, user, request.POST)

        if form.is_valid():
            form.updatePassword()
            return redirect('core:login-view')

    context = {
        'form': PasswordUpdateForm(),
    }

    TEMPLATE = 'passwordUpdateForm' if user is not None and verifyToken else 'linkFailedTemplate'
    return render(request, 'core/{}.html'.format(TEMPLATE), context)


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
