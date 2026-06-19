import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# إعداد السجلات
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

BOT_TOKEN = "8972405767:AAEZbdl-c_jasyLpNShT-uur3IfwAY370rU"

# تخزين بيانات المزاد والنقاط
user_points = {}  # مثال: {user_id: points}
auction_state = {
    "active": False,
    "phase": "join",
    "creator_id": None,
    "item": "",
    "participants": set(),
    "current_bid": 0,
    "highest_bidder": None,
    "msg_id": None,
    "chat_id": None
}

async def setup_auction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auction_state
    if auction_state["active"]:
        await update.message.reply_text("❌ هناك مزاد قائم بالفعل!")
        return
    if not context.args:
        await update.message.reply_text("📝 يرجى تحديد الشيء المراد المزايدة عليه.\nمثال: `/auction لقب الملك`", parse_mode="Markdown")
        return
        
    auction_state.update({
        "active": True,
        "phase": "join",
        "creator_id": update.effective_user.id,
        "item": " ".join(context.args),
        "participants": set(),
        "current_bid": 0,
        "highest_bidder": None,
        "chat_id": update.effective_chat.id
    })
    
    keyboard = [[InlineKeyboardButton("انضمام للمزاد ✋", callback_data="join_auction")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📢 **تم فتح باب التسجيل لمزاد جديد!**\n\n📦 **السلعة:** {auction_state['item']}\n\n👥 **المشتركون الحاليون:** 0\n\n⚠️ اضغط على الزر بالأسفل للانضمام."
    msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    auction_state["msg_id"] = msg.message_id

async def handle_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auction_state
    query = update.callback_query
    user = query.from_user
    
    if not auction_state["active"] or auction_state["phase"] != "join":
        await query.answer("❌ لا يوجد تسجيل متاح حالياً.")
        return
        
    if user.id in auction_state["participants"]:
        await query.answer("⚠️ أنت منضم بالفعل للمزاد!")
        return
        
    auction_state["participants"].add(user.id)
    await query.answer("✅ تم تسجيلك بنجاح في المزاد!")
    
    keyboard = [[InlineKeyboardButton("انضمام للمزاد ✋", callback_data="join_auction")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"📢 **تم فتح باب التسجيل لمزاد جديد!**\n\n📦 **السلعة:** {auction_state['item']}\n\n👥 **عدد المشتركين:** {len(auction_state['participants'])}\n\n👤 اطلب من المشرف كتابة 'بدء' لبدء المزايدة."
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def handle_auction_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auction_state
    if not auction_state["active"]:
        return
        
    if update.message.text.strip() == "بدء" and auction_state["phase"] == "join":
        if update.effective_user.id != auction_state["creator_id"]:
            await update.message.reply_text("⚠️ فقط منشئ المزاد يمكنه البدء!")
            return
            
        if len(auction_state["participants"]) < 1:
            await update.message.reply_text("❌ لا يمكن بدء المزاد بدون مشتركين!")
            return
            
        auction_state["phase"] = "bidding"
        keyboard = [
            [
                InlineKeyboardButton("+10 نقاط", callback_data="bid_10"),
                InlineKeyboardButton("+50 نقطة", callback_data="bid_50")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        text = f"⚡️ **بدأت المزايدة الآن!**\n\n📦 **السلعة:** {auction_state['item']}\n💰 **السعر الحالي:** 0 نقطة\n⏱ **الوقت المتبقي:** 45 ثانية!"
        msg = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        auction_state["msg_id"] = msg.message_id
        asyncio.create_task(end_auction_timer(context))

async def handle_bid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global auction_state
    query = update.callback_query
    user = query.from_user
    
    if not auction_state["active"] or auction_state["phase"] != "bidding":
        await query.answer("❌ المزاد غير نشط حالياً.")
        return
        
    if user.id not in auction_state["participants"]:
        await query.answer("❌ يجب أن تكون مسجلاً في المزاد لتتمكن من المزايدة!")
        return
        
    bid_increase = int(query.data.split("_")[1])
    auction_state["current_bid"] += bid_increase
    auction_state["highest_bidder"] = user
    
    await query.answer(f"✅ قمت برفع السعر بمقدار {bid_increase}!")
    
    keyboard = [
        [
            InlineKeyboardButton("+10 نقاط", callback_data="bid_10"),
            InlineKeyboardButton("+50 نقطة", callback_data="bid_50")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = f"⚡️ **المزاد مستمر!**\n\n📦 **السلعة:** {auction_state['item']}\n💰 **أعلى سعر:** {auction_state['current_bid']} نقطة\n👤 **المزايد الحالي:** {user.mention_markdown()}"
    try:
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    except Exception:
        pass

async def end_auction_timer(context: ContextTypes.DEFAULT_TYPE):
    global auction_state
    await asyncio.sleep(45)
    if not auction_state["active"] or auction_state["phase"] != "bidding":
        return
        
    auction_state["active"] = False
    if auction_state["highest_bidder"]:
        text = f"🏁 **انتهى المزاد رسميـاً!**\n\n📦 **السلعة:** {auction_state['item']}\n👑 **الفائز:** {auction_state['highest_bidder'].mention_markdown()}\n💰 **الثمن النهائي:** {auction_state['current_bid']} نقطة."
    else:
        text = f"🏁 **انتهى المزاد بدون فائز لعدم وجود أي مزايدات.**"
        
    await context.bot.send_message(chat_id=auction_state["chat_id"], text=text, parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("auction", setup_auction))
    app.add_handler(CallbackQueryHandler(handle_join, pattern="^join_auction$"))
    app.add_handler(CallbackQueryHandler(handle_bid, pattern="^bid_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_auction_text))
    
    print("🚀 البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == "__main__":
    main()
