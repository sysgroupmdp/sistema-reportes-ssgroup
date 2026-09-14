
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

# Firmas profesionales. Si existen estos archivos dentro de /assets, se insertan en el PDF.
FIRMA_MARTIN_PATH = ASSETS / "firma_martin.png"
FIRMA_JUANI_PATH = ASSETS / "firma_juani.png"

PROFESIONALES = {
    "Lic. Martín Nicolás Sirvent": {
        "nombre": "Lic. Martín Nicolás Sirvent",
        "matricula": "LSH-007382 PBA CPSH",
        "firma": FIRMA_MARTIN_PATH,
    },
    "Lic. Juan Ignacio Sirvent": {
        "nombre": "Lic. Juan Ignacio Sirvent",
        "matricula": "",
        "firma": FIRMA_JUANI_PATH,
    },
}

UPLOADS.mkdir(exist_ok=True)
REPORTES.mkdir(exist_ok=True)

VERDE = colors.HexColor("#11823b")
VIOLETA = colors.HexColor("#3f2578")
GRIS = colors.HexColor("#777777")

# Clientes base migrados desde Gestión Administrativa.
# Se reponen automáticamente si la base local se reinicia, sin duplicarlos.
CLIENTES_GESTION_BASE = [{'nombre': 'MAGLIANO MARCELO', 'cuit': ''},
 {'nombre': 'JUAREZ CESAR', 'cuit': ''},
 {'nombre': 'EULOGIO CONDORI', 'cuit': ''},
 {'nombre': 'ROJAS MARTIN', 'cuit': ''},
 {'nombre': 'BIOPARQUE BATAN 2023 S.A.', 'cuit': '30718359453'},
 {'nombre': 'ALTURAS MS MIRAMAR S.R.L', 'cuit': '30718579763'},
 {'nombre': 'GAUTHIER WALTER', 'cuit': ''},
 {'nombre': 'COOPERATIVA DE TRABAJO COOPECONS LTDA', 'cuit': '30717179680'},
 {'nombre': 'OBISPADO DE MAR DEL PLATA', 'cuit': '30542337555'},
 {'nombre': 'COOPERATIVA DE TRABAJO EL CHE LIMITADA', 'cuit': '33711078199'},
 {'nombre': 'COOPERATIVA DE TRABAJO SEGUIMOS LUCHANDO LTDA', 'cuit': '30714199753'},
 {'nombre': 'INVERSORA EN CONSTRUCCIONES DE COBO S.A.', 'cuit': '30711651280'},
 {'nombre': 'GALVAN', 'cuit': ''},
 {'nombre': 'SINDICATO DE QUIMICOS', 'cuit': '30532700414'},
 {'nombre': 'INFINIT', 'cuit': '30711262713'},
 {'nombre': 'GENARO Y ANDRES DE STEFANO', 'cuit': '30500689826'},
 {'nombre': 'RUCANEDA S.A.', 'cuit': '30712269134'},
 {'nombre': 'SARAZOLA', 'cuit': ''},
 {'nombre': 'RBC CONSTRUCCIONES', 'cuit': '6 MONOTRIBUTISTAS'},
 {'nombre': 'FIDEICOMISO DAPROTIS 4156 MAR DEL PLATA', 'cuit': '30717979296'},
 {'nombre': 'OESTE (LAURA FARIAS)', 'cuit': '27149714826'},
 {'nombre': 'DISTRISUPER S.R.L.', 'cuit': '30609249206'},
 {'nombre': 'DIMES S.A.', 'cuit': '33715613439'},
 {'nombre': 'ROCA 2936 MAR DEL PLATA S.A.', 'cuit': '30717026965'},
 {'nombre': 'RAMOS SANCHEZ ALCIDES', 'cuit': ''},
 {'nombre': 'GEHIE GASTRONOMICA SRL (alito)', 'cuit': '30681375135'},
 {'nombre': 'GUSTAVO RIVERA PLOMERO', 'cuit': ''},
 {'nombre': 'BARD ATILIO RENE', 'cuit': '20047463514'},
 {'nombre': 'MAGGI MARCELO Y MAGGI MAURICIO SOC …', 'cuit': '30688684028'},
 {'nombre': 'CRUZ GEORGE', 'cuit': ''},
 {'nombre': 'MONDEGO DA GUARDA S.A.', 'cuit': '30716517361'},
 {'nombre': 'GRUPO BOREAS S.R.L.', 'cuit': '30714816981'},
 {'nombre': 'COOK MASTER S.A.', 'cuit': '30708214368'},
 {'nombre': 'UP EXPLANADA S.A.', 'cuit': '33718243829'},
 {'nombre': 'PEZZANA DIEGO', 'cuit': '20259572453'},
 {'nombre': 'LUBRIEL SRL', 'cuit': '30711294704'},
 {'nombre': 'MANALER S.A.', 'cuit': '30716570440'},
 {'nombre': 'LOGISMAR S.R.L.', 'cuit': '30708043636'},
 {'nombre': 'USAI ANALIA USAI GABRIELA USAI ESTEBAN S.H.', 'cuit': '33636629559'},
 {'nombre': 'ANGELICO CORP', 'cuit': '30718290747'},
 {'nombre': 'PROSEGUR S.A.', 'cuit': '30575170125'},
 {'nombre': 'JUNCADELLA', 'cuit': '30546969874'},
 {'nombre': 'MADRID', 'cuit': ''},
 {'nombre': 'CAPARARO', 'cuit': '23272137404'}]


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
:root { --ss-verde:#11823b; --ss-violeta:#3f2578; }
.block-container { padding-top: .7rem; padding-bottom: 5rem; max-width: 1180px; }
.main-title { color: var(--ss-verde); font-weight: 800; margin: .15rem 0; }
.small-muted { color:#777; font-size:.9rem; }
div[data-testid="stForm"], div[data-testid="stVerticalBlockBorderWrapper"] { border-radius: 14px; }
.stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button {
    min-height: 46px; border-radius: 10px; font-weight: 700;
}
button[kind="primary"] { background: var(--ss-verde) !important; border-color: var(--ss-verde) !important; }
input, textarea { font-size: 16px !important; } /* evita zoom automático en iPhone */
[data-testid="stFileUploaderDropzone"] { padding: .8rem !important; }
@media (max-width: 700px) {
  .block-container { padding-left: .65rem; padding-right: .65rem; padding-top: .35rem; }
  h1 { font-size: 1.75rem !important; } h2 { font-size: 1.35rem !important; } h3 { font-size: 1.1rem !important; }
  [data-testid="stHorizontalBlock"] { gap: .45rem; }
  .stButton > button, .stDownloadButton > button, div[data-testid="stFormSubmitButton"] > button { width:100%; }
  [data-testid="stImage"] img { max-height: 240px; object-fit: contain; }
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

def migrar_clientes_gestion():
    """Incorpora la cartera base de Gestión Administrativa sin duplicar clientes."""
    con = conectar()
    cur = con.cursor()
    agregados = 0
    for cli in CLIENTES_GESTION_BASE:
        nombre = (cli.get("nombre") or "").strip()
        cuit = (cli.get("cuit") or "").strip()
        if not nombre:
            continue

        row = None
        if cuit:
            cur.execute("SELECT id FROM clientes WHERE TRIM(COALESCE(cuit, '')) = ?", (cuit,))
            row = cur.fetchone()
        if not row:
            cur.execute("SELECT id FROM clientes WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))", (nombre,))
            row = cur.fetchone()

        if row:
            cur.execute(
                "UPDATE clientes SET cuit = COALESCE(NULLIF(?, ''), cuit) WHERE id = ?",
                (cuit, row[0]),
            )
        else:
            cur.execute(
                "INSERT INTO clientes (nombre, cuit, contacto, telefono, email, observaciones) VALUES (?, ?, '', '', '', ?)",
                (nombre, cuit, "Migrado automáticamente desde Gestión Administrativa"),
            )
            agregados += 1

    con.commit()
    con.close()
    return agregados

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
    cur.execute("SELECT id, nombre, cuit, contacto, telefono, email, observaciones FROM clientes ORDER BY nombre")
    datos = cur.fetchall()
    con.close()
    return datos

def crear_cliente(nombre, cuit, contacto, telefono, email, observaciones):
    nombre = (nombre or "").strip()
    cuit = (cuit or "").strip()
    con = conectar()
    cur = con.cursor()
    row = None
    if cuit:
        cur.execute("SELECT id FROM clientes WHERE TRIM(COALESCE(cuit, '')) = ?", (cuit,))
        row = cur.fetchone()
    if not row:
        cur.execute("SELECT id FROM clientes WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))", (nombre,))
        row = cur.fetchone()
    if row:
        cur.execute("""
            UPDATE clientes
            SET cuit = COALESCE(NULLIF(?, ''), cuit),
                contacto = COALESCE(NULLIF(?, ''), contacto),
                telefono = COALESCE(NULLIF(?, ''), telefono),
                email = COALESCE(NULLIF(?, ''), email),
                observaciones = COALESCE(NULLIF(?, ''), observaciones)
            WHERE id = ?
        """, (cuit, contacto, telefono, email, observaciones, row[0]))
    else:
        cur.execute("""
            INSERT INTO clientes (nombre, cuit, contacto, telefono, email, observaciones)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (nombre, cuit, contacto, telefono, email, observaciones))
    con.commit()
    con.close()

def obtener_o_crear_cliente(nombre, cuit="", contacto="", telefono="", email="", observaciones=""):
    """Devuelve el ID del cliente existente o lo crea automáticamente al generar el reporte."""
    nombre = (nombre or "").strip()
    cuit = (cuit or "").strip()
    contacto = (contacto or "").strip()
    telefono = (telefono or "").strip()
    email = (email or "").strip()
    observaciones = (observaciones or "").strip()

    con = conectar()
    cur = con.cursor()

    if cuit:
        cur.execute("SELECT id FROM clientes WHERE TRIM(COALESCE(cuit, '')) = ?", (cuit,))
        row = cur.fetchone()
        if row:
            cliente_id = row[0]
            cur.execute("""
                UPDATE clientes
                SET nombre = COALESCE(NULLIF(?, ''), nombre),
                    contacto = COALESCE(NULLIF(?, ''), contacto),
                    telefono = COALESCE(NULLIF(?, ''), telefono),
                    email = COALESCE(NULLIF(?, ''), email),
                    observaciones = COALESCE(NULLIF(?, ''), observaciones)
                WHERE id = ?
            """, (nombre, contacto, telefono, email, observaciones, cliente_id))
            con.commit()
            con.close()
            return cliente_id

    cur.execute("SELECT id FROM clientes WHERE LOWER(TRIM(nombre)) = LOWER(TRIM(?))", (nombre,))
    row = cur.fetchone()
    if row:
        cliente_id = row[0]
        cur.execute("""
            UPDATE clientes
            SET cuit = COALESCE(NULLIF(?, ''), cuit),
                contacto = COALESCE(NULLIF(?, ''), contacto),
                telefono = COALESCE(NULLIF(?, ''), telefono),
                email = COALESCE(NULLIF(?, ''), email),
                observaciones = COALESCE(NULLIF(?, ''), observaciones)
            WHERE id = ?
        """, (cuit, contacto, telefono, email, observaciones, cliente_id))
        con.commit()
        con.close()
        return cliente_id

    cur.execute("""
    INSERT INTO clientes (nombre, cuit, contacto, telefono, email, observaciones)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (nombre, cuit, contacto, telefono, email, observaciones))
    cliente_id = cur.lastrowid
    con.commit()
    con.close()
    return cliente_id

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

def obtener_o_crear_obra(cliente_id, nombre, direccion="", contratista="", observaciones=""):
    """Devuelve el ID de la obra existente o la crea automáticamente al generar el reporte."""
    nombre = (nombre or "").strip()
    direccion = (direccion or "").strip()
    contratista = (contratista or "").strip()
    observaciones = (observaciones or "").strip()

    con = conectar()
    cur = con.cursor()
    cur.execute("""
        SELECT id FROM obras
        WHERE cliente_id = ?
          AND LOWER(TRIM(nombre)) = LOWER(TRIM(?))
    """, (cliente_id, nombre))
    row = cur.fetchone()
    if row:
        obra_id = row[0]
        cur.execute("""
            UPDATE obras
            SET direccion = COALESCE(NULLIF(?, ''), direccion),
                contratista = COALESCE(NULLIF(?, ''), contratista),
                observaciones = COALESCE(NULLIF(?, ''), observaciones)
            WHERE id = ?
        """, (direccion, contratista, observaciones, obra_id))
        con.commit()
        con.close()
        return obra_id

    cur.execute("""
    INSERT INTO obras (cliente_id, nombre, direccion, contratista, observaciones)
    VALUES (?, ?, ?, ?, ?)
    """, (cliente_id, nombre, direccion, contratista, observaciones))
    obra_id = cur.lastrowid
    con.commit()
    con.close()
    return obra_id

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
        fotos_hallazgo = h.get("foto_paths") or ([h.get("foto_path")] if h.get("foto_path") else [])
        imagenes = []
        for foto_h in fotos_hallazgo:
            if not foto_h:
                continue
            try:
                iw, ih = fit_image_for_pdf(foto_h, max_w=7.5*cm, max_h=4.4*cm)
                imagenes.append(RLImage(foto_h, width=iw, height=ih))
                imagenes.append(Spacer(1, 4))
            except Exception:
                pass
        img_element = imagenes if imagenes else Paragraph("Sin imagen", normal)

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

    story.append(Paragraph("2. OBSERVACIONES GENERALES", h2))
    observaciones_generales = (datos.get("observaciones_generales") or "").strip()
    story.append(Paragraph(observaciones_generales if observaciones_generales else "Sin observaciones adicionales.", normal))

    story.append(Paragraph("3. CONCLUSIÓN", h2))
    story.append(Paragraph(datos.get("conclusion", ""), normal))
    story.append(Spacer(1, 14))

    profesional = PROFESIONALES.get(datos.get("tecnico"), PROFESIONALES["Lic. Martín Nicolás Sirvent"])
    firma_path = profesional.get("firma")
    if firma_path and Path(firma_path).exists():
        try:
            iw, ih = fit_image_for_pdf(str(firma_path), max_w=5.0*cm, max_h=2.2*cm)
            story.append(RLImage(str(firma_path), width=iw, height=ih))
            story.append(Spacer(1, 2))
        except Exception:
            pass

    matricula = profesional.get("matricula", "")
    firma_txt = f"{profesional.get('nombre','')}<br/>Higiene y Seguridad en el Trabajo"
    if matricula:
        firma_txt += f"<br/>{matricula}"
    story.append(Paragraph(firma_txt, ParagraphStyle(
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
migrar_clientes_gestion()
cargar_recomendaciones_base()

if "hallazgos" not in st.session_state:
    st.session_state.hallazgos = []
if "ultimo_pdf" not in st.session_state:
    st.session_state.ultimo_pdf = None
if "foto_widget_nonce" not in st.session_state:
    st.session_state.foto_widget_nonce = 0

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
    st.image(str(LOGO_PATH), width=360)

st.markdown("<h1 class='main-title'>Sistema de Reportes de Obra</h1>", unsafe_allow_html=True)
st.caption("S&S Group · Clientes migrados de Gestión Administrativa · Múltiples obras por cliente · PDF directo")

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
    st.info("Elegí un cliente de Gestión Administrativa y luego una de sus obras. Si la obra todavía no existe, cargala una vez: al generar el PDF queda asociada a ese cliente.")

    with st.container(border=True):
        st.subheader("Datos del cliente y obra")
        clientes_guardados = listar_clientes()
        opciones_clientes = {"— Cargar cliente nuevo —": None}
        for cli in clientes_guardados:
            etiqueta = cli[1]
            if cli[2]:
                etiqueta += f" · CUIT {cli[2]}"
            opciones_clientes[etiqueta] = cli

        def cargar_cliente_guardado():
            seleccionado = opciones_clientes.get(st.session_state.get("selector_cliente_guardado"))
            if seleccionado:
                st.session_state["nuevo_cliente_nombre"] = seleccionado[1] or ""
                st.session_state["nuevo_cliente_cuit"] = seleccionado[2] or ""
                st.session_state["nuevo_cliente_contacto"] = seleccionado[3] or ""
                st.session_state["nuevo_cliente_telefono"] = seleccionado[4] or ""
                st.session_state["nuevo_cliente_email"] = seleccionado[5] or ""
                st.session_state["nuevo_observaciones_internas"] = seleccionado[6] or ""
                obras_cli = listar_obras(seleccionado[0])
                st.session_state["obras_cliente_actual"] = obras_cli
            else:
                for k in ["nuevo_cliente_nombre","nuevo_cliente_cuit","nuevo_cliente_contacto","nuevo_cliente_telefono","nuevo_cliente_email","nuevo_observaciones_internas","nuevo_obra_nombre","nuevo_direccion","nuevo_contratista"]:
                    st.session_state[k] = ""
                st.session_state["obras_cliente_actual"] = []
                st.session_state["selector_obra_guardada"] = "— Cargar obra nueva —"

        st.selectbox(
            "Elegir cliente guardado",
            list(opciones_clientes.keys()),
            key="selector_cliente_guardado",
            on_change=cargar_cliente_guardado,
            help="Elegí un cliente y sus datos se completan automáticamente."
        )

        cliente_sel = opciones_clientes.get(st.session_state.get("selector_cliente_guardado"))
        obras_cliente = listar_obras(cliente_sel[0]) if cliente_sel else []
        opciones_obras = {"— Cargar obra nueva —": None}
        for ob in obras_cliente:
            etiqueta = ob[1] + (f" · {ob[2]}" if ob[2] else "")
            opciones_obras[etiqueta] = ob

        def cargar_obra_guardada():
            seleccionado = opciones_obras.get(st.session_state.get("selector_obra_guardada"))
            if seleccionado:
                detalle = obtener_obra(seleccionado[0])
                st.session_state["nuevo_obra_nombre"] = detalle[2] or ""
                st.session_state["nuevo_direccion"] = detalle[3] or ""
                st.session_state["nuevo_contratista"] = detalle[4] or ""
            else:
                st.session_state["nuevo_obra_nombre"] = ""
                st.session_state["nuevo_direccion"] = ""
                st.session_state["nuevo_contratista"] = ""

        if cliente_sel:
            st.selectbox(
                "Elegir obra guardada",
                list(opciones_obras.keys()),
                key="selector_obra_guardada",
                on_change=cargar_obra_guardada,
                help="Muestra solamente las obras del cliente elegido."
            )

        tab_principal, tab_contacto = st.tabs(["Datos principales", "Contacto / internos"])
        with tab_principal:
            cliente_nombre = st.text_input("Cliente / Razón social", key="nuevo_cliente_nombre")
            cliente_cuit = st.text_input("CUIT", key="nuevo_cliente_cuit")
            obra_nombre = st.text_input("Obra / Establecimiento", key="nuevo_obra_nombre")
            direccion = st.text_input("Dirección", key="nuevo_direccion")
            contratista = st.text_input("Comitente / Contratista", key="nuevo_contratista")
        with tab_contacto:
            cliente_contacto = st.text_input("Contacto", key="nuevo_cliente_contacto")
            cliente_telefono = st.text_input("Teléfono", key="nuevo_cliente_telefono")
            cliente_email = st.text_input("Email", key="nuevo_cliente_email")
            observaciones_cliente_obra = st.text_area("Observaciones internas del cliente/obra", key="nuevo_observaciones_internas")

    col1, col2 = st.columns(2)
    with col1:
        fecha_visita = st.date_input("Fecha de visita", value=date.today())
        tecnico = st.selectbox(
            "Profesional actuante / firma",
            list(PROFESIONALES.keys()),
            index=0,
            help="El profesional seleccionado figurará como responsable y firmante del reporte."
        )
    with col2:
        objetivo = st.text_area("Objetivo", value="Relevar condiciones de higiene y seguridad en obra, registrar desvíos y proponer medidas correctivas.")
        observaciones_generales = st.text_area(
            "Observaciones generales",
            value="",
            help="Espacio libre para aclaraciones generales que no correspondan a un hallazgo puntual."
        )
        conclusion = st.text_area("Conclusión", value="Se recomienda implementar las medidas correctivas indicadas a fin de garantizar condiciones seguras de trabajo y prevenir incidentes.")

    st.divider()
    st.subheader("Observaciones / Hallazgos")

    recs = listar_recomendaciones()
    rec_options = ["Escribir manualmente"] + [f"{r[1]} · {r[2]}" for r in recs]
    rec_map = {f"{r[1]} · {r[2]}": r[3] for r in recs}

    # La foto es opcional. Se pueden seleccionar varias desde galería.
    # Al agregar el hallazgo se incrementa el nonce y Streamlit crea un uploader/cámara limpio.
    adjuntar_foto = st.toggle(
        "📎 Adjuntar foto(s) a esta recomendación (opcional)",
        value=False,
        key=f"adjuntar_foto_hallazgo_{st.session_state.foto_widget_nonce}"
    )

    fotos = []
    if adjuntar_foto:
        modo_foto = st.radio(
            "Origen de las fotos",
            ["📷 Abrir cámara", "🖼️ Elegir de galería"],
            horizontal=True,
            key=f"modo_foto_hallazgo_{st.session_state.foto_widget_nonce}"
        )
        if modo_foto == "📷 Abrir cámara":
            foto_camara = st.camera_input(
                "Tomar foto para esta recomendación",
                key=f"camara_hallazgo_{st.session_state.foto_widget_nonce}"
            )
            if foto_camara:
                fotos = [foto_camara]
            st.caption("Con cámara se toma una foto por vez. Para adjuntar varias juntas, elegí Galería.")
        else:
            fotos = st.file_uploader(
                "Elegir una o varias fotos para esta recomendación",
                type=["jpg", "jpeg", "png"],
                accept_multiple_files=True,
                key=f"galeria_hallazgo_{st.session_state.foto_widget_nonce}"
            ) or []

    # Recomendación fuera del form para poder completar el texto inmediatamente al seleccionarla.
    def actualizar_recomendacion_frecuente():
        seleccion = st.session_state.get("rec_sel_hallazgo", "Escribir manualmente")
        st.session_state["recomendacion_hallazgo"] = "" if seleccion == "Escribir manualmente" else rec_map.get(seleccion, "")

    st.selectbox(
        "Recomendación frecuente",
        rec_options,
        key="rec_sel_hallazgo",
        on_change=actualizar_recomendacion_frecuente
    )
    recomendacion_manual = st.text_area(
        "Recomendación técnica",
        key="recomendacion_hallazgo",
        height=130,
        help="Al elegir una recomendación frecuente el texto se completa automáticamente y podés editarlo."
    )

    with st.form("form_hallazgo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            sector = st.text_input("Sector")
            riesgo = st.text_input("Riesgo asociado")
            prioridad = st.selectbox("Prioridad", ["Alta", "Media", "Baja", "Observación"])
            plazo = st.text_input("Plazo sugerido", value="Inmediato / A definir")
        with c2:
            observacion = st.text_area("Observación detectada", height=120)

        agregar = st.form_submit_button("➕ Agregar hallazgo")
        if agregar:
            recomendacion = (recomendacion_manual or "").strip()

            foto_paths = []
            if adjuntar_foto and fotos:
                for idx_foto, foto in enumerate(fotos, start=1):
                    nombre_original = getattr(foto, "name", f"foto_{idx_foto}.jpg")
                    nombre = f"{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}_{idx_foto}_{nombre_original}"
                    nombre = "".join(c for c in nombre if c.isalnum() or c in "._- ")
                    foto_path = UPLOADS / nombre
                    with open(foto_path, "wb") as f:
                        f.write(foto.getbuffer())
                    foto_paths.append(str(foto_path))

            st.session_state.hallazgos.append({
                "sector": sector,
                "observacion": observacion,
                "riesgo": riesgo,
                "recomendacion": recomendacion,
                "prioridad": prioridad,
                "plazo": plazo,
                "foto_paths": foto_paths,
                "foto_path": foto_paths[0] if foto_paths else None,
            })
            # Limpia realmente los widgets de fotos y la recomendación para el próximo hallazgo.
            st.session_state.foto_widget_nonce += 1
            st.session_state["rec_sel_hallazgo"] = "Escribir manualmente"
            st.session_state["recomendacion_hallazgo"] = ""
            st.rerun()

    if st.session_state.hallazgos:
        for i, h in enumerate(st.session_state.hallazgos, start=1):
            with st.container(border=True):
                st.markdown(f"### Hallazgo {i} · {h.get('prioridad','')}")
                fotos_preview = h.get("foto_paths") or ([h.get("foto_path")] if h.get("foto_path") else [])
                if fotos_preview:
                    st.image(fotos_preview, use_container_width=True)
                st.write(f"**Observación:** {h.get('observacion','')}")
                st.write(f"**Recomendación:** {h.get('recomendacion','')}")
                st.caption(f"Sector: {h.get('sector','')} · Riesgo: {h.get('riesgo','')} · Plazo: {h.get('plazo','')}")
                if st.button("🗑️ Eliminar este hallazgo", key=f"del_h_{i}"):
                    borrado = st.session_state.hallazgos.pop(i-1)
                    try:
                        fotos_borrar = borrado.get("foto_paths") or ([borrado.get("foto_path")] if borrado.get("foto_path") else [])
                        for foto_borrar in fotos_borrar:
                            if foto_borrar:
                                Path(foto_borrar).unlink(missing_ok=True)
                    except Exception:
                        pass
                    st.rerun()

        c1, c2 = st.columns(2)
        with c1:
            if st.button("📄 Generar PDF", type="primary"):
                if not cliente_nombre.strip():
                    st.error("Completá el cliente / razón social antes de generar el PDF.")
                elif not obra_nombre.strip():
                    st.error("Completá la obra / establecimiento antes de generar el PDF.")
                else:
                    cliente_id = obtener_o_crear_cliente(
                        cliente_nombre,
                        cliente_cuit,
                        cliente_contacto,
                        cliente_telefono,
                        cliente_email,
                        observaciones_cliente_obra,
                    )
                    obra_id = obtener_o_crear_obra(
                        cliente_id,
                        obra_nombre,
                        direccion,
                        contratista,
                        observaciones_cliente_obra,
                    )
                    datos = {
                        "cliente_nombre": cliente_nombre.strip(),
                        "obra_nombre": obra_nombre.strip(),
                        "direccion": direccion.strip(),
                        "contratista": contratista.strip(),
                        "fecha": fecha_visita.strftime("%d/%m/%Y"),
                        "tecnico": tecnico,
                        "objetivo": objetivo,
                        "observaciones_generales": observaciones_generales,
                        "conclusion": conclusion,
                    }
                    pdf_path = generar_pdf(datos, st.session_state.hallazgos)
                    guardar_reporte(cliente_id, obra_id, datos["fecha"], tecnico, str(pdf_path))
                    st.session_state.ultimo_pdf = str(pdf_path)
                    st.success("PDF generado. Cliente, obra e historial guardados automáticamente.")
        with c2:
            if st.button("🧹 Limpiar hallazgos"):
                st.session_state.hallazgos = []
                st.session_state.ultimo_pdf = None
                st.rerun()

        if st.session_state.ultimo_pdf:
            ultimo = Path(st.session_state.ultimo_pdf)
            if ultimo.exists():
                st.success("✅ Reporte listo para descargar o compartir desde el teléfono.")
                st.download_button(
                    "⬇️ Descargar / compartir PDF",
                    data=ultimo.read_bytes(),
                    file_name=ultimo.name,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                    key="ultimo_pdf_descarga"
                )
                st.caption("En Samsung o iPhone, al abrir/descargar el PDF podés usar Compartir para enviarlo por WhatsApp, Mail o Drive.")
    else:
        st.info("Todavía no cargaste hallazgos.")
