from unittest.mock import patch

from django.core.cache import cache
from django.urls import reverse

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTestViews import BaseTestViews
from core.forms import LoginForm


class LoginViewTest(BaseTestViews):

    def setUp(self, path=reverse('core:login-view')) -> None:
        super(LoginViewTest, self).setUp(path)
        self.client.logout()

    def testLoginGet(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/loginView.html')
        self.assertTrue(isinstance(response.context['form'], LoginForm))

    @patch('core.views.LoginForm.is_valid')
    def testLoginAuthenticateValidUser(self, mockLoginForm):
        mockLoginForm.return_value = True
        testParams = self.TestParams(self.user.email, TEST_PASSWORD)
        self.client.login(username=self.user.username, password=TEST_PASSWORD)

        response = self.post(testParams.getData())
        sessionKey = self.getSessionKey()

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        self.assertEqual(cache.get(sessionKey), None)

    @patch('core.views.LoginForm.is_valid')
    def testLoginAuthenticateInvalidUser(self, mockLoginForm):
        mockLoginForm.return_value = False
        testParams = self.TestParams(self.user.username, 'TEST_PASSWORD')
        response = self.post(testParams.getData())
        sessionKey = self.getSessionKey()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/loginView.html")
        self.assertNotIn('_auth_user_id', self.client.session)

        self.assertEqual(cache.get(sessionKey), 1)

    def testLoginMaxAttempts(self):
        response = None
        for i in range(6):
            response = self.post()

        self.assertNotEqual(cache.get(self.getSessionKey()), None)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/login/')

        messages = list(response.context['messages'])
        self.assertEqual(len(messages), 1)

        for message in messages:
            self.assertEqual(
                str(message),
                'Your account has been temporarily locked out because of too many failed login attempts.'
            )
        cache.set(self.getSessionKey(), None)

    def testLoginRedirectToIndexViewIfAlreadyAuthenticated(self):
        self.client.force_login(self.user)
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')

    @patch('core.views.LoginForm.is_valid')
    def testDeleteCacheAndRedirectToPreviousPageIfExists(self, mockLoginForm):
        mockLoginForm.return_value = True
        testParams = self.TestParams(self.user.email, TEST_PASSWORD)
        self.path += f"?next={reverse('core:user-shelf-view')}"
        response = self.post(testParams.getData())
        self.assertIsNone(cache.get(self.getSessionKey()))

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/login/?next=/user-shelf/')

    @patch('core.views.LoginForm.is_valid')
    def testRedirectToIndexViewIfPreviousPageDoesNotExists(self, mockLoginForm):
        mockLoginForm.return_value = True
        testParams = self.TestParams(self.user.email, TEST_PASSWORD)
        response = self.post(testParams.getData())
        self.assertIsNone(cache.get(self.getSessionKey()))

        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/')

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
