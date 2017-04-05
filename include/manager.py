from django.db.models import Manager

from include.query import IncludeQuerySet


IncludeManager = Manager.from_queryset(IncludeQuerySet)
