from flask import Flask, request, jsonify
import telegram
import os
from dotenv import load_dotenv

# ✅ Load environment variables from .env file
load_dotenv(dotenv_path=".env")  # Ensure it loads from the correct location

app = Flask(__name__)

# ✅ Read environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# ✅ Debugging: Print values to check if they are loaded
print(f"BOT_TOKEN: {BOT_TOKEN[:5]}********") if BOT_TOKEN else print("❌ BOT_TOKEN is missing!")
print(f"ADMIN_CHAT_ID: {ADMIN_CHAT_ID}") if ADMIN_CHAT_ID else print("❌ ADMIN_CHAT_ID is missing!")

# ✅ Validate that tokens are set
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Set it in your .env file.")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in your .env file.")

# ✅ Initialize Telegram bot
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    data = request.json
    
    if data and data.get("status") == "successful":
        user_id = data["customer"].get("phonenumber", "Unknown User")
        order_details = data.get("meta", {}).get("order_details", "No details provided")
        
        send_order_to_group(user_id, order_details)
    
    return jsonify({"status": "success"}), 200

def send_order_to_group(user_id, order_details):
    message = f"📦 *New Order Received!*\n\n{order_details}\n\nClick below to confirm:"
    keyboard = [[telegram.InlineKeyboardButton("Confirm Order ✅", callback_data=f"confirm_{user_id}")]]
    reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    bot.send_message(chat_id=ADMIN_CHAT_ID, text=message, reply_markup=reply_markup, parse_mode="Markdown")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
