from unittest.mock import patch

from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.reverse import reverse

from bookrec.tests.BaseTestViews import BaseTestViews


class PasswordChangeRequestTest(BaseTestViews):

    def setUp(self, path=reverse('core:password-change-request')) -> None:
        self.prtg = PasswordResetTokenGenerator()
        super(PasswordChangeRequestTest, self).setUp(path)
        self.request.user.is_active = False
        self.request.user.save()

    def testLoginGet(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/passwordChangeRequest.html')

    @patch('bookrec.operations.emailOperations.sendEmailToChangePassword')
    def testPasswordRequestExistingUser(self, mockSendEmailToChangePassword):
        testParams = self.TestParams(self.user.email)
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        for message in messages:
            self.assertEqual(
                str(message),
                'Check your email for a password change link.'
            )

        mockSendEmailToChangePassword.assert_called_once()

    @patch('bookrec.operations.emailOperations.sendEmailToChangePassword')
    def testPasswordRequestNonExistingUser(self, mockSendEmailToChangePassword):
        testParams = self.TestParams("example@example.com")
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        for message in messages:
            self.assertEqual(
                str(message),
                'Check your email for a password change link.'
            )

        mockSendEmailToChangePassword.assert_not_called()

    class TestParams:

        def __init__(self, email):
            self.email = email

        def getData(self):
            data = {
                'email': self.email,
            }
            return data
