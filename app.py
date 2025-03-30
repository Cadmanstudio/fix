from flask import Flask, request, jsonify
import requests
import os

# ✅ Read environment variables (Set in Railway)
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()

# ✅ Replace GROUP_LINK with GROUP_ID (Telegram Group ID should be a negative number)
GROUP_ID = -1002507060280  # Replace with your actual Telegram group ID

# ✅ Validate environment variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Set it in Railway environment variables.")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in Railway environment variables.")

# ✅ Base Telegram API URL
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# ✅ Initialize Flask app
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Webhook is running successfully!"

def send_telegram_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = reply_markup

    response = requests.post(TELEGRAM_API_URL, json=data)
    print("📨 Telegram Response:", response.json())
    return response.json()

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    if data.get("event") == "charge.completed" and data["data"].get("status") == "successful":
        tx_ref = data["data"].get("tx_ref", "")
        user_id = tx_ref.split("_")[1] if "_" in tx_ref else None
        items = data["data"].get("meta", {}).get("items", "No items listed")
        
        order_details = (f"📦 *New Order Received!*

"
                         f"💰 Amount: {data['data']['amount']} {data['data']['currency']}
"
                         f"💳 Payment Type: {data['data']['payment_type']}
"
                         f"🔗 Transaction Reference: {data['data']['flw_ref']}
"
                         f"🛍 Items: {items}

"
                         f"Click below to confirm:")

        if user_id:
            send_order_to_group(user_id, order_details)
            return jsonify({"status": "success", "message": "Order sent"}), 200
    return jsonify({"status": "error", "message": "Payment not successful"}), 400

def send_order_to_group(user_id, order_details):
    message = f"{order_details}\n\n👤 *Customer ID:* {user_id}"
    keyboard = {"inline_keyboard": [[{"text": "✅ Confirm Order", "callback_data": f"confirm_{user_id}"}]]}
    send_telegram_message(GROUP_ID, message, reply_markup=keyboard)

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    if "callback_query" in json_data:
        query = json_data["callback_query"]
        admin_id = query["from"]["id"]
        admin_username = query["from"].get("username", "")
        callback_data = query.get("data", "")
        
        if not callback_data.startswith("confirm_"):
            return jsonify({"status": "error", "message": "Invalid callback data"}), 400

        user_id = callback_data.split("_")[1]
        admin_identifier = f"@{admin_username}" if admin_username else f"User ID: {admin_id}"

        confirmation_message = f"✅ Your order has been confirmed by {admin_identifier}.\n\n"
                               f"Please send your delivery address. 📍"
        send_telegram_message(user_id, confirmation_message)
        send_telegram_message(GROUP_ID, f"🚀 Order for {user_id} has been confirmed by {admin_identifier}.")
        return jsonify({"status": "success", "message": "Order confirmed"}), 200

    if "message" in json_data:
        message = json_data["message"]
        user_id = message["from"]["id"]
        text = message.get("text", "")
        
        if text.lower().startswith("address:"):
            send_telegram_message(GROUP_ID, f"📍 Delivery Address from {user_id}:\n{text}")
            return jsonify({"status": "success", "message": "Address received"}), 200
    
    return jsonify({"status": "error", "message": "Invalid request"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
