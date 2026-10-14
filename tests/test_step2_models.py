"""Step 2 – Model Registration."""
import io
from pathlib import Path

import pytest
from django.contrib.admin import ModelAdmin
from django.core.management import call_command
from django.db import models

from tests.helpers import (
    BASE_DIR,
    get_admin_or_fail,
    get_field_or_fail,
    get_model_or_fail,
    require_app,
)

STEP = 2


# --------------------------------------------------------------------------- #
# Author
# --------------------------------------------------------------------------- #
def test_author_name_field():
    Author = get_model_or_fail("Author", STEP)
    field = get_field_or_fail(Author, "name", STEP, "models.CharField(max_length=100)")
    assert isinstance(field, models.CharField) and field.max_length == 100, (
        "Step 2: Author.name must be a CharField(max_length=100)."
    )


def test_author_str():
    Author = get_model_or_fail("Author", STEP)
    assert str(Author(name="Ursula K. Le Guin")) == "Ursula K. Le Guin", (
        "Step 2: Author.__str__ must return the author's name."
    )


# --------------------------------------------------------------------------- #
# Book
# --------------------------------------------------------------------------- #
def test_book_title_field():
    Book = get_model_or_fail("Book", STEP)
    field = get_field_or_fail(Book, "title", STEP, "models.CharField(max_length=200)")
    assert isinstance(field, models.CharField) and field.max_length == 200, (
        "Step 2: Book.title must be a CharField(max_length=200)."
    )


def test_book_price_field():
    Book = get_model_or_fail("Book", STEP)
    field = get_field_or_fail(
        Book, "price", STEP, "models.DecimalField(max_digits=6, decimal_places=2)"
    )
    assert (
        isinstance(field, models.DecimalField)
        and field.max_digits == 6
        and field.decimal_places == 2
    ), "Step 2: Book.price must be a DecimalField(max_digits=6, decimal_places=2)."


def test_book_published_field():
    Book = get_model_or_fail("Book", STEP)
    field = get_field_or_fail(Book, "published", STEP, "models.DateField()")
    # DateTimeField is a subclass of DateField, so compare the exact type.
    assert type(field) is models.DateField, (
        f"Step 2: Book.published must be a DateField (found {type(field).__name__})."
    )


def test_book_str():
    Book = get_model_or_fail("Book", STEP)
    assert str(Book(title="The Dispossessed")) == "The Dispossessed", (
        "Step 2: Book.__str__ must return the book's title."
    )


# --------------------------------------------------------------------------- #
# Migrations
# --------------------------------------------------------------------------- #
def test_migration_files_exist():
    require_app("library", STEP, "Add 'library' to INSTALLED_APPS (Step 1).")
    migrations_dir = BASE_DIR / "library" / "migrations"
    files = [p for p in Path(migrations_dir).glob("[0-9][0-9][0-9][0-9]_*.py")]
    assert files, (
        "Step 2: library/migrations/ has no migration files. Run "
        "`python manage.py makemigrations library` and commit the generated files."
    )


def test_no_missing_migrations(db):
    require_app("library", STEP, "Add 'library' to INSTALLED_APPS (Step 1).")
    out = io.StringIO()
    try:
        call_command("makemigrations", "library", "--check", "--dry-run", stdout=out, stderr=out)
        changes_pending = False
    except SystemExit:
        changes_pending = True
    if changes_pending:
        pytest.fail(
            "Step 2: your models have changes that are not in a migration yet. Run "
            "`python manage.py makemigrations library` and commit library/migrations/.\n"
            + out.getvalue(),
            pytrace=False,
        )


# --------------------------------------------------------------------------- #
# Admin registration
# --------------------------------------------------------------------------- #
def test_author_registered():
    Author = get_model_or_fail("Author", STEP)
    get_admin_or_fail(Author, STEP)


def test_book_registered_with_custom_admin():
    Book = get_model_or_fail("Book", STEP)
    admin_cls = type(get_admin_or_fail(Book, STEP))
    assert issubclass(admin_cls, ModelAdmin) and admin_cls is not ModelAdmin, (
        "Step 2: Book must be registered with its own admin class: "
        "@admin.register(Book) above `class BookAdmin(admin.ModelAdmin)`."
    )
    assert admin_cls.__name__ == "BookAdmin", (
        f"Step 2: Book's admin class should be named BookAdmin (found {admin_cls.__name__})."
    )
