import datetime
import random

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone
from faker import Faker

from accounts.models import Profile
from core.models import Book, BookReview


class Command(BaseCommand):
    PASSWORD = 'admin'
    NUMBER_OF_USERS = 40
    NUMBER_OF_REVIEWS_PER_BOOK = 50

    def __init__(self):
        super().__init__()
        self.faker = Faker('en_GB')

    def handle(self, *args, **kwargs):
        try:
            adminUser = User(
                username='admin',
                email='django.admin@example.com',
                first_name='Django',
                last_name='Admin',
                is_staff=True,
                is_active=True,
                is_superuser=True,
            )
            adminUser.set_password(Command.PASSWORD)
            adminUser.save()
        except IntegrityError:
            pass

        try:
            with transaction.atomic():
                print(f'Attempting to create {Command.NUMBER_OF_USERS} users.')
                # self.bulkCreateUsers()

                print(f'Attempting to create {Command.NUMBER_OF_REVIEWS_PER_BOOK} reviews per book.')
                self.bulkCreateBookReviews()
        except BaseException as e:
            print('Failed to seed data. Rolled back all the transactions', e)

    def _email(self, first_name, last_name):
        return f'{first_name}.{last_name}@{self.faker.free_email_domain()}'

    def bulkCreateUsers(self):
        USERS = []
        PROFILES = []
        for i in range(Command.NUMBER_OF_USERS):
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = self._email(first_name.lower(), last_name.lower())

            user = User()
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.username = email
            user.set_password(Command.PASSWORD)
            USERS.append(user)

            profile = Profile()
            profile.user = user
            PROFILES.append(profile)

        User.objects.bulk_create(USERS)
        Profile.objects.bulk_create(PROFILES)

    def bulkCreateBookReviews(self):
        allUsers = User.objects.all().values_list('id', flat=True)
        BookReview.objects.all().delete()
        for book in Book.objects.all():
            REVIEWS = []
            for i in range(Command.NUMBER_OF_REVIEWS_PER_BOOK):
                bookReview = BookReview()
                bookReview.book = book
                bookReview.edited = random.choice([True, False])
                bookReview.creator_id = random.choice(allUsers)
                bookReview.description = self.faker.paragraph()
                bookReview.rating = random.randint(0, 5)
                bookReview.createdDateTime = timezone.now() - datetime.timedelta(seconds=random.randint(0, 999999999))

                REVIEWS.append(bookReview)
                print(f'Created {Command.NUMBER_OF_REVIEWS_PER_BOOK} review for book with id: {book.id}.')

            BookReview.objects.bulk_create(REVIEWS)

        for review in BookReview.objects.all():
            review.likes.add(*random.sample(list(allUsers), random.randint(0, allUsers.count())))
            review.dislikes.add(*random.sample(list(allUsers), random.randint(0, allUsers.count())))
