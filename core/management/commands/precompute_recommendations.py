from types import SimpleNamespace

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from bookrec.operations import bookOperations
from core.models import PrecomputedRecommendation


class Command(BaseCommand):
    help = "Precompute heavy recommendations and store them per user."

    def add_arguments(self, parser):
        parser.add_argument(
            "--user-id",
            type=int,
            default=None,
            help="Only compute for a single user id",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=20,
            help="Number of ISBNs to store per recommendation type",
        )

    def handle(self, *args, **options):
        userId = options.get("user_id")
        limit = int(options.get("limit") or 20)

        users = User.objects.filter(id=userId) if userId else User.objects.all()
        now = timezone.now()

        computed = 0
        for user in users.iterator():
            dummyRequest = SimpleNamespace(user=user)

            # 1) Rating-based collaborative filtering
            ratingBooks = bookOperations.booksBasedOnRating(dummyRequest)
            ratingIsbns = list(ratingBooks.values_list("isbn13", flat=True)[:limit]) if ratingBooks else []
            self._upsert(user, PrecomputedRecommendation.Type.BASED_ON_RATING, ratingIsbns, now)

            # 2) Other users' favourites collaborative filtering
            otherFavBooks = bookOperations.computeOtherUsersFavouriteBooks(user, limit=limit)
            otherFavIsbns = [b.isbn13 for b in otherFavBooks][:limit] if otherFavBooks else []
            self._upsert(user, PrecomputedRecommendation.Type.OTHER_USERS_FAVOURITE, otherFavIsbns, now)

            computed += 1

        self.stdout.write(self.style.SUCCESS(f"Precomputed recommendations for {computed} user(s)."))

    @staticmethod
    def _upsert(user, recommendationType, isbns, now):
        PrecomputedRecommendation.objects.update_or_create(
            user=user,
            recommendationType=recommendationType,
            defaults={
                "isbns": isbns,
                "generatedAt": now,
            },
        )

