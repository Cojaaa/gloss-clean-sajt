import json
import os
import requests
from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# --- GREEN API PODEŠAVANJA ---
ID_INSTANCE = "710722751720"
API_TOKEN = "51cab856f6da43c1aa1751a09221bf11"
GROUP_ID = "120363429949318594@g.us"

FAJL_REZERVACIJE = "rezervacije.json"
FAJL_RECENZIJE = "recenzije.json"


def ucitaj_podatke(fajl):
  if not os.path.exists(fajl):
    return []
  with open(fajl, "r", encoding="utf-8") as f:
    try:
      return json.load(f)
    except Exception:
      return []


def sacuvaj_podatke(fajl, podaci):
  with open(fajl, "w", encoding="utf-8") as f:
    json.dump(podaci, f, ensure_ascii=False, indent=4)


def posalji_u_whatsapp_grupu(tekst_poruke):
  """Šalje poruku direktno u WhatsApp grupu"""
  # Ispravljen host na 7107.api.greenapi.com
  url = f"https://7107.api.greenapi.com/waInstance{ID_INSTANCE}/sendMessage/{API_TOKEN}"
  payload = {"chatId": GROUP_ID, "message": tekst_poruke}
  headers = {"Content-Type": "application/json"}

  try:
    res = requests.post(url, json=payload, headers=headers, timeout=10)
    print(f"Green API status code: {res.status_code}")
    print(f"Green API response: {res.text}")
  except Exception as e:
    print(f"Greška pri slanju WhatsApp poruke: {e}")


@app.route("/")
def index():
  return render_template("index.html")


@app.route("/zauzeti-termini", methods=["GET"])
def zauzeti_termini():
  datum = request.args.get("datum")
  rezervacije = ucitaj_podatke(FAJL_REZERVACIJE)
  zauzeti = [r["vreme"] for r in rezervacije if r.get("datum") == datum]
  return jsonify(zauzeti)


@app.route("/rezervisi", methods=["POST"])
def rezervisi():
  podaci = request.get_json()
  ime = podaci.get("ime")
  telefon = podaci.get("telefon")
  usluga = podaci.get("usluga")
  datum = podaci.get("datum")
  vreme = podaci.get("vreme")

  if not all([ime, telefon, usluga, datum, vreme]):
    return jsonify({"poruka": "Molimo popunite sva polja!"}), 400

  rezervacije = ucitaj_podatke(FAJL_REZERVACIJE)

  for r in rezervacije:
    if r.get("datum") == datum and r.get("vreme") == vreme:
      return (
          jsonify({"poruka": "Ovaj termin je u međuvremenu zauzet!"}),
          400,
      )

  nova_rezervacija = {
      "ime": ime,
      "telefon": telefon,
      "usluga": usluga,
      "datum": datum,
      "vreme": vreme,
  }

  rezervacije.append(nova_rezervacija)
  sacuvaj_podatke(FAJL_REZERVACIJE, rezervacije)

  # Formiranje i slanje poruke u WhatsApp grupu
  poruka_za_grupu = (
      f"🚨 NOVA REZERVACIJA! 🚨\n\n"
      f"👤 Klijent: {ime}\n"
      f"📞 Telefon: {telefon}\n"
      f"🛠️ Usluga: {usluga}\n"
      f"📅 Datum: {datum}\n"
      f"⏰ Termin: {vreme}"
  )
  posalji_u_whatsapp_grupu(poruka_za_grupu)

  return jsonify({"poruka": "Uspešno ste rezervisali termin!"})


@app.route("/recenzije", methods=["GET"])
def recenzije():
  return jsonify(ucitaj_podatke(FAJL_RECENZIJE))


@app.route("/ostavi-recenziju", methods=["POST"])
def ostavi_recenziju():
  podaci = request.get_json()
  ime = podaci.get("ime")
  ocena = podaci.get("ocena")
  komentar = podaci.get("komentar")

  if not all([ime, ocena, komentar]):
    return jsonify({"poruka": "Popunite sva polja za recenziju!"}), 400

  sve_recenzije = ucitaj_podatke(FAJL_RECENZIJE)
  sve_recenzije.insert(
      0, {"ime": ime, "ocena": int(ocena), "komentar": komentar}
  )
  sacuvaj_podatke(FAJL_RECENZIJE, sve_recenzije)

  return jsonify({"poruka": "Hvala na recenziji!"})


if __name__ == "__main__":
  app.run(debug=True)
