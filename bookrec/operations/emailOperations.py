import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def sendEmailToActivateAccount(request, user: User):
    currentSite = get_current_site(request)
    emailSubject = 'Activate your Bookrec Account'

    fullName = user.get_full_name()
    base64 = urlsafe_base64_encode(force_bytes(user.pk))

    passwordResetTokenGenerator = PasswordResetTokenGenerator()
    token = passwordResetTokenGenerator.make_token(user)

    message = f'''
        Hi {fullName},
        \n
        Welcome to Bookrec, thank you for your joining our service.
        We have created an account for you to unlock more features.
        \n
        please click this link below to verify your account
        http://{currentSite.domain + reverse('core:account-activation-request', kwargs={'base64': base64, 'token': token})}
        \n
        Thanks,
        The Bookrec Team
    '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailForAccountDeletionCode(request, user: User):
    emailSubject = 'Bookrec account deletion code'
    fullName = user.get_full_name()

    message = f'''
                Hi {fullName},
                \n
                Below is the code to delete your account permanently.
                Copy the code and paste it on our website.
                \n
                Your code is: {request.session.session_key}
                \n
                Thanks,
                The Bookrec Team
            '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToChangePassword(request, user: User):
    currentSite = get_current_site(request)
    emailSubject = 'Request to change Bookrec Password'

    fullName = user.get_full_name()
    base64 = urlsafe_base64_encode(force_bytes(user.pk))

    passwordResetTokenGenerator = PasswordResetTokenGenerator()
    token = passwordResetTokenGenerator.make_token(user)

    message = f'''
            Hi {fullName},
            \n
            You have recently request to change your account password.
            Please click this link below to change your account password.
            \n
            http://{currentSite.domain + reverse('core:password-update-request', kwargs={'base64': base64, 'token': token})}
            \n
            Thanks,
            The Bookrec Team
        '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailForUserDataAsJson(user: User, userData: dict):
    emailSubject = 'Bookrec User Data'
    message = 'Attached is your user data export file.'

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.attach('Bookrec_user_data.json', json.dumps(userData, indent=4), 'application/json')
    emailMessage.send()
    return


def sendEmailForUserDataAsXlsx(user: User, file):
    emailSubject = 'Bookrec User Data'
    message = 'Attached is your user data export file.'

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.attach_file(file)
    emailMessage.send()
    return
