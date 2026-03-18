import requests
import time
import os
import math
from datetime import datetime, timezone, timedelta

# ── Konfigurasi ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
FETCH_INTERVAL = 15
SR_TOLERANCE   = 10

if not BOT_TOKEN or not CHAT_ID:
    print("[ERROR] BOT_TOKEN dan CHAT_ID harus diset di environment variables!")
    exit(1)

WIB = timezone(timedelta(hours=7))

def now_wib():
    return datetime.now(WIB)

def get_session():
    t = now_wib().hour + now_wib().minute / 60
    if t < 9:   return "asia"
    if t < 14:  return "pre"
    if t < 22:  return "london"
    return "ny"

def market_open():
    n = datetime.now(timezone.utc)
    d, h = n.weekday(), n.hour
    if d == 6: return False
    if d == 5: return False
    if d == 4 and h >= 22: return False
    return True

# ── Telegram ──────────────────────────────────────────────
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False

def get_updates(offset=None):
    try:
        params = {"timeout": 1, "allowed_updates": ["message"]}
        if offset: params["offset"] = offset
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params=params, timeout=5)
        return r.json().get("result", [])
    except:
        return []

# ── Harga Gold ────────────────────────────────────────────
def fetch_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()["price"])
    except Exception as e:
        print(f"[PRICE ERROR] {e}")
        return None

# ── Indikator ─────────────────────────────────────────────
def detect_bos(candles, lb=5):
    if len(candles) < lb + 2: return None
    rec = candles[-(lb+1):]
    last, prev = rec[-1], rec[:-1]
    if last["close"] > max(c["high"] for c in prev): return "BULL"
    if last["close"] < min(c["low"]  for c in prev): return "BEAR"
    return None

def detect_rejection(c):
    body = abs(c["close"] - c["open"])
    uw   = c["high"] - max(c["open"], c["close"])
    lw   = min(c["open"], c["close"]) - c["low"]
    tot  = c["high"] - c["low"]
    if tot == 0: return None
    if lw > body * 1.5 and lw > tot * 0.4: return "BULLISH"
    if uw > body * 1.5 and uw > tot * 0.4: return "BEARISH"
    return None

def calc_fib(lo, hi):
    r = hi - lo
    return {
        "f0":   round(hi, 2),
        "f382": round(hi - r * 0.382, 2),
        "f618": round(hi - r * 0.618, 2),
        "f100": round(lo, 2),
    }

# ── 🌙 ASTROLOGI ──────────────────────────────────────────
def get_moon_phase():
    now = datetime.now(timezone.utc)
    known_new_moon = datetime(2026, 3, 18, 0, 23, 0, tzinfo=timezone.utc)
    lunar_cycle = 29.53058867
    diff = (now - known_new_moon).total_seconds() / 86400
    phase_days = diff % lunar_cycle
    if phase_days < 0: phase_days += lunar_cycle
    illumination = round((1 - math.cos(2 * math.pi * phase_days / lunar_cycle)) / 2 * 100)
    if phase_days < 1.85:   phase, phase_en = "🌑 New Moon", "new_moon"
    elif phase_days < 7.38: phase, phase_en = "🌒 Waxing Crescent", "waxing_crescent"
    elif phase_days < 9.22: phase, phase_en = "🌓 First Quarter", "first_quarter"
    elif phase_days < 14.77: phase, phase_en = "🌔 Waxing Gibbous", "waxing_gibbous"
    elif phase_days < 16.61: phase, phase_en = "🌕 Full Moon", "full_moon"
    elif phase_days < 22.15: phase, phase_en = "🌖 Waning Gibbous", "waning_gibbous"
    elif phase_days < 23.99: phase, phase_en = "🌗 Last Quarter", "last_quarter"
    else: phase, phase_en = "🌘 Waning Crescent", "waning_crescent"
    return {"phase": phase, "phase_en": phase_en, "days": round(phase_days, 1),
            "illumination": illumination, "days_to_next": round(lunar_cycle - phase_days, 1)}

def get_moon_impact(phase_en):
    impacts = {
        "new_moon":        {"bias": "⚠️ NETRAL — Siklus Baru",       "signal": "neutral",
                            "desc": "New Moon = awal siklus baru. Sering terjadi REVERSAL. Hindari posisi besar.",
                            "trading": "⛔ Hindari posisi besar\n✅ Tunggu konfirmasi arah\n📌 Reversal sering terjadi"},
        "waxing_crescent": {"bias": "📈 BULLISH BIAS",                "signal": "bullish",
                            "desc": "Energi tumbuh. Gold cenderung naik. Setup BUY lebih disukai.",
                            "trading": "✅ Fokus BUY di support\n✅ Fibonacci BUY valid\n⚠️ SELL hanya konfirmasi kuat"},
        "first_quarter":   {"bias": "📈 BULLISH KUAT",                "signal": "bullish",
                            "desc": "Momentum naik menguat. Breakout ke atas lebih sering terjadi.",
                            "trading": "✅ BUY setiap pullback\n✅ Breakout resistance valid\n⚠️ Waspada overbought"},
        "waxing_gibbous":  {"bias": "📈 BULLISH — Waspada Puncak",    "signal": "bullish_caution",
                            "desc": "Mendekati puncak siklus. Gold naik tapi momentum melemah.",
                            "trading": "✅ Hold BUY yang profit\n⚠️ Jangan BUY baru besar\n📌 Siap SELL di Full Moon"},
        "full_moon":       {"bias": "📉 BEARISH — Reversal Zone",     "signal": "bearish",
                            "desc": "Puncak siklus. Sering jadi titik reversal dari naik ke turun.",
                            "trading": "✅ Fokus SELL di resistance\n✅ High Full Moon = resistance kuat\n⚠️ BUY sangat berisiko"},
        "waning_gibbous":  {"bias": "📉 BEARISH",                     "signal": "bearish",
                            "desc": "Energi melemah. Gold cenderung turun setelah Full Moon.",
                            "trading": "✅ SELL di resistance\n✅ Fibonacci SELL valid\n⚠️ BUY hanya support sangat kuat"},
        "last_quarter":    {"bias": "📉 BEARISH — Melemah",           "signal": "bearish",
                            "desc": "Momentum turun melemah. Market mulai ranging/konsolidasi.",
                            "trading": "⚠️ Market mulai ranging\n✅ SELL TP lebih kecil\n📌 Siap BUY di New Moon"},
        "waning_crescent": {"bias": "⚠️ NETRAL — Menjelang Reset",    "signal": "neutral",
                            "desc": "Energi paling lemah. Market choppy. Kurangi trading.",
                            "trading": "⛔ Kurangi trading\n⚠️ Banyak fake signal\n📌 Tunggu siklus baru"},
    }
    return impacts.get(phase_en, impacts["new_moon"])

def get_planet_info():
    now = now_wib()
    month, day = now.month, now.day
    planets = []
    if (month == 2 and day >= 15) or month == 3 or (month == 4 and day <= 9):
        planets.append("☿ Mercury Retrograde — Banyak fake move, hati-hati overtrading")
    if (month == 2) or (month == 3 and day <= 25):
        planets.append("♀ Venus di Pisces — Sentiment tidak menentu")
    if month == 3 and day <= 22:
        planets.append("♂ Mars di Pisces — Pergerakan tidak linear, spike tiba-tiba")
    planets.append("♄ Saturn di Aries — Support/Resistance lebih kuat")
    return planets

# ── 🌅 MORNING BRIEFING ───────────────────────────────────
def get_day_name():
    days = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    return days[now_wib().weekday()]

def get_month_name():
    months = ["","Januari","Februari","Maret","April","Mei","Juni",
              "Juli","Agustus","September","Oktober","November","Desember"]
    return months[now_wib().month]

def get_session_schedule():
    return (
        "🌏 Asia:    00:00 – 09:00 WIB\n"
        "⏳ Pre-London: 09:00 – 14:00 WIB\n"
        "🇬🇧 London:  14:00 – 22:00 WIB\n"
        "🇺🇸 New York: 19:00 – 03:00 WIB"
    )

def send_morning_briefing(price):
    now = now_wib()
    moon   = get_moon_phase()
    impact = get_moon_impact(moon["phase_en"])
    planets = get_planet_info()
    day_of_week = get_day_name()
    planet_text = "\n".join([f"  • {p}" for p in planets])

    # Analisa hari berdasarkan nama hari
    if day_of_week in ["Sabtu", "Minggu"]:
        market_status = "🔴 PASAR TUTUP — Istirahat dulu! Persiapkan strategi untuk Senin."
        setup_today = "❌ Tidak ada sesi trading hari ini."
    elif day_of_week == "Senin":
        market_status = "🟡 SENIN — Range Asia sering tidak terbentuk sempurna. Hati-hati!"
        setup_today = "⚠️ Skip sesi Asia, fokus London & NY"
    elif day_of_week == "Jumat":
        market_status = "🟡 JUMAT — Pasar tutup jam 23:00 WIB. Jangan hold posisi ke weekend!"
        setup_today = "⚠️ Close semua posisi sebelum jam 22:00 WIB"
    else:
        market_status = "🟢 PASAR BUKA — Hari trading normal!"
        setup_today = (
            f"✅ Sesi Asia: Cari Low Asia → BUY BOS\n"
            f"✅ London: SELL di High Asia + Fib\n"
            f"✅ 61.8%: BUY ke-2 kalau ada rejection"
        )

    # Bias teknikal berdasarkan moon
    if impact["signal"] == "bullish":
        tech_bias = "📈 BULLISH — Prioritaskan setup BUY"
        key_levels = (
            f"🎯 Target naik: ${price+50:.0f} → ${price+100:.0f} → ${price+150:.0f}\n"
            f"🛡 Support kuat: ${price-30:.0f} → ${price-60:.0f}"
        )
    elif impact["signal"] == "bearish":
        tech_bias = "📉 BEARISH — Prioritaskan setup SELL"
        key_levels = (
            f"🎯 Target turun: ${price-50:.0f} → ${price-100:.0f} → ${price-150:.0f}\n"
            f"🛡 Resistance: ${price+30:.0f} → ${price+60:.0f}"
        )
    else:
        tech_bias = "⚠️ NETRAL — Tunggu konfirmasi arah"
        key_levels = (
            f"🎯 Range: ${price-50:.0f} – ${price+50:.0f}\n"
            f"🛡 Waspada fake breakout!"
        )

    # Round numbers terdekat
    base = int(price / 100) * 100
    rn_below = base
    rn_above = base + 100
    rn_mid   = base + 50

    send_telegram(
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🌅 *GOLD MORNING BRIEFING*\n"
        f"📅 {day_of_week}, {now.day} {get_month_name()} {now.year}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"☀️ *SELAMAT PAGI, TRADER!*\n"
        f"Ini briefing gold kamu hari ini.\n"
        f"Siapkan kopi dan fokus! ☕\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 *HARGA GOLD SEKARANG*\n"
        f"━━━━━━━━━━━━━━\n"
        f"Harga: *${price:.2f}*\n"
        f"Round di bawah: ${rn_below}\n"
        f"Half round:     ${rn_mid}\n"
        f"Round di atas:  ${rn_above}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📊 *STATUS MARKET*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{market_status}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎯 *BIAS HARI INI*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{tech_bias}\n\n"
        f"{key_levels}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"📋 *SETUP YANG DICARI*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{setup_today}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"⏰ *JADWAL SESI*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{get_session_schedule()}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌙 *ASTROLOGI HARI INI*\n"
        f"━━━━━━━━━━━━━━\n"
        f"Fase Bulan: {moon['phase']}\n"
        f"Illuminasi: {moon['illumination']}%\n"
        f"Bias Astro: {impact['bias']}\n\n"
        f"📝 {impact['desc']}\n\n"
        f"🪐 Planet aktif:\n{planet_text}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 *SARAN HARI INI*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{impact['trading']}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚠️ *REMINDER PENTING*\n"
        f"━━━━━━━━━━━━━━\n"
        f"✅ Selalu tunggu BOS konfirmasi\n"
        f"✅ SL wajib sebelum entry\n"
        f"✅ R:R minimal 1:2\n"
        f"✅ Max 2 trade per hari\n"
        f"❌ Jangan revenge trade!\n"
        f"❌ Jangan FOMO!\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🤖 Bot aktif 24 jam\n"
        f"Ketik /status untuk update\n"
        f"Semangat trading hari ini! 💪🥇\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ _Bukan saran investasi_"
    )
    print(f"[BRIEFING] Morning briefing terkirim jam {now.strftime('%H:%M')} WIB")

# ── Auto S&R ──────────────────────────────────────────────
def get_auto_sr(candles, current_price):
    levels = []
    if len(candles) < 10: return levels
    day = 288
    if len(candles) >= day * 2:
        yesterday = candles[-(day*2):-(day)]
        pdh = round(max(c["high"] for c in yesterday), 2)
        pdl = round(min(c["low"]  for c in yesterday), 2)
        levels.append({"price": pdh, "label": "PDH", "type": "resistance"})
        levels.append({"price": pdl, "label": "PDL", "type": "support"})
    week = 2016
    if len(candles) >= week:
        wk = candles[-week:]
        levels.append({"price": round(max(c["high"] for c in wk), 2), "label": "Weekly High", "type": "resistance"})
        levels.append({"price": round(min(c["low"]  for c in wk), 2), "label": "Weekly Low",  "type": "support"})
    base = int(current_price / 100) * 100
    for mult in range(-3, 5):
        rn = base + mult * 100
        if rn > 0 and abs(current_price - rn) <= 150:
            levels.append({"price": float(rn), "label": f"Round ${rn}", "type": "resistance" if rn > current_price else "support"})
    unique = []
    for lv in sorted(levels, key=lambda x: x["price"]):
        if not unique or abs(lv["price"] - unique[-1]["price"]) >= 5:
            unique.append(lv)
    return unique

# ── State ─────────────────────────────────────────────────
state = {
    "candles": [], "cur_candle": None, "prev_price": None,
    "asia_lo": None, "asia_hi": None, "fib": None, "fib_locked": False,
    "buy_done": False, "sell_done": False, "buy2_done": False,
    "alerted": set(), "sr_alerted": set(), "last_day": None,
    "last_update": 0, "briefing_sent": False,
}

def reset_daily():
    today = now_wib().strftime("%Y-%m-%d")
    if state["last_day"] == today: return
    print(f"[RESET] Hari baru: {today}")
    state.update({
        "asia_lo": None, "asia_hi": None, "fib": None, "fib_locked": False,
        "buy_done": False, "sell_done": False, "buy2_done": False,
        "alerted": set(), "sr_alerted": set(), "cur_candle": None,
        "last_day": today, "briefing_sent": False,
    })

def check_morning_briefing():
    """Kirim morning briefing jam 07:00 WIB"""
    now = now_wib()
    if now.hour == 7 and now.minute < 1 and not state["briefing_sent"]:
        price = state["prev_price"]
        if price:
            state["briefing_sent"] = True
            send_morning_briefing(price)

def signal(sig_type, price, detail):
    key = f"{sig_type}-{now_wib().strftime('%Y-%m-%d-%H')}"
    if key in state["alerted"]: return
    state["alerted"].add(key)
    labels = {
        "BUY1": "📈 BUY — Sesi Asia",
        "SELL": "📉 SELL — London Open",
        "BUY2": "🔄 BUY ke-2 — Level 61.8%",
    }
    moon   = get_moon_phase()
    impact = get_moon_impact(moon["phase_en"])
    send_telegram(
        f"🥇 *XAUUSD SIGNAL M5*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{labels[sig_type]}\n"
        f"💰 Harga: *${price:.2f}*\n"
        f"{detail}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌙 {moon['phase']} | Bias: {impact['bias']}\n"
        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB\n"
        f"⚠️ _Bukan saran investasi_"
    )
    print(f"[SIGNAL] {labels[sig_type]} @ ${price:.2f}")

def check_sr(candle, all_candles):
    if not market_open(): return
    price = candle["close"]
    b = detect_bos(all_candles)
    rej = detect_rejection(candle)
    for sr in get_auto_sr(all_candles, price):
        level, label, sr_type = sr["price"], sr["label"], sr["type"]
        if abs(price - level) > SR_TOLERANCE: continue
        touch_key = f"touch-{label}-{now_wib().strftime('%Y-%m-%d-%H')}"
        if touch_key not in state["sr_alerted"]:
            state["sr_alerted"].add(touch_key)
            emoji = "🔴" if sr_type == "resistance" else "🟢"
            send_telegram(
                f"📍 *Harga Menyentuh {sr_type.upper()}*\n"
                f"━━━━━━━━━━━━━━\n"
                f"{emoji} {label}: *${level:.2f}*\n"
                f"💰 Harga: *${price:.2f}*\n"
                f"📏 Jarak: {abs(price-level):.1f} poin\n"
                f"🕐 {now_wib().strftime('%H:%M:%S')} WIB\n"
                f"⏳ _Tunggu konfirmasi candle..._"
            )
        if rej:
            rej_key = f"rej-{label}-{now_wib().strftime('%Y-%m-%d-%H-%M')}"
            if rej_key not in state["sr_alerted"]:
                state["sr_alerted"].add(rej_key)
                action = "BUY 📈" if rej == "BULLISH" else "SELL 📉"
                send_telegram(
                    f"🕯 *Rejection di {sr_type.upper()}!*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"*{action}* Signal\n"
                    f"📍 {label}: *${level:.2f}*\n"
                    f"💰 Harga: *${price:.2f}*\n"
                    f"🕯 Pola: {rej} Rejection\n"
                    f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
                )
        if b:
            bos_key = f"bos-{label}-{b}-{now_wib().strftime('%Y-%m-%d-%H-%M')}"
            if bos_key not in state["sr_alerted"]:
                state["sr_alerted"].add(bos_key)
                if b == "BULL" and sr_type == "support":
                    send_telegram(
                        f"💥 *BOS Bullish di SUPPORT!*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📈 *KONFIRMASI BUY*\n"
                        f"📍 {label}: *${level:.2f}*\n"
                        f"💰 Harga: *${price:.2f}*\n"
                        f"✅ BOS M5 terkonfirmasi\n"
                        f"🎯 Target: Resistance terdekat\n"
                        f"🛡 SL: Di bawah {label}\n"
                        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
                    )
                elif b == "BEAR" and sr_type == "resistance":
                    send_telegram(
                        f"💥 *BOS Bearish di RESISTANCE!*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📉 *KONFIRMASI SELL*\n"
                        f"📍 {label}: *${level:.2f}*\n"
                        f"💰 Harga: *${price:.2f}*\n"
                        f"✅ BOS M5 terkonfirmasi\n"
                        f"🎯 Target: Support terdekat\n"
                        f"🛡 SL: Di atas {label}\n"
                        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
                    )

def process_candle(candle):
    if not market_open(): return
    sess  = get_session()
    all_c = state["candles"]
    b     = detect_bos(all_c)
    check_sr(candle, all_c)
    if sess == "asia":
        state["asia_lo"] = candle["low"]  if state["asia_lo"] is None else min(state["asia_lo"], candle["low"])
        state["asia_hi"] = candle["high"] if state["asia_hi"] is None else max(state["asia_hi"], candle["high"])
        if b == "BULL" and not state["buy_done"]:
            state["buy_done"] = True
            signal("BUY1", candle["close"],
                f"📍 Low Asia: *${state['asia_lo']:.2f}*\n"
                f"🎯 Target: High Asia *${state['asia_hi']:.2f}*\n"
                f"🛡 SL: Di bawah Low Asia\n📊 TF: M5")
    if sess in ("pre", "london"):
        if state["asia_lo"] and state["asia_hi"] and not state["fib_locked"]:
            state["fib"] = calc_fib(state["asia_lo"], state["asia_hi"])
            state["fib_locked"] = True
            f = state["fib"]
            send_telegram(
                f"📐 *Fibonacci Terbentuk*\n"
                f"━━━━━━━━━━━━━━\n"
                f"🟦 Low Asia:  *${f['f100']:.2f}*\n"
                f"🟡 38.2%:    *${f['f382']:.2f}*\n"
                f"🔴 61.8%:    *${f['f618']:.2f}*\n"
                f"🟢 High Asia: *${f['f0']:.2f}*\n"
                f"🕐 {now_wib().strftime('%H:%M')} WIB"
            )
    if sess == "london" and state["asia_hi"] and state["fib"]:
        hi, f = state["asia_hi"], state["fib"]
        if abs(candle["close"] - hi) <= 8 and b == "BEAR" and not state["sell_done"]:
            state["sell_done"] = True
            signal("SELL", candle["close"],
                f"📍 High Asia: *${hi:.2f}*\n"
                f"🎯 TP: 61.8% *${f['f618']:.2f}*\n"
                f"🛡 SL: Di atas High Asia\n📊 TF: M5")
        if abs(candle["close"] - f["f618"]) <= 8 and b == "BULL" and not state["buy2_done"]:
            state["buy2_done"] = True
            signal("BUY2", candle["close"],
                f"📍 Level 61.8%: *${f['f618']:.2f}*\n"
                f"🎯 TP: High Asia *${hi:.2f}*\n"
                f"🛡 SL: Bawah 61.8%\n📊 TF: M5")

# ── Command Handler ───────────────────────────────────────
def handle_commands():
    updates = get_updates(offset=state["last_update"])
    for upd in updates:
        state["last_update"] = upd["update_id"] + 1
        text = upd.get("message", {}).get("text", "").strip()
        if not text: continue
        print(f"[CMD] {text}")

        if text in ("/start", "/help"):
            send_telegram(
                f"🥇 *XAUUSD Bot v5 — Morning Briefing*\n"
                f"━━━━━━━━━━━━━━\n"
                f"/briefing → Kirim morning briefing sekarang\n"
                f"/status   → Status bot + astrologi\n"
                f"/moon     → Fase bulan detail\n"
                f"/astro    → Info planet hari ini\n"
                f"/listsr   → Level S&R aktif\n"
                f"/help     → Menu ini\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌅 Morning briefing otomatis jam *07:00 WIB*\n"
                f"🤖 Sinyal BOS + S&R + Fibonacci otomatis\n"
                f"🌙 Info astrologi terintegrasi\n"
                f"━━━━━━━━━━━━━━\n"
                f"Bot aktif 24 jam • gold-api.com"
            )

        elif text == "/briefing":
            p = state["prev_price"]
            if p:
                send_morning_briefing(p)
            else:
                send_telegram("⏳ Harga belum tersedia. Coba lagi sebentar.")

        elif text == "/status":
            p       = state["prev_price"] or 0
            moon    = get_moon_phase()
            impact  = get_moon_impact(moon["phase_en"])
            planets = get_planet_info()
            sr_count = len(get_auto_sr(state["candles"], p))
            planet_text = "\n".join([f"  • {pl}" for pl in planets])
            sess_map = {"asia": "🌏 Sesi Asia", "pre": "⏳ Pre-London",
                       "london": "🇬🇧 London", "ny": "🇺🇸 New York"}
            send_telegram(
                f"📊 *STATUS BOT XAUUSD*\n"
                f"━━━━━━━━━━━━━━\n"
                f"💰 Harga: *${p:.2f}*\n"
                f"🌏 Sesi: *{sess_map.get(get_session())}*\n"
                f"📍 Low Asia: *{'$'+str(state['asia_lo']) if state['asia_lo'] else 'Belum ada'}*\n"
                f"📍 High Asia: *{'$'+str(state['asia_hi']) if state['asia_hi'] else 'Belum ada'}*\n"
                f"📐 Fibonacci: {'✅ Aktif' if state['fib'] else '⏳ Belum'}\n"
                f"📈 BUY Asia: {'✅' if state['buy_done'] else '⏳'}\n"
                f"📉 SELL London: {'✅' if state['sell_done'] else '⏳'}\n"
                f"🔄 BUY 61.8%: {'✅' if state['buy2_done'] else '⏳'}\n"
                f"🎯 Level S&R: {sr_count} aktif\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌙 *ASTROLOGI*\n"
                f"━━━━━━━━━━━━━━\n"
                f"{moon['phase']} ({moon['illumination']}%)\n"
                f"Hari ke-{moon['days']} | Sisa {moon['days_to_next']} hari\n\n"
                f"Bias: {impact['bias']}\n"
                f"📝 {impact['desc']}\n\n"
                f"💡 Saran:\n{impact['trading']}\n\n"
                f"🪐 Planet aktif:\n{planet_text}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🕐 {now_wib().strftime('%d %b %Y %H:%M:%S')} WIB"
            )

        elif text == "/moon":
            moon   = get_moon_phase()
            impact = get_moon_impact(moon["phase_en"])
            p      = state["prev_price"] or 0
            send_telegram(
                f"🌙 *FASE BULAN & GOLD*\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌑🌒🌓🌔🌕🌖🌗🌘\n\n"
                f"Fase: {moon['phase']}\n"
                f"Hari ke-{moon['days']} dari 29.5\n"
                f"Illuminasi: {moon['illumination']}%\n"
                f"Sisa: {moon['days_to_next']} hari\n"
                f"━━━━━━━━━━━━━━\n"
                f"📊 Bias: {impact['bias']}\n"
                f"📝 {impact['desc']}\n\n"
                f"💡 {impact['trading']}\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌑 New Moon → Reversal\n"
                f"🌒🌓 Waxing → Gold naik\n"
                f"🌕 Full Moon → High/Reversal\n"
                f"🌖🌗 Waning → Gold turun\n"
                f"🌘 Dark → Volatile"
            )

        elif text == "/astro":
            moon    = get_moon_phase()
            impact  = get_moon_impact(moon["phase_en"])
            planets = get_planet_info()
            planet_text = "\n".join([f"• {p}" for p in planets])
            send_telegram(
                f"🔭 *ASTROLOGI — {now_wib().strftime('%d %b %Y')}*\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌙 {moon['phase']} ({moon['illumination']}%)\n\n"
                f"🪐 Planet aktif:\n{planet_text}\n\n"
                f"📊 Bias: {impact['bias']}\n"
                f"📝 {impact['desc']}\n\n"
                f"💡 Saran:\n{impact['trading']}\n"
                f"━━━━━━━━━━━━━━\n"
                f"⚠️ _Astro = panduan tambahan\n"
                f"Teknikal tetap prioritas!_"
            )

        elif text == "/listsr":
            p = state["prev_price"] or 0
            levels = get_auto_sr(state["candles"], p)
            if not levels:
                send_telegram("⏳ Data S&R belum cukup.")
            else:
                res = sorted([l for l in levels if l["type"] == "resistance" and l["price"] > p], key=lambda x: x["price"])[:5]
                sup = sorted([l for l in levels if l["type"] == "support"    and l["price"] < p], key=lambda x: x["price"], reverse=True)[:5]
                msg = [f"📋 *Level S&R* (harga: ${p:.2f})\n"]
                if res:
                    msg.append("🔴 *Resistance:*")
                    for l in res: msg.append(f"  • {l['label']}: *${l['price']:.2f}* (+{l['price']-p:.1f})")
                if sup:
                    msg.append("\n🟢 *Support:*")
                    for l in sup: msg.append(f"  • {l['label']}: *${l['price']:.2f}* (-{p-l['price']:.1f})")
                send_telegram("\n".join(msg))

# ── Main Loop ─────────────────────────────────────────────
def main():
    print("=" * 45)
    print("  XAUUSD Bot v5 — Morning Briefing Edition")
    print("  BOS + Fib + S&R + Astro + Daily Briefing")
    print("=" * 45)

    moon   = get_moon_phase()
    impact = get_moon_impact(moon["phase_en"])
    send_telegram(
        f"🚀 *XAUUSD Bot v5 Started!*\n"
        f"━━━━━━━━━━━━━━\n"
        f"📡 gold-api.com (unlimited)\n"
        f"📊 Timeframe: M5\n"
        f"🌅 Morning briefing: jam 07:00 WIB\n"
        f"🌙 {moon['phase']} | {impact['bias']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"Ketik /briefing untuk briefing sekarang!\n"
        f"🕐 {now_wib().strftime('%d %b %Y %H:%M')} WIB"
    )

    while True:
        try:
            reset_daily()
            check_morning_briefing()
            handle_commands()
            price = fetch_price()
            if price:
                prev  = state["prev_price"]
                chg   = round(price - prev, 2) if prev else 0
                arrow = "▲" if chg >= 0 else "▼"
                print(f"[{now_wib().strftime('%H:%M:%S')}] ${price:.2f} {arrow}{abs(chg):.2f} | {get_session()} | Lo:{state['asia_lo']} Hi:{state['asia_hi']}")
                mk = int(time.time() // 300)
                if state["cur_candle"] is None or state["cur_candle"]["mk"] != mk:
                    if state["cur_candle"] is not None:
                        closed = {k: state["cur_candle"][k] for k in ["open","high","low","close"]}
                        state["candles"] = state["candles"][-8640:] + [closed]
                        process_candle(closed)
                    state["cur_candle"] = {"mk": mk, "open": price, "high": price, "low": price, "close": price}
                else:
                    c = state["cur_candle"]
                    c["high"] = max(c["high"], price)
                    c["low"]  = min(c["low"],  price)
                    c["close"] = price
                state["prev_price"] = price
        except KeyboardInterrupt:
            print("\n[STOP] Bot dihentikan.")
            send_telegram("⏹ *XAUUSD Bot dihentikan.*")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()
