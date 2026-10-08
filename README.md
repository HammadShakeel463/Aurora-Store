# Aurora Store

A small e-commerce storefront built with Django 5.1 — product catalog, session-backed
shopping cart, and a transactional checkout that snapshots prices and decrements
inventory atomically.

## Features

- **Catalog** — categories, slug-based URLs, keyword search across name and description,
  pagination, and a related-products panel. A custom `ProductQuerySet` exposes
  `.available()` and `.search()` so view code stays thin.
- **Cart** — stored in the session, so no login is needed to shop. Line prices are
  captured when the item is added, and quantities are capped at available stock.
  A context processor keeps the header badge in sync on every page.
- **Checkout** — `place_order()` runs inside `transaction.atomic`, locks the affected
  products with `select_for_update()`, re-validates stock, writes `OrderItem` rows with
  `bulk_create`, decrements inventory, and clears the cart. If any line is short,
  the whole order rolls back and nothing is written.
- **Admin** — inventory management with inline order items, editable price/stock
  columns, and `list_select_related` to avoid N+1 queries.
- **Tests** — 41 tests covering model properties, queryset filters, cart arithmetic,
  view responses, and the checkout rollback path.

## Layout

```
config/     project settings and root URLconf
catalog/    Category + Product models, catalog views, seed_catalog command
cart/       session Cart class, add/remove/update views, context processor
orders/     Order + OrderItem models, checkout form, place_order service
templates/  base layout plus per-app templates
static/css/ single stylesheet
```

The checkout logic lives in `orders/services.py` rather than the view, so the
transactional behaviour can be tested without going through HTTP.

## Running it

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py seed_catalog
.venv/Scripts/python.exe manage.py runserver
```

Then open http://127.0.0.1:8000/. Use `seed_catalog --flush` to reset the demo data.

For the admin at `/admin/`, create a superuser first:

```bash
.venv/Scripts/python.exe manage.py createsuperuser
```

## Tests

```bash
.venv/Scripts/python.exe manage.py test
```

## Notes

This is a portfolio project. It runs on SQLite with `DEBUG = True` and a placeholder
`SECRET_KEY`, and it has no payment integration — checkout records an order at status
`PENDING` and stops there. Before deploying anything like it, move the secret key and
database settings into the environment, turn `DEBUG` off, and set the secure-cookie
flags that `manage.py check --deploy` lists.
