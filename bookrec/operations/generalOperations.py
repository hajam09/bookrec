from django.contrib.auth.models import User

from core.models import (
    BookReview,
    Profile
)


def isPasswordStrong(password):
    if len(password) < 8:
        return False

    if not any(letter.isalpha() for letter in password):
        return False

    if not any(capital.isupper() for capital in password):
        return False

    if not any(number.isdigit() for number in password):
        return False

    return True


def redactUserData(user: User):
    user.first_name = 'redacted'
    user.last_name = 'redacted'
    user.username = f'redacted-{user.id}'
    user.email = f'redacted-{user.id}@bookrec.com'
    user.is_active = False
    user.set_unusable_password()
    user.save()

    Profile.objects.filter(user=user).update(
        favouriteGenres=[],
        profilePicture=None,
    )

    """
    Book.objects.filter(favouriteRead=user).delete()
    Book.objects.filter(readingNow=user).delete()
    Book.objects.filter(toRead=user).delete()
    Book.objects.filter(haveRead=user).delete()
    """

    BookReview.objects.filter(creator=user).update(
        comment='redacted'
    )
