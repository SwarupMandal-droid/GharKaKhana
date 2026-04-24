# Gharkhana - Home Cooked Food Delivery Platform

Gharkhana is a comprehensive home-cooked food delivery platform built with Django. It connects passionate home cooks with customers seeking authentic, healthy, and homemade meals. The platform manages the entire lifecycle of an order, from discovery to delivery.

## 🚀 Features

### 👤 User Roles
- **Customers**: Browse menus, filter by location, place orders, and track deliveries.
- **Cooks**: Manage their profile, list dishes, set prices, and handle incoming orders.
- **Delivery Partners**: Accept delivery tasks and ensure timely meal fulfillment.
- **Admin**: Oversee platform operations, manage users, and handle billing.

### 🍱 Core Functionality
- **Cook Discovery**: Search for cooks based on proximity and ratings.
- **Order Management**: Real-time order tracking and status updates.
- **Menu Management**: Dynamic menu creation for cooks with dish descriptions and pricing.
- **Reviews & Ratings**: Transparency and quality control through customer feedback.
- **Notifications**: Integrated notification system for order updates and alerts.
- **Billing & Payments**: Integrated billing module (with Razorpay support).

## 🛠️ Tech Stack
- **Backend**: Django 4.2
- **Database**: MySQL
- **Frontend**: HTML5, Vanilla CSS, JavaScript
- **Payments**: Razorpay Integration
- **Auth**: Custom User Model with Role-based Access Control (RBAC)

## 📦 Installation & Setup

### 1. Prerequisite
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
Create a `.env` file in the root directory and add the following:
```env
SECRET_KEY=your_django_secret_key
DEBUG=True
DB_NAME=gharkhana_db
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
```

### 6. Database Setup
Create a MySQL database named `gharkhana_db`:
```sql
CREATE DATABASE gharkhana_db;
```

### 7. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Start Development Server
```bash
python manage.py runserver
```

## 📂 Project Structure
- `accounts/`: User authentication and profile management.
- `cooks/`: Menu management and cook-specific logic.
- `orders/`: Cart functionality and order processing.
- `delivery/`: Logistics and delivery partner workflows.
- `billing/`: Invoicing and payment integration.
- `reviews/`: Rating and feedback system.
- `notifications/`: User alert system.
- `templates/`: HTML templates organized by application.
- `static/`: CSS, JS, and image assets.

## 📄 License
This project is licensed under the MIT License.
