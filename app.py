from flask import Flask, request, jsonify
from twilio.rest import Client
from dotenv import load_dotenv
import os

# Load .env
load_dotenv()

app = Flask(__name__)

# Twilio Credentials
ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

print("========== TWILIO CONFIG ==========")
print("ACCOUNT SID:", ACCOUNT_SID)
print("PHONE NUMBER:", TWILIO_NUMBER)
print("AUTH TOKEN FOUND:", AUTH_TOKEN is not None)
print("===================================")

client = Client(ACCOUNT_SID, AUTH_TOKEN)


@app.route("/")
def home():
    return "ResQ SMS Server Running"


@app.route("/send_alert", methods=["POST"])
def send_alert():

    try:

        print("\n========== ALERT RECEIVED ==========")

        data = request.get_json()

        print("Incoming Data:", data)

        latitude = data["latitude"]
        longitude = data["longitude"]
        contacts = data["contacts"]

        maps_link = f"https://maps.google.com/?q={latitude},{longitude}"

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

                print(f"\nSending SMS to {number}")

                sms = client.messages.create(
                    body=message,
                    from_=TWILIO_NUMBER,
                    to=number
                )

                print("SUCCESS!")
                print("Message SID:", sms.sid)
                print("Status:", sms.status)

                success.append(number)

            except Exception as e:

                print("TWILIO ERROR:")
                print(str(e))

                failed.append({
                    "number": number,
                    "error": str(e)
                })

        print("\n========== FINISHED ==========")
        print("Success:", success)
        print("Failed:", failed)

        return jsonify({
            "status": "success",
            "sent": success,
            "failed": failed
        }), 200

    except Exception as e:

        print("SERVER ERROR:")
        print(str(e))

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)