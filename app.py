from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import sqlite3
import os

# =====================================================
# Load Environment Variables
# =====================================================

load_dotenv()

app = Flask(__name__)

# =====================================================
# Database
# =====================================================

DATABASE = "contacts.db"


def get_db():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():

    conn = get_db()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS contacts(

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            phone TEXT NOT NULL
        )
        """
    )

    conn.commit()

    conn.close()


initialize_database()

# =====================================================
# Twilio
# =====================================================

ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")

AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")

TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

print("\n==============================")
print("ResQ SMS Server")
print("==============================")
print("ACCOUNT SID :", ACCOUNT_SID)
print("PHONE       :", TWILIO_NUMBER)
print("TOKEN FOUND :", AUTH_TOKEN is not None)
print("==============================\n")

client = Client(
    ACCOUNT_SID,
    AUTH_TOKEN,
)

# =====================================================
# Home
# =====================================================

@app.route("/")
def home():

    return jsonify({

        "status": "running",

        "server": "ResQ SMS Server"

    })
    # =====================================================
# Get Contacts
# =====================================================

@app.route("/contacts", methods=["GET"])
def get_contacts():

    conn = get_db()

    contacts = conn.execute(
        "SELECT * FROM contacts ORDER BY id DESC"
    ).fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in contacts
    ])


# =====================================================
# Add Contact
# =====================================================

@app.route("/contacts", methods=["POST"])
def add_contact():

    try:

        data = request.get_json()

        name = data.get("name", "").strip()

        phone = data.get("phone", "").strip()

        if name == "" or phone == "":

            return jsonify({
                "status": "error",
                "message": "Name and Phone are required."
            }), 400

        # Remove spaces
        phone = phone.replace(" ", "")

        # Store phone in international format
        if not phone.startswith("+"):

            if phone.startswith("91") and len(phone) == 12:

                phone = "+" + phone

            else:

                phone = "+91" + phone

        conn = get_db()

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO contacts(name, phone)
            VALUES(?, ?)
            """,
            (
                name,
                phone,
            ),
        )

        conn.commit()

        contact_id = cursor.lastrowid

        conn.close()

        return jsonify({

            "status": "success",

            "id": contact_id,

            "message": "Contact Saved"

        }), 201

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# =====================================================
# Update Contact
# =====================================================

@app.route("/contacts/<int:id>", methods=["PUT"])
def update_contact(id):

    try:

        data = request.get_json()

        name = data.get("name", "").strip()

        phone = data.get("phone", "").strip()

        phone = phone.replace(" ", "")

        if not phone.startswith("+"):

            if phone.startswith("91") and len(phone) == 12:

                phone = "+" + phone

            else:

                phone = "+91" + phone

        conn = get_db()

        conn.execute(
            """
            UPDATE contacts
            SET name=?, phone=?
            WHERE id=?
            """,
            (
                name,
                phone,
                id,
            ),
        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message": "Contact Updated"

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# =====================================================
# Delete Contact
# =====================================================

@app.route("/contacts/<int:id>", methods=["DELETE"])
def delete_contact(id):

    try:

        conn = get_db()

        conn.execute(

            "DELETE FROM contacts WHERE id=?",

            (id,)

        )

        conn.commit()

        conn.close()

        return jsonify({

            "status": "success",

            "message": "Contact Deleted"

        })

    except Exception as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500
        # =====================================================
# Send Alert
# =====================================================

@app.route("/send_alert", methods=["POST"])
def send_alert():

    try:

        print("\n========================================")
        print("RESQ ALERT RECEIVED")
        print("========================================")

        data = request.get_json()

        print("Incoming Data:")
        print(data)

        latitude = data.get("latitude")
        longitude = data.get("longitude")
        contacts = data.get("contacts", [])

        maps_link = (
            f"https://maps.google.com/?q="
            f"{latitude},{longitude}"
        )

        message = f"""
🚨 RESQ ACCIDENT ALERT 🚨

An accident has been detected.

Location:
{maps_link}

Please reach immediately.
"""

        success = []
        failed = []

        for number in contacts:

            try:

                number = str(number).strip()

                if number == "":
                    continue

                # Remove spaces and dashes
                number = (
                    number.replace(" ", "")
                          .replace("-", "")
                )

                # Convert to E.164
                if not number.startswith("+"):

                    if number.startswith("91") and len(number) == 12:

                        number = "+" + number

                    else:

                        number = "+91" + number

                print(f"\nSending SMS to {number}")

                sms = client.messages.create(

                    body=message,

                    from_=TWILIO_NUMBER,

                    to=number,

                )

                print("SUCCESS")
                print("SID :", sms.sid)
                print("STATUS :", sms.status)

                success.append(number)

            except Exception as e:

                print("FAILED :", str(e))

                failed.append({

                    "number": number,

                    "error": str(e)

                })

        print("\n========================================")
        print("SMS Sending Finished")
        print("Success :", success)
        print("Failed  :", failed)
        print("========================================")

        return jsonify({

            "status": "success",

            "sent": success,

            "failed": failed

        }), 200

    except Exception as e:

        print("\nSERVER ERROR")
        print(str(e))

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500
        # =====================================================
# Health Check
# =====================================================

@app.route("/health", methods=["GET"])
def health():

    return jsonify({

        "status": "online",

        "database": "connected",

        "twilio": TWILIO_NUMBER,

        "message": "ResQ Server Running"

    })


# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    print("\n====================================")
    print("      ResQ SMS Server Started")
    print("====================================")
    print("Listening on Port : 5000")
    print("====================================\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )
