import requests
import random
import google.generativeai as genai
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

TOKEN = "8662446897:AAEZIaZ9tWtbeK-vy7H4MG4uUbgrN5Pgu_I"
GEMINI_KEY = "AIzaSyDDa02t_y2HYp33IwGR_ksXOoax-XDOUfI"

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

TOP_COINS = ["bitcoin", "ethereum", "solana", "binancecoin", "ripple", "dogecoin", "cardano", "avalanche-2", "matic-network", "polkadot"]
COIN_NAMES = {"bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL", "binancecoin": "BNB", "ripple": "XRP", "dogecoin": "DOGE", "cardano": "ADA", "avalanche-2": "AVAX", "matic-network": "MATIC", "polkadot": "DOT"}

def get_price_data(coin_id):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart?vs_currency=usd&days=1&interval=hourly"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        prices = r.json()["prices"]
        return prices
    except:
        return None

def search_coin(coin_name):
    try:
        url = f"https://api.coingecko.com/api/v3/search?query={coin_name}"
        r = requests.get(url, timeout=10)
        if r.status_code != 200:
            return None
        results = r.json().get("coins", [])
        if results:
            return results[0]["id"]
        return None
    except:
        return None

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
        coin_id = random.choice(TOP_COINS)
        context.user_data["coin_id"] = coin_id
        context.user_data["coin"] = COIN_NAMES[coin_id]
        await query.edit_message_text(f"✅ تم!\nالعملة المختارة: {COIN_NAMES[coin_id]}\nاكتب /signal للإشارة")

    elif query.data == "custom_coin":
        context.user_data["waiting_coin"] = True
        await query.edit_message_text("اكتب اسم العملة (مثال: BTC أو SOL):")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("waiting_coin"):
        coin_input = update.message.text.strip()
        coin_id = search_coin(coin_input)
        if not coin_id:
            await update.message.reply_text(f"❌ ما لقيت العملة {coin_input}، جرب عملة ثانية.")
            return
        context.user_data["coin_id"] = coin_id
        context.user_data["coin"] = coin_input.upper()
        context.user_data["waiting_coin"] = False
        await update.message.reply_text(f"✅ تم!\nالعملة: {coin_input.upper()}\nاكتب /signal للإشارة")

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ جاري التحليل...")

    style = context.user_data.get("style", "swing")
    market = context.user_data.get("market", "spot")
    coin = context.user_data.get("coin", "BTC")
    coin_id = context.user_data.get("coin_id", "bitcoin")

    prices = get_price_data(coin_id)
    if not prices:
        await update.message.reply_text("❌ ما قدرت أجيب البيانات، جرب بعد شوي.")
        return

    candles = "\n".join([f"السعر: {p[1]:.4f}$" for p in prices[-10:]])

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