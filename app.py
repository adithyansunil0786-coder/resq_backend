from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Twilio Credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


@app.route("/")
def home():
    return "ResQ SMS Server Running"


@app.route("/send_alert", methods=["POST"])
def send_alert():
    try:

        data = request.get_json()

        latitude = data["latitude"]
        longitude = data["longitude"]
        contacts = data["contacts"]

        maps_link = f"https://maps.google.com/?q={latitude},{longitude}"

        message = f"""🚨 RESQ ACCIDENT ALERT 🚨

An accident has been detected.

Location:
{maps_link}

Please reach immediately.
"""

        success = []
        failed = []

        for number in contacts:
            try:
                client.messages.create(
                    body=message,
                    from_=TWILIO_NUMBER,
                    to=number,
                )
                success.append(number)

            except Exception as e:
                failed.append({
                    "number": number,
                    "error": str(e)
                })

        return jsonify({
            "status": "success",
            "sent": success,
            "failed": failed
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)