from django.urls import reverse
from rest_framework import status

from bookrec.tests.BaseTestAjax import BaseTestAjax


class ProfileApiEventVersion1ComponentTest(BaseTestAjax):

    def setUp(self, path=reverse('core:profileApiEventVersion1Component')) -> None:
        super(ProfileApiEventVersion1ComponentTest, self).setUp(path)
        self.login()

    def test_get_profile_success(self):
        response = self.get()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], '1.0.0')
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['profile']['firstName'], 'Test')
        self.assertEqual(response.data['data']['profile']['lastName'], 'User')
        self.assertEqual(response.data['data']['profile']['email'], 'test.user@example.com')
        self.assertEqual(
            response.data['data']['profile']['favouriteGenres'],
            ['Category_1', 'Category_2', 'Category_3', 'Category_4']
        )
        self.assertIsNone(response.data['data']['profile']['profilePicture'])

    def test_update_profile_success(self):
        data = {
            'firstName': 'Updated First Name',
            'lastName': 'Updated Last Name',
            'email': 'updated@example.com',
            'genres': ['Action', 'Adventure']
        }
        response = self.put(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['version'], '1.0.0')
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['data']['alerts'][0]['alert'], 'success')
        self.assertEqual(response.data['data']['alerts'][0]['message'], 'Profile update successfully.')

        # Refresh profile from DB and check updated values
        self.user.profile.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated First Name')
        self.assertEqual(self.user.last_name, 'Updated Last Name')
        self.assertEqual(self.user.email, 'updated@example.com')
        self.assertEqual(self.user.profile.favouriteGenres, ['Action', 'Adventure'])
