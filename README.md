# EcoTrack AI 🌿

EcoTrack AI is a production-grade, highly responsive full-stack web application designed to help individuals calculate, monitor, and reduce their carbon footprint. Featuring a modern glassmorphic interface, interactive dashboards, gamification (green points, streaks, level tiers, achievement badges), interactive quizzes, a community forum, custom report downloads, and a rule-based AI Sustainability Coach (EcoGuide AI).

This project is fully designed and optimized to be submitted to **Hack2Skill PromptWars** as an innovative, real-world, AI-powered environmental solution.

---

## 🚀 Features

1. **Carbon Footprint Calculator**: Detailed multi-step questionnaire tracking **Transportation** (Car, Bike, Bus, Train, Flight), **Home Energy** (Electricity, LPG, AC, appliances), **Food Habits** (Diet type, food wastage), **Shopping** (Clothes, electronics, online deliveries), and **Waste Management** (Plastic, recycling offset, water usage).
2. **Interactive Visual Dashboard**: High-fidelity metrics cards and responsive **Chart.js** trends (Daily, Weekly, Monthly emissions), category donut distributions, and category-wise user vs. regional average comparative benchmarking.
3. **EcoGuide AI Coach**: Interactive chatbot offering carbon footprints explanations, weekly sustainability reduction action plans, predictive emissions forecasting, and eco-friendly recommendations.
4. **Gamification System**: Collect green points (+10 per logged carbon entry, +30 per completed recommendation, +50 per quiz, +5 per community tip). Level up from **Seed** ➡️ **Sapling** ➡️ **Tree** ➡️ **Forest Guardian** ➡️ **Planet Protector** and unlock achievement badges.
5. **Interactive Quizzes**: Take sustainability quizzes to check environmental knowledge and earn green points.
6. **Reporting Center**: Generate and download Daily, Weekly, Monthly, and Annual summary reports in **PDF** (rendered with tables via `reportlab`), **Excel** (via `openpyxl`), and flat **CSV** formats.
7. **Community Forum**: Share tips, like posts, and write comments.
8. **Dark Mode & Glassmorphic Styling**: Sleek, fully responsive design using a CSS variables theme with fluid CSS animations and loading skeletons.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.11, Django, Django REST Framework, SimpleJWT (JWT Authentication)
- **Frontend**: HTML5, CSS3 (Glassmorphism), Tailwind CSS v3 (Responsive utility layer), Chart.js, Font Awesome
- **Reporting**: ReportLab (PDF compiler), OpenPyXL (Excel builder), python CSV standard library
- **Database**: SQLite (Local development), PostgreSQL (Production ready)
- **Deployment**: Docker, Docker Compose, Gunicorn, Nginx

---

## 📐 Carbon Calculation Coefficients

Emissions are calculated using standard regional carbon coefficients (in **kg CO₂** per unit):

### 🚗 Transportation (per km)
- **Petrol Car**: `0.18`
- **Diesel Car**: `0.17`
- **Electric Car (EV)**: `0.05`
- **Motorcycle/Bike**: `0.08`
- **Bus Ride**: `0.03`
- **Train Ride**: `0.02`
- **Flight**: `0.15`

### ⚡ Home Energy
- **Grid Electricity (per kWh)**: `0.50`
- **LPG Cooking Gas (per kg)**: `3.00`
- **Air Conditioning (per hour)**: `0.60`
- **Home Appliances (per hour)**: `0.15`

### 🍕 Food Habits (per day / kg)
- **Vegan Diet**: `1.50` (daily baseline)
- **Vegetarian Diet**: `2.50` (daily baseline)
- **Eggetarian Diet**: `3.20` (daily baseline)
- **Non-Vegetarian Diet**: `5.00` (daily baseline)
- **Food Wastage (per kg)**: `2.50`

### 🛍️ Shopping (per item / shipping)
- **Clothes Items**: `10.00`
- **Electronics devices**: `80.00`
- **Online Delivery shipping**: `2.00`

### ♻️ Waste Management (per kg / kL)
- **Plastic Usage (per kg)**: `6.00`
- **Recycled Waste (per kg)**: `-1.50` (negative emission offset/saving)
- **Water Consumption (per kL / 1000L)**: `0.30`
- **General Trash (per kg)**: `1.00`

---

## 💻 Local Setup & Execution

### Prerequisites
- Python 3.11+
- Pip (Python Package Manager)

### Step 1: Install Dependencies
Open your command terminal in the project root and run:
```bash
pip install -r requirements.txt
```

### Step 2: Database Setup & Seeding
Prepare the local database and seed all default emission coefficients, badges, articles, and quizzes:
```bash
python backend/manage.py makemigrations api
python backend/manage.py migrate
python backend/manage.py seed_data
```
*Note: Seeding automatically creates a superuser account for dashboard access:*
- **Username**: `admin`
- **Password**: `adminpass123`

### Step 3: Run Development Server
Start the local server:
```bash
python backend/manage.py runserver
```
Open your browser and navigate to **`http://127.0.0.1:8000/`** to load the application.

### Step 4: Run Tests
Execute the unit tests verifying calculations and endpoints:
```bash
python backend/manage.py test api
```

---

## 🐳 Docker Production Setup (Compose)

Build and run the entire PostgreSQL, Nginx, and Django server stack in Docker:

```bash
# Build and run containers
docker-compose up --build
```
This launches:
- **Nginx** reverse proxy listening on Port **`80`** (`http://localhost`)
- **Django Gunicorn** app running internally on Port **`8000`**
- **PostgreSQL** database database server running on Port **`5432`**

To stop the containers:
```bash
docker-compose down -v
```

---

## 📡 REST API Specifications

| Method | Endpoint | Description | Permissions |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/auth/register/` | Register new user + welcome bonus | AllowAny |
| **POST** | `/api/auth/login/` | Generate JWT Access/Refresh tokens | AllowAny |
| **GET** | `/api/profile/` | Retrieve/Update profile, avatar, budget | IsAuthenticated |
| **GET** | `/api/analytics/summary/` | Get total CO2, trees saved, scores | IsAuthenticated |
| **GET** | `/api/analytics/history/` | Time series data for dashboards charts | IsAuthenticated |
| **POST** | `/api/carbon/calculate/` | Estimate emissions on-the-fly | IsAuthenticated |
| **POST** | `/api/carbon/entries/` | Create carbon entry + award points | IsAuthenticated |
| **GET** | `/api/carbon/entries/` | Retrieve past calculation entries logs | IsAuthenticated |
| **POST** | `/api/coach/chat/` | Chat with EcoGuide AI Coach | IsAuthenticated |
| **GET** | `/api/recommendations/personalized/` | Get ranked actions based on categories | IsAuthenticated |
| **POST** | `/api/recommendations/<id>/complete/` | Complete recommendations (+30 points) | IsAuthenticated |
| **GET** | `/api/challenges/` | Get available sustainability goals | IsAuthenticated |
| **POST** | `/api/challenges/<id>/join/` | Accept a challenge challenge | IsAuthenticated |
| **POST** | `/api/challenges/<id>/complete/` | Claim reward points for challenge | IsAuthenticated |
| **GET** | `/api/leaderboard/` | Fetch global ranking lists | IsAuthenticated |
| **POST** | `/api/quizzes/<id>/submit/` | Submit quiz answers and score points | IsAuthenticated |
| **POST** | `/api/reports/generate/` | Create & download PDF/Excel/CSV | IsAuthenticated |
| **GET** | `/api/reports/generate/` | Get all past generated report files logs | IsAuthenticated |
| **GET** | `/api/community/posts/` | Fetch forum posts & tips | IsAuthenticated |
| **POST** | `/api/community/posts/` | Share a tip (+5 points) | IsAuthenticated |
| **POST** | `/api/community/posts/<id>/like/` | Toggle like status on post | IsAuthenticated |
| **POST** | `/api/community/posts/<id>/comment/` | Write comment thread on post | IsAuthenticated |
