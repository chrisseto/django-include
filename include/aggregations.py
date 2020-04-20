from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.aggregates.mixins import OrderableAggMixin
from django.db.models.aggregates import Aggregate


class JSONAgg(OrderableAggMixin, Aggregate):
    function = 'JSON_AGG'
    allow_distinct = False
    contains_aggregate = False

    @property
    def output_field(self):
        return JSONField()

    def convert_value(self, value, expression, connection):
        if not value:
            return []
        return value

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, function='JSON_GROUP_ARRAY', **extra_context)
