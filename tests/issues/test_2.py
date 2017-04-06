import pytest

from tests import models
from tests import factories


@pytest.mark.django_db
class TestIssue2:
    """Test(s) for [Related fields that are included cannot be filtered](https://github.com/chrisseto/django-include/issues/2)

    When including a relationship (contributor__user), .all() returns the expected value but .filter(...) does not.
    """

    def test_related_filter_requeries(self, django_assert_num_queries):
        a1, a2 = factories.ArchetypeFactory(), factories.ArchetypeFactory()

        for _ in range(10):
            parent = factories.CatFactory()

            for i in range(10):
                factories.CatFactory(archetype=a1 if i % 2 == 0 else a2, parent=parent)

            for parent in models.Cat.objects.include('children').filter(parent__isnull=True):
                with django_assert_num_queries(0):
                    assert len(parent.children.all()) == 10

                with django_assert_num_queries(1):
                    assert len(parent.children.filter(archetype=a1)) == 5

                with django_assert_num_queries(1):
                    assert len(parent.children.all().filter(archetype=a2)) == 5
