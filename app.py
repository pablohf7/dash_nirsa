"""
Dashboard de Monitoreo - Flota Atunera NIRSA
Versión Mejorada con ordenamiento automático y optimizaciones de rendimiento
"""

import dash
from dash import dcc, html, Input, Output, State, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pytz
import requests
from io import StringIO
import re
import json
from flask_caching import Cache
from typing import Dict, List, Tuple, Optional

# ============================================================================
# CONFIGURACIÓN INICIAL
# ============================================================================

# Inicializar la app Dash
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
    suppress_callback_exceptions=True
)

# Configurar cache
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    'CACHE_THRESHOLD': 50
})

app.title = "Dashboard Monitoreo Flota Atunera"
server = app.server

# ============================================================================
# CONSTANTES
# ============================================================================

BARCOS_ATUNEROS = [
    "MILENA A", "MARIA DEL MAR", "ROSA F", "BP RICKY A", "MILAGROS A",
    "EL MARQUEZ", "ROBERTO A", "MARIA EULOGIA", "ELIZABETH F", "GLORIA A",
    "VIA SIMOUN", "DRENNEC", "GABRIELA A", "GURIA", "RAFA A"
]

SHEET_ID = "1kt9igSja2pUTTwzVvWGmGptErH3FUviSb1bymsOx0iU"

COLORES_FRANJAS = {
    'verde': 'rgba(46, 204, 113, 0.8)',
    'amarillo': 'rgba(241, 196, 15, 0.8)',
    'rojo_claro': 'rgba(231, 76, 60, 0.8)',
    'rojo_oscuro': 'rgba(192, 57, 43, 0.8)'
}

ZONA_HORARIA = pytz.timezone('America/Guayaquil')

# ============================================================================
# CSS PERSONALIZADO
# ============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #000000;
                color: #ffffff;
                font-family: 'Arial', sans-serif;
                margin: 0;
                padding: 0;
                overflow-x: hidden;
            }
            
            /* LOGOS */
            .logo-container {
                position: fixed;
                top: 20px;
                z-index: 1100;
                transition: all 0.3s ease;
            }
            .logo-left {
                left: 80px;
            }
            .logo-right {
                right: 20px;
            }
            .logo-img {
                height: 60px;
                width: auto;
                object-fit: contain;
                background-color: rgba(255, 255, 255, 0.9);
                padding: 8px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
            }
            
            .metric-card {
                background-color: #1a1a1a;
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid #2c3e50;
                transition: transform 0.2s ease;
            }
            .metric-card:hover {
                transform: translateY(-2px);
            }
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                color: #2ecc71;
            }
            .metric-label {
                font-size: 0.9rem;
                color: #bdc3c7;
            }
            .btn-primary {
                background-color: #2ecc71;
                border: none;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                width: 100%;
                transition: background-color 0.3s ease;
            }
            .btn-primary:hover { 
                background-color: #27ae60;
                transform: translateY(-1px);
            }

            .btn-sidebar-left {
                position: fixed;
                top: 20px;
                left: 20px;
                z-index: 1100;
                background-color: #2ecc71;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 10px 15px;
                font-size: 16px;
                cursor: pointer;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);
                transition: all 0.3s ease;
            }
            .btn-sidebar-left:hover { 
                background-color: #27ae60;
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0,0,0,0.4);
            }

            .sidebar {
                position: fixed;
                top: 0;
                height: 100vh;
                background-color: #0a0a0a;
                padding: 20px;
                border-radius: 0;
                transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
                overflow-y: auto;
                z-index: 1050;
                box-shadow: 0 0 30px rgba(0,0,0,0.7);
            }
            .sidebar-left {
                left: 0;
                transform: translateX(-100%);
                width: 350px;
            }
            .sidebar-right {
                right: 0;
                transform: translateX(100%);
                width: 700px;
            }
            .sidebar-left.visible { 
                transform: translateX(0);
            }
            .sidebar-right.visible { 
                transform: translateX(0);
            }

            .last-update {
                background: linear-gradient(135deg, #1a1a1a 0%, #2c3e50 100%);
                padding: 12px;
                border-radius: 8px;
                border-left: 5px solid #2ecc71;
                margin: 10px 0;
            }

            .overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(0,0,0,0.6);
                z-index: 1040;
                display: none;
                transition: opacity 0.3s ease;
            }
            .overlay.visible { 
                display: block;
                opacity: 1;
            }

            .gauge-row {
                display: flex;
                justify-content: center;
                align-items: stretch;
                width: 100%;
                margin-bottom: 20px;
            }
            .gauge-col {
                display: flex;
                justify-content: center;
                align-items: stretch;
            }

            .barco-title {
                cursor: pointer;
                transition: all 0.3s ease;
                padding: 4px 10px;
                border-radius: 6px;
                text-align: center;
                margin-bottom: 4px;
                display: block;
                user-select: none;
            }
            .barco-title:hover {
                background-color: rgba(46, 204, 113, 0.12);
                transform: scale(1.03);
            }

            .close-sidebar-btn {
                position: absolute;
                top: 15px;
                right: 15px;
                background: none;
                border: none;
                color: #ecf0f1;
                font-size: 24px;
                cursor: pointer;
                z-index: 1060;
                width: 30px;
                height: 30px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 50%;
                transition: all 0.3s ease;
            }
            .close-sidebar-btn:hover {
                background-color: rgba(231, 76, 60, 0.3);
                color: #e74c3c;
                transform: rotate(90deg);
            }

            .detail-header {
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 2px solid #2c3e50;
            }

            .alertas-resumen {
                background-color: rgba(26, 26, 26, 0.8);
                border-radius: 8px;
                padding: 15px;
                margin-bottom: 20px;
                border: 1px solid #2c3e50;
            }

            .main-content {
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                min-height: 100vh;
                width: 100%;
                padding-top: 20px;
            }
            .sidebar-open-left .main-content {
                margin-left: 350px;
                width: calc(100% - 350px);
            }
            .sidebar-open-right .main-content {
                margin-right: 700px;
                width: calc(100% - 700px);
            }
            .sidebar-open-left.sidebar-open-right .main-content {
                margin-left: 350px;
                margin-right: 700px;
                width: calc(100% - 1050px);
            }

            .graph-container {
                width: 100%;
                height: 500px;
                margin-bottom: 20px;
            }
            .sidebar-content-wrapper { 
                padding: 10px; 
                width: 100%; 
            }

            .equipo-details {
                margin-top: 20px;
                background-color: rgba(26, 26, 26, 0.8);
                border-radius: 8px;
                padding: 15px;
                border: 1px solid #2c3e50;
            }
            .equipo-table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }
            .equipo-table th {
                background-color: #2c3e50;
                color: #ecf0f1;
                padding: 10px;
                text-align: left;
                font-weight: bold;
            }
            .equipo-table td {
                padding: 10px;
                border-bottom: 1px solid #2c3e50;
                color: #bdc3c7;
            }
            .equipo-table tr:hover { 
                background-color: rgba(44, 62, 80, 0.3);
            }

            .tipo-alerta-badge {
                display: inline-block;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
                margin-right: 5px;
                margin-bottom: 5px;
            }

            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 15px;
                margin-bottom: 20px;
            }
            .stat-item {
                background-color: rgba(26, 26, 26, 0.8);
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                border: 1px solid #2c3e50;
                transition: transform 0.2s ease;
            }
            .stat-item:hover {
                transform: translateY(-2px);
            }
            .stat-value {
                font-size: 1.8rem;
                font-weight: bold;
                color: #2ecc71;
                margin-bottom: 5px;
            }
            .stat-label { 
                font-size: 0.9rem; 
                color: #bdc3c7; 
            }

            /* TARJETA DE VELOCÍMETRO */
            .gauge-card {
                position: relative;
                width: 100%;
                max-width: 275px;
                background: rgba(10,10,10,0.55);
                border: 1px solid rgba(255,255,255,0.85);
                border-radius: 20px;
                padding: 10px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.35);
                backdrop-filter: blur(2px);
                transition: transform 0.18s ease, box-shadow 0.18s ease;
                cursor: pointer;
                box-sizing: border-box;
                overflow: hidden;
            }
            .gauge-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 28px rgba(0,0,0,0.45);
            }

            .gauge-card .dash-graph, 
            .gauge-card .js-plotly-plot {
                width: 100% !important;
            }

            /* RESALTADO CON ANIMACIÓN */
            @keyframes gaugePulseThin {
                0%   { transform: scale(1);   box-shadow: 0 0 0 rgba(241,196,15,0.0); }
                50%  { transform: scale(1.015); box-shadow: 0 0 14px rgba(241,196,15,0.75); }
                100% { transform: scale(1);   box-shadow: 0 0 0 rgba(241,196,15,0.0); }
            }
            .gauge-highlight { 
                animation: gaugePulseThin 1s ease-in-out infinite; 
            }
            .gauge-highlight::after {
                content: "";
                position: absolute;
                inset: 7px;
                border: 1px solid rgba(241,196,15,0.95);
                border-radius: 18px;
                pointer-events: none;
            }

            /* ETIQUETA DE EQUIPO CON NUEVA ALERTA */
            .equipo-highlight {
                margin-top: 2px;
                padding: 4px 8px;
                border-radius: 999px;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 0.2px;
                color: #000000;
                background: rgba(241,196,15,0.95);
                max-width: 92%;
                text-align: center;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                box-shadow: 0 6px 16px rgba(0,0,0,0.35);
                user-select: none;
            }

            /* RESPONSIVE */
            @media (max-width: 768px) {
                .sidebar-right { width: 100% !important; }
                .sidebar-open-right .main-content { 
                    margin-right: 0; 
                    width: 100%; 
                }
                .sidebar-open-left.sidebar-open-right .main-content {
                    margin-left: 350px;
                    margin-right: 0;
                    width: calc(100% - 350px);
                }
                .stats-grid { 
                    grid-template-columns: repeat(2, 1fr); 
                }
                .gauge-card { 
                    max-width: 100%; 
                }
                .logo-img {
                    height: 40px;
                }
                .logo-left {
                    left: 70px;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def extraer_nombre_barco_de_area(area: str) -> Optional[str]:
    """Extrae el nombre del barco del campo Área usando expresiones regulares."""
    if not isinstance(area, str):
        return None
    
    area_upper = area.upper()
    patrones = [
        r'\(BARCO\s+([^)]+)\)',
        r'BARCO\s+([A-Z0-9\s\.]+?)(?:\)|$)',
        r'\(\s*([A-Z][A-Z0-9\s\.]+?)\s*\)',
    ]
    
    for patron in patrones:
        match = re.search(patron, area_upper)
        if match:
            nombre = match.group(1).strip()
            nombre = nombre.replace('BARCO', '').strip()
            nombre = re.sub(r'\s+', ' ', nombre)
            if len(nombre) >= 2:
                return nombre
    
    return None


def normalizar_nombre_barco(nombre: str) -> Optional[str]:
    """Normaliza el nombre del barco para que coincida con la lista oficial."""
    if not nombre:
        return None
    
    nombre = str(nombre).strip().upper()
    nombre = re.sub(r'[^\w\s]', '', nombre)
    nombre = re.sub(r'\s+', ' ', nombre).strip()

    # Mapeo especial para nombres alternativos comunes
    mapeo_especial = {
        'RICKY A': 'BP RICKY A', 
        'BP RICKY': 'BP RICKY A', 
        'RICK A': 'BP RICKY A',
        'MARIA D MAR': 'MARIA DEL MAR', 
        'MARIA D EL MAR': 'MARIA DEL MAR',
        'ELIZABETH': 'ELIZABETH F', 
        'ROSA': 'ROSA F', 
        'MILENA': 'MILENA A',
        'MILAGROS': 'MILAGROS A', 
        'GLORIA': 'GLORIA A', 
        'ROBERTO': 'ROBERTO A',
        'GABRIELA': 'GABRIELA A', 
        'RAFA': 'RAFA A',
    }
    
    if nombre in mapeo_especial:
        return mapeo_especial[nombre]

    # Búsqueda fuzzy en la lista oficial
    for barco in BARCOS_ATUNEROS:
        barco_norm = re.sub(r'[^\w\s]', '', barco).strip()
        if nombre == barco_norm or barco_norm in nombre or (len(nombre) >= 4 and nombre in barco_norm):
            return barco

    return nombre


@cache.memoize(timeout=60)
def cargar_datos_google_sheets() -> Tuple[pd.DataFrame, Optional[str]]:
    """Carga los datos desde Google Sheets y los retorna como DataFrame."""
    try:
        url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            return pd.DataFrame(), f"Error HTTP {response.status_code}"
        
        df = pd.read_csv(StringIO(response.text))
        return df, None
    
    except requests.exceptions.Timeout:
        return pd.DataFrame(), "Timeout al conectar con Google Sheets"
    except requests.exceptions.RequestException as e:
        return pd.DataFrame(), f"Error de conexión: {str(e)}"
    except Exception as e:
        return pd.DataFrame(), f"Error inesperado: {str(e)}"


def preparar_df_flota_24h(df_raw_local: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Procesa el DataFrame raw y filtra los datos de la flota de las últimas 24 horas."""
    debug = []
    
    if df_raw_local is None or df_raw_local.empty:
        return pd.DataFrame(), ["DataFrame vacío"]

    df = df_raw_local.copy()

    # Mapeo de columnas alternativas
    mapeo_cols = {
        'Fecha': ['Fecha', 'FECHA', 'fecha', 'FECHA Y HORA', 'Fecha y hora'],
        'Area': ['Área', 'Area', 'ÁREA', 'AREA', 'Área de Alerta', 'AREA DE ALERTA'],
        'Activo': ['Activo', 'ACTIVO', 'activo', 'Equipo', 'EQUIPO', 'equipo'],
        'Alerta': ['Alerta', 'ALERTA', 'alerta', 'Tipo de Alerta', 'TIPO DE ALERTA', 'Tipo de alerta']
    }
    
    for std, variantes in mapeo_cols.items():
        if std in df.columns:
            continue
        for var in variantes:
            if var in df.columns:
                df = df.rename(columns={var: std})
                break

    # Validar columnas requeridas
    if 'Fecha' not in df.columns or 'Area' not in df.columns:
        return pd.DataFrame(), [f"Columnas faltantes. Disponibles: {list(df.columns)}"]

    df['Fecha_Original'] = df['Fecha']

    # Intentar conversión de fechas con múltiples formatos
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce', dayfirst=True, utc=False)

    mask = df['Fecha'].isna()
    if mask.any():
        df.loc[mask, 'Fecha'] = pd.to_datetime(
            df.loc[mask, 'Fecha_Original'],
            errors='coerce',
            format='%d/%m/%Y %H:%M:%S'
        )

    mask = df['Fecha'].isna()
    if mask.any():
        df.loc[mask, 'Fecha'] = pd.to_datetime(
            df.loc[mask, 'Fecha_Original'],
            errors='coerce',
            format='%m/%d/%Y %H:%M:%S'
        )

    mask = df['Fecha'].isna()
    if mask.any():
        df.loc[mask, 'Fecha'] = pd.to_datetime(
            df.loc[mask, 'Fecha_Original'],
            errors='coerce'
        )

    df = df[df['Fecha'].notna()].copy()
    debug.append(f"✅ Fechas válidas: {len(df)}/{len(df_raw_local)}")

    if df.empty:
        ejemplos = df_raw_local['Fecha'].head(5).tolist() if 'Fecha' in df_raw_local.columns else []
        return pd.DataFrame(), [f"No se pudieron convertir fechas. Ejemplos: {ejemplos}"]

    # Ajustar zona horaria
    if getattr(df['Fecha'].dt, 'tz', None) is None:
        df['Fecha'] = df['Fecha'].dt.tz_localize(ZONA_HORARIA, ambiguous='NaT', nonexistent='NaT')
    else:
        df['Fecha'] = df['Fecha'].dt.tz_convert(ZONA_HORARIA)

    df = df[df['Fecha'].notna()].copy()

    # Filtrar últimas 24 horas
    ahora_ec = datetime.now(ZONA_HORARIA)
    limite_ec = ahora_ec - timedelta(hours=24)

    debug.append(f"⏰ Límite 24h (EC): {limite_ec.strftime('%d/%m/%Y %H:%M:%S %Z')}")
    debug.append(f"⏰ Ahora (EC): {ahora_ec.strftime('%d/%m/%Y %H:%M:%S %Z')}")

    df_24h = df[df['Fecha'] >= limite_ec].copy()
    debug.append(f"📊 Registros totales: {len(df)}")
    debug.append(f"📊 Registros 24h: {len(df_24h)}")

    if df_24h.empty:
        return pd.DataFrame(), debug + ["⚠️ Sin registros en 24h"]

    # Filtrar flota atunera
    patrones = ['🐟', 'FLOTA ATUNERA', 'Flota Atunera', 'flota atunera', 'ATUNERA', 'atunera']
    area_str = df_24h['Area'].astype(str)
    mask_flota = pd.Series(False, index=df_24h.index)
    
    for patron in patrones:
        mask_flota |= area_str.str.contains(patron, case=False, na=False)

    df_flota = df_24h[mask_flota].copy()
    debug.append(f"🚢 Registros flota atunera (24h): {len(df_flota)}")

    if df_flota.empty:
        return pd.DataFrame(), debug + ["⚠️ Sin flota atunera en 24h"]

    # Extraer y normalizar nombres de barcos
    df_flota['Barco_Extraido'] = df_flota['Area'].apply(extraer_nombre_barco_de_area)
    df_flota['Barco_Normalizado'] = df_flota['Barco_Extraido'].apply(normalizar_nombre_barco)

    return df_flota, debug


def procesar_alertas_ultimas_24h(df_raw_local: pd.DataFrame) -> Tuple[Dict[str, int], int, List[str]]:
    """Procesa las alertas de las últimas 24 horas y retorna conteos por barco."""
    conteo_por_barco = {barco: 0 for barco in BARCOS_ATUNEROS}
    alertas_sin_barco_local = 0

    df_flota, debug = preparar_df_flota_24h(df_raw_local)
    if df_flota.empty:
        return conteo_por_barco, 0, debug

    df_con = df_flota[df_flota['Barco_Normalizado'].notna()].copy()
    df_sin = df_flota[df_flota['Barco_Normalizado'].isna()].copy()
    alertas_sin_barco_local = len(df_sin)

    df_con = df_con[df_con['Barco_Normalizado'].isin(BARCOS_ATUNEROS)].copy()
    conteo_raw = df_con['Barco_Normalizado'].value_counts().to_dict()

    for barco, cant in conteo_raw.items():
        conteo_por_barco[barco] = int(cant)

    total_identificadas = sum(conteo_por_barco.values())
    debug.append(f"📝 Con barco identificado: {len(df_con)}")
    debug.append(f"⚠️ Sin barco identificado: {alertas_sin_barco_local}")
    debug.append(f"✅ Total alertas (24h): {total_identificadas + alertas_sin_barco_local}")

    return conteo_por_barco, alertas_sin_barco_local, debug


def crear_velocimetro_24h(valor: int, titulo_barco: str, max_valor: int = 30) -> go.Figure:
    """Crea un gráfico de velocímetro para mostrar las alertas de un barco."""
    if valor == 0:
        estado, color, emoji = "Sin Alerta", "#2ecc71", "✅"
    elif valor <= 6:
        estado, color, emoji = "Alerta", "#f1c40f", "⚠️"
    elif valor <= 10:
        estado, color, emoji = "Crítico", "#e74c3c", "🔴"
    else:
        estado, color, emoji = "Crítico Máximo", "#c0392b", "🚨"

    rangos = [0, 0.5, 6.5, 10.5, max_valor]
    colores = [
        COLORES_FRANJAS['verde'], 
        COLORES_FRANJAS['amarillo'],
        COLORES_FRANJAS['rojo_claro'], 
        COLORES_FRANJAS['rojo_oscuro']
    ]

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={
            'text': f"<span style='color: {color}; font-size:13px'>{emoji} {estado}</span>",
            'font': {'size': 13}
        },
        number={
            'font': {'size': 38, 'color': color, 'family': "Arial Black"},
            'suffix': "<br><span style='font-size:10px; color:#bdc3c7'>alertas (24h)</span>"
        },
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {
                'range': [0, max_valor], 
                'tickwidth': 2, 
                'tickcolor': "#ffffff",
                'tickfont': {'color': "#ffffff", 'size': 9}
            },
            'bar': {'color': "#000000", 'thickness': 0.8},
            'bgcolor': "rgba(10,10,10,0.3)",
            'borderwidth': 2,
            'bordercolor': "#7f8c8d",
            'steps': [
                {'range': [rangos[i], rangos[i+1]], 'color': colores[i]} 
                for i in range(len(colores))
            ],
            'threshold': {
                'line': {'color': "#000000", 'width': 3}, 
                'thickness': 0.8, 
                'value': valor
            }
        }
    ))

    fig.update_layout(
        height=176,
        margin=dict(l=6, r=6, t=48, b=6),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#ffffff", 'family': "Arial"}
    )
    
    return fig


def obtener_detalle_barco_24h(df_raw_local: pd.DataFrame, barco_seleccionado: str) -> pd.DataFrame:
    """Obtiene el detalle de alertas por equipo para un barco específico."""
    if df_raw_local is None or df_raw_local.empty:
        return pd.DataFrame()

    df_flota, _ = preparar_df_flota_24h(df_raw_local)
    if df_flota.empty:
        return pd.DataFrame()

    df_barco = df_flota[df_flota['Barco_Normalizado'] == barco_seleccionado].copy()
    if df_barco.empty:
        return pd.DataFrame()

    if 'Activo' not in df_barco.columns:
        df_barco['Activo'] = None
    if 'Alerta' not in df_barco.columns:
        df_barco['Alerta'] = None

    df_barco['Activo'] = df_barco['Activo'].fillna('SIN ACTIVO').astype(str).str.strip()
    df_barco['Alerta'] = df_barco['Alerta'].fillna('SIN ALERTA').astype(str).str.strip()

    df_agrupado = (
        df_barco.groupby(['Activo', 'Alerta'])
        .size()
        .reset_index(name='Cantidad')
        .sort_values('Cantidad', ascending=False)
    )
    
    return df_agrupado


def crear_grafico_barras_apilado(df_detalle: pd.DataFrame, barco_seleccionado: str) -> go.Figure:
    """Crea un gráfico de barras apiladas para mostrar alertas por equipo."""
    if df_detalle.empty:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No hay alertas en las últimas 24 horas para {barco_seleccionado}",
            xref="paper", 
            yref="paper",
            x=0.5, 
            y=0.5,
            showarrow=False,
            font=dict(size=30, color="#ecf0f1")
        )
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font={'color': "#ffffff"},
            height=500
        )
        return fig

    fig = go.Figure()
    tipos_alerta = df_detalle['Alerta'].unique()
    colors = px.colors.qualitative.Set3[:len(tipos_alerta)]
    equipos = df_detalle['Activo'].unique()

    for i, tipo in enumerate(tipos_alerta):
        df_tipo = df_detalle[df_detalle['Alerta'] == tipo]
        equipo_dict = dict(zip(df_tipo['Activo'], df_tipo['Cantidad']))
        valores = [equipo_dict.get(e, 0) for e in equipos]

        fig.add_trace(go.Bar(
            y=equipos,
            x=valores,
            name=tipo,
            orientation='h',
            marker=dict(color=colors[i % len(colors)]),
            hovertemplate='<b>%{y}</b><br>' + f'{tipo}: %{{x}} alertas (24h)<br><extra></extra>'
        ))

    fig.update_layout(
        title={
            'text': f'Alertas por Equipo - {barco_seleccionado} (Últimas 24 horas)',
            'y': 0.95, 
            'x': 0.5, 
            'xanchor': 'center', 
            'yanchor': 'top',
            'font': {'size': 18, 'color': '#2ecc71'}
        },
        barmode='stack',
        height=max(500, len(equipos) * 35 + 100),
        margin=dict(l=10, r=10, t=100, b=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#ffffff", 'family': "Arial", 'size': 12},
        xaxis_title="Cantidad de Alertas (últimas 24h)",
        yaxis_title="Equipos",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(size=11),
            itemwidth=30
        ),
        hoverlabel=dict(bgcolor="#2c3e50", font_size=12, font_family="Arial"),
        xaxis=dict(gridcolor='rgba(44, 62, 80, 0.5)', zerolinecolor='rgba(44, 62, 80, 0.5)'),
        yaxis=dict(gridcolor='rgba(44, 62, 80, 0.3)', tickfont=dict(size=11))
    )
    
    return fig


def crear_tabla_equipos_detallada(df_detalle: pd.DataFrame) -> html.Div:
    """Crea una tabla HTML con el detalle de alertas por equipo."""
    if df_detalle.empty:
        return html.Div([
            html.P(
                "No hay datos detallados disponibles para las últimas 24 horas.",
                style={'color': '#bdc3c7', 'textAlign': 'center', 'padding': '20px'}
            )
        ])

    df_detalle = df_detalle.sort_values(['Activo', 'Cantidad'], ascending=[True, False])
    equipos_unicos = df_detalle['Activo'].unique()

    filas = []
    for equipo in equipos_unicos:
        datos_equipo = df_detalle[df_detalle['Activo'] == equipo]
        total_equipo = int(datos_equipo['Cantidad'].sum())

        badges = []
        for _, row in datos_equipo.iterrows():
            color_idx = hash(row['Alerta']) % len(px.colors.qualitative.Set3)
            color = px.colors.qualitative.Set3[color_idx]
            badges.append(
                html.Span(
                    f"{row['Alerta']}: {int(row['Cantidad'])}",
                    className="tipo-alerta-badge",
                    style={'backgroundColor': color, 'color': '#000000'}
                )
            )

        filas.append(html.Tr([
            html.Td(equipo, style={'fontWeight': 'bold', 'color': '#ecf0f1'}),
            html.Td(
                total_equipo, 
                style={'textAlign': 'center', 'fontWeight': 'bold', 'color': '#2ecc71'}
            ),
            html.Td(
                html.Div(badges, style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '5px'})
            )
        ]))

    return html.Div([
        html.H6(
            "Detalle por Equipo (Últimas 24 horas)", 
            style={'color': '#2ecc71', 'marginBottom': '15px'}
        ),
        html.Table([
            html.Thead(
                html.Tr([
                    html.Th("Equipo", style={'width': '30%'}),
                    html.Th("Total Alertas (24h)", style={'width': '20%', 'textAlign': 'center'}),
                    html.Th("Distribución por Tipo", style={'width': '50%'})
                ])
            ),
            html.Tbody(filas)
        ], className="equipo-table")
    ], className="equipo-details")


def obtener_equipo_mas_reciente_por_barco(df_raw_local: pd.DataFrame, barco: str) -> Optional[str]:
    """Obtiene el equipo con la alerta más reciente para un barco específico."""
    try:
        if df_raw_local is None or df_raw_local.empty:
            return None

        df_flota, _ = preparar_df_flota_24h(df_raw_local)
        if df_flota.empty:
            return None

        df_barco = df_flota[df_flota['Barco_Normalizado'] == barco].copy()
        if df_barco.empty:
            return None

        if 'Activo' not in df_barco.columns:
            return None

        df_barco['Activo'] = df_barco['Activo'].fillna('SIN ACTIVO').astype(str).str.strip()
        df_barco = df_barco.sort_values('Fecha', ascending=False)
        equipo = df_barco.iloc[0]['Activo']
        
        return equipo if equipo else None
    
    except Exception as e:
        print(f"Error obteniendo equipo más reciente: {e}")
        return None


# ============================================================================
# LAYOUT DE LA APLICACIÓN
# ============================================================================

app.layout = html.Div([
    # Botón para abrir sidebar izquierda
    html.Button(
        "⚙️", 
        id="toggle-sidebar-left", 
        className="btn-sidebar-left", 
        title="Mostrar/Ocultar Configuración"
    ),

    # Logos
    html.Div([
        html.Img(
            src="/assets/logo_cecuamaq.jpg",
            className="logo-img",
            alt="Logo Cecuamaq"
        )
    ], className="logo-container logo-left"),
    
    html.Div([
        html.Img(
            src="/assets/logo_nirsa.jpg",
            className="logo-img",
            alt="Logo Nirsa"
        )
    ], className="logo-container logo-right"),

    # Botón para cerrar sidebar derecha
    html.Button(
        "×", 
        id="close-sidebar-right", 
        className="close-sidebar-btn", 
        style={'display': 'none'}
    ),

    # Overlay de fondo
    html.Div(id="sidebar-overlay", className="overlay"),

    # ========================================================================
    # SIDEBAR IZQUIERDA - CONFIGURACIÓN
    # ========================================================================
    html.Div([
        html.H4(
            "⚙️ CONFIGURACIÓN", 
            style={'color': '#2ecc71', 'marginBottom': '20px'}
        ),
        html.Hr(style={'borderColor': '#2c3e50'}),

        html.Label(
            "⏱️ Intervalo de actualización (segundos):", 
            style={'color': '#ecf0f1', 'marginTop': '15px'}
        ),
        dcc.Slider(
            id='intervalo-slider',
            min=30, 
            max=300, 
            step=30, 
            value=60,
            marks={i: str(i) for i in [30, 60, 120, 180, 240, 300]},
            tooltip={"placement": "bottom", "always_visible": True}
        ),
        html.Br(),
        dbc.Button(
            "🔄 ACTUALIZAR AHORA", 
            id="btn-actualizar", 
            color="primary", 
            className="btn-primary",
            style={'marginTop': '20px'}
        ),
    ], className="sidebar sidebar-left", id="sidebar-left"),

    # ========================================================================
    # SIDEBAR DERECHA - DETALLES DEL BARCO
    # ========================================================================
    html.Div([
        html.Div([
            html.H4(
                "🚢 DETALLES DEL BARCO", 
                style={
                    'color': '#2ecc71', 
                    'marginBottom': '20px', 
                    'fontSize': '22px'
                }
            ),
            html.Hr(style={'borderColor': '#2c3e50', 'marginBottom': '20px'}),
            html.Div(id="detail-sidebar-content", className="sidebar-content-wrapper")
        ], className="detail-header")
    ], className="sidebar sidebar-right", id="sidebar-right"),

    # ========================================================================
    # CONTENIDO PRINCIPAL
    # ========================================================================
    html.Div([
        dbc.Container([
            # Título principal
            dbc.Row([
                dbc.Col([
                    html.H1([
                        html.Span("🚢", style={'marginRight': '10px'}),
                        "Dashboard de Monitoreo - Flota Atunera NIRSA"
                    ], style={
                        'textAlign': 'center',
                        'color': '#2ecc71',
                        'textShadow': '0 0 10px rgba(46, 204, 113, 0.5)',
                        'marginTop': '20px',
                        'marginBottom': '10px'
                    }),
                    html.H5(
                        "Indicadores de alertas de vibración y temperatura últimas 24 horas",
                        style={
                            'textAlign': 'center', 
                            'color': '#ecf0f1', 
                            'marginBottom': '30px'
                        }
                    )
                ], width=12)
            ]),

            # Información de actualización
            html.Div(id='update-info', className="last-update"),

            # Contenedor de velocímetros (ordenado automáticamente)
            html.Div(id='velocimeters-container'),

            # Separador
            html.Hr(
                style={
                    'borderColor': '#2c3e50', 
                    'marginTop': '30px', 
                    'marginBottom': '20px'
                }
            ),
            
            # Estadísticas generales
            html.H4(
                "📈 ESTADÍSTICAS GENERALES", 
                style={'color': '#2ecc71', 'marginBottom': '20px'}
            ),

            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.Div(id="total-alertas", className="metric-value"),
                        html.Div("Total Alertas Flota", className="metric-label")
                    ], className="metric-card")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Div(id="barcos-con-alertas", className="metric-value"),
                        html.Div("Barcos con Alertas", className="metric-label")
                    ], className="metric-card")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Div(id="estado-critico", className="metric-value"),
                        html.Div("Estado Crítico", className="metric-label")
                    ], className="metric-card")
                ], width=3),
                dbc.Col([
                    html.Div([
                        html.Div(id="alertas-sin-barco", className="metric-value"),
                        html.Div("Alertas Sin Barco", className="metric-label")
                    ], className="metric-card")
                ], width=3),
            ]),

            # Alerta de advertencia para alertas sin barco
            dbc.Alert(
                id="nota-alertas-sin-barco", 
                color="warning", 
                dismissable=True, 
                is_open=False,
                style={'marginTop': '20px'}
            ),

            # Acordeón con información de debug
            dbc.Accordion([
                dbc.AccordionItem(
                    html.Pre(id="debug-info-content", style={
                        'whiteSpace': 'pre-wrap',
                        'fontFamily': 'monospace',
                        'fontSize': '12px',
                        'backgroundColor': '#2c3e50',
                        'padding': '10px',
                        'borderRadius': '5px'
                    }),
                    title="🔍 INFORMACIÓN DE PROCESAMIENTO"
                )
            ], start_collapsed=True, style={'marginTop': '20px'}),

            # ================================================================
            # COMPONENTES AUXILIARES (Intervals, Stores, Audio)
            # ================================================================
            dcc.Interval(
                id='interval-component', 
                interval=60 * 1000, 
                n_intervals=0
            ),
            dcc.Interval(
                id='countdown-timer', 
                interval=1000, 
                n_intervals=0
            ),
            dcc.Interval(
                id='highlight-timer', 
                interval=1000, 
                n_intervals=0
            ),

            # Stores para mantener estado
            dcc.Store(
                id='alertas-data', 
                data={'conteo_alertas': {}, 'alertas_sin_barco': 0}
            ),
            dcc.Store(
                id='ultima-actualizacion', 
                data=datetime.now().isoformat()
            ),
            dcc.Store(
                id='sidebar-left-state', 
                data={'visible': False}
            ),
            dcc.Store(
                id='sidebar-right-state', 
                data={'visible': False}
            ),
            dcc.Store(id='raw-data-store'),
            dcc.Store(id='selected-boat', data=None),
            dcc.Store(id='prev-alertas-store', data={}),
            dcc.Store(
                id='highlight-store', 
                data={'boats': [], 'until': None, 'equipos': {}}
            ),

            # Audio para alarma
            html.Audio(
                id="alarm-audio",
                src="/assets/alarm.mp3",
                autoPlay=False,
                controls=False,
                style={"display": "none"}
            ),

        ], fluid=True)
    ], className="main-content", id="main-content")
], id="app-container")


# ============================================================================
# CALLBACKS
# ============================================================================

@app.callback(
    [
        Output('alertas-data', 'data'),
        Output('ultima-actualizacion', 'data'),
        Output('debug-info-content', 'children'),
        Output('raw-data-store', 'data')
    ],
    [
        Input('btn-actualizar', 'n_clicks'),
        Input('interval-component', 'n_intervals')
    ],
    [
        State('intervalo-slider', 'value'),
        State('alertas-data', 'data')
    ]
)
def actualizar_datos(n_clicks, n_intervals, intervalo, alertas_data_actual):
    """Callback principal para actualizar los datos desde Google Sheets."""
    ahora = datetime.now()
    
    # Determinar última actualización
    ultima_act_str = alertas_data_actual.get('ultima_actualizacion', ahora.isoformat()) if alertas_data_actual else ahora.isoformat()
    ultima_act = datetime.fromisoformat(ultima_act_str) if isinstance(ultima_act_str, str) else ahora
    tiempo_transcurrido = (ahora - ultima_act).seconds

    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else ''

    # Actualizar si es necesario
    if 'btn-actualizar' in triggered or tiempo_transcurrido >= intervalo or n_intervals == 0:
        df_raw, error = cargar_datos_google_sheets()
        
        if error or df_raw.empty:
            debug_info = [f"❌ Error: {error if error else 'Sin datos'}"]
            return dash.no_update, dash.no_update, "\n".join(debug_info), dash.no_update

        conteo_alertas, alertas_sin_barco, debug_info = procesar_alertas_ultimas_24h(df_raw)
        ultima_actualizacion = ahora

        alertas_data = {
            'conteo_alertas': conteo_alertas,
            'alertas_sin_barco': alertas_sin_barco,
            'ultima_actualizacion': ultima_actualizacion.isoformat()
        }

        raw_data = df_raw.to_json(date_format='iso', orient='split') if not df_raw.empty else None
        return alertas_data, ultima_actualizacion.isoformat(), "\n".join(debug_info), raw_data

    return dash.no_update, dash.no_update, "Esperando próxima actualización...", dash.no_update


@app.callback(
    Output('update-info', 'children'),
    [
        Input('ultima-actualizacion', 'data'),
        Input('intervalo-slider', 'value'),
        Input('countdown-timer', 'n_intervals')
    ]
)
def actualizar_info_actualizacion(ultima_act_data, intervalo, _tick):
    """Actualiza la información de última actualización y tiempo restante."""
    if ultima_act_data:
        try:
            ultima_act = datetime.fromisoformat(ultima_act_data)
            ahora = datetime.now()
            tiempo_transcurrido = (ahora - ultima_act).seconds
            tiempo_restante = max(0, intervalo - (tiempo_transcurrido % max(1, intervalo)))

            return html.Div([
                html.Div([
                    html.Span(
                        "🕒 Última actualización: ", 
                        style={'color': '#2ecc71', 'fontWeight': 'bold'}
                    ),
                    html.Span(
                        ultima_act.strftime('%H:%M:%S'), 
                        style={'color': '#ecf0f1'}
                    )
                ]),
                html.Div([
                    html.Span(
                        "⏱️ Próxima: ", 
                        style={'color': '#2ecc71', 'fontWeight': 'bold'}
                    ),
                    html.Span(
                        f"{tiempo_restante}s", 
                        style={'color': '#ecf0f1'}
                    )
                ])
            ])
        except Exception as e:
            print(f"Error actualizando info: {e}")
            
    return html.Div("🕒 Cargando datos...")


@app.callback(
    [
        Output('prev-alertas-store', 'data'),
        Output('highlight-store', 'data'),
        Output('alarm-audio', 'src'),
        Output('alarm-audio', 'autoPlay')
    ],
    Input('alertas-data', 'data'),
    [
        State('prev-alertas-store', 'data'),
        State('raw-data-store', 'data')
    ]
)
def detectar_nuevas_alertas(alertas_data, prev_data, raw_data):
    """Detecta nuevas alertas comparando con el estado anterior y activa alarma."""
    if not alertas_data or 'conteo_alertas' not in alertas_data:
        return prev_data or {}, {'boats': [], 'until': None, 'equipos': {}}, dash.no_update, False

    current = alertas_data.get('conteo_alertas', {}) or {}
    prev = prev_data or {}

    # Detectar barcos con incremento de alertas
    changed = []
    for barco, val in current.items():
        try:
            if int(val) > int(prev.get(barco, 0)):
                changed.append(barco)
        except (ValueError, TypeError):
            pass

    if changed:
        equipos_map = {}
        if raw_data:
            try:
                df = pd.read_json(raw_data, orient='split')
                for b in changed:
                    eq = obtener_equipo_mas_reciente_por_barco(df, b)
                    if eq:
                        equipos_map[b] = eq
            except Exception as e:
                print(f"Error obteniendo equipos: {e}")
                equipos_map = {}

        until = (datetime.now() + timedelta(seconds=10)).isoformat()
        highlight = {'boats': changed, 'until': until, 'equipos': equipos_map}

        # Activar alarma
        src = f"/assets/alarm.mp3?ts={int(datetime.now().timestamp())}"
        return current, highlight, src, True

    return current, {'boats': [], 'until': None, 'equipos': {}}, dash.no_update, False


@app.callback(
    Output('velocimeters-container', 'children'),
    [
        Input('alertas-data', 'data'),
        Input('interval-component', 'n_intervals'),
        Input('highlight-store', 'data'),
        Input('highlight-timer', 'n_intervals')
    ]
)
def actualizar_velocimetros(alertas_data, n_intervals, highlight_data, n_ticks):
    """
    Actualiza los velocímetros ordenándolos automáticamente de mayor a menor alertas.
    """
    if alertas_data and 'conteo_alertas' in alertas_data:
        conteo = alertas_data.get('conteo_alertas', {})
    else:
        conteo = {barco: 0 for barco in BARCOS_ATUNEROS}

    # Ordenar barcos por cantidad de alertas (mayor a menor)
    barcos_ordenados = sorted(
        BARCOS_ATUNEROS, 
        key=lambda x: int(conteo.get(x, 0)), 
        reverse=True
    )

    # Datos de resaltado
    highlight_boats = set((highlight_data or {}).get('boats', []))
    equipos_map = (highlight_data or {}).get('equipos', {}) or {}
    until_str = (highlight_data or {}).get('until', None)

    still_on = False
    if until_str:
        try:
            still_on = datetime.now() < datetime.fromisoformat(until_str)
        except Exception:
            still_on = False

    # Crear filas con tarjetas ordenadas
    rows = []
    for fila in range(3):
        cols = []
        inicio = fila * 5
        fin = min(inicio + 5, len(barcos_ordenados))

        for barco in barcos_ordenados[inicio:fin]:
            alertas = int(conteo.get(barco, 0))
            fig = crear_velocimetro_24h(alertas, barco, max_valor=30)

            is_highlight = still_on and (barco in highlight_boats)
            equipo_alerta = equipos_map.get(barco)

            cols.append(
                dbc.Col([
                    html.Div(
                        [
                            html.H4(
                                barco,
                                className="barco-title",
                                style={
                                    'textAlign': 'center',
                                    'color': '#ecf0f1',
                                    'marginBottom': '2px',
                                    'fontSize': '18px'
                                }
                            ),
                            html.Div(
                                equipo_alerta if (is_highlight and equipo_alerta) else "",
                                className="equipo-highlight",
                                style={
                                    'display': 'block' if (is_highlight and equipo_alerta) else 'none'
                                }
                            ),
                            html.Div(
                                dcc.Graph(
                                    figure=fig,
                                    config={'displayModeBar': False},
                                    style={'width': '100%', 'height': '176px'}
                                ),
                                style={'width': '100%'}
                            )
                        ],
                        id={'type': 'barco-card', 'index': barco},
                        n_clicks=0,
                        className=("gauge-card gauge-highlight" if is_highlight else "gauge-card"),
                        style={
                            'display': 'flex',
                            'flexDirection': 'column',
                            'justifyContent': 'flex-start',
                            'alignItems': 'center',
                            'margin': '0px 10px',
                        }
                    )
                ], width=2, className="gauge-col")
            )

        rows.append(
            dbc.Row(
                cols, 
                className="gauge-row mb-5 g-4", 
                justify='center'
            )
        )

    return rows


@app.callback(
    [
        Output('total-alertas', 'children'),
        Output('barcos-con-alertas', 'children'),
        Output('estado-critico', 'children'),
        Output('alertas-sin-barco', 'children'),
        Output('nota-alertas-sin-barco', 'children'),
        Output('nota-alertas-sin-barco', 'is_open')
    ],
    Input('alertas-data', 'data')
)
def actualizar_estadisticas(alertas_data):
    """Actualiza las tarjetas de estadísticas generales."""
    if not alertas_data:
        return "0", "0", "0", "0", "", False

    conteo = alertas_data.get('conteo_alertas', {})
    sin_barco = int(alertas_data.get('alertas_sin_barco', 0))

    total_identificadas = sum(int(v) for v in conteo.values())
    total_alertas = total_identificadas + sin_barco
    barcos_con_alerta = sum(1 for v in conteo.values() if int(v) > 0)
    barcos_criticos = sum(1 for v in conteo.values() if int(v) >= 3)

    nota = ""
    mostrar_nota = False
    if sin_barco > 0:
        mostrar_nota = True
        nota = f"""
        ⚠️ **NOTA IMPORTANTE:** Hay **{sin_barco} alertas** de flota atunera que NO tienen
        barco específico identificado en la columna "Área".
        """

    return (
        str(total_alertas),
        str(barcos_con_alerta),
        str(barcos_criticos),
        str(sin_barco),
        nota,
        mostrar_nota
    )


@app.callback(
    Output('interval-component', 'interval'),
    Input('intervalo-slider', 'value')
)
def actualizar_intervalo(intervalo):
    """Actualiza el intervalo de refresco automático."""
    return intervalo * 1000


@app.callback(
    [
        Output('sidebar-left', 'className'),
        Output('sidebar-left-state', 'data'),
        Output('sidebar-overlay', 'className'),
        Output('app-container', 'className')
    ],
    [
        Input('toggle-sidebar-left', 'n_clicks'),
        Input('sidebar-overlay', 'n_clicks')
    ],
    [
        State('sidebar-left-state', 'data'),
        State('sidebar-right-state', 'data')
    ]
)
def toggle_sidebar_left(left_clicks, overlay_clicks, left_state, right_state):
    """Controla la apertura/cierre de la sidebar izquierda."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return "sidebar sidebar-left", {'visible': False}, "overlay", ""

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    left_visible = left_state.get('visible', False) if left_state else False
    right_visible = right_state.get('visible', False) if right_state else False

    if trigger_id == 'toggle-sidebar-left':
        left_visible = not left_visible

    if trigger_id == 'sidebar-overlay':
        left_visible = False

    overlay_class = "overlay visible" if (left_visible or right_visible) else "overlay"

    container_class = ""
    if left_visible and right_visible:
        container_class = "sidebar-open-left sidebar-open-right"
    elif left_visible:
        container_class = "sidebar-open-left"
    elif right_visible:
        container_class = "sidebar-open-right"

    left_class = "sidebar sidebar-left visible" if left_visible else "sidebar sidebar-left"
    
    return left_class, {'visible': left_visible}, overlay_class, container_class


@app.callback(
    [
        Output('sidebar-right', 'className'),
        Output('detail-sidebar-content', 'children'),
        Output('close-sidebar-right', 'style'),
        Output('selected-boat', 'data'),
        Output('sidebar-right-state', 'data'),
        Output('sidebar-overlay', 'className', allow_duplicate=True),
        Output('app-container', 'className', allow_duplicate=True)
    ],
    [
        Input({'type': 'barco-card', 'index': ALL}, 'n_clicks'),
        Input('close-sidebar-right', 'n_clicks'),
        Input('sidebar-overlay', 'n_clicks')
    ],
    [
        State('raw-data-store', 'data'),
        State('selected-boat', 'data'),
        State('sidebar-left-state', 'data'),
        State('sidebar-right-state', 'data')
    ],
    prevent_initial_call=True
)
def toggle_sidebar_right(card_clicks, close_clicks, overlay_clicks, raw_data, selected_boat, left_state, right_state):
    """Controla la apertura/cierre de la sidebar derecha con detalles del barco."""
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    trigger_info = ctx.triggered[0]
    trigger_id = trigger_info['prop_id'].split('.')[0]
    trigger_value = trigger_info.get('value')

    left_visible = left_state.get('visible', False) if left_state else False

    # Click en una tarjeta de barco
    if trigger_id.startswith('{'):
        if not trigger_value:
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

        try:
            barco_info = json.loads(trigger_id)
            barco_seleccionado = barco_info['index']

            df_detalle = pd.DataFrame()
            if raw_data:
                try:
                    df = pd.read_json(raw_data, orient='split')
                    df_detalle = obtener_detalle_barco_24h(df, barco_seleccionado)
                except Exception as e:
                    print(f"Error al cargar datos: {e}")

            if df_detalle.empty:
                contenido = html.Div([
                    html.H5(
                        f"{barco_seleccionado}", 
                        style={
                            'color': '#2ecc71', 
                            'marginBottom': '15px', 
                            'fontSize': '20px'
                        }
                    ),
                    html.P(
                        f"No hay alertas registradas para {barco_seleccionado} en las últimas 24 horas.",
                        style={
                            'color': '#bdc3c7', 
                            'textAlign': 'center', 
                            'padding': '30px', 
                            'fontSize': '16px'
                        }
                    )
                ])
            else:
                fig = crear_grafico_barras_apilado(df_detalle, barco_seleccionado)
                total_alertas = int(df_detalle['Cantidad'].sum())
                equipos_afectados = int(df_detalle['Activo'].nunique())
                tipos_alerta = int(df_detalle['Alerta'].nunique())

                tabla_detallada = crear_tabla_equipos_detallada(df_detalle)

                contenido = html.Div([
                    html.H5(
                        f"{barco_seleccionado}", 
                        style={
                            'color': '#2ecc71', 
                            'marginBottom': '20px', 
                            'fontSize': '24px', 
                            'textAlign': 'center'
                        }
                    ),
                    html.Div([
                        html.H6(
                            "Resumen de Alertas (Últimas 24 horas)", 
                            style={
                                'color': '#2ecc71', 
                                'marginBottom': '15px', 
                                'fontSize': '18px'
                            }
                        ),
                        html.Div([
                            html.Div([
                                html.Div(str(total_alertas), className="stat-value"), 
                                html.Div("Total Alertas", className="stat-label")
                            ], className="stat-item"),
                            html.Div([
                                html.Div(str(equipos_afectados), className="stat-value"), 
                                html.Div("Equipos Afectados", className="stat-label")
                            ], className="stat-item"),
                            html.Div([
                                html.Div(str(tipos_alerta), className="stat-value"), 
                                html.Div("Tipos de Alerta", className="stat-label")
                            ], className="stat-item"),
                        ], className="stats-grid")
                    ], className="alertas-resumen"),

                    html.Hr(style={'borderColor': '#2c3e50', 'margin': '20px 0'}),

                    dcc.Graph(
                        figure=fig,
                        config={
                            'displayModeBar': True, 
                            'displaylogo': False, 
                            'responsive': True
                        },
                        className="graph-container"
                    ),

                    html.Hr(style={'borderColor': '#2c3e50', 'margin': '25px 0'}),

                    tabla_detallada
                ])

            container_class = "sidebar-open-right" if not left_visible else "sidebar-open-left sidebar-open-right"
            overlay_class = "overlay visible"

            return (
                "sidebar sidebar-right visible",
                contenido,
                {'display': 'block'},
                barco_seleccionado,
                {'visible': True},
                overlay_class,
                container_class
            )

        except Exception as e:
            print(f"Error al procesar clic en tarjeta: {e}")
            return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update

    # Cerrar sidebar derecha
    if trigger_id in ['close-sidebar-right', 'sidebar-overlay']:
        container_class = "sidebar-open-left" if left_visible else ""
        overlay_class = "overlay visible" if left_visible else "overlay"
        
        return (
            "sidebar sidebar-right",
            dash.no_update,
            {'display': 'none'},
            None,
            {'visible': False},
            overlay_class,
            container_class
        )

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == '__main__':
    app.run(debug=True, port=8050)

