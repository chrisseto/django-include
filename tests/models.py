from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models

from include import IncludeManager


class Alias(models.Model):
    content_type = models.ForeignKey(ContentType, null=True, blank=True)
    describes = GenericForeignKey()
    name = models.CharField(max_length=32)
    object_id = models.PositiveIntegerField(null=True, blank=True)

    class Meta:
        ordering = ('name', )


class Archetype(models.Model):
    aliases = GenericRelation(Alias)
    color = models.CharField(max_length=75)
    num_toes = models.PositiveIntegerField(default=5)

    objects = IncludeManager()


class Cat(models.Model):
    aliases = GenericRelation(Alias)
    archetype = models.ForeignKey(Archetype)
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('Cat', null=True, related_name='children')
    siblings = models.ManyToManyField('Cat')

    objects = IncludeManager()
