# Django Include
ORM extensions for performance conscious perfectionists.

Django-include provides `select_related` functionality for Many-to-X relation.


## Requirements
Python 2.7 or 3.4+, Django 1.9+, and any SQL server with support for JSON aggregations.

Currently only SQLite and Postgres are supported.


## Installation
```bash
pip install django-include
```


## Usage
Add `include` to `INSTALLED_APPS`.

Attach `IncludeManager` to a model:
```python
from include import IncludeMaager

class BlogPost(models.Model):
    objects = IncludeManager()
```

Subclass `IncludeQuerySet`:

```python
from include import IncludeQuerySet

class BlogPost(models.Model):
    objects = CustomQuerySet.as_manager()
```


## What/Why?
Consider the following:

Given the following models.
```python
class Email(Model):
    name = CharField()
    user = ForeignKey('User')


class User(Model):
    emails = ...


class Contributor(Model):
    role = CharField()
    user = ForeignKey('User')
    project = ForeignKey('Project')

class Project(Model):
    contributors = ...
```

There is an endpoint that returns all the users that contributed to a project, their roles, and their email addresses.

If this endpoint were to be implemented using just Django's ORM, it would end up looking something like this:
```python
project = Project.objects.get(pk=id)  # 1 Query!
for contributor in project.contributors.select_related('users'):  # 1 Query!
  [x for x in contributor.user.emails.all()]  # N * M Queries!
  # Some serialization code
```
At first this solution seems fine, but what happens when a project has an entire college of people, each with a couple email addresses?
Now, there are certainly other tricks that could be done here to reduce the number of queries and runtime.
For instance, dropping down into raw SQL with a couple joins and/or subselects.

Or you could just use `.include`, do a single query, and not have to explain all the *neat* things you did.
```python
project = Project.objects.include('contributors__user__emails')  # 1 Query!
for contributor in project.contributors.all():  # Already loaded
  [x for x in contributor.user.emails.all()]  # Already loaded
  # Some serialization code
```


## How?
Django Include abuses JSON aggregations and Django's `extra`/`annotate` functions to embed related data.
