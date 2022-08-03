from django.core.exceptions import FieldDoesNotExist
from django.utils import dateparse
from psycopg2 import extras

try:
    import ujson as json

    extras.register_default_json(loads=json.loads)
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


def get_field(model, fieldname):
    try:
        return model._meta.get_field(fieldname)
    except FieldDoesNotExist:
        for field in model._meta.get_fields():
            if not hasattr(field, 'get_accessor_name'):
                continue
            if field.get_accessor_name() == fieldname:
                return field
        raise
