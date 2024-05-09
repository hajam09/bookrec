from django.urls import reverse
from rest_framework import status

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTestAjax import BaseTestAjax


class UserPasswordUpdateApiEventVersion1ComponentTest(BaseTestAjax):
    def setUp(self, path=reverse('core:userPasswordUpdateApiEventVersion1Component')) -> None:
        super(UserPasswordUpdateApiEventVersion1ComponentTest, self).setUp(path)

    def testOnlyThatCurrentPasswordDoesNotMatchWithExistingUserPassword(self):
        self.client.force_login(user=self.user)
        data = {
            'currentPassword': 'old_password',
            'newPassword': 'm#P52s@ap$V',
            'repeatNewPassword': 'm#P52s@ap$V'
        }

        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['data']['alerts'],
            [{'alert': 'danger', 'message': "Your current password doesn't match the existing one."}
             ]
        )

    def testOnlyNewPasswordAndConfirmPasswordDoNotMatch(self):
        self.client.force_login(user=self.user)
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': 'm#P52s@ap$V1',
            'repeatNewPassword': 'm#P52s@ap$V'
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['data']['alerts'],
            [{'alert': 'danger', 'message': "Your new password and confirm password does not match."}
             ]
        )

    def testOnlyNewPasswordIsNotStrongEnough(self):
        self.client.force_login(user=self.user)
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': '123',
            'repeatNewPassword': '123'
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['data']['alerts'],
            [{'alert': 'danger', 'message': "Your new password is not strong enough."}
             ]
        )

    def testPasswordUpdatedSuccessfully(self):
        self.client.force_login(user=self.user)
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': f'{TEST_PASSWORD} + WtfvN!!kJov]I;N',
            'repeatNewPassword': f'{TEST_PASSWORD} + WtfvN!!kJov]I;N'
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(
            response.data['data']['alerts'],
            [{'alert': 'success', 'message': "Password updated successfully."}
             ]
        )
        self.assertFalse(self.user.check_password(f'{TEST_PASSWORD} + WtfvN!!kJov]I;N'))
