from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

# ✅ Read environment variables with default values
BOT_TOKEN = os.getenv("BOT_TOKEN", "your_default_bot_token")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "your_default_chat_id")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY", "your_default_secret_key")

# ✅ Telegram Group Link
GROUP_LINK = "https://t.me/+t7kOR8hKRr0yZGE0"  # Replace with your actual Telegram group link

# ✅ Validate environment variables
if BOT_TOKEN == "your_default_bot_token":
    raise ValueError("❌ BOT_TOKEN is missing! Set it in Railway environment variables.")
if ADMIN_CHAT_ID == "your_default_chat_id":
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in Railway environment variables.")
if FLW_SECRET_KEY == "your_default_secret_key":
    raise ValueError("❌ FLW_SECRET_KEY is missing! Set it in Railway environment variables.")

# ✅ Base Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ✅ Initialize Flask app
app = Flask(__name__)

# ✅ Home route to verify deployment
@app.route('/')
def home():
    return "✅ Webhook is running successfully!"

def send_telegram_message(chat_id, text, reply_markup=None):
    """Sends a message to Telegram with optional inline keyboard."""
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup

    response = requests.post(TELEGRAM_API_URL, json=data)
    return response.json()

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    """Handles Flutterwave webhook and verifies the request signature."""

    # ✅ Validate request data
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    print("🔹 Received Webhook Data:", data)  # Debugging

    # ✅ Verify Flutterwave signature (for security)
    request_signature = request.headers.get("verif-hash")
    if not request_signature or request_signature != FLW_SECRET_KEY:
        print("❌ Invalid Flutterwave webhook signature!")
        return jsonify({"status": "error", "message": "Unauthorized"}), 403

    # ✅ Process successful payment
    if data.get("status") == "successful":
        meta = data.get("meta", {})
        user_id = meta.get("telegram_user_id")  # Ensure Telegram user ID is passed in metadata
        order_details = meta.get("order_details", "No details provided")

        if user_id:
            send_order_to_group(user_id, order_details)
            return jsonify({"status": "success", "message": "Order sent"}), 200
        else:
            print("❌ No telegram_user_id found in metadata!")
            return jsonify({"status": "error", "message": "No Telegram User ID"}), 400

    return jsonify({"status": "error", "message": "Payment not successful"}), 400

def send_order_to_group(user_id, order_details):
    """Sends order details to the admin group with a confirmation button."""
    message = f"📦 *New Order Received!*\n\n{order_details}\n\n" \
              f"🚀 *Join our delivery group:* [Click Here]({GROUP_LINK})\n\n" \
              f"Click below to confirm:"

    keyboard = {
        "inline_keyboard": [[{"text": "Confirm Order ✅", "callback_data": f"confirm_{user_id}"}]]
    }

    send_telegram_message(ADMIN_CHAT_ID, message, reply_markup=keyboard)

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handles Telegram button clicks for confirming orders."""
    json_data = request.get_json()
    
    # ✅ Validate request data
    if not json_data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    if "callback_query" in json_data:
        query = json_data["callback_query"]
        admin_id = query["from"]["id"]
        admin_username = query["from"].get("username", "")

        # ✅ Ensure correct format before splitting
        callback_data = query.get("data", "")
        if not callback_data.startswith("confirm_"):
            return jsonify({"status": "error", "message": "Invalid callback data"}), 400

        try:
            user_id = callback_data.split("_")[1]  # Extract user ID from callback_data
        except IndexError:
            return jsonify({"status": "error", "message": "Malformed callback data"}), 400

        # ✅ Use username if available, else use Telegram ID
        admin_identifier = f"@{admin_username}" if admin_username else f"User ID: {admin_id}"

        # ✅ Notify the customer
        confirmation_message = f"✅ Your order has been confirmed by {admin_identifier}.\n\n" \
                               f"Thank you for shopping with us!"
        send_telegram_message(user_id, confirmation_message)

        # ✅ Notify the admin group that the order has been confirmed
        send_telegram_message(ADMIN_CHAT_ID, f"🚀 Order for {user_id} has been confirmed by {admin_identifier}.")

        # ✅ Acknowledge the button click
        return jsonify({"status": "success", "message": "Order confirmed"}), 200

    return jsonify({"status": "error", "message": "Invalid request"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
