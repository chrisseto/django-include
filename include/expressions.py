from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import JSONField
from django.db.models import Expression
from django.db.models.expressions import Func
from django.db.models.sql.constants import LOUTER
from django.db.models.sql.datastructures import Join
from django.utils.six.moves import zip

from include.aggregations import JSONAgg


class JSONBuildArray(Func):
    function = 'JSON_BUILD_ARRAY'

    def __init__(self, *args, **kwargs):
        super(JSONBuildArray, self).__init__(*args, output_field=JSONField(), **kwargs)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, function='JSON_ARRAY', **extra_context)


class IncludeExpressionConstructor(object):

    @property
    def host_model(self):
        return self.field.model

    @property
    def included_model(self):
        return self.field.related_model

    def __init__(self, field, children=None):
        self.field = field
        self.children = children or {}

    def get_joining_columns(self):
        return self.field.get_joining_columns()[0]

    def get_queryset(self):
        qs = self.included_model.objects.all()

        # Django's queries are amazing lazy. Calling get_initial_alias() seems
        # to be the fastest way to populate the internal alias structures so we can avoid any overlap
        # This all needs to happen before anything else, otherwise the aliases will get out of sync
        # and they queries could either break or return the wrong data
        qs.query.get_initial_alias()

        return qs

    def add_where(self, queryset, host_table, included_table):
        queryset.query.add_extra(None, None, self._build_where(queryset, host_table, included_table), None, None, None)

        return queryset

    def build_aggregate(self, queryset, compiler):
        expressions = [f.column for f in self.included_model._meta.concrete_fields]

        expressions.extend(self.children)

        agg = JSONBuildArray(*expressions)

        return agg

    def as_sql(self, compiler):
        qs = self.get_queryset()

        # bump_prefix will effectively place this query's aliases into their own namespace
        # No need to worry about conflicting includes
        qs.query.bump_prefix(compiler.query)

        table = qs.query.get_compiler(connection=compiler.connection).quote_name_unless_alias(qs.query.get_initial_alias())
        host_table = compiler.query.resolve_ref('pk').alias

        # # TODO be able to set limits per thing included
        # if self._include_limit:
        #     qs.query.set_limits(0, self._include_limit)

        agg = self.build_aggregate(qs, compiler)
        self.add_where(qs, host_table, table)

        qs.query.add_annotation(agg, '__fields', is_summary=True)
        sql, params = qs.values_list('__fields').query.sql_with_params()

        return '({})'.format(sql), params

    def _build_where(self, queryset, host_table, included_table):
        host_column, included_column = self.get_joining_columns()

        return ['{table}."{column}" = {host_table}."{host_column}"'.format(
            table=included_table,
            column=included_column,
            host_table=host_table,
            host_column=host_column,
        )]

    def __repr__(self):
        return '<{}({})>'.format(type(self).__name__, self.field.name)


class ManyToOneConstructor(IncludeExpressionConstructor):

    def build_aggregate(self, queryset, compiler):
        agg = super(ManyToOneConstructor, self).build_aggregate(queryset, compiler)

        # Any ordering needs to be plucked from the query set and added into the JSONAgg that we will be build
        # because SQL
        kwargs = {}
        if queryset.ordered:
            kwargs['order_by'] = next(zip(*queryset.query.get_compiler(connection=compiler.connection).get_order_by()))
        queryset.query.clear_ordering(True)

        # many_to_one is a bit of a misnomer, the field we have is the "one" side
        return JSONAgg(agg, **kwargs)


class GenericRelationConstructor(ManyToOneConstructor):

    def get_joining_columns(self):
        column, host_column = self.field.get_joining_columns()[0]

        return host_column, column

    def _build_where(self, queryset, host_table, included_table):
        where = super(GenericRelationConstructor, self)._build_where(queryset, host_table, included_table)

        # Add the additional content type filter for GFKs
        # TODO Use apps.get_model
        where.append('{table}."{content_type}" = {content_type_id}'.format(
            table=included_table,
            content_type=self.included_model._meta.get_field(self.field.content_type_field_name).column,
            content_type_id=ContentType.objects.get_for_model(self.host_model).pk
        ))

        return where


class ManyToManyConstructor(ManyToOneConstructor):

    @property
    def through_model(self):
        return self.field.remote_field.through

    @property
    def from_field(self):
        return self.through_model._meta.get_field(self.field.m2m_field_name()).remote_field

    @property
    def to_field(self):
        return self.through_model._meta.get_field(self.field.m2m_reverse_field_name()).remote_field

    def add_where(self, queryset, host_table, included_table):
        alias = None
        nullable = True
        join = Join(self.through_model._meta.db_table, included_table, None, LOUTER, self.to_field, nullable)

        alias, _ = queryset.query.table_alias(join.table_name, create=True)
        join.table_alias = alias
        queryset.query.alias_map[alias] = join

        where = [
            '{through_table}."{from_column}" = {host_table}."{host_column}"'.format(
                through_table=join.table_alias,
                from_column=self.from_field.field.column,
                host_table=host_table,
                host_column=self.from_field.target_field.column
            )
        ]

        queryset.query.add_extra(None, None, where, None, None, None)

        return queryset


class IncludeExpression(Expression):
    # No need to use group bys when using .include
    contains_aggregate = True

    def __init__(self, field, children=None):
        expressions = []
        for cfield, kids in (children or {}).items():
            expressions.append(IncludeExpression(cfield, kids))

        if isinstance(field, GenericRelation):
            self._constructor = GenericRelationConstructor(field, expressions)
        elif getattr(field, 'many_to_many', False):
            self._constructor = ManyToManyConstructor(field, expressions)
        elif getattr(field, 'multiple', False):
            self._constructor = ManyToOneConstructor(field, expressions)
        else:
            self._constructor = IncludeExpressionConstructor(field, expressions)

        super(IncludeExpression, self).__init__(output_field=JSONField())

    def as_sql(self, compiler, connection, template=None):
        return self._constructor.as_sql(compiler)
