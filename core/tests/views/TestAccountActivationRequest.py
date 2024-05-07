from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework.reverse import reverse

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTestViews import BaseTestViews


class AccountActivationRequestTest(BaseTestViews):

    def setUp(self, path=None) -> None:
        self.prtg = PasswordResetTokenGenerator()
        super(AccountActivationRequestTest, self).setUp(path)
        self.request.user.is_active = False
        self.request.user.save()

    def testDjangoUnicodeDecodeErrorCaught(self):
        token = self.prtg.make_token(self.request.user)
        path = reverse('core:account-activation-request', kwargs={'base64': 'DECODE_ERROR', 'token': token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testUserDoesNotExistCaught(self):
        base64 = urlsafe_base64_encode(force_bytes(0))
        token = self.prtg.make_token(self.request.user)
        path = reverse('core:account-activation-request', kwargs={'base64': base64, 'token': token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testValueErrorCaught(self):
        base64 = urlsafe_base64_encode(force_bytes('ID'))
        token = self.prtg.make_token(self.request.user)
        path = reverse('core:account-activation-request', kwargs={'base64': base64, 'token': token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testIncorrectToken(self):
        newUser = User(
            username='test2.user@example.com',
            email='test2.user@example.com',
            first_name='Test2',
            last_name='User2'
        )
        newUser.set_password(TEST_PASSWORD)
        newUser.save()

        base64 = urlsafe_base64_encode(force_bytes(newUser.id))
        token = self.prtg.make_token(self.request.user)
        path = reverse('core:account-activation-request', kwargs={'base64': base64, 'token': token})
        response = self.get(path=path)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testUserActivatedSuccessfully(self):
        self.assertFalse(self.request.user.is_active)

        base64 = urlsafe_base64_encode(force_bytes(self.request.user.id))
        token = self.prtg.make_token(self.request.user)
        path = reverse('core:account-activation-request', kwargs={'base64': base64, 'token': token})

        response = self.get(path=path)
        messages = self.getMessages(response)
        self.request.user.refresh_from_db()

        self.assertTrue(self.request.user.is_active)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/login/')

        self.assertEqual(1, len(messages))
        for message in messages:
            self.assertEqual(
                str(message),
                'Account activated successfully'
            )
