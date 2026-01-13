import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO
import hashlib
import base64

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
            st.success("Connecté. Recharge la page si nécessaire.")
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

h1, h2, h3, h4, h5 {
    color: #005baa;
}

label, .stMarkdown {
    color: #005baa;
}

/* Supprime tout effet de "carte" */
div[data-testid="stVerticalBlock"] > div {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    margin: 0 0 16px 0 !important;
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
    for i, c in enumerate(code):
        if not c.isdigit():
            pos = i
            break
    else:
        return None
    for n in range(10):
        test = list(code)
        test[pos] = str(n)
        test = "".join(test)
        if checksum_ean13(test[:12]) == int(test[12]):
            return test
    return None

def euro_to_francs(e):
    return round(e * 6.55957, 2)

def francs_5_digits(f):
    return f"{int(round(f * 100)):05d}"

def open_image_new_tab(img):
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f'<a href="data:image/png;base64,{b64}" target="_blank">🖨️ Ouvrir l’image pour impression</a>'

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# ---------- EAN13 MANQUANT ----------
st.subheader("🔢 Calcul chiffre manquant – EAN13")
ean_input = st.text_input("Code avec chiffre manquant (ex : 3521X4900218)")
if st.button("Calculer"):
    res = solve_ean13(ean_input)
    if res:
        st.success(res)
        EAN13(res, writer=ImageWriter()).save("ean13_calc")
        st.image("ean13_calc.png")
    else:
        st.error("Impossible de résoudre")

# ---------- CARTE FIDÉLITÉ ----------
st.subheader("💳 Carte fidélité")
card_code = st.text_input("Code carte fidélité (chiffres)")
if st.button("Générer carte"):
    if card_code.isdigit():
        code = Code128(card_code, writer=ImageWriter())
        code.save("card", options={
            "write_text": True,
            "font_size": 12,
            "module_height": 120
        })
        img = Image.open("card.png")
        w, h = img.size
        img = img.crop((0, int(h * 0.6), w, h))
        img = img.resize((w // 2, h // 4), Image.Resampling.LANCZOS)
        st.image(img)
        st.markdown(open_image_new_tab(img), unsafe_allow_html=True)
    else:
        st.error("Chiffres uniquement")

# ---------- ARTICLES AU POIDS ----------
st.subheader("⚖️ Article au poids (EAN13)")

if "articles" not in st.session_state:
    st.session_state.articles = {}

name = st.text_input("Nom de l’article (ex : raisin)")
prefix = st.text_input("Préfixe article (7 chiffres)")

if st.button("Enregistrer article"):
    if prefix.isdigit() and len(prefix) == 7:
        st.session_state.articles[name] = prefix
        st.success("Article enregistré")
    else:
        st.error("Préfixe invalide")

article = st.selectbox("Articles enregistrés", [""] + list(st.session_state.articles.keys()))
if article:
    prefix = st.session_state.articles[article]

mode = st.radio("Méthode de prix", ["Prix connu", "Poids × prix/kg"])

if mode == "Prix connu":
    prix = st.number_input("Prix (€)", min_value=0.0, step=0.01)
else:
    poids = st.number_input("Poids (kg)", min_value=0.0, step=0.001)
    prixkg = st.number_input("Prix/kg (€)", min_value=0.0, step=0.01)
    prix = poids * prixkg

if st.button("Générer code article"):
    francs = euro_to_francs(prix)
    base = prefix + francs_5_digits(francs)
    code = base + str(checksum_ean13(base))
    st.success(f"EAN13 : {code}")
    EAN13(code, writer=ImageWriter()).save("ean_poids")
    st.image("ean_poids.png")

# ---------- LOGOUT ----------
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.stop()
