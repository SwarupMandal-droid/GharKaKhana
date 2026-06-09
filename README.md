# 🍲 GharKhana — Premium Home-Cooked Food Delivery

GharKhana is a high-fidelity, comprehensive food delivery platform built with Django. It bridges the gap between passionate home cooks and food enthusiasts seeking authentic, healthy meals. Engineered with performance and aesthetics in mind, the platform features premium UI interactions, advanced routing algorithms, and a robust end-to-end delivery pipeline.

---

## 🌟 Key Features

### 💎 Premium User Experience
- **Immersive Landing Page**: Built with GSAP for high-performance parallax scrolling, magnetic UI interactions, and dynamic text reveals.
- **Modern Aesthetic**: A meticulously designed interface featuring glassmorphism, responsive layouts, and a clean, premium visual hierarchy.

### 🗺️ Advanced Location & Routing
- **Algorithmic Delivery Routing**: Utilises the **Haversine formula** for accurate distance calculation and the **Nearest Neighbor** algorithm for optimised delivery pathfinding.
- **Interactive Map Onboarding**: Integrated **Leaflet.js** for interactive map-based location picking, allowing cooks to pinpoint their exact kitchen coordinates effortlessly.

### ⚙️ Robust Business Logic
- **Real-Time Inventory**: Automated stock validation, deduction upon successful orders, and restoration on cancellations.
- **Timezone-Aware Operations**: Strict timezone compliance using Django's timezone utilities ensuring accurate order scheduling (e.g., next-day pre-orders) and reliable metric reporting.

### 👥 Comprehensive Role-Based Ecosystem
- **Customers**: Browse hyper-local cooks, filter by location, place pre-orders, and track delivery status.
- **Cooks**: Interactive dashboards with revenue metrics, real-time order status management, and dynamic menu creation.
- **Delivery Partners**: Optimised delivery dashboards featuring route overviews, actionable contact details, and streamlined order fulfillment workflows.
- **Administrators**: Powerful admin panel for overseeing platform statistics, monitoring orders, and approving cook applications.

### 💳 Seamless Payments
- **UPI & Online Billing**: Secure payment gateway integration via **Razorpay**, supporting UPI and comprehensive billing management.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.2 |
| Database | MySQL |
| Frontend | HTML5, Vanilla CSS, JavaScript |
| Animations | GSAP (GreenSock) |
| Mapping | Leaflet.js |
| Payments | Razorpay API |
| Media Storage | Cloudinary |
| Static Files | WhiteNoise |
| WSGI Server | Gunicorn |
| Architecture | MVT + Custom User Model (RBAC) |

---

## 📦 Local Development Setup

### 1. Prerequisites
- Python 3.11+
- MySQL Server

### 2. Clone the Repository
```bash
git clone https://github.com/your-username/gharkhana.git
cd gharkhana
```

### 3. Setup Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Configuration
Copy the example file and fill in your values:
```bash
cp .env.example .env
```

Minimum required variables for local development:
```env
SECRET_KEY=any-random-string
DEBUG=True
DB_NAME=gharkhana_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
RAZORPAY_KEY_ID=rzp_test_xxxx
RAZORPAY_KEY_SECRET=xxxx
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### 6. Database Initialisation
Create the MySQL database:
```sql
CREATE DATABASE gharkhana_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Apply migrations:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Run the Development Server
```bash
python manage.py runserver
```

---

## 🚀 Railway Deployment

### Step 1 — Push to GitHub
Make sure `.env` is **not** committed (it's in `.gitignore`). Push your code:
```bash
git add .
git commit -m "chore: production-ready configuration"
git push origin main
```

### Step 2 — Create a Railway Project
1. Go to [railway.app](https://railway.app) and create a new project.
2. Click **"Deploy from GitHub repo"** and select this repository.

### Step 3 — Add a MySQL Database
1. In your Railway project, click **"+ New"** → **"Database"** → **"MySQL"**.
2. Railway will automatically inject `DATABASE_URL` into your service — no manual config needed.

### Step 4 — Set Environment Variables
In your Railway service, go to **Variables** and add the following:

| Variable | Value |
|---|---|
| `SECRET_KEY` | A strong random string (generate one below) |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `your-app.up.railway.app` |
| `RAILWAY_PUBLIC_DOMAIN` | `your-app.up.railway.app` |
| `CLOUDINARY_CLOUD_NAME` | From [cloudinary.com/console](https://cloudinary.com/console) |
| `CLOUDINARY_API_KEY` | From Cloudinary console |
| `CLOUDINARY_API_SECRET` | From Cloudinary console |
| `RAZORPAY_KEY_ID` | Your Razorpay live/test key |
| `RAZORPAY_KEY_SECRET` | Your Razorpay secret |
| `EMAIL_HOST_USER` | Your Gmail address |
| `EMAIL_HOST_PASSWORD` | Your Gmail App Password |
| `PLATFORM_UPI_ID` | `gharkhana@icici` |

> **Generate a SECRET_KEY:**
> ```bash
> python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
> ```

### Step 5 — Run Migrations on Railway
After deployment, open a Railway shell or use the **"Run command"** feature:
```bash
python manage.py migrate
python manage.py createsuperuser
```

### Step 6 — Done! 🎉
Your app will be live at `https://your-app.up.railway.app`.

---

## 📂 Project Architecture

| Directory | Purpose |
|---|---|
| `accounts/` | RBAC, custom user models, and authentication flows |
| `cooks/` | Menu management, interactive map onboarding, cook dashboards |
| `orders/` | Cart logic, real-time inventory, timezone-aware processing |
| `delivery/` | Haversine/Nearest Neighbor routing, delivery partner dashboard |
| `billing/` | Razorpay integration and automated invoicing |
| `reviews/` | Customer ratings and feedback system |
| `notifications/` | Real-time alerts for state changes |
| `admin_panel/` | Platform oversight and data analytics |
| `templates/` | Modular HTML templates (GSAP + Leaflet) |
| `static/` | CSS, vanilla JS, and image assets |

---

## 📄 License
This project is licensed under the MIT License.
