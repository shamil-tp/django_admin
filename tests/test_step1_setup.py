"""Step 1 – Admin Setup."""
import pytest
from django.apps import apps
from django.contrib.auth import get_user_model

from tests.helpers import DUMPDATA_CMD, load_auth_fixture, read_auth_fixture


def test_admin_app_installed():
    assert apps.is_installed("django.contrib.admin"), (
        "Step 1: add 'django.contrib.admin' to INSTALLED_APPS in config/settings.py."
    )


def test_library_app_installed():
    assert apps.is_installed("library"), (
        "Step 1: add 'library' to INSTALLED_APPS in config/settings.py."
    )


def test_admin_redirects_to_login(client, db):
    response = client.get("/admin/")
    assert response.status_code == 302, (
        f"Step 1: GET /admin/ returned {response.status_code}, expected a 302 redirect to the "
        "login page. Add path('admin/', admin.site.urls) to config/urls.py."
    )
    assert response["Location"].startswith("/admin/login/"), (
        f"Step 1: GET /admin/ should redirect to /admin/login/, got {response['Location']!r}."
    )


def test_fixture_contains_superuser():
    data = read_auth_fixture(step=1)
    superusers = [
        obj
        for obj in data
        if obj.get("model") == "auth.user"
        and obj.get("fields", {}).get("is_superuser")
        and obj.get("fields", {}).get("is_staff")
    ]
    assert superusers, (
        "Step 1: fixtures/auth.json has no user with is_superuser=true and is_staff=true. "
        f"Run `python manage.py createsuperuser`, then re-export with:\n    {DUMPDATA_CMD}"
    )


def test_superuser_can_open_admin(client, db):
    if not apps.is_installed("django.contrib.admin"):
        pytest.fail("Step 1: 'django.contrib.admin' is not in INSTALLED_APPS.", pytrace=False)
    load_auth_fixture(step=1)
    superuser = get_user_model().objects.filter(
        is_superuser=True, is_staff=True, is_active=True
    ).first()
    assert superuser is not None, (
        "Step 1: no active superuser was found after loading fixtures/auth.json. "
        f"Run createsuperuser and re-export with:\n    {DUMPDATA_CMD}"
    )
    client.force_login(superuser)
    response = client.get("/admin/")
    assert response.status_code == 200, (
        f"Step 1: logged in as '{superuser.username}', GET /admin/ returned "
        f"{response.status_code} instead of 200."
    )
