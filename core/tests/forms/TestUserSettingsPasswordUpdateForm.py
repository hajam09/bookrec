from unittest.mock import patch

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTest import BaseTest
from core.forms import UserSettingsPasswordUpdateForm


class UserSettingsPasswordUpdateFormTest(BaseTest):
    def setUp(self, path=None) -> None:
        super(UserSettingsPasswordUpdateFormTest, self).setUp(path)
        self.login()

    @patch('core.forms.login')
    def testValidForm(self, mockLogin):
        mockLogin.return_value = None
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': 'NewPassword123',
            'repeatNewPassword': 'NewPassword123',
        }
        form = UserSettingsPasswordUpdateForm(self.request, data=data)
        self.assertTrue(form.is_valid())
        form.updatePassword()
        user = form.reAuthenticate()
        self.user.check_password('NewPassword123')
        self.assertIsNotNone(user)
        # todo: test the messages upon successful password update after reAuthenticate

    def testIncorrectCurrentPassword(self):
        data = {
            'currentPassword': 'wrongpassword',
            'newPassword': 'NewPassword123',
            'repeatNewPassword': 'NewPassword123',
        }
        form = UserSettingsPasswordUpdateForm(self.request, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            'Your current password does not match with the account\'s existing password.',
            form.errors.get('__all__')[0]
        )

    def testNewPasswordMismatch(self):
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': 'NewPassword123',
            'repeatNewPassword': 'DifferentPassword123',
        }
        form = UserSettingsPasswordUpdateForm(self.request, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            'Your new password and confirm password does not match.',
            form.errors.get('__all__')[0]
        )

    def testNewPasswordNotStrong(self):
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': '123',
            'repeatNewPassword': '123',
        }
        form = UserSettingsPasswordUpdateForm(self.request, data=data)
        self.assertFalse(form.is_valid())
        self.assertEqual(
            'Your new password is not strong enough.',
            form.errors.get('__all__')[0]
        )

    @patch('core.forms.authenticate')
    def testPasswordUpdatedButUnableToReAuthenticate(self, mockAuthenticate):
        mockAuthenticate.return_value = None
        data = {
            'currentPassword': TEST_PASSWORD,
            'newPassword': 'NewPassword123',
            'repeatNewPassword': 'NewPassword123',
        }
        form = UserSettingsPasswordUpdateForm(self.request, data=data)
        self.assertTrue(form.is_valid())
        form.updatePassword()
        user = form.reAuthenticate()
        self.user.check_password('NewPassword123')
        self.assertIsNone(user)
        # todo: test the messages upon successful password update after reAuthenticate
