from urllib.parse import urlencode

from django import template
from django.core.paginator import Page
from django.urls import reverse
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


@register.simple_tag
def paginationComponent(request, objects: Page):
    if not objects.has_other_pages():
        return mark_safe('<span></span>')

    parameters = request.GET.copy()
    currentParameters = parameters.copy()
    parameters.pop('page', None)
    query = urlencode(parameters)

    def createUrlWithPage(number):
        return f"?page={number}&{query}" if query else f"?page={number}"

    def hasParametersChanged():
        return currentParameters.get('tab') != request.GET.get('tab') or currentParameters.get(
            'query') != request.GET.get('query')

    if hasParametersChanged():
        pageNumber = 1
    else:
        pageNumber = int(request.GET.get('page') or 1)

    if objects.has_previous():
        previousPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.previous_page_number())}" tabindex="-1">Previous</a>
        </li>
        '''
        firstPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(1)}" tabindex="-1">First</a>
        </li>
        '''
    else:
        previousPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Previous</a>
        </li>
        '''
        firstPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">First</a>
        </li>
        '''

    # Next and last page links
    if objects.has_next():
        nextPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.next_page_number())}" tabindex="-1">Next</a>
        </li>
        '''
        lastPageLink = f'''
        <li class="page-item">
            <a class="page-link" href="{createUrlWithPage(objects.paginator.num_pages)}" tabindex="-1">Last</a>
        </li>
        '''
    else:
        nextPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Next</a>
        </li>
        '''
        lastPageLink = f'''
        <li class="page-item disabled">
            <a class="page-link" href="#" tabindex="-1">Last</a>
        </li>
        '''

    # Page number links
    pageNumberLinks = ''
    EITHER_SIDE_PAGE_LIMIT = 20
    pageRange = objects.paginator.page_range
    if pageRange.stop > EITHER_SIDE_PAGE_LIMIT:
        currentPage = pageNumber
        minRange = currentPage - EITHER_SIDE_PAGE_LIMIT // 2
        maxRange = currentPage + EITHER_SIDE_PAGE_LIMIT // 2

        if minRange <= 0:
            minRange = 1
        if maxRange > pageRange.stop:
            maxRange = pageRange.stop

        pageRange = range(minRange, maxRange)

    for pageNumber in pageRange:
        if objects.number == pageNumber:
            pageNumberLinks += f'''
                <li class="page-item active"><a class="page-link" href="#">{pageNumber}</a></li>
            '''
        else:
            pageNumberLinks += f'''
                <li class="page-item"><a class="page-link" href="{createUrlWithPage(pageNumber)}">{pageNumber}</a></li>
            '''

    itemContent = f'''
    <div class="row">
        <div class="col-md-12" style="width: 1100px;">
            <nav aria-label="Page navigation example">
                <ul class="pagination justify-content-center">
                    {firstPageLink}
                    {previousPageLink}
                    {pageNumberLinks}
                    {nextPageLink}
                    {lastPageLink}
                </ul>
            </nav>
        </div>
    </div>
    '''
    return mark_safe(itemContent)
