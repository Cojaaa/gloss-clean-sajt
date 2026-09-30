from flask import Flask, render_template, request, jsonify
import json
import os
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

app = Flask(__name__, template_folder=TEMPLATE_DIR)

TELEGRAM_BOT_TOKEN = "8660458192:AAGrvs0QwgyMMnDN99MyPJLvbnK-dTK1o-U"
TELEGRAM_CHAT_ID = "5273881275"

DB_FILE = os.path.join(BASE_DIR, "rezervacije.json")
RECENZIJE_FILE = os.path.join(BASE_DIR, "recenzije.json")

def posalji_telegram_poruku(tekst):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({'chat_id': TELEGRAM_CHAT_ID, "text": tekst, "parse_mode": "Markdown"}).encode("utf-8")
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req)
    except Exception as e:
        print(f"Greška pri slanju na Telegram: {e}")

def ucitaj_podatke(fajl):
    if os.path.exists(fajl):
        with open(fajl, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return []
    return []

def sacuvaj_podatke(fajl, podaci):
    with open(fajl, "w", encoding="utf-8") as f:
        json.dump(podaci, f, ensure_ascii=False, indent=4)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/zauzeti-termini", methods=["GET"])
def zauzeti_termini():
    datum = request.args.get("datum")
    rezervacije = ucitaj_podatke(DB_FILE)
    zauzeti = [r["vreme"] for r in rezervacije if r.get("datum") == datum]
    return jsonify(zauzeti)

@app.route("/rezervisi", methods=["POST"])
def rezervisi():
    data = request.json or {}
    ime = data.get("ime")
    telefon = data.get("telefon")
    usluga = data.get("usluga")
    datum = data.get("datum")
    vreme = data.get("vreme")

    if not all([ime, telefon, usluga, datum, vreme]):
        return jsonify({"status": "error", "poruka": "Molimo popunite sva polja."}), 400

    rezervacije = ucitaj_podatke(DB_FILE)

    for r in rezervacije:
        if r.get("datum") == datum and r.get("vreme") == vreme:
            return jsonify({"status": "error", "poruka": "Termin je već zauzet!"}), 400

    nova_rezervacija = {
        "ime": ime,
        "telefon": telefon,
        "usluga": usluga,
        "datum": datum,
        "vreme": vreme
    }
    rezervacije.append(nova_rezervacija)
    sacuvaj_podatke(DB_FILE, rezervacije)

    poruka = f"✨ *GLOSS CLEAN - NOVA REZERVACIJA!*\n\n👤 *Ime:* {ime}\n📞 *Telefon:* {telefon}\n🛋 *Usluga:* {usluga}\n📅 *Datum:* {datum}\n⏰ *Vreme:* {vreme}"
    posalji_telegram_poruku(poruka)

    return jsonify({"status": "success", "poruka": "Uspešno ste rezervisali termin!"})

@app.route("/recenzije", methods=["GET"])
def preuzmi_recenzije():
    recenzije = ucitaj_podatke(RECENZIJE_FILE)
    return jsonify(recenzije)

@app.route("/ostavi-recenziju", methods=["POST"])
def ostavi_recenziju():
    data = request.json or {}
    ime = data.get("ime")
    ocena = data.get("ocena")
    komentar = data.get("komentar")

    if not ime or not ocena or not komentar:
        return jsonify({"status": "error", "poruka": "Molimo popunite sva polja."}), 400

    recenzije = ucitaj_podatke(RECENZIJE_FILE)
    nova_recenzija = {"ime": ime, "ocena": int(ocena), "komentar": komentar}
    recenzije.insert(0, nova_recenzija)
    sacuvaj_podatke(RECENZIJE_FILE, recenzije)

    zvezdice = "⭐" * int(ocena)
    poruka = f"💬 *GLOSS CLEAN - NOVA RECENZIJA!*\n\n👤 *Ime:* {ime}\n⭐ *Ocena:* {zvezdice} ({ocena}/5)\n📝 *Komentar:* {komentar}"
    posalji_telegram_poruku(poruka)

    return jsonify({"status": "success", "poruka": "Hvala na recenziji!"})

if __name__ == "__main__":
    app.run(debug=True)
