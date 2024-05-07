from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTestViews import BaseTestViews


class PasswordUpdateRequestTest(BaseTestViews):

    def setUp(self, path=None) -> None:
        super(PasswordUpdateRequestTest, self).setUp(path)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = PasswordResetTokenGenerator().make_token(self.user)

    def testPasswordUpdateRequestSuccess(self):
        path = reverse('core:password-update-request', kwargs={'base64': self.uid, 'token': self.token})
        response = self.get(path=path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/passwordUpdateForm.html')

    def testPasswordUpdateRequestFailedDecode(self):
        path = reverse('core:password-update-request', kwargs={'base64': 'invalidbase64', 'token': self.token})
        response = self.get(path=path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testPasswordUpdateRequestFailedUserDoesNotExist(self):
        uid = urlsafe_base64_encode(force_bytes(999999))  # Assuming there's no user with pk=999999
        path = reverse('core:password-update-request', kwargs={'base64': uid, 'token': self.token})
        response = self.get(path=path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')

    def testPasswordUpdateRequestPostSuccess(self):
        path = reverse('core:password-update-request', kwargs={'base64': self.uid, 'token': self.token})
        data = {'password': f'{TEST_PASSWORD}-1', 'repeatPassword': f'{TEST_PASSWORD}-1'}
        response = self.post(data, path)
        self.assertEqual(response.status_code, 200)  # should be 302
        self.assertRedirects(response, '/login/')

    def testPasswordUpdateRequestPostInvalidForm(self):
        path = reverse('core:password-update-request', kwargs={'base64': self.uid, 'token': self.token})
        data = {'password': f'{TEST_PASSWORD}-1', 'repeatPassword': f'{TEST_PASSWORD}'}
        response = self.post(data, path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/passwordUpdateForm.html')

        for message in response.context['form'].errors.as_data()['__all__'][0]:
            self.assertEquals(message, 'Your new password and confirm password does not match.')

    def testPasswordUpdateRequestPostUserDoesNotExist(self):
        uid = urlsafe_base64_encode(force_bytes(999999))  # Assuming there's no user with pk=999999
        path = reverse('core:password-update-request', kwargs={'base64': uid, 'token': self.token})
        data = {'password': f'{TEST_PASSWORD}-1', 'repeatPassword': f'{TEST_PASSWORD}'}
        response = self.post(data, path)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/linkFailedTemplate.html')
