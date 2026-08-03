# Lumen Supply Co.

Small online storefront. Customers browse the catalogue, leave product reviews, place
orders, track receipts, and open support tickets with attachments.

## Run

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
python run.py
```

The app listens on <http://0.0.0.0:8000>. State lives under `LUMEN_STATE_DIR`
(default `/tmp/lumen-store`) and the database is rebuilt from seed data on every start,
so restarting discards local changes.

## Container

```bash
docker build -t lumen-store .
docker run --rm -p 8000:8000 lumen-store
```

`docker-compose.yml` attaches the service to a fixed address on its own bridge network.

## Layout

```
run.py                      entry point
app/__init__.py             application factory
app/config.py               configuration defaults
app/db.py                   schema and seed data
app/views/catalog.py        storefront and catalogue search
app/views/auth.py           sign-in and session handling
app/views/products.py       product pages and reviews
app/views/orders.py         order history and receipts
app/views/support.py        support tickets and attachments
app/views/checkout.py       cart and checkout
app/store/                  query and persistence helpers
app/static/                 stylesheet and client scripts
```

## Accounts

Seed accounts are created on start; see `app/db.py` for the seed table.
