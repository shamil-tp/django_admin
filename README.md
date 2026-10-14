# Django Admin Lab 📚

In this lab you'll turn an almost-empty Django project into a working **library
admin site**. You'll switch the admin on, add models, make the change list
useful, connect models together, and finally lock things down with groups and
permissions.

Each time you push, GitHub Actions checks your work and shows a ✅ or ❌ for
each of the 5 steps.

### Learning goals

By the end you will be able to:

- enable the Django admin and create a superuser
- define models and register them with a custom `ModelAdmin`
- configure `list_display`, `search_fields`, `list_filter` and `ordering`
- model one-to-many and many-to-many relationships and edit them with inlines
- control what staff users can do with groups, permissions and `has_delete_permission`

---

## Contents

- [Getting started](#getting-started)
- [Step 1 – Admin Setup](#step-1--admin-setup)
- [Step 2 – Model Registration](#step-2--model-registration)
- [Step 3 – Data Management](#step-3--data-management)
- [Step 4 – Relationships](#step-4--relationships)
- [Step 5 – Access Control](#step-5--access-control)
- [Testing locally](#testing-locally)
- [Submitting your work](#submitting-your-work)
- [Troubleshooting](#troubleshooting)
- [Rules](#rules)
- [For instructors](#for-instructors)

---

## Getting started

1. **Fork** this repository: click **Fork** at the top right of the GitHub page.
2. **Enable Actions on your fork.** GitHub turns workflows off on forks by default.
   Open the **Actions** tab of *your fork* and click
   **"I understand my workflows, go ahead and enable them"**.
   If you skip this, nothing gets checked when you push.
3. **Clone your fork** (replace `YOUR-USERNAME`):

   ```bash
   git clone https://github.com/YOUR-USERNAME/django-admin-lab.git
   cd django-admin-lab
   ```

4. **Create and activate a virtual environment**, then install the requirements:

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate
   # Windows (PowerShell)
   venv\Scripts\Activate.ps1
   # Windows (cmd)
   venv\Scripts\activate.bat

   pip install -r requirements.txt
   ```

   You need **Python 3.12** (3.10 or newer works locally, but the checks run on 3.12).

5. Run the tests once. Everything should fail, because you haven't done anything yet:

   ```bash
   pytest
   ```

### Project layout

```
config/          Django project: settings.py, urls.py   ← you edit these in Step 1
library/         the app you build: models.py, admin.py ← you edit these in Steps 2–5
fixtures/        your exported users and groups (auth.json)
tests/           the automatic checks (do not edit)
```

### The export command

Steps 1 and 5 ask you to export your users and groups to `fixtures/auth.json`
so the checker can use them. Always use **exactly** this command:

```bash
python manage.py dumpdata auth.user auth.group --natural-foreign --indent 2 -o fixtures/auth.json
```

- `--natural-foreign` stores permissions by name (`add_book`) instead of an internal
  number, so the file loads correctly in a fresh database.
- `-o fixtures/auth.json` writes a UTF-8 file. Don't use `> fixtures/auth.json`,
  because on Windows PowerShell that produces a UTF-16 file.

> ⚠️ The fixture contains your users' **password hashes** and your fork is public.
> Use a password you don't use anywhere else.

---

## Step 1 – Admin Setup

**Goal:** turn on the Django admin and create a superuser who can log in to it.

**Files to edit:** `config/settings.py`, `config/urls.py`

### What to do

1. In `config/settings.py`, add `"django.contrib.admin"` and `"library"` to `INSTALLED_APPS`
   (look for the `TODO` comments):

   ```python
   INSTALLED_APPS = [
       "django.contrib.admin",
       # ... the existing django.contrib apps ...
       "library",
   ]
   ```

2. In `config/urls.py`, import the admin and add the admin route:

   ```python
   from django.contrib import admin
   from django.urls import path

   urlpatterns = [
       path(...),   # "admin/" → admin.site.urls
   ]
   ```

3. Create the database tables, then create your superuser:

   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

4. Start the server and log in at <http://127.0.0.1:8000/admin/>:

   ```bash
   python manage.py runserver
   ```

   Press `Ctrl+C` to stop it.

5. Export your users (you'll do this again at the end of Step 5):

   ```bash
   python manage.py dumpdata auth.user auth.group --natural-foreign --indent 2 -o fixtures/auth.json
   ```

6. Commit and push:

   ```bash
   git add config/ fixtures/auth.json
   git commit -m "Step 1: enable the admin"
   git push
   ```

### How it's checked

- `django.contrib.admin` and `library` are in `INSTALLED_APPS`
- `GET /admin/` redirects (302) to `/admin/login/` when you're not logged in
- `fixtures/auth.json` exists and contains a user with `is_superuser=true` and `is_staff=true`
- after loading the fixture, that superuser gets a 200 on `/admin/`

---

## Step 2 – Model Registration

**Goal:** create the `Author` and `Book` models and show them in the admin.

**Files to edit:** `library/models.py`, `library/admin.py`

### What to do

1. In `library/models.py`, create two models:

   | Model    | Field       | Type                                              |
   |----------|-------------|---------------------------------------------------|
   | `Author` | `name`      | `CharField(max_length=100)`                       |
   | `Book`   | `title`     | `CharField(max_length=200)`                       |
   | `Book`   | `price`     | `DecimalField(max_digits=6, decimal_places=2)`    |
   | `Book`   | `published` | `DateField()`                                     |

   Give each model a `__str__` method. `Author` returns its name and `Book` returns its title:

   ```python
   class Author(models.Model):
       name = models.CharField(max_length=100)

       def __str__(self):
           return ...
   ```

2. Create the migration and apply it:

   ```bash
   python manage.py makemigrations library
   python manage.py migrate
   ```

   This creates a file in `library/migrations/` (for example `0001_initial.py`).
   **You must commit it**, because the checker builds its database from your migrations.

3. In `library/admin.py`, register both models. Register `Book` with the
   **decorator** and its own admin class:

   ```python
   from django.contrib import admin
   from .models import Author, Book

   admin.site.register(...)

   @admin.register(...)
   class BookAdmin(admin.ModelAdmin):
       pass
   ```

4. Run the server, log in, and add a couple of authors and books.

5. Commit and push:

   ```bash
   git add library/
   git commit -m "Step 2: Author and Book models"
   git push
   ```

### How it's checked

- `Author.name`, `Book.title`, `Book.price` and `Book.published` exist with exactly the types and options above
- `str(author)` returns the name and `str(book)` returns the title
- `library/migrations/` contains migrations, and `makemigrations --check` finds no missing ones
- `Author` and `Book` are registered in the admin
- `Book` uses a custom admin class named `BookAdmin` (a `ModelAdmin` subclass)

---

## Step 3 – Data Management

**Goal:** make the book list easy to scan, search and filter.

**File to edit:** `library/admin.py`

> ### ℹ️ About `author`
>
> In the finished project, `BookAdmin` uses the book's **author**, but `Book.author`
> doesn't exist until **Step 4**. If you add `"author"` now, Django will raise an error.
>
> So in Step 3, set everything **except** the author entries. Step 3's checks skip
> the author entries while `Book.author` doesn't exist. Step 4 tells you to come back
> and add them, and from then on Steps 3 and 4 both check them.

### What to do

1. Configure `BookAdmin`:

   ```python
   @admin.register(Book)
   class BookAdmin(admin.ModelAdmin):
       list_display = ("title", ...)     # columns: title, price, published
       search_fields = (...)             # search box: title
       list_filter = (...)               # sidebar filter: published
       ordering = (...)                  # newest published first
   ```

   Hint: a `-` in front of a field name in `ordering` reverses the order.

2. Open <http://127.0.0.1:8000/admin/library/book/> and try the columns, the search box and the filter.
   Add, change and delete a book to see the whole workflow.

3. Commit and push:

   ```bash
   git add library/admin.py
   git commit -m "Step 3: list display, search, filters, ordering"
   git push
   ```

### How it's checked

- `list_display` includes `title`, `price`, `published` (and `author` once it exists)
- `search_fields` includes `title` (and `author__name` once `author` exists)
- `list_filter` includes `published` (and `author` once it exists)
- `ordering == ("-published",)`
- `/admin/library/book/` returns 200 for a superuser
- searching with `?q=` returns only matching books
- a book can be added, viewed, changed and deleted through the admin

---

## Step 4 – Relationships

**Goal:** connect books to authors and tags, and edit an author's books on the author page.

**Files to edit:** `library/models.py`, `library/admin.py`

### What to do

1. In `library/models.py`:
   - Create a `Tag` model with `name = CharField(max_length=50)` (and a `__str__`).
   - Add `author` to `Book` as a `ForeignKey` to `Author` with `on_delete=models.CASCADE`.
   - Add `tags` to `Book` as a `ManyToManyField` to `Tag` with `blank=True`.

   ```python
   class Book(models.Model):
       ...
       author = models.ForeignKey(..., on_delete=...)
       tags = models.ManyToManyField(..., blank=True)
   ```

   Hint: define `Tag` *above* `Book`, or refer to it as a string: `"Tag"`.

2. Make and apply the migration:

   ```bash
   python manage.py makemigrations library
   python manage.py migrate
   ```

   Because you may already have books, Django asks what author to give them:

   ```
   It is impossible to add a non-nullable field 'author' to book without specifying a default.
   Please select a fix:
    1) Provide a one-off default now ...
   ```

   Type `1`, press Enter, then type the **id of an existing author** (usually `1`) and press Enter.
   No authors yet? Create one in the admin first, or see
   [Fixture/database problems](#fixture-loading-errors-after-model-changes) to start from a clean database.

3. In `library/admin.py`:
   - Register `Tag`.
   - Add `filter_horizontal = ("tags",)` to `BookAdmin`.
   - **Step 3 follow-up:** add `"author"` to `list_display`, `"author__name"` to
     `search_fields`, and `"author"` to `list_filter`.
   - Create a `BookInline` and use it in an `AuthorAdmin`. Replace your old
     `admin.site.register(Author)` with this:

   ```python
   class BookInline(admin.TabularInline):
       model = ...
       extra = 1

   @admin.register(Author)
   class AuthorAdmin(admin.ModelAdmin):
       inlines = [...]
   ```

4. Open an author in the admin. You should see a table of their books at the bottom.
   Open a book and you'll see the two-box tag picker.

5. Commit and push. Remember the new migration file:

   ```bash
   git add library/
   git commit -m "Step 4: relationships, tags and inlines"
   git push
   ```

### How it's checked

- `Book.author` is a `ForeignKey` to `Author` with `on_delete=CASCADE`, and deleting an author deletes their books
- `Tag.name` is a `CharField(max_length=50)`
- `Book.tags` is a `ManyToManyField` to `Tag` with `blank=True`
- `Tag` is registered, and `BookAdmin.filter_horizontal` contains `tags`
- `BookAdmin` has the author entries from the Step 3 follow-up
- `AuthorAdmin.inlines` contains an inline (`TabularInline`/`StackedInline`) for `Book` with `extra = 1`
- the Author change page renders the Book inline formset

---

## Step 5 – Access Control

**Goal:** create an "Editors" role that can add and edit books but can't delete them
and can't manage users.

**Files to edit:** `library/admin.py`, `fixtures/auth.json` (re-exported)

### What to do

1. Start the server and log in as your superuser.

2. **Create the group.** Go to **Authentication and Authorization → Groups → Add group**:
   - Name: `Editors` (exactly this, with a capital E)
   - Permissions: choose these three **and nothing else**:
     - `library | book | Can add book`
     - `library | book | Can change book`
     - `library | book | Can view book`
   - Do **not** add `Can delete book`. Save.

3. **Create the user.** Go to **Users → Add user**:
   - Username: `editor1`, plus a password (it isn't checked)
   - Save, and on the next page:
     - tick **Staff status**
     - leave **Superuser status** unticked
     - under **Groups**, move `Editors` to "Chosen groups"
   - Save.

4. In `library/admin.py`, override `has_delete_permission` on `BookAdmin`
   so that **only superusers** can delete books:

   ```python
   class BookAdmin(admin.ModelAdmin):
       ...
       def has_delete_permission(self, request, obj=None):
           return ...   # hint: request.user has an is_superuser attribute
   ```

5. Log out and log in as `editor1` to try it. You should be able to see, add and edit books,
   but there should be no delete button and no **Users** section.

6. **Re-export the fixture** so it contains the group and `editor1`:

   ```bash
   python manage.py dumpdata auth.user auth.group --natural-foreign --indent 2 -o fixtures/auth.json
   ```

7. Commit and push:

   ```bash
   git add library/admin.py fixtures/auth.json
   git commit -m "Step 5: Editors group and delete restrictions"
   git push
   ```

### How it's checked

After loading `fixtures/auth.json`:

- the group `Editors` has exactly `add_book`, `change_book` and `view_book` (no `delete_book`)
- `editor1` exists, is active, is staff, is **not** a superuser, and is in `Editors`
- logged in as `editor1`:
  - `/admin/library/book/` → 200
  - `/admin/library/book/add/` → 200
  - `/admin/library/book/<id>/delete/` → 403
  - `/admin/auth/user/` → 403
- `BookAdmin` overrides `has_delete_permission`: a non-superuser staff user is refused even if
  they have `delete_book`, while a superuser can still delete

---

## Testing locally

Run the same checks as GitHub Actions on your own machine:

```bash
pytest tests/test_step1_setup.py -v      # one step
pytest tests/test_step3_data_management.py -v
pytest                                   # everything
```

The tests use a temporary database built from **your migrations** and load users from
`fixtures/auth.json`, so your `db.sqlite3` is never touched.

Every failure starts with `Step N:` and tells you what to fix, for example:

```
Failed: Step 2: Book.price must be a DecimalField(max_digits=6, decimal_places=2).
```

---

## Submitting your work

1. Commit and push:

   ```bash
   git add .
   git commit -m "Complete Django admin lab"
   git push
   ```

   `db.sqlite3` and `venv/` are listed in `.gitignore`, so they are never committed. That's intentional.

2. Open the **Actions** tab on your fork on GitHub and click the latest **Verify lab** run.

3. You'll see one job per step (**Step 1 – Admin Setup**, ...) with ✅ or ❌, and the
   **Summary** shows a results table with your score out of 5:

   | Step | Topic              | Result  |
   |:----:|--------------------|:-------:|
   | 1    | Admin Setup        | ✅ Pass |
   | 2    | Model Registration | ✅ Pass |
   | 3    | Data Management    | ❌ Fail |
   | ...  |                    |         |

4. If a step failed, click its job and expand **Run Step N tests** to read the messages.

---

## Troubleshooting

### Actions are not running on my fork

- Open the **Actions** tab of your fork. If you see a green
  **"I understand my workflows, go ahead and enable them"** button, click it.
- Push a new commit (or use **Run workflow** on the *Verify lab* workflow) to start a run.
- Make sure you pushed to **your fork**, not the original repository: `git remote -v`.

### "No database table for library model(s)" / "your models have changes that are not in a migration yet"

You forgot to create or commit your migrations. The checker only has what you pushed.

```bash
python manage.py makemigrations library
git add library/migrations/
git commit -m "Add migrations"
git push
```

### Step 5 says the Editors group or editor1 doesn't exist

You created them in the admin but didn't **re-export** the fixture afterwards (or didn't
commit it). The checker never sees your `db.sqlite3`, only `fixtures/auth.json`:

```bash
python manage.py dumpdata auth.user auth.group --natural-foreign --indent 2 -o fixtures/auth.json
git add fixtures/auth.json
git commit -m "Re-export users and groups"
git push
```

Open `fixtures/auth.json` and check that you can find `"Editors"` and `"editor1"` in it.

### Fixture loading errors after model changes

Messages like *"fixtures/auth.json could not be loaded"*, *"Permission matching query does
not exist"* or *"Problem installing fixture"* usually mean one of these:

- **You exported without `--natural-foreign`.** Permissions were saved as numbers that don't
  match a fresh database. Re-export with the exact command above.
- **Your models changed after you exported** (for example a model was renamed). Run
  `python manage.py migrate`, check the group's permissions in the admin, then re-export.
- **You used `>` in PowerShell.** Use `-o fixtures/auth.json` instead.

If your local database gets into a mess, you can start again. Your users are safe in the fixture:

```bash
# delete db.sqlite3 (macOS/Linux: rm db.sqlite3   Windows: del db.sqlite3)
python manage.py migrate
python manage.py loaddata fixtures/auth.json
```

### The admin shows an error mentioning `author` after Step 3

You added `"author"` to `BookAdmin` before `Book.author` existed. Remove it for now, or do
Step 4's model changes first (see [About `author`](#step-3--data-management)).

---

## Rules

- **Do not edit anything in `tests/` or `.github/`.** Before grading, the workflow replaces
  `tests/` (and `pytest.ini`) with the original copies from the instructor's repository, so any
  changes there are ignored.
- Commit your migrations and `fixtures/auth.json`. Don't commit `db.sqlite3`.
- You may add extra admin options, models or fields, as long as the required ones are there exactly as described.

---

## For instructors

- **Before publishing**, open `.github/workflows/verify.yml` and replace `OWNER` in
  `UPSTREAM_REPO: ${{ vars.UPSTREAM_REPO || 'OWNER/django-admin-lab' }}` with your GitHub
  user/organisation. Forks don't inherit repository variables, so the default in the file is
  what students' runs use. The upstream repository must be public.
  While it is still `OWNER/...`, the workflow warns and grades with the fork's own `tests/`.
- Optional repository variables: `UPSTREAM_REPO`, `UPSTREAM_REF` (default `main`).
- A complete reference implementation, including a fixture, lives on the **`solution`** branch.
  It passes all 5 steps. If your lab repository is public, **don't push that branch to it**. Keep it
  in a private repository instead, because public branches are visible to students.
  The solution fixture's logins are `admin` / `LabAdmin-2026!` and `editor1` / `Editor-2026!`.
- Tamper protection covers `tests/`, `pytest.ini` and stray `conftest.py` files. A determined
  student can still edit the workflow in their own fork, so for graded work, re-run the checks
  from your side (for example by cloning the fork and running `pytest` with your `tests/`).
