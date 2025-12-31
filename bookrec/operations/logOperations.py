from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from core.models import UserActivityLog

CACHE_KEY = 'UserActivityLog'
CACHE_BATCH_SIZE = 20


def log(request, action, data=None):
    logs = cache.get(CACHE_KEY, default=[])

    logs.append(
        UserActivityLog(
            user=request.user if request.user.is_authenticated else None,
            action=action,
            ipAddress=request.META.get('REMOTE_ADDR'),
            userAgent=request.META.get('HTTP_USER_AGENT'),
            timeStamp=timezone.now(),
            data=data or {}
        )
    )

    if len(logs) >= CACHE_BATCH_SIZE:
        with transaction.atomic():
            UserActivityLog.objects.bulk_create(logs)
            logs = []

    cache.set(CACHE_KEY, logs)
