import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
import hashlib

# ================= CONFIG =================
st.set_page_config(
    page_title="Outil privé – Codes-barres",
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
.section { background: #ffffff; padding: 20px; border-radius: 14px; box-shadow: 0 4px 14px rgba(0,0,0,0.1); color: #005baa; }
.columns-container { display: flex; flex-wrap: wrap; gap: 20px; }
.column { flex: 1; min-width: 300px; }
.card-container { display: flex; justify-content: center; margin-top: 15px; }
.card {
    width: 340px;
    height: 215px;
    background: #ffffff;
    border: 3px solid red;
    border-radius: 16px;
    padding: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.stTextInput>div>div>input { color: #005baa; }
/* Impression carte bancaire */
@media print {
    body * { visibility: hidden; }
    .print-card, .print-card * { visibility: visible; }
    .print-card { position: absolute; top: 0; left: 0; width: 85.6mm; height: 54mm; margin: 0; padding: 0; }
}
</style>
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
st.markdown('<div class="columns-container">', unsafe_allow_html=True)

# -------- COLONNE GAUCHE : EAN-13 -----------
st.markdown('<div class="column">', unsafe_allow_html=True)
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("🔢 Calcul du chiffre manquant – EAN-13")
ean13_input = st.text_input("Code EAN-13 avec chiffre manquant (ex : 3521X4900218)", max_chars=13, key="ean13")

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
st.markdown('</div>', unsafe_allow_html=True)

# -------- COLONNE DROITE : CARTE FIDÉLITÉ -----------
st.markdown('<div class="column">', unsafe_allow_html=True)
st.markdown('<div class="section">', unsafe_allow_html=True)
st.subheader("💳 Carte fidélité – Code128")

card_code = st.text_input(
    "Code carte fidélité – chiffres libres (19 ou plus)",
    placeholder="Ex : 0371234567890123456", key="card_code"
)

if st.button("Générer la carte"):
    if not card_code or not card_code.isdigit():
        st.error("Veuillez entrer uniquement des chiffres")
    else:
        # Génération code-barres Code128
        code128 = Code128(
            card_code,
            writer=ImageWriter()
        )
        # Options : texte complet visible, pas de checksum, largeur ajustée
        code128.save("code128_card", options={
            "write_text": True,        # texte complet visible
            "add_checksum": False,     # aucun caractère supplémentaire
            "background": "white",
            "foreground": "black",
            "module_width": 0.25,     # largeur ajustée pour que tous les chiffres rentrent
            "module_height": 50,      # hauteur ~1,5-2 cm
            "font_size": 12            # texte lisible sous le code-barres
        })
        barcode_img = Image.open("code128_card.png")

        st.markdown('<div class="card-container">', unsafe_allow_html=True)
        st.markdown('<div class="card print-card">', unsafe_allow_html=True)
        st.image(barcode_img, width=280)
        st.markdown('</div></div>', unsafe_allow_html=True)

        # Télécharger pour impression
        st.download_button(
            label="📥 Télécharger la carte pour impression",
            data=open("code128_card.png", "rb").read(),
            file_name="carte_fidelite.png",
            mime="image/png"
        )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ================= LOGOUT =================
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.stop()  # stable sur Streamlit Cloud
