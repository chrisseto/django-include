from django.apps import AppConfig

from include.query import IncludeQuerySet
from include.manager import IncludeManager
# VERSION = (3, 1, 3)
# __version__ = '.'.join(map(str, VERSION if VERSION[-1] else VERSION[:2]))


default_app_config = 'include.IncludeConfig'
__all__ = ('IncludeManager', 'IncludeQuerySet', )


class IncludeConfig(AppConfig):
    name = 'include'
