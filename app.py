import streamlit as st
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image
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
if "auth" not in st.session_state:
    st.session_state.auth = False

def check_login(user, pwd):
    return user == USERNAME and hashlib.sha256(pwd.encode()).hexdigest() == PASSWORD_HASH

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
body, .stApp { background-color: #ffffff; color: #005baa; }

.logo-top-left { position: fixed; top: 10px; left: 10px; z-index: 9999; }

.section {
    background: #ffffff;
    padding: 20px;
    border-radius: 14px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.1);
    margin-bottom: 30px;
    color: #005baa;
}

.card-container { display: flex; justify-content: center; margin-top: 15px; }

.card {
    width: 340px;
    height: 215px;
    background: #ffffff;
    border: 3px solid red;  /* contour rouge */
    border-radius: 16px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.stTextInput>div>div>input { color: #005baa; }

/* Impression en taille carte bancaire */
@media print {
    body * { visibility: hidden; }
    .print-card, .print-card * { visibility: visible; }
    .print-card { position: absolute; top: 0; left: 0; width: 85.6mm; height: 54mm; margin: 0; padding: 0; }
}
</style>
""", unsafe_allow_html=True)

# ================= LOGO =================
st.markdown("""
<div class="logo-top-left">
    <img src="logo_carrefour.PNG" width="120">
</div>
""", unsafe_allow_html=True)

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# -------- SECTION 2 : CARTE FIDÉLITÉ -----------
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("💳 Carte fidélité avec EAN-128")

ean128_input = st.text_input(
    "Code EAN-128 (GS1-128) à afficher sur la carte",
    placeholder="Ex : ]C10103712345678901"
)

if st.button("Générer la carte"):
    if not ean128_input:
        st.error("Veuillez entrer un code EAN-128")
    else:
        # Génération du code-barres EAN-128
        code128 = Code128(
            ean128_input,
            writer=ImageWriter()
        )
        filename = code128.save("ean128_card", options={
            "write_text": False,
            "background": "white",
            "foreground": "black",
            "module_width": 0.2,
            "module_height": 40
        })

        # Ouvrir l'image générée
        barcode_img = Image.open("ean128_card.png")

        # Affichage carte dans Streamlit
        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown('<div class="card print-card">', unsafe_allow_html=True)
        st.image(barcode_img, width=260)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Bouton d'impression
        st.markdown("""
        <button onclick="window.print()" style="
            background-color:#005baa;color:white;padding:10px 20px;
            border:none;border-radius:8px;margin-top:10px;cursor:pointer;">
            🖨️ Imprimer la carte
        </button>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ================= LOGOUT =================
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.experimental_rerun()
