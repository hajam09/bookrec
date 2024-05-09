from unittest.mock import patch

from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status

from bookrec.tests.BaseTestAjax import BaseTestAjax


class AccountDeleteCodeApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self, path=reverse('core:accountDeleteCodeApiEventVersion1Component')) -> None:
        super(AccountDeleteCodeApiEventVersion1ComponentTest, self).setUp(path)

    @patch('bookrec.operations.emailOperations.sendEmailForAccountDeletionCode')
    def testAuthenticatedUser(self, sendEmailForAccountDeletionCode):
        self.client.force_login(self.user)
        response = self.get()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        sendEmailForAccountDeletionCode.assert_called_once()

    def testUnauthenticatedUser(self):
        response = self.get()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['data']['alerts'][0]['alert'], 'danger')
        self.assertEqual(response.data['data']['alerts'][0]['message'], 'Login to request a code.')

    def testSessionCreation(self):
        self.get()
        self.assertTrue(self.client.session.session_key)

    def testVersionInResponse(self):
        self.client.force_login(self.user)
        response = self.get()
        self.assertEqual(response.data['version'], '1.0.0')

    def testCorrectDeleteCode(self):
        self.client.force_login(self.user)
        session_key = self.client.session.session_key
        response = self.delete(data={'code': session_key})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.filter(id=self.request.user.id).first()
        self.assertIsNotNone(user)
        self.assertEqual('redacted', user.first_name)
        self.assertEqual('redacted', user.last_name)
        self.assertEqual('redacted', user.username)
        self.assertEqual('redacted@bookrec.com', user.email)
        self.assertFalse(user.is_active)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['alerts'][0]['alert'], 'success')
        self.assertEqual(response.data['data']['alerts'][0]['message'], 'Account deleted successfully.')

    def testIncorrectDeleteCode(self):
        self.client.force_login(self.user)
        response = self.delete(data={'code': 'incorrect_code'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user = User.objects.filter(id=self.request.user.id).first()
        self.assertIsNotNone(user)
        self.assertEqual('Test', user.first_name)
        self.assertEqual('User', user.last_name)
        self.assertEqual('test.user@example.com', user.username)
        self.assertEqual('test.user@example.com', user.email)
        self.assertTrue(user.is_active)
        self.assertEqual(response.data['success'], False)
        self.assertEqual(response.data['data']['alerts'][0]['alert'], 'danger')
        self.assertEqual(
            response.data['data']['alerts'][0]['message'],
            'Account delete code is incorrect, please try again later.'
        )
