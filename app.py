import streamlit as st
from barcode import EAN13
from barcode.writer import ImageWriter
import re
from PIL import Image
import hashlib

# ---------------- CONFIG PAGE ----------------
st.set_page_config(
    page_title="Carte Fidélité Carrefour – Accès privé",
    page_icon="🔒",
    layout="centered"
)

# ---------------- IDENTIFIANTS ----------------
USERNAME = "11"
PASSWORD_HASH = hashlib.sha256(
    "5.1178.58.1289.589".encode()
).hexdigest()

# ---------------- AUTHENTIFICATION ----------------
def check_login(username, password):
    return (
        username == USERNAME and
        hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH
    )

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔐 Accès privé")

    username = st.text_input("Nom d’utilisateur")
    password = st.text_input("Mot de passe", type="password")

    if st.button("Se connecter"):
        if check_login(username, password):
            st.session_state.authenticated = True
            st.experimental_rerun()
        else:
            st.error("Identifiants incorrects")

    st.stop()  # ⛔ BLOQUE TOUT LE RESTE

# ---------------- STYLE ----------------
st.markdown("""
<style>
.card {
    width: 340px;
    height: 215px;
    background: linear-gradient(135deg, #005baa, #003b7a);
    border-radius: 16px;
    padding: 16px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.25);
    color: white;
    position: relative;
}
.barcode {
    background: white;
    padding: 10px;
    border-radius: 8px;
    margin-top: 20px;
}
.footer {
    position: absolute;
    bottom: 12px;
    font-size: 10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- LOGIQUE EAN13 ----------------
def calcul_checksum_ean13(code12):
    total = 0
    for i, c in enumerate(code12):
        total += int(c) if i % 2 == 0 else int(c) * 3
    return (10 - (total % 10)) % 10

def trouver_chiffre_manquant(code):
    for i, c in enumerate(code):
        if not c.isdigit():
            pos = i
            break
    else:
        return []

    solutions = []
    for n in range(10):
        test = list(code)
        test[pos] = str(n)
        test = "".join(test)
        if len(test) == 13:
            if calcul_checksum_ean13(test[:12]) == int(test[12]):
                solutions.append(n)
    return solutions

# ---------------- APPLICATION ----------------
st.title("🛒 Générateur de carte fidélité Carrefour")

code = st.text_input("Code-barres EAN-13 (ex : 3521X4900218)", max_chars=13)

if st.button("Générer la carte"):
    solutions = trouver_chiffre_manquant(code)

    if not solutions:
        st.error("Code invalide")
    else:
        chiffre = solutions[0]
        code_complet = code.replace(
            re.search(r"\D", code).group(),
            str(chiffre),
            1
        )

        ean = EAN13(code_complet, writer=ImageWriter())
        ean.save("barcode")

        st.success(f"Code valide : {code_complet}")

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image("carrefour_logo.png", width=90)
        st.markdown("""
        <div class="barcode">
            <img src="barcode.png" width="260">
        </div>
        <div class="footer">
            Usage interne – Accès restreint
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if st.button("Se déconnecter"):
    st.session_state.authenticated = False
    st.experimental_rerun()
