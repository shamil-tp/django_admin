"""
Shared helpers for the lab tests.

Every helper turns "this doesn't exist yet" into a readable `pytest.fail(...)`
message instead of an ImportError/LookupError that would crash the suite.
"""
import json
import tempfile
from pathlib import Path

import pytest
from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.core.management import call_command

BASE_DIR = Path(__file__).resolve().parent.parent
FIXTURE_PATH = BASE_DIR / "fixtures" / "auth.json"
DUMPDATA_CMD = (
    "python manage.py dumpdata auth.user auth.group "
    "--natural-foreign --indent 2 -o fixtures/auth.json"
)


# --------------------------------------------------------------------------- #
# Apps, models and fields
# --------------------------------------------------------------------------- #
def require_app(app_label, step, hint):
    if not apps.is_installed(app_label):
        pytest.fail(f"Step {step}: '{app_label}' is not in INSTALLED_APPS. {hint}", pytrace=False)


def get_model_or_fail(model_name, step):
    require_app("library", step, "Add 'library' to INSTALLED_APPS in config/settings.py (Step 1).")
    try:
        return apps.get_model("library", model_name)
    except LookupError:
        pytest.fail(
            f"Step {step}: model 'library.{model_name}' does not exist. "
            f"Define `class {model_name}(models.Model)` in library/models.py.",
            pytrace=False,
        )


def get_field_or_fail(model, field_name, step, expected):
    try:
        return model._meta.get_field(field_name)
    except FieldDoesNotExist:
        pytest.fail(
            f"Step {step}: {model.__name__}.{field_name} is missing. "
            f"Add `{field_name} = {expected}` to the {model.__name__} model.",
            pytrace=False,
        )


def has_field(model, field_name):
    try:
        model._meta.get_field(field_name)
        return True
    except FieldDoesNotExist:
        return False


# --------------------------------------------------------------------------- #
# Admin registrations
# --------------------------------------------------------------------------- #
def get_admin_or_fail(model, step):
    require_app(
        "django.contrib.admin", step, "Add 'django.contrib.admin' to INSTALLED_APPS (Step 1)."
    )
    from django.contrib import admin

    model_admin = admin.site._registry.get(model)
    if model_admin is None:
        pytest.fail(
            f"Step {step}: {model.__name__} is not registered in the admin. "
            f"Register it in library/admin.py.",
            pytrace=False,
        )
    return model_admin


# --------------------------------------------------------------------------- #
# fixtures/auth.json
# --------------------------------------------------------------------------- #
def read_auth_fixture(step):
    """Return the parsed fixture (tolerates UTF-16 files produced by PowerShell's `>`)."""
    if not FIXTURE_PATH.exists():
        pytest.fail(
            f"Step {step}: fixtures/auth.json is missing. Export your users with:\n"
            f"    {DUMPDATA_CMD}\n"
            f"then commit and push the file.",
            pytrace=False,
        )
    raw = FIXTURE_PATH.read_bytes()
    try:
        if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
            text = raw.decode("utf-16")
        else:
            text = raw.decode("utf-8-sig")
        data = json.loads(text)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        pytest.fail(
            f"Step {step}: fixtures/auth.json is not valid JSON ({exc}). Re-export it with:\n"
            f"    {DUMPDATA_CMD}",
            pytrace=False,
        )
    if not isinstance(data, list):
        pytest.fail(f"Step {step}: fixtures/auth.json must contain a JSON list.", pytrace=False)
    return data


def load_auth_fixture(step):
    """Load fixtures/auth.json into the test database (requires the `db` fixture)."""
    data = read_auth_fixture(step)
    with tempfile.TemporaryDirectory() as tmp:
        normalized = Path(tmp) / "auth.json"
        normalized.write_text(json.dumps(data), encoding="utf-8")
        try:
            call_command("loaddata", str(normalized), verbosity=0)
        except Exception as exc:  # noqa: BLE001 – any failure gets a friendly message
            pytest.fail(
                f"Step {step}: fixtures/auth.json could not be loaded: {exc}\n"
                f"Re-export it (after running migrate) with:\n    {DUMPDATA_CMD}",
                pytrace=False,
            )
    return data
