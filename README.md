# Bazaro: Django REST + React e-commerce

> **Brand:** Bazaro — The Local Market, Reimagined.
> **Status:** Running. Backend at `http://127.0.0.1:8000/`, frontend at `http://localhost:5175/` (port may vary).

## Features implemented
Auth (token), categories, products with search / category / price / rating / stock filters and sorting, cart with stock-checked quantities, wishlist, saved addresses, checkout creating orders with server-calculated totals, price snapshots and row-locked stock decrement, order history, Razorpay order creation + HMAC signature verification (labelled DEMO mode without keys), admin API (products, orders, stats) plus Django admin, seed command, tests.

## Not implemented (limitations)
Product variants/sizes, reviews, profile editing page, custom admin dashboard UI (use `/admin/` and `/api/admin/*`), Docker, committed migrations, order cancellation/stock restock for abandoned unpaid orders, order-status tracking UI beyond the status label.

## Setup
```bash
cp .env.example .env            # edit values; leave DB_NAME empty for SQLite
cd backend && python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py makemigrations shop   # migrations are NOT included
python manage.py migrate
python manage.py seed                   # sample data + admin/admin12345 (change it)
python manage.py test shop
python manage.py runserver              # http://localhost:8000
# new terminal
cd frontend && npm install && npm run dev   # http://localhost:5173
```
PostgreSQL: `createdb store`, then set `DB_NAME=store` and credentials in `.env`.
Razorpay test mode: put test `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` in `.env`; without them checkout uses a clearly labelled demo confirmation.

## Product photos and detail pages (v2)
New route `/products/:id` (breadcrumb, gallery, quantity, cart/wishlist, similar products). New API: `GET /api/products/<id>/similar/`; products now include a `gallery` list of absolute image URLs.
After updating run `python manage.py makemigrations shop && python manage.py migrate` (adds `ProductImage` for extra gallery photos, editable inline in `/admin/`).
Photos: `python manage.py fetch_images` fills **only products without an image** (never overwrites). It first uses `backend/seed_images/<slug>.jpg` if you put one there, else searches Wikimedia Commons for openly licensed images (credits go to `seed_images/ATTRIBUTION.txt`). Matches can be imperfect, so review them and replace via `/admin/`. Uploaded media is served from `/media/` in development.

## Homepage, shops and sample data (v3)
New: Shops (`GET /api/shops/`, `/api/shops/<id>/`, `/api/products/?shop=<id>`), category and shop images, `mrp` (strike-through price), 28 sample products in 6 categories sold by 4 sample shops. Clickable: category tiles, shop cards (`/shops/:id`), product cards (`/products/:id`).
Update steps: `python manage.py makemigrations shop && python manage.py migrate && python manage.py seed && python manage.py fetch_images`. Seed and fetch_images are safe to re-run and never overwrite existing images. Shop names and listings are fictional sample data.

## API
`POST /api/auth/register|login|logout/` · `GET /api/products/?q=&category=&min_price=&max_price=&min_rating=&in_stock=true&ordering=price_asc|price_desc|popular|rating|newest` · `GET /api/categories/` · `/api/cart/` `/api/wishlist/` `/api/addresses/` (CRUD, own data only) · `POST /api/orders/ {address_id}` · `GET /api/orders/` · `POST /api/payments/initiate/ {order_id}` · `POST /api/payments/verify/` · admin only: `/api/admin/products/`, `/api/admin/orders/`, `GET /api/admin/stats/`.

## Production notes
Set `DJANGO_DEBUG=False`, a strong secret, real `ALLOWED_HOSTS`/`CORS_ORIGINS`, serve media/static via a web server, run behind HTTPS.
