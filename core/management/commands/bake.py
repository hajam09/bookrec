import datetime
import random
import time

from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from tqdm import tqdm

from core.models import (
    Book,
    BookReview,
    Category,
    Profile,
    UserActivityLog
)

genres = [
    # Fiction
    "Action", "Adventure", "Alternate History", "Chick Lit", "Contemporary Romance",
    "Dark Fantasy", "Detective Fiction", "Crime Fiction", "Dystopian", "Epic Fantasy",
    "Fairy Tales", "Fantasy", "Gothic Horror", "Historical Fiction", "Historical Mystery",
    "Historical Romance", "Horror", "Literary Fiction", "Literary Fantasy", "Magical Realism",
    "Middle Grade", "Mystery", "Mythology", "New Adult", "Paranormal", "Post-Apocalyptic",
    "Psychological Thriller", "Romance", "Romantic Comedy", "Romantic Suspense", "Science Fiction",
    "Spy / Espionage", "Steampunk", "Supernatural", "Thriller", "Urban Fantasy", "Western",
    "Young Adult", "Short Stories", "Epistolary Fiction", "Experimental Fiction", "Picture Books",

    # Non-fiction
    "Academic Journal", "Art", "Art Theory", "Architecture", "Autobiography", "Memoir",
    "Biography", "Business", "Economics", "Finance", "Cooking", "Baking", "Food & Drink",
    "Crafts", "DIY", "Design", "Education", "Teaching", "Encyclopedia", "Reference",
    "Film", "Music", "Performing Arts", "Theater", "Gardening", "Outdoors", "Nature",
    "Pets", "Health & Wellness", "Fitness", "Nutrition", "Medicine", "Nursing", "Pharmacy",
    "Journalism", "Language Learning", "Linguistics", "Law", "Legal Thriller", "Philosophy",
    "Theology", "Religion", "Spirituality", "Politics", "Sociology", "Psychology",
    "Science", "Data Science", "Technology", "Programming", "Artificial Intelligence",
    "Engineering", "Mathematics", "Self-Help", "Personal Development", "Motivational",
    "Productivity", "Mindfulness", "Travel", "Guidebooks", "True Crime", "Historical Accounts",
    "Research", "Essays", "Home Improvement", "Fashion", "Beauty",

    # Graphic / Illustrated
    "Comic Book", "Graphic Novel", "Manga", "Illustrated Books"
]


class Command(BaseCommand):
    NUMBER_OF_BOOKS = 200
    NUMBER_OF_BOOKS_BATCH = 50

    NUMBER_OF_USERS = 20
    NUMBER_OF_USERS_BATCH = 5

    NUMBER_OF_REVIEWS = 40
    NUMBER_OF_REVIEWS_BATCH = 10

    NUMBER_OF_LOGS = 200
    NUMBER_OF_LOGS_BATCH = 50

    def __init__(self):
        super().__init__()
        self.faker = Faker('en_GB')

    def handle(self, *args, **kwargs):
        self.seedBooks()
        self.seedUsers()
        self.seedReviews()
        self.seedLogs()

    def seedBooks(self):
        start_time = time.time()
        self.stdout.write("🔹 Starting database reset and book creation...\n")

        # Delete old data
        self.stdout.write("🗑️ Deleting existing books and categories...")
        Book.objects.all().delete()
        Category.objects.all().delete()
        self.stdout.write("✅ Deleted old books and categories.\n")

        # Recreate categories
        self.stdout.write(f"📚 Creating {len(genres)} categories...")
        categories = [Category(name=genre) for genre in genres]
        Category.objects.bulk_create(categories)
        self.stdout.write("✅ Categories created successfully.\n")

        # Creating books with tqdm progress bar
        self.stdout.write(f"📖 Creating {self.NUMBER_OF_BOOKS} books in batches of {self.NUMBER_OF_BOOKS_BATCH}...")
        books = []
        for i in tqdm(range(1, self.NUMBER_OF_BOOKS + 1), desc="Books created", unit="book"):
            book = Book(
                title=self.faker.sentence(nb_words=random.randint(1, 5)),
                authors=[self.faker.name() for _ in range(random.randint(1, 3))],
                publisher=self.faker.company(),
                publishedDate=self.faker.date_between(start_date='-30y', end_date='today'),
                description=self.faker.paragraph(nb_sentences=random.randint(5, 25)),
                isbn13=self.faker.unique.isbn13().replace("-", ""),
                categories=random.sample(genres, random.randint(1, 3)),
                thumbnail="https://dummyimage.com/200x300",  # self.faker.image_url(),
                selfLink=self.faker.url(),
                averageRating=round(random.uniform(1, 5), 2),
                ratingsCount=random.randint(1, 5000),
            )
            books.append(book)

            # Bulk create in batches
            if i % self.NUMBER_OF_BOOKS_BATCH == 0:
                Book.objects.bulk_create(books, batch_size=self.NUMBER_OF_BOOKS_BATCH)
                books = []

        # Create any remaining books
        if books:
            Book.objects.bulk_create(books, batch_size=len(books))

        elapsed_time = time.time() - start_time
        self.stdout.write(f"\n🎉 Finished creating {self.NUMBER_OF_BOOKS} books in {elapsed_time:.2f} seconds.")

    def seedUsers(self):
        # Delete existing non-superuser users and profiles
        Profile.objects.filter(user__is_superuser=False).delete()
        User.objects.filter(is_superuser=False).delete()
        self.stdout.write("🗑️ Deleted old users and profiles.\n")
        self.stdout.write(f"📄 Creating {self.NUMBER_OF_USERS} users and profiles...\n")

        hashed_password = make_password("admin")

        # ---- Create Users ----
        users_to_create = []
        pbar_users = tqdm(total=self.NUMBER_OF_USERS, desc="Creating users", unit="user")

        for _ in range(self.NUMBER_OF_USERS):
            first_name = self.faker.unique.first_name()
            last_name = self.faker.unique.last_name()
            email = f'{first_name}.{last_name}@{self.faker.free_email_domain()}'

            user = User(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=email,
                password=hashed_password
            )
            users_to_create.append(user)

            # Bulk insert in batches
            if len(users_to_create) >= self.NUMBER_OF_USERS_BATCH:
                User.objects.bulk_create(users_to_create, batch_size=self.NUMBER_OF_USERS_BATCH)
                pbar_users.update(len(users_to_create))
                users_to_create = []

        # Insert remaining users
        if users_to_create:
            User.objects.bulk_create(users_to_create, batch_size=len(users_to_create))
            pbar_users.update(len(users_to_create))
        pbar_users.close()

        # ---- Create Profiles ----
        profiles_to_create = []
        new_users = User.objects.filter(is_superuser=False).order_by('id')
        pbar_profiles = tqdm(total=new_users.count(), desc="Creating profiles", unit="profile")

        for user in new_users:
            favourite_genres = random.sample(genres, random.randint(2, 5))
            profile = Profile(user=user, favouriteGenres=favourite_genres)
            profiles_to_create.append(profile)

            if len(profiles_to_create) >= self.NUMBER_OF_USERS_BATCH:
                Profile.objects.bulk_create(profiles_to_create, batch_size=self.NUMBER_OF_USERS_BATCH)
                pbar_profiles.update(len(profiles_to_create))
                profiles_to_create = []

        # Insert remaining profiles
        if profiles_to_create:
            Profile.objects.bulk_create(profiles_to_create, batch_size=len(profiles_to_create))
            pbar_profiles.update(len(profiles_to_create))
        pbar_profiles.close()

        self.stdout.write(f"\n✅ Successfully created {self.NUMBER_OF_USERS} users with profiles.")

    def seedReviews(self):
        self.stdout.write("🗑️ Deleting existing reviews...")
        BookReview.objects.all().delete()
        self.stdout.write("✅ Done deleting reviews.\n")

        users = list(User.objects.all().values_list('id', flat=True))
        books = list(Book.objects.all())
        total_reviews_created = 0

        self.stdout.write("📄 Generating reviews for books...\n")
        book_reviews_to_create = []

        for book in tqdm(books, desc="Books processed", unit="book"):
            num_reviews = random.randint(40, 61)
            selected_users = random.sample(users, min(num_reviews, len(users)))

            for user_id in selected_users:
                review = BookReview(
                    book=book,
                    creator_id=user_id,
                    edited=random.choice([True, False]),
                    comment=self.faker.paragraph(),
                    rating=random.randint(0, 5),
                    createdDateTime=timezone.make_aware(
                        datetime.datetime.combine(
                            self.faker.date_between(start_date='-5y', end_date='today'),
                            datetime.time.min  # or random time if you want
                        ),
                        timezone.get_current_timezone()
                    )
                )
                book_reviews_to_create.append(review)

                if len(book_reviews_to_create) >= self.NUMBER_OF_REVIEWS_BATCH:
                    BookReview.objects.bulk_create(book_reviews_to_create, batch_size=self.NUMBER_OF_REVIEWS_BATCH)
                    total_reviews_created += len(book_reviews_to_create)
                    book_reviews_to_create = []

        # Create remaining reviews
        if book_reviews_to_create:
            BookReview.objects.bulk_create(book_reviews_to_create)
            total_reviews_created += len(book_reviews_to_create)

        self.stdout.write(f"✅ Created {total_reviews_created} reviews.\n")

        # ---- Bulk add likes and dislikes ----
        self.stdout.write("📄 Adding likes and dislikes to reviews...\n")
        all_reviews = list(BookReview.objects.all())
        through_likes = BookReview.likes.through
        through_dislikes = BookReview.dislikes.through
        likes_to_create = []
        dislikes_to_create = []

        for review in tqdm(all_reviews, desc="Reviews processed", unit="review"):
            like_ids = random.sample(users, random.randint(0, len(users)))
            dislike_ids = random.sample(users, random.randint(0, len(users)))

            for uid in like_ids:
                likes_to_create.append(through_likes(bookreview_id=review.id, user_id=uid))
            for uid in dislike_ids:
                dislikes_to_create.append(through_dislikes(bookreview_id=review.id, user_id=uid))

            # Bulk insert in batches
            if len(likes_to_create) >= self.NUMBER_OF_REVIEWS_BATCH:
                through_likes.objects.bulk_create(likes_to_create, batch_size=self.NUMBER_OF_REVIEWS_BATCH)
                likes_to_create = []
            if len(dislikes_to_create) >= self.NUMBER_OF_REVIEWS_BATCH:
                through_dislikes.objects.bulk_create(dislikes_to_create, batch_size=self.NUMBER_OF_REVIEWS_BATCH)
                dislikes_to_create = []

        if likes_to_create:
            through_likes.objects.bulk_create(likes_to_create)
        if dislikes_to_create:
            through_dislikes.objects.bulk_create(dislikes_to_create)

        self.stdout.write("✅ Likes and dislikes added.\n")

        # ---- Bulk add ManyToMany for book lists ----
        self.stdout.write("📄 Updating user book lists...\n")
        book_relations = [
            ('favouriteRead', Book.favouriteRead.through),
            ('readingNow', Book.readingNow.through),
            ('toRead', Book.toRead.through),
            ('haveRead', Book.haveRead.through)
        ]

        for book in tqdm(books, desc="Books processed", unit="book"):
            for field_name, through_model in book_relations:
                user_ids = random.sample(users, random.randint(0, len(users)))
                m2m_bulk = [through_model(book_id=book.id, user_id=uid) for uid in user_ids]
                if m2m_bulk:
                    through_model.objects.bulk_create(m2m_bulk, batch_size=self.NUMBER_OF_REVIEWS_BATCH,
                                                      ignore_conflicts=True)

        self.stdout.write("\n✅ Finished populating BookReviews and all relations.")

    def seedLogs(self):
        start_time = time.time()
        self.stdout.write("🗑️ Deleting existing user activity logs...")
        UserActivityLog.objects.all().delete()
        self.stdout.write("✅ Deleted old logs.\n")

        users = list(User.objects.all())
        books = list(Book.objects.only("isbn13", "title"))
        actions = list(UserActivityLog.Action)
        book_data_actions = {
            UserActivityLog.Action.EDIT_COMMENT,
            UserActivityLog.Action.ADD_COMMENT,
            UserActivityLog.Action.DELETE_COMMENT,
            UserActivityLog.Action.ADD_TO_FAVOURITES,
            UserActivityLog.Action.REMOVE_FROM_FAVOURITES,
            UserActivityLog.Action.ADD_TO_READING_NOW,
            UserActivityLog.Action.REMOVE_FROM_READING_NOW,
            UserActivityLog.Action.ADD_TO_TO_READ,
            UserActivityLog.Action.REMOVE_FROM_TO_READ,
            UserActivityLog.Action.ADD_TO_HAVE_READ,
            UserActivityLog.Action.REMOVE_FROM_HAVE_READ,
            UserActivityLog.Action.ADD_LIKE_TO_COMMENT,
            UserActivityLog.Action.REMOVE_LIKE_FROM_COMMENT,
            UserActivityLog.Action.ADD_DISLIKE_TO_COMMENT,
            UserActivityLog.Action.REMOVE_DISLIKE_FROM_COMMENT,
            UserActivityLog.Action.VIEW_BOOK,
        }

        self.stdout.write(
            f"📄 Creating {self.NUMBER_OF_LOGS} activity logs per user "
            f"({len(users) * self.NUMBER_OF_LOGS} total)...\n"
        )

        logs_to_create = []
        total_logs = len(users) * self.NUMBER_OF_LOGS
        pbar = tqdm(total=total_logs, desc="Creating activity logs", unit="log")

        for user in users:
            for _ in range(self.NUMBER_OF_LOGS):
                action = random.choice(actions)
                data = {}

                if action in book_data_actions and books:
                    book = random.choice(books)
                    data = {
                        "book-isbn13": book.isbn13,
                        "book-title": book.title,
                    }

                start_date = timezone.now() - datetime.timedelta(days=random.randint(365 * 2, 365 * 5))
                random_seconds = random.randint(0, 24 * 60 * 60 - 1)

                logs_to_create.append(
                    UserActivityLog(
                        user=user,
                        action=action,
                        ipAddress=self.faker.ipv4(),
                        userAgent=self.faker.user_agent(),
                        data=data,
                        timeStamp=start_date + datetime.timedelta(seconds=random_seconds)
                    )
                )

                if len(logs_to_create) >= self.NUMBER_OF_LOGS_BATCH:
                    UserActivityLog.objects.bulk_create(
                        logs_to_create,
                        batch_size=self.NUMBER_OF_LOGS_BATCH,
                    )
                    pbar.update(len(logs_to_create))
                    logs_to_create = []

        if logs_to_create:
            UserActivityLog.objects.bulk_create(logs_to_create, batch_size=len(logs_to_create))
            pbar.update(len(logs_to_create))

        pbar.close()
        elapsed_time = time.time() - start_time
        self.stdout.write(
            f"\n✅ Successfully created {total_logs} user activity logs "
            f"in {elapsed_time:.2f} seconds."
        )
