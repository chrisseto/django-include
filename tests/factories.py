import factory
from factory.django import DjangoModelFactory

from tests.models import Cat, Alias, Archetype, Post, Comment, Author


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


class PostFactory(DjangoModelFactory):
    title = factory.Faker('sentence')

    class Meta:
        model = Post


class AuthorFactory(DjangoModelFactory):
    name = factory.Faker('name')

    class Meta:
        model = Author


class CommentFactory(DjangoModelFactory):
    content = factory.Faker('sentence')

    class Meta:
        model = Comment
