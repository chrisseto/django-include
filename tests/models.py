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
    siblings = models.ManyToManyField('Cat', related_name='related_to')
    emergency_contact = models.OneToOneField('Cat', null=True, related_name='emergency_contact_for')
    organizations = models.ManyToManyField('Organization', through='Membership')

    objects = IncludeManager()


class Organization(models.Model):
    title = models.CharField(max_length=75)
    disliked = models.BooleanField(default=True)

    objects = IncludeManager()


class Membership(models.Model):
    active = models.BooleanField(default=True)
    joined = models.DateTimeField(auto_now_add=True)

    organization = models.ForeignKey(Organization, related_name='members')
    member = models.ForeignKey(Cat, related_name='memberships')

    objects = IncludeManager()
