import itertools
import logging
import time
from threading import Thread, RLock

import config
from app import db

_cached_region_key = 'regions'


class CacheEntry:
    def __init__(self, key, value, ttl):
        self.key = key
        self.value = value
        self.expires_at = time.time() + float(ttl)
        self._expired = False

    def expired(self):
        if self._expired is False:
            return self.expires_at < time.time()
        else:
            return self._expired


class CacheList:
    conf_ttl = int(config.load_config(config.get_config_path(), {'cache.expired': 10})['cache.expired'])
    conf_ttl *= 60  # in minutes

    def __init__(self):
        self.entries = []
        self.lock = RLock()

    def add_entry(self, key, value, ttl=conf_ttl):
        with self.lock:
            self.entries.append(CacheEntry(key, value, ttl))

    def read_entries(self):
        with self.lock:
            self.entries = list(itertools.dropwhile(lambda x: x.expired(), self.entries))
            return self.entries


def _read_entries(name, slp, cl):
    while True:
        logging.debug("{}: {}".format(name, ",".join(map(lambda x: x.key, cl.read_entries()))))
        time.sleep(slp)


def _cache_regions_details():
    query_stmt = """
        SELECT region_name, r.region_id, city_name, c.city_id
        FROM regions r JOIN cities c ON r.region_id = c.region_id
        ORDER BY region_name, city_name;
    """

    regions_details = dict()
    db_instance = db.PostgresDB()
    for rc in db_instance.query(query_stmt):
        regions_details[rc[0]] = region = regions_details.get(rc[0], {})
        if len(region) == 0:
            region['region_id'] = rc[1]
            region['region_name'] = rc[0]
            region['cities'] = []
        region['cities'].append(dict(city_id=rc[3], city_name=rc[2]))

    cache_list.add_entry(_cached_region_key, regions_details)
    return regions_details


def get_regions_from_cache():
    for cache_item in cache_list.read_entries():
        if cache_item.key == _cached_region_key:
            logging.debug('Cache hit for %s', _cached_region_key)
            return cache_item.value

    logging.debug("Cache miss for '%s'", _cached_region_key)
    return _cache_regions_details()


cache_list = CacheList()
thrd = Thread(None, _read_entries, args=('cache_reader', CacheList.conf_ttl, cache_list))
thrd.start()
