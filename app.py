from flask import Flask, request, jsonify
import requests
import os

# ✅ Read environment variables (Set in Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()

# ✅ Telegram Group Link (Updated)
GROUP_LINK = "https://t.me/+t7kOR8hKRr0yZGE0"  # Your actual Telegram group link

# ✅ Validate environment variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Set it in Railway environment variables.")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in Railway environment variables.")

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
    """Handles Flutterwave webhook and processes successful payments."""

    # ✅ Validate request data
    data = request.get_json()
    if not data:
        print("❌ Invalid webhook request (No JSON received)")
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    print("🔹 Received Webhook Data:", data)  # Debugging

    # ✅ Process successful payment
    if data.get("event") == "charge.completed" and data["data"].get("status") == "successful":
        tx_ref = data["data"].get("tx_ref", "")
        user_id = tx_ref.split("_")[1] if "_" in tx_ref else None  # Extract user ID from tx_ref
        order_details = f"💰 Amount: {data['data']['amount']} {data['data']['currency']}\n" \
                        f"💳 Payment Type: {data['data']['payment_type']}\n" \
                        f"🔗 Transaction Reference: {data['data']['flw_ref']}"

        if user_id:
            send_order_to_group(user_id, order_details)
            print(f"✅ Order sent to group for user {user_id}")  # Debugging
            return jsonify({"status": "success", "message": "Order sent"}), 200
        else:
            print("❌ No telegram_user_id found in tx_ref!")
            return jsonify({"status": "error", "message": "No Telegram User ID"}), 400

    print("❌ Payment was not successful")
    return jsonify({"status": "error", "message": "Payment not successful"}), 400

def send_order_to_group(user_id, order_details):
    """Sends order details to the admin group with a confirmation button."""
    message = f"📦 *New Order Received!*\n\n{order_details}\n\n" \
              f"🚀 *Join our delivery group:* [Click Here]({GROUP_LINK})\n\n" \
              f"Click below to confirm:"

    keyboard = {
        "inline_keyboard": [[{"text": "✅ Confirm Order", "callback_data": f"confirm_{user_id}"}]]
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
    port = int(os.environ.get("PORT", 8080))  # Use Railway's default port
    app.run(host="0.0.0.0", port=port)
