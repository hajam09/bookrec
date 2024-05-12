from unittest.mock import patch

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTest import BaseTest
from core.forms import LoginForm


class LoginFormTest(BaseTest):

    def setUp(self, path=None) -> None:
        super(LoginFormTest, self).setUp(path)

    @patch('core.forms.login')
    def testFormIsValid(self, mockLogin):
        mockLogin.return_value = True
        testParams = self.TestParams(email=self.user.email, password=TEST_PASSWORD)
        form = LoginForm(request=self.request, data=testParams.getData())
        self.client.login(username=self.user.username, password=TEST_PASSWORD)
        self.assertTrue(form.is_valid())
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual({}, form.errors.as_data())

    def testFormIncorrectCredentials(self):
        testParams = self.TestParams(email=self.user.email, password='TEST_PASSWORD')
        form = LoginForm(request=self.request, data=testParams.getData())
        self.assertFalse(form.is_valid())
        self.assertEqual(len(form.errors), 1)
        self.assertNotIn('_auth_user_id', self.client.session)

        for message in form.errors.as_data()['password'][0]:
            self.assertEqual(message, 'Please enter a correct email and password.')

    class TestParams:

        def __init__(self, email, password):
            self.email = email
            self.password = password

        def getData(self):
            data = {
                'email': self.email,
                'password': self.password,
            }
            return data
