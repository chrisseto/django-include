from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.aggregates import ArrayAgg


class JSONAgg(ArrayAgg):
    function = 'JSON_AGG'
    template = '%(function)s(%(expressions)s%(order_by)s)'

    def __init__(self, *args, **kwargs):
        super(JSONAgg, self).__init__(*args, output_field=JSONField(), **kwargs)

    def as_sql(self, compiler, connection, function=None, template=None):
        # TODO Find a better way to handle this
        if self.extra.get('order_by'):
            self.extra['order_by'] = ' ORDER BY ' + ', '.join(compiler.compile(x)[0] for x in self.extra['order_by'])
        else:
            self.extra['order_by'] = ''
        return super(JSONAgg, self).as_sql(compiler, connection, function=function, template=template)

    def as_sqlite(self, compiler, connection, **extra_context):
        return self.as_sql(compiler, connection, function='JSON_GROUP_ARRAY', **extra_context)
