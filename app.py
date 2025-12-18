import requests
import toml
import streamlit as st

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm

# --- Génération PDF élégante ---
def generate_pdf(title, content):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    # Titre centré
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width / 2, height - 2*cm, title)

    # Ligne de séparation
    c.setLineWidth(1)
    c.line(2*cm, height - 2.3*cm, width - 2*cm, height - 2.3*cm)

    # Corps du texte
    c.setFont("Helvetica", 11)
    y = height - 3*cm
    for line in content.split("\n"):
        if line.strip() == "":
            y -= 10
            continue
        if y < 2*cm:
            c.showPage()
            c.setFont("Helvetica", 11)
            y = height - 3*cm
        c.drawString(2*cm, y, line)
        y -= 15

    # Pied de page
    c.setFont("Helvetica-Oblique", 9)
    c.drawCentredString(width / 2, 1.5*cm, "Document généré par IA - Générateur CV & Lettre")

    c.save()
    buffer.seek(0)
    return buffer

# --- Config Streamlit ---
st.set_page_config(page_title="Générateur CV + Lettre", layout="centered")
st.title("🧠 Générateur IA de CV + Lettre de motivation")

# --- Fonction d'appel à Ollama ---
def call_ollama(prompt):
    config = toml.load("config.toml")
    if config["ollama"]["enabled"]:
        endpoint = config["ollama"]["endpoint"]
        model = config["ollama"]["model"]
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        r = requests.post(endpoint, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "")
    else:
        return "⚠️ Ollama n'est pas activé dans config.toml"

# --- Init session_state ---
for key in ["cv_text", "lettre_text", "cv_pdf", "lettre_pdf"]:
    if key not in st.session_state:
        st.session_state[key] = "" if "text" in key else None

# --- Formulaire utilisateur ---
nom = st.text_input("Ton nom complet")
poste = st.text_input("Poste visé")
exp = st.text_area("Tes expériences")
skills = st.text_area("Tes compétences")
telephone = st.text_input("Téléphone")
email = st.text_input("Email")
linkedin = st.text_input("LinkedIn")
ville = st.text_input("Ville")

bouton = st.button("🚀 Générer CV + Lettre")

# --- Génération ---
if bouton and nom and poste:
    prompt = f"""
Tu es un assistant RH. Génère un CV et une lettre de motivation en français.

⚠️ Règles strictes :
- Utilise uniquement les informations fournies ci-dessous.
- N’invente pas d’adresses, d’entreprises, de dates ou de diplômes fictifs.
- Si une date n’est pas fournie, ne mets rien à la place.
- La lettre de motivation doit être rédigée en français uniquement.
- Le style doit être professionnel, clair et adapté à une candidature.

Informations fournies :
Nom : {nom}
Poste visé : {poste}
Expériences : {exp}
Compétences : {skills}
Contact : Téléphone {telephone}, Email {email}, LinkedIn {linkedin}
Ville : {ville}

Le CV doit contenir :
- Un titre professionnel clair
- Une section Profil (3 phrases maximum, mettant en avant mes points forts concrets)
- Une section Expériences détaillée (responsabilités, réalisations, outils utilisés, sans dates fictives)
- Une section Compétences techniques (liste claire et corrigée)
- Une section Formation (si non précisée, indiquer Bac+2 Informatique)
- Une mise en page lisible avec puces et sous-titres

La lettre de motivation doit :
- Être adressée à “Madame, Monsieur”
- Mettre en avant mes compétences en supervision, Zabbix et Grafana
- Souligner mon expérience et ma motivation
- Reprendre exactement les informations de contact fournies (téléphone, email, LinkedIn)
- Être rédigée dans un style professionnel, fluide et impactant

Réponds avec deux sections claires :
SECTION_CV:
[Ton CV ici]

SECTION_LETTRE:
[Ton texte de lettre ici]
"""

    resultat = call_ollama(prompt)

    # Séparer CV et Lettre
    cv, lettre = "", ""
    if "SECTION_CV:" in resultat and "SECTION_LETTRE:" in resultat:
        cv = resultat.split("SECTION_CV:")[1].split("SECTION_LETTRE:")[0].strip()
        lettre = resultat.split("SECTION_LETTRE:")[1].strip()
    else:
        cv = resultat
        lettre = "⚠️ La lettre n’a pas été générée correctement."

    # Persistance
    st.session_state.cv_text = cv
    st.session_state.lettre_text = lettre
    st.session_state.cv_pdf = generate_pdf("CV - " + nom, cv)
    st.session_state.lettre_pdf = generate_pdf("Lettre de motivation - " + nom, lettre)

# --- Affichage persistant ---
if st.session_state.cv_text:
    st.subheader("📄 CV généré")
    st.markdown(st.session_state.cv_text)

if st.session_state.lettre_text:
    st.subheader("✉️ Lettre de motivation générée")
    st.markdown(st.session_state.lettre_text)

# --- Download buttons ---
if st.session_state.cv_pdf is not None:
    st.download_button(
        "📥 Télécharger le CV en PDF",
        data=st.session_state.cv_pdf.getvalue(),
        file_name="cv.pdf",
        mime="application/pdf",
        key="dl_cv"
    )

if st.session_state.lettre_pdf is not None:
    st.download_button(
        "📥 Télécharger la lettre en PDF",
        data=st.session_state.lettre_pdf.getvalue(),
        file_name="lettre_motivation.pdf",
        mime="application/pdf",
        key="dl_lettre"
    )
