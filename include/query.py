import copy
from collections import OrderedDict

from django.utils.six.moves import zip
from django.db import models
from django.db.models.query import ModelIterable
from django.db.models.fields.reverse_related import ForeignObjectRel

from include import util
from include.expressions import IncludeExpression


class IncludeModelIterable(ModelIterable):

    # ModelIterables are responsible for hydrating the rows sent back from the DB
    # Hook in here to pluck off the extra json aggregations that were tacked on

    @classmethod
    def parse_nested(cls, instance, field, nested, datas):
        if field.many_to_one or field.one_to_one:
            datas = (datas, )
        ps = []

        # Fun caveat of throwing everything into JSON, it doesn't support datetimes. Everything gets sent back as iso8601 strings
        # Make a list of all fields that should be datetimes and parse them ahead of time
        dts = [i for i, f in enumerate(field.related_model._meta.concrete_fields) if isinstance(f, models.DateTimeField)]

        for data in datas or []:
            if data is None:
                ps.append(None)
                continue

            data, nested_data = data[:-len(nested) or None], data[-len(nested):]

            for i in dts:
                data[i] = util.parse_datetime(data[i])

            # from_db expects the final argument to be a tuple of fields in the order of concrete_fields
            parsed = field.related_model.from_db(instance._state.db, None, data)

            for (f, n), d in zip(nested.items(), nested_data):
                cls.parse_nested(parsed, f, n, d)

            if field.remote_field.concrete:
                setattr(parsed, field.remote_field.get_cache_name(), instance)

            ps.append(parsed)

        if (field.many_to_one or field.one_to_one) and ps:
            return setattr(instance, field.get_cache_name(), ps[0])

        if not hasattr(instance, '_prefetched_objects_cache'):
            instance._prefetched_objects_cache = {}

        if hasattr(field, 'get_accessor_name'):
            accessor_name = field.get_accessor_name()
        else:
            accessor_name = field.name

        # get_queryset() sets a bunch of attributes for us and will respect any custom managers
        instance._prefetched_objects_cache[field.name] = getattr(instance, accessor_name).get_queryset()
        instance._prefetched_objects_cache[field.name]._result_cache = ps
        instance._prefetched_objects_cache[field.name]._prefetch_done = True

    @classmethod
    def parse_includes(cls, instance, fields):
        for field, nested in fields.items():
            data = getattr(instance, '__' + field.name)
            delattr(instance, '__' + field.name)
            # SQLite doesn't auto parse JSON
            if isinstance(data, util.STR_TYPE):
                data = util.json.loads(data)
            cls.parse_nested(instance, field, nested, data)

    def __iter__(self):
        for instance in super(IncludeModelIterable, self).__iter__():
            self.parse_includes(instance, self.queryset._includes)

            yield instance


class IncludeQuerySet(models.QuerySet):

    def __init__(self, *args, **kwargs):
        super(IncludeQuerySet, self).__init__(*args, **kwargs)
        self._include_limit = None
        # Needs to be ordered, otherwise there is no way to tell which elements are the child includes
        # {field: {child_field: {}}}
        self._includes = OrderedDict()
        # Not sure why Django didn't make this a class level variable w/e
        self._iterable_class = IncludeModelIterable

    def include(self, *fields, **kwargs):
        """
        Return a new QuerySet instance that will include related objects.

        If fields are specified, they must be non-hidden relationships.

        If select_related(None) is called, clear the list.
        """
        clone = self._clone()

        # Preserve the stickiness of related querysets
        # NOTE: by default _clone will clear this attribute
        # .include does not modify the actual query, so we
        # should not clear `filter_is_sticky`
        if self.query.filter_is_sticky:
            clone.query.filter_is_sticky = True

        clone._include_limit = kwargs.pop('limit_includes', None)
        assert not kwargs, '"limit_includes" is the only accepted kwargs. Eat your heart out 2.7'

        # Copy the behavior of .select_related(None)
        if fields == (None, ):
            for field in clone._includes.keys():
                clone.query._annotations.pop('__{}'.format(field.name), None)
            clone._includes.clear()
            return clone

        # Parse everything the way django handles joins/select related
        # Including multiple child fields ie .include(field1__field2, field1__field3)
        # turns into {field1: {field2: {}, field3: {}}
        for name in fields:
            ctx, model = clone._includes, clone.model
            for spl in name.split('__'):
                field = model._meta.get_field(spl)
                if isinstance(field, ForeignObjectRel) and field.is_hidden():
                    raise ValueError('Hidden field "{!r}" has no descriptor and therefore cannot be included'.format(field))
                model = field.related_model
                ctx = ctx.setdefault(field, OrderedDict())

        for field in clone._includes.keys():
            clone._include(field)

        return clone

    def _clone(self):
        clone = super(IncludeQuerySet, self)._clone()
        clone._includes = copy.deepcopy(self._includes)
        return clone

    def _include(self, field):
        self.query.get_initial_alias()
        self.query.add_annotation(IncludeExpression(field, self._includes[field]), '__{}'.format(field.name), is_summary=False)
