"""Step 5 – Access Control."""
import datetime
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission

from tests.helpers import (
    DUMPDATA_CMD,
    get_admin_or_fail,
    get_model_or_fail,
    has_field,
    load_auth_fixture,
)

STEP = 5
EXPECTED_PERMS = {"add_book", "change_book", "view_book"}


@pytest.fixture
def loaded(db):
    load_auth_fixture(STEP)


@pytest.fixture
def editors(loaded):
    group = Group.objects.filter(name="Editors").first()
    if group is None:
        pytest.fail(
            "Step 5: there is no group named exactly 'Editors' in fixtures/auth.json. "
            f"Create it in the admin, then re-export with:\n    {DUMPDATA_CMD}",
            pytrace=False,
        )
    return group


@pytest.fixture
def editor1(loaded):
    user = get_user_model().objects.filter(username="editor1").first()
    if user is None:
        pytest.fail(
            "Step 5: there is no user named 'editor1' in fixtures/auth.json. "
            f"Create it in the admin, then re-export with:\n    {DUMPDATA_CMD}",
            pytrace=False,
        )
    return user


@pytest.fixture
def book(db):
    Book = get_model_or_fail("Book", STEP)
    kwargs = {"title": "The Fifth Season", "price": Decimal("17.99"),
              "published": datetime.date(2015, 8, 4)}
    if has_field(Book, "author"):
        Author = Book._meta.get_field("author").related_model
        kwargs["author"] = Author.objects.create(name="N. K. Jemisin")
    return Book.objects.create(**kwargs)


# --------------------------------------------------------------------------- #
# Group and user from the fixture
# --------------------------------------------------------------------------- #
def test_editors_group_permissions(editors):
    perms = {
        f"{p.content_type.app_label}.{p.codename}"
        for p in editors.permissions.select_related("content_type")
    }
    expected = {f"library.{codename}" for codename in EXPECTED_PERMS}
    assert "library.delete_book" not in perms, (
        "Step 5: the Editors group must NOT have the 'Can delete book' permission."
    )
    assert perms == expected, (
        f"Step 5: the Editors group must have exactly {sorted(expected)}, found {sorted(perms)}. "
        "(If the names look unrelated, re-export with --natural-foreign:\n"
        f"    {DUMPDATA_CMD})"
    )


def test_editor1_account(editor1, editors):
    assert editor1.is_active, "Step 5: editor1 must be active."
    assert editor1.is_staff, "Step 5: editor1 must have 'Staff status' (is_staff=True)."
    assert not editor1.is_superuser, "Step 5: editor1 must NOT be a superuser."
    assert editor1.groups.filter(pk=editors.pk).exists(), (
        "Step 5: editor1 must be a member of the Editors group."
    )


# --------------------------------------------------------------------------- #
# Admin access as editor1
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "url, expected, meaning",
    [
        ("/admin/library/book/", 200, "see the book list"),
        ("/admin/library/book/add/", 200, "add books"),
        ("/admin/auth/user/", 403, "NOT manage users"),
    ],
)
def test_editor1_access(client, editor1, editors, book, url, expected, meaning):
    client.force_login(editor1)
    response = client.get(url)
    assert response.status_code == expected, (
        f"Step 5: editor1 should be able to {meaning}: GET {url} returned "
        f"{response.status_code}, expected {expected}."
    )


def test_editor1_cannot_delete_book(client, editor1, editors, book):
    client.force_login(editor1)
    response = client.get(f"/admin/library/book/{book.pk}/delete/")
    assert response.status_code == 403, (
        f"Step 5: editor1 must not be able to delete books: the delete page returned "
        f"{response.status_code}, expected 403."
    )


# --------------------------------------------------------------------------- #
# has_delete_permission override
# --------------------------------------------------------------------------- #
def test_has_delete_permission_overridden():
    from django.contrib.admin import ModelAdmin

    Book = get_model_or_fail("Book", STEP)
    admin_cls = type(get_admin_or_fail(Book, STEP))
    assert admin_cls.has_delete_permission is not ModelAdmin.has_delete_permission, (
        "Step 5: override `has_delete_permission(self, request, obj=None)` in BookAdmin."
    )


def test_only_superusers_can_delete(client, admin_client, book, django_user_model):
    # Staff user who *does* have delete_book – the override must still say no.
    staff = django_user_model.objects.create_user("staff_with_delete", password="x", is_staff=True)
    staff.user_permissions.add(
        *Permission.objects.filter(
            content_type__app_label="library",
            codename__in=["view_book", "delete_book"],
        )
    )
    client.force_login(staff)
    url = f"/admin/library/book/{book.pk}/delete/"
    response = client.get(url)
    assert response.status_code == 403, (
        "Step 5: has_delete_permission must return True only for superusers – a staff user "
        f"with the delete_book permission got {response.status_code} instead of 403."
    )
    response = admin_client.get(url)
    assert response.status_code == 200, (
        f"Step 5: a superuser should still be able to delete books (got {response.status_code})."
    )
