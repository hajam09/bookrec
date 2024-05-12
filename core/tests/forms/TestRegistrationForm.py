from django.contrib.auth.models import User

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTest import BaseTest
from core.forms import RegistrationForm
from core.models import Category


class RegistrationFormTest(BaseTest):
    def setUp(self, path=None) -> None:
        super(RegistrationFormTest, self).setUp(path)

    def testAccountAlreadyExists(self):
        testParams = self.TestParams(self.request.user.email, TEST_PASSWORD, TEST_PASSWORD, [])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['email'][0]:
            self.assertEqual(message, 'An account already exists for this email address!')

    def testPasswordsNotEqual(self):
        testParams = self.TestParams('example@example.com', TEST_PASSWORD, 'TEST_PASSWORD', [])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEqual(message, 'Your passwords do not match!')

    def testPasswordDoesNotHaveAlphabets(self):
        testParams = self.TestParams('example@example.com', '1234567890', '1234567890', [])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEqual(message, 'Your password is not strong enough.')

    def testPasswordDoesNotHaveCapitalLetters(self):
        testParams = self.TestParams('example@example.com', 'test_password', 'test_password', [])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEqual(message, 'Your password is not strong enough.')

    def testPasswordDoesNotHaveNumbers(self):
        testParams = self.TestParams('example@example.com', 'TEST_PASSWORD', 'TEST_PASSWORD', [])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['password2'][0]:
            self.assertEqual(message, 'Your password is not strong enough.')

    def testLessThan3GenresSelected(self):
        testParams = self.TestParams('example@example.com', 'TEST_PASSWORD', 'TEST_PASSWORD', ['Category_1'])
        form = RegistrationForm(data=testParams.getData())
        self.assertFalse(form.is_valid())

        for message in form.errors.as_data()['genres'][0]:
            self.assertEqual(message, 'Select at least 3 different genres.')

    def testRegisterUserSuccessfully(self):
        selectedGenres = ['Category_1', 'Category_2', 'Category_3']
        testParams = self.TestParams('example@example.com', TEST_PASSWORD, TEST_PASSWORD, selectedGenres)
        form = RegistrationForm(data=testParams.getData())
        self.assertTrue(form.is_valid())
        form.save()

        user = User.objects.get(email='example@example.com')
        self.assertTrue(user.check_password(TEST_PASSWORD))
        self.assertEqual('firstName', user.first_name)
        self.assertEqual('lastName', user.last_name)

    class TestParams:
        def __init__(self, email, password1, password2, genres):
            self.email = email
            self.password1 = password1
            self.password2 = password2
            self.firstName = 'firstName'
            self.lastName = 'lastName'
            self.genres = genres

        def getData(self):
            data = {
                'email': self.email,
                'password1': self.password1,
                'password2': self.password2,
                'first_name': self.firstName,
                'last_name': self.lastName,
                'genres': self.genres,
            }
            return data
