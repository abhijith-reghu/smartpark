# SmartPark

A real-time parking availability and navigation system.

SmartPark shows drivers the nearest free parking slot and which direction to go. Staff update slots with one click, and a dashboard shows live statistics.

## Pages

- **Login** - staff login
- **Staff Panel** - click a slot to mark it free or occupied
- **Entrance Display** - shows the recommended slot, direction and a QR code
- **Driver page** (`/driver`) - opened by scanning the QR code; holds the recommended slot for 10 minutes
- **Admin Dashboard** - shows total, available and occupied slots

## Built With

Python, Flask, SQLite, HTML, CSS, JavaScript

## How to Run

1. Install the packages: `pip install -r requirements.txt`
2. (Optional) set a password and secret key:
   - Windows (PowerShell): `$env:ADMIN_PASSWORD="your-password"; $env:SECRET_KEY="any-long-random-text"`
   - Mac/Linux: `export ADMIN_PASSWORD=your-password SECRET_KEY=any-long-random-text`
3. Open a terminal in the `backend` folder and run: `python app.py`
4. Open `http://127.0.0.1:5000/login` in your browser

Demo login: username `admin`. If `ADMIN_PASSWORD` is not set, the demo password is `admin123` (change it before deploying). The admin account is created the first time the database is made, so to change the password later, delete `database/smartpark.db` and start the app again.

## QR code on your phone

The QR code only appears when the entrance display is opened using your computer's Wi-Fi address (for example `http://192.168.1.10:5000/entrance-display`), not `localhost`. Your phone must be on the same Wi-Fi.
