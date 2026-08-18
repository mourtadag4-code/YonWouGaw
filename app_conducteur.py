import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime
import pandas as pd
import time

st.set_page_config(
    page_title="YonWouGaw - Conducteur",
    page_icon="🚌",
    layout="centered"
)

# ---------- CONNEXION À FIREBASE ----------
import json

# ---------- CONNEXION À FIREBASE ----------
if not firebase_admin._apps:
    # Lire depuis les secrets Streamlit (si disponible)
    if 'firebase_type' in st.secrets:
        # Reconstruire le dictionnaire des identifiants à partir des secrets
        cred_dict = {
            "type": st.secrets["firebase_type"],
            "project_id": st.secrets["firebase_project_id"],
            "private_key_id": st.secrets["firebase_private_key_id"],
            "private_key": st.secrets["firebase_private_key"],
            "client_email": st.secrets["firebase_client_email"],
            "client_id": st.secrets["firebase_client_id"],
            "auth_uri": st.secrets["firebase_auth_uri"],
            "token_uri": st.secrets["firebase_token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase_auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase_client_x509_cert_url"]
        }
        cred = credentials.Certificate(cred_dict)
    else:
        # En local, lire le fichier
        cred = credentials.Certificate("firebase-credentials.json")
    
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://yonwougaw-default-rtdb.firebaseio.com/'
    })

# ---------- EN-TÊTE ----------
st.title("🚌 YonWouGaw - Conducteur")
st.caption("Partagez votre position en temps réel")

# ---------- IDENTIFIANT DU BUS ----------
bus_id = st.text_input("🚏 Identifiant de votre bus", value="TATA-001")

# ---------- GÉOLOCALISATION AUTOMATIQUE ----------
st.subheader("📍 Votre position GPS")

# Utiliser streamlit-geolocation pour récupérer la position automatiquement
from streamlit_geolocation import streamlit_geolocation
location = streamlit_geolocation()

if location and location.get("latitude") is not None:
    lat = float(location["latitude"])
    lon = float(location["longitude"])
    st.success(f"📍 Position automatique : {lat:.6f}, {lon:.6f}")
else:
    # Fallback : coordonnées par défaut si GPS non disponible
    lat = 14.7167
    lon = -17.4677
    st.warning("⚠️ En attente du GPS... Utilisation des coordonnées par défaut")

# Afficher les coordonnées (lecture seule)
col1, col2 = st.columns(2)
with col1:
    st.text_input("Latitude", value=f"{lat:.6f}", disabled=True, key="lat_display")
with col2:
    st.text_input("Longitude", value=f"{lon:.6f}", disabled=True, key="lon_display")

# ---------- DÉMARRER / ARRÊTER ----------
col_start, col_stop = st.columns(2)

if 'partage_actif' not in st.session_state:
    st.session_state.partage_actif = False

with col_start:
    if st.button("▶️ Démarrer", use_container_width=True):
        st.session_state.partage_actif = True
        st.success(f"✅ Bus {bus_id} visible !")

with col_stop:
    if st.button("⏹️ Arrêter", use_container_width=True):
        st.session_state.partage_actif = False
        ref = db.reference(f'bus/{bus_id}')
        ref.update({'active': False})
        st.warning(f"⏹️ Bus {bus_id} arrêté")

# ---------- ENVOI AUTOMATIQUE (SANS RECHARGEMENT) ----------
if st.session_state.partage_actif:
    # Envoyer la position à Firebase
    ref = db.reference(f'bus/{bus_id}')
    ref.set({
        'nom': bus_id,
        'lat': lat,
        'lon': lon,
        'active': True,
        'derniere_mise_a_jour': datetime.now().strftime('%H:%M:%S')
    })
    
    st.info(f"🔄 Position envoyée à {datetime.now().strftime('%H:%M:%S')}")
    
    # Afficher la carte
    st.subheader("📍 Votre position sur la carte")
    map_df = pd.DataFrame({'lat': [lat], 'lon': [lon]})
    st.map(map_df, zoom=14)
    
    # Afficher un compteur de temps écoulé
    placeholder = st.empty()
    for i in range(3, 0, -1):
        placeholder.info(f"⏳ Prochaine mise à jour dans {i} secondes...")
        time.sleep(1)
    
    # Rafraîchir la page pour une nouvelle position
    st.rerun()
else:
    st.info("⏸️ En attente. Cliquez sur 'Démarrer' pour partager votre position")
    st.caption("💡 Assurez-vous d'avoir autorisé l'accès à votre position GPS")