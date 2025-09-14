from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import csv
import json
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, session, flash
import datetime
import random
app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
USER_CSV = "users.csv"
AGENCY_CSV = "agencies.csv"
PACKAGE_CSV = "PACKAGE_CSV.csv"
# Ensure directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
UPLOAD_FOLDER = os.path.join('static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




# Ensure the upload directory exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
def check_csv_exists(file_path, headers):
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(headers)  # Add column headers

# Check if files exist before running the app
check_csv_exists("users.csv", ["user_id", "name", "address", "contact", "email", "password"])
check_csv_exists("agencies.csv", ["agent_name", "city", "budget", "contact", "email"])
check_csv_exists("PACKAGE_CSV.csv", ["agent_name", "package_name", "tourist_place", "contact", "email", "places", "days_count", "weather", "budget", "images"])


### ---------- HOME ROUTE ---------- ###
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

### ---------- USER REGISTRATION ---------- ###
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        user_data = {
            "user_id": request.form.get('user_id', '').strip(),
            "name": request.form.get('name', '').strip(),
            "address": request.form.get('address', '').strip(),
            "contact": request.form.get('contact', '').strip(),
            "email": request.form.get('email', '').strip(),
            "password": request.form.get('password', '').strip(),
        }

        if not all(user_data.values()):
            flash("All fields are required!", "warning")
            return redirect(url_for('register'))

        if len(user_data["contact"]) != 10 or not user_data["contact"].isdigit():
            flash("Invalid Contact Number! Must be 10 digits.", "danger")
            return redirect(url_for('register'))

        if "@" not in user_data["email"] or "." not in user_data["email"]:
            flash("Invalid Email Address!", "danger")
            return redirect(url_for('register'))

        file_exists = os.path.exists(USER_CSV)
        with open(USER_CSV, 'a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=user_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(user_data)

        flash("Registration successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

### ---------- USER LOGIN ---------- ###
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id', '').strip()
        password = request.form.get('password', '').strip()

        with open(USER_CSV, 'r', newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row['user_id'] == user_id and row['password'] == password:
                    session['user'] = user_id
                    flash("Login successful!", "success")
                    return redirect(url_for('dashboard'))

        flash("Invalid credentials! Try again.", "danger")
        return redirect(url_for('login'))

    return render_template('login.html')

### ---------- USER DASHBOARD ---------- ###
@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    agencies = []
    if request.method == 'POST':
        place = request.form.get('place', '').strip()
        budget = request.form.get('budget', '0').strip()

        if place and budget.isdigit():
            agencies = get_agencies_from_csv(place, int(budget))

        return render_template('user_view_packages.html', packages=agencies)  # Redirect to view packages page

    return render_template('dashboard.html', agencies=agencies)


def get_agencies_from_csv(place, budget):
    agencies = []
    try:
        with open(PACKAGE_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print("CSV Row:", row)  # Debugging print

                # Extract necessary fields
                package_place = row.get('tourist_place', '').strip()
                package_budget = row.get('budget', '0').strip()
                agent_name = row.get('agent_name', 'N/A').strip()
                contact = row.get('contact', 'N/A').strip()
                email = row.get('email', 'N/A').strip()
                places = row.get('places', '').strip().split(';')
                days_count = row.get('days_count', 'N/A').strip()
                weather = row.get('weather', 'N/A').strip()
                images = row.get('images', '').strip().split(';')

                # Validate budget
                if not package_budget.isdigit():
                    print(f"Skipping invalid budget: {package_budget}")
                    continue

                # Match based on place and budget
                if package_place.lower() == place.lower() and int(package_budget) <= budget:
                    agencies.append({
                        "agent_name": agent_name,
                        "package_name": row.get('package_name', 'N/A'),
                        "tourist_place": package_place,
                        "contact": contact,
                        "email": email,
                        "places": places,
                        "days_count": days_count,
                        "weather": weather,
                        "budget": package_budget,
                        "images": images
                    })

    except FileNotFoundError:
        print("PACKAGE_CSV.csv file not found.")

    return agencies

@app.route('/view_packages')
def user_view_packages():
    packages = []
    try:
        with open(PACKAGE_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                packages.append({
                    "package_name": row["package_name"],
                    "agent_name": row["agent"],
                    "tourist_place": row["tourist_place"],
                    "contact": row["contact"],
                    "weather": row["weather"],
                    "days_count": row["days_count"],
                    "budget": row["budget"],
                    "images": row["images"].split(";") if row["images"] else []
                })
    except FileNotFoundError:
        print("Error: PACKAGE_CSV.csv not found.")

    return render_template("user_view_packages.html", packages=packages)


### ---------- PAYMENT ---------- ###
@app.route('/payment/<package_name>', methods=['GET', 'POST'])
def payment(package_name):
    booking_id = f"BK{random.randint(100000, 999999)}"
    booking_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    package_amount = "Not Available"

    # ✅ **Fetch package amount from CSV correctly**
    try:
        with open(PACKAGE_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(f"Checking row: {row}")  # Debugging
                if row["package_name"].strip().lower() == package_name.strip().lower():
                    package_amount = row["budget"].strip()  # Extract and clean budget
                    print(f"Found package: {package_name} - Amount: {package_amount}")  # Debugging
                    break
    except FileNotFoundError:
        print("Error: PACKAGE_CSV.csv not found.")

    if request.method == 'POST':
        return render_template("payment.html", package_name=package_name, booking_id=booking_id, booking_date=booking_date, package_amount=package_amount, success=True)

    return render_template("payment.html", package_name=package_name, booking_id=booking_id, booking_date=booking_date, package_amount=package_amount, success=False)

### ---------- USER LOGOUT ---------- ###
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

### ---------- AGENT REGISTRATION (STORE IN CSV) ---------- ###
@app.route('/agent/register', methods=['GET', 'POST'])
def agent_register():
    if request.method == 'POST':
        agent_name = request.form.get('agent_name', '').strip()
        password = request.form.get('password', '').strip()

        if not agent_name or not password:
            flash("Agent name and password cannot be empty.", "warning")
            return redirect(url_for('agent_register'))

        # Save agent credentials in CSV
        with open(AGENCY_CSV, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([agent_name, password])

        flash("Agent registration successful! Please log in.", "success")
        return redirect(url_for('agent_login'))

    return render_template('agent_register.html')

### ---------- AGENT LOGIN ---------- ###
@app.route('/agent/login', methods=['GET', 'POST'])
def agent_login():
    if request.method == 'POST':
        agent_name = request.form.get('agent_name', '').strip()
        password = request.form.get('password', '').strip()

        with open(AGENCY_CSV, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if row and row[0] == agent_name and row[1] == password:
                    session['agent'] = agent_name
                    flash("Agent login successful!", "success")
                    return redirect(url_for('agent_dashboard'))

        flash("Invalid credentials! Try again.", "danger")
        return redirect(url_for('agent_login'))

    return render_template('agent_login.html')

### ---------- AGENT DASHBOARD (View Own Packages) ---------- ###
@app.route('/agent/dashboard', methods=['GET', 'POST'])
def agent_dashboard():
    if 'agent' not in session:
        flash("Please log in to access the agent dashboard.", "warning")
        return redirect(url_for('agent_login'))

    agent_name = session['agent']
    packages = get_agent_packages(agent_name)

    if request.method == 'POST':
        package_name = request.form.get('package_name', '').strip()
        tourist_place = request.form.get('tourist_place', '').strip()
        contact = request.form.get('contact', '').strip()
        email = request.form.get('email', '').strip()
        places = request.form.get('places', '').strip()
        days_count = request.form.get('days_count', '').strip()
        weather = request.form.get('weather', '').strip()
        budget = request.form.get('budget', '').strip()

        if not package_name or not tourist_place or not budget.isdigit() or not days_count.isdigit():
            flash("Invalid input. Please enter valid details.", "warning")
            return redirect(url_for('agent_dashboard'))

        budget = int(budget)
        days_count = int(days_count)
        places_list = [p.strip() for p in places.split(",") if p.strip()]

        # Handle file uploads safely
        images = []
        if 'place_images' in request.files:
            files = request.files.getlist('place_images')
            for file in files:
                if file.filename:
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    file.save(filepath)
                    images.append(filename)

        # Save data to CSV
        file_exists = os.path.exists(PACKAGE_CSV)
        with open(PACKAGE_CSV, 'a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["agent_name", "package_name", "tourist_place", "contact", "email", "places", "days_count", "weather", "budget", "images"])
            writer.writerow([agent_name, package_name, tourist_place, contact, email, ";".join(places_list), days_count, weather, budget, ";".join(images)])


        flash("Package added successfully!", "success")
        return redirect(url_for('agent_dashboard'))

    return render_template('agent_dashboard.html', packages=packages)

### ---------- FETCH AGENT'S OWN PACKAGES ---------- ###
def get_agent_packages(agent_name):
    packages = []
    if os.path.exists(PACKAGE_CSV):
        with open(PACKAGE_CSV, 'r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                print(f"Checking package: {row}")  # Debugging
                
                # Validate row data
                if not row.get("package_name") or not row.get("tourist_place"):
                    print(f"Skipping invalid row: {row}")
                    continue

                # Ensure proper data types
                budget = row.get("budget", "0")
                if not budget.isdigit():
                    print(f"Skipping package due to invalid budget: {row}")
                    continue

                days_count = row.get("days_count", "0")
                if not days_count.isdigit():
                    print(f"Skipping package due to invalid days_count: {row}")
                    continue

                # Ensure list conversion
                places = row.get("places", "").split(";") if row.get("places") else []
                images = row.get("images", "").split(";") if row.get("images") else []

                # Append valid package
                packages.append({
                    "package_name": row["package_name"],
                    "tourist_place": row["tourist_place"],
                    "contact": row.get("contact", "N/A"),
                    "email": row.get("email", "N/A"),
                    "places": places,
                    "days_count": days_count,
                    "weather": row.get("weather", "Unknown"),
                    "budget": budget,
                    "images": row.get("images", "").split(";") if row.get("images") else []
                })
    
    print(f"Packages found for {agent_name}: {packages}")  # Debugging output
    return packages



### ---------- AGENT VIEW PACKAGES (Only Own) ---------- ###
@app.route('/agent/view_packages')
def view_packages():
    if 'agent' not in session:
        flash("Please log in to view your packages.", "warning")
        return redirect(url_for('agent_login'))

    agent_name = session['agent']
    print(f"Logged in agent: {agent_name}")  # Debugging
    
    packages = get_agent_packages(agent_name)
    
    return render_template('view_packages.html', packages=packages)


### ---------- FILE UPLOAD HANDLER ---------- ###
@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles file uploads for packages."""
    if 'file' not in request.files:
        flash('No file part', 'danger')
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(request.url)

    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        flash('File successfully uploaded', 'success')
        return redirect(url_for('view_packages'))

### ---------- AGENT LOGOUT ---------- ###
@app.route('/agent/logout')
def agent_logout():
    session.pop('agent', None)
    flash("Agent logged out successfully.", "info")
    return redirect(url_for('agent_login'))

if __name__ == '__main__':
    app.run(debug=False)