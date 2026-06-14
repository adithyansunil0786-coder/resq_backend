from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

app = Flask(__name__)

# Twilio Credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)

# Emergency Contacts
EMERGENCY_CONTACTS = [
    "+919074121495",   # Father
    "+919846053326",   # Mother
    "+917902253326",   # Friend
]

@app.route("/")
def home():
    return "ResQ SMS Server Running"

@app.route("/send_alert", methods=["POST"])
def send_alert():

    data = request.json

    latitude = data["latitude"]
    longitude = data["longitude"]

    maps_link = f"https://maps.google.com/?q={latitude},{longitude}"

    message = f"""
🚨 RESQ ACCIDENT ALERT 🚨

An accident has been detected.

Location:
{maps_link}

Please reach immediately.
"""

    for number in EMERGENCY_CONTACTS:

        client.messages.create(
            body=message,
            from_=TWILIO_NUMBER,
            to=number
        )

    return jsonify({
        "status": "success",
        "message": "SMS Sent Successfully"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)