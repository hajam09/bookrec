from django import template
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

register = template.Library()


class Icon:

    def __init__(self, name, clazz, size):
        self.name = name
        self.clazz = clazz
        self.size = size


def getIcon(icon):
    if icon is None:
        return None
    return f'<i style="font-size:{icon.size}px" class="{icon.clazz}">{icon.name}</i>'


def linkItem(name, url, icon=None, subLinks=None):
    return {'name': name, 'url': url, 'icon': getIcon(icon), 'subLinks': subLinks}


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
                    linkItem('Settings', reverse('core:settings-view') + '?' + urlencode({'tab': 'profile'}),
                             Icon('', 'fa fa-gear', '15')),
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


class SettingsTab:
    def __init__(self, internalKey, isActive, tab):
        self.internalKey = internalKey
        self.isActive = isActive
        self.tab = tab

    def getButtonColour(self):
        return 'btn btn-primary' if self.isActive else 'btn btn-light'

    def getUrl(self):
        return reverse('core:settings-view') + '?' + urlencode({'tab': self.tab})

    def renderTabComponent(self):
        itemContent = f'''
        <span>
            <a class='{self.getButtonColour()}' href='{self.getUrl()}' role='button'>{self.internalKey}</a>&nbsp;
        </span>
        '''
        return itemContent


@register.simple_tag
def settingsBaseTabs(request):
    currentTab = request.GET.get('tab')
    tabs = [
        SettingsTab('My profile', currentTab == 'profile', 'profile'),
        SettingsTab('Update password', currentTab == 'password', 'password'),
        SettingsTab('Account', currentTab == 'account', 'account'),
        SettingsTab('Activity', currentTab == 'activity', 'activity'),
    ]

    itemContent = f'''
    <div class='container'>
        <br>
            <div class='row justify-content-md-center'>
                <div class='btn-group' role='group' aria-label='Shelf'>
                    {''.join([tab.renderTabComponent() for tab in tabs])}</div>
                </div>
            </div>
        <br>
        <br>
    </div>
    '''
    return mark_safe(itemContent)
