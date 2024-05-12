from unittest.mock import patch

from django.http import QueryDict
from django.urls import reverse

from bookrec.settings import TEST_PASSWORD
from bookrec.tests.BaseTestViews import BaseTestViews
from core.forms import RegistrationForm


class RegistrationViewTest(BaseTestViews):

    def setUp(self, path=reverse('core:register-view')) -> None:
        super(RegistrationViewTest, self).setUp(path)

    def testRegisterGet(self):
        response = self.get()
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/registrationView.html')
        self.assertTrue(isinstance(response.context['form'], RegistrationForm))

    @patch('core.views.RegistrationForm.is_valid')
    @patch('core.views.RegistrationForm.save')
    @patch('bookrec.operations.emailOperations.sendEmailToActivateAccount')
    def testLoginAuthenticateValidForm(self, mockRegistrationFormIsValid, mockRegistrationFormSave,
                                       mockSendEmailToActivateAccount):
        mockRegistrationFormIsValid.return_value = True
        mockRegistrationFormSave.save = self.request.user

        testParams = self.TestParams('user@example.com', TEST_PASSWORD, 'Django', 'Admin', ['Action', 'Adventure'])
        response = self.post(testParams.getData())
        messages = self.getMessages(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(messages))
        mockSendEmailToActivateAccount.assert_called()
        self.assertRedirects(response, '/login/')

        for message in messages:
            self.assertEqual(
                str(message),
                'We\'ve sent you an activation link. Please check your email.'
            )

    class TestParams:
        def __init__(self, email, password, firstName, lastName, genres):
            self.email = email
            self.password = password
            self.firstName = firstName
            self.lastName = lastName
            self.genres = genres

        def getData(self):
            data = {
                'first_name': self.firstName,
                'last_name': self.lastName,
                'email': self.email,
                'password': self.password,

            }
            queryDict = QueryDict('', mutable=True)
            queryDict.update(data)
            return queryDict
