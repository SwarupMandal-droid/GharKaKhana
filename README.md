# 🍲 GharKhana - Premium Home-Cooked Food Delivery

GharKhana is a high-fidelity, comprehensive food delivery platform built with Django. It bridges the gap between passionate home cooks and food enthusiasts seeking authentic, healthy meals. Engineered with performance and aesthetics in mind, the platform features premium UI interactions, advanced routing algorithms, and a robust end-to-end delivery pipeline.

---

## 🌟 Key Features

### 💎 Premium User Experience
- **Immersive Landing Page**: Built with GSAP for high-performance parallax scrolling, magnetic UI interactions, and dynamic text reveals.
- **Modern Aesthetic**: A meticulously designed interface featuring glassmorphism, responsive layouts, and a clean, premium visual hierarchy.

### 🗺️ Advanced Location & Routing
- **Algorithmic Delivery Routing**: Utilizes the **Haversine formula** for accurate distance calculation and the **Nearest Neighbor** algorithm for optimized delivery pathfinding.
- **Interactive Map Onboarding**: Integrated **Leaflet.js** for interactive map-based location picking, allowing cooks to pinpoint their exact kitchen coordinates effortlessly.

### ⚙️ Robust Business Logic
- **Real-Time Inventory**: Automated stock validation, deduction upon successful orders, and restoration on cancellations.
- **Timezone-Aware Operations**: Strict timezone compliance using Django's timezone utilities ensuring accurate order scheduling (e.g., next-day pre-orders) and reliable metric reporting.

### 👥 Comprehensive Role-Based Ecosystem
- **Customers**: Browse hyper-local cooks, filter by location, place pre-orders, and track delivery status.
- **Cooks**: Interactive dashboards with revenue metrics, real-time order status management, and dynamic menu creation.
- **Delivery Partners**: Optimized delivery dashboards featuring route overviews, actionable contact details, and streamlined order fulfillment workflows.
- **Administrators**: Powerful admin panel for overseeing platform statistics, monitoring orders, and approving cook applications.

### 💳 Seamless Payments
- **UPI & Online Billing**: Secure payment gateway integration via **Razorpay**, supporting UPI and comprehensive billing management.

---

## 🛠️ Technology Stack

- **Backend Framework**: Django 4.2
- **Database**: MySQL
- **Frontend**: HTML5, Vanilla CSS, JavaScript
- **Animations**: GSAP (GreenSock Animation Platform)
- **Mapping**: Leaflet.js
- **Payments**: Razorpay API
- **Architecture**: MVT (Model-View-Template) with Custom User Model (RBAC)

---

## 📦 Installation & Local Setup

### 1. Prerequisites
- Python 3.8+
- MySQL Server

### 2. Clone the Repository
```bash
git clone <your-repository-url>
cd gharkhana
```

### 3. Setup Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install django mysqlclient python-decouple pillow
```

### 5. Environment Configuration
Create a `.env` file in the root directory and configure the following variables:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
DB_NAME=gharkhana_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```

### 6. Database Initialization
Create the MySQL database:
```sql
CREATE DATABASE gharkhana_db;
```

Apply migrations to set up the schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Run the Application
Start the development server:
```bash
python manage.py runserver
```

---

## 📂 Project Architecture

- `accounts/`: RBAC, custom user models, and authentication flows.
- `cooks/`: Menu management, interactive map onboarding, and cook dashboards.
- `orders/`: Cart logic, real-time inventory management, and timezone-aware processing.
- `delivery/`: Haversine/Nearest Neighbor routing and delivery partner dashboard.
- `billing/`: Razorpay integration and automated invoicing.
- `reviews/`: System for customer ratings and feedback.
- `notifications/`: Real-time alerts for state changes.
- `admin_panel/`: Platform oversight and data analytics.
- `templates/`: Modular HTML templates integrating GSAP and Leaflet.
- `static/`: Compiled assets, custom CSS, and vanilla JS logic.

---

## 📄 License
This project is licensed under the MIT License.
