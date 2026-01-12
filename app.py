import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
import re
from PIL import Image
import hashlib

# ================= CONFIG PAGE =================
st.set_page_config(
    page_title="Outil privé – Codes-barres Carrefour",
    page_icon="🔒",
    layout="wide"  # plus d'espace horizontal pour logo
)

# ================= AUTH =================
USERNAME = "11"
PASSWORD_HASH = hashlib.sha256(
    "5.1178.58.1289.589".encode()
).hexdigest()

def check_login(user, pwd):
    return (
        user == USERNAME and
        hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH
    )

if "auth" not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 Accès privé")

    u = st.text_input("Nom d’utilisateur")
    p = st.text_input("Mot de passe", type="password")

    if st.button("Connexion"):
        if check_login(u, p):
            st.session_state.auth = True
            st.experimental_rerun()
        else:
            st.error("Identifiants incorrects")

    st.stop()

# ================= STYLE =================
st.markdown("""
<style>
/* Page blanche */
body, .stApp {
    background-color: #ffffff;
}

/* Logo en haut à gauche */
.logo-top-left {
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 9999;
}

/* Section blanche avec ombre */
.section {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    margin-bottom: 30px;
}

/* Carte fidélité */
.card {
    width: 340px;
    height: 215px;
    background: linear-gradient(135deg, #005baa, #003b7a);
    border-radius: 16px;
    padding: 16px;
    color: white;
    box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}

.barcode-box {
    background: white;
    padding: 10px;
    border-radius: 8px;
    margin-top: 25px;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGO EN HAUT =================
st.markdown("""
<div class="logo-top-left">
    <img src="carrefour_logo.png" width="120">
</div>
""", unsafe_allow_html=True)

# ================= LOGIQUE EAN13 =================
def checksum_ean13(code12):
    total = 0
    for i, c in enumerate(code12):
        total += int(c) if i % 2 == 0 else int(c) * 3
    return (10 - (total % 10)) % 10

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
        if len(test) == 13:
            if checksum_ean13(test[:12]) == int(test[12]):
                return test
    return None

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# ----------- SECTION 1 : EAN13 -----------
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🔢 Calcul du chiffre manquant – EAN-13")

ean13_input = st.text_input(
    "Code EAN-13 avec chiffre manquant (ex : 3521X4900218)",
    max_chars=13
)

if st.button("Calculer le code EAN-13"):
    result = solve_ean13(ean13_input)

    if result:
        st.success(f"Code EAN-13 valide : {result}")
        ean = EAN13(result, writer=ImageWriter())
        ean.save("ean13_result")
        st.image("ean13_result.png")
    else:
        st.error("Code invalide ou impossible à résoudre")

st.markdown('</div>', unsafe_allow_html=True)

# ----------- SECTION 2 : CARTE FIDÉLITÉ -----------
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("💳 Génération carte de fidélité (EAN-128)")

ean128_input = st.text_input(
    "Code EAN-128 (GS1-128) à afficher sur la carte",
    placeholder="Ex : ]C10103712345678901"
)

if st.button("Générer la carte"):
    if not ean128_input:
        st.error("Veuillez entrer un code EAN-128")
    else:
        code128 = Code128(ean128_input, writer=ImageWriter())
        code128.save("ean128_card")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image("carrefour_logo.png", width=90)
        st.markdown("""
        <div class="barcode-box">
            <img src="ean128_card.png" width="260">
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.info("🖨️ Impression : échelle 100 % – format carte bancaire")

st.markdown('</div>', unsafe_allow_html=True)

# ================= LOGOUT =================
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.experimental_rerun()
