import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image, ImageOps
import hashlib

# ================= CONFIG =================
st.set_page_config(
    page_title="Outil privé – Codes-barres Carrefour",
    page_icon="🔒",
    layout="wide"
)

# ================= AUTH =================
USERNAME = "11"
PASSWORD_HASH = hashlib.sha256("5.1178.58.1289.589".encode()).hexdigest()

def check_login(user, pwd):
    return user == USERNAME and hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH

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
body, .stApp {
    background-color: #ffffff;
    color: #005baa;
}

.logo-top-left {
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 9999;
}

.section {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    margin-bottom: 30px;
    color: #005baa;
}

.card-container {
    display: flex;
    justify-content: center;
    margin-top: 15px;
}

.card {
    width: 340px;
    height: 215px;
    background: #ffffff;
    border: 3px solid red; /* contour rouge */
    border-radius: 16px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.barcode-box {
    background: white;
    padding: 10px;
    border-radius: 8px;
}

.stTextInput>div>div>input {
    color: #005baa;
}

button.css-1emrehy.edgvbvh3 {  /* bouton bleu */
    background-color: #005baa !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ================= LOGO =================
st.markdown("""
<div class="logo-top-left">
    <img src="logo_carrefour.PNG" width="120">
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
        if len(test) == 13 and checksum_ean13(test[:12]) == int(test[12]):
            return test
    return None

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# --------- SECTION 1 : EAN-13 -----------
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🔢 Calcul du chiffre manquant – EAN-13")
ean13_input = st.text_input("Code EAN-13 avec chiffre manquant (ex : 3521X4900218)", max_chars=13)

if st.button("Calculer le code EAN-13"):
    result = solve_ean13(ean13_input)
    if result:
        st.success(f"Code EAN-13 valide : {result}")
        ean = EAN13(result, writer=ImageWriter())
        ean.save("ean13_result", options={"write_text": True, "background": "white", "foreground": "black"})
        st.image("ean13_result.png")
    else:
        st.error("Code invalide ou impossible à résoudre")
st.markdown('</div>', unsafe_allow_html=True)

# --------- SECTION 2 : CARTE FIDÉLITÉ -----------
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("💳 Génération carte de fidélité (EAN-128)")

ean128_input = st.text_input("Code EAN-128 (GS1-128) à afficher sur la carte", placeholder="Ex : ]C10103712345678901")

if st.button("Générer la carte"):
    if not ean128_input:
        st.error("Veuillez entrer un code EAN-128")
    else:
        # Génération du code-barres EAN-128
        code128 = Code128(ean128_input, writer=ImageWriter())
        filename = code128.save("ean128_card", options={
            "write_text": False,
            "background": "white",
            "foreground": "black",
            "module_width": 0.2,
            "module_height": 40
        })

        # Ouvrir et centrer le code-barres dans une carte blanche avec contour rouge
        barcode_img = Image.open("ean128_card.png")
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.image(barcode_img, width=260)
        st.markdown('</div></div>', unsafe_allow_html=True)

        st.info("🖨️ Impression : échelle 100 % – format carte bancaire")
st.markdown('</div>', unsafe_allow_html=True)

# ================= LOGOUT =================
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.experimental_rerun()
