import ccxt
import random
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8662446897:AAEZIaZ9tWtbeK-vy7H4MG4uUbgrN5Pgu_I"
GEMINI_KEY = "AIzaSyDDa02t_y2HYp33IwGR_ksXOoax-XDOUfI"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")
import requests

def get_price_data(coin):
    url = f"https://api.coingecko.com/api/v3/coins/{coin.lower()}/market_chart?vs_currency=usd&days=1&interval=hourly"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    prices = r.json()["prices"]
    return prices

TOP_COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "MATIC", "DOT"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("⚡ سكالبينغ", callback_data="scalping")],
        [InlineKeyboardButton("📊 سوينغ", callback_data="swing")],
        [InlineKeyboardButton("🎯 بوزيشن", callback_data="position")],
    ]
    await update.message.reply_text("مرحبا! اختر نمط التداول:", reply_markup=InlineKeyboardMarkup(keyboard))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data in ["scalping", "swing", "position"]:
        context.user_data["style"] = query.data
        keyboard = [
            [InlineKeyboardButton("🔵 سبوت", callback_data="spot")],
            [InlineKeyboardButton("🔴 فيوتشر", callback_data="futures")],
        ]
        await query.edit_message_text("اختر نوع السوق:", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data in ["spot", "futures"]:
        context.user_data["market"] = query.data
        keyboard = [
            [InlineKeyboardButton("🎲 توصية عشوائية", callback_data="random_coin")],
            [InlineKeyboardButton("✍️ اختار عملة بنفسك", callback_data="custom_coin")],
        ]
        await query.edit_message_text("كيف تبي الإشارة؟", reply_markup=InlineKeyboardMarkup(keyboard))

    elif query.data == "random_coin":
        coin = random.choice(TOP_COINS)
        context.user_data["coin"] = coin
        await query.edit_message_text(f"✅ تم!\nالعملة المختارة: {coin}\nاكتب /signal للإشارة")

    elif query.data == "custom_coin":
        context.user_data["waiting_coin"] = True
        await query.edit_message_text("اكتب اسم العملة (مثال: BTC أو SOL):")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_coin"):
        coin = update.message.text.upper().strip()
        context.user_data["coin"] = coin
        context.user_data["waiting_coin"] = False
        await update.message.reply_text(f"✅ تم!\nالعملة: {coin}\nاكتب /signal للإشارة")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري التحليل...")

    style = context.user_data.get("style", "swing")
    market = context.user_data.get("market", "spot")
    coin = context.user_data.get("coin", "BTC")

    prices = get_price_data(coin)
if not prices:
    await update.message.reply_text(f"❌ العملة {coin} مو موجودة، جرب عملة ثانية.")
    return
candles = "\n".join([f"السعر: {p[1]:.2f}$" for p in prices[-10:]])

    prompt = f"""أنت محلل SMC محترف. حلل هاي البيانات لـ {coin}/USDT:

{candles}

النمط: {style} | السوق: {market}

أعطني إشارة بهالشكل:
🪙 الزوج: {coin}/USDT
📈 الاتجاه: 
🎯 Entry: 
🛑 Stop Loss: 
✅ TP1: 
✅ TP2: 
📊 SMC: (order block / FVG / BOS)
⚠️ الخلاصة:"""

    response = model.generate_content(prompt)
    await update.message.reply_text(response.text)

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("البوت شغال...")
    app.run_polling()

if __name__ == "__main__":
    main()