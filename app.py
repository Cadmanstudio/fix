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
    print("📨 Telegram Response:", response.json())  # Debugging
    return response.json()

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    """Handles Flutterwave webhook and processes successful payments."""
    data = request.get_json()

    if not data:
        print("❌ Invalid webhook request (No JSON received)")
        return jsonify({"status": "error", "message": "Invalid request"}), 400

    print("🔹 Received Webhook Data:", data)  # Debugging

    # ✅ Process successful payment
    if data.get("event") == "charge.completed" and data["data"].get("status") == "successful":
        print("✅ Payment is successful")  # Debugging

        tx_ref = data["data"].get("tx_ref", "")
        user_id = tx_ref.split("_")[1] if "_" in tx_ref else None

        ordered_items = data["data"].get("meta", {}).get("ordered_items", [])
        hostel_name = data["data"].get("meta", {}).get("hostel", "Not provided")
        room_number = data["data"].get("meta", {}).get("room_number", "Not provided")
        recipient_name = data["data"].get("meta", {}).get("recipient_name", "Not provided")
        
        items_text = "\n".join([f" - {item}" for item in ordered_items]) if ordered_items else "No items specified."

        order_details = (
            f"📦 *New Order Received!*
\n"
            f"👤 *Customer ID:* {user_id}\n"
            f"🏠 Hostel: {hostel_name}\n"
            f"🚪 Room Number: {room_number}\n"
            f"👤 Recipient: {recipient_name}\n"
            f"💰 Amount: {data['data']['amount']} {data['data']['currency']}\n"
            f"💳 Payment Type: {data['data']['payment_type']}\n"
            f"🔗 Transaction Reference: {data['data']['flw_ref']}\n\n"
            f"🛒 *Ordered Items:*\n{items_text}\n\n"
            "Click below to confirm:"
        )

        print(f"✅ Extracted User ID: {user_id}")  # Debugging

        if user_id:
            send_order_to_group(user_id, order_details)
            send_telegram_message(user_id, "✅ Payment confirmed! Your order has been received.")
            print(f"✅ Order sent to group for user {user_id}")  # Debugging
            return jsonify({"status": "success", "message": "Order sent"}), 200
        else:
            print("❌ No Telegram User ID found in tx_ref!")
            return jsonify({"status": "error", "message": "No Telegram User ID"}), 400

    print("❌ Payment was not successful")
    return jsonify({"status": "error", "message": "Payment not successful"}), 400

def send_order_to_group(user_id, order_details):
    """Sends order details to the Telegram group with a confirmation button."""
    keyboard = {
        "inline_keyboard": [[{"text": "✅ Confirm Order", "callback_data": f"confirm_{user_id}"}]]
    }
    send_telegram_message(GROUP_ID, order_details, reply_markup=keyboard)

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handles Telegram button clicks for confirming orders."""
    json_data = request.get_json()
    
    # ✅ Validate request data
    if not json_data:
        return jsonify({"status": "error", "message": "No JSON data received"}), 400

    if "callback_query" in json_data:
        query = json_data["callback_query"]
        callback_id = query["id"]
        admin_id = query["from"]["id"]
        admin_username = query["from"].get("username", "")
        admin_phone = query["from"].get("phone_number", "Not available")

        # ✅ Acknowledge button click to stop "loading..."
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery", 
                      json={"callback_query_id": callback_id})

        callback_data = query.get("data", "")
        if not callback_data.startswith("confirm_"):
            return jsonify({"status": "error", "message": "Invalid callback data"}), 400

        try:
            user_id = callback_data.split("_")[1]
        except IndexError:
            return jsonify({"status": "error", "message": "Malformed callback data"}), 400

        admin_identifier = f"@{admin_username}" if admin_username else f"Phone: {admin_phone}"

        confirmation_message = (
            f"✅ Your order has been picked by {admin_identifier}.\n\n"
            f"Thank you for shopping with us! 🎉"
        )
        send_telegram_message(user_id, confirmation_message)

        return jsonify({"status": "success", "message": "Order confirmed"}), 200

    return jsonify({"status": "error", "message": "Invalid request"}), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
