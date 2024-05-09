from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from bookrec.operations import generalOperations
from core.models import Category, Profile


class RegistrationForm(forms.ModelForm):
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
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'genres')

    USERNAME_FIELD = 'email'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['genres'].choices = [(category.name, category.name) for category in Category.objects.all()]

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

    def clean_genres(self):
        if len(self.cleaned_data.get('genres')) < 3:
            raise ValidationError('Select at least 3 different genres.')
        return self.cleaned_data.get('genres')

    def save(self, commit=True):
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

        if commit:
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
