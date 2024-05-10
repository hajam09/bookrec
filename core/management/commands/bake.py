import datetime
import random
import threading

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils import timezone
from faker import Faker

from bookrec.operations import bookOperations
from core.models import Book, BookReview, Category, Profile


class Command(BaseCommand):
    PASSWORD = 'admin'
    NUMBER_OF_USERS = 40
    NUMBER_OF_REVIEWS_PER_BOOK = 30

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
                self.downloadBooks()
                self.bulkCreateUsersAndProfiles()
                self.bulkCreateBookReviews()
        except BaseException as e:
            print('Failed to seed data. Rolled back all the transactions', e)

        return

    def _email(self, first_name, last_name):
        return f'{first_name}.{last_name}@{self.faker.free_email_domain()}'

    def bulkCreateUsersAndProfiles(self):
        print(f'Attempting to create {Command.NUMBER_OF_USERS} users and profiles.')
        Profile.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        USERS = []
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

        User.objects.bulk_create(USERS)

        allCategory = Category.objects.all()
        allCategoryCount = allCategory.count()

        PROFILES = []
        for user in User.objects.all():
            n = min(random.randint(3, 10), allCategoryCount)
            randomCategories = allCategory.order_by('?')[:n]

            profile = Profile()
            profile.user = user
            profile.favouriteGenres = list(randomCategories.values_list('name', flat=True))
            PROFILES.append(profile)

        Profile.objects.bulk_create(PROFILES)
        return

    def bulkCreateBookReviews(self):
        print(f'Attempting to create {Command.NUMBER_OF_REVIEWS_PER_BOOK} reviews per book.')
        allUsers = list(User.objects.all().values_list('id', flat=True))
        BookReview.objects.all().delete()

        for book in Book.objects.all():
            for user in random.sample(allUsers, Command.NUMBER_OF_REVIEWS_PER_BOOK):
                bookReview = BookReview()
                bookReview.book = book
                bookReview.edited = random.choice([True, False])
                bookReview.creator_id = user
                bookReview.comment = self.faker.paragraph()
                bookReview.rating = random.randint(0, 5)
                bookReview.createdDateTime = timezone.now() - datetime.timedelta(seconds=random.randint(0, 999999999))
                bookReview.save()

        for review in BookReview.objects.all():
            review.likes.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))
            review.dislikes.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))

        bookList = Book.objects.all()

        for book in bookList:
            book.favouriteRead.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))
            book.readingNow.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))
            book.toRead.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))
            book.haveRead.add(*random.sample(list(allUsers), random.randint(0, len(allUsers))))

        return

    def downloadBooksFromApi(self, books):
        for book in books:
            print('Downloading book ' + book)
            try:
                bookOperations.googleBooksAPIRequests(book)
            except Exception as e:
                print(f'Exception found when attempting to download book: {book}, {e}')

    def downloadBooks(self):
        print(f'Attempting to download books to the system')
        Book.objects.all().delete()
        bookNames = [
            "A view from the bridge", "Of mice and men", "Zenith", "Harry potter", "To Kill a Mockingbird", "1984",
            "The Great Gatsby", "Pride and Prejudice", "The Catcher in the Rye", "Animal Farm", "The Lord of the Rings",
            "Jane Eyre", "The Hobbit", "Brave New World", "The Chronicles of Narnia", "Wuthering Heights",
            "Lord of the Flies", "The Grapes of Wrath", "Great Expectations", "Catch-22", "Little Women",
            "The Scarlet Letter", "Moby Dick", "Fahrenheit 451", "A Tale of Two Cities", "The Picture of Dorian Gray",
            "The Hitchhiker's Guide to the Galaxy", "Gone with the Wind", "Crime and Punishment", "Frankenstein",
            "Anna Karenina", "One Hundred Years of Solitude", "The Odyssey", "The Bell Jar", "The Brothers Karamazov",
            "Don Quixote", "The Count of Monte Cristo", "War and Peace", "The Stranger", "Dracula", "The Road",
            "Les Miserables", "The Sun Also Rises", "Slaughterhouse-Five", "The Old Man and the Sea",
            "A Clockwork Orange", "Heart of Darkness", "The Canterbury Tales", "Lolita", "The Divine Comedy",
            "The Stranger Beside Me", "The Shining", "The Secret History", "The Poisonwood Bible", "The Stand",
            "The Road Less Traveled", "The Handmaid's Tale", "American Gods", "Ender's Game",
            "The Adventures of Huckleberry Finn", "Alice's Adventures in Wonderland", "The Picture of Dorian Gray",
            "The Adventures of Sherlock Holmes", "The Time Machine", "Dr. Jekyll and Mr. Hyde", "Oliver Twist",
            "Treasure Island", "The War of the Worlds", "Gulliver's Travels", "The Jungle Book", "Anne of Green Gables",
            "Around the World in Eighty Days", "Black Beauty", "A Christmas Carol", "The Wind in the Willows",
            "Peter Pan", "Sense and Sensibility", "The Adventures of Tom Sawyer", "Mansfield Park",
            "The Call of the Wild", "White Fang", "The Hound of the Baskervilles", "The Three Musketeers",
            "Twenty Thousand Leagues Under the Sea", "Robinson Crusoe", "The Swiss Family Robinson",
            "David Copperfield", "A Journey to the Center of the Earth", "The Phantom of the Opera",
            "The Strange Case of Dr. Coué", "The Mysterious Affair at Styles", "The Lost World",
            "The Legend of Sleepy Hollow", "The Last of the Mohicans", "Northanger Abbey", "The Woman in White",
            "The Portrait of a Lady", "The Turn of the Screw", "The Red Badge of Courage", "The Call of Cthulhu",
            "The Arabian Nights", "The Island of Dr. Moreau", "The Jungle", "The Moonstone",
            "The Murders in the Rue Morgue", "The War in the Air", "The Thirty-Nine Steps",
            "The Wonderful Wizard of Oz", "The Prince and the Pauper", "The Last Man", "The Prince",
            "The Strange Case of Dr. Jekyll and Mr. Hyde", "The Yellow Wallpaper", "The Art of War",
            "The Importance of Being Earnest", "The Little Prince", "The Metamorphosis", "The Outsiders", "The Raven",
            "The Republic", "The Road to Wigan Pier", "The Sound and the Fury", "The Tempest",
            "The Things They Carried", "The Waste Land", "The Wind-Up Bird Chronicle", "The Woman Warrior",
            "Things Fall Apart", "Thus Spoke Zarathustra", "Tinker Tailor Soldier Spy", "To the Lighthouse",
            "Travels with Charley", "Ulysses", "Uncle Tom's Cabin", "Under the Net", "Waiting for Godot", "Walden",
            "Watchmen", "Where the Sidewalk Ends", "White Noise", "Wide Sargasso Sea", "Winesburg, Ohio",
            "Winnie-the-Pooh", "Woman Hollering Creek", "Women in Love", "World War Z", "Wuthering Heights",
            "Zen and the Art of Motorcycle Maintenance", "The Hunger Games", "The Girl with the Dragon Tattoo",
            "The Da Vinci Code", "The Help", "The Kite Runner", "The Alchemist", "The Girl on the Train", "Gone Girl",
            "The Fault in Our Stars", "The Girl with the Pearl Earring", "The Notebook", "The Martian",
            "The Joy Luck Club", "The Secret Life of Bees", "The Lovely Bones", "The Book Thief",
            "The Time Traveler's Wife", "The Color Purple", "The Pillars of the Earth", "The Night Circus",
            "The Goldfinch", "The Shadow of the Wind", "The Glass Castle", "The Nightingale",
            "The Light Between Oceans", "The Immortal Life of Henrietta Lacks", "The Miniaturist", "The Night Manager",
            "The Nest", "The Snowman", "The Bone Collector", "The Night Stalker", "The Silent Patient", "The Chain",
            "The Silent Wife", "The Whisper Man", "The Guest List", "The Woman in Cabin 10", "The Girl in the Ice",
            "The Last Mrs. Parrish", "The Woman in the Window", "The Wife Between Us", "The Flight Attendant",
            "The Couple Next Door", "The Girl Who Lived", "The Good Daughter", "The Wife", "The Girl Before",
            "The Wife Stalker", "The Last House Guest", "The Other Woman", "The Wife Upstairs", "The Guest List",
            "The Silent Wife", "The Dilemma", "The Holdout", "The Wife Between Us", "The Lying Game",
            "The Wife Upstairs", "The Guest List", "The Wives", "The Girl You Left Behind", "The Wife",
            "The Girl Before", "The Wife Stalker", "The Housekeeper", "The Other Wife", "The Wife Between Us",
            "The Night Swim", "The Wife Upstairs", "The Guest List", "The Silent Patient", "The Wife",
            "The Girl Before", "The Wife Stalker", "The Wife Between Us", "The Guest List", "The Good Girl",
            "The Wife Upstairs", "The Silent Wife", "The Last Mrs. Parrish", "The Wife", "The Girl Before",
            "The Wife Stalker", "The Silent Patient", "The Wife Between Us", "The Guest List", "The Girl in the Mirror",
            "The Wife Upstairs", "The Silent Wife", "The Last Mrs. Parrish", "The Wife", "The Wife Stalker",
            "The Guest List", "The Girl in the Mirror", "The Silent Patient", "The Wife Between Us",
            "The Wife Upstairs", "The Girl You Gave Away", "The Wife", "The Wife Stalker", "The Silent Wife",
            "The Last Mrs. Parrish", "The Guest List", "The Girl in the Mirror", "The Silent Patient",
            "The Wife Between Us", "The Wife Upstairs",
        ]

        print(f'Attempting to download {len(bookNames)} books to the system.')

        NUMBER_OF_THREADS = 4
        chunks = [bookNames[i::NUMBER_OF_THREADS] for i in range(NUMBER_OF_THREADS)]

        threads = []
        for chunk in chunks:
            thread = threading.Thread(target=self.downloadBooksFromApi, args=(chunk,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        print("All books downloaded successfully.")
        return
