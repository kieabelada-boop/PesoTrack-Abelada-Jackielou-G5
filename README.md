# CSIT327-G5-Abelada-Jackielou-FirstDjango

Jackielou C. Abelada  
G5

# PesoTrack

**PesoTrack** is a full-stack Django web application designed for small resellers and sari-sari store owners to monitor wholesale purchasing costs, compare store/supplier prices, track weighted average unit costs, and protect retail profit margins.

## Core Features

1. **Product & Purchase-Price Tracking:**
   - Full Create, Read, Update, and Delete (CRUD) workflows for retail products (`Product`) and supplier purchase records (`PriceRecord`) with strict user-level data isolation.
   - Server-side validation enforcing positive prices, valid margin thresholds (`0%–100%`), non-future purchase dates, positive batch quantities, and unique product names per store owner.
   - Automatic calculation of unit profit, profit margin %, markup %, price shifts, automated low-margin/loss dashboard alert banners, and one-click suggested selling price recovery.

2. **Supplier & Store Price Comparison:**
   - Batch quantity tracking (`quantity` per purchase record) to compute total units purchased, total purchase spend, and weighted average purchasing cost.
   - Product overview (`product_detail.html`) with **Compare stores** and **Purchase history** tabs highlighting the `LOWEST` supplier price, price difference vs. lowest cost, and unit savings potential across stores.
   - Interactive modals in the product overview for logging new purchase batches and adjusting retail selling prices with live margin recalculation.

3. **Authentication, Roles & Hardening:**
   - User registration, login, logout, and profile management with `@login_required` protection and view-level role enforcement (`Small Reseller` and `Administrator`).
   - Single-admin registration enforcement and automatic Django Admin (`/admin/`) connection for the Administrator account.
   - Dedicated Administrator Dashboard focused strictly on monitoring registered small resellers and store owners.
   - Atomic multi-step database transactions (`transaction.atomic()`), CSRF protection, POST-only mutations/deletions with confirmation pages, and custom `404` / `500` error pages.

## Tech Stack

- **Backend:** Python, Django 6.1.2
- **Database:** PostgreSQL (Supabase)
- **Frontend:** Django Templates, HTML5, CSS3, Bootstrap 5

## Setup & Run Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kieabelada-boop/PesoTrack-Abelada-Jackielou-G5.git
   cd PesoTrack-Abelada-Jackielou-G5
   ```

2. **Create and activate a virtual environment:**
   - **Windows (PowerShell):**
     ```powershell
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   Copy `.env.example` to `.env` and fill in your values (keep `.env` out of version control — it is listed in `.gitignore`):
   ```bash
   cp .env.example .env
   ```
   Required variables in `.env`:
   - `SECRET_KEY` — Django secret key
   - `DEBUG` — `True` for local development, `False` for production
   - `ALLOWED_HOSTS` — Comma-separated list of allowed hosts (e.g. `localhost,127.0.0.1`)
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` — PostgreSQL / Supabase connection settings

5. **Apply database migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver
   ```
   Open [http://127.0.0.1:8000/](http://127.0.0.1:8000/) in your browser.

## Running Automated Tests

PesoTrack includes **31 automated Django test cases** (`20` in `products` and `11` in `accounts`) covering core CRUD operations, profit-margin and supplier-comparison calculations, valid and invalid form inputs, login requirements, cross-user record isolation (`404` enforcement), role-based access control, single-admin enforcement, and custom `404` error handling.

- **Run the entire test suite:**
  ```bash
  python manage.py test
  ```
- **When running against Supabase / managed PostgreSQL (recommended if test DB teardown is restricted):**
  ```bash
  python manage.py test --keepdb
  ```
- **Run tests for a specific app:**
  ```bash
  python manage.py test products
  python manage.py test accounts
  ```
- **Run with verbose output:**
  ```bash
  python manage.py test --keepdb -v 2
  ```
