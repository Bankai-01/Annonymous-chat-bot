import asyncio
import nest_asyncio
import logging
import firebase_admin
from firebase_admin import credentials, db
from aiogram import Bot, Dispatcher, types
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor

# **Apply Nest Asyncio for Async Compatibility**
nest_asyncio.apply()

# **Logging Configuration**
logging.basicConfig(level=logging.INFO)

# **Firebase Credentials & Initialization**
cred = credentials.Certificate("telebot-80496-firebase-adminsdk-fbsvc-e4e7eec121.json")  # JSON key file
firebase_admin.initialize_app(cred, {"databaseURL": "https://console.firebase.google.com/u/0/project/telebot-80496/database/telebot-80496-default-rtdb/data/~2F"})
users_ref = db.reference("users")

# **Bot Setup**
TOKEN = "7636983079:AAGr35bB03asg2IYta-EnClzMX3FSa35ink"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

# **Group Details**
GROUP_IDS = [-1002572807793, -1002500642384, -1002673544700]  # Multiple groups
GROUP_LINKS = ["https://t.me/bankai_offcial", "https://t.me/bankai_software", "https://t.me/bankai_bots"]

# **Constants**
DEFAULT_CHAT_LIMIT = 15
REFERRAL_BONUS = 100
POINTS_PER_REFER = 1
GENDER_UNLOCK_POINTS = 10

# **Rules Text**
RULES_TEXT = (
    "🚨 **Malayalie Chat Bot – Rules & Guidelines** 🚨\n\n"
    "🔴 **STRICTLY FOLLOW THESE RULES OR FACE PERMANENT BAN!**\n"
    "🔹 Breaking these rules may result in a **temporary or permanent ban** without warning!\n\n"
    "1️⃣ **NO SHARING PERSONAL INFORMATION**\n"
    "   🔸 Your privacy is your responsibility!\n"
    "   Do NOT share your phone number, email, home address, bank details, social media accounts, or any other private information.\n"
    "   Never ask others for their personal details either.\n"
    "   We are NOT responsible for any harm caused by sharing private details with strangers.\n"
    "   If you violate this rule, your access to the bot may be revoked permanently.\n\n"
    "2️⃣ **NO HARASSMENT OR ABUSE**\n"
    "   🔸 Respect others at all times!\n"
    "   Do NOT send threats, insults, bullying messages, hate speech, racist remarks, sexist comments, or any offensive content.\n"
    "   Sexual harassment and inappropriate messages are strictly prohibited!\n"
    "   Violators will be immediately banned and reported if necessary.\n"
    "   Keep the chat friendly, respectful, and safe for everyone.\n\n"
    "3️⃣ **NO SPAMMING OR PROMOTIONS**\n"
    "   🔸 Spamming will result in an instant mute or ban!\n"
    "   Do NOT send repeated messages, flood the chat, or spam emojis/stickers.\n"
    "   Promoting businesses, products, services, Telegram groups, or external links is strictly forbidden.\n"
    "   No self-promotion, advertisements, or referral links are allowed.\n\n"
    "4️⃣ **NO IMPERSONATION OR FRAUD**\n"
    "   🔸 Be yourself, don’t pretend to be someone else!\n"
    "   Do NOT impersonate other users, moderators, admins, or famous personalities.\n"
    "   Scamming, phishing, or any fraudulent activities will result in a permanent ban and may be reported to authorities.\n"
    "   Fake profiles and catfishing are strictly prohibited!\n\n"
    "5️⃣ **RESPECT EVERYONE**\n"
    "   🔸 Treat others how you want to be treated!\n"
    "   If someone asks you to stop a conversation, respect their decision and move on.\n"
    "   No forcing, no manipulation, and no controlling others.\n"
    "   If you feel uncomfortable, you have the right to leave the chat anytime.\n\n"
    "6️⃣ **NO ILLEGAL OR OFFENSIVE CONTENT**\n"
    "   🔸 Legal and ethical behavior is mandatory!\n"
    "   Do NOT share illegal, violent, explicit, or disturbing content.\n"
    "   Sharing hacking tools, drugs, weapons, or any prohibited material will result in a permanent ban.\n"
    "   Breaking this rule may lead to legal consequences.\n\n"
    "7️⃣ **BOT ADMINS HAVE FULL CONTROL**\n"
    "   🔸 Admin decisions are FINAL!\n"
    "   Admins have the right to mute, ban, or remove any user at any time without prior notice.\n"
    "   If you violate any rule, you may be permanently blocked from using the bot.\n"
    "   Arguing with admins or challenging their decisions will not be tolerated.\n\n"
    "❗ **IMPORTANT DISCLAIMER** ❗\n"
    "This bot does not store your messages permanently.\n"
    "The admin is NOT responsible for any personal data shared. Use the bot at your own risk.\n"
    "We are NOT responsible for any issues, damages, or consequences caused by using this bot.\n"
    "If you encounter any issues, report them immediately to the admin.\n\n"
    "By using this bot, you agree to all these rules.\n\n"
    "🚨 **Violators will face an IMMEDIATE BAN without warning!** 🚨\n\n"
    "**Developer: Bankai**"
)

# **Inline Keyboard for Rules Confirmation**
def rules_confirmation_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("✅ I Accept the Rules", callback_data="accept_rules"))
    return keyboard

# **Check If User is in Any Group**
async def is_user_in_group(user_id):
    try:
        for group_id in GROUP_IDS:
            member = await bot.get_chat_member(group_id, user_id)
            if member.status in ["member", "administrator", "creator"]:
                return True
    except Exception as e:
        logging.error(f"Error checking group membership: {e}")
    return False

# **Handle Start Command**
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = message.from_user.id

    # **Check If User Has Already Accepted Rules**
    user_data = users_ref.child(str(user_id)).get()
    if user_data and user_data.get("accepted_rules"):
        await message.reply("✅ You have already accepted the rules! Welcome back.", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("💬 Start Chat")))
        return

    # **Send Rules & Ask for Confirmation**
    await message.reply(RULES_TEXT, reply_markup=rules_confirmation_keyboard())

# **Handle Rules Acceptance**
@dp.callback_query_handler(lambda query: query.data == "accept_rules")
async def accept_rules(query: types.CallbackQuery):
    user_id = query.from_user.id
    users_ref.child(str(user_id)).update({"accepted_rules": True})
    
    await query.message.edit_text("✅ Thank you for accepting the rules! You can now use the bot.", reply_markup=None)
    await bot.send_message(user_id, "💬 Click below to start chatting!", reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("💬 Start Chat")))

# **Run Bot**
if __name__ == "__main__":
    try:
        executor.start_polling(dp, skip_updates=True)
    except Exception as e:
        logging.error(f"Bot startup error: {e}")
