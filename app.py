from flask import Flask, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask_cors import CORS
import os, json

# --- Flask setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # allow all origins for now

# --- Google Sheets setup ---
SHEET_NAME = "Lanyard_Data"
STUDENT_TAB = "Lanyard_Data"
SCAN_LOG_SHEET = "lanyard_log"

# Load Google credentials from Render environment variable
try:
    creds_dict = json.loads(os.environ["GOOGLE_CREDS"])
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
except Exception as e:
    print("⚠️ Failed to load Google credentials:", e)
    client = None

# --- Color thresholds ---
color_thresholds = [
    {"min": 1, "max": 4, "color": "#b6f7b6", "title": "Tier 1"},
    {"min": 5, "max": 9, "color": "#fff7a6", "title": "Tier 2"},
    {"min": 10, "max": 14, "color": "#ffd8a6", "title": "Tier 3"},
    {"min": 15, "max": 9999, "color": "#ffb3b3", "title": "Tier 4"}
]

@app.route("/")
def home():
    return "✅ Lanyard API is running and connected to Google Sheets."

@app.route("/api/student")
def get_student():
    if client is None:
        return jsonify({"error": "Google credentials not loaded"}), 500

    student_id = request.args.get("id", "").strip()
    if not student_id:
        return jsonify({"error": "Missing student ID"}), 400

    try:
        # --- Open Google Sheet ---
        spreadsheet = client.open(SHEET_NAME)
        student_sheet = spreadsheet.worksheet(STUDENT_TAB)
        students = student_sheet.get_all_records()

        # --- Try to find student (handle number vs string mismatch) ---
        student = next(
            (
                s for s in students
                if str(s.get("student_id")).strip() == student_id
                or str(int(float(s.get("student_id")))) == student_id
            ),
            None
        )

        if not student:
            return jsonify({"error": f"Student {student_id} not found"}), 404

        # --- Count scans from log sheet ---
        log_sheet = spreadsheet.worksheet(SCAN_LOG_SHEET)
        ids = log_sheet.col_values(2)[1:]  # column 2 = student_id
        count = ids.count(student_id)

        # --- Determine tier ---
        tier = next((t for t in color_thresholds if t["min"] <= count <= t["max"]), None)
        tier_name = tier["title"] if tier else "N/A"
        tier_color = tier["color"] if tier else "#fff"

        # --- Build response ---
        return jsonify({
            "student_id": student_id,
            "name": f"{student.get('first_name', '')} {student.get('last_name', '')}".strip(),
            "class_year": student.get("class_year", ""),
            "team": student.get("team", ""),
            "scan_count": count,
            "tier": tier_name,
            "color": tier_color
        })

    except Exception as e:
        print("❌ Error in /api/student:", e)
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, debug=True)
