"""Step 4 – Relationships."""
import datetime
from decimal import Decimal

from django.contrib.admin.options import InlineModelAdmin
from django.db import models

from tests.helpers import get_admin_or_fail, get_field_or_fail, get_model_or_fail

STEP = 4


def _author_field():
    Book = get_model_or_fail("Book", STEP)
    return Book, get_field_or_fail(
        Book, "author", STEP, "models.ForeignKey(Author, on_delete=models.CASCADE)"
    )


def _list_filter_names(option):
    return [
        item if isinstance(item, str) else item[0]
        for item in option or ()
        if isinstance(item, str) or (isinstance(item, (tuple, list)) and item)
    ]


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
def test_book_author_is_foreign_key():
    Author = get_model_or_fail("Author", STEP)
    _, field = _author_field()
    assert isinstance(field, models.ForeignKey), (
        f"Step 4: Book.author must be a ForeignKey (found {type(field).__name__})."
    )
    assert field.related_model is Author, (
        "Step 4: Book.author must point to the Author model."
    )
    assert field.remote_field.on_delete is models.CASCADE, (
        "Step 4: Book.author must use on_delete=models.CASCADE."
    )


def test_deleting_author_deletes_books(db):
    Author = get_model_or_fail("Author", STEP)
    Book, _ = _author_field()
    author = Author.objects.create(name="Octavia E. Butler")
    Book.objects.create(
        title="Kindred", price=Decimal("15.00"), published=datetime.date(1979, 6, 1), author=author
    )
    author.delete()
    assert not Book.objects.filter(title="Kindred").exists(), (
        "Step 4: deleting an Author should also delete their books (on_delete=CASCADE)."
    )


def test_tag_name_field():
    Tag = get_model_or_fail("Tag", STEP)
    field = get_field_or_fail(Tag, "name", STEP, "models.CharField(max_length=50)")
    assert isinstance(field, models.CharField) and field.max_length == 50, (
        "Step 4: Tag.name must be a CharField(max_length=50)."
    )


def test_book_tags_field():
    Tag = get_model_or_fail("Tag", STEP)
    Book = get_model_or_fail("Book", STEP)
    field = get_field_or_fail(Book, "tags", STEP, "models.ManyToManyField(Tag, blank=True)")
    assert isinstance(field, models.ManyToManyField), (
        f"Step 4: Book.tags must be a ManyToManyField (found {type(field).__name__})."
    )
    assert field.related_model is Tag, "Step 4: Book.tags must point to the Tag model."
    assert field.blank, "Step 4: Book.tags must have blank=True so a book can have no tags."


# --------------------------------------------------------------------------- #
# Admin
# --------------------------------------------------------------------------- #
def test_tag_registered():
    Tag = get_model_or_fail("Tag", STEP)
    get_admin_or_fail(Tag, STEP)


def test_filter_horizontal():
    Book = get_model_or_fail("Book", STEP)
    book_admin = get_admin_or_fail(Book, STEP)
    assert "tags" in book_admin.filter_horizontal, (
        "Step 4: set filter_horizontal = ('tags',) on BookAdmin."
    )


def test_book_admin_author_options():
    """The author parts of Step 3 that need the ForeignKey to exist."""
    Book = get_model_or_fail("Book", STEP)
    book_admin = get_admin_or_fail(Book, STEP)
    problems = []
    if "author" not in book_admin.list_display:
        problems.append("add 'author' to list_display")
    if "author__name" not in book_admin.search_fields:
        problems.append("add 'author__name' to search_fields")
    if "author" not in _list_filter_names(book_admin.list_filter):
        problems.append("add 'author' to list_filter")
    assert not problems, "Step 4 (Step 3 follow-up): on BookAdmin, " + "; ".join(problems) + "."


def _book_inlines():
    Author = get_model_or_fail("Author", STEP)
    Book = get_model_or_fail("Book", STEP)
    author_admin = get_admin_or_fail(Author, STEP)
    return [
        inline
        for inline in getattr(author_admin, "inlines", ())
        if isinstance(inline, type)
        and issubclass(inline, InlineModelAdmin)
        and inline.model is Book
    ]


def test_author_admin_has_book_inline():
    inlines = _book_inlines()
    assert inlines, (
        "Step 4: AuthorAdmin.inlines must contain a Book inline, e.g. "
        "`class BookInline(admin.TabularInline): model = Book; extra = 1` and "
        "`inlines = [BookInline]` on an AuthorAdmin registered for Author."
    )
    assert inlines[0].extra == 1, (
        f"Step 4: BookInline.extra must be 1 (found {inlines[0].extra})."
    )


def test_author_change_page_renders_inline(admin_client):
    Author = get_model_or_fail("Author", STEP)
    Book = get_model_or_fail("Book", STEP)
    author = Author.objects.create(name="N. K. Jemisin")
    response = admin_client.get(f"/admin/library/author/{author.pk}/change/")
    assert response.status_code == 200, (
        f"Step 4: the Author change page returned {response.status_code}."
    )
    formsets = response.context.get("inline_admin_formsets", [])
    assert any(fs.formset.model is Book for fs in formsets), (
        "Step 4: the Author change page does not show a Book inline. "
        "Add your BookInline to AuthorAdmin.inlines."
    )
