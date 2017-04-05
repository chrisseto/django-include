import factory
from factory.django import DjangoModelFactory

from tests.models import Cat, Alias, Archetype


class AliasFactory(DjangoModelFactory):
    name = factory.Faker('md5')

    class Meta:
        model = Alias


class ArchetypeFactory(DjangoModelFactory):
    color = factory.Faker('safe_color_name')
    num_toes = factory.Faker('pyint')

    class Meta:
        model = Archetype


class CatFactory(DjangoModelFactory):
    name = factory.Faker('name')
    archetype = factory.SubFactory(ArchetypeFactory)

    class Meta:
        model = Cat
