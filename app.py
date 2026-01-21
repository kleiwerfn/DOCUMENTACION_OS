
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import io

st.caption(f"🔎 Keys en secrets: {list(st.secrets.keys())}")
st.set_page_config(page_title="Gestor OS", layout="centered")

# ============================
# AUTH GOOGLE DRIVE
# ============================
def get_drive_service():
    creds_info = st.secrets["google_credentials"]
    creds = service_account.Credentials.from_service_account_info(
        creds_info,
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    return build("drive", "v3", credentials=creds)

drive = get_drive_service()

# Usamos el ID de la carpeta raíz directamente desde secrets.toml
ROOT_ID = st.secrets["ROOT_FOLDER_ID"]

# ============================
# DRIVE HELPERS
# ============================
def search_folder(name, parent_id):
    """Busca una carpeta por nombre dentro de otra carpeta."""
    query = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and name='{name}' and '{parent_id}' in parents and trashed=false"
    )
    results = drive.files().list(q=query, fields="files(id,name)").execute()
    files = results.get("files", [])
    return files[0]["id"] if files else None


def create_folder(name, parent_id):
    """Crea una carpeta y devuelve su ID."""
    file_metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }
    folder = drive.files().create(body=file_metadata, fields="id").execute()
    return folder["id"]


def list_subfolders(parent_id):
    query = (
        f"mimeType='application/vnd.google-apps.folder' "
        f"and '{parent_id}' in parents and trashed=false"
    )
    results = drive.files().list(q=query, fields="files(id,name)").execute()
    files = results.get("files", [])
    return sorted(files, key=lambda f: f["name"].lower())


def file_exists(name, parent_id):
    query = f"name='{name}' and '{parent_id}' in parents and trashed=false"
    results = drive.files().list(q=query, fields="files(id)").execute()
    return len(results.get("files", [])) > 0


def upload_file(uploaded_file, parent_id, save_name):
    """Sube archivo si no existe."""
    if file_exists(save_name, parent_id):
        st.warning(f"⚠️ {save_name} ya existe. No se reemplazó.")
        return

    file_metadata = {"name": save_name, "parents": [parent_id]}
    media = MediaIoBaseUpload(
        io.BytesIO(uploaded_file.read()),
        mimetype=uploaded_file.type,
        resumable=True
    )

    drive.files().create(body=file_metadata, media_body=media, fields="id").execute()
    st.success(f"✔ {save_name} subido correctamente.")


# ============================
# NORMALIZAR FACTURA
# ============================
def normalizar_factura(valor: str) -> str:
    valor = valor.strip()
    if "_" not in valor:
        if valor.isdigit():
            parte1 = ""
            parte2 = valor
        else:
            partes = [p for p in valor.replace("-", "_").split("_") if p]
            if len(partes) == 1:
                parte1 = partes[0]
                parte2 = ""
            else:
                parte1, parte2 = partes[0], partes[1]
    else:
        parte1, parte2 = valor.split("_", 1)

    parte1 = "".join([c for c in parte1 if c.isalnum()]).upper()[:4].zfill(4)
    parte2 = "".join([c for c in parte2 if c.isdigit()])[:7].zfill(7)

    return f"{parte1}_{parte2}"


# ============================
# UI PRINCIPAL
# ============================
st.title("📂 Gestor de Documentación por Obra Social (Google Drive)")

# 1) OBRAS SOCIALES
st.subheader("1️⃣ Seleccione Obra Social")
os_list = list_subfolders(ROOT_ID)
os_names = [f["name"] for f in os_list]
obra_social = st.selectbox("Obra Social", os_names)

OS_ID = search_folder(obra_social, ROOT_ID)

# 2) Año
st.subheader("2️⃣ Año")
years = list_subfolders(OS_ID)
year_names = [y["name"] for y in years]
anio = st.selectbox("Año", year_names)

ANIO_ID = search_folder(anio, OS_ID)

# 3) Mes
st.subheader("3️⃣ Mes")
meses = list_subfolders(ANIO_ID)
mes_names = [m["name"] for m in meses]
mes = st.selectbox("Mes", mes_names)

MES_ID = search_folder(mes, ANIO_ID)

# 4) Prestación
st.subheader("4️⃣ Tipo de Prestación")
prest = list_subfolders(MES_ID)
prest_names = [p["name"] for p in prest]
prestacion = st.selectbox("Prestación", prest_names)

PRES_ID = search_folder(prestacion, MES_ID)

# 5) Nº Factura
st.subheader("5️⃣ Número de Factura")
num_raw = st.text_input("Formato XXXX_XXXXXXX")
num_factura = normalizar_factura(num_raw) if num_raw else ""

if num_factura:
    st.success(f"Número normalizado: **{num_factura}**")

# Crear carpeta factura
if st.button("📁 Crear / Usar factura"):
    factura_id = search_folder(num_factura, PRES_ID)

    if factura_id:
        st.warning("⚠ La factura ya existía. Se usarán las carpetas existentes.")
    else:
        factura_id = create_folder(num_factura, PRES_ID)
        create_folder("DOCUMENTACION_NO_OBLIGATORIA", factura_id)

    st.success("✔ Estructura creada correctamente.")
    st.session_state.factura_id = factura_id


# ============================
# SUBIR ARCHIVOS
# ============================
if "factura_id" in st.session_state:
    factura_id = st.session_state.factura_id

    st.subheader("📤 Subir archivos")
    factura_pdf = st.file_uploader("Factura (PDF)", type=["pdf"])
    soporte = st.file_uploader("Soporte (XLS/XLSX)", type=["xls", "xlsx"])
    rendicion = st.file_uploader("Rendición (PDF)", type=["pdf"])
    extra = st.file_uploader("Documentación NO obligatoria", accept_multiple_files=True)

    if st.button("💾 Guardar archivos"):
        if factura_pdf:
            upload_file(factura_pdf, factura_id, "FACTURA.pdf")

        if soporte:
            ext = soporte.name.split(".")[-1]
            upload_file(soporte, factura_id, f"SOPORTE_FACTURA.{ext}")

        if rendicion:
            upload_file(rendicion, factura_id, "RENDICION.pdf")

        if extra:
            no_obl_id = search_folder("DOCUMENTACION_NO_OBLIGATORIA", factura_id)
            for f in extra:
                upload_file(f, no_obl_id, f.name)


# ============================
# FOOTER ANIMADO
# ============================
st.markdown("---")
st.markdown("""
<style>
@keyframes spinZoom {
    0% { transform: rotate(0deg) scale(1); }
    50% { transform: rotate(180deg) scale(1.3); }
    100% { transform: rotate(360deg) scale(1); }
}
.robot-icon {
    display: inline-block;
    animation: spinZoom 3s ease-in-out 4 forwards;
}
.footer-text {
    text-align: center;
    color: #555;
    font-size: 0.95em;
    font-family: 'Segoe UI', sans-serif;
    margin-top: 20px;
}
</style>
<div class="footer-text">
<span class="robot-icon">🤖</span> <strong>Desarrollado por Kleiwerf Núñez</strong> <span class="robot-icon">🤖</span>
</div>
""", unsafe_allow_html=True)
