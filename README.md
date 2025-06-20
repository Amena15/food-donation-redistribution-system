# ♻️ Food Donation and Redistribution System
Food Donation & Redistribution System is a web-based platform developed using the Django framework to tackle the growing issues of food wastage and food insecurity in Malaysia. The system facilitates the complete food donation lifecycle by connecting food donors with recipients and empowering administrators with intelligent tools to manage and optimize redistribution efforts.

## 💻 Tech Stack
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![HTML5](https://img.shields.io/badge/html5-%23E34F26.svg?style=for-the-badge&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/css3-%231572B6.svg?style=for-the-badge&logo=css3&logoColor=white) ![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white) ![SQLite](https://img.shields.io/badge/sqlite-%2307405e.svg?style=for-the-badge&logo=sqlite&logoColor=white)

## 🧠 Key Features
- **Donor Module**: List surplus food with quantity, expiry, and location.
- **Recipient Module**: Browse available items, request food, and track status.
- **Admin Module**: Manage users, approve/reject requests, generate reports.
- **Live Updates**: Observer Pattern for real-time stock and expiry tracking.
- **Modular Architecture**: Built with 5 key design patterns for flexibility:
  - Factory Pattern – Role-based user creation
  - Strategy Pattern – Customizable food-matching algorithms
  - Observer Pattern – Automated updates for food status
  - Singleton Pattern – Centralized app settings
  - Decorator Pattern – Scalable, pluggable notification system

## 🛠️ Use Cases
### Food Donor
- Register an account  
- Log in to the system  
- Add new food listings with quantity, expiry date, and pickup details  
- Edit existing food listings  
- Delete food listings  
- View donation history  
- Update personal profile information  
- Manage pickup schedules for donations  
- Submit feedback about the system  

### Food Recipient
- Register an account  
- Log in to the system  
- Update personal profile information  
- Browse available food listings from donors  
- Submit food requests  
- Track the status of submitted requests  
- Cancel pending food requests  
- Manage pickup schedules for accepted food  
- Confirm pickup upon receiving donations  
- Submit feedback about the donation process  

### Administrator
- Log in to the admin dashboard  
- Manage incoming food requests and transactions  
- Moderate and verify food listings  
- Manage user accounts (donors and recipients)  
- Monitor pickup schedules and fulfillment
- Generate reports on system activities and operations

## 🚀 Run Locally
Prerequisites
- Python 3.8 or newer installed
- Git installed
- Internet connection to install dependencies

1. Clone the Repository
```bash
git clone https://github.com/FarahHanim25/softwaredesign.git
cd softwaredesign
```

2. Set Up Virtual Environment (Recommended)
For Windows:
```bash
python -m venv venv
venv\Scripts\activate
```
For macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install Dependencies
```bash
pip install -r requirements.txt
pip install Django
```
> **Note:** If you get an error with requirements.txt, make sure the file exists or skip to install Django manually.

4. Apply Migrations
```bash
python manage.py migrate
```

5. Run the Development Server
```bash
python manage.py runserver
```

6. Access the App at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

[![](https://visitcount.itsvg.in/api?id=imy1l&icon=0&color=0)](https://visitcount.itsvg.in)
