import requests
import time
import os
import math
import json
import xml.etree.ElementTree as ET
import re as _re
from datetime import datetime, timezone, timedelta


SINARMAS_CALENDAR = {
    1: {1:"U",2:"O",3:"L",4:"L",5:"O",6:"O",7:"L",8:"L",9:"U",10:"L",
        11:"L",12:"O",13:"U",14:"O",15:"O",16:"L",17:"L",18:"L",19:"L",
        20:"L",21:"U",22:"L",23:"L",24:"O",25:"U",26:"O",27:"L",28:"L",
        29:"L",30:"O",31:"L"},
    2: {1:"O",2:"U",3:"U",4:"L",5:"O",6:"L",7:"U",8:"O",9:"O",10:"L",
        11:"L",12:"O",13:"L",14:"O",15:"U",16:"L",17:"L",18:"O",19:"U",
        20:"O",21:"L",22:"L",23:"O",24:"O",25:"L",26:"L",27:"U",28:"L"},
    3: {1:"U",2:"U",3:"U",4:"O",5:"L",6:"O",7:"O",8:"O",9:"O",10:"L",
        11:"L",12:"U",13:"L",14:"L",15:"U",16:"O",17:"O",18:"O",19:"U",
        20:"L",21:"O",22:"L",23:"O",24:"U",25:"U",26:"L",27:"U",28:"O",
        29:"L",30:"O",31:"L"},
    4: {1:"L",2:"O",3:"L",4:"O",5:"L",6:"U",7:"O",8:"U",9:"O",10:"L",
        11:"O",12:"O",13:"O",14:"O",15:"O",16:"L",17:"L",18:"U",19:"O",
        20:"U",21:"L",22:"O",23:"O",24:"O",25:"L",26:"O",27:"O",28:"L",
        29:"L",30:"U"},
    5: {1:"U",2:"U",3:"L",4:"U",5:"O",6:"L",7:"L",8:"L",9:"O",10:"L",
        11:"O",12:"O",13:"U",14:"U",15:"O",16:"L",17:"L",18:"O",19:"O",
        20:"L",21:"L",22:"O",23:"O",24:"L",25:"U",26:"U",27:"L",28:"O",
        29:"O",30:"L",31:"L"},
    6: {1:"O",2:"O",3:"O",4:"L",5:"L",6:"O",7:"U",8:"O",9:"L",10:"O",
        11:"L",12:"O",13:"O",14:"L",15:"L",16:"L",17:"L",18:"O",19:"U",
        20:"U",21:"L",22:"O",23:"O",24:"O",25:"O",26:"L",27:"L",28:"L",
        29:"L",30:"U"},
    7: {1:"U",2:"O",3:"L",4:"O",5:"L",6:"O",7:"O",8:"L",9:"L",10:"O",
        11:"O",12:"L",13:"U",14:"U",15:"L",16:"L",17:"O",18:"O",19:"L",
        20:"O",21:"L",22:"O",23:"L",24:"O",25:"U",26:"U",27:"L",28:"L",
        29:"L",30:"O",31:"O"},
    8: {1:"O",2:"O",3:"L",4:"O",5:"L",6:"U",7:"U",8:"U",9:"O",10:"O",
        11:"L",12:"U",13:"O",14:"L",15:"O",16:"L",17:"O",18:"U",19:"O",
        20:"U",21:"L",22:"L",23:"L",24:"O",25:"L",26:"L",27:"L",28:"U",
        29:"U",30:"U",31:"L"},
    9: {1:"U",2:"O",3:"L",4:"L",5:"L",6:"O",7:"O",8:"O",9:"O",10:"L",
        11:"U",12:"L",13:"O",14:"U",15:"L",16:"L",17:"O",18:"L",19:"L",
        20:"L",21:"O",22:"U",23:"U",24:"O",25:"L",26:"U",27:"O",28:"L",
        29:"O",30:"L"},
    10:{1:"L",2:"O",3:"L",4:"L",5:"U",6:"L",7:"O",8:"U",9:"U",10:"O",
        11:"L",12:"O",13:"L",14:"O",15:"L",16:"O",17:"U",18:"L",19:"L",
        20:"O",21:"U",22:"U",23:"L",24:"O",25:"L",26:"L",27:"O",28:"U",
        29:"U",30:"O",31:"O"},
    11:{1:"L",2:"U",3:"L",4:"L",5:"O",6:"U",7:"O",8:"O",9:"O",10:"U",
        11:"O",12:"L",13:"L",14:"O",15:"U",16:"L",17:"L",18:"O",19:"L",
        20:"O",21:"O",22:"U",23:"L",24:"L",25:"L",26:"L",27:"U",28:"O",
        29:"L",30:"O"},
    12:{1:"L",2:"O",3:"O",4:"U",5:"O",6:"L",7:"O",8:"L",9:"O",10:"U",
        11:"O",12:"L",13:"O",14:"L",15:"O",16:"U",17:"L",18:"O",19:"O",
        20:"L",21:"U",22:"U",23:"O",24:"L",25:"L",26:"O",27:"U",28:"U",
        29:"L",30:"L",31:"O"},
}


# ── 📈 US 10Y TREASURY YIELD ──────────────────────────
TRUMP_ZONE_LOW  = 4.30
TRUMP_ZONE_HIGH = 4.50

def fetch_us10y_yield():
    try:
        url = (
            f"https://api.stlouisfed.org/fred/series/observations"
            f"?series_id=DGS10"
            f"&api_key={FRED_KEY}"
            f"&sort_order=desc"
            f"&limit=5"
            f"&file_type=json"
        )
        r = requests.get(url, timeout=10)
        data = r.json()
        obs = data.get("observations", [])
        for o in obs:
            if o["value"] != ".":
                return {"yield": float(o["value"]), "date": o["date"]}
        return None
    except Exception as e:
        print(f"[FRED ERROR] {e}")
        return None

def analyze_yield(y):
    if y is None: return None
    val = y["yield"]
    if val > TRUMP_ZONE_HIGH:
        return {"val":val,"zone":"ABOVE","emoji":"🔴","label":f"DI ATAS ZONA ({val:.2f}%)",
                "impact":"📉 BEARISH Gold","desc":"Yield tinggi = USD kuat = Gold tertekan",
                "trump":"⚠️ Belum ada Trump good news","gold":"Fokus SELL di resistance",
                "prob":"Yield turun: 100% (histori) kalau masuk zona"}
    elif TRUMP_ZONE_LOW <= val <= TRUMP_ZONE_HIGH:
        return {"val":val,"zone":"DANGER","emoji":"⚡","label":f"TRUMP DANGER ZONE ({val:.2f}%)",
                "impact":"📈 Potensi BULLISH Gold!","desc":"Historis Trump buat good news = yield turun = Gold naik",
                "trump":"✅ Kemungkinan Trump good news segera! (81% historis)",
                "gold":"⚠️ Waspada reversal BUY! Siapkan setup BUY di support",
                "prob":"81% yield TURUN dalam 5 hari berikutnya!"}
    else:
        return {"val":val,"zone":"BELOW","emoji":"🟢","label":f"DI BAWAH ZONA ({val:.2f}%)",
                "impact":"📈 BULLISH Gold","desc":"Yield rendah = USD lemah = Gold didukung naik",
                "trump":"✅ Zone aman, Trump tidak perlu intervensi","gold":"✅ Fokus BUY di support kuat",
                "prob":"Market relatif tenang dari faktor yield"}

def send_yield_alert(analysis, is_new=False):
    if not analysis: return
    moon   = get_moon_phase()
    impact = get_moon_impact(moon["phase_en"])
    prefix = "🚨 *YIELD ALERT BARU!*" if is_new else "📊 *US 10Y YIELD UPDATE*"
    send_telegram(
        f"{prefix}\n━━━━━━━━━━━━━━\n"
        f"{analysis['emoji']} *{analysis['label']}*\n"
        f"📅 Data: {analysis.get('date','')}\n\n"
        f"💥 *Dampak Gold:*\n{analysis['impact']}\n📝 {analysis['desc']}\n\n"
        f"🇺🇸 *Trump Factor:*\n{analysis['trump']}\n\n"
        f"📊 *Probabilitas:*\n{analysis['prob']}\n\n"
        f"💡 *Strategi Gold:*\n{analysis['gold']}\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌙 {moon['phase']} | {impact['bias']}\n"
        f"🕐 {now_wita().strftime('%H:%M')} WITA\n📡 Sumber: FRED (Federal Reserve)"
    )


# ── 📰 NEWS & ECONOMIC CALENDAR ──────────────────────
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

ECONOMIC_EVENTS = {}

def fetch_gold_news():
    feeds = [
        "https://feeds.finance.yahoo.com/rss/2.0/headline?s=GC=F&region=US&lang=en-US",
        "https://www.investing.com/rss/news_285.rss",
    ]
    articles = []
    for url in feeds:
        try:
            r = requests.get(url, timeout=8, headers={"User-Agent": "Mozilla/5.0"})
            root = ET.fromstring(r.content)
            for item in root.findall(".//item")[:3]:
                title = item.findtext("title", "")
                desc  = item.findtext("description", "")
                pub   = item.findtext("pubDate", "")
                desc  = _re.sub('<[^<]+?>', '', desc)[:200]
                if title:
                    articles.append({"title":title.strip(),"desc":desc.strip(),"pub":pub.strip()})
            if articles: break
        except Exception as e:
            print(f"[RSS] {e}")
            continue
    return articles[:5]

def analyze_news_with_ai(articles, price):
    if not ANTHROPIC_KEY or not articles:
        return None
    try:
        news_text = "\n".join([f"{i+1}. {a['title']}\n   {a['desc']}" for i, a in enumerate(articles)])
        prompt = f"""Kamu adalah analis trading gold profesional.

Harga Gold saat ini: ${price:.2f}

Berita terbaru tentang gold:
{news_text}

Berikan analisa SINGKAT dalam format:
BIAS: [BULLISH/BEARISH/NETRAL]
DAMPAK: [Penjelasan 1 kalimat dampak ke gold]
LEVEL: [Support dan resistance kunci hari ini]
STRATEGI: [1-2 kalimat saran trading]
RISIKO: [1 risiko utama yang perlu diwaspadai]

Jawab dalam Bahasa Indonesia, singkat dan langsung."""

        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-20250514","max_tokens":300,
                  "messages":[{"role":"user","content":prompt}]},
            timeout=15
        )
        data = r.json()
        return data["content"][0]["text"] if data.get("content") else None
    except Exception as e:
        print(f"[AI NEWS] {e}")
        return None

def parse_ai_analysis(text):
    if not text: return {}
    result = {}
    for line in text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip()
    return result

def send_news_briefing(price, is_breaking=False):
    articles = fetch_gold_news()
    if not articles:
        print("[NEWS] No articles found")
        return
    ai_text   = analyze_news_with_ai(articles, price)
    ai_parsed = parse_ai_analysis(ai_text) if ai_text else {}
    bias = ai_parsed.get("BIAS", "NETRAL")
    if "BULLISH" in bias.upper():   bias_emoji = "📈"
    elif "BEARISH" in bias.upper(): bias_emoji = "📉"
    else:                           bias_emoji = "⚠️"
    news_text = ""
    for i, a in enumerate(articles[:3]):
        news_text += f"\n{i+1}. *{a['title'][:80]}*"
        if a["desc"]: news_text += f"\n   _{a['desc'][:100]}_"
    y_data = fetch_us10y_yield()
    yield_text = ""
    if y_data:
        ya = analyze_yield(y_data)
        yield_text = f"\n\n💹 *US 10Y Yield:* {ya['emoji']} {ya['label']}"
    header = "🚨 *BREAKING NEWS GOLD!*" if is_breaking else "📰 *GOLD NEWS UPDATE*"
    moon   = get_moon_phase()
    impact = get_moon_impact(moon["phase_en"])
    msg = (f"{header}\n━━━━━━━━━━━━━━\n💰 Harga: *${price:.2f}*\n"
           f"🕐 {now_wita().strftime('%H:%M')} WITA\n\n📋 *BERITA TERKINI:*{news_text}\n━━━━━━━━━━━━━━\n")
    if ai_text:
        msg += (f"🤖 *ANALISA AI:*\n{bias_emoji} Bias: *{ai_parsed.get('BIAS','?')}*\n")
        if ai_parsed.get("DAMPAK"):  msg += f"💥 {ai_parsed['DAMPAK']}\n"
        if ai_parsed.get("LEVEL"):   msg += f"📊 {ai_parsed['LEVEL']}\n"
        if ai_parsed.get("STRATEGI"):msg += f"💡 {ai_parsed['STRATEGI']}\n"
        if ai_parsed.get("RISIKO"):  msg += f"⚠️ {ai_parsed['RISIKO']}\n"
        msg += "━━━━━━━━━━━━━━\n"
    msg += (f"{yield_text}\n\n🌙 {moon['phase']} | {impact['bias']}\n"
            f"📡 Yahoo Finance | AI: Claude\n⚠️ _Bukan saran investasi_")
    send_telegram(msg)
    print(f"[NEWS] Briefing sent, {len(articles)} articles")

def get_economic_calendar_today():
    now  = now_wita()
    day  = now.weekday()
    weekly = {
        1: [{"time":"20:30","impact":"🟡","name":"US Retail Sales","desc":"Konsumsi retail US"}],
        2: [{"time":"21:30","impact":"🔴","name":"FOMC Minutes / CPI","desc":"Kebijakan Fed & inflasi"},
            {"time":"03:00","impact":"🔴","name":"FOMC Rate Decision","desc":"Keputusan suku bunga (kalau ada)"}],
        3: [{"time":"19:30","impact":"🔴","name":"US Initial Jobless Claims","desc":"Data pengangguran mingguan"},
            {"time":"20:30","impact":"🟡","name":"US PPI","desc":"Producer Price Index"}],
        4: [{"time":"20:30","impact":"🔴","name":"US NFP / CPI","desc":"Non-Farm Payroll & inflasi"},
            {"time":"22:00","impact":"🟡","name":"UoM Consumer Sentiment","desc":"Sentimen konsumen"}],
    }
    return weekly.get(day, [])

def send_calendar_alert():
    events = get_economic_calendar_today()
    if not events: return
    now  = now_wita()
    day_name = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"][now.weekday()]
    events_text = ""
    for e in events:
        events_text += f"\n{e['impact']} *{e['time']} WITA* — {e['name']}\n   📝 {e['desc']}"
    send_telegram(
        f"📅 *ECONOMIC CALENDAR*\n━━━━━━━━━━━━━━\n"
        f"📆 {day_name}, {now.day} {get_month_name()} {now.year}\n\n"
        f"*News High Impact Hari Ini:*{events_text}\n\n━━━━━━━━━━━━━━\n"
        f"🔴 HIGH = Jangan trading saat keluar!\n🟡 MEDIUM = Kurangi size posisi\n\n"
        f"💡 Ketik /news untuk berita & analisa terkini!"
    )


# ── 📐 PIVOT POINT ────────────────────────────────────────
def calc_pivot_points(ph, pl, pc):
    c  = (ph + pl + pc) / 3
    r1 = 2*c - pl;  s1 = 2*c - ph
    r2 = c + (ph - pl);  s2 = c - (ph - pl)
    r3 = ph + 2*(c - pl); s3 = pl - 2*(ph - c)
    return {"pivot":round(c,2),"r1":round(r1,2),"r2":round(r2,2),"r3":round(r3,2),
            "s1":round(s1,2),"s2":round(s2,2),"s3":round(s3,2)}

def get_pivot_from_candles(candles):
    if len(candles) < 288: return None
    yesterday = candles[-288:]
    ph = max(c["high"] for c in yesterday)
    pl = min(c["low"]  for c in yesterday)
    pc = yesterday[-1]["close"]
    return calc_pivot_points(ph, pl, pc)

def get_pivot_signal(price, pivot):
    if not pivot: return None
    p = pivot["pivot"]
    if price > pivot["r2"]:   return {"signal":"STRONG SELL","emoji":"🔴🔴","desc":f"Di atas R2 ${pivot['r2']:.2f} → Overbought"}
    elif price > pivot["r1"]: return {"signal":"SELL","emoji":"🔴","desc":f"Di atas R1 ${pivot['r1']:.2f} → Cari SELL"}
    elif price > p:           return {"signal":"BULLISH","emoji":"📈","desc":f"Di atas Pivot ${p:.2f} → Bias BUY"}
    elif price > pivot["s1"]: return {"signal":"BEARISH","emoji":"📉","desc":f"Di bawah Pivot ${p:.2f} → Bias SELL"}
    elif price > pivot["s2"]: return {"signal":"BUY","emoji":"🟢","desc":f"Di bawah S1 ${pivot['s1']:.2f} → Cari BUY"}
    else:                     return {"signal":"STRONG BUY","emoji":"🟢🟢","desc":f"Di bawah S2 ${pivot['s2']:.2f} → Oversold"}

def send_pivot_briefing(price, candles):
    pivot = get_pivot_from_candles(candles)
    if not pivot: print("[PIVOT] Data belum cukup"); return
    signal = get_pivot_signal(price, pivot)
    sig_text = f"{signal['emoji']} {signal['signal']}: {signal['desc']}" if signal else ""
    moon = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
    send_telegram(
        f"📐 *PIVOT POINT HARI INI*\n━━━━━━━━━━━━━━\n💰 Harga: *${price:.2f}*\n\n"
        f"🔴 *Resistance:*\n  R3: *${pivot['r3']:.2f}*\n  R2: *${pivot['r2']:.2f}*\n  R1: *${pivot['r1']:.2f}*\n\n"
        f"⚪ *Pivot:* *${pivot['pivot']:.2f}* ← Level tengah\n\n"
        f"🟢 *Support:*\n  S1: *${pivot['s1']:.2f}*\n  S2: *${pivot['s2']:.2f}*\n  S3: *${pivot['s3']:.2f}*\n\n"
        f"━━━━━━━━━━━━━━\n📊 *Signal Sekarang:*\n{sig_text}\n\n"
        f"💡 *Cara Pakai:*\n→ Harga > Pivot = Bias BUY\n→ Harga < Pivot = Bias SELL\n"
        f"→ R1/R2 = Target SELL\n→ S1/S2 = Target BUY\n→ Konfirmasi dengan BOS M15!\n"
        f"━━━━━━━━━━━━━━\n🌙 {moon['phase']} | {impact['bias']}\n"
        f"📚 Formula: Kakushadze & Serur (2018)\n🕐 {now_wita().strftime('%H:%M')} WITA"
    )
    print(f"[PIVOT] Sent: P={pivot['pivot']} R1={pivot['r1']} S1={pivot['s1']}")


# ── 📊 MULTI-TIMEFRAME ANALYSIS ──────────────────────────
def build_tf_candles(candles_m5, tf_minutes):
    if not candles_m5: return []
    bars_per_tf = tf_minutes // 5
    result = []
    for i in range(0, len(candles_m5) - bars_per_tf + 1, bars_per_tf):
        chunk = candles_m5[i:i + bars_per_tf]
        if len(chunk) < bars_per_tf: continue
        result.append({"open":chunk[0]["open"],"high":max(c["high"] for c in chunk),
                        "low":min(c["low"] for c in chunk),"close":chunk[-1]["close"],"volume":len(chunk)})
    return result

def calc_rsi(candles, period=14):
    if len(candles) < period + 1: return None
    closes = [c["close"] for c in candles[-(period+10):]]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0)); losses.append(max(-diff, 0))
    if len(gains) < period: return None
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100.0
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

def calc_ema(candles, period=21):
    if len(candles) < period: return None
    closes = [c["close"] for c in candles]
    k = 2 / (period + 1)
    ema = sum(closes[:period]) / period
    for price in closes[period:]: ema = price * k + ema * (1 - k)
    return round(ema, 2)

def calc_momentum(candles, period=10):
    if len(candles) < period + 1: return None
    return round(candles[-1]["close"] - candles[-(period+1)]["close"], 2)

def calc_relative_volume(candles, period=20):
    if len(candles) < period + 1: return None
    recent_range = abs(candles[-1]["high"] - candles[-1]["low"])
    avg_range    = sum(abs(c["high"] - c["low"]) for c in candles[-period:]) / period
    if avg_range == 0: return 1.0
    return round(recent_range / avg_range, 2)

def get_tf_bias(candles, tf_name):
    if len(candles) < 15:
        return {"tf":tf_name,"bias":"⏳","label":"Data kurang","rsi":None,"rsi_label":"?",
                "ema":None,"ema_pos":"?","mom":None,"rvol":None,"price":0,"bull":0,"bear":0}
    rsi  = calc_rsi(candles); ema = calc_ema(candles, 21)
    mom  = calc_momentum(candles, 10); rvol = calc_relative_volume(candles, 20)
    price = candles[-1]["close"]
    bull_signals = bear_signals = 0
    if ema and price > ema: bull_signals += 1
    elif ema and price < ema: bear_signals += 1
    if rsi:
        if rsi < 45: bear_signals += 1
        elif rsi > 55: bull_signals += 1
    if mom:
        if mom > 0: bull_signals += 1
        else: bear_signals += 1
    if bull_signals > bear_signals:   bias = "📈"; label = "BULL"
    elif bear_signals > bull_signals: bias = "📉"; label = "BEAR"
    else:                             bias = "⚠️"; label = "NETRAL"
    rsi_label = ""
    if rsi:
        if rsi >= 70:   rsi_label = "🔴OB"
        elif rsi <= 30: rsi_label = "🟢OS"
        else:           rsi_label = f"{rsi:.0f}"
    return {"tf":tf_name,"bias":bias,"label":label,"rsi":rsi,"rsi_label":rsi_label,
            "ema":ema,"ema_pos":"Atas" if (ema and price > ema) else "Bawah",
            "mom":mom,"rvol":rvol,"price":price,"bull":bull_signals,"bear":bear_signals}

def get_all_tf_analysis(candles_m5):
    tfs = [
        ("M15",15,candles_m5[-200:] if len(candles_m5)>=200 else candles_m5),
        ("H1",60,candles_m5[-600:] if len(candles_m5)>=600 else candles_m5),
        ("H4",240,candles_m5[-2000:] if len(candles_m5)>=2000 else candles_m5),
        ("D1",1440,candles_m5),("W1",10080,candles_m5),
    ]
    results = []
    for tf_name, tf_min, data in tfs:
        tf_candles = build_tf_candles(data, tf_min)
        if len(tf_candles) < 3:
            results.append({"tf":tf_name,"bias":"⏳","label":"Data kurang","rsi":None,
                            "rsi_label":"?","ema":None,"ema_pos":"?","mom":None,"rvol":None,
                            "price":0,"bull":0,"bear":0})
        else:
            results.append(get_tf_bias(tf_candles, tf_name))
    return results

def get_overall_bias(tf_results):
    bulls = sum(1 for r in tf_results if r["label"]=="BULL")
    bears = sum(1 for r in tf_results if r["label"]=="BEAR")
    total = len([r for r in tf_results if r["label"] not in ["⏳","Data kurang","NETRAL"]])
    if total == 0: return "⏳ Data kurang", ""
    if bulls > bears:
        strength = "KUAT" if bulls >= 4 else "SEDANG"
        return f"📈 BULLISH {strength} ({bulls}/{total})", "BUY di support!"
    elif bears > bulls:
        strength = "KUAT" if bears >= 4 else "SEDANG"
        return f"📉 BEARISH {strength} ({bears}/{total})", "SELL di resistance!"
    else:
        return f"⚠️ MIXED ({bulls}B/{bears}S)", "Tunggu konfirmasi!"

def send_mtf_analysis(price, candles_m5):
    results = get_all_tf_analysis(candles_m5)
    overall, action = get_overall_bias(results)
    moon   = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
    luck   = get_luck_status()
    pivot  = get_pivot_from_candles(candles_m5)
    pivot_signal = get_pivot_signal(price, pivot) if pivot else None
    rows = ""
    for r in results:
        rvol_str = f"{r['rvol']:.1f}x" if r["rvol"] else "?"
        rvol_emoji = "🔥" if (r["rvol"] and r["rvol"]>1.5) else "💤" if (r["rvol"] and r["rvol"]<0.7) else "📊"
        ema_str = f"{'▲' if r['ema_pos']=='Atas' else '▼'}EMA"
        rows += f"\n`{r['tf']:4}` {r['bias']} RSI:{r['rsi_label']:>5} {ema_str} Vol:{rvol_emoji}{rvol_str}"
    conflict = ""
    labels = [r["label"] for r in results if r["label"] not in ["⏳","Data kurang"]]
    if "BULL" in labels and "BEAR" in labels:
        bull_tfs = [r["tf"] for r in results if r["label"]=="BULL"]
        bear_tfs = [r["tf"] for r in results if r["label"]=="BEAR"]
        conflict = (f"\n⚠️ *Konflik TF!*\nBULL: {', '.join(bull_tfs)}\nBEAR: {', '.join(bear_tfs)}\n→ Ikuti TF yang lebih tinggi!")
    pivot_text = ""
    if pivot:
        pivot_text = f"\n\n📐 *Pivot:* ${pivot['pivot']:.2f} | R1:${pivot['r1']:.2f} | S1:${pivot['s1']:.2f}"
        if pivot_signal: pivot_text += f"\n{pivot_signal['emoji']} {pivot_signal['signal']}"
    rsi_alert = ""
    for r in results:
        if r["rsi"]:
            if r["rsi"] >= 70: rsi_alert += f"\n🔴 {r['tf']} OVERBOUGHT (RSI {r['rsi']:.0f}) → Potensi SELL!"
            elif r["rsi"] <= 30: rsi_alert += f"\n🟢 {r['tf']} OVERSOLD (RSI {r['rsi']:.0f}) → Potensi BUY!"
    send_telegram(
        f"📊 *MULTI TIMEFRAME ANALYSIS*\n━━━━━━━━━━━━━━\n💰 Gold: *${price:.2f}*\n"
        f"🕐 {now_wita().strftime('%H:%M')} WITA\n\n"
        f"```\nTF    Bias  RSI   EMA    VOL\n{'─'*32}{rows}\n```\n━━━━━━━━━━━━━━\n"
        f"🎯 *Overall:* {overall}\n💡 {action}{conflict}{rsi_alert}{pivot_text}\n\n"
        f"━━━━━━━━━━━━━━\n📖 *Cara Baca:*\n📈=Bull 📉=Bear ⚠️=Netral\n"
        f"🔴OB=Overbought 🟢OS=Oversold\n▲EMA=Di atas EMA ▼EMA=Di bawah\n"
        f"🔥Vol=Tinggi 💤Vol=Rendah\n\n🌙 {moon['phase']} | {impact['bias']}\n{luck['emoji']} {luck['label']}"
    )
    print(f"[MTF] Analysis sent @ ${price:.2f}")


def get_luck_status(date=None):
    if date is None: date = now_wita()
    month = date.month; day = date.day
    status = SINARMAS_CALENDAR.get(month, {}).get(day, "O")
    if status == "L":
        return {"status":"LUCKY","emoji":"🍀","label":"🍀 LUCKY DAY","color":"MERAH",
                "desc":"Hari baik untuk trading! Energi positif mendukung keputusan.",
                "trading":"✅ Hari bagus untuk entry\n✅ Percayai setup yang valid\n✅ Target bisa lebih agresif"}
    elif status == "U":
        return {"status":"UNLUCKY","emoji":"⚠️","label":"⚠️ UNLUCKY DAY","color":"HITAM",
                "desc":"Hari kurang baik. Hindari keputusan besar & overtrading.",
                "trading":"⛔ Kurangi ukuran posisi\n⚠️ Hindari FOMO\n❌ Skip kalau setup tidak jelas"}
    else:
        return {"status":"ORDINARY","emoji":"📅","label":"📅 ORDINARY DAY","color":"HIJAU",
                "desc":"Hari biasa. Trading normal sesuai metode.",
                "trading":"✅ Trading normal\n✅ Ikuti setup seperti biasa"}


BOT_TOKEN  = os.environ.get("BOT_TOKEN")
CHAT_ID    = os.environ.get("CHAT_ID")
FRED_KEY   = os.environ.get("FRED_API_KEY", "638b72616ca3504d71817c63e820aeb5")
FETCH_INTERVAL = 15
SR_TOLERANCE   = 10

if not BOT_TOKEN or not CHAT_ID:
    print("[ERROR] BOT_TOKEN dan CHAT_ID harus diset!")
    exit(1)

WITA = timezone(timedelta(hours=8))
WIB  = timezone(timedelta(hours=7))

def now_wita(): return datetime.now(WITA)
def now_wib():  return datetime.now(WIB)

def get_session():
    t = now_wita().hour + now_wita().minute / 60
    if t < 10:  return "asia"
    if t < 15:  return "pre"
    if t < 23:  return "london"
    return "ny"

def market_open():
    n = datetime.now(timezone.utc)
    d, h = n.weekday(), n.hour
    if d == 6: return False
    if d == 5: return False
    if d == 4 and h >= 22: return False
    return True

def get_day_name():
    return ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"][now_wita().weekday()]

def get_month_name(m=None):
    months = ["","Januari","Februari","Maret","April","Mei","Juni",
              "Juli","Agustus","September","Oktober","November","Desember"]
    return months[m or now_wita().month]

KILLZONES = [
    {"name":"Asian Killzone","emoji":"🌏","start_h":1,"start_m":0,"end_h":4,"end_m":0,
     "desc":"Sesi Asia dimulai! Low & High Asia mulai terbentuk.",
     "action":"✅ Tracking Low & High Asia\n✅ Catat range Asia\n⚠️ Jangan entry dulu","danger":False},
    {"name":"Pre-London Aktif","emoji":"⏳","start_h":10,"start_m":0,"end_h":15,"end_m":0,
     "desc":"Market mulai bersiap. Volume mulai naik.",
     "action":"✅ Tandai High & Low Asia\n✅ Tarik Fibonacci\n⏳ Standby untuk London","danger":False},
    {"name":"LONDON OPEN — JUDAS SWING!","emoji":"🇬🇧","start_h":15,"start_m":0,"end_h":15,"end_m":30,
     "desc":"BAHAYA! London open = zona Judas Swing. Fake move sering terjadi ke atas/bawah sebelum arah asli terbentuk!",
     "action":"⛔ JANGAN entry sekarang!\n⚠️ Tunggu sweep selesai\n👀 Pantau High & Low Asia\n📐 Siap entry di 61.8%","danger":True},
    {"name":"London Main — Entry Zone","emoji":"✅","start_h":15,"start_m":30,"end_h":18,"end_m":0,
     "desc":"Judas Swing selesai. Arah dominan London mulai terbentuk. Ini waktu entry terbaik!",
     "action":"✅ Cari BOS konfirmasi\n✅ Entry di 61.8% Fib\n✅ Sweep Low Asia → BUY\n🎯 Target High Asia","danger":False},
    {"name":"LONDON-NY OVERLAP — PALING VOLATILE!","emoji":"🔥","start_h":20,"start_m":0,"end_h":21,"end_m":30,
     "desc":"Overlap London-NY! Pergerakan TERBESAR hari ini. Volume sangat tinggi.",
     "action":"🔥 Volume paling tinggi!\n✅ Entry kalau belum dapat setup\n⚠️ SL wajib lebih lebar","danger":False},
    {"name":"NYSE Open — Data US!","emoji":"🇺🇸","start_h":21,"start_m":30,"end_h":22,"end_m":0,
     "desc":"NYSE open! Data ekonomi US sering keluar. Displacement besar bisa terjadi tiba-tiba.",
     "action":"⚠️ Waspada data ekonomi US\n✅ SL sudah di profit?\n✅ Konfirmasi arah hari ini","danger":False},
    {"name":"NY Main Session","emoji":"🇺🇸","start_h":22,"start_m":0,"end_h":23,"end_m":59,
     "desc":"New York session utama. Konfirmasi arah dominan hari ini.",
     "action":"✅ Hold posisi yang sudah profit\n✅ Partial close jika sudah target\n⚠️ Jangan buka posisi baru besar","danger":False},
    {"name":"London Close — Reversal Zone","emoji":"🔚","start_h":0,"start_m":0,"end_h":2,"end_m":0,
     "desc":"London tutup. Institusi London menutup posisi. Sering terjadi reversal dari tren hari ini.",
     "action":"⚠️ Reversal mungkin terjadi!\n✅ Pertimbangkan close posisi\n✅ Jangan buka posisi baru\n🌙 Persiapkan Asia besok","danger":False},
]

def get_current_killzone():
    now = now_wita()
    h, m = now.hour, now.minute
    t = h * 60 + m
    for kz in KILLZONES:
        start = kz["start_h"] * 60 + kz["start_m"]
        end   = kz["end_h"]   * 60 + kz["end_m"]
        if start <= t < end: return kz
    return None

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id":CHAT_ID,"text":text,"parse_mode":"Markdown"}, timeout=10)
        return r.json().get("ok", False)
    except Exception as e:
        print(f"[TG ERROR] {e}")
        return False

def get_updates(offset=None):
    try:
        params = {"timeout":1,"allowed_updates":["message"]}
        if offset: params["offset"] = offset
        r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params=params, timeout=5)
        return r.json().get("result", [])
    except:
        return []

def fetch_price():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=10)
        return float(r.json()["price"])
    except Exception as e:
        print(f"[PRICE ERROR] {e}")
        return None

def analyze_candle(candles):
    if len(candles) < 3: return None
    c1, c2, c3 = candles[-1], candles[-2], candles[-3]
    body1  = abs(c1["close"] - c1["open"]); body2 = abs(c2["close"] - c2["open"]); body3 = abs(c3["close"] - c3["open"])
    uw1    = c1["high"] - max(c1["open"], c1["close"]); lw1 = min(c1["open"], c1["close"]) - c1["low"]
    total1 = c1["high"] - c1["low"]
    uw2    = c2["high"] - max(c2["open"], c2["close"]); lw2 = min(c2["open"], c2["close"]) - c2["low"]
    bull1  = c1["close"] > c1["open"]; bear1 = c1["close"] < c1["open"]
    bull2  = c2["close"] > c2["open"]; bear2 = c2["close"] < c2["open"]
    patterns = []
    if bull1 and bear2 and c1["open"] <= c2["close"] and c1["close"] >= c2["open"] and body1 > body2 * 0.8:
        patterns.append({"tier":1,"bias":"BULL","name":"🔴 Bullish Engulfing","emoji":"📈","desc":"Buyer mengambil alih!","action":"✅ BUY kuat! Konfirmasi BOS."})
    if bear1 and bull2 and c1["open"] >= c2["close"] and c1["close"] <= c2["open"] and body1 > body2 * 0.8:
        patterns.append({"tier":1,"bias":"BEAR","name":"🔴 Bearish Engulfing","emoji":"📉","desc":"Seller mengambil alih!","action":"✅ SELL kuat! Konfirmasi BOS."})
    if total1 > 0 and lw1 > body1*2.0 and lw1 > total1*0.5 and uw1 < body1*0.5:
        patterns.append({"tier":1,"bias":"BULL","name":"🔴 Bullish Pin Bar","emoji":"📈","desc":"Rejection kuat ke bawah!","action":"✅ BUY kuat di support/61.8%!"})
    if total1 > 0 and uw1 > body1*2.0 and uw1 > total1*0.5 and lw1 < body1*0.5:
        patterns.append({"tier":1,"bias":"BEAR","name":"🔴 Bearish Pin Bar","emoji":"📉","desc":"Rejection kuat ke atas!","action":"✅ SELL kuat di resistance/61.8%!"})
    if bear2 and bull1 and body2 < body3*0.3 and c3["close"] < c3["open"] and c1["close"] > (c3["open"]+c3["close"])/2:
        patterns.append({"tier":1,"bias":"BULL","name":"🔴 Morning Star ⭐","emoji":"📈","desc":"3 candle reversal! Sangat kuat!","action":"✅ BUY setup sangat kuat!"})
    if bull2 and bear1 and body2 < body3*0.3 and c3["close"] > c3["open"] and c1["close"] < (c3["open"]+c3["close"])/2:
        patterns.append({"tier":1,"bias":"BEAR","name":"🔴 Evening Star ⭐","emoji":"📉","desc":"3 candle reversal! Sangat kuat!","action":"✅ SELL setup sangat kuat!"})
    if total1 > 0 and lw1 > body1*1.5 and lw1 > total1*0.4 and uw1 < body1*1.0 and bull1:
        patterns.append({"tier":2,"bias":"BULL","name":"🟡 Hammer 🔨","emoji":"📈","desc":"Ekor bawah panjang di support.","action":"⏳ Watch! Tunggu candle konfirmasi."})
    if total1 > 0 and uw1 > body1*1.5 and uw1 > total1*0.4 and lw1 < body1*1.0 and bear1:
        patterns.append({"tier":2,"bias":"BEAR","name":"🟡 Shooting Star ⭐","emoji":"📉","desc":"Ekor atas panjang di resistance.","action":"⏳ Watch! Tunggu candle konfirmasi."})
    if abs(c1["low"]-c2["low"]) < 3 and bear2 and bull1:
        patterns.append({"tier":2,"bias":"BULL","name":"🟡 Tweezer Bottom","emoji":"📈","desc":"Double low! Support sangat kuat.","action":"⏳ Watch!"})
    if abs(c1["high"]-c2["high"]) < 3 and bull2 and bear1:
        patterns.append({"tier":2,"bias":"BEAR","name":"🟡 Tweezer Top","emoji":"📉","desc":"Double high! Resistance sangat kuat.","action":"⏳ Watch!"})
    if bull1 and bear2 and c1["open"] > c2["close"] and c1["close"] < c2["open"] and body1 < body2*0.5:
        patterns.append({"tier":2,"bias":"BULL","name":"🟡 Bullish Harami","emoji":"📈","desc":"Candle kecil hijau dalam candle merah besar.","action":"⏳ Watch! Tunggu BOS bullish."})
    if bear1 and bull2 and c1["open"] < c2["close"] and c1["close"] > c2["open"] and body1 < body2*0.5:
        patterns.append({"tier":2,"bias":"BEAR","name":"🟡 Bearish Harami","emoji":"📉","desc":"Candle kecil merah dalam candle hijau besar.","action":"⏳ Watch! Tunggu BOS bearish."})
    if total1 > 0 and body1 < total1*0.1 and total1 > 5:
        doji_type = "Dragonfly" if lw1 > uw1*2 else "Gravestone" if uw1 > lw1*2 else "Doji"
        doji_bias = "BULL" if lw1 > uw1 else "BEAR"
        patterns.append({"tier":3,"bias":doji_bias,"name":f"🟢 {doji_type} Doji","emoji":"⚠️","desc":"Kebimbangan market!","action":"ℹ️ Tunggu candle berikutnya."})
    if c1["high"] < c2["high"] and c1["low"] > c2["low"]:
        patterns.append({"tier":3,"bias":"NEUTRAL","name":"🟢 Inside Bar","emoji":"⏸️","desc":"Konsolidasi. Breakout akan terjadi!","action":"ℹ️ Siapkan entry breakout!"})
    if bull1 and total1 > 0 and body1 > total1*0.85 and body1 > 15:
        patterns.append({"tier":3,"bias":"BULL","name":"🟢 Bullish Marubozu","emoji":"📈","desc":"Momentum bullish kuat!","action":"ℹ️ BUY di pullback berikutnya."})
    if bear1 and total1 > 0 and body1 > total1*0.85 and body1 > 15:
        patterns.append({"tier":3,"bias":"BEAR","name":"🟢 Bearish Marubozu","emoji":"📉","desc":"Momentum bearish kuat!","action":"ℹ️ SELL di rally berikutnya."})
    return patterns if patterns else None

def calc_fib(lo, hi):
    r = hi - lo
    return {"f0":round(hi,2),"f382":round(hi-r*0.382,2),"f618":round(hi-r*0.618,2),
            "f786":round(hi-r*0.786,2),"f100":round(lo,2),"f127":round(lo-r*0.272,2),"f161":round(lo-r*0.618,2)}

def detect_bos(candles, lb=5):
    if len(candles) < lb+2: return None
    rec = candles[-(lb+1):]
    last, prev = rec[-1], rec[:-1]
    if last["close"] > max(c["high"] for c in prev): return "BULL"
    if last["close"] < min(c["low"]  for c in prev): return "BEAR"
    return None

def detect_bos_m15(lb=5):
    candles = state["candles_m15"]
    if len(candles) < lb+2: return None
    rec = candles[-(lb+1):]
    last, prev = rec[-1], rec[:-1]
    if last["close"] > max(c["high"] for c in prev): return "BULL"
    if last["close"] < min(c["low"]  for c in prev): return "BEAR"
    return None

def get_m15_status():
    bos = state.get("bos_m15"); t = state.get("bos_m15_time")
    if not bos: return "⏳ Belum ada BOS M15"
    time_str = t.strftime("%H:%M") if t else ""
    return f"📈 BULLISH BOS M15 ({time_str} WITA)" if bos == "BULL" else f"📉 BEARISH BOS M15 ({time_str} WITA)"

def get_moon_phase():
    now = datetime.now(timezone.utc)
    known_new_moon = datetime(2026, 3, 18, 0, 23, 0, tzinfo=timezone.utc)
    lunar_cycle = 29.53058867
    phase_days = ((now-known_new_moon).total_seconds()/86400) % lunar_cycle
    if phase_days < 0: phase_days += lunar_cycle
    illumination = round((1-math.cos(2*math.pi*phase_days/lunar_cycle))/2*100)
    if phase_days < 1.85:    phase,phase_en = "🌑 New Moon",        "new_moon"
    elif phase_days < 7.38:  phase,phase_en = "🌒 Waxing Crescent", "waxing_crescent"
    elif phase_days < 9.22:  phase,phase_en = "🌓 First Quarter",   "first_quarter"
    elif phase_days < 14.77: phase,phase_en = "🌔 Waxing Gibbous",  "waxing_gibbous"
    elif phase_days < 16.61: phase,phase_en = "🌕 Full Moon",       "full_moon"
    elif phase_days < 22.15: phase,phase_en = "🌖 Waning Gibbous",  "waning_gibbous"
    elif phase_days < 23.99: phase,phase_en = "🌗 Last Quarter",    "last_quarter"
    else:                    phase,phase_en = "🌘 Waning Crescent", "waning_crescent"
    return {"phase":phase,"phase_en":phase_en,"days":round(phase_days,1),"illumination":illumination,
            "next_full":round(14.77-phase_days if phase_days<14.77 else lunar_cycle-phase_days+14.77,1),
            "next_new":round(lunar_cycle-phase_days,1)}

def get_moon_impact(phase_en):
    impacts = {
        "new_moon":       {"bias":"⚠️ NETRAL","signal":"neutral","desc":"Siklus baru. Sering REVERSAL.","trading":"⛔ Hindari posisi besar"},
        "waxing_crescent":{"bias":"📈 BULLISH","signal":"bullish","desc":"Energi naik.","trading":"✅ Fokus BUY"},
        "first_quarter":  {"bias":"📈 BULLISH KUAT","signal":"bullish","desc":"Momentum naik kuat.","trading":"✅ BUY setiap pullback"},
        "waxing_gibbous": {"bias":"📈 BULLISH","signal":"bullish_caution","desc":"Mendekati puncak.","trading":"✅ Hold BUY"},
        "full_moon":      {"bias":"📉 BEARISH","signal":"bearish","desc":"Puncak. REVERSAL.","trading":"✅ Fokus SELL"},
        "waning_gibbous": {"bias":"📉 BEARISH","signal":"bearish","desc":"Energi turun.","trading":"✅ SELL di resistance"},
        "last_quarter":   {"bias":"📉 MELEMAH","signal":"bearish","desc":"Momentum melemah.","trading":"⚠️ Market ranging"},
        "waning_crescent":{"bias":"⚠️ NETRAL","signal":"neutral","desc":"Energi lemah.","trading":"⛔ Kurangi trading"},
    }
    return impacts.get(phase_en, impacts["new_moon"])

def get_planet_info():
    now = now_wita(); month, day = now.month, now.day
    planets = []
    if (month==2 and day>=15) or month==3 or (month==4 and day<=9):
        planets.append("☿ Mercury Retrograde — Fake moves ekstrem")
    if month==3 or (month==2 and day>=1): planets.append("♀ Venus di Pisces — Volatilitas tinggi")
    if month==3 and day<=22: planets.append("♂ Mars di Pisces — Spike brutal tiba-tiba")
    planets.append("♄ Saturn di Aries — S&R sangat kuat")
    return planets

def detect_perfect_storm(candles, price):
    score=0; factors=[]; warnings=[]
    moon = get_moon_phase()
    if moon["phase_en"] in ["new_moon","full_moon"]: score+=3; factors.append(f"🌙 {moon['phase']} (+3)")
    elif moon["phase_en"] in ["first_quarter","last_quarter"]: score+=2; factors.append(f"🌙 Quarter Moon (+2)")
    now = now_wita()
    if (now.month==2 and now.day>=15) or now.month==3 or (now.month==4 and now.day<=9):
        score+=2; factors.append("☿ Mercury Retrograde (+2)")
    if now.weekday()==2: score+=2; factors.append("☀️ Anchor Day Rabu (+2)")
    if len(candles)>=10:
        last10=candles[-10:]
        r=max(c["high"] for c in last10)-min(c["low"] for c in last10)
        if r<15: score+=2; factors.append(f"😴 Sideways brutal {r:.1f}pts (+2)"); warnings.append("⚡ Hurricane siap!")
        eq_h=sum(1 for i in range(len(last10)-1) if abs(last10[i]["high"]-last10[i+1]["high"])<3)
        eq_l=sum(1 for i in range(len(last10)-1) if abs(last10[i]["low"]-last10[i+1]["low"])<3)
        if eq_h>=3 or eq_l>=3: score+=2; factors.append("💧 Liquidity buildup (+2)"); warnings.append("⚡ Sweep akan brutal!")
    base=int(price/100)*100
    for rn in [base,base+100,base+50]:
        if abs(price-rn)<=15: score+=1; factors.append(f"🎯 Round ${rn} (+1)"); break
    if score>=9:   level="🌪️🌪️🌪️ PERFECT STORM EXTREME!"; action="💥 DOMINANT STRATEGY AKTIF!"
    elif score>=6: level="🌪️🌪️ HURRICANE WARNING!";          action="⚡ Pergerakan besar mendekat!"
    elif score>=3: level="⛈️ STORM BUILDING";                action="⚠️ Kondisi memanas."
    else:          level="☀️ NORMAL";                         action="✅ Kondisi normal."
    return {"score":score,"level":level,"factors":factors,"warnings":warnings,"action":action}

def get_auto_sr(candles, current_price):
    levels=[]
    if len(candles)<10: return levels
    if len(candles)>=576:
        y=candles[-576:-288]
        if y:
            levels.append({"price":round(max(c["high"] for c in y),2),"label":"PDH","type":"resistance"})
            levels.append({"price":round(min(c["low"] for c in y),2), "label":"PDL","type":"support"})
    if len(candles)>=2016:
        wk=candles[-2016:]
        levels.append({"price":round(max(c["high"] for c in wk),2),"label":"Weekly High","type":"resistance"})
        levels.append({"price":round(min(c["low"] for c in wk),2), "label":"Weekly Low","type":"support"})
    base=int(current_price/100)*100
    for mult in range(-3,5):
        rn=base+mult*100
        if rn>0 and abs(current_price-rn)<=150:
            levels.append({"price":float(rn),"label":f"Round ${rn}","type":"resistance" if rn>current_price else "support"})
    unique=[]
    for lv in sorted(levels,key=lambda x:x["price"]):
        if not unique or abs(lv["price"]-unique[-1]["price"])>=5: unique.append(lv)
    return unique

def send_morning_briefing(price):
    now=now_wita(); moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
    planets=get_planet_info(); storm=detect_perfect_storm(state["candles"],price)
    luck=get_luck_status(now); day=get_day_name()
    planet_text="\n".join([f"  • {p}" for p in planets])
    factor_text="\n".join([f"  {f}" for f in storm["factors"]]) if storm["factors"] else "  Tidak ada"
    if day in ["Sabtu","Minggu"]: market_note="🔴 PASAR TUTUP"; setup_plan="Istirahat & persiapkan strategi!"
    elif day=="Senin": market_note="🟡 SENIN — Range Asia belum sempurna"; setup_plan="⚠️ Skip Asia, fokus London & NY"
    elif day=="Rabu":  market_note="🟡 RABU — Anchor Day!"; setup_plan="⚠️ Pantau resistance & support utama!\n🗓️ Analisis Anchor Day terkirim jam 21:30 WITA"
    elif day=="Kamis": market_note="🟡 KAMIS — Follow Anchor Day Setup!"; setup_plan="✅ Cek reminder Anchor Day hari ini\n✅ Konfirmasi BOS M15 sebelum entry"
    elif day=="Jumat": market_note="🟡 JUMAT — Profit taking!"; setup_plan="⚠️ Close sebelum 23:00 WITA"
    else: market_note="🟢 PASAR BUKA — Normal"; setup_plan="✅ Asia: Low Asia → BUY BOS\n✅ London: SELL High Asia\n✅ 61.8%: BUY ke-2"
    bias="📈 BULLISH" if impact["signal"]=="bullish" else "📉 BEARISH" if impact["signal"]=="bearish" else "⚠️ NETRAL"
    targets=f"🎯 Naik: ${price+50:.0f}→${price+100:.0f}" if impact["signal"]=="bullish" else f"🎯 Turun: ${price-50:.0f}→${price-100:.0f}" if impact["signal"]=="bearish" else f"🎯 Range: ${price-50:.0f}–${price+50:.0f}"
    base=int(price/100)*100
    send_telegram(
        f"━━━━━━━━━━━━━━━━━━━━\n🌅 *GOLD MORNING BRIEFING*\n"
        f"📅 {day}, {now.day} {get_month_name()} {now.year}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"☀️ *Selamat pagi, Trader!* ☕\n\n"
        f"💰 *HARGA:* *${price:.2f}*\nRound: ${base} | Half: ${base+50} | Res: ${base+100}\n\n"
        f"📊 {market_note}\n\n🌪️ *Storm:* {storm['level']} ({storm['score']}/12)\n{factor_text}\n\n"
        f"🎯 *Bias:* {bias} | {targets}\n\n📋 *Setup:*\n{setup_plan}\n\n"
        f"⏰ *Killzone WITA:*\n🌏 Asia:    01:00–04:00\n🇬🇧 London:  15:00–18:00\n"
        f"⚠️ Judas:   15:00–15:30 ← BAHAYA!\n🔥 Overlap: 20:00–21:30 ← TERKUAT!\n🇺🇸 NYSE:    21:30–22:00\n🔚 Close:   00:00–02:00\n\n"
        f"🌙 {moon['phase']} ({moon['illumination']}%) | {impact['bias']}\n📝 {impact['desc']}\n💡 {impact['trading']}\n\n"
        f"🪐\n{planet_text}\n\n⚠️ *Rules:* BOS dulu | SL wajib | R:R 1:2\n━━━━━━━━━━━━━━\n"
        f"💡 Ketik /pivot untuk Pivot Point hari ini\n💡 Ketik /yield untuk US 10Y Yield update\n"
        f"💡 Ketik /anchorday untuk Anchor Day analysis\n━━━━━━━━━━━━━━━━━━━━\n"
        f"Semangat! 💪🥇\n⚠️ _Bukan saran investasi_"
    )
    print("[BRIEFING] Daily sent")

def send_weekly_briefing(price):
    now=now_wita(); moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
    planets=get_planet_info(); storm=detect_perfect_storm(state["candles"],price)
    planet_text="\n".join([f"  • {p}" for p in planets])
    monday=now-timedelta(days=now.weekday())
    day_notes={0:"Senin  → Range Asia belum sempurna",1:"Selasa → Hari terbaik 🌟",
               2:"Rabu   → ⚠️ Anchor Day (analysis jam 21:30)",3:"Kamis  → Follow Anchor Setup 🌟",4:"Jumat  → Profit taking"}
    calendar="\n".join([f"  {(monday+timedelta(days=i)).strftime('%d %b')} {day_notes.get(i,'')}" for i in range(5)])
    weekly_bias="📈 BULLISH" if impact["signal"] in ["bullish","bullish_caution"] else "📉 BEARISH" if impact["signal"]=="bearish" else "⚠️ NETRAL"
    base=int(price/100)*100
    monday_date = now - timedelta(days=now.weekday())
    week_luck = []
    day_names = ["Sen","Sel","Rab","Kam","Jum"]
    for i in range(5):
        d = monday_date + timedelta(days=i)
        lk = get_luck_status(d)
        week_luck.append(f"{day_names[i]} {d.day}: {lk['emoji']}")
    week_luck_text = " | ".join(week_luck)
    send_telegram(
        f"━━━━━━━━━━━━━━━━━━━━\n📅 *GOLD WEEKLY BRIEFING*\n"
        f"Minggu {monday.strftime('%d')}–{(monday+timedelta(days=4)).strftime('%d')} {get_month_name(monday.month)}\n━━━━━━━━━━━━━━━━━━━━\n\n"
        f"💰 *${price:.2f}* | Bias: {weekly_bias}\n\n🍀 *Luck Week:*\n{week_luck_text}\n🍀=Lucky | 📅=Biasa | ⚠️=Unlucky\n\n"
        f"🗓️ *Kalender:*\n{calendar}\n\n🌪️ *Storm:* {storm['level']} ({storm['score']}/12)\n\n"
        f"🌙 {moon['phase']} ({moon['illumination']}%)\nFull Moon: {moon['next_full']:.0f}hr | New Moon: {moon['next_new']:.0f}hr\n\n"
        f"🪐 Planet:\n{planet_text}\n\n🎯 *Level:*\n"
        f"🔴 Res: ${base+100}→${base+150}→${base+200}\n📍 Now: ${price:.2f}\n🟢 Sup: ${base}→${base-50}→${base-100}\n\n"
        f"⏰ *Killzone WITA:*\n🌏 Asia 01:00–04:00 | ⚠️ Judas 15:00–15:30\n"
        f"✅ Entry 15:30–18:00 | 🔥 Overlap 20:00–21:30\n🇺🇸 NYSE 21:30–22:00 | 🔚 Close 00:00–02:00\n\n"
        f"🧠 *Dominant Strategy:*\n1. Asia sideway → London Hurricane (15:00)\n2. Sweep Low Asia → Entry 61.8% BUY\n"
        f"3. NY Overlap 20:00 = Arah Dominan\n🗓️ Rabu 21:30 = Anchor Day Analysis otomatis\n\n"
        f"⚠️ Max 2/hari | SL wajib | Close Jumat\n━━━━━━━━━━━━━━━━━━━━\nSemangat minggu ini! 💪🥇"
    )
    print("[BRIEFING] Weekly sent")


# ══════════════════════════════════════════════
# 🗓️ ANCHOR DAY — RABU ANALYSIS → KAMIS ENTRY
# ══════════════════════════════════════════════

ANCHOR_STATE_FILE = "anchor_day_state.json"
ANCHOR_ZONE_BUF   = 0.005   # 0.5% buffer uji level

def _anchor_conf_bar(score):
    filled = score // 20
    return "🟩" * filled + "⬜" * (5 - filled)

def _anchor_rejection(high, low, open_, close, direction):
    """Cek rejection candle. Return (is_rejection, wick_pct)"""
    body  = abs(close - open_)
    range_ = high - low
    if range_ == 0: return False, 0.0
    if direction == "up":
        wick  = high - max(open_, close)
        ratio = wick / range_
        return ratio > 0.40 and close < open_, round(ratio * 100, 1)
    else:
        wick  = min(open_, close) - low
        ratio = wick / range_
        return ratio > 0.40 and close > open_, round(ratio * 100, 1)

def _anchor_bos_m15(candles_m5, direction="bearish"):
    """BOS M15 dari data M5 yang ada"""
    m15 = build_tf_candles(candles_m5[-160:], 15)   # ~10 jam terakhir
    if len(m15) < 10: return False
    lookback  = m15[-15:-3]
    last_close = m15[-1]["close"]
    if direction == "bearish":
        swing = min(c["low"] for c in lookback)
        return last_close < swing
    else:
        swing = max(c["high"] for c in lookback)
        return last_close > swing

def _anchor_rsi_h1(candles_m5):
    """RSI(14) pada H1 dari data M5"""
    h1 = build_tf_candles(candles_m5[-840:], 60)   # ~35 jam H1
    return calc_rsi(h1) if len(h1) >= 15 else None

def _anchor_is_trend_day(candles_m5):
    """True jika Rabu bergerak >1.5% dari open → bukan Anchor, skip"""
    if len(candles_m5) < 252: return False
    today = candles_m5[-252:]     # ~21 jam terakhir
    open_  = today[0]["open"]
    close  = today[-1]["close"]
    return abs(close - open_) / open_ > 0.015

def _anchor_today_ohlc(candles_m5):
    """OHLC hari ini dari M5 candles terakhir (~21 jam = 252 bars)"""
    n = min(252, len(candles_m5))
    today = candles_m5[-n:]
    return {
        "open" : today[0]["open"],
        "high" : max(c["high"] for c in today),
        "low"  : min(c["low"]  for c in today),
        "close": today[-1]["close"],
    }

def _anchor_key_levels(candles_m5, price):
    """
    Level kunci dari data candles yang ada:
    - Weekly high/low (candles[-1440:] = ~5 hari M5)
    - Pivot dari kemarin (candles[-576:-288] = candle sebelum hari ini)
    """
    # Weekly range (5 hari terakhir, exclude hari ini)
    week_candles = candles_m5[-1440:-252] if len(candles_m5) >= 1440 else candles_m5[:-252] if len(candles_m5) > 252 else candles_m5
    weekly_high = max(c["high"] for c in week_candles) if week_candles else price + 50
    weekly_low  = min(c["low"]  for c in week_candles) if week_candles else price - 50

    # Pivot dari candle kemarin (288 bars = 1 hari M5)
    pivot = get_pivot_from_candles(candles_m5)
    if not pivot:
        pivot = calc_pivot_points(weekly_high, weekly_low, price)

    return {
        "current"     : price,
        "weekly_high" : round(weekly_high, 2),
        "weekly_low"  : round(weekly_low,  2),
        "pivot"       : pivot["pivot"],
        "r1": pivot["r1"], "r2": pivot["r2"],
        "s1": pivot["s1"], "s2": pivot["s2"],
    }

def anchor_save_state(sig):
    """Simpan hasil analisis ke in-memory state dan file JSON"""
    state["anchor_day_state"] = sig
    try:
        with open(ANCHOR_STATE_FILE, "w") as f:
            json.dump({"date": now_wita().strftime("%Y-%m-%d"), "signals": sig},
                      f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ANCHOR] Gagal simpan state: {e}")

def anchor_load_thursday_state():
    """Muat state Rabu untuk reminder Kamis. Cek in-memory dulu, lalu file."""
    # 1. In-memory (bot tidak restart)
    mem = state.get("anchor_day_state")
    if mem and mem.get("bias") not in (None, ""):
        return mem
    # 2. Dari file (bot restart semalam)
    if not os.path.exists(ANCHOR_STATE_FILE):
        return None
    try:
        with open(ANCHOR_STATE_FILE) as f:
            saved = json.load(f)
        saved_date = datetime.strptime(saved["date"], "%Y-%m-%d").date()
        yesterday  = (now_wita() - timedelta(days=1)).date()
        if saved_date == yesterday:
            return saved["signals"]
    except Exception as e:
        print(f"[ANCHOR] Gagal baca file: {e}")
    return None

def run_anchor_analysis():
    """
    Analisis utama Anchor Day.
    Dipanggil Rabu 21:30 WITA oleh check_anchor_day().
    Menggunakan state["candles"] (M5) — tidak butuh MT5.
    """
    candles = state["candles"]
    price   = state["prev_price"] or 0

    if len(candles) < 100 or price == 0:
        return {"bias": "NONE", "reason": "Data candles belum cukup"}

    # Trend day check
    if _anchor_is_trend_day(candles):
        return {"bias": "NONE", "reason": "Rabu bergerak >1.5% dari open (trend day, bukan anchor)"}

    ohlc   = _anchor_today_ohlc(candles)
    levels = _anchor_key_levels(candles, price)
    buf    = price * ANCHOR_ZONE_BUF

    # Zona resistance & support terkuat
    resistance = max(levels["weekly_high"], levels["r1"])
    support    = min(levels["weekly_low"],  levels["s1"])

    # Fallback jika level terlalu jauh
    if resistance - price > price * 0.02: resistance = levels["r1"]
    if price - support    > price * 0.02: support    = levels["s1"]

    # ── SELL scenario: harga uji resistance tapi gagal close di atasnya
    touched_r = ohlc["high"] >= resistance - buf
    failed_r  = ohlc["close"] < resistance

    if touched_r and failed_r:
        rej_ok, wick_pct = _anchor_rejection(ohlc["high"], ohlc["low"], ohlc["open"], ohlc["close"], "up")
        rsi_val = _anchor_rsi_h1(candles)
        rsi_ok  = (rsi_val or 0) > 65
        bos_ok  = _anchor_bos_m15(candles, "bearish")

        score = 30 * True + 20 * failed_r + 25 * rej_ok + 15 * rsi_ok + 10 * bos_ok
        if score >= 50:
            entry = resistance + buf * 0.3
            sl    = ohlc["high"] + buf * 0.5
            return {
                "bias": "SELL", "confidence": score,
                "reason": f"Rabu gagal tembus resistance {resistance:.2f}",
                "wed_high": round(ohlc["high"], 2), "wed_low": round(ohlc["low"], 2),
                "wed_close": round(ohlc["close"], 2), "zone": round(resistance, 2),
                "entry": round(entry, 2), "sl": round(sl, 2),
                "tp1": levels["pivot"], "tp2": levels["s1"], "tp3": levels["s2"],
                "wick_pct": wick_pct, "rsi": rsi_val, "bos": bos_ok, "rejection": rej_ok,
            }
        return {"bias": "NONE", "reason": f"Resistance {resistance:.2f} diuji tapi konfirmasi lemah (score {score}/100)"}

    # ── BUY scenario: harga uji support tapi gagal close di bawahnya
    touched_s = ohlc["low"] <= support + buf
    failed_s  = ohlc["close"] > support

    if touched_s and failed_s:
        rej_ok, wick_pct = _anchor_rejection(ohlc["high"], ohlc["low"], ohlc["open"], ohlc["close"], "down")
        rsi_val = _anchor_rsi_h1(candles)
        rsi_ok  = (rsi_val or 100) < 35
        bos_ok  = _anchor_bos_m15(candles, "bullish")

        score = 30 * True + 20 * failed_s + 25 * rej_ok + 15 * rsi_ok + 10 * bos_ok
        if score >= 50:
            entry = support - buf * 0.3
            sl    = ohlc["low"] - buf * 0.5
            return {
                "bias": "BUY", "confidence": score,
                "reason": f"Rabu gagal tembus support {support:.2f}",
                "wed_high": round(ohlc["high"], 2), "wed_low": round(ohlc["low"], 2),
                "wed_close": round(ohlc["close"], 2), "zone": round(support, 2),
                "entry": round(entry, 2), "sl": round(sl, 2),
                "tp1": levels["pivot"], "tp2": levels["r1"], "tp3": levels["r2"],
                "wick_pct": wick_pct, "rsi": rsi_val, "bos": bos_ok, "rejection": rej_ok,
            }
        return {"bias": "NONE", "reason": f"Support {support:.2f} diuji tapi konfirmasi lemah (score {score}/100)"}

    return {"bias": "NONE", "reason": f"Harga tidak uji resistance ({resistance:.2f}) maupun support ({support:.2f})"}

def _format_anchor_wednesday(sig):
    now = now_wita()
    if sig.get("bias") == "NONE":
        return (
            f"🗓️ *ANCHOR DAY — RABU*\n━━━━━━━━━━━━━━\n\n"
            f"⚪ *Tidak ada setup valid hari ini*\n\n"
            f"_{sig.get('reason', 'Kondisi tidak memenuhi syarat')}_\n\n"
            f"➡️ *Rekomendasi: Skip Kamis / Wait & See*\n"
            f"🤖 _Anchor Day | {now.strftime('%H:%M WITA %d/%m/%Y')}_"
        )
    bias       = sig["bias"]
    emoji_dir  = "🔴" if bias == "SELL" else "🟢"
    conf       = sig["confidence"]
    rej_icon   = "✅" if sig["rejection"] else "⚠️"
    rsi_icon   = (f"✅ Overbought ({sig['rsi']})" if bias == "SELL" and (sig["rsi"] or 0) > 65
                  else f"✅ Oversold ({sig['rsi']})" if bias == "BUY" and (sig["rsi"] or 0) < 35
                  else f"⚠️ Netral ({sig['rsi']})")
    bos_icon   = "✅ Confirmed" if sig["bos"] else "⚠️ Belum"
    zone_label = "Resistance" if bias == "SELL" else "Support"
    invalidate = "resistance" if bias == "SELL" else "support"
    sl_dist    = abs(sig["entry"] - sig["sl"])
    rr1 = round(abs(sig["zone"] - sig["tp1"]) / max(sl_dist, 0.01), 1)
    rr2 = round(abs(sig["zone"] - sig["tp2"]) / max(sl_dist, 0.01), 1)
    rr3 = round(abs(sig["zone"] - sig["tp3"]) / max(sl_dist, 0.01), 1)
    moon   = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
    luck   = get_luck_status()
    return (
        f"🗓️ *ANCHOR DAY ANALYSIS — RABU*\n━━━━━━━━━━━━━━\n\n"
        f"📊 *Price Action Rabu:*\n"
        f"```\n{zone_label:<16}: {sig['zone']:.2f}\n"
        f"Wed High        : {sig['wed_high']:.2f}\n"
        f"Wed Close       : {sig['wed_close']:.2f}\n"
        f"Wed Low         : {sig['wed_low']:.2f}\n```\n"
        f"{emoji_dir} *BIAS KAMIS: {bias}*\n_{sig['reason']}_\n\n"
        f"📈 *Konfirmasi:*\n"
        f"• Wick Rejection  : {rej_icon} ({sig['wick_pct']:.1f}%)\n"
        f"• RSI H1          : {rsi_icon}\n"
        f"• BOS M15         : {bos_icon}\n\n"
        f"🎯 *Confidence Score: {conf}%*\n{_anchor_conf_bar(conf)}\n\n"
        f"━━━━━━━━━━━━━━\n📌 *Setup Entry Kamis:*\n"
        f"```\nEntry Zone  : {sig['entry']:.2f}\n"
        f"Stop Loss   : {sig['sl']:.2f}  ({sl_dist:.2f} pts)\n"
        f"TP1         : {sig['tp1']:.2f}  (R:R ~1:{rr1})\n"
        f"TP2         : {sig['tp2']:.2f}  (R:R ~1:{rr2})\n"
        f"TP3         : {sig['tp3']:.2f}  (R:R ~1:{rr3})\n```\n"
        f"⚙️ *Manajemen:*\n"
        f"• Entry Asia Kamis: 09:00–11:00 WITA\n"
        f"• Konfirmasi London: 14:00–16:00 WITA\n"
        f"• Close 50% di TP1 → trailing ke TP2/TP3\n"
        f"• Max risk: 1–2% modal per trade\n\n"
        f"⚠️ *Invalidasi — Batalkan Setup Jika:*\n"
        f"• Harga breakout {invalidate} sebelum entry\n"
        f"• Ada news high-impact Kamis/Jumat\n"
        f"• Candle H4 Kamis close melawan bias\n"
        f"• NFP week (periksa kalender!)\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌙 {moon['phase']} | {impact['bias']}\n"
        f"{luck['emoji']} {luck['label']}\n"
        f"🤖 _Anchor Day | {now.strftime('%H:%M WITA %d/%m/%Y')}_"
    )

def _format_anchor_thursday(sig):
    now    = now_wita()
    bias   = sig["bias"]
    emoji  = "🔴" if bias == "SELL" else "🟢"
    action = "OPEN SELL — Retrace ke Resistance" if bias == "SELL" else "OPEN BUY — Pullback ke Support"
    timing = ("Tunggu harga naik ke zona resistance kemarin,\n"
              "konfirmasi rejection/BOS M15 sebelum entry.") if bias == "SELL" else \
             ("Tunggu harga turun ke zona support kemarin,\n"
              "konfirmasi rejection/BOS M15 sebelum entry.")
    moon   = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
    luck   = get_luck_status()
    return (
        f"⏰ *KAMIS — ANCHOR DAY ENTRY REMINDER*\n━━━━━━━━━━━━━━\n\n"
        f"{emoji} *Bias Hari Ini: {action}*\n_Berdasarkan Anchor Day Rabu kemarin_\n\n"
        f"📌 *Level Kritis:*\n"
        f"```\nEntry Zone  : {sig['entry']:.2f}\n"
        f"Stop Loss   : {sig['sl']:.2f}\n"
        f"TP1         : {sig['tp1']:.2f}\n"
        f"TP2         : {sig['tp2']:.2f}\n"
        f"TP3         : {sig['tp3']:.2f}\n```\n"
        f"💡 *Cara Entry:*\n_{timing}_\n\n"
        f"✅ *Window Entry:*\n"
        f"• Asia session    : 09:00–11:00 WITA\n"
        f"• London killzone : 14:00–16:00 WITA\n"
        f"• NY session      : 20:00–23:00 WITA\n\n"
        f"🎯 Confidence kemarin: *{sig['confidence']}%*\n{_anchor_conf_bar(sig['confidence'])}\n\n"
        f"━━━━━━━━━━━━━━\n"
        f"🌙 {moon['phase']} | {impact['bias']}\n"
        f"{luck['emoji']} {luck['label']}\n"
        f"⚠️ _Selalu konfirmasi dengan price action real-time_\n"
        f"🤖 _Anchor Day | {now.strftime('%H:%M WITA %d/%m/%Y')}_"
    )

def check_anchor_day():
    """
    Scheduler Anchor Day — dipanggil dari main loop setiap iterasi.
    Rabu 21:30 WITA  → analisis + kirim alert
    Kamis 08:05 WITA → kirim reminder entry
    """
    now = now_wita()
    h, m = now.hour, now.minute
    weekday = now.weekday()   # 0=Sen, 2=Rabu, 3=Kamis

    # ── Rabu 21:30 WITA: Anchor Day Analysis ────────────────────────────────
    if weekday == 2 and h == 21 and 30 <= m < 31:
        if not state.get("anchor_wednesday_sent"):
            state["anchor_wednesday_sent"] = True
            print("[ANCHOR] Menjalankan Anchor Day analysis...")
            try:
                sig = run_anchor_analysis()
                anchor_save_state(sig)
                msg = _format_anchor_wednesday(sig)
                send_telegram(msg)
                print(f"[ANCHOR] Alert terkirim: bias={sig.get('bias','?')}")
            except Exception as e:
                print(f"[ANCHOR] Error analysis: {e}")
                send_telegram(f"⚠️ *Anchor Day Error*\n\n`{e}`")

    # ── Kamis 08:05 WITA: Entry Reminder ─────────────────────────────────────
    if weekday == 3 and h == 8 and 5 <= m < 6:
        if not state.get("anchor_thursday_sent"):
            state["anchor_thursday_sent"] = True
            print("[ANCHOR] Mengirim reminder Kamis...")
            try:
                sig = anchor_load_thursday_state()
                if not sig:
                    send_telegram(
                        f"⚪ *KAMIS — Tidak ada Anchor Day Setup*\n\n"
                        f"_Tidak ada analisis Rabu yang tersimpan._\n"
                        f"_Lanjutkan dengan analisis biasa hari ini._\n\n"
                        f"🤖 _Anchor Day | {now.strftime('%H:%M WITA %d/%m/%Y')}_"
                    )
                elif sig.get("bias") == "NONE":
                    send_telegram(
                        f"⚪ *KAMIS — No Anchor Setup*\n\n"
                        f"_{sig.get('reason','Kemarin tidak ada setup valid')}_\n\n"
                        f"➡️ Gunakan analisis independen hari ini.\n"
                        f"🤖 _Anchor Day | {now.strftime('%H:%M WITA %d/%m/%Y')}_"
                    )
                else:
                    send_telegram(_format_anchor_thursday(sig))
                    print("[ANCHOR] Reminder Kamis terkirim")
            except Exception as e:
                print(f"[ANCHOR] Thursday error: {e}")


# ══════════════════════════════════════════════════════════


state = {
    "candles":[],"cur_candle":None,"prev_price":None,
    "candles_m15":[],"cur_candle_m15":None,
    "bos_m15":None,"bos_m15_time":None,
    "asia_lo":None,"asia_hi":None,"fib":None,"fib_locked":False,
    "buy_done":False,"sell_done":False,"buy2_done":False,
    "alerted":set(),"sr_alerted":set(),"pattern_alerted":set(),
    "last_day":None,"last_update":0,"briefing_sent":False,
    "weekly_sent":False,"storm_alerted":False,"low_asia_swept":False,
    "kz_alerted":set(),
    "last_yield":None,"last_yield_zone":None,"yield_alerted_today":False,"yield_checked":False,
    # ── Anchor Day ─────────────────────────────────────────
    "anchor_day_state": None,       # dict sinyal tersimpan (Rabu→Kamis)
    "anchor_wednesday_sent": False, # sudah kirim alert Rabu hari ini?
    "anchor_thursday_sent": False,  # sudah kirim reminder Kamis hari ini?
}

def reset_daily():
    today = now_wita().strftime("%Y-%m-%d")
    if state["last_day"] == today: return
    print(f"[RESET] {today}")
    state.update({
        "asia_lo":None,"asia_hi":None,"fib":None,"fib_locked":False,
        "buy_done":False,"sell_done":False,"buy2_done":False,
        "alerted":set(),"sr_alerted":set(),"pattern_alerted":set(),
        "cur_candle":None,"cur_candle_m15":None,
        "bos_m15":None,"bos_m15_time":None,
        "last_day":today,"briefing_sent":False,
        "storm_alerted":False,"low_asia_swept":False,"kz_alerted":set(),
        "yield_alerted_today":False,"yield_checked":False,
        "pivot_sent":False,"mtf_sent_hour":None,
        "news_sent_morning":False,"news_sent_afternoon":False,"calendar_sent":False,
        "last_yield":None,"last_yield_zone":None,
        # Reset flag harian (bukan data-nya — anchor_day_state tetap sampai Kamis)
        "anchor_wednesday_sent": False,
        "anchor_thursday_sent": False,
    })
    # anchor_day_state TIDAK direset — perlu persist dari Rabu ke Kamis

def check_killzone_alerts():
    if not market_open(): return
    now = now_wita()
    h, m = now.hour, now.minute
    for kz in KILLZONES:
        if h == kz["start_h"] and m == kz["start_m"]:
            kz_key = f"kz-{kz['name']}-{now.strftime('%Y-%m-%d')}"
            if kz_key in state["kz_alerted"]: continue
            state["kz_alerted"].add(kz_key)
            p = state["prev_price"] or 0
            moon = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
            start_min = kz["start_h"]*60 + kz["start_m"]
            end_min   = kz["end_h"]*60   + kz["end_m"]
            duration  = end_min - start_min
            header = f"🚨 *{kz['emoji']} {kz['name']}*" if kz["danger"] else f"⏰ *{kz['emoji']} {kz['name']}*"
            asia_info = ""
            if state["asia_lo"] and state["asia_hi"]:
                asia_info = (f"\n━━━━━━━━━━━━━━\n📍 Range Asia:\nLow: *${state['asia_lo']:.2f}*\n"
                             f"High: *${state['asia_hi']:.2f}*\nRange: {state['asia_hi']-state['asia_lo']:.1f} poin")
                if state["fib"]: asia_info += f"\n🔴 61.8%: *${state['fib']['f618']:.2f}*"
            send_telegram(
                f"━━━━━━━━━━━━━━\n{header}\n🕐 {h:02d}:{m:02d} WITA | Durasi: {duration} menit\n━━━━━━━━━━━━━━\n"
                f"💰 Harga: *${p:.2f}*\n\n📝 *{kz['desc']}*\n\n💡 *Action:*\n{kz['action']}{asia_info}\n"
                f"━━━━━━━━━━━━━━\n🌙 {moon['phase']} | {impact['bias']}\n⚠️ _Bukan saran investasi_"
            )
            print(f"[KILLZONE] {kz['name']} @ {h:02d}:{m:02d} WITA")

def check_yield_daily():
    now = now_wita()
    if now.hour == 19 and now.minute < 1 and not state["yield_checked"]:
        state["yield_checked"] = True
        y = fetch_us10y_yield()
        if y:
            analysis = analyze_yield(y); analysis["date"] = y["date"]
            prev_zone = state.get("last_yield_zone")
            is_new = (prev_zone != analysis["zone"])
            state["last_yield"] = y["yield"]; state["last_yield_zone"] = analysis["zone"]
            if is_new or analysis["zone"] == "DANGER": send_yield_alert(analysis, is_new=is_new)
            print(f"[YIELD] {y['yield']}% Zone:{analysis['zone']}")

def check_news_schedule():
    now = now_wita(); p = state["prev_price"] or 0
    if not p: return
    if now.hour % 4 == 1 and now.minute < 1:
        if state.get("mtf_sent_hour") != now.hour:
            state["mtf_sent_hour"] = now.hour
            if market_open(): send_mtf_analysis(p, state["candles"])
    if now.hour==8 and 30<=now.minute<31 and not state.get("calendar_sent"):
        state["calendar_sent"] = True; send_calendar_alert()
    if now.hour==9 and 5<=now.minute<6 and not state.get("pivot_sent"):
        state["pivot_sent"] = True; send_pivot_briefing(p, state["candles"])
    if now.hour==9 and now.minute<1 and not state.get("news_sent_morning"):
        state["news_sent_morning"] = True; send_news_briefing(p)
    if now.hour==16 and now.minute<1 and not state.get("news_sent_afternoon"):
        state["news_sent_afternoon"] = True; send_news_briefing(p)

def check_briefings():
    now=now_wita(); p=state["prev_price"]
    if not p: return
    if now.hour==8 and now.minute<1 and not state["briefing_sent"]:
        state["briefing_sent"]=True; send_morning_briefing(p)
    if now.weekday()==0 and now.hour==8 and 30<=now.minute<31 and not state["weekly_sent"]:
        state["weekly_sent"]=True; send_weekly_briefing(p)

def signal(sig_type, price, detail):
    key=f"{sig_type}-{now_wita().strftime('%Y-%m-%d-%H')}"
    if key in state["alerted"]: return
    state["alerted"].add(key)
    labels={"BUY1":"📈 BUY — Sesi Asia","SELL":"📉 SELL — London","BUY2":"🔄 BUY ke-2 — 61.8%"}
    moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
    send_telegram(
        f"🥇 *XAUUSD SIGNAL M5*\n━━━━━━━━━━━━━━\n{labels[sig_type]}\n💰 *${price:.2f}*\n{detail}\n"
        f"━━━━━━━━━━━━━━\n🌙 {moon['phase']} | {impact['bias']}\n"
        f"🕐 {now_wita().strftime('%H:%M:%S')} WITA\n⚠️ _Bukan saran investasi_"
    )

def check_sr_and_patterns(candle, all_candles):
    if not market_open(): return
    price=candle["close"]; b=detect_bos(all_candles)
    if not state["storm_alerted"]:
        storm=detect_perfect_storm(all_candles,price)
        if storm["score"]>=6:
            state["storm_alerted"]=True
            factor_text="\n".join([f"  {f}" for f in storm["factors"]])
            send_telegram(
                f"🌪️ *PERFECT STORM DETECTED!*\n━━━━━━━━━━━━━━\nLevel: {storm['level']} ({storm['score']}/12)\n\n"
                f"Faktor:\n{factor_text}\n\n💥 *{storm['action']}*\n━━━━━━━━━━━━━━\n"
                f"🎯 Watch:\n1. Asia sideway → London Hurricane 15:00\n2. Sweep → 61.8% Golden Ratio\n3. NY 20:00 = Dominant\n"
                f"🕐 {now_wita().strftime('%H:%M:%S')} WITA"
            )
    if state["asia_lo"] and get_session()=="london" and not state["low_asia_swept"]:
        if candle["low"]<state["asia_lo"]:
            state["low_asia_swept"]=True
            f=calc_fib(state["asia_lo"],state["asia_hi"]) if state["asia_hi"] else None
            fib_text=f"\n🔴 Golden Ratio 61.8%: *${f['f618']:.2f}*" if f else ""
            send_telegram(
                f"🌊 *LONDON SWEEP LOW ASIA!*\n━━━━━━━━━━━━━━\n"
                f"📍 Low Asia: *${state['asia_lo']:.2f}*\n📍 Candle Low: *${candle['low']:.2f}*{fib_text}\n\n"
                f"🎯 Monitor 61.8% untuk BUY reversal!\n🕐 {now_wita().strftime('%H:%M:%S')} WITA"
            )
    pivot = get_pivot_from_candles(all_candles)
    if pivot:
        pivot_levels = [
            (pivot["r3"],"R3","resistance"),(pivot["r2"],"R2","resistance"),
            (pivot["r1"],"R1","resistance"),(pivot["pivot"],"Pivot","neutral"),
            (pivot["s1"],"S1","support"),(pivot["s2"],"S2","support"),(pivot["s3"],"S3","support"),
        ]
        for plevel, plabel, ptype in pivot_levels:
            if abs(price - plevel) <= SR_TOLERANCE:
                pk = f"pivot-{plabel}-{now_wita().strftime('%Y-%m-%d-%H')}"
                if pk not in state["sr_alerted"]:
                    state["sr_alerted"].add(pk)
                    emoji = "🔴" if ptype=="resistance" else "🟢" if ptype=="support" else "⚪"
                    signal_hint = "→ Cari SELL" if ptype=="resistance" else "→ Cari BUY" if ptype=="support" else "→ Level tengah"
                    send_telegram(
                        f"📐 *Harga Menyentuh {plabel.upper()}!*\n━━━━━━━━━━━━━━\n"
                        f"{emoji} Pivot {plabel}: *${plevel:.2f}*\n💰 Harga: *${price:.2f}*\n"
                        f"💡 {signal_hint}\n⏳ Tunggu BOS M15 konfirmasi!\n🕐 {now_wita().strftime('%H:%M:%S')} WITA"
                    )
    for sr in get_auto_sr(all_candles,price):
        level,label,sr_type=sr["price"],sr["label"],sr["type"]
        if abs(price-level)>SR_TOLERANCE: continue
        touch_key=f"touch-{label}-{now_wita().strftime('%Y-%m-%d-%H')}"
        if touch_key not in state["sr_alerted"]:
            state["sr_alerted"].add(touch_key)
            emoji="🔴" if sr_type=="resistance" else "🟢"
            send_telegram(
                f"📍 *Menyentuh {sr_type.upper()}*\n━━━━━━━━━━━━━━\n"
                f"{emoji} {label}: *${level:.2f}*\n💰 *${price:.2f}*\n"
                f"📏 Jarak: {abs(price-level):.1f} poin\n🕐 {now_wita().strftime('%H:%M:%S')} WITA\n⏳ Tunggu konfirmasi..."
            )

def process_bos_m15(bos, old_bos, price):
    if not market_open(): return
    moon   = get_moon_phase(); impact = get_moon_impact(moon["phase_en"])
    luck   = get_luck_status()
    sess_map = {"asia":"🌏 Asia","pre":"⏳ Pre-London","london":"🇬🇧 London","ny":"🇺🇸 New York"}
    bos_m5 = detect_bos(state["candles"])
    confirmation = ""; power = ""
    if bos_m5 == bos:
        confirmation = "✅ *M5 BOS KONFIRMASI!* → ENTRY VALID!"
        power = "🔥🔥🔥 SANGAT KUAT"
    else:
        confirmation = "⏳ Tunggu M5 BOS konfirmasi dulu"
        power = "⭐⭐ SEDANG"
    fib_text = ""
    if state["fib"]:
        f = state["fib"]
        if abs(price - f["f618"]) <= 15:
            fib_text = f"\n🎯 *Dekat 61.8% Golden Ratio!* ${f['f618']:.2f}"
            power = "🔥🔥🔥🔥 SUPER KUAT!" if bos_m5 == bos else "🔥🔥🔥 KUAT"
    key = f"bos_m15_{bos}_{now_wita().strftime('%Y-%m-%d-%H-%M')}"
    if key in state["alerted"]: return
    state["alerted"].add(key)
    emoji = "📈" if bos == "BULL" else "📉"
    direction = "BULLISH" if bos == "BULL" else "BEARISH"
    action = "BUY 📈" if bos == "BULL" else "SELL 📉"
    send_telegram(
        f"⚡ *BOS M15 TERBENTUK!*\n━━━━━━━━━━━━━━\n{emoji} *{direction} BOS M15*\n"
        f"💰 Harga: *${price:.2f}*\n📊 Kekuatan: {power}\n\n━━━━━━━━━━━━━━\n"
        f"*🎯 Konfirmasi M5:*\n{confirmation}{fib_text}\n\n━━━━━━━━━━━━━━\n"
        f"*💡 Yang harus dilakukan:*\n{'✅ Entry ' + action + ' sekarang!' if bos_m5 == bos else '👀 Buka chart M5'}\n"
        f"{'✅ M15 + M5 + Fib = TRIPLE KONFIRMASI!' if bos_m5 == bos and fib_text else ''}\n🛡 Set SL sebelum entry!\n\n"
        f"━━━━━━━━━━━━━━\n🌏 Sesi: {sess_map.get(get_session())}\n🌙 {moon['phase']} | {impact['bias']}\n"
        f"{luck['emoji']} {luck['label']}\n🕐 {now_wita().strftime('%H:%M:%S')} WITA\n━━━━━━━━━━━━━━\n"
        f"⚠️ _Konfirmasi di chart sebelum entry!_"
    )
    print(f"[BOS M15] {direction} @ ${price:.2f} | M5:{bos_m5} | Power:{power}")

def process_candle(candle):
    if not market_open(): return
    sess=get_session(); all_c=state["candles"]; b=detect_bos(all_c)
    check_sr_and_patterns(candle,all_c)
    if sess=="asia":
        state["asia_lo"]=candle["low"] if state["asia_lo"] is None else min(state["asia_lo"],candle["low"])
        state["asia_hi"]=candle["high"] if state["asia_hi"] is None else max(state["asia_hi"],candle["high"])
        if b=="BULL" and not state["buy_done"]:
            state["buy_done"]=True
            signal("BUY1",candle["close"],
                   f"📍 Low Asia: *${state['asia_lo']:.2f}*\n🎯 Target: High Asia *${state['asia_hi']:.2f}*\n🛡 SL: Di bawah Low Asia\n📊 TF: M5")
    if sess in ("pre","london"):
        if state["asia_lo"] and state["asia_hi"] and not state["fib_locked"]:
            f=calc_fib(state["asia_lo"],state["asia_hi"])
            state["fib"]=f; state["fib_locked"]=True
            send_telegram(
                f"📐 *Fibonacci Terbentuk*\n━━━━━━━━━━━━━━\n🟦 Low:  *${f['f100']:.2f}*\n"
                f"🟡 38.2%: *${f['f382']:.2f}*\n🔴 61.8%: *${f['f618']:.2f}* ← Golden Ratio\n"
                f"🟤 78.6%: *${f['f786']:.2f}*\n🟢 High:  *${f['f0']:.2f}*\n"
                f"🚀 Ext 127%: *${f['f127']:.2f}*\n🕐 {now_wita().strftime('%H:%M')} WITA"
            )
    if sess=="london" and state["asia_hi"] and state["fib"]:
        hi,f=state["asia_hi"],state["fib"]
        if abs(candle["close"]-hi)<=8 and b=="BEAR" and not state["sell_done"]:
            state["sell_done"]=True
            signal("SELL",candle["close"],
                   f"📍 High Asia: *${hi:.2f}*\n🎯 TP1: 61.8% *${f['f618']:.2f}*\n"
                   f"🎯 TP2: 78.6% *${f['f786']:.2f}*\n🛡 SL: Atas High Asia\n📊 TF: M5")
        if abs(candle["close"]-f["f618"])<=8 and b=="BULL" and not state["buy2_done"]:
            state["buy2_done"]=True
            signal("BUY2",candle["close"],
                   f"📍 Golden Ratio 61.8%: *${f['f618']:.2f}*\n🎯 TP1: High Asia *${hi:.2f}*\n"
                   f"🎯 TP2: Extension *${f['f127']:.2f}*\n🛡 SL: Bawah 61.8%\n📊 TF: M5")


# ── Commands ──────────────────────────────────────────────
def handle_commands():
    updates=get_updates(offset=state["last_update"])
    for upd in updates:
        state["last_update"]=upd["update_id"]+1
        text=upd.get("message",{}).get("text","").strip()
        if not text: continue
        print(f"[CMD] {text}")

        if text in ("/start","/help"):
            send_telegram(
                f"🥇 *XAUUSD Bot — Sinarmas + Anchor Day Edition*\n━━━━━━━━━━━━━━\n"
                f"/briefing    → Daily briefing sekarang\n"
                f"/weekly      → Weekly briefing\n"
                f"/luck        → Cek luck hari ini (Sinarmas)\n"
                f"/luckmonth   → Luck calendar bulan ini\n"
                f"/killzone    → Jadwal killzone hari ini\n"
                f"/storm       → Perfect Storm meter\n"
                f"/status      → Status + astro + luck\n"
                f"/moon        → Fase bulan\n"
                f"/astro       → Planet hari ini\n"
                f"/listsr      → Level S&R\n"
                f"/mtf         → Multi Timeframe Analysis\n"
                f"/bos         → Status BOS M15 & M5 sekarang\n"
                f"/pivot       → Pivot Point hari ini\n"
                f"/news        → Berita gold + analisa AI\n"
                f"/calendar    → Jadwal news hari ini\n"
                f"/yield       → US 10Y Yield + Trump Zone\n"
                f"/trump       → Penjelasan Trump Yield Theory\n"
                f"/patterns    → Info candle patterns\n"
                f"/anchorday   → 🗓️ Anchor Day analysis sekarang\n"
                f"/kamis       → ⏰ Cek setup Kamis dari Anchor Day\n"
                f"/help        → Menu ini\n"
                f"━━━━━━━━━━━━━━\n"
                f"🌅 Daily: *08:00 WITA*\n📅 Weekly: *Senin 08:30 WITA*\n"
                f"🗓️ Anchor Day: *Rabu 21:30 WITA* (otomatis)\n"
                f"⏰ Kamis Setup: *Kamis 08:05 WITA* (otomatis)\n"
                f"⏰ Killzone auto-alert WITA\n"
                f"━━━━━━━━━━━━━━\nBot aktif 24 jam • gold-api.com"
            )

        elif text=="/anchorday":
            send_telegram("⏳ Menjalankan Anchor Day analysis...")
            try:
                sig = run_anchor_analysis()
                anchor_save_state(sig)
                msg = _format_anchor_wednesday(sig)
                send_telegram(msg)
            except Exception as e:
                send_telegram(f"⚠️ Error: `{e}`")

        elif text=="/kamis":
            sig = anchor_load_thursday_state()
            if not sig:
                send_telegram(
                    "⚪ *Tidak ada Anchor Day setup tersimpan*\n\n"
                    "_Jalankan /anchorday terlebih dahulu._"
                )
            elif sig.get("bias") == "NONE":
                send_telegram(
                    f"⚪ *No Anchor Setup*\n\n_{sig.get('reason','Tidak ada setup valid')}_\n\n"
                    f"➡️ Gunakan analisis independen."
                )
            else:
                send_telegram(_format_anchor_thursday(sig))

        elif text=="/luck":
            luck=get_luck_status(); now_d=now_wita()
            send_telegram(
                f"🍀 *LUCK STATUS HARI INI*\n━━━━━━━━━━━━━━\n"
                f"📅 {now_d.day} {get_month_name()} {now_d.year}\n\nStatus: {luck['label']}\nWarna: {luck['color']}\n\n"
                f"📝 {luck['desc']}\n\n💡 *Saran Trading:*\n{luck['trading']}\n━━━━━━━━━━━━━━\n"
                f"Sumber: Kalender Bank Sinarmas 2026\n🔴 Lucky = Hari baik\n📅 Ordinary = Hari biasa\n⚠️ Unlucky = Hindari keputusan besar"
            )

        elif text=="/luckmonth":
            now_d=now_wita(); month_data=SINARMAS_CALENDAR.get(now_d.month,{})
            lucky_days=[str(d) for d,s in month_data.items() if s=="L"]
            unlucky_days=[str(d) for d,s in month_data.items() if s=="U"]
            send_telegram(
                f"🍀 *LUCK CALENDAR — {get_month_name()} {now_d.year}*\n━━━━━━━━━━━━━━\n"
                f"🔴 *Lucky Days ({len(lucky_days)} hari):*\n{', '.join(lucky_days)}\n\n"
                f"⚠️ *Unlucky Days ({len(unlucky_days)} hari):*\n{', '.join(unlucky_days)}\n\n━━━━━━━━━━━━━━\n"
                f"💡 *Trading Strategy:*\n🔴 Lucky → Full size, confident entry\n📅 Ordinary → Normal trading\n"
                f"⚠️ Unlucky → Kurangi size, ekstra hati-hati\n━━━━━━━━━━━━━━\nSumber: Bank Sinarmas 2026"
            )

        elif text=="/briefing":
            p=state["prev_price"]
            if p: send_morning_briefing(p)
            else: send_telegram("⏳ Harga belum tersedia.")

        elif text=="/weekly":
            p=state["prev_price"]
            if p: send_weekly_briefing(p)
            else: send_telegram("⏳ Harga belum tersedia.")

        elif text=="/killzone":
            now=now_wita(); kz_list=[]
            for kz in KILLZONES:
                h,m=now.hour,now.minute; t=h*60+m
                start=kz["start_h"]*60+kz["start_m"]; end=kz["end_h"]*60+kz["end_m"]
                is_active="🔴 AKTIF SEKARANG!" if start<=t<end else ""
                kz_list.append(f"{kz['emoji']} *{kz['name']}*\n   {kz['start_h']:02d}:{kz['start_m']:02d}–{kz['end_h']:02d}:{kz['end_m']:02d} WITA {is_active}")
            kz_text="\n\n".join(kz_list); kz_now=get_current_killzone()
            current_text=f"\n\n📍 *Sekarang:* {kz_now['emoji']} {kz_now['name']}" if kz_now else "\n\n📍 *Sekarang:* Di luar killzone"
            send_telegram(
                f"⏰ *KILLZONE SCHEDULE WITA*\n━━━━━━━━━━━━━━\n\n{kz_text}{current_text}\n\n━━━━━━━━━━━━━━\n"
                f"⚠️ Judas Swing: 15:00–15:30 WITA\n🔥 Paling volatile: 20:00–21:30 WITA\n"
                f"❌ Dead zone: 04:00–10:00 WITA\n🕐 {now.strftime('%H:%M:%S')} WITA"
            )

        elif text=="/storm":
            p=state["prev_price"] or 0; storm=detect_perfect_storm(state["candles"],p)
            factor_text="\n".join([f"  {f}" for f in storm["factors"]]) if storm["factors"] else "  Tidak ada"
            send_telegram(
                f"🌪️ *PERFECT STORM METER*\n━━━━━━━━━━━━━━\nLevel: {storm['level']}\nScore: {storm['score']}/12\n\n"
                f"Faktor:\n{factor_text}\n\n💥 {storm['action']}\n━━━━━━━━━━━━━━\n"
                f"🎯 Dominant Strategy:\n1. Asia sideway → London 15:00 Hurricane\n2. Sweep Low Asia → 61.8% BUY\n"
                f"3. NY 20:00 = Arah Dominan\n🕐 {now_wita().strftime('%H:%M:%S')} WITA"
            )

        elif text=="/status":
            p=state["prev_price"] or 0; moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
            planets=get_planet_info(); storm=detect_perfect_storm(state["candles"],p)
            planet_text="\n".join([f"  • {pl}" for pl in planets])
            sess_map={"asia":"🌏 Asia","pre":"⏳ Pre-London","london":"🇬🇧 London","ny":"🇺🇸 New York"}
            kz=get_current_killzone(); kz_text=f"\n⏰ Killzone: {kz['emoji']} {kz['name']}" if kz else ""
            luck=get_luck_status(); m15_status = get_m15_status()
            bos_m5_now = detect_bos(state["candles"])
            m5_status  = f"📈 BULLISH" if bos_m5_now=="BULL" else f"📉 BEARISH" if bos_m5_now=="BEAR" else "⏳ Belum ada"
            triple = ""
            if state["bos_m15"] and bos_m5_now == state["bos_m15"]: triple = f"\n🔥 *M15+M5 SEARAH = ENTRY VALID!*"
            # Anchor Day status
            anchor_sig = state.get("anchor_day_state")
            anchor_text = ""
            if anchor_sig and anchor_sig.get("bias") not in (None, "NONE", ""):
                bias_e = "🔴 SELL" if anchor_sig["bias"]=="SELL" else "🟢 BUY"
                anchor_text = f"\n🗓️ Anchor Day: {bias_e} (conf: {anchor_sig.get('confidence',0)}%)"
            send_telegram(
                f"📊 *STATUS XAUUSD BOT*\n━━━━━━━━━━━━━━\n{luck['label']} | {luck['color']}\n📝 {luck['desc']}\n\n"
                f"💰 *${p:.2f}* | {sess_map.get(get_session())}{kz_text}\n"
                f"📍 Low Asia: {'$'+str(state['asia_lo']) if state['asia_lo'] else 'Belum'}\n"
                f"📍 High Asia: {'$'+str(state['asia_hi']) if state['asia_hi'] else 'Belum'}\n"
                f"📐 Fib: {'✅' if state['fib'] else '⏳'}\n"
                f"📈 BUY: {'✅' if state['buy_done'] else '⏳'} | 📉 SELL: {'✅' if state['sell_done'] else '⏳'} | 🔄 BUY2: {'✅' if state['buy2_done'] else '⏳'}\n"
                f"🌊 Swept: {'✅' if state['low_asia_swept'] else '❌'}{anchor_text}\n"
                f"━━━━━━━━━━━━━━\n📊 *BOS Status:*\nM15: {m15_status}\nM5:  {m5_status}{triple}\n"
                f"━━━━━━━━━━━━━━\n🌪️ {storm['level']} ({storm['score']}/12)\n━━━━━━━━━━━━━━\n"
                f"🌙 {moon['phase']} ({moon['illumination']}%)\nBias: {impact['bias']}\n{impact['desc']}\n💡 {impact['trading']}\n\n"
                f"🪐\n{planet_text}\n━━━━━━━━━━━━━━\n🕐 {now_wita().strftime('%d %b %Y %H:%M:%S')} WITA"
            )

        elif text=="/moon":
            moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
            send_telegram(
                f"🌙 *FASE BULAN & GOLD*\n━━━━━━━━━━━━━━\n{moon['phase']} ({moon['illumination']}%)\n"
                f"Hari ke-{moon['days']} | Full: {moon['next_full']:.0f}hr | New: {moon['next_new']:.0f}hr\n\n"
                f"Bias: {impact['bias']}\n{impact['desc']}\n💡 {impact['trading']}\n━━━━━━━━━━━━━━\n"
                f"🌑 New → Reversal | 🌒🌓 Waxing → Naik\n🌕 Full → Reversal | 🌖🌗 Waning → Turun"
            )

        elif text=="/astro":
            moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
            planets=get_planet_info(); planet_text="\n".join([f"• {p}" for p in planets])
            send_telegram(
                f"🔭 *ASTROLOGI — {now_wita().strftime('%d %b %Y')}*\n━━━━━━━━━━━━━━\n"
                f"🌙 {moon['phase']} ({moon['illumination']}%)\n\n🪐 Planet:\n{planet_text}\n\n"
                f"Bias: {impact['bias']}\n{impact['desc']}\n💡 {impact['trading']}"
            )

        elif text=="/listsr":
            p=state["prev_price"] or 0; levels=get_auto_sr(state["candles"],p)
            if not levels: send_telegram("⏳ Data S&R belum cukup.")
            else:
                res=sorted([l for l in levels if l["type"]=="resistance" and l["price"]>p],key=lambda x:x["price"])[:5]
                sup=sorted([l for l in levels if l["type"]=="support" and l["price"]<p],key=lambda x:x["price"],reverse=True)[:5]
                msg=[f"📋 *S&R* (${p:.2f})\n"]
                if res:
                    msg.append("🔴 *Resistance:*")
                    for l in res: msg.append(f"  • {l['label']}: *${l['price']:.2f}* (+{l['price']-p:.1f})")
                if sup:
                    msg.append("\n🟢 *Support:*")
                    for l in sup: msg.append(f"  • {l['label']}: *${l['price']:.2f}* (-{p-l['price']:.1f})")
                send_telegram("\n".join(msg))

        elif text=="/bos":
            p = state["prev_price"] or 0; bos_m5 = detect_bos(state["candles"])
            bos_m15 = state.get("bos_m15"); m15_t = state.get("bos_m15_time")
            m5_str  = f"📈 BULLISH" if bos_m5=="BULL" else f"📉 BEARISH" if bos_m5=="BEAR" else "⏳ Belum ada"
            m15_str = f"📈 BULLISH" if bos_m15=="BULL" else f"📉 BEARISH" if bos_m15=="BEAR" else "⏳ Belum ada"
            m15_time = m15_t.strftime("%H:%M WITA") if m15_t else "-"
            if bos_m5 and bos_m15 and bos_m5 == bos_m15:
                power = "🔥🔥🔥🔥 SUPER KUAT — M15+M5 SEARAH!"
                action = "✅ ENTRY VALID! BUY" if bos_m15=="BULL" else "✅ ENTRY VALID! SELL"
            elif bos_m15:
                power = "⭐⭐⭐ KUAT — Tunggu M5 konfirmasi"
                action = f"⏳ Tunggu M5 BOS {'BULL' if bos_m15=='BULL' else 'BEAR'}"
            elif bos_m5:
                power = "⭐⭐ SEDANG — M5 saja, belum M15"; action = "⚠️ Hati-hati, belum dikonfirmasi M15"
            else:
                power = "⏳ Belum ada BOS"; action = "Tunggu BOS terbentuk"
            fib_note = ""
            if state["fib"] and p:
                f = state["fib"]
                if abs(p - f["f618"]) <= 20: fib_note = f"\n🎯 *Dekat Golden Ratio 61.8%!* ${f['f618']:.2f}"
            send_telegram(
                f"📊 *BOS STATUS — XAUUSD*\n━━━━━━━━━━━━━━\n💰 Harga: *${p:.2f}*\n\n"
                f"⏱ *M15 BOS:* {m15_str}\n   Terbentuk: {m15_time}\n\n⚡ *M5 BOS:* {m5_str}\n\n"
                f"━━━━━━━━━━━━━━\n💪 *Kekuatan:*\n{power}{fib_note}\n\n💡 *Action:*\n{action}\n"
                f"━━━━━━━━━━━━━━\n📋 *Panduan:*\n🔥🔥🔥🔥 M15+M5 = Entry langsung\n"
                f"⭐⭐⭐ M15 saja = Standby, tunggu M5\n⭐⭐ M5 saja = Skip atau hati-hati\n"
                f"━━━━━━━━━━━━━━\n🕐 {now_wita().strftime('%H:%M:%S')} WITA"
            )

        elif text=="/news":
            p = state["prev_price"] or 0
            send_telegram("⏳ Mengambil berita & analisa AI... Tunggu sebentar!")
            send_news_briefing(p)

        elif text=="/calendar":
            send_calendar_alert()

        elif text=="/mtf":
            p = state["prev_price"] or 0
            if len(state["candles"]) < 50: send_telegram("⏳ Data belum cukup untuk MTF.")
            else:
                send_telegram("⏳ Menganalisa semua timeframe... Tunggu sebentar!")
                send_mtf_analysis(p, state["candles"])

        elif text=="/pivot":
            p = state["prev_price"] or 0
            pivot = get_pivot_from_candles(state["candles"])
            if not pivot: send_telegram("⏳ Data pivot belum cukup.")
            else: send_pivot_briefing(p, state["candles"])

        elif text=="/yield":
            y = fetch_us10y_yield()
            if not y: send_telegram("⏳ Data yield belum tersedia.")
            else:
                analysis = analyze_yield(y); analysis["date"] = y["date"]
                send_yield_alert(analysis, is_new=False)

        elif text=="/trump":
            send_telegram(
                "🇺🇸 *TRUMP YIELD THEORY*\n━━━━━━━━━━━━━━\n"
                "📊 *Claim:*\nDengan hutang $39 Triliun,\nTrump buat 'good news' setiap kali\n"
                "US 10Y Yield mendekati 4.3–4.5%\nuntuk cegah bunga naik!\n\n━━━━━━━━━━━━━━\n"
                "📈 *Backtest 17 Events (2025–2026):*\n✅ Yield turun: 13/16 = *81%*\n❌ Yield naik:   3/16 = 19%\n\n"
                "📋 *Contoh Trump good news:*\n• No China tariffs\n• 90-day pause tariffs\n• US-UK trade deal\n• Iran peace talks\n\n"
                "━━━━━━━━━━━━━━\n🎯 *Dampak ke Gold:*\nYield turun → USD lemah → Gold NAIK!\n\n"
                "⚡ *Trump Zone: 4.30–4.50%*\n→ Kalau yield masuk zone ini\n  bot otomatis kirim alert!\n"
                "→ 81% yield akan turun\n→ Siapkan setup BUY gold!\n━━━━━━━━━━━━━━\nKetik /yield untuk cek data sekarang!"
            )

        elif text=="/patterns":
            send_telegram(
                f"🕯 *CANDLE PATTERNS*\n━━━━━━━━━━━━━━\n\n"
                f"🔴 *TIER 1 — STRONG* (selalu kirim)\n• Bullish/Bearish Engulfing\n• Bullish/Bearish Pin Bar\n• Morning/Evening Star\n\n"
                f"🟡 *TIER 2 — WATCH* (di level kunci)\n• Hammer / Shooting Star\n• Tweezer Top/Bottom\n• Bullish/Bearish Harami\n\n"
                f"🟢 *TIER 3 — INFO* (hanya di level kunci)\n• Doji / Inside Bar / Marubozu\n\n"
                f"Level kunci = S&R + Fibonacci\n⚠️ Konfirmasi dengan BOS!"
            )


# ── Main ──────────────────────────────────────────────────
def main():
    print("="*50)
    print("  XAUUSD Bot v16 — Anchor Day Edition")
    print("  Anchor Day Rabu 21:30 | Reminder Kamis 08:05")
    print("="*50)
    moon=get_moon_phase(); impact=get_moon_impact(moon["phase_en"])
    send_telegram(
        f"🚀 *XAUUSD Bot v16 — Anchor Day Edition!*\n━━━━━━━━━━━━━━\n"
        f"📡 gold-api.com | 📊 M5 | 🕐 WITA\n\n"
        f"*Fitur:*\n"
        f"🗓️ Anchor Day Analysis (Rabu 21:30 WITA)\n"
        f"⏰ Entry Reminder (Kamis 08:05 WITA)\n"
        f"⏰ Killzone Alert otomatis (WITA)\n"
        f"📊 BOS M15 (utama) + M5 filter\n"
        f"📰 AI News Analysis otomatis\n"
        f"📐 Pivot Point R1/R2/R3 + S1/S2/S3\n"
        f"📊 MTF Analysis setiap 4 jam\n"
        f"🌪️ Perfect Storm detection\n"
        f"🌅 Daily briefing: *08:00 WITA*\n\n"
        f"⏰ *Jadwal Otomatis:*\n"
        f"08:00 Morning briefing\n"
        f"08:30 Economic calendar\n"
        f"09:00 AI news analysis\n"
        f"09:05 Pivot points\n"
        f"08:05 Kamis: Anchor Day reminder\n"
        f"16:00 Afternoon news\n"
        f"19:00 US 10Y yield update\n"
        f"21:30 Rabu: Anchor Day analysis\n\n"
        f"🌙 {moon['phase']} | {impact['bias']}\n━━━━━━━━━━━━━━\n"
        f"/anchorday untuk analysis sekarang!\n"
        f"/kamis untuk cek setup Kamis!\n"
        f"🕐 {now_wita().strftime('%d %b %Y %H:%M')} WITA"
    )

    while True:
        try:
            reset_daily()
            check_briefings()
            check_yield_daily()
            check_news_schedule()
            check_killzone_alerts()
            check_anchor_day()          # ← Anchor Day scheduler
            handle_commands()
            price=fetch_price()
            if price:
                prev=state["prev_price"]
                chg=round(price-prev,2) if prev else 0
                arrow="▲" if chg>=0 else "▼"
                print(f"[{now_wita().strftime('%H:%M:%S')} WITA] ${price:.2f} {arrow}{abs(chg):.2f} | {get_session()} | Lo:{state['asia_lo']} Hi:{state['asia_hi']}")
                mk=int(time.time()//300)
                if state["cur_candle"] is None or state["cur_candle"]["mk"]!=mk:
                    if state["cur_candle"] is not None:
                        closed={k:state["cur_candle"][k] for k in ["open","high","low","close"]}
                        state["candles"]=state["candles"][-8640:]+[closed]
                        process_candle(closed)
                        # ── Update M15 candle ────────────────────────────
                        mk15 = int(time.time()//900)
                        if state["cur_candle_m15"] is None or state["cur_candle_m15"]["mk"]!=mk15:
                            if state["cur_candle_m15"] is not None:
                                closed15={k:state["cur_candle_m15"][k] for k in ["open","high","low","close"]}
                                state["candles_m15"]=state["candles_m15"][-2016:]+[closed15]
                                # BOS M15 detection
                                new_bos = detect_bos_m15()
                                old_bos = state["bos_m15"]
                                if new_bos and new_bos != old_bos:
                                    state["bos_m15"] = new_bos
                                    state["bos_m15_time"] = now_wita()
                                    process_bos_m15(new_bos, old_bos, price)
                            state["cur_candle_m15"]={"mk":mk15,"open":price,"high":price,"low":price,"close":price}
                        else:
                            c15=state["cur_candle_m15"]
                            c15["high"]=max(c15["high"],price); c15["low"]=min(c15["low"],price); c15["close"]=price
                    state["cur_candle"]={"mk":mk,"open":price,"high":price,"low":price,"close":price}
                else:
                    c=state["cur_candle"]
                    c["high"]=max(c["high"],price); c["low"]=min(c["low"],price); c["close"]=price
                state["prev_price"]=price
        except KeyboardInterrupt:
            print("\n[STOP]"); send_telegram("⏹ *Bot dihentikan.*"); break
        except Exception as e:
            print(f"[ERROR] {e}")
        time.sleep(FETCH_INTERVAL)

if __name__=="__main__":
    main()
