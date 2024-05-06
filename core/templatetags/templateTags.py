from django import template
from django.urls import reverse

from bookrec.operations.navigationOperations import linkItem, Icon

register = template.Library()


@register.simple_tag
def navigationPanel(request):
    links = [
        linkItem('Home', reverse('core:index-view'), None),
    ]

    if request.user.is_authenticated:
        links.extend(
            [
                linkItem('Account', '', None, [
                    linkItem('Shelf', reverse('core:user-shelf-view'), Icon('', 'fas fa-book', '15')),
                    linkItem('Settings', reverse('core:settings-view'), Icon('', 'fa fa-gear', '15')),
                    None,
                    linkItem('Logout', reverse('core:logout-view'), Icon('', 'fas fa-sign-out-alt', '15')),
                ]),
            ]
        )
    else:
        links.append(
            linkItem('Login / Register', '', None, [
                linkItem('Register', reverse('core:register-view'), Icon('', 'fas fa-user-circle', '20')),
                None,
                linkItem('Login', reverse('core:login-view'), Icon('', 'fas fa-sign-in-alt', '20')),
            ]),
        )
    return links
