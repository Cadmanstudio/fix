from flask import Flask, request, jsonify
import telegram
import os
from dotenv import load_dotenv

# ✅ Load environment variables (ignored on Render but works locally)
load_dotenv()

app = Flask(__name__)

# ✅ Read environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")

# ✅ Telegram Group Link (Replace with your actual link)
GROUP_LINK = "https://t.me/+upYS-Qll3PoxMGU0"  # 🔹 Replace with your group link

# ✅ Debugging: Print values to check if they are loaded
print(f"BOT_TOKEN: {BOT_TOKEN[:5]}********") if BOT_TOKEN else print("❌ BOT_TOKEN is missing!")
print(f"ADMIN_CHAT_ID: {ADMIN_CHAT_ID}") if ADMIN_CHAT_ID else print("❌ ADMIN_CHAT_ID is missing!")

# ✅ Validate that tokens are set
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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
