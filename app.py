import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
import hashlib
import os

# ================= CONFIG =================
st.set_page_config(page_title="Outil privé – Codes-barres", layout="wide")

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
body, .stApp {
    background-color: white;
    color: #005baa;
}

h1, h2, h3, h4 {
    color: #005baa;
}

label, span, p, div {
    color: #005baa;
}

input, textarea {
    background-color: #f2f2f2 !important;
    color: #005baa !important;
    border-radius: 6px !important;
}

input::placeholder {
    color: #005baa !important;
    opacity: 0.6;
}

div[role="radiogroup"] label {
    color: #005baa !important;
    font-weight: 500;
}

div[data-testid="stVerticalBlock"] > div {
    background: transparent !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ================= FONCTIONS =================
def checksum_ean13(code12):
    total = 0
    for i, c in enumerate(code12):
        total += int(c) if i % 2 == 0 else int(c) * 3
    return (10 - total % 10) % 10

def solve_ean13(code):
    pos = None
    for i, c in enumerate(code):
        if not c.isdigit():
            pos = i
            break
    if pos is None:
        return None
    for n in range(10):
        test = list(code)
        test[pos] = str(n)
        test = "".join(test)
        if checksum_ean13(test[:12]) == int(test[12]):
            return test
    return None

def euro_to_francs(euro):
    return round(euro * 6.55957, 2)

def francs_5_digits(francs):
    return f"{int(round(francs * 100)):05d}"

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# ---------- EAN13 MANQUANT ----------
st.subheader("🔢 Calcul chiffre manquant – EAN13")
ean_input = st.text_input("Code avec chiffre manquant (ex : 3521X4900218)")
if st.button("Calculer le chiffre manquant"):
    result = solve_ean13(ean_input)
    if result:
        st.success(result)
        EAN13(result, writer=ImageWriter()).save("ean13_calc")
        st.image("ean13_calc.png")
    else:
        st.error("Impossible de résoudre ce code")

st.divider()

# ---------- CARTE FIDÉLITÉ ----------
st.subheader("💳 Carte fidélité")

card_code = st.text_input("Code carte fidélité (chiffres uniquement)")
if st.button("Générer la carte fidélité"):
    if card_code.isdigit():
        barcode = Code128(card_code, writer=ImageWriter())
        barcode.save("card_raw", options={
            "write_text": True,
            "font_size": 12,
            "module_height": 120
        })

        img = Image.open("card_raw.png")
        w, h = img.size

        # On garde le bas du code-barres + chiffres
        img = img.crop((0, int(h * 0.55), w, h))
        img = img.resize((w // 2, h // 4), Image.Resampling.LANCZOS)

        img.save("card_final.png")

        st.image("card_final.png")
        st.markdown(
            '<a href="card_final.png" target="_blank">🖨️ Ouvrir l’image pour impression</a>',
            unsafe_allow_html=True
        )
    else:
        st.error("Le code doit contenir uniquement des chiffres")

st.divider()

# ---------- ARTICLES AU POIDS ----------
st.subheader("⚖️ Articles au poids – EAN13")

if "articles" not in st.session_state:
    st.session_state.articles = {}

article_name = st.text_input("Nom de l’article (ex : raisin)")
article_prefix = st.text_input("Préfixe article (7 chiffres)")

if st.button("Enregistrer l’article"):
    if article_prefix.isdigit() and len(article_prefix) == 7:
        st.session_state.articles[article_name] = article_prefix
        st.success("Article enregistré")
    else:
        st.error("Préfixe invalide")

article_selected = st.selectbox(
    "Articles enregistrés",
    [""] + list(st.session_state.articles.keys())
)

if article_selected:
    article_prefix = st.session_state.articles[article_selected]

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
