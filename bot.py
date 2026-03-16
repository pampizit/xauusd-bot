import requests
import time
import os
from datetime import datetime, timezone, timedelta

# ── Konfigurasi ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID   = os.environ.get("CHAT_ID")
FETCH_INTERVAL = 15

if not BOT_TOKEN or not CHAT_ID:
    print("[ERROR] BOT_TOKEN dan CHAT_ID harus diset di environment variables!")
    exit(1)

WIB = timezone(timedelta(hours=7))
SR_TOLERANCE = 10  # ±10 poin

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
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False

def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
    params = {"timeout": 1, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(url, params=params, timeout=5)
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
def detect_bos(candles, lookback=5):
    if len(candles) < lookback + 2: return None
    recent = candles[-(lookback+1):]
    last, prev = recent[-1], recent[:-1]
    if last["close"] > max(c["high"] for c in prev): return "BULL"
    if last["close"] < min(c["low"]  for c in prev): return "BEAR"
    return None

def detect_rejection(candle):
    body = abs(candle["close"] - candle["open"])
    upper_wick = candle["high"] - max(candle["open"], candle["close"])
    lower_wick = min(candle["open"], candle["close"]) - candle["low"]
    total = candle["high"] - candle["low"]
    if total == 0: return None
    if lower_wick > body * 1.5 and lower_wick > total * 0.4: return "BULLISH"
    if upper_wick > body * 1.5 and upper_wick > total * 0.4: return "BEARISH"
    return None

def calc_fib(lo, hi):
    r = hi - lo
    return {
        "f0":   round(hi, 2),
        "f382": round(hi - r * 0.382, 2),
        "f618": round(hi - r * 0.618, 2),
        "f100": round(lo, 2),
    }

# ── Auto S&R dari PDH/PDL & Weekly ───────────────────────
def calc_auto_sr(candles):
    if len(candles) < 2: return []
    levels = []
    # Previous Day High/Low (288 candle M5 = 1 hari)
    day_candles = candles[-288:-1] if len(candles) >= 288 else candles[:-1]
    if day_candles:
        pdh = max(c["high"] for c in day_candles)
        pdl = min(c["low"]  for c in day_candles)
        levels.append({"price": pdh, "label": "PDH (High Kemarin)", "type": "resistance"})
        levels.append({"price": pdl, "label": "PDL (Low Kemarin)",  "type": "support"})
    # Weekly High/Low (2016 candle M5 = 1 minggu)
    week_candles = candles[-2016:-1] if len(candles) >= 2016 else candles[:-1]
    if week_candles:
        wkh = max(c["high"] for c in week_candles)
        wkl = min(c["low"]  for c in week_candles)
        levels.append({"price": wkh, "label": "Weekly High", "type": "resistance"})
        levels.append({"price": wkl, "label": "Weekly Low",  "type": "support"})
    return levels

# ── State ─────────────────────────────────────────────────
state = {
    "candles":      [],
    "cur_candle":   None,
    "prev_price":   None,
    "asia_lo":      None,
    "asia_hi":      None,
    "fib":          None,
    "fib_locked":   False,
    "buy_done":     False,
    "sell_done":    False,
    "buy2_done":    False,
    "alerted":      set(),
    "last_day":     None,
    "manual_sr":    [],        # level manual dari user
    "sr_alerted":   set(),     # tracking alert S&R
    "last_update":  0,         # untuk polling Telegram command
}

def reset_daily():
    today = now_wib().strftime("%Y-%m-%d")
    if state["last_day"] == today: return
    print(f"[RESET] Hari baru: {today}")
    state.update({
        "asia_lo": None, "asia_hi": None,
        "fib": None, "fib_locked": False,
        "buy_done": False, "sell_done": False, "buy2_done": False,
        "alerted": set(), "sr_alerted": set(),
        "cur_candle": None, "last_day": today
    })
    send_telegram(
        f"🔄 *Reset Harian XAUUSD Bot*\n"
        f"📅 {today}\n🕐 {now_wib().strftime('%H:%M')} WIB\n"
        f"Bot siap monitoring!\n\n"
        f"📌 *Level Manual aktif:*\n" +
        ("\n".join([f"• {s['label']}: *${s['price']:.2f}*" for s in state["manual_sr"]])
         if state["manual_sr"] else "Belum ada. Kirim /addsr untuk tambah.")
    )

# ── Command Handler ───────────────────────────────────────
def handle_commands():
    updates = get_updates(offset=state["last_update"])
    for upd in updates:
        state["last_update"] = upd["update_id"] + 1
        msg = upd.get("message", {})
        text = msg.get("text", "").strip()
        if not text: continue

        print(f"[CMD] {text}")

        # /addsr 3050.00 Resistance Area
        if text.startswith("/addsr"):
            parts = text.split(" ", 2)
            if len(parts) >= 2:
                try:
                    price = float(parts[1])
                    label = parts[2] if len(parts) > 2 else f"Manual SR ${price:.2f}"
                    sr_type = "support" if len(state["manual_sr"]) % 2 == 0 else "resistance"
                    state["manual_sr"].append({"price": price, "label": label, "type": sr_type})
                    send_telegram(
                        f"✅ *Level S&R Ditambahkan*\n"
                        f"📍 {label}: *${price:.2f}*\n"
                        f"Toleransi: ±{SR_TOLERANCE} poin"
                    )
                except:
                    send_telegram("❌ Format salah. Contoh:\n`/addsr 3050.00 Resistance Area`")
            else:
                send_telegram("❌ Format: `/addsr 3050.00 Nama Level`")

        # /listsr
        elif text == "/listsr":
            auto = calc_auto_sr(state["candles"])
            all_sr = auto + state["manual_sr"]
            if not all_sr:
                send_telegram("Belum ada level S&R.")
            else:
                msg_lines = ["📋 *Level S&R Aktif:*\n"]
                msg_lines.append("*Auto:*")
                for s in auto:
                    msg_lines.append(f"• {s['label']}: *${s['price']:.2f}*")
                if state["manual_sr"]:
                    msg_lines.append("\n*Manual:*")
                    for s in state["manual_sr"]:
                        msg_lines.append(f"• {s['label']}: *${s['price']:.2f}*")
                send_telegram("\n".join(msg_lines))

        # /delsr
        elif text == "/delsr":
            state["manual_sr"] = []
            send_telegram("✅ Semua level S&R manual dihapus.")

        # /status
        elif text == "/status":
            price = state["prev_price"]
            send_telegram(
                f"📊 *Status Bot XAUUSD*\n"
                f"━━━━━━━━━━━━━━\n"
                f"💰 Harga: *${price:.2f}*\n" if price else "💰 Harga: Menunggu...\n"
                f"🌏 Sesi: *{get_session()}*\n"
                f"📍 Low Asia: *${state['asia_lo']:.2f}*\n" if state["asia_lo"] else "📍 Low Asia: Belum ada\n"
                f"📍 High Asia: *${state['asia_hi']:.2f}*\n" if state["asia_hi"] else "📍 High Asia: Belum ada\n"
                f"📐 Fib: {'✅' if state['fib'] else '⏳ Belum'}\n"
                f"📈 BUY Asia: {'✅' if state['buy_done'] else '⏳'}\n"
                f"📉 SELL London: {'✅' if state['sell_done'] else '⏳'}\n"
                f"🔄 BUY 61.8%: {'✅' if state['buy2_done'] else '⏳'}\n"
                f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
            )

        # /help
        elif text == "/help" or text == "/start":
            send_telegram(
                f"🥇 *XAUUSD Bot Commands:*\n"
                f"━━━━━━━━━━━━━━\n"
                f"/status → Lihat status bot & harga\n"
                f"/listsr → Lihat semua level S&R\n"
                f"/addsr [harga] [nama] → Tambah S&R manual\n"
                f"  Contoh: `/addsr 3050.00 Resistance`\n"
                f"/delsr → Hapus semua S&R manual\n"
                f"/help → Tampilkan menu ini\n"
                f"━━━━━━━━━━━━━━\n"
                f"Bot aktif 24 jam • M5 • gold-api.com"
            )

# ── Cek S&R ───────────────────────────────────────────────
def check_sr(candle, all_candles):
    if not market_open(): return
    auto_sr  = calc_auto_sr(all_candles)
    all_sr   = auto_sr + state["manual_sr"]
    price    = candle["close"]
    b        = detect_bos(all_candles)
    rejection = detect_rejection(candle)

    for sr in all_sr:
        level = sr["price"]
        label = sr["label"]
        sr_type = sr["type"]

        # Cek apakah harga dalam zona ±10 poin
        if abs(price - level) > SR_TOLERANCE:
            continue

        # Touch alert
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
            print(f"[SR TOUCH] {label} @ ${price:.2f}")

        # Rejection alert
        if rejection:
            rej_key = f"rej-{label}-{now_wib().strftime('%Y-%m-%d-%H-%M')}"
            if rej_key not in state["sr_alerted"]:
                state["sr_alerted"].add(rej_key)
                rej_emoji = "📈" if rejection == "BULLISH" else "📉"
                action = "BUY" if rejection == "BULLISH" else "SELL"
                send_telegram(
                    f"🕯 *Candle Rejection di {sr_type.upper()}*\n"
                    f"━━━━━━━━━━━━━━\n"
                    f"{rej_emoji} *{action}* Signal\n"
                    f"📍 Level: {label} *${level:.2f}*\n"
                    f"💰 Harga: *${price:.2f}*\n"
                    f"🕯 Pola: {rejection} Rejection\n"
                    f"🕐 {now_wib().strftime('%H:%M:%S')} WIB\n"
                    f"📊 TF: M5"
                )
                print(f"[SR REJECT] {rejection} @ {label} ${price:.2f}")

        # BOS setelah menyentuh S&R
        if b:
            bos_key = f"bos-{label}-{b}-{now_wib().strftime('%Y-%m-%d-%H-%M')}"
            if bos_key not in state["sr_alerted"]:
                state["sr_alerted"].add(bos_key)
                if b == "BULL" and sr_type == "support":
                    send_telegram(
                        f"💥 *BOS Bullish di SUPPORT!*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📈 *KONFIRMASI BUY*\n"
                        f"📍 Support: {label} *${level:.2f}*\n"
                        f"💰 Harga: *${price:.2f}*\n"
                        f"✅ BOS terkonfirmasi M5\n"
                        f"🎯 Target: Resistance terdekat\n"
                        f"🛡 SL: Di bawah support\n"
                        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
                    )
                elif b == "BEAR" and sr_type == "resistance":
                    send_telegram(
                        f"💥 *BOS Bearish di RESISTANCE!*\n"
                        f"━━━━━━━━━━━━━━\n"
                        f"📉 *KONFIRMASI SELL*\n"
                        f"📍 Resistance: {label} *${level:.2f}*\n"
                        f"💰 Harga: *${price:.2f}*\n"
                        f"✅ BOS terkonfirmasi M5\n"
                        f"🎯 Target: Support terdekat\n"
                        f"🛡 SL: Di atas resistance\n"
                        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB"
                    )
                print(f"[SR BOS] {b} @ {label} ${price:.2f}")

# ── Signal BOS Asia/London ────────────────────────────────
def signal(sig_type, price, detail):
    key = f"{sig_type}-{now_wib().strftime('%Y-%m-%d-%H')}"
    if key in state["alerted"]: return
    state["alerted"].add(key)
    labels = {
        "BUY1": "📈 BUY — Sesi Asia",
        "SELL": "📉 SELL — London Open",
        "BUY2": "🔄 BUY ke-2 — Level 61.8%",
    }
    send_telegram(
        f"🥇 *XAUUSD SIGNAL M5*\n"
        f"━━━━━━━━━━━━━━\n"
        f"{labels[sig_type]}\n"
        f"💰 Harga: *${price:.2f}*\n"
        f"{detail}\n"
        f"🕐 {now_wib().strftime('%H:%M:%S')} WIB\n"
        f"━━━━━━━━━━━━━━\n"
        f"⚠️ _Bukan saran investasi_"
    )
    print(f"[SIGNAL] {labels[sig_type]} @ ${price:.2f}")

def process_candle(candle):
    if not market_open(): return
    sess  = get_session()
    all_c = state["candles"]
    b     = detect_bos(all_c)

    # Cek S&R dulu
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
            state["fib"]        = calc_fib(state["asia_lo"], state["asia_hi"])
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

# ── Main Loop ─────────────────────────────────────────────
def main():
    print("=" * 40)
    print("  XAUUSD Auto Alert Bot v2 - M5")
    print("  BOS + Fibonacci + S&R")
    print("=" * 40)

    send_telegram(
        f"🚀 *XAUUSD Bot v2 Started!*\n"
        f"━━━━━━━━━━━━━━\n"
        f"📡 API: gold-api.com (unlimited)\n"
        f"📊 Timeframe: M5\n"
        f"🆕 *Fitur Baru: S&R Alert!*\n"
        f"• Harga menyentuh S&R\n"
        f"• Candle rejection di S&R\n"
        f"• BOS konfirmasi di S&R\n\n"
        f"Ketik /help untuk lihat commands\n"
        f"🕐 {now_wib().strftime('%d %b %Y %H:%M')} WIB"
    )

    while True:
        try:
            reset_daily()
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
                        state["candles"] = state["candles"][-2016:] + [closed]
                        process_candle(closed)
                    state["cur_candle"] = {"mk": mk, "open": price, "high": price, "low": price, "close": price}
                else:
                    c = state["cur_candle"]
                    c["high"]  = max(c["high"], price)
                    c["low"]   = min(c["low"],  price)
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
