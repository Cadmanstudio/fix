from flask import Flask, request, jsonify
import telegram
from telegram import Update
import os
import requests
import hashlib
import hmac
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ Read environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
FLW_SECRET_KEY = os.getenv("FLW_SECRET_KEY")  # Flutterwave Secret Key

# ✅ Telegram Group Link (Replace with your actual link)
GROUP_LINK = "https://t.me/+t7kOR8hKRr0yZGE0"  # 🔹 Replace with your actual Telegram group link

# ✅ Validate environment variables
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Set it in Render's environment variables.")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in Render's environment variables.")
if not FLW_SECRET_KEY:
    raise ValueError("❌ FLW_SECRET_KEY is missing! Set it in Render's environment variables.")

# ✅ Initialize Telegram bot
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    """Handles Flutterwave webhook and verifies the request with the Secret Key."""

    # ✅ Get the Flutterwave signature from headers
    signature = request.headers.get("verif-hash")

    # ✅ Compute HMAC SHA256 hash from the request body
    computed_signature = hmac.new(
        FLW_SECRET_KEY.encode(),  # Use your secret key
        request.data,  # Use the raw request body
        hashlib.sha256  # Hashing algorithm
    ).hexdigest()

    # ✅ Verify the signature
    if not signature or signature != computed_signature:
        return jsonify({"status": "error", "message": "Invalid Webhook Signature"}), 403  # Reject request

    # ✅ Process the webhook if the signature is valid
    data = request.json
    
    if data and data.get("status") == "successful":
        user_id = data["customer"].get("phonenumber", "Unknown User")
        order_details = data.get("meta", {}).get("order_details", "No details provided")
        
        send_order_to_group(user_id, order_details)
    
    return jsonify({"status": "success"}), 200

def send_order_to_group(user_id, order_details):
    """Sends order details to the admin group and includes the group link."""
    message = f"📦 *New Order Received!*\n\n{order_details}\n\n" \
              f"🚀 *Join our delivery group for updates:* [Click Here]({GROUP_LINK})\n\n" \
              f"Click below to confirm:"
    
    keyboard = [[telegram.InlineKeyboardButton("Confirm Order ✅", callback_data=f"confirm_{user_id}")]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=ADMIN_CHAT_ID, text=message, reply_markup=reply_markup, parse_mode="Markdown")

@app.route('/get-group-link', methods=['GET'])
def get_group_link():
    """Returns the Telegram group link when requested."""
    return jsonify({"group_link": GROUP_LINK})

@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handles Telegram button clicks for confirming orders."""
    update = Update.de_json(request.get_json(), bot)
    
    if update.callback_query:
        query = update.callback_query
        admin_id = query.from_user.id  # Get the admin's Telegram user ID
        admin_username = query.from_user.username  # Get the admin's username (if available)
        user_id = query.data.split("_")[1]  # Extract user ID from callback_data
        
        # ✅ Use username if available, else use the Telegram ID
        admin_identifier = f"@{admin_username}" if admin_username else f"User ID: {admin_id}"
        
        # ✅ Notify the customer
        confirmation_message = f"✅ Your order has been confirmed by {admin_identifier}.\n\n" \
                               f"Thank you for shopping with us!"
        bot.send_message(chat_id=user_id, text=confirmation_message)
        
        # ✅ Notify the admin group that the order has been confirmed
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🚀 Order for {user_id} has been confirmed by {admin_identifier}.")

        # ✅ Acknowledge the button click
        query.answer("✅ Order confirmed successfully!")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
