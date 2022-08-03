import json
from django.db.models import JSONField
from django.db.models.fields.json import KeyTransform
from django.contrib.postgres.aggregates.mixins import OrderableAggMixin
from django.db.models.aggregates import Aggregate


class IncludeJSONField(JSONField):

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        # Some backends (SQLite at least) extract non-string values in their
        # SQL datatypes.
        if isinstance(expression, KeyTransform) and not isinstance(value, str):
            return value

        if isinstance(value, list):
            return value

        try:
            return json.loads(value, cls=self.decoder)
        except json.JSONDecodeError:
            return value

class JSONAgg(OrderableAggMixin, Aggregate):
    function = 'JSON_AGG'
    allow_distinct = False
    contains_aggregate = False

    @property
    def output_field(self):
        return IncludeJSONField()

    def convert_value(self, value, expression, connection):
        if not value:
            return []
        return value

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, function='JSON_GROUP_ARRAY', **extra_context)
