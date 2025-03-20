from flask import Flask, request, jsonify
import telegram
from telegram import Update
from telegram.ext import CallbackContext
import os
from dotenv import load_dotenv

# ✅ Load environment variables
load_dotenv()

app = Flask(__name__)

# ✅ Read environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# ✅ Telegram Group Link (Replace with your actual link)
GROUP_LINK = "https://t.me/+upYS-Qll3PoxMGU0"  # 🔹 Replace with your actual Telegram group link

# ✅ Validate tokens
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Set it in Render's environment variables.")
if not ADMIN_CHAT_ID:
    raise ValueError("❌ ADMIN_CHAT_ID is missing! Set it in Render's environment variables.")

# ✅ Initialize Telegram bot
bot = telegram.Bot(token=BOT_TOKEN)

@app.route('/flutterwave-webhook', methods=['POST'])
def flutterwave_webhook():
    """Handles Flutterwave webhook when a payment is successful."""
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

# ✅ Handle "Confirm Order ✅" button clicks
@app.route('/telegram-webhook', methods=['POST'])
def telegram_webhook():
    """Handles Telegram button clicks."""
    update = telegram.Update.de_json(request.get_json(), bot)
    
    if update.callback_query:
        query = update.callback_query
        admin_phone_number = query.from_user.id  # Get the admin who clicked the button
        user_id = query.data.split("_")[1]  # Extract user ID from callback_data
        
        # ✅ Notify the customer
        confirmation_message = f"✅ Your order has been confirmed by an admin (Phone: {admin_phone_number}).\n\n" \
                               f"Thank you for shopping with us!"
        bot.send_message(chat_id=user_id, text=confirmation_message)
        
        # ✅ Notify the admin group that the order has been confirmed
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"🚀 Order for {user_id} has been confirmed by {admin_phone_number}.")

        # ✅ Acknowledge the button click
        query.answer("✅ Order confirmed successfully!")

    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
