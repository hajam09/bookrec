from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import Client
from django.test import RequestFactory
from django.test import TestCase

from bookrec.settings import TEST_PASSWORD
from core.models import Profile


class BaseTest(TestCase):
    # coverage run --source='.' manage.py test && coverage html

    def createUserAndProfile(self):
        self.user = User(
            username='test.user@example.com', email='test.user@example.com', first_name='Test', last_name='User'
        )
        self.user.set_password(TEST_PASSWORD)
        self.user.save()

        Profile.objects.create(
            user=self.user,
            favouriteGenres=['Category_1', 'Category_2', 'Category_3', 'Category_4'],
            profilePicture=None
        )
        return self.user

    def setUp(self, url='') -> None:
        """
        setUp: Run once for every test method to setup clean data.
        """
        self.factory = RequestFactory()
        self.user = self.createUserAndProfile()
        self.client = Client(
            HTTP_USER_AGENT='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36'
        )

        self.request = self.factory.get(url)
        self.request.user = self.user

        # To fix the messages during unit testing
        setattr(self.request, 'session', 'session')
        messages = FallbackStorage(self.request)
        setattr(self.request, '_messages', messages)

    def login(self):
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

    @classmethod
    def setUpClass(cls):
        super(BaseTest, cls).setUpClass()

    def tearDown(self) -> None:
        self.client.logout()
        self.user.delete()
        super(BaseTest, self).tearDown()

    @classmethod
    def tearDownClass(cls):
        super(BaseTest, cls).tearDownClass()

    @classmethod
    def setUpTestData(cls):
        """
        setUpTestData: Run once to set up non-modified data for all class methods.
        """
        pass

    def getSessionKey(self):
        return self.client.session.session_key

    def getMessages(self, response):
        return list(get_messages(response.wsgi_request))
