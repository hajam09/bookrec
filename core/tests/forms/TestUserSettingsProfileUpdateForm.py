from bookrec.tests.BaseTest import BaseTest
from core.forms import UserSettingsProfileUpdateForm


class UserSettingsProfileUpdateFormTest(BaseTest):
    def setUp(self, path=None) -> None:
        super(UserSettingsProfileUpdateFormTest, self).setUp(path)

    def testValidForm(self):
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'genres': ['Category_1', 'Category_2', 'Category_3']
        }
        form = UserSettingsProfileUpdateForm(self.request, data=data)
        self.assertTrue(form.is_valid())

        form.save()
        self.assertEqual(self.user.first_name, 'John')
        self.assertEqual(self.user.last_name, 'Doe')
        self.assertListEqual(self.user.profile.favouriteGenres, ['Category_1', 'Category_2', 'Category_3'])

    def testInvalidForm(self):
        data = {
            'first_name': '',
            'last_name': 'Doe',
            'genres': ['Action', 'Adventure']
        }
        form = UserSettingsProfileUpdateForm(self.request, data=data)
        self.assertFalse(form.is_valid())
        self.assertTrue('first_name' in form.errors)
        self.assertTrue('genres' in form.errors)
        self.assertEqual('This field is required.', form.errors.get('first_name')[0])
        self.assertEqual(
            'Select a valid choice. Action is not one of the available choices.', form.errors.get('genres')[0]
        )

    def testDisabledEmailField(self):
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'new_email@example.com',
            'genres': ['Category_1', 'Category_2', 'Category_3']
        }
        form = UserSettingsProfileUpdateForm(self.request, data=form_data)
        self.assertTrue(form.is_valid())
        self.assertNotEqual(self.user.email, 'new_email@example.com')
