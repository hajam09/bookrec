from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import transaction

from bookrec.operations import (
    generalOperations,
    logOperations
)
from core.models import (
    Category,
    Profile,
    UserActivityLog
)


class BaseUserAndProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label='',
        strip=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Firstname'
            }
        )
    )
    last_name = forms.CharField(
        label='',
        strip=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Lastname'
            }
        )
    )
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email'
            }
        )
    )
    genres = forms.MultipleChoiceField(
        label='',
        choices=[],
        widget=forms.SelectMultiple(
            attrs={
                'class': 'form-control item-selector',
                'style': 'width: 100%',
                'required': 'required',
            }
        )
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'genres')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genres'].choices = [(category.name, category.name) for category in Category.objects.all()]

    def clean_email(self):
        raise NotImplemented

    def clean_genres(self):
        if len(self.cleaned_data.get('genres')) < 3:
            raise ValidationError('Select at least 3 different genres.')
        return self.cleaned_data.get('genres')

    @transaction.atomic
    def save(self):
        raise NotImplemented


class RegistrationForm(BaseUserAndProfileForm):
    password1 = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )
    password2 = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirm Password'
            }
        )
    )

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'genres')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise ValidationError('An account already exists for this email address!')

        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise ValidationError('Your passwords do not match!')

        if not generalOperations.isPasswordStrong(password1):
            raise ValidationError('Your password is not strong enough.')

        return password1

    @transaction.atomic
    def save(self):
        user = User()
        user.username = self.cleaned_data.get('email')
        user.email = self.cleaned_data.get('email')
        user.set_password(self.cleaned_data['password1'])
        user.first_name = self.cleaned_data.get('first_name')
        user.last_name = self.cleaned_data.get('last_name')
        user.is_active = False

        profile = Profile()
        profile.user = user
        profile.favouriteGenres = self.cleaned_data.get('genres')

        user.save()
        profile.save()
        return user


class LoginForm(forms.ModelForm):
    email = forms.EmailField(
        label='',
        widget=forms.EmailInput(
            attrs={
                'placeholder': 'Email'
            }
        )
    )
    password = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )

    class Meta:
        model = User
        fields = ('email',)

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

    def clean_password(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        user = authenticate(self.request, username=email, password=password)
        if user:
            login(self.request, user)
            return self.cleaned_data

        raise ValidationError('Please enter a correct email and password.')


class PasswordUpdateForm(forms.Form):
    password = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Password'
            }
        )
    )

    repeatPassword = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Repeat Password'
            }
        )
    )

    def __init__(self, request=None, user=None, *args, **kwargs):
        self.request = request
        self.user = user
        super(PasswordUpdateForm, self).__init__(*args, **kwargs)

    def clean(self):
        newPassword = self.cleaned_data.get('password')
        confirmPassword = self.cleaned_data.get('repeatPassword')

        if newPassword != confirmPassword:
            raise ValidationError('Your new password and confirm password does not match.')

        if not generalOperations.isPasswordStrong(newPassword):
            raise ValidationError('Your new password is not strong enough.')

        return self.cleaned_data

    def updatePassword(self):
        newPassword = self.cleaned_data.get('password')
        self.user.set_password(newPassword)
        self.user.save()


class UserSettingsProfileUpdateForm(BaseUserAndProfileForm):

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = request
        self.fields['email'].disabled = True

        self.fields['first_name'].initial = self.request.user.first_name
        self.fields['last_name'].initial = self.request.user.last_name
        self.fields['email'].initial = self.request.user.email
        self.fields['genres'].initial = self.request.user.profile.favouriteGenres

    def clean_email(self):
        pass

    @transaction.atomic
    def save(self):
        self.request.user.first_name = self.cleaned_data.get('first_name')
        self.request.user.last_name = self.cleaned_data.get('last_name')
        self.request.user.profile.favouriteGenres = self.cleaned_data.get('genres')

        self.request.user.save(update_fields=['first_name', 'last_name'])
        self.request.user.profile.save(update_fields=['favouriteGenres'])
        messages.success(self.request, 'Profile update successfully.')
        logOperations.log(self.request, UserActivityLog.Action.UPDATE_PROFILE)


class UserSettingsPasswordUpdateForm(forms.Form):
    currentPassword = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Current password'
            }
        )
    )
    newPassword = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'New password'
            }
        )
    )
    repeatNewPassword = forms.CharField(
        label='',
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Repeat new password'
            }
        )
    )

    def __init__(self, request, *args, **kwargs):
        self.request = request
        self.user = request.user
        super(UserSettingsPasswordUpdateForm, self).__init__(*args, **kwargs)

    def clean(self):
        currentPassword = self.cleaned_data.get('currentPassword')
        newPassword = self.cleaned_data.get('newPassword')
        repeatNewPassword = self.cleaned_data.get('repeatNewPassword')

        if currentPassword and not self.user.check_password(currentPassword):
            raise ValidationError('Your current password does not match with the account\'s existing password.')

        if newPassword and repeatNewPassword:
            if newPassword != repeatNewPassword:
                raise ValidationError('Your new password and confirm password does not match.')

            if not generalOperations.isPasswordStrong(newPassword):
                raise ValidationError('Your new password is not strong enough.')

        return self.cleaned_data

    def updatePassword(self):
        newPassword = self.cleaned_data.get('newPassword')
        self.user.set_password(newPassword)
        self.user.save()
        logOperations.log(self.request, UserActivityLog.Action.UPDATE_PASSWORD)

    def reAuthenticate(self):
        newPassword = self.cleaned_data.get('newPassword')
        user = authenticate(self.request, username=self.user.username, password=newPassword)
        if user:
            login(self.request, user)
            messages.success(self.request, 'Your password has been updated.')
        else:
            messages.warning(self.request, 'Something happened. Try to login to the system again.')
        return user
