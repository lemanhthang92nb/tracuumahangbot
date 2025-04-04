import logging
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import pandas as pd
import os
from fuzzywuzzy import process

TOKEN = "8020879390:AAHb6LhBE0LpRO4yMdSBwG_mx8TougYHCyA"
bot = Bot(token=TOKEN)

DATA_FILE = "data.xlsx"
if os.path.exists(DATA_FILE):
    df = pd.read_excel(DATA_FILE)
else:
    df = pd.DataFrame(columns=["Mã hàng", "Tên hàng"])
    df.to_excel(DATA_FILE, index=False)

def save_data():
    df.to_excel(DATA_FILE, index=False)

def tim_gan_dung(text):
    ten_hangs = df["Tên hàng"].dropna().astype(str).tolist()
    ket_qua = process.extract(text, ten_hangs, limit=3)
    return [ten for ten, score in ket_qua if score >= 60]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    huong_dan = (
        "🤖 *Hướng dẫn sử dụng bot tra cứu mã hàng:*

"
        "`//tra <tên hàng hoặc mã hàng>` – Tra cứu thông tin\n"
        "`//them <mã hàng> - <tên hàng>` – Thêm hàng mới\n"
        "`//xoa <mã hàng hoặc tên hàng>` – Xóa hàng\n"
        "`//sua <mã hoặc tên> - <nội dung mới>` – Sửa thông tin\n\n"
        "⏺ Bot hỗ trợ gõ không dấu và tìm gần đúng\n"
        "📁 Dữ liệu tự động lưu vào Excel"
    )
    await update.message.reply_markdown_v2(huong_dan)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global df
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    try:
        lower = text.lower()

        if lower.startswith("//tra") or lower.startswith("//tim"):
            tu_khoa = text[5:].strip().lower()
            ket_qua = df[
                df["Mã hàng"].astype(str).str.lower().str.contains(tu_khoa) |
                df["Tên hàng"].astype(str).str.lower().str.contains(tu_khoa)
            ]
            if not ket_qua.empty:
                tra = "\n".join([f"{row['Mã hàng']} – {row['Tên hàng']}" for _, row in ket_qua.iterrows()])
                await update.message.reply_text(f"Kết quả tìm thấy:\n{tra}")
            else:
                gan_dung = tim_gan_dung(tu_khoa)
                goi_y = "\n".join(gan_dung) if gan_dung else "Không có gợi ý nào gần giống."
                await update.message.reply_text(f"Không tìm thấy. Có thể anh muốn tìm:\n{goi_y}")

        elif lower.startswith("//them"):
            parts = text[6:].split("-")
            if len(parts) == 2:
                ma, ten = parts[0].strip(), parts[1].strip()
                if (df["Mã hàng"] == ma).any() or (df["Tên hàng"].str.lower() == ten.lower()).any():
                    await update.message.reply_text("⚠️ Mã hàng hoặc tên hàng đã tồn tại.")
                else:
                    df.loc[len(df)] = [ma, ten]
                    save_data()
                    await update.message.reply_text("✅ Đã thêm thành công.")
            else:
                await update.message.reply_text("❌ Sai cú pháp. Dùng: //them <mã> - <tên>")

        elif lower.startswith("//xoa") or lower.startswith("//xoá") or lower.startswith("//xóa"):
            tu_khoa = text[5:].strip().lower()
            mask = (df["Mã hàng"].astype(str).str.lower() == tu_khoa) | (df["Tên hàng"].astype(str).str.lower() == tu_khoa)
            if df[mask].empty:
                await update.message.reply_text("❌ Không tìm thấy để xóa.")
            else:
                df = df[~mask]
                save_data()
                await update.message.reply_text("🗑️ Đã xóa thành công.")

        elif lower.startswith("//sua"):
            parts = text[5:].split("-")
            if len(parts) == 2:
                cu, moi = parts[0].strip(), parts[1].strip()
                mask_ma = df["Mã hàng"].astype(str).str.lower() == cu.lower()
                mask_ten = df["Tên hàng"].astype(str).str.lower() == cu.lower()
                if mask_ma.any():
                    df.loc[mask_ma, "Mã hàng"] = moi
                    save_data()
                    await update.message.reply_text("✏️ Đã sửa mã hàng.")
                elif mask_ten.any():
                    df.loc[mask_ten, "Tên hàng"] = moi
                    save_data()
                    await update.message.reply_text("✏️ Đã sửa tên hàng.")
                else:
                    await update.message.reply_text("❌ Không tìm thấy để sửa.")
            else:
                await update.message.reply_text("❌ Sai cú pháp. Dùng: //sua <mã hoặc tên> - <nội dung mới>")
    except Exception as e:
        await update.message.reply_text(f"Lỗi: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()
