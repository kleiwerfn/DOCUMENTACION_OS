
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="Gestor OS", layout="centered")

st.title("📂 Gestor de Documentación por Obra Social")

# ===========================================
# SESSION STATE
# ===========================================
if "ruta_factura" not in st.session_state:
    st.session_state.ruta_factura = None


# ===========================================
# HELPERS
# ===========================================
def list_subdirs(path: Path):
    if not path or not path.exists():
        return []
    return sorted([d.name for d in path.iterdir() if d.is_dir()], key=lambda x: x.lower())


MESES_ORDEN = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
               "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
ORDEN_MES = {m: i for i, m in enumerate(MESES_ORDEN)}

def sort_meses(meses):
    conocidos = [m for m in meses if m in ORDEN_MES]
    otros = [m for m in meses if m not in ORDEN_MES]
    return sorted(conocidos, key=lambda x: ORDEN_MES[x]) + sorted(otros)


# --- NORMALIZAR FACTURA ---
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
                parte1 = partes[0]
                parte2 = partes[1]
    else:
        parte1, parte2 = valor.split("_", 1)

    parte1 = "".join([c for c in parte1 if c.isalnum()]).upper()
    parte1 = parte1[:4].zfill(4)

    parte2 = "".join([c for c in parte2 if c.isdigit()])
    parte2 = parte2[:7].zfill(7)

    return f"{parte1}_{parte2}"


# ===========================================
# 1) DIRECTORIO BASE
# ===========================================
st.subheader("1️⃣ Seleccione el directorio base")
directorio_base = st.text_input(
    "Ruta del directorio:",
    value=r"C:\Users\knunez\Streaming de Google Drive\Mi unidad"
)
base_path = Path(directorio_base) if directorio_base else None


# ===========================================
# 2) OBRAS SOCIALES DESDE CARPETAS
# ===========================================
st.subheader("2️⃣ Seleccione la Obra Social")
obras = list_subdirs(base_path) if base_path else []

obra_social = st.selectbox("Obra Social", options=obras) if obras else None
ruta_os = base_path / obra_social if obra_social else None


# ===========================================
# 3) AÑO
# ===========================================
st.subheader("3️⃣ Año")
anios = [d for d in list_subdirs(ruta_os) if d.startswith("Año ")] if ruta_os else []
anio = st.selectbox("Año", options=anios) if anios else None
ruta_anio = ruta_os / anio if anio else None


# ===========================================
# 4) MES
# ===========================================
st.subheader("4️⃣ Mes")
meses = sort_meses(list_subdirs(ruta_anio)) if ruta_anio else []
mes = st.selectbox("Mes", options=meses) if meses else None
ruta_mes = ruta_anio / mes if mes else None


# ===========================================
# 5) PRESTACIÓN
# ===========================================
st.subheader("5️⃣ Tipo de prestación")
prestaciones = list_subdirs(ruta_mes) if ruta_mes else []
prestacion = st.selectbox("Prestación", options=prestaciones) if prestaciones else None
ruta_prestacion = ruta_mes / prestacion if prestacion else None


# ===========================================
# 6) NUMERO DE FACTURA
# ===========================================
st.subheader("6️⃣ Número de factura")

num_factura_raw = st.text_input("Número de factura (formato XXXX_XXXXXXX)")
num_factura = normalizar_factura(num_factura_raw) if num_factura_raw else ""

if num_factura:
    st.success(f"Formato normalizado: **{num_factura}**")



# ===========================================
# 7) BOTÓN CREAR O TOMAR EXISTENTE
# ===========================================
if st.button("📁 Crear / Cargar estructura"):

    if not all([ruta_prestacion, num_factura]):
        st.error("⚠️ Complete todos los datos.")
    else:
        ruta_factura = ruta_prestacion / num_factura

        if ruta_factura.exists():
            st.warning("⚠️ La carpeta ya existía. Se utilizará para cargar archivos.")
        else:
            (ruta_factura / "DOCUMENTACION_NO_OBLIGATORIA").mkdir(parents=True, exist_ok=True)
            st.success(f"✔️ Carpeta creada:\n{ruta_factura}")

        st.session_state.ruta_factura = ruta_factura



# ===========================================
# 8) SUBIDA DE ARCHIVOS (SI YA EXISTE CARPETA)
# ===========================================
if st.session_state.ruta_factura:

    ruta_factura = st.session_state.ruta_factura
    st.markdown("### 📤 Subir documentación")

    factura_pdf = st.file_uploader("Factura (PDF)", type=["pdf"])
    soporte = st.file_uploader("Soporte (XLS/XLSX)", type=["xls", "xlsx"])
    rendicion = st.file_uploader("Rendición (PDF)", type=["pdf"])
    extra = st.file_uploader("Documentación NO obligatoria", accept_multiple_files=True)

    if st.button("💾 Guardar archivos"):

        # FACTURA
        path_factura = ruta_factura / "FACTURA.pdf"
        if factura_pdf:
            if path_factura.exists():
                st.warning("⚠️ FACTURA.pdf ya existe. No se reemplazó.")
            else:
                with open(path_factura, "wb") as f:
                    f.write(factura_pdf.read())
                st.success("✔ FACTURA guardada.")

        # SOPORTE
        if soporte:
            ext = soporte.name.split(".")[-1]
            path_soporte = ruta_factura / f"SOPORTE_FACTURA.{ext}"

            if path_soporte.exists():
                st.warning("⚠️ SOPORTE_FACTURA ya existe. No se reemplazó.")
            else:
                with open(path_soporte, "wb") as f:
                    f.write(soporte.read())
                st.success("✔ SOPORTE guardado.")

        # RENDICION
        path_rendicion = ruta_factura / "RENDICION.pdf"
        if rendicion:
            if path_rendicion.exists():
                st.warning("⚠️ RENDICION.pdf ya existe. No se reemplazó.")
            else:
                with open(path_rendicion, "wb") as f:
                    f.write(rendicion.read())
                st.success("✔ RENDICION guardada.")

        # NO OBLIGATORIA
        if extra:
            for file in extra:
                path_extra = ruta_factura / "DOCUMENTACION_NO_OBLIGATORIA" / file.name
                if path_extra.exists():
                    st.warning(f"⚠️ {file.name} ya existe. No se reemplazó.")
                else:
                    with open(path_extra, "wb") as f:
                        f.write(file.read())
                    st.success(f"✔ {file.name} guardado.")



# ===========================================
# FOOTER ANIMADO
# ===========================================
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