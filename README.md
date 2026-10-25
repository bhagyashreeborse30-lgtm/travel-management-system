# TravelMate – Tourist Management System

A beginner-friendly full-stack tourist management web application built with **Python Flask, SQLite, HTML, CSS and Bootstrap-style responsive CSS**.

## Features

### Visitor / User
- Register and log in securely (passwords are hashed).
- Browse tourist destinations.
- Search destinations by name, city or state.
- Filter destinations by category.
- View destination details, estimated price, duration and map link.
- Submit tour booking requests with visit date and number of visitors.
- View personal booking history and booking status.

### Administrator
- Admin login and dashboard.
- View total users, destinations and bookings.
- Add new tourist destinations.
- Confirm or cancel booking requests.

## Technology stack
- Front end: HTML5, CSS3, Jinja templates
- Back end: Python 3 and Flask
- Database: SQLite
- Authentication: Flask sessions and Werkzeug password hashing

## Installation (Windows / VS Code)

1. Install Python 3.10 or newer.
2. Extract the ZIP file.
3. Open the `TravelMate_Tourist_Management` folder in VS Code.
4. Open Terminal → New Terminal.
5. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

6. Activate it in Windows PowerShell:

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use Command Prompt:

   ```cmd
   venv\Scripts\activate.bat
   ```

7. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

8. Run the project:

   ```bash
   python app.py
   ```

9. Open this address in your browser:

   `http://127.0.0.1:5000`

The SQLite database `travelmate.db` is created automatically the first time the application starts.

## Demo administrator account

- Email: `admin@travelmate.com`
- Password: `Admin@12345`

**Important:** This is a demonstration account for local college-project testing. Change the password and `SECRET_KEY` before deploying the project publicly. Do not upload real passwords, API keys or personal data to GitHub.

## Project structure

```text
TravelMate_Tourist_Management/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── travelmate.db              # created automatically when app runs
│
├── static/
│   └── css/
│       └── style.css
│
└── templates/
    ├── base.html
    ├── home.html
    ├── destinations.html
    ├── destination.html
    ├── login.html
    ├── register.html
    ├── my_bookings.html
    ├── admin.html
    ├── add_destination.html
    ├── about.html
    └── 404.html
```

## Notes
- Destination sample photos are loaded from external Unsplash image URLs, so an internet connection is needed to display them.
- Map links open OpenStreetMap search results.
- This is an educational starter project, not a production-ready travel booking/payment platform. It does not process online payments or book third-party hotels, cabs or guides.
