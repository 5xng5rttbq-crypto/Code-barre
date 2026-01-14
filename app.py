import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
import hashlib
import json
import os

# ================= CONFIG =================
st.set_page_config(page_title="Outil privé – Codes-barres", layout="wide")

ARTICLES_FILE = "articles.json"

# ================= AUTH =================
USERNAME = "11"
PASSWORD_HASH = hashlib.sha256("11".encode()).hexdigest()

if "auth" not in st.session_state:
    st.session_state.auth = False

def check_login(u, p):
    return u == USERNAME and hashlib.sha256(p.encode()).hexdigest() == PASSWORD_HASH

if not st.session_state.auth:
    st.title("🔐 Accès privé")
    u = st.text_input("Nom d’utilisateur")
    p = st.text_input("Mot de passe", type="password")
    if st.button("Connexion"):
        if check_login(u, p):
            st.session_state.auth = True
            st.stop()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# ================= STYLE =================
st.markdown("""
<style>
body, .stApp { background-color: white; color: #005baa; }
h1, h2, h3, h4 { color: #005baa; }
label, span, p, div { color: #005baa; }
input, textarea {
    background-color: #f2f2f2 !important;
    color: #005baa !important;
    border-radius: 6px !important;
}
input::placeholder { color: #005baa !important; opacity: 0.6; }
div[role="radiogroup"] label { color: #005baa !important; font-weight: 500; }
div[data-testid="stVerticalBlock"] > div {
    background: transparent !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ================= UTILITAIRES =================
def checksum_ean13(code12):
    total = 0
    for i, c in enumerate(code12):
        total += int(c) if i % 2 == 0 else int(c) * 3
    return (10 - total % 10) % 10

def euro_to_francs(e):
    return round(e * 6.55957, 2)

def francs_5_digits(f):
    return f"{int(round(f * 100)):05d}"

# ================= ARTICLES (PERSISTANTS) =================
def load_articles():
    if os.path.exists(ARTICLES_FILE):
        with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_articles(data):
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

articles = load_articles()

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# ---------- CARTE FIDÉLITÉ ----------
# ---------- CARTE FIDÉLITÉ ----------
st.subheader("💳 Carte fidélité")

card_code = st.text_input("Code carte fidélité (chiffres uniquement)")

if st.button("Générer la carte fidélité"):
    if card_code.isdigit():
        # Génération du code-barres avec chiffres plus petits
        barcode = Code128(card_code, writer=ImageWriter())
        barcode.save("card_raw", options={
            "write_text": True,
            "font_size": 9,          # 🔽 chiffres plus petits
            "text_distance": 4,      # 🔽 rapproche les chiffres du code-barres
            "module_height": 120,
            "quiet_zone": 10
        })

        img = Image.open("card_raw.png")
        w, h = img.size

        # Rognage doux : garder tout le bas du code-barres et chiffres
        left = int(w * 0.02)
        right = int(w * 0.98)
        top = int(h * 0.55)      # on garde plus de haut pour inclure chiffres
        bottom = h

        img = img.crop((left, top, right, bottom))
        img = img.resize(
            (int(img.width * 0.6), int(img.height * 0.6)),
            Image.Resampling.LANCZOS
        )

        img.save("card_final.png")

        # Affichage + ouverture dans un nouvel onglet pour impression
        st.image("card_final.png")
        st.markdown(
            '<a href="card_final.png" target="_blank">🖨️ Ouvrir l’image pour impression</a>',
            unsafe_allow_html=True
        )
    else:
        st.error("Le code doit contenir uniquement des chiffres")

# ---------- ARTICLES AU POIDS ----------
st.subheader("⚖️ Articles au poids – EAN13")

article_name = st.text_input("Nom de l’article (ex : raisin)")
article_prefix = st.text_input("Préfixe article (7 chiffres)")

if st.button("Enregistrer / Mettre à jour l’article"):
    if article_prefix.isdigit() and len(article_prefix) == 7:
        articles[article_name] = article_prefix
        save_articles(articles)
        st.success("Article enregistré (ou remplacé)")
    else:
        st.error("Le préfixe doit contenir exactement 7 chiffres")

article_selected = st.selectbox(
    "Articles enregistrés",
    [""] + sorted(articles.keys())
)

if article_selected:
    article_prefix = articles[article_selected]

mode = st.radio(
    "Méthode de calcul du prix",
    ["Prix connu", "Poids × prix au kilo"]
)

if mode == "Prix connu":
    price = st.number_input("Prix total (€)", min_value=0.0, step=0.01)
else:
    weight = st.number_input("Poids (kg)", min_value=0.0, step=0.001)
    price_kg = st.number_input("Prix au kilo (€)", min_value=0.0, step=0.01)
    price = weight * price_kg

if st.button("Générer le code article au poids"):
    if article_prefix and price > 0:
        francs = euro_to_francs(price)
        base_code = article_prefix + francs_5_digits(francs)
        ean13 = base_code + str(checksum_ean13(base_code))

        st.success(f"Code EAN13 : {ean13}")
        EAN13(ean13, writer=ImageWriter()).save("ean_poids")
        st.image("ean_poids.png")
    else:
        st.error("Informations incomplètes")

st.divider()

# ---------- LOGOUT ----------
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.stop()
