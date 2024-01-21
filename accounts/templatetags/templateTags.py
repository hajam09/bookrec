from django import template
from django.urls import reverse

from bookrec.operations.navigationOperations import linkItem, Icon

register = template.Library()


@register.simple_tag
def navigationPanel(request):
    links = [
        linkItem('Home', reverse('core:index-view'), None),
        linkItem('Shelf', reverse('core:user-shelf-view'), None),
    ]

    # if request.user.is_authenticated:
    #     links.extend(
    #         [
    #             linkItem('Create a Quiz', reverse('core:quiz-create-view'), None),
    #             linkItem('Account', '', None, [
    #                 linkItem('History', reverse('core:attempted-quizzes-view'), Icon('', 'fas fa-book-open', '15')),
    #                 linkItem('My Quizzes', reverse('core:user-created-quizzes-view'),
    #                          Icon('', 'fas fa-question', '15')),
    #                 None,
    #                 linkItem('Logout', reverse('accounts:logout'), Icon('', 'fas fa-sign-out-alt', '15')),
    #             ]),
    #         ]
    #     )
    # else:
    #     links.append(
    #         linkItem('Login / Register', '', None, [
    #             linkItem('Register', reverse('accounts:register'), Icon('', 'fas fa-user-circle', '20')),
    #             None,
    #             linkItem('Login', reverse('accounts:login'), Icon('', 'fas fa-sign-in-alt', '20')),
    #         ]),
    #     )
    return links
