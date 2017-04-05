import pytest

from django.db.models.aggregates import Count

from tests import models
from tests import factories


@pytest.mark.django_db
class TestQuerySet:

    def test_empty(self):
        for _ in range(10):
            factories.CatFactory()
        assert len(models.Cat.objects.include().all()) == 10
        assert models.Cat.objects.include().all().count() == 10

    # def test_annotate(self, django_assert_num_queries):
    #     for _ in range(3):
    #         parent = factories.CatFactory()
    #         for _ in range(10):
    #             factories.CatFactory(parent=parent)
    #     qs = models.Cat.objects.include('children').annotate(num_childern=Count('children'))
    #     import ipdb; ipdb.set_trace()
    #     with django_assert_num_queries(1):
    #         for cat in models.Cat.objects.include('children').annotate(num_childern=Count('children')):
    #             assert cat.num_childern == len(cat.children.all())


@pytest.mark.django_db
class TestManyToOne:

    def test_many_to_one(self):
        for _ in range(10):
            factories.CatFactory()
        assert len(models.Cat.objects.include('archetype').all()) == 10

    def test_one_query(self, django_assert_num_queries):
        archetype = factories.ArchetypeFactory(color='Someone is looking for you', num_toes=6)

        for _ in range(10):
            factories.CatFactory(archetype=archetype)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('archetype'):
                assert cat.archetype is not None
                assert cat.archetype is not archetype
                assert cat.archetype.pk == archetype.pk
                assert cat.archetype.num_toes == 6
                assert cat.archetype.color == 'Someone is looking for you'

    def test_nullable(self, django_assert_num_queries):
        for _ in range(10):
            factories.CatFactory()

        assert len(models.Cat.objects.include('parent').all()) == 10

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('parent'):
                assert cat.parent is None

    def test_mixed(self, django_assert_num_queries):
        for i in range(10):
            if i % 2 == 0:
                parent = None
            else:
                parent = factories.CatFactory(archetype=factories.ArchetypeFactory(num_toes=3))

            factories.CatFactory(parent=parent, archetype=factories.ArchetypeFactory(num_toes=5))

        with django_assert_num_queries(1):
            for i, cat in enumerate(models.Cat.objects.include('parent').filter(archetype__num_toes=5)):
                if i % 2 == 0:
                    assert cat.parent is None
                else:
                    assert cat.parent is not None

        with django_assert_num_queries(1):
            for i, cat in enumerate(models.Cat.objects.filter(archetype__num_toes=5).include('parent')):
                if i % 2 == 0:
                    assert cat.parent is None
                else:
                    assert cat.parent is not None

    def test_multiple_nested(self, django_assert_num_queries):
        for i in range(10):
            factories.CatFactory(
                archetype=factories.ArchetypeFactory(num_toes=5),
                parent=factories.CatFactory(archetype=factories.ArchetypeFactory(num_toes=3))
            )

        with django_assert_num_queries(1):
            for i, cat in enumerate(models.Cat.objects.include('archetype', 'parent__archetype').filter(archetype__num_toes=5)):
                assert cat.archetype.num_toes == 5
                assert cat.parent.archetype.num_toes == 3


@pytest.mark.django_db
class TestOneToMany:

    def test_many_to_one(self, django_assert_num_queries):
        for _ in range(10):
            parent = factories.CatFactory()
            for _ in range(2):
                factories.CatFactory(parent=parent)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('children').filter(parent__isnull=True):
                assert len(cat.children.all()) == 2

                for child in cat.children.all():
                    assert child.parent == cat

        assert len(models.Cat.objects.filter(parent__isnull=True)) == 10

    def test_nested(self, django_assert_num_queries):
        for _ in range(10):
            parent = factories.CatFactory()
            for _ in range(10):
                child = factories.CatFactory(parent=parent)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('children__archetype').filter(parent__isnull=True):
                assert len(cat.children.all()) == 10

                for child in cat.children.all():
                    assert child.archetype is not None
        assert models.Cat.objects.include('children__archetype').filter(parent__isnull=True).count() == 10

    def test_nested_same(self, django_assert_num_queries):
        for _ in range(10):
            parent = factories.CatFactory()
            for _ in range(10):
                child = factories.CatFactory(parent=parent)
                for _ in range(10):
                    factories.CatFactory(parent=child)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('children__children').filter(parent__isnull=True):
                assert len(cat.children.all()) == 10

                for child in cat.children.all():
                    assert child.parent == cat
                    assert len(child.children.all()) == 10

                    for grandchild in child.children.all():
                        assert grandchild.parent == child
        assert models.Cat.objects.include('children__children').filter(parent__isnull=True).count() == 10


@pytest.mark.skip
class TestManyToMany:
    pass


@pytest.mark.skip
class TestOneToOne:
    pass


@pytest.mark.skip
class TestForeignKey:
    pass


@pytest.mark.skip
class TestGenericForeignKey:
    pass
