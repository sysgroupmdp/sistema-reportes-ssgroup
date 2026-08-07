
import streamlit as st
import sqlite3
from pathlib import Path
from datetime import date, datetime
from PIL import Image
import tempfile
import os
import textwrap

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image as RLImage,
    Table, TableStyle, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT

APP_DIR = Path(__file__).parent
ASSETS = APP_DIR / "assets"
UPLOADS = APP_DIR / "uploads"
REPORTES = APP_DIR / "reportes_pdf"
DB_PATH = APP_DIR / "ss_group_reportes.db"
LOGO_PATH = ASSETS / "logo_ss_group.jpg"

UPLOADS.mkdir(exist_ok=True)
REPORTES.mkdir(exist_ok=True)

VERDE = colors.HexColor("#11823b")
VIOLETA = colors.HexColor("#3f2578")
GRIS = colors.HexColor("#777777")

st.set_page_config(
    page_title="S&S Group - Reportes PDF",
    page_icon="🦺",
    layout="wide"
)

# --------------------------------------------------
# CSS
# --------------------------------------------------
st.markdown("""
<style>
.block-container {
    padding-top: 1rem;
}
.main-title {
    color: #11823b;
    font-weight: 800;
    margin-bottom: 0.2rem;
}
.card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 12px;
    background-color: #ffffff;
}
.small-muted {
    color: #777;
    font-size: 0.9rem;
}
.badge-alta {
    color: #b00020;
    border: 1px solid #ffb5b5;
    border-radius: 6px;
    padding: 3px 8px;
}
.badge-media {
    color: #c26a00;
    border: 1px solid #ffd8a8;
    border-radius: 6px;
    padding: 3px 8px;
}
.badge-baja {
    color: #11823b;
    border: 1px solid #a8dfb9;
    border-radius: 6px;
    padding: 3px 8px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DB
# --------------------------------------------------
def conectar():
    return sqlite3.connect(DB_PATH)

def init_db():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        cuit TEXT,
        contacto TEXT,
        telefono TEXT,
        email TEXT,
        observaciones TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS obras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        direccion TEXT,
        contratista TEXT,
        observaciones TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS recomendaciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        categoria TEXT,
        titulo TEXT,
        texto TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS reportes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        cliente_id INTEGER,
        obra_id INTEGER,
        fecha TEXT,
        tecnico TEXT,
        archivo TEXT,
        creado TEXT,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id),
        FOREIGN KEY(obra_id) REFERENCES obras(id)
    )
    """)

    con.commit()
    con.close()

def cargar_recomendaciones_base():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM recomendaciones")
    if cur.fetchone()[0] == 0:
        datos = [
            ("Trabajo en altura", "Protección contra caídas", "Implementar protecciones colectivas contra caídas a distinto nivel. Cuando no sea posible, utilizar sistema anticaídas con arnés de seguridad, cabo de vida, línea de vida o punto de anclaje certificado, según corresponda."),
            ("Excavaciones", "Señalización y protección de excavación", "Señalizar, delimitar y proteger la excavación. Evaluar estabilidad de taludes, necesidad de entibación, accesos seguros y evitar permanencia de personal no autorizado en el sector."),
            ("Orden y limpieza", "Orden general del sector", "Mantener el sector limpio, ordenado y libre de obstáculos. Retirar residuos, materiales en desuso y elementos que puedan generar caídas, golpes o interferencias en la circulación."),
            ("EPP", "Uso obligatorio de EPP", "Asegurar el uso de casco, calzado de seguridad, guantes, protección ocular, protección auditiva y demás elementos de protección personal específicos según la tarea desarrollada."),
            ("Riesgo eléctrico", "Instalaciones eléctricas seguras", "Verificar el correcto estado de tableros, disyuntores diferenciales, puesta a tierra, cables, prolongaciones y tomacorrientes. Evitar conexiones precarias, empalmes expuestos o tendidos inseguros."),
            ("Maquinaria vial", "Circulación segura de equipos", "Delimitar el área de circulación de maquinaria, controlar puntos ciegos, evitar la presencia de personas dentro del radio operativo y disponer señalero cuando corresponda."),
            ("Andamios", "Condiciones seguras de andamios", "Verificar plataformas completas, barandas, rodapiés, diagonales, nivelación, apoyos firmes y accesos seguros. No utilizar andamios incompletos o sin condiciones de estabilidad."),
            ("Incendio", "Prevención y extintores", "Mantener extintores adecuados al riesgo, accesibles, señalizados y con carga vigente. Controlar fuentes de ignición, materiales combustibles y orden general del sector."),
        ]
        cur.executemany(
            "INSERT INTO recomendaciones (categoria, titulo, texto) VALUES (?, ?, ?)",
            datos
        )
    con.commit()
    con.close()

def listar_clientes():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, cuit, contacto, telefono, email FROM clientes ORDER BY nombre")
    datos = cur.fetchall()
    con.close()
    return datos

def crear_cliente(nombre, cuit, contacto, telefono, email, observaciones):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO clientes (nombre, cuit, contacto, telefono, email, observaciones)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, cuit, contacto, telefono, email, observaciones))
    con.commit()
    con.close()

def listar_obras(cliente_id=None):
    con = conectar()
    cur = con.cursor()
    if cliente_id:
        cur.execute("""
        SELECT obras.id, obras.nombre, obras.direccion, obras.contratista, clientes.nombre
        FROM obras
        JOIN clientes ON clientes.id = obras.cliente_id
        WHERE obras.cliente_id = ?
        ORDER BY obras.nombre
        """, (cliente_id,))
    else:
        cur.execute("""
        SELECT obras.id, obras.nombre, obras.direccion, obras.contratista, clientes.nombre
        FROM obras
        JOIN clientes ON clientes.id = obras.cliente_id
        ORDER BY clientes.nombre, obras.nombre
        """)
    datos = cur.fetchall()
    con.close()
    return datos

def crear_obra(cliente_id, nombre, direccion, contratista, observaciones):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO obras (cliente_id, nombre, direccion, contratista, observaciones)
    VALUES (?, ?, ?, ?, ?)
    """, (cliente_id, nombre, direccion, contratista, observaciones))
    con.commit()
    con.close()

def obtener_cliente(cliente_id):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, nombre, cuit, contacto, telefono, email, observaciones FROM clientes WHERE id = ?", (cliente_id,))
    dato = cur.fetchone()
    con.close()
    return dato

def obtener_obra(obra_id):
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, cliente_id, nombre, direccion, contratista, observaciones FROM obras WHERE id = ?", (obra_id,))
    dato = cur.fetchone()
    con.close()
    return dato

def listar_recomendaciones():
    con = conectar()
    cur = con.cursor()
    cur.execute("SELECT id, categoria, titulo, texto FROM recomendaciones ORDER BY categoria, titulo")
    datos = cur.fetchall()
    con.close()
    return datos

def crear_recomendacion(categoria, titulo, texto):
    con = conectar()
    cur = con.cursor()
    cur.execute("INSERT INTO recomendaciones (categoria, titulo, texto) VALUES (?, ?, ?)", (categoria, titulo, texto))
    con.commit()
    con.close()

def guardar_reporte(cliente_id, obra_id, fecha, tecnico, archivo):
    con = conectar()
    cur = con.cursor()
    cur.execute("""
    INSERT INTO reportes (cliente_id, obra_id, fecha, tecnico, archivo, creado)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (cliente_id, obra_id, fecha, tecnico, archivo, datetime.now().strftime("%d/%m/%Y %H:%M")))
    con.commit()
    con.close()

def listar_reportes():
    con = conectar()
    cur = con.cursor()
    cur.execute("""
    SELECT reportes.id, reportes.fecha, clientes.nombre, obras.nombre, reportes.archivo, reportes.creado
    FROM reportes
    LEFT JOIN clientes ON clientes.id = reportes.cliente_id
    LEFT JOIN obras ON obras.id = reportes.obra_id
    ORDER BY reportes.id DESC
    """)
    datos = cur.fetchall()
    con.close()
    return datos

# --------------------------------------------------
# PDF
# --------------------------------------------------
def fit_image_for_pdf(img_path, max_w=7.5*cm, max_h=5.2*cm):
    try:
        img = Image.open(img_path)
        w, h = img.size
        ratio = min(max_w / w, max_h / h)
        return max(1, w * ratio), max(1, h * ratio)
    except Exception:
        return max_w, max_h

def header_footer(canvas, doc):
    width, height = A4
    canvas.saveState()

    if LOGO_PATH.exists():
        try:
            canvas.drawImage(str(LOGO_PATH), 1.4*cm, height - 2.6*cm, width=7.2*cm, height=1.55*cm, preserveAspectRatio=True, mask='auto')
        except Exception:
            pass

    canvas.setStrokeColor(VERDE)
    canvas.setLineWidth(1.2)
    canvas.line(1.4*cm, height - 3.0*cm, width - 1.4*cm, height - 3.0*cm)

    canvas.setStrokeColor(VERDE)
    canvas.setLineWidth(1)
    canvas.line(1.4*cm, 1.45*cm, width - 1.4*cm, 1.45*cm)

    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS)
    canvas.drawString(1.5*cm, 1.0*cm, "S&S Group – Higiene y Seguridad en el Trabajo")
    canvas.drawRightString(width - 1.5*cm, 1.0*cm, f"Página {doc.page}")

    canvas.restoreState()

def generar_pdf(datos, hallazgos):
    cliente = datos.get("cliente_nombre", "Cliente")
    obra = datos.get("obra_nombre", "Obra")
    fecha_archivo = datos.get("fecha", date.today().strftime("%d-%m-%Y")).replace("/", "-")

    safe_name = f"Reporte_{cliente}_{obra}_{fecha_archivo}.pdf"
    safe_name = "".join(c for c in safe_name if c.isalnum() or c in "._- ")
    pdf_path = REPORTES / safe_name

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=1.4*cm,
        leftMargin=1.4*cm,
        topMargin=3.35*cm,
        bottomMargin=1.8*cm
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "TitleSS",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=15,
        alignment=TA_CENTER,
        textColor=colors.black,
        spaceAfter=12
    )
    h2 = ParagraphStyle(
        "H2SS",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=VERDE,
        spaceBefore=10,
        spaceAfter=6
    )
    normal = ParagraphStyle(
        "NormalSS",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12
    )
    normal_bold = ParagraphStyle(
        "NormalBoldSS",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12
    )

    story = []
    story.append(Paragraph("INFORME DE VISITA DE HIGIENE Y SEGURIDAD", title))

    tabla_datos = [
        [Paragraph("<b>Cliente:</b>", normal), Paragraph(datos.get("cliente_nombre", ""), normal), Paragraph("<b>Obra:</b>", normal), Paragraph(datos.get("obra_nombre", ""), normal)],
        [Paragraph("<b>Dirección:</b>", normal), Paragraph(datos.get("direccion", ""), normal), Paragraph("<b>Fecha:</b>", normal), Paragraph(datos.get("fecha", ""), normal)],
        [Paragraph("<b>Responsable:</b>", normal), Paragraph(datos.get("tecnico", ""), normal), Paragraph("<b>Contratista:</b>", normal), Paragraph(datos.get("contratista", ""), normal)],
    ]

    t = Table(tabla_datos, colWidths=[3.0*cm, 5.5*cm, 3.0*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#f2f2f2")),
        ("BACKGROUND", (2,0), (2,-1), colors.HexColor("#f2f2f2")),
        ("LEFTPADDING", (0,0), (-1,-1), 5),
        ("RIGHTPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 8))

    story.append(Paragraph("OBJETIVO DE LA VISITA", h2))
    story.append(Paragraph(datos.get("objetivo", ""), normal))

    story.append(Paragraph("1. OBSERVACIONES / HALLAZGOS", h2))

    for i, h in enumerate(hallazgos, start=1):
        img_element = Paragraph("Sin imagen", normal)
        if h.get("foto_path"):
            try:
                iw, ih = fit_image_for_pdf(h["foto_path"])
                img_element = RLImage(h["foto_path"], width=iw, height=ih)
            except Exception:
                img_element = Paragraph("No se pudo cargar la imagen", normal)

        texto = []
        prioridad = h.get("prioridad", "")
        texto.append(Paragraph(f"<b>Observación:</b> {h.get('observacion','')}", normal))
        texto.append(Paragraph(f"<b>Sector:</b> {h.get('sector','')}", normal))
        texto.append(Paragraph(f"<b>Riesgo asociado:</b> {h.get('riesgo','')}", normal))
        texto.append(Paragraph(f"<b>Recomendación:</b> {h.get('recomendacion','')}", normal))
        texto.append(Paragraph(f"<b>Prioridad:</b> {prioridad} &nbsp;&nbsp; <b>Plazo:</b> {h.get('plazo','')}", normal))

        num = Paragraph(f"<b>{i}</b>", ParagraphStyle("Num", parent=normal, textColor=colors.white, alignment=TA_CENTER))
        num_box = Table([[num]], colWidths=[0.55*cm], rowHeights=[0.55*cm])
        num_box.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), VIOLETA),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ]))

        item_table = Table(
            [[num_box, img_element, texto]],
            colWidths=[0.75*cm, 8.0*cm, 8.2*cm]
        )
        item_table.setStyle(TableStyle([
            ("GRID", (0,0), (-1,-1), 0.35, colors.HexColor("#cccccc")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("LEFTPADDING", (0,0), (-1,-1), 5),
            ("RIGHTPADDING", (0,0), (-1,-1), 5),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(item_table)
        story.append(Spacer(1, 8))

    story.append(Paragraph("2. CONCLUSIÓN", h2))
    story.append(Paragraph(datos.get("conclusion", ""), normal))
    story.append(Spacer(1, 18))
    story.append(Paragraph("Lic. Martín Nicolás Sirvent<br/>Higiene y Seguridad en el Trabajo<br/>LSH-007382 PBA CPSH", ParagraphStyle(
        "FirmaTexto",
        parent=normal,
        alignment=TA_LEFT,
        fontSize=9
    )))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return pdf_path

# --------------------------------------------------
# APP
# --------------------------------------------------
init_db()
cargar_recomendaciones_base()

if "hallazgos" not in st.session_state:
    st.session_state.hallazgos = []

with st.sidebar:
    if LOGO_PATH.exists():
        st.image(str(LOGO_PATH), use_container_width=True)
    st.markdown("## Menú")
    menu = st.radio(
        "Seleccionar",
        ["Nuevo reporte", "Clientes", "Obras", "Biblioteca de recomendaciones", "Historial"],
        label_visibility="collapsed"
    )
    st.divider()
    st.markdown("**Lic. Martín Nicolás Sirvent**")
    st.caption("Higiene y Seguridad en el Trabajo")
    st.caption("LSH-007382 PBA CPSH")

if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=430)

st.markdown("<h1 class='main-title'>Sistema de Reportes de Obra</h1>", unsafe_allow_html=True)
st.caption("S&S Group · Clientes guardados · Obras guardadas · Exportación directa a PDF")

# ----------------------------
# CLIENTES
# ----------------------------
if menu == "Clientes":
    st.header("Clientes")

    with st.expander("➕ Agregar cliente", expanded=True):
        with st.form("form_cliente"):
            c1, c2 = st.columns(2)
            with c1:
                nombre = st.text_input("Nombre / Razón social")
                cuit = st.text_input("CUIT")
                contacto = st.text_input("Contacto")
            with c2:
                telefono = st.text_input("Teléfono")
                email = st.text_input("Email")
                observaciones = st.text_area("Observaciones")
            ok = st.form_submit_button("Guardar cliente")
            if ok:
                if nombre.strip():
                    crear_cliente(nombre, cuit, contacto, telefono, email, observaciones)
                    st.success("Cliente guardado.")
                    st.rerun()
                else:
                    st.error("El nombre es obligatorio.")

    clientes = listar_clientes()
    if clientes:
        st.dataframe(
            [{"ID": x[0], "Cliente": x[1], "CUIT": x[2], "Contacto": x[3], "Teléfono": x[4], "Email": x[5]} for x in clientes],
            use_container_width=True
        )
    else:
        st.info("Todavía no hay clientes cargados.")

# ----------------------------
# OBRAS
# ----------------------------
elif menu == "Obras":
    st.header("Obras")

    clientes = listar_clientes()
    if not clientes:
        st.warning("Primero cargá un cliente.")
    else:
        cliente_options = {x[1]: x[0] for x in clientes}
        with st.expander("➕ Agregar obra", expanded=True):
            with st.form("form_obra"):
                cliente_nombre = st.selectbox("Cliente", list(cliente_options.keys()))
                nombre_obra = st.text_input("Nombre de obra")
                direccion = st.text_input("Dirección")
                contratista = st.text_input("Comitente / Contratista")
                observaciones = st.text_area("Observaciones")
                ok = st.form_submit_button("Guardar obra")
                if ok:
                    if nombre_obra.strip():
                        crear_obra(cliente_options[cliente_nombre], nombre_obra, direccion, contratista, observaciones)
                        st.success("Obra guardada.")
                        st.rerun()
                    else:
                        st.error("El nombre de obra es obligatorio.")

    obras = listar_obras()
    if obras:
        st.dataframe(
            [{"ID": x[0], "Cliente": x[4], "Obra": x[1], "Dirección": x[2], "Contratista": x[3]} for x in obras],
            use_container_width=True
        )
    else:
        st.info("Todavía no hay obras cargadas.")

# ----------------------------
# RECOMENDACIONES
# ----------------------------
elif menu == "Biblioteca de recomendaciones":
    st.header("Biblioteca de recomendaciones")

    with st.expander("➕ Agregar recomendación", expanded=False):
        with st.form("form_reco"):
            categoria = st.text_input("Categoría")
            titulo = st.text_input("Título")
            texto = st.text_area("Texto")
            ok = st.form_submit_button("Guardar recomendación")
            if ok:
                if titulo.strip() and texto.strip():
                    crear_recomendacion(categoria, titulo, texto)
                    st.success("Recomendación guardada.")
                    st.rerun()
                else:
                    st.error("Completá título y texto.")

    for r in listar_recomendaciones():
        with st.expander(f"{r[1]} · {r[2]}"):
            st.write(r[3])

# ----------------------------
# HISTORIAL
# ----------------------------
elif menu == "Historial":
    st.header("Historial de reportes PDF")
    reportes = listar_reportes()
    if reportes:
        for r in reportes:
            archivo = Path(r[4]) if r[4] else None
            with st.container(border=True):
                st.write(f"**{r[2]} · {r[3]}**")
                st.caption(f"Fecha visita: {r[1]} · Creado: {r[5]}")
                if archivo and archivo.exists():
                    with open(archivo, "rb") as f:
                        st.download_button(
                            "Descargar PDF",
                            data=f,
                            file_name=archivo.name,
                            mime="application/pdf",
                            key=f"hist_{r[0]}"
                        )
    else:
        st.info("Todavía no hay reportes generados.")

# ----------------------------
# NUEVO REPORTE
# ----------------------------
elif menu == "Nuevo reporte":
    st.header("Nuevo reporte PDF")

    clientes = listar_clientes()
    if not clientes:
        st.warning("Primero cargá un cliente desde el menú Clientes.")
        st.stop()

    cliente_options = {x[1]: x[0] for x in clientes}
    cliente_nombre = st.selectbox("Cliente", list(cliente_options.keys()))
    cliente_id = cliente_options[cliente_nombre]

    obras = listar_obras(cliente_id)
    if not obras:
        st.warning("Este cliente no tiene obras cargadas. Cargá una obra desde el menú Obras.")
        st.stop()

    obra_options = {f"{x[1]} - {x[2] or 'Sin dirección'}": x[0] for x in obras}
    obra_label = st.selectbox("Obra", list(obra_options.keys()))
    obra_id = obra_options[obra_label]

    cliente = obtener_cliente(cliente_id)
    obra = obtener_obra(obra_id)

    col1, col2 = st.columns(2)
    with col1:
        fecha_visita = st.date_input("Fecha de visita", value=date.today())
        tecnico = st.text_input("Responsable", value="Lic. Martín Nicolás Sirvent")
    with col2:
        objetivo = st.text_area("Objetivo", value="Relevar condiciones de higiene y seguridad en obra, registrar desvíos y proponer medidas correctivas.")
        conclusion = st.text_area("Conclusión", value="Se recomienda implementar las medidas correctivas indicadas a fin de garantizar condiciones seguras de trabajo y prevenir incidentes.")

    st.divider()
    st.subheader("Observaciones / Hallazgos")

    recs = listar_recomendaciones()
    rec_options = ["Escribir manualmente"] + [f"{r[1]} · {r[2]}" for r in recs]
    rec_map = {f"{r[1]} · {r[2]}": r[3] for r in recs}

    with st.form("form_hallazgo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            sector = st.text_input("Sector")
            riesgo = st.text_input("Riesgo asociado")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja", "Observación"])
            plazo = st.text_input("Plazo sugerido", value="Inmediato / A definir")
            foto = st.file_uploader("Foto", type=["jpg", "jpeg", "png"])
        with c2:
            observacion = st.text_area("Observación detectada")
            rec_sel = st.selectbox("Recomendación frecuente", rec_options)
            recomendacion_manual = st.text_area("Recomendación técnica manual")

        agregar = st.form_submit_button("➕ Agregar hallazgo")
        if agregar:
            recomendacion = recomendacion_manual.strip()
            if not recomendacion and rec_sel != "Escribir manualmente":
                recomendacion = rec_map.get(rec_sel, "")

            foto_path = None
            if foto:
                ext = os.path.splitext(foto.name)[1].lower()
                nombre = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{foto.name}"
                nombre = "".join(c for c in nombre if c.isalnum() or c in "._- ")
                foto_path = UPLOADS / nombre
                with open(foto_path, "wb") as f:
                    f.write(foto.getbuffer())

            st.session_state.hallazgos.append({
                "sector": sector,
                "observacion": observacion,
                "riesgo": riesgo,
                "recomendacion": recomendacion,
                "prioridad": prioridad,
                "plazo": plazo,
                "foto_path": str(foto_path) if foto_path else None
            })
            st.success("Hallazgo agregado.")

    if st.session_state.hallazgos:
        for i, h in enumerate(st.session_state.hallazgos, start=1):
            with st.container(border=True):
                cols = st.columns([1, 4, 1])
                with cols[0]:
                    st.write(f"### {i}")
                    if h.get("foto_path"):
                        st.image(h["foto_path"], width=160)
                with cols[1]:
                    st.write(f"**Observación:** {h.get('observacion','')}")
                    st.write(f"**Recomendación:** {h.get('recomendacion','')}")
                    st.caption(f"Sector: {h.get('sector','')} · Riesgo: {h.get('riesgo','')} · Plazo: {h.get('plazo','')}")
                with cols[2]:
                    st.write(f"**{h.get('prioridad','')}**")

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Generar PDF", type="primary"):
                datos = {
                    "cliente_nombre": cliente[1],
                    "obra_nombre": obra[2],
                    "direccion": obra[3],
                    "contratista": obra[4],
                    "fecha": fecha_visita.strftime("%d/%m/%Y"),
                    "tecnico": tecnico,
                    "objetivo": objetivo,
                    "conclusion": conclusion,
                }
                pdf_path = generar_pdf(datos, st.session_state.hallazgos)
                guardar_reporte(cliente_id, obra_id, datos["fecha"], tecnico, str(pdf_path))
                with open(pdf_path, "rb") as f:
                    st.download_button(
                        "Descargar PDF",
                        data=f,
                        file_name=pdf_path.name,
                        mime="application/pdf"
                    )
                st.success("PDF generado y guardado en historial.")
        with c2:
            if st.button("🧹 Limpiar hallazgos"):
                st.session_state.hallazgos = []
                st.rerun()
    else:
        st.info("Todavía no cargaste hallazgos.")
