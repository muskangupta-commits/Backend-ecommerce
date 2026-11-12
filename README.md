# Cartify Backend API

Cartify is a FastAPI backend for an e-commerce application. It uses MongoDB for
persistent storage and supports customer authentication, product/catalog
management, carts, orders, and optional Stripe payments.

## Requirements

- Python 3.10 or later (Python 3.13 is supported)
- MongoDB, either a local server or a MongoDB Atlas database
- Stripe test keys only if you want to test online payments

## Windows setup (PowerShell)

Run these commands from the `backend-ecommerce-main` directory:

```powershell
py --version
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

If PowerShell blocks virtual-environment activation, either allow local scripts
for your user with
`Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`, or run
the venv's Python directly:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

## macOS/Linux setup

Run these commands from the `backend-ecommerce-main` directory:

```sh
python3 --version
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

## Environment configuration

Edit `.env` before starting the API:

1. Set `MONGODB_URI` to your local MongoDB URI or Atlas connection string.
   The example file uses local MongoDB at `mongodb://localhost:27017`.
2. Set `TOKEN_ENCRYPTION_KEY` to a new 64-character hexadecimal key. Generate
   one with `py -c "import secrets; print(secrets.token_hex(32))"` on Windows or
   `python3 -c "import secrets; print(secrets.token_hex(32))"` on macOS/Linux,
   then paste the output into `.env`. Changing this key invalidates existing
   login tokens.
3. Keep `DEMO_OTP_ENABLED=true` only for local development. The demo OTP is not
   a real SMS/email delivery service and must not be used in production.
4. Leave the Stripe values empty to disable online payments. To test online
   payments, use Stripe test keys; never put live keys in a development setup.
5. Keep `.env` private. It is ignored by Git; do not paste its contents into
   issues, screenshots, or source files.

When MongoDB is unavailable, the current backend falls back to an in-memory
demo database. Its data is temporary and is lost when the process stops. Use a
reachable MongoDB instance if you need persistent data.

## Run the API

From the backend directory, with the virtual environment active:

```powershell
python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

Without activating the venv on Windows:

```powershell
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The API is available at:

- Base URL: <http://127.0.0.1:8000/api/v1>
- Health check: <http://127.0.0.1:8000/health>
- Swagger UI: <http://127.0.0.1:8000/docs>

## Main endpoints

- `POST /api/v1/auth/send-otp` and `POST /api/v1/auth/verify-otp`
- `GET /api/v1/products` and `GET /api/v1/products/{id}`
- `GET`, `POST`, `PUT`, and `DELETE /api/v1/cart`
- `POST /api/v1/orders` and `GET /api/v1/orders/my-orders`
- `GET /api/v1/admin/dashboard` (admin only)
- `GET /api/v1/payments/config`
- `POST /api/v1/payments/create-intent` and `POST /api/v1/payments/verify`

## Notes

- The demo OTP flow is intended for local development; no OTP delivery
  provider is configured by this project.
- Online payments require valid Stripe configuration. Payment verification
  must succeed with Stripe before an online order can be marked paid.
- Product seeding can request the public DummyJSON catalog during startup. If
  that request is unavailable, the bundled demo products are still used.
