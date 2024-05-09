from django.core.cache import cache
from django.test import TestCase


class RedisCacheTest(TestCase):

    def testCache(self):
        cache.set('key-sample', 'value-sample', timeout=3600)
        cached_value = cache.get('key-sample')
        self.assertEqual(cached_value, 'value-sample')
