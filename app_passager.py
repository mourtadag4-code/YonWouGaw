import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import math
import folium
from streamlit_folium import st_folium
from streamlit_geolocation import streamlit_geolocation
import json

st.set_page_config(
    page_title="YonWouGaw - Passager",
    page_icon="🚌",
    layout="wide"
)

# ---------- CONNEXION À FIREBASE ----------
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-credentials.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://yonwougaw-default-rtdb.firebaseio.com/'  # ← À MODIFIER
    })

# ---------- EN-TÊTE ----------
st.title("🚌 YonWouGaw - Passager")
st.caption("Suivez votre TATA en temps réel - Mise à jour automatique de la carte")

# ---------- POSITION DU PASSAGER ----------
st.subheader("📍 Votre position")
location = streamlit_geolocation()

if location and location.get("latitude") is not None:
    passager_lat = float(location["latitude"])
    passager_lon = float(location["longitude"])
    st.success(f"📍 Position : {passager_lat:.6f}, {passager_lon:.6f}")
else:
    passager_lat = 14.7167
    passager_lon = -17.4677
    st.warning("⚠️ Utilisation des coordonnées par défaut. Activez votre GPS pour plus de précision.")

# ---------- RÉCUPÉRATION DE LA LISTE DES BUS ----------
ref = db.reference('bus')
bus_data = ref.get()

if bus_data:
    bus_actifs = {k: v for k, v in bus_data.items() if v.get('active', False)}
    
    if bus_actifs:
        bus_liste = list(bus_actifs.keys())
        bus_choisi = st.selectbox("🚌 Choisissez votre bus :", bus_liste)
        
        if bus_choisi:
            data = bus_actifs[bus_choisi]
            
            # ---------- AFFICHAGE DES INFOS ----------
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🚌 Bus", data.get('nom', bus_choisi))
            with col2:
                st.metric("🟢 Statut", "En ligne" if data.get('active') else "Arrêté")
            with col3:
                st.metric("⏰ Mis à jour", data.get('derniere_mise_a_jour', 'Inconnu'))
            
            # ---------- TEMPS D'ARRIVÉE ----------
            if 'lat' in data and 'lon' in data:
                distance = math.sqrt((data['lat'] - passager_lat)**2 + (data['lon'] - passager_lon)**2) * 111.32
                
                if distance > 0.1:
                    temps_minutes = (distance / 18) * 60
                    st.info(f"⏱️ Arrivée dans environ **{int(temps_minutes)} minutes**")
                else:
                    st.success("🚌 Le bus est arrivé !")
            
            # ---------- CARTE AVEC MAJ AUTO (JavaScript) ----------
            st.subheader("🗺️ Visualisation (mise à jour auto toutes les 3s)")

            # Récupérer l'URL Firebase
            firebase_url = 'https://yonwougaw-default-rtdb.firebaseio.com/'

            # Construire le code HTML/CSS/JavaScript comme une chaîne
            html_code = f"""
            <div id="map-container" style="height:400px; width:100%;"></div>
            <div id="info" style="margin-top:10px; font-size:14px; color:gray;">
                🟢 Mise à jour automatique toutes les 3 secondes
            </div>

            <!-- Font Awesome pour les icônes -->
            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css" />
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

            <style>
            .custom-icon-bus {{
                background: #2196F3;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 10px rgba(33, 150, 243, 0.5);
                border: 2px solid white;
                transition: all 0.1s ease;
            }}
            .custom-icon-passenger {{
                background: #f44336;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 2px 10px rgba(244, 67, 54, 0.5);
                border: 2px solid white;
                transition: all 0.1s ease;
            }}
            </style>

            <script>
                // Initialisation de la carte
                var map = L.map('map-container').setView([{passager_lat}, {passager_lon}], 14);
                
                L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                    maxZoom: 19,
                    attribution: '© OpenStreetMap'
                }}).addTo(map);
                
                // ---------- FONCTION POUR CRÉER LES MARQUEURS ----------
                function createBusIcon(zoomLevel) {{
                    let baseSize = 35;
                    let zoomFactor = Math.max(0.7, Math.min(1.5, zoomLevel / 14));
                    let size = Math.round(baseSize * zoomFactor);
                    let fontSize = Math.round(18 * zoomFactor);
                    
                    return L.divIcon({{
                        className: 'custom-icon-bus',
                        html: `<i class="fa fa-bus" style="font-size:${{fontSize}}px; color:white;"></i>`,
                        iconSize: [size, size],
                        iconAnchor: [size/2, size],
                        popupAnchor: [0, -size]
                    }});
                }}
                
                function createPassengerIcon(zoomLevel) {{
                    let baseSize = 35;
                    let zoomFactor = Math.max(0.7, Math.min(1.5, zoomLevel / 14));
                    let size = Math.round(baseSize * zoomFactor);
                    let fontSize = Math.round(18 * zoomFactor);
                    
                    return L.divIcon({{
                        className: 'custom-icon-passenger',
                        html: `<i class="fa fa-user" style="font-size:${{fontSize}}px; color:white;"></i>`,
                        iconSize: [size, size],
                        iconAnchor: [size/2, size],
                        popupAnchor: [0, -size]
                    }});
                }}
                
                // ---------- CRÉATION DES MARQUEURS ----------
                var busMarker = L.marker([{data['lat']}, {data['lon']}], {{
                    icon: createBusIcon(14)
                }}).addTo(map);
                busMarker.bindPopup('🚌 {data.get('nom', bus_choisi)}');
                
                var passengerMarker = L.marker([{passager_lat}, {passager_lon}], {{
                    icon: createPassengerIcon(14)
                }}).addTo(map);
                passengerMarker.bindPopup('📍 Vous');
                
                // ---------- LIGNE ENTRE LES DEUX ----------
                var line = L.polyline([
                    [{data['lat']}, {data['lon']}],
                    [{passager_lat}, {passager_lon}]
                ], {{color: 'gray', weight: 2, dashArray: '5, 5'}}).addTo(map);
                
                // ---------- MISE À JOUR DES MARQUEURS QUAND LE ZOOM CHANGE ----------
                map.on('zoomend', function() {{
                    var zoom = map.getZoom();
                    busMarker.setIcon(createBusIcon(zoom));
                    passengerMarker.setIcon(createPassengerIcon(zoom));
                }});
                
                // ---------- MISE À JOUR DE LA POSITION DU BUS ----------
                function updateMap() {{
                    fetch('{firebase_url}bus/{bus_choisi}.json')
                        .then(response => response.json())
                        .then(data => {{
                            if (data && data.active) {{
                                const busLat = data.lat;
                                const busLon = data.lon;
                                
                                busMarker.setLatLng([busLat, busLon]);
                                line.setLatLngs([
                                    [busLat, busLon],
                                    [{passager_lat}, {passager_lon}]
                                ]);
                                
                                document.getElementById('info').innerHTML = 
                                    '🟢 Dernière mise à jour : ' + new Date().toLocaleTimeString();
                            }}
                        }})
                        .catch(error => {{
                            console.error('Erreur:', error);
                            document.getElementById('info').innerHTML = '🔴 Erreur de connexion';
                        }});
                }}
                
                setInterval(updateMap, 3000);
                updateMap();
            </script>
            """

            # Afficher le composant HTML
            st.components.v1.html(html_code, height=450)
            
            # Afficher les coordonnées détaillées
            with st.expander("📍 Coordonnées détaillées"):
                st.write(f"**Bus** : {data['lat']:.6f}, {data['lon']:.6f}")
                st.write(f"**Vous** : {passager_lat:.6f}, {passager_lon:.6f}")
                st.write(f"📏 Distance : **{distance * 1000:.0f} mètres**")
            
            # Petit bouton pour forcer une mise à jour manuelle
            if st.button("🔄 Forcer la mise à jour de la carte"):
                st.rerun()
    else:
        st.warning("🚫 Aucun bus actif")
else:
    st.info("📭 Aucun bus enregistré")