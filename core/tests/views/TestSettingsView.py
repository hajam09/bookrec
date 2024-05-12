from unittest import skip
from unittest.mock import patch

from django.urls import reverse

from bookrec.tests.BaseTestViews import BaseTestViews
from core.forms import UserSettingsProfileUpdateForm, UserSettingsPasswordUpdateForm
from core.views import SettingsView


class SettingsViewTest(BaseTestViews):
    def setUp(self, path=reverse('core:settings-view')) -> None:
        super(SettingsViewTest, self).setUp(path)
        self.login()

    @skip
    def testGetTab(self):
        view = SettingsView()
        self.assertIsNone(view.getTab())
        self.assertEqual(view.getTab(), '')

        self.path = reverse('core:settings-view') + '?tab=profile'
        self.get()
        self.assertEqual(view.getTab(), 'profile')

        self.path = reverse('core:settings-view') + '?tab=PASSWORD'
        self.assertEqual(view.getTab(), 'password')

        self.path = reverse('core:settings-view') + '?tab=Account'
        self.assertEqual(view.getTab(), 'account')

    @patch('core.views.SettingsView.getTab')
    def testGetTemplate(self, mockGetTab):
        view = SettingsView()
        mockGetTab.return_value = 'profile'
        self.assertEqual(view.getTemplate(), 'core/settingsProfile.html')

        mockGetTab.return_value = 'password'
        self.assertEqual(view.getTemplate(), 'core/settingsPassword.html')

        mockGetTab.return_value = 'account'
        self.assertEqual(view.getTemplate(), 'core/settingsAccount.html')

    @patch('core.views.SettingsView.getTab')
    def testGetForm(self, mockGetTab):
        view = SettingsView()
        mockGetTab.return_value = 'profile'
        isinstance(view.getForm(self.request), UserSettingsProfileUpdateForm)

        mockGetTab.return_value = 'password'
        isinstance(view.getForm(self.request), UserSettingsPasswordUpdateForm)

        mockGetTab.return_value = 'account'
        self.assertIsNone(view.getForm(self.request))

    @patch('core.views.SettingsView.getTab')
    def testUrlTabNotSetThenRedirectToProfileTab(self, mockGetTab):
        pass

    @patch('core.views.UserSettingsProfileUpdateForm')
    @patch('core.views.SettingsView.getTab')
    def testPostProfileIsUpdated(self, mockGetTab, mockProfileForm):
        mockGetTab.return_value = 'profile'
        formInstance = mockProfileForm.return_value
        formInstance.is_valid.return_value = True
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'genres': ['Category_1', 'Category_2', 'Category_3']
        }
        self.post(data)
        self.assertEqual(formInstance.save.call_count, 1)

    def testPostPasswordIsUpdated(self):
        pass
