from django.urls import reverse

from bookrec.tests.BaseTestViews import BaseTestViews


class LogoutViewTest(BaseTestViews):

    def setUp(self, path=reverse('core:logout-view')) -> None:
        super(LogoutViewTest, self).setUp(path)

    def testLogoutRedirectToPreviousUrl(self):
        self.client.force_login(self.user)
        response = self.client.get(path=self.path, HTTP_REFERER='/previous/url/')
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.url, '/previous/url/')

    def testLogoutRedirectToDefaultUrl(self):
        self.client.force_login(self.user)
        response = self.get()
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(response.url, reverse('core:index-view'))
