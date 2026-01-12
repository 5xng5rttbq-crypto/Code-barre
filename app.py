import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
from io import BytesIO
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
.stTextInput>div>div>input { color: #005baa; }
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
    "Code carte fidélité – chiffres libres",
    placeholder="Ex : 0371234567890123456", key="card_code"
)

if st.button("Générer la carte"):
    if not card_code or not card_code.isdigit():
        st.error("Veuillez entrer uniquement des chiffres")
    else:
        # Génération code-barres Code128
        code128 = Code128(card_code, writer=ImageWriter())
        code128.save("code128_card", options={
            "write_text": True,
            "add_checksum": False,
            "background": "white",
            "foreground": "black",
            "module_width": 0.35,
            "module_height": 120,   
            "font_size": 12   # réduit la taille des chiffres
        })

        barcode_img = Image.open("code128_card.png")

        # ROGNER LE HAUT : garder uniquement la partie basse avec chiffres
        width, height = barcode_img.size
        crop_top = int(height * 0.6)  # garder les 40% du bas
        cropped_img = barcode_img.crop((0, crop_top, width, height))

        # REDUIRE DE 2× pour aperçu compact
        new_width = width // 2
        new_height = (height - crop_top) // 2
        cropped_img_small = cropped_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        st.image(cropped_img_small)

        # Télécharger pour impression
        output_buffer = BytesIO()
        cropped_img_small.save(output_buffer, format="PNG")
        st.download_button(
            label="📥 Télécharger la carte pour impression",
            data=output_buffer.getvalue(),
            file_name="carte_fidelite.png",
            mime="image/png"
        )

st.markdown('</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ================= LOGOUT =================
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.stop()
