from django.contrib.postgres.fields import JSONField
from django.db.models.expressions import Func, Expression


class JSONBuildArray(Func):
    function = 'JSON_BUILD_ARRAY'

    def __init__(self, *args, **kwargs):
        super(JSONBuildArray, self).__init__(*args, output_field=JSONField(), **kwargs)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, function='JSON_ARRAY', **extra_context)
