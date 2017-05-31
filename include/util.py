from django.utils import dateparse

try:
    import ujson as json
except ImportError:
    import json  # noqa


try:
    import ciso8601
except ImportError:
    ciso8601 = None

try:
    STR_TYPE = basestring
except NameError:
    STR_TYPE = str


def parse_datetime(s):
    if not s:
        return s

    if ciso8601:
        return ciso8601.parse_datetime(s)

    return dateparse.parse_datetime(s)
