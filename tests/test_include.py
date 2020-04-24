import pytest

from django.db.models import Count
try:
    from django.db.models import OuterRef
    from django.db.models import Subquery
except ImportError:  # Django < 1.11
    HAS_SUBQUERIES = False
else:
    HAS_SUBQUERIES = True

from tests import models
from tests import factories


@pytest.mark.django_db
class TestQuerySet:

    def test_empty(self):
        for _ in range(10):
            factories.CatFactory()
        assert len(models.Cat.objects.include().all()) == 10
        assert models.Cat.objects.include().all().count() == 10

    def test_none(self, django_assert_num_queries):
        archetype = factories.ArchetypeFactory(color='Calico', num_toes=6)
        factories.CatFactory(archetype=archetype)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('archetype'):
                assert cat.archetype == archetype
                assert cat.archetype.num_toes == 6
                assert cat.archetype.color == 'Calico'

        with django_assert_num_queries(2):
            for cat in models.Cat.objects.include(None):
                assert cat.archetype == archetype
                assert cat.archetype.num_toes == 6
                assert cat.archetype.color == 'Calico'

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include(None).include('archetype'):
                assert cat.archetype == archetype
                assert cat.archetype.num_toes == 6
                assert cat.archetype.color == 'Calico'

        with django_assert_num_queries(2):
            for cat in models.Cat.objects.include('archetype').include(None):
                assert cat.archetype == archetype
                assert cat.archetype.num_toes == 6
                assert cat.archetype.color == 'Calico'

    def test_none_with_annotate(self):
        for _ in range(2):
            parent = factories.CatFactory()
            for _ in range(2):
                factories.CatFactory(parent=parent)

        for cat in models.Cat.objects.include('children').annotate(num_children=Count('children')).include(None):
            assert cat.num_children == len(cat.children.all())

    @pytest.mark.skipif(not HAS_SUBQUERIES, reason='Subqueries not supported on older Django versions')
    def test_values(self):
        qs = models.Cat.objects.include('archetype')
        list(qs.filter(id__in=Subquery(qs.filter(id=OuterRef('pk')).values('pk'))))

    def test_annotate(self, django_assert_num_queries):
        for _ in range(3):
            parent = factories.CatFactory()
            for _ in range(10):
                factories.CatFactory(parent=parent)
        with django_assert_num_queries(1):
            for cat in models.Cat.objects.include('children').annotate(num_childern=Count('children')):
                assert cat.num_childern == len(cat.children.all())


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
                assert cat.parent_id == cat.parent.id
                assert cat.archetype_id == cat.archetype.id
                assert cat.parent.archetype_id == cat.parent.archetype.id


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


@pytest.mark.django_db
class TestManyToMany:

    def test_include(self, django_assert_num_queries):
        cat1 = factories.CatFactory()
        siblings = factories.CatFactory.create_batch(5)
        cat1.siblings.add(*siblings)

        with django_assert_num_queries(1):
            cat = models.Cat.objects.filter(id=cat1.id).include('siblings').first()
            for sib in cat.siblings.all():
                assert sib in siblings
            assert len(cat.siblings.all()) == 5

    def test_filter(self, django_assert_num_queries):
        cat1 = factories.CatFactory()
        siblings = factories.CatFactory.create_batch(3, name='Henry')
        siblings += factories.CatFactory.create_batch(2, name='George')
        cat1.siblings.add(*siblings)

        # If .filter is called, our cache is invalid and must be ignored
        with django_assert_num_queries(4):
            cat = models.Cat.objects.filter(id=cat1.id).include('siblings').first()
            for sib in cat.siblings.filter():
                assert sib in siblings

            for sib in cat.siblings.filter(name='Henry'):
                assert sib.name == 'Henry'
                assert sib in siblings[:3]

            for sib in cat.siblings.filter(name='George'):
                assert sib.name == 'George'
                assert sib in siblings[3:]

            assert len(cat.siblings.all()) == 5

    def test_include_many(self, django_assert_num_queries):
        cats = factories.CatFactory.create_batch(10)
        sibs = []
        for cat in cats:
            sibs.append(factories.CatFactory.create_batch(5))
            cat.siblings.add(*sibs[-1])

        with django_assert_num_queries(1):
            for cat, siblings in zip(models.Cat.objects.filter(id__in=[x.id for x in cats]).include('siblings'), sibs):
                for included, created in zip(cat.siblings.all(), siblings):
                    assert included == created
                assert len(cat.siblings.all()) == 5

    def test_nested(self, django_assert_num_queries):
        cat1 = factories.CatFactory()
        cat1.siblings.add(*factories.CatFactory.create_batch(3))
        for sib in cat1.siblings.all():
            sib.siblings.add(*factories.CatFactory.create_batch(2))

        with django_assert_num_queries(1):
            cat1_i = models.Cat.objects.include('siblings__siblings').filter(id=cat1.id).first()
            assert len(cat1_i.siblings.all()) == 3
            for sib in cat1_i.siblings.all():
                assert len(sib.siblings.all()) == 2

    def test_hidden_fields(self):
        with pytest.raises(ValueError) as e:
            models.Cat.objects.include('Cat_siblings+')
        assert e.value.args == (
            'Hidden field "{!r}" has no descriptor '
            'and therefore cannot be included'.format(models.Cat._meta.get_field('Cat_siblings+')),
        )


@pytest.mark.django_db
class TestOneToOne:

    def test_include(self, django_assert_num_queries):
        cats = factories.CatFactory.create_batch(5)

        for cat in cats:
            factories.CatFactory(emergency_contact=cat)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.filter(emergency_contact__isnull=False).include('emergency_contact__emergency_contact_for'):
                assert cat.emergency_contact is not None
                assert cat.emergency_contact.emergency_contact_for.id == cat.id
                assert isinstance(cat.emergency_contact, models.Cat)
                assert cat.emergency_contact.id != cat.id

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.filter(emergency_contact__isnull=True).include('emergency_contact'):
                assert cat.emergency_contact is None

    def test_reverse(self, django_assert_num_queries):
        cats = factories.CatFactory.create_batch(5)

        for cat in cats:
            factories.CatFactory(emergency_contact=cat)

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.filter(emergency_contact__isnull=False).include('emergency_contact_for'):
                with pytest.raises(models.Cat.DoesNotExist):
                    assert cat.emergency_contact_for is None

        with django_assert_num_queries(1):
            for cat in models.Cat.objects.filter(emergency_contact__isnull=True).include('emergency_contact_for__emergency_contact'):
                assert cat.emergency_contact_for is not None
                assert isinstance(cat.emergency_contact_for, models.Cat)
                assert cat.emergency_contact_for.emergency_contact.id == cat.id
                assert cat.emergency_contact_for != cat.id


@pytest.mark.skip
class TestForeignKey:
    pass


@pytest.mark.django_db
class TestGenericForeignKey:

    def test_reverse_gfk(self, django_assert_num_queries):
        cat = factories.CatFactory()

        for _ in range(7):
            factories.AliasFactory(describes=cat)

        with django_assert_num_queries(1):
            ket = models.Cat.objects.include('aliases').get(pk=cat.id)
            assert len(ket.aliases.all()) == 7

    def test_chaining(self, django_assert_num_queries):
        cat = factories.CatFactory()

        qs1 = cat.organizations.all().filter(members__active=False).include('members')
        qs2 = cat.organizations.all().include('members').filter(members__active=False)

        assert str(qs1.query) == str(qs2.query)


@pytest.mark.django_db
class TestGeneratedAccessors:

    def test_m2m_nested(self, django_assert_num_queries):
        for _ in range(5):
            post = factories.PostFactory()
            post.authors.set(factories.AuthorFactory.create_batch(5))

        with django_assert_num_queries(1):
            for post in models.Post.objects.include('authors__post_set'):
                for author in post.authors.all():
                    assert len(author.post_set.all()) == 1

    def test_m2m(self, django_assert_num_queries):
        for _ in range(5):
            post = factories.PostFactory()
            post.authors.set(factories.AuthorFactory.create_batch(5))
            factories.CommentFactory(author=factories.AuthorFactory(), post=post)

        with django_assert_num_queries(1):
            for post in models.Post.objects.include('authors'):
                assert len(post.authors.all()) == 5

        with django_assert_num_queries(1):
            for post in models.Post.objects.include('comment_set__author__post_set'):
                for comment in post.comment_set.all():
                    assert len(comment.author.post_set.all()) == 0

        with django_assert_num_queries(1):
            for post in models.Post.objects.include('authors__comment_set'):
                for author in post.authors.all():
                    assert len(author.comment_set.all()) == 0
