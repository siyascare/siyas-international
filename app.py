from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from datetime import datetime
from bson import ObjectId
import pymongo
import random
import requests
import resend
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "siyas_secret_super_key"

# ===== UPLOAD =====
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ===== WHATSAPP =====
ACCESS_TOKEN = "EAAPZCjepv8K0BR3LVZAJ1P9a71wmtvljDrc1RWsDrLfAteuTwzBMNOV5BIXV8RgCCm2lJTczaYlgmR4fw4vQYSAvZBZBLEx2BwOXuFGYO5TaBt4kvbvsddzm7sJmoFH616XATUn41f2ge0Mxn9PYWFZB1gHs5IUQJgIrutLXJbnAvOUutGhXyZB9ZBPyJiU0vXHe2P8n3i8YwREDDTZCfqKlqM4TQyjLtDNwDf79Nd5n"
PHONE_NUMBER_ID = "1125409918808237"
VERSION = "v20.0"
WA_URL = f"https://graph.facebook.com/{VERSION}/{PHONE_NUMBER_ID}/messages"

# ===== EMAIL =====
EMAIL_SENDER = "siyas.care@gmail.com"
OWNER_EMAIL = "siyas.care@gmail.com"

# ===== DATABASE =====
client = pymongo.MongoClient("mongodb+srv://vidhi:Vidhi12@cluster0.lpjthfz.mongodb.net/?appName=Cluster0")
db = client["siyas_database"]
form1_collection = db["form1_records"]
form2_collection = db["form2_records"]

# ===== LOGIN =====
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"
ENGINEER_PASSWORD = "engineer123"

# ===== EMAIL FUNCTION =====
def send_email(to_email, subject, body):
    if not to_email:
        return
    try:
        resend.api_key = os.environ.get("RESEND_API_KEY")
        resend.Emails.send({
            "from": "Siya's International <onboarding@resend.dev>",
            "to": ["siyas.care@gmail.com"],
            "subject": subject,
            "text": body,
        })
        print(f"Email sent!")
    except Exception as e:
        print(f"Email failed: {e}")
        


# ===== WHATSAPP FUNCTION =====
def send_whatsapp(to_number, message_body):
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to_number, "type": "text", "text": {"body": message_body}}
    response = requests.post(WA_URL, headers=headers, json=payload)
    return response.json()

# ===== NOTIFICATION =====
def send_notification(contact, email, message, subject="Notification"):
    try:
        result = send_whatsapp(contact, message)
        if "error" in result:
            send_email(email, subject, message)
        else:
            print("WhatsApp sent")
    except Exception as e:
        print(f"WA error: {e}")
        send_email(email, subject, message)

# ===== DECORATORS =====
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("staff_login_page"))
        return f(*args, **kwargs)
    return wrapper

def engineer_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("engineer_logged_in"):
            return redirect(url_for("engineer_login_page"))
        return f(*args, **kwargs)
    return wrapper

# ===== ROUTES =====
@app.route("/")
def home():
    return redirect(url_for("booking_page"))

@app.route("/booking")
def booking_page():
    return render_template("booking.html")

@app.route("/tracking")
def tracking_page():
    return render_template("tracking.html")

@app.route("/chalan")
def chalan_page():
    count = form2_collection.count_documents({}) + 1
    serial_no = str(count).zfill(3)
    return render_template("chalan.html", serial_no=serial_no)

# ===== BOOKING SUBMIT =====
@app.route("/submit-booking", methods=["POST"])
def submit_booking():
    data = {
        "fullname":    request.form.get("fullname"),
        "contact":     request.form.get("contact"),
        "email":       request.form.get("email"),
        "brand":       request.form.get("brand"),
        "issue":       request.form.get("issue"),
        "description": request.form.get("description"),
        "status":      "Unseen",
        "admin_note":  "",
        "created_at":  datetime.now(),
        "is_deleted":  False
    }
    form1_collection.insert_one(data)
    send_notification(data["contact"], data["email"],
        f"Hi {data['fullname']}, your booking is received! We'll call you shortly. - Siya's International",
        "Booking Confirmation")
    send_email(OWNER_EMAIL, "New Booking Received!",
        f"New Booking!\n\nName: {data['fullname']}\nContact: {data['contact']}\nBrand: {data['brand']}\nIssue: {data['issue']}\nDescription: {data['description']}")
    flash("Booking submitted successfully!")
    return redirect(url_for("booking_page"))


# ===== CHALAN SUBMIT =====
@app.route("/submit-chalan", methods=["POST"])
def submit_chalan():
    tracking_no = "TRK" + str(random.randint(10000, 99999))

    photo_filename = None
    if 'device_photo' in request.files:
        photo = request.files['device_photo']
        if photo and photo.filename != '' and allowed_file(photo.filename):
            filename = secure_filename(f"{tracking_no}_{photo.filename}")
            photo.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            photo_filename = filename

    parts = request.form.getlist("parts")
    data = {
        "name":             request.form.get("name"),
        "contact":          request.form.get("contact"),
        "email":            request.form.get("email"),
        "tracking_no":      tracking_no,
        "serial_no":        request.form.get("serial_no"),
        "date":             request.form.get("date"),
        "product_type":     request.form.get("product_type"),
        "brand":            request.form.get("brand"),
        "model_no":         request.form.get("model_no"),
        "body_damaged":     request.form.get("body_damaged"),
        "tray_no":          request.form.get("tray_no"),
        "problem":          request.form.get("problem"),
        "password":         request.form.get("password"),
        "analysis_charge":  request.form.get("analysis_charge") or "0",
        "estimate_charge":  request.form.get("estimate_charge") or "0",
        "parts":            ", ".join(parts) if parts else "",
        "device_photo":     photo_filename,
        "status":           "Received",
        "assigned_engineer":"",
        "admin_note":       "",
        "bill_generated":   False,
        "bill_items":       [],
        "created_at":       datetime.now(),
        "is_deleted":       False
    }
    form2_collection.insert_one(data)
    send_notification(data["contact"], data["email"],
        f"Hi {data['name']}, device received! Tracking No: {tracking_no} - Siya's International",
        "Device Received")
    send_email(OWNER_EMAIL, "New Device Received!",
        f"Name: {data['name']}\nContact: {data['contact']}\nTracking: {tracking_no}\nBrand: {data['brand']}\nProblem: {data['problem']}")
    flash(f"Device received! Tracking No: {tracking_no}")
    return redirect(url_for("tracking_page"))

# ===== TRACKING =====
@app.route("/tracking-result")
def tracking_result_page():
    search = request.args.get("search_term", "").strip()
    record = form2_collection.find_one({
        "is_deleted": False,
        "$or": [{"tracking_no": search}, {"contact": search}]
    })
    found = bool(record)
    if record:
        record["_id"] = str(record["_id"])
    return render_template("tracking_result.html", found=found, record=record)

# ===== BILL PAGE =====
@app.route("/bill")
def bill_page():
    search = request.args.get("search_term", "").strip()
    record = form2_collection.find_one({
        "is_deleted": False,
        "$or": [{"tracking_no": search}, {"contact": search}]
    })
    if not record or not record.get("bill_generated"):
        flash("Bill not found.")
        return redirect(url_for("tracking_page"))
    record["_id"] = str(record["_id"])
    return render_template("bill.html", record=record)

# ===== LOGIN =====
@app.route("/admin-login", methods=["GET", "POST"])
def staff_login_page():
    if request.method == "POST":
        if request.form["username"] == ADMIN_USERNAME and request.form["password"] == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Wrong username or password")
    return render_template("staff_login.html")

@app.route("/engineer-login", methods=["GET", "POST"])
def engineer_login_page():
    if request.method == "POST":
        if request.form["password"] == ENGINEER_PASSWORD:
            session["engineer_logged_in"] = True
            return redirect(url_for("engineer_dashboard"))
        flash("Wrong password")
    return render_template("staff_login.html")

# ===== LOGOUT =====
@app.route("/admin-logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("staff_login_page"))

@app.route("/engineer-logout")
def engineer_logout():
    session.pop("engineer_logged_in", None)
    return redirect(url_for("engineer_login_page"))

# ===== DASHBOARDS =====
@app.route("/admin-dashboard")
@admin_required
def admin_dashboard():
    bookings = list(form1_collection.find({"is_deleted": False}))
    chalans  = list(form2_collection.find({"is_deleted": False}))
    return render_template("admin_dashboard.html", bookings=bookings, chalans=chalans)

@app.route("/engineer-dashboard")
@engineer_required
def engineer_dashboard():
    chalans = list(form2_collection.find({"is_deleted": False}))
    return render_template("engineer_dashboard.html", chalans=chalans)

# ===== ADMIN ACTIONS =====
@app.route("/update-booking-status", methods=["POST"])
@admin_required
def update_booking_status():
    form1_collection.update_one(
        {"_id": ObjectId(request.form.get("booking_id"))},
        {"$set": {"status": request.form.get("status"), "admin_note": request.form.get("admin_note", "")}}
    )
    flash("Booking updated!")
    return redirect(url_for("admin_dashboard"))

@app.route("/update-chalan-status", methods=["POST"])
@admin_required
def update_chalan_status():
    chalan_id  = request.form.get("chalan_id")
    new_status = request.form.get("status")
    record = form2_collection.find_one({"_id": ObjectId(chalan_id)})
    form2_collection.update_one({"_id": ObjectId(chalan_id)}, {"$set": {
        "status": new_status,
        "assigned_engineer": request.form.get("assigned_engineer", ""),
        "admin_note": request.form.get("admin_note", "")
    }})
    if record:
        send_notification(record.get("contact",""), record.get("email",""),
            f"Hi {record['name']}, repair status updated: {new_status}. Tracking: {record['tracking_no']} - Siya's International",
            "Repair Status Update")
    flash(f"Status updated to {new_status}")
    return redirect(url_for("admin_dashboard"))

@app.route("/delete-booking", methods=["POST"])
@admin_required
def delete_booking():
    form1_collection.update_one({"_id": ObjectId(request.form.get("booking_id"))}, {"$set": {"is_deleted": True}})
    flash("Booking deleted")
    return redirect(url_for("admin_dashboard"))

@app.route("/delete-chalan", methods=["POST"])
@admin_required
def delete_chalan():
    form2_collection.update_one({"_id": ObjectId(request.form.get("chalan_id"))}, {"$set": {"is_deleted": True}})
    flash("Record deleted")
    return redirect(url_for("admin_dashboard"))

@app.route("/clear-bookings")
@admin_required
def clear_bookings():
    form1_collection.update_many({}, {"$set": {"is_deleted": True}})
    flash("All bookings cleared")
    return redirect(url_for("admin_dashboard"))

@app.route("/clear-chalans")
@admin_required
def clear_chalans():
    form2_collection.update_many({}, {"$set": {"is_deleted": True}})
    flash("All records cleared")
    return redirect(url_for("admin_dashboard"))

# ===== GENERATE BILL =====
@app.route("/generate-bill/<id>", methods=["POST"])
@admin_required
def generate_bill(id):
    items = []
    subtotal = 0
    for i in range(1, 15):
        name = request.form.get(f"item{i}", "").strip()
        amt  = request.form.get(f"item{i}_amount", "").strip()
        if name and amt:
            try:
                a = float(amt)
                subtotal += a
                items.append({"item": name, "amount": a})
            except ValueError:
                pass
    cgst  = round(subtotal * 0.09, 2)
    sgst  = round(subtotal * 0.09, 2)
    total = round(subtotal + cgst + sgst, 2)
    form2_collection.update_one({"_id": ObjectId(id)}, {"$set": {
        "bill_items": items, "subtotal": subtotal,
        "cgst": cgst, "sgst": sgst,
        "bill_amount": total, "bill_generated": True
    }})
    record = form2_collection.find_one({"_id": ObjectId(id)})
    if record:
        send_notification(record.get("contact",""), record.get("email",""),
            f"Hi {record['name']}, your bill is ready! Total: Rs.{total}. Tracking: {record['tracking_no']} - Siya's International",
            "Bill Ready")
    flash(f"Bill generated! Total: Rs.{total} (incl. GST)")
    return redirect(url_for("admin_dashboard"))

# ===== ENGINEER UPDATE =====
@app.route("/engineer-update/<id>", methods=["POST"])
@engineer_required
def engineer_update(id):
    new_status = request.form.get("status")
    record = form2_collection.find_one({"_id": ObjectId(id)})
    form2_collection.update_one({"_id": ObjectId(id)}, {"$set": {
        "status": new_status,
        "admin_note": request.form.get("work_note", "")
    }})
    if record:
        send_notification(record.get("contact",""), record.get("email",""),
            f"Hi {record['name']}, status updated: {new_status}. Tracking: {record['tracking_no']} - Siya's International",
            "Status Update")
    flash(f"Status updated to {new_status}")
    return redirect(url_for("engineer_dashboard"))

# ===== GET CUSTOMER =====
@app.route("/get-customer")
def get_customer():
    contact = request.args.get("contact", "").strip()
    record = form1_collection.find_one({"contact": contact})
    if record:
        return jsonify({"found": True, "name": record.get("fullname",""), "email": record.get("email","")})
    record = form2_collection.find_one({"contact": contact})
    if record:
        return jsonify({"found": True, "name": record.get("name",""), "email": record.get("email","")})
    return jsonify({"found": False})

if __name__ == "__main__":
    app.run(debug=True)