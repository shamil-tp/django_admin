import pytest
from django.apps import apps
from django.db import connection


@pytest.fixture(autouse=True)
def _library_tables_exist(request):
    """
    For tests that use the database: if a library model exists but its table
    doesn't, the migration files were not created/committed. Fail with a hint
    instead of an obscure "no such table" error.
    """
    if "db" not in request.fixturenames or not apps.is_installed("library"):
        return
    request.getfixturevalue("db")
    tables = set(connection.introspection.table_names())
    missing = [
        m.__name__
        for m in apps.get_app_config("library").get_models()
        if m._meta.db_table not in tables
    ]
    if missing:
        pytest.fail(
            f"No database table for library model(s): {', '.join(missing)}. "
            "Run `python manage.py makemigrations library`, then commit the new "
            "files in library/migrations/.",
            pytrace=False,
        )
