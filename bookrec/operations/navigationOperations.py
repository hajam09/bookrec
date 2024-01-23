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
