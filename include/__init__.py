from django.apps import AppConfig

from include.query import IncludeQuerySet
from include.manager import IncludeManager

__version__ = '0.2.4'
__all__ = ('IncludeManager', 'IncludeQuerySet', )

default_app_config = 'include.IncludeConfig'


class IncludeConfig(AppConfig):
    name = 'include'
