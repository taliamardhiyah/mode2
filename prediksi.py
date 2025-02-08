import requests
import asyncio
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import time
from collections import deque, Counter

# Konfigurasi Bot Telegram
TOKEN = "8032741463:AAHg7AuM63zu64HiNEoCSF3XwpPbY9lbYDw"
CHAT_IDS = [-1001460863353]  # Ubah ke daftar

# URL API
API_URL = "https://didihub20.com/api/main/lottery/rounds?page=1&count=20&type=2"

# Tabel Kompensasi (taruhan progresif jika kalah)
KOMPEN_TABLE = [1000, 3000, 6000, 16000, 32000, 80000, 160000, 350000, 800000, 
                1700000, 4000000, 8000000, 18000000, 50000000]

# Pola Prediksi: "B K B B K K"
PREDICTION_PATTERN = ["B", "K", "B", "B", "K", "K"]
pattern_index = 0  # Menyimpan posisi dalam pola prediksi

# Riwayat prediksi dan kekalahan
history = deque(maxlen=20)
loss_streak = 0  # Menghitung kekalahan berturut-turut

# Menyimpan periode terakhir yang sudah dikirim
last_sent_period = None
current_bet_index = 0  # Index untuk tabel kompensasi (mulai dari 1000)
current_bet_amount = KOMPEN_TABLE[current_bet_index]  # Taruhan awal

# Mapping CHAT_ID ke URL yang berbeda
GROUP_REGISTER_LINKS = {
    "-1001513372321": "https://www.didihub.net",
    "-1001460863353": "https://didihub20.com/register?spreadCode=MCYET",
}

GROUP_JOIN_LINKS = {
    "-1001513372321": "t.me/YASSATRADERPRO",
    "-1001460863353": "https://t.me/adaakuyea",
}

# Fungsi untuk mengambil data dari API
def get_lottery_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()["items"]
        else:
            print("Gagal mengambil data dari API.")
            return []
    except Exception as e:
        print(f"Error saat mengambil data API: {e}")
        return []

# Fungsi untuk mengecek apakah taruhan menang atau kalah
def check_win_loss(prediction, last_result):
    result_type = "K" if 0 <= last_result <= 4 else "B"
    status = "WIN✅" if prediction == result_type else "MIN☑️"
    return status, last_result, result_type

# Fungsi untuk menentukan angka yang sering muncul
def get_most_frequent_trend(data):
    numbers = [item["number"] for item in data]
    counter = Counter(numbers)
    
    if not counter:
        return "B"  # Default jika data kosong
    
    # Hitung jumlah kemunculan kategori B dan K
    big_count = sum(count for num, count in counter.items() if num >= 5)
    small_count = sum(count for num, count in counter.items() if num <= 4)
    
    return "B" if big_count >= small_count else "K"

# Fungsi untuk mengirim pesan dengan tombol URL
async def send_telegram_message(message, chat_id):
    bot = telegram.Bot(token=TOKEN)

    # Buat dua tombol URL sesuai dengan chat_id
    keyboard = [
        [InlineKeyboardButton("🔗 DAFTAR RESMI", url=GROUP_REGISTER_LINKS.get(chat_id, "https://www.didihub.net/"))],
        [InlineKeyboardButton("🔗 JOIN HUB", url=GROUP_JOIN_LINKS.get(chat_id, "https://t.me/YASSATRADERPRO"))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    async with bot:
        try:
            await bot.send_message(chat_id=chat_id, text=message, reply_markup=reply_markup)
        except telegram.error.BadRequest as e:
            print(f"Error sending message to {chat_id}: {e}")

# Fungsi utama (looping terus menerus)
async def main():
    global last_sent_period, current_bet_index, current_bet_amount, pattern_index, loss_streak

    while True:
        data = get_lottery_data()
        
        if data:
            last_period = int(data[0]["period"])  # Periode terakhir dalam data
            last_result = data[0]["number"]  # Hasil angka periode terakhir
            next_period = last_period + 1  # Periode berikutnya
            
            # Ambil 3 angka terakhir dari periode
            short_last_period = str(last_period)[-3:]
            short_next_period = str(next_period)[-3:]
            
            # Jika periode baru, lakukan prediksi dan evaluasi hasil sebelumnya
            if last_period != last_sent_period:
                # Gunakan pola prediksi kecuali kalah 3x berturut-turut
                if loss_streak >= 3:
                    prediction = get_most_frequent_trend(data)
                else:
                    prediction = PREDICTION_PATTERN[pattern_index]
                    pattern_index = (pattern_index + 1) % len(PREDICTION_PATTERN)  # Geser ke pola berikutnya
                
                # Cek hasil taruhan
                status, result_number, result_type = check_win_loss(prediction, last_result)

                # Simpan nilai taruhan sebelum diperbarui
                bet_amount = current_bet_amount  

                # Update taruhan untuk periode berikutnya
                if status == "WIN✅":
                    current_bet_index = 0  # Reset taruhan ke 1000 jika menang
                    loss_streak = 0  # Reset hitungan kalah berturut-turut
                else:
                    current_bet_index = min(current_bet_index + 1, len(KOMPEN_TABLE) - 1)  # Naikkan level taruhan
                    loss_streak += 1  # Tambah hitungan kalah berturut-turut
                
                # Update nilai taruhan yang akan digunakan di periode berikutnya
                current_bet_amount = KOMPEN_TABLE[current_bet_index]  

                # Simpan ke riwayat dengan taruhan yang benar
                history.append(f"{short_last_period}|{result_type} {result_number}     |{prediction} {bet_amount} {status} |")

                # Debugging: Cetak di layar untuk cek menang/kalah
                print("\n==== DEBUG INFO ====")
                print(f"Periode: {short_last_period}")
                print(f"Prediksi: {prediction}")
                print(f"Taruhan: {bet_amount}")
                print(f"Hasil: {result_number} ({result_type})")
                print(f"Status: {status}")
                print(f"Streak Kalah: {loss_streak}")
                print("====================\n")

                # Format pesan riwayat prediksi
                history_message = "📌 Riwayat Prediksi DIDIHUB\n\nWINGO CEPAT\nNo | Hasil |Betting Win Los|\n" + "\n".join(history)

                # Kirim ke Telegram dengan tombol
                for chat_id in CHAT_IDS:
                    await send_telegram_message(history_message, chat_id)

                # Kirim prediksi baru dengan taruhan yang diperbarui
                prediction_message = f"📢 Prediksi Server: WINGO CEPAT\n🎯 Periode: {short_next_period}\n📊 Prediksi: {prediction}\n💰 Taruhan: {current_bet_amount}"
                print(prediction_message)  # Cetak di layar juga
                for chat_id in CHAT_IDS:
                    await send_telegram_message(prediction_message, chat_id)

                last_sent_period = last_period  # Simpan periode terakhir yang dikirim

        await asyncio.sleep(5)  # Cek API setiap 5 detik

# Jalankan program
asyncio.run(main())
