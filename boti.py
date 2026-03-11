# =========================================
# ShadowCipher Bot – ALL IN ONE (FIXED)
# AES-grade File & Message Encryption
# Permanent Reply Keyboard
# =========================================

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from cryptography.fernet import Fernet
import asyncio, tempfile, os

BOT_TOKEN = "8533340369:AAERWYB-gZZMiNSxp5PnXJJNpyiEbvT-wGk"
sessions = {}

# =========================
# Permanent Keyboard
# =========================
MENU = ReplyKeyboardMarkup(
    [
        ["🔒 Encrypt Message", "🔓 Decrypt Message"],
        ["📎 Encrypt File", "📂 Decrypt File"],
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# =========================
# Crypto Helpers
# =========================
def gen_key():
    return Fernet.generate_key()

def enc_text(text, key):
    return Fernet(key).encrypt(text.encode()).decode()

def dec_text(cipher, key):
    return Fernet(key).decrypt(cipher.encode()).decode()

def enc_file_bytes(data, key):
    return Fernet(key).encrypt(data)

def dec_file_bytes(data, key):
    return Fernet(key).decrypt(data)

# =========================
# Auto Delete
# =========================
async def auto_del(msg, t):
    await asyncio.sleep(t)
    try:
        await msg.delete()
    except:
        pass

# =========================
# Start
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🕵️‍♂️ ShadowCipher Bot\nSecure File & Message Encryption",
        reply_markup=MENU
    )

# =========================
# Text Handler
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    txt = update.message.text.strip()

    if txt == "🔒 Encrypt Message":
        sessions[chat] = {"mode": "enc_text"}
        await update.message.reply_text("✍️ Send message", reply_markup=MENU)
        return

    if txt == "🔓 Decrypt Message":
        sessions[chat] = {"mode": "dec_text", "step": 1}
        await update.message.reply_text("📦 Send encrypted text", reply_markup=MENU)
        return

    if txt == "📎 Encrypt File":
        sessions[chat] = {"mode": "enc_file"}
        await update.message.reply_text("📎 Send file", reply_markup=MENU)
        return

    if txt == "📂 Decrypt File":
        sessions[chat] = {"mode": "dec_file", "step": 1}
        await update.message.reply_text("📎 Send encrypted file (.enc)", reply_markup=MENU)
        return

    if chat not in sessions:
        return

    s = sessions[chat]

    # Encrypt text
    if s["mode"] == "enc_text":
        key = gen_key()
        cipher = enc_text(txt, key)
        msg = await update.message.reply_text(
            f"🔐 Encrypted:\n{cipher}\n\n🗝 Key:\n{key.decode()}",
            reply_markup=MENU
        )
        asyncio.create_task(auto_del(msg, 30))
        sessions.pop(chat)

    # Decrypt text
    elif s["mode"] == "dec_text":
        if s["step"] == 1:
            s["cipher"] = txt
            s["step"] = 2
            await update.message.reply_text("🔑 Send key", reply_markup=MENU)
        else:
            try:
                plain = dec_text(s["cipher"], txt.encode())
                msg = await update.message.reply_text(f"✅ Decrypted:\n{plain}", reply_markup=MENU)
            except:
                msg = await update.message.reply_text("❌ Wrong key", reply_markup=MENU)
            asyncio.create_task(auto_del(msg, 30))
            sessions.pop(chat)

    # File decryption key
    elif s["mode"] == "dec_file" and s["step"] == 2:
        try:
            with open(s["path"], "rb") as f:
                enc_data = f.read()

            dec_data = dec_file_bytes(enc_data, txt.encode())

            out_path = os.path.join(tempfile.gettempdir(), s["orig_name"])
            with open(out_path, "wb") as f:
                f.write(dec_data)

            await update.message.reply_document(
                open(out_path, "rb"),
                caption="✅ File decrypted (Original format restored)",
                reply_markup=MENU
            )

            os.remove(out_path)

        except:
            await update.message.reply_text("❌ Wrong key or corrupted file", reply_markup=MENU)
        finally:
            os.remove(s["path"])
            sessions.pop(chat)

# =========================
# File Handler
# =========================
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat.id
    if chat not in sessions:
        return

    s = sessions[chat]
    doc = update.message.document

    tmp_path = tempfile.mktemp()
    file = await doc.get_file()
    await file.download_to_drive(tmp_path)

    # Encrypt file
    if s["mode"] == "enc_file":
        with open(tmp_path, "rb") as f:
            data = f.read()

        key = gen_key()
        enc_data = enc_file_bytes(data, key)

        enc_name = doc.file_name + ".enc"
        enc_path = os.path.join(tempfile.gettempdir(), enc_name)

        with open(enc_path, "wb") as f:
            f.write(enc_data)

        await update.message.reply_document(
            open(enc_path, "rb"),
            caption=f"🗝 Key:\n{key.decode()}",
            reply_markup=MENU
        )

        os.remove(tmp_path)
        os.remove(enc_path)
        sessions.pop(chat)

    # Decrypt file
    elif s["mode"] == "dec_file":
        s["path"] = tmp_path
        s["orig_name"] = doc.file_name.replace(".enc", "")
        s["step"] = 2
        await update.message.reply_text("🔑 Send key", reply_markup=MENU)

# =========================
# Main
# =========================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    print("🤖 ShadowCipher Bot running (FILE FIXED)")
    app.run_polling()

if __name__ == "__main__":
    main()
