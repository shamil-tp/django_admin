"""
Step 3 – Data Management.

`author` only exists after Step 4's ForeignKey. The `author` entries in
list_display / search_fields / list_filter are therefore checked here only once
Book.author exists (otherwise that test is skipped), and Step 4 checks them
unconditionally.
"""
import datetime
from decimal import Decimal

import pytest

from tests.helpers import get_admin_or_fail, get_model_or_fail, has_field

STEP = 3


def _book_admin():
    Book = get_model_or_fail("Book", STEP)
    return Book, get_admin_or_fail(Book, STEP)


def _names(option):
    """Normalise admin options like list_filter, which may hold tuples or classes."""
    names = []
    for item in option or ():
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, (tuple, list)) and item:
            names.append(item[0])
    return names


def _author_for(Book):
    if not has_field(Book, "author"):
        return None
    Author = Book._meta.get_field("author").related_model
    return Author.objects.create(name="Test Author")


def _make_book(Book, title, published=datetime.date(2024, 1, 15)):
    kwargs = {"title": title, "price": Decimal("19.99"), "published": published}
    author = _author_for(Book)
    if author is not None:
        kwargs["author"] = author
    return Book.objects.create(**kwargs)


def _form_errors(response):
    context = getattr(response, "context", None)
    if context and "adminform" in context:
        return dict(context["adminform"].form.errors)
    return {}


# --------------------------------------------------------------------------- #
# ModelAdmin options
# --------------------------------------------------------------------------- #
def test_list_display():
    _, book_admin = _book_admin()
    missing = {"title", "price", "published"} - set(book_admin.list_display)
    assert not missing, (
        f"Step 3: BookAdmin.list_display is missing {sorted(missing)}. "
        "Expected list_display = ('title', 'author', 'price', 'published')."
    )


def test_search_fields():
    _, book_admin = _book_admin()
    assert "title" in book_admin.search_fields, (
        "Step 3: BookAdmin.search_fields must include 'title'."
    )


def test_list_filter():
    _, book_admin = _book_admin()
    assert "published" in _names(book_admin.list_filter), (
        "Step 3: BookAdmin.list_filter must include 'published'."
    )


def test_ordering():
    _, book_admin = _book_admin()
    assert tuple(book_admin.ordering or ()) == ("-published",), (
        f"Step 3: BookAdmin.ordering must be ('-published',) (newest first), "
        f"found {book_admin.ordering!r}."
    )


def test_author_options_once_foreign_key_exists():
    Book, book_admin = _book_admin()
    if not has_field(Book, "author"):
        pytest.skip("Book.author doesn't exist yet – the author options are checked after Step 4.")
    problems = []
    if "author" not in book_admin.list_display:
        problems.append("list_display must include 'author'")
    if "author__name" not in book_admin.search_fields:
        problems.append("search_fields must include 'author__name'")
    if "author" not in _names(book_admin.list_filter):
        problems.append("list_filter must include 'author'")
    assert not problems, "Step 3: BookAdmin " + "; ".join(problems) + "."


# --------------------------------------------------------------------------- #
# Change list + search
# --------------------------------------------------------------------------- #
def test_changelist_page_loads(admin_client):
    Book, _ = _book_admin()
    _make_book(Book, "The Left Hand of Darkness")
    response = admin_client.get("/admin/library/book/")
    assert response.status_code == 200, (
        f"Step 3: /admin/library/book/ returned {response.status_code} for a superuser. "
        "Check your BookAdmin options (run `python manage.py check`)."
    )


def test_search(admin_client):
    Book, _ = _book_admin()
    _make_book(Book, "A Wizard of Earthsea")
    _make_book(Book, "The Lathe of Heaven")
    response = admin_client.get("/admin/library/book/", {"q": "Earthsea"})
    assert response.status_code == 200, (
        f"Step 3: searching with ?q= returned {response.status_code}. Check search_fields."
    )
    count = response.context["cl"].result_count
    assert count == 1, (
        f"Step 3: searching for 'Earthsea' returned {count} books, expected 1. "
        "Make sure search_fields includes 'title'."
    )


# --------------------------------------------------------------------------- #
# CRUD through the admin
# --------------------------------------------------------------------------- #
def test_crud_through_admin(admin_client):
    Book, _ = _book_admin()

    # Create
    data = {"title": "Always Coming Home", "price": "24.50", "published": "1985-09-01"}
    author = _author_for(Book)
    if author is not None:
        data["author"] = author.pk
    response = admin_client.post("/admin/library/book/add/", data)
    assert response.status_code == 302, (
        f"Step 3: adding a Book through the admin failed (status {response.status_code}, "
        f"form errors: {_form_errors(response)})."
    )
    book = Book.objects.filter(title="Always Coming Home").first()
    assert book is not None, "Step 3: the Book added through the admin was not saved."

    # Read
    change_url = f"/admin/library/book/{book.pk}/change/"
    response = admin_client.get(change_url)
    assert response.status_code == 200, (
        f"Step 3: viewing a Book in the admin returned {response.status_code}."
    )

    # Update
    data["title"] = "Always Coming Home (Revised)"
    response = admin_client.post(change_url, data)
    assert response.status_code == 302, (
        f"Step 3: changing a Book through the admin failed (status {response.status_code}, "
        f"form errors: {_form_errors(response)})."
    )
    book.refresh_from_db()
    assert book.title == "Always Coming Home (Revised)", (
        "Step 3: the Book change made through the admin was not saved."
    )

    # Delete
    response = admin_client.post(f"/admin/library/book/{book.pk}/delete/", {"post": "yes"})
    assert response.status_code == 302, (
        f"Step 3: deleting a Book through the admin returned {response.status_code}."
    )
    assert not Book.objects.filter(pk=book.pk).exists(), (
        "Step 3: the Book deleted through the admin still exists."
    )
