# 💳 Stripe API Payment Gateway

A fullstack Stripe payment gateway built with **Django REST Framework** on the backend and **vanilla HTML/CSS/JavaScript + Stripe.js** on the frontend. Supports custom payment amounts, real-time card validation, transaction persistence, and a Django Admin panel — all running in Stripe test mode.

---

## 🚀 Live Demo Flow
- **Live Production URL:** [https://stripe-api-fullstack-payment-gateway.onrender.com](https://stripe-api-fullstack-payment-gateway.onrender.com)

```
Customer enters amount & card → Frontend sends to Django API → Stripe processes payment → Transaction saved to DB → Success receipt shown
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|:---|:---|
| **Backend** | Django 6 + Django REST Framework |
| **Payment Processing** | Stripe Python SDK + Stripe.js Elements |
| **Database** | SQLite (via Django ORM) |
| **Frontend** | HTML5 + Vanilla CSS + JavaScript |
| **Environment Config** | python-decouple |
| **CORS** | django-cors-headers |

---

## ✨ Features

- 💰 **Custom payment amounts** — user can enter any amount (min $0.50)
- 💳 **Stripe Elements card UI** — secure, embedded card input
- 📧 **Customer email capture** — stored with each order
- 🧾 **Transaction tracking** — every transaction saved to SQLite with Stripe Payment ID
- 📊 **Django Admin panel** — view, search, and filter all transactions
- ✅ **REST API** — `/orders/` endpoint returns all orders as JSON
- 🔒 **Environment-based secrets** — keys loaded securely from `.env`, never exposed to the client

---

## 📁 Project Structure

```
stripe-api-payment-gateway/
│
├── backend/
│   ├── .env                  # Your Stripe API keys (gitignored)
│   └── .env.example          # Template for setup
│
├── frontend/
│   ├── index.html            # Checkout page
│   ├── success.html          # Payment success receipt
│   ├── style.css             # UI styling (Inter font, indigo design system)
│   └── script.js             # Stripe.js integration + payment logic
│
├── stripegateway/            # Django project
│   ├── manage.py
│   ├── payments/             # Core app
│   │   ├── models.py         # Transaction model
│   │   ├── views.py          # API endpoints
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   └── admin.py
│   └── stripegateway/
│       ├── settings.py
│       └── urls.py
│
├── run.py                    # Cross-platform runner for backend & frontend servers
```

---

## ⚙️ Setup & Installation

### 1. Clone the repo

```bash
git clone https://github.com/PranavHotha/stripe-api-payment-gateway.git
cd stripe-api-payment-gateway
```

### 2. Create & activate virtual environment

```bash
# Windows PowerShell
python -m venv backend/venv
.\backend\venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv backend/venv
source backend/venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django djangorestframework stripe python-decouple django-cors-headers
```

### 4. Configure Stripe API keys

Copy the example env file and add your keys:

```bash
copy backend\.env.example backend\.env
```

Edit `backend/.env`:

```env
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key_here
STRIPE_SECRET_KEY=sk_test_your_secret_key_here
```

> Get your test keys from [dashboard.stripe.com/test/apikeys](https://dashboard.stripe.com/test/apikeys)

### 5. Run database migrations

```bash
cd stripegateway
python manage.py migrate
```

### 6. (Optional) Create admin superuser

```bash
python manage.py createsuperuser
```

---

## ▶️ Running the Project

From the **project root**, start both servers with one command:

```bash
python run.py
```

Or individually:

```bash
python run.py backend     # Django API on http://127.0.0.1:8001
python run.py frontend    # Frontend on  http://127.0.0.1:5500
```

---

## 🌐 Available Endpoints

| Endpoint | Method | Description |
|:---|:---|:---|
| `http://127.0.0.1:5500` | — | Checkout frontend |
| `http://127.0.0.1:8001/` | GET | API landing page |
| `http://127.0.0.1:8001/health/` | GET | Health check |
| `http://127.0.0.1:8001/config/` | GET | Returns publishable key status |
| `http://127.0.0.1:8001/create-payment-intent/` | POST | Creates Stripe PaymentIntent + saves Transaction |
| `http://127.0.0.1:8001/confirm-payment/` | POST | Verifies payment with Stripe & marks status as `succeeded` |
| `http://127.0.0.1:8001/webhook/` | POST | Stripe Webhook listener for asynchronous payment events |
| `http://127.0.0.1:8001/transactions/` | GET | Lists all transactions (JSON) |
| `http://127.0.0.1:8001/orders/` | GET | Alias for `/transactions/` |
| `http://127.0.0.1:8001/admin/` | — | Django Admin panel |

---

## 💳 Stripe Test Cards

| Card Number | Scenario |
|:---|:---|
| `4242 4242 4242 4242` | ✅ Successful payment |
| `4000 0000 0000 9995` | ❌ Insufficient funds |
| `4000 0000 0000 0069` | ❌ Expired card |
| `4000 0000 0000 0127` | ❌ Incorrect CVC |
| `4000 0000 0000 0002` | ❌ Generic decline |

> Use any future expiry date (e.g. `12/28`) and any 3-digit CVC (e.g. `123`)

---

## 📦 `create-payment-intent` API — Request & Response

**Request** `POST /create-payment-intent/`
```json
{
  "amount": 3500,
  "email": "customer@example.com"
}
```

**Response**
```json
{
  "clientSecret": "pi_xxx_secret_xxx",
  "transactionId": 42,
  "orderId": 42
}
```

---

## 🧑‍💼 Django Admin

Access at `http://127.0.0.1:8001/admin/` — view, search, and filter all customer transactions with full Stripe Payment ID, amount, status, email, and timestamp.

---

## 📝 License

MIT — free to use, modify, and distribute.
