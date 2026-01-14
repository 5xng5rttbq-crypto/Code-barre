import streamlit as st
from barcode import EAN13, Code128
from barcode.writer import ImageWriter
from PIL import Image
import hashlib
import io
import json
import requests
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
            st.stop()
        else:
            st.error("Identifiants incorrects")
    st.stop()

# ================= STYLE =================
st.markdown("""
<style>
body, .stApp { background-color: white; color: #005baa; }
label, span, p, div, .stNumberInput, .stTextInput, .stTextArea, div[role="radiogroup"] label {
    color: #005baa !important; font-weight: 500;
}
input, textarea { background-color: #f2f2f2 !important; color: #005baa !important; border-radius:6px !important; }
input::placeholder { color:#005baa !important; opacity:0.6; }
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

def euro_to_francs(e):
    return round(e * 6.55957, 2)

def francs_5_digits(f):
    return f"{int(round(f * 100)):05d}"

# ================= ARTICLES GITHUB =================
# Modifier ces infos
GITHUB_USER = "TON_UTILISATEUR"
GITHUB_REPO = "TON_DEPOT"
GITHUB_FILE = "articles.json"
GITHUB_BRANCH = "main"
TOKEN = st.secrets["GITHUB_TOKEN"]

def github_get_articles():
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}?ref={GITHUB_BRANCH}"
    r = requests.get(url)
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"])
        return json.loads(content), data["sha"]
    return {}, None

def github_save_articles(data, sha):
    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    content = base64.b64encode(json.dumps(data, indent=2, ensure_ascii=False).encode()).decode()
    payload = {
        "message": "Mise à jour articles via Streamlit",
        "content": content,
        "branch": GITHUB_BRANCH,
        "sha": sha
    }
    headers = {"Authorization": f"token {TOKEN}"}
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code == 200

articles, current_sha = github_get_articles()

# ================= PAGE =================
st.title("🛒 Outil privé – Codes-barres")

# ----- Chiffre manquant EAN13 -----
st.subheader("🔢 Calcul chiffre manquant – EAN13")
ean_input = st.text_input("Code avec chiffre manquant (ex: 3521X4900218)")
if st.button("Calculer le chiffre manquant"):
    result = solve_ean13(ean_input)
    if result:
        st.success(f"Code complet : {result}")
        EAN13(result, writer=ImageWriter()).save("ean13_calc")
        st.image("ean13_calc.png")
    else:
        st.error("Impossible de résoudre ce code")

st.divider()

# ----- Carte fidélité -----
st.subheader("💳 Carte fidélité")
card_code = st.text_input("Code carte fidélité (chiffres uniquement)")

if st.button("Générer la carte fidélité"):
    if card_code.isdigit():
        barcode = Code128(card_code, writer=ImageWriter())
        buffer = io.BytesIO()
        barcode.write(buffer, {"write_text": True, "font_size": 7, "text_distance": 3, "module_height": 120})
        buffer.seek(0)
        img = Image.open(buffer)
        w,h = img.size
        left = int(w*0.02); right=int(w*0.98); top=int(h*0.55); bottom=h
        img = img.crop((left,top,right,bottom))
        img = img.resize((int(img.width*0.6), int(img.height*0.6)))
        st.image(img)
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes = img_bytes.getvalue()
        st.markdown("<small>Pour imprimer : glisser l'image sur la barre d'adresse ou clic droit → ouvrir dans un nouvel onglet.</small>", unsafe_allow_html=True)
        st.download_button("💾 Enregistrer l'image", img_bytes, file_name="carte_fidelite.png", mime="image/png")
    else:
        st.error("Le code doit contenir uniquement des chiffres")

st.divider()

# ----- Articles au poids -----
st.subheader("⚖️ Articles au poids – EAN13")
article_name = st.text_input("Nom de l’article (ex: raisin)")
article_prefix = st.text_input("Préfixe article (7 chiffres)")

if st.button("Enregistrer / Mettre à jour l’article"):
    if article_prefix.isdigit() and len(article_prefix)==7:
        articles[article_name] = article_prefix
        # Sauvegarde permanente GitHub
        if github_save_articles(articles, current_sha):
            st.success("Article enregistré (ou remplacé) de manière permanente")
            # Recharger sha pour prochaines modifications
            _, current_sha = github_get_articles()
        else:
            st.error("Erreur lors de la sauvegarde sur GitHub")
    else:
        st.error("Le préfixe doit contenir exactement 7 chiffres")

article_selected = st.selectbox("Articles enregistrés", [""] + sorted(articles.keys()))
if article_selected:
    article_prefix = articles[article_selected]

mode = st.radio("Méthode de calcul du prix", ["Prix connu", "Poids × prix au kilo"])
if mode=="Prix connu":
    price = st.number_input("Prix total (€)", min_value=0.0, step=0.01)
else:
    weight = st.number_input("Poids (kg)", min_value=0.0, step=0.001)
    price_kg = st.number_input("Prix au kilo (€)", min_value=0.0, step=0.01)
    price = weight*price_kg

if st.button("Générer le code article au poids"):
    if article_prefix and price>0:
        francs = euro_to_francs(price)
        base_code = article_prefix + francs_5_digits(francs)
        ean13 = base_code + str(checksum_ean13(base_code))
        st.success(f"Code EAN13 : {ean13}")
        EAN13(ean13, writer=ImageWriter()).save("ean_poids")
        st.image("ean_poids.png")
    else:
        st.error("Informations incomplètes")

st.divider()

# ----- Logout -----
if st.button("Se déconnecter"):
    st.session_state.auth = False
    st.stop()
