# Phase 3 Part 2 Frontend

This is a no-build vendor inventory frontend for the Plant Disease Detection
Rover prototype.

It helps the vendor/admin update backend inventory through forms instead of
editing the database or using Swagger manually.

## Features

- Login to the existing Phase 2 backend.
- View inventory.
- Add medicine.
- Edit stock quantity, price, and expiry date.
- Delete medicine.
- Search inventory.
- Import CSV or TSV inventory rows.
- See low-stock, expired, and near-expiry counts.

## Run

Start the backend first:

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend from the workspace root:

```powershell
.\phase3\.venv\Scripts\python.exe -m http.server 5500 -d phase3\frontend
```

Open:

```text
http://localhost:5500
```

## CSV Format

```csv
medicine_name,stock_quantity_kg,price_per_kg,expiry_date
Mancozeb 75% WP,15,220,2026-11-05
Metalaxyl + Mancozeb,8,460,2026-12-15
Neem Cake,40,45,2027-05-01
```

Excel files should be exported as CSV before importing. This keeps the prototype
dependency-free and avoids changing the documented backend schema.

A ready-made sample file is included at `sample_inventory.csv`.
