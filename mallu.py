import os
import asyncio
import logging
import nest_asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatMember
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from collections import defaultdict, deque

# -------------------- Bot Configuration --------------------

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_IDS = list(map(int, os.getenv("GROUP_IDS").split(',')))
GROUP_LINKS = os.getenv("GROUP_LINKS").split(',')

# Referral & Access Tracking
referrals = defaultdict(set)
allowed_users = set()
checked_users = {}
waiting_users = deque()
active_chats = {}

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

# -------------------- Check Group Membership --------------------

async def is_user_in_groups(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if the user is in all required groups. If left, remove access."""
    
    async def check_group(group_id):
        try:
            chat_member = await context.bot.get_chat_member(group_id, user_id)
            return chat_member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
        except Exception as e:
            logging.error(f"Error checking group {group_id}: {e}")
            return False

    results = await asyncio.gather(*(check_group(gid) for gid in GROUP_IDS))
    is_member = all(results)
    
    if not is_member:
        allowed_users.discard(user_id)
        checked_users.pop(user_id, None)
    
    checked_users[user_id] = is_member
    return is_member

# -------------------- Rules --------------------

RULES_TEXT = (
    "🚨 **Malayalie Chat Bot – Rules & Guidelines** 🚨\n\n"
    "🔴 **STRICTLY FOLLOW THESE RULES OR FACE PERMANENT BAN!**\n"
    "🔹 Breaking these rules may result in a **temporary or permanent ban** without warning!\n\n"
    "1️⃣ **NO SHARING PERSONAL INFORMATION**\n"
    "2️⃣ **NO HARASSMENT OR ABUSE**\n"
    "3️⃣ **NO SPAMMING OR PROMOTIONS**\n"
    "4️⃣ **NO IMPERSONATION OR FRAUD**\n"
    "5️⃣ **RESPECT EVERYONE**\n"
    "6️⃣ **NO ILLEGAL OR OFFENSIVE CONTENT**\n"
    "7️⃣ **BOT ADMINS HAVE FULL CONTROL**\n\n"
    "✅ **By using this bot, you agree to all these rules.**\n\n"
    "**Developer: Bankai**"
)

# -------------------- Start Command --------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Start Command - Checks Group Membership First """
    user_id = update.message.from_user.id

    if not await is_user_in_groups(user_id, context):
        join_buttons = [[InlineKeyboardButton(f"🔗 Join Group {i+1}", url=link)] for i, link in enumerate(GROUP_LINKS)]
        reply_markup = InlineKeyboardMarkup(join_buttons)
        await update.message.reply_text("🚨 You must **join all required groups** before using this bot!", reply_markup=reply_markup)
        return
    
    await update.message.reply_text(RULES_TEXT)
    confirm_button = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Confirm & Enter", callback_data="confirm")]])
    await update.message.reply_text("✅ **Click below to enter the referral system!**", reply_markup=confirm_button)

# -------------------- Confirm Command --------------------

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handles inline confirm button click """
    query = update.callback_query
    user_id = query.from_user.id

    await query.answer()  # Acknowledge the button click

    if not await is_user_in_groups(user_id, context):
        join_buttons = [[InlineKeyboardButton(f"🔗 Join Group {i+1}", url=link)] for i, link in enumerate(GROUP_LINKS)]
        reply_markup = InlineKeyboardMarkup(join_buttons)
        await query.message.reply_text("🚨 You must **join all required groups** before confirming!", reply_markup=reply_markup)
        return
    
    referral_link = f"https://t.me/{context.bot.username}?start={user_id}"

    if user_id in allowed_users:
        await query.message.reply_text("✅ You already have access. Start chatting!")
        return

    keyboard = [[InlineKeyboardButton("📢 Share & Unlock", switch_inline_query=referral_link)],
                [InlineKeyboardButton("✅ Check Referral Status", callback_data="check_referrals")]]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text(
        f"🎯 To unlock the bot, **refer 2 users** using your link:\n"
        f"🔗 {referral_link}\n\n"
        f"📌 You can **send this link to anyone** (users, groups, or channels)!",
        reply_markup=reply_markup
    )

# -------------------- Check Referrals --------------------

async def check_referrals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Checks if the user has met referral requirements"""
    user_id = update.callback_query.from_user.id

    if user_id in allowed_users:
        await update.callback_query.answer("✅ You already have access!")
        return
    
    referred_users = referrals[user_id]
    
    if len(referred_users) >= 2:
        allowed_users.add(user_id)
        await update.callback_query.answer("🎉 Referral requirement met! You can now chat.")
    else:
        await update.callback_query.answer(f"🚨 You need {2 - len(referred_users)} more referrals!")

# -------------------- Find Chat Partner --------------------

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Matches users for anonymous chat """
    user_id = update.message.from_user.id

    if user_id in active_chats:
        await update.message.reply_text("❌ You are already in a chat. Use /leave to exit first.")
        return

    if waiting_users:
        partner_id = waiting_users.popleft()
        active_chats[user_id] = partner_id
        active_chats[partner_id] = user_id

        await context.bot.send_message(user_id, "✅ Match found! Start chatting.")
        await context.bot.send_message(partner_id, "✅ Match found! Start chatting.")
    else:
        waiting_users.append(user_id)
        await update.message.reply_text("🔍 Searching for a chat partner... Please wait.")

# -------------------- Leave Chat --------------------

async def leave_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Disconnects a user from an active chat """
    user_id = update.message.from_user.id

    if user_id in active_chats:
        partner_id = active_chats.pop(user_id)
        active_chats.pop(partner_id, None)

        await context.bot.send_message(partner_id, "❌ Your chat partner has left.")
        await update.message.reply_text("✅ You have left the chat.")
    else:
        await update.message.reply_text("❌ You are not in a chat.")

# -------------------- Handle Messages --------------------

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Handles messages between matched users """
    user_id = update.message.from_user.id

    if user_id not in active_chats:
        await update.message.reply_text("❌ You are not in a chat. Use /find to find a partner.")
        return

    partner_id = active_chats[user_id]
    await context.bot.send_message(partner_id, update.message.text)

# -------------------- Bot Initialization --------------------

async def main():
    """ Initialize Bot """
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(confirm, pattern="confirm"))
    app.add_handler(CommandHandler("find", find_partner))
    app.add_handler(CommandHandler("leave", leave_chat))
    app.add_handler(CallbackQueryHandler(check_referrals, pattern="check_referrals"))
    app.add_handler(MessageHandler(filters.TEXT, handle_messages))

    print("🤖 Bankai Bot is running...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
