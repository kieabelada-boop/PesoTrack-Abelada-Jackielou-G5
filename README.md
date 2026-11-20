# CSIT327-G5-Abelada-Jackielou-FirstDjango

Jackielou C. Abelada
G5

# PesoTrack

**PesoTrack** is a Django web application designed for small resellers and sari-sari store owners to monitor wholesale purchasing costs, compare store/supplier prices, track weighted average unit costs, and protect retail profit margins.

## Core Features

1. **Product & Purchase-Price Tracking:**
   - Full Create, Read, Update, and Delete (CRUD) workflows for retail products (`Product`) and supplier purchase records (`PriceRecord`) with strict user-level data isolation.
   - Automatic calculation of unit profit, profit margin %, markup %, price shifts ($\Delta C$ and percentage change), automated low-margin/loss dashboard alert banners, and one-click suggested selling price recovery.

2. **Supplier & Store Price Comparison:**
   - Batch quantity tracking (`quantity` per purchase record) to compute total units purchased, total purchase spend, and weighted average purchasing cost ($\frac{\sum (C_i \times Q_i)}{\sum Q_i}$).
   - Product-level comparison (`product_detail.html`) and catalog-wide store matrix (`compare_suppliers.html`) highlighting the `LOWEST` supplier price, price difference vs. lowest cost, and unit savings potential across stores.
   - Interactive modals in the product overview for logging new purchase batches and adjusting retail selling prices with live margin recalculation.

3. **Authentication, Roles & Dashboards:**
   - User registration, login, logout, and profile management with `@login_required` protection and role-restricted views for Small Reseller and Admin roles.

## Tech Stack

- **Backend:** Python, Django
- **Database:** PostgreSQL / Supabase
- **Frontend:** HTML5, CSS3, Bootstrap 5

## Setup & Run Instructions

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/kieabelada-boop/PesoTrack-Abelada-Jackielou-G5.git](https://github.com/kieabelada-boop/PesoTrack-Abelada-Jackielou-G5.git)
   cd PesoTrack-Abelada-Jackielou-G5
