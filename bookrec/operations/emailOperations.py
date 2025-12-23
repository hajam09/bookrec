import json

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode


def sendEmailToActivateAccount(request, user: User):
    emailSubject = 'Activate your Bookrec Account'
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('core:activate-account', kwargs={'base64': uid, 'token': prtg.make_token(user)})
    currentSiteDomain = get_current_site(request).domain

    message = f'''
        Hi {fullName},
        \n
        Welcome to Bookrec, thank you for your joining our service.
        We have created an account for you to unlock more features.
        \n
        please click this link below to verify your account
        http://{currentSiteDomain}{url}
        \n
        Thanks,
        The Bookrec Team
    '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailForAccountDeletionCode(user: User):
    emailSubject = 'Bookrec account deletion code'
    fullName = user.get_full_name()

    passwordResetTokenGenerator = PasswordResetTokenGenerator()
    token = passwordResetTokenGenerator.make_token(user)

    message = f'''
                Hi {fullName},
                \n
                Below is the code to delete your account permanently.
                Copy the code and paste it on our website.
                \n
                Your code is: {token}
                \n
                Thanks,
                The Bookrec Team
            '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailToResetPassword(request, user: User):
    emailSubject = 'Request to reset Bookrec Password'
    fullName = user.get_full_name()
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    prtg = PasswordResetTokenGenerator()
    url = reverse('core:set-password-view', kwargs={'base64': uid, 'token': prtg.make_token(user)})
    currentSiteDomain = get_current_site(request).domain

    message = f'''
            Hi {fullName},
            \n
            You have recently request to reset your account password.
            Please click this link below to reset your account password.
            \n
            http://{currentSiteDomain}{url}
            \n
            Thanks,
            The TaskMaster Team
        '''

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.send()
    return


def sendEmailForUserDataAsJson(user: User, userData: dict):
    emailSubject = 'Bookrec User Data'
    message = 'Attached is your user data export file.'

    emailMessage = EmailMessage(emailSubject, message, settings.EMAIL_HOST_USER, [user.email])
    emailMessage.attach(f'Bookrec_user_data_{timezone.now()}.json', json.dumps(userData, indent=4), 'application/json')
    emailMessage.send()
    return
