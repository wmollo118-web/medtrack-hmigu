# ============================================================
#  MedTrack Bio — Sistema de Gestión de Equipos Médicos
#  H.M.I. Germán Urquidi · Unidad de Bioingeniería
#  Versión 1.0 — 2026
# ============================================================

import streamlit as st
import base64
import json
import qrcode
import io
from pathlib import Path
from datetime import datetime, date
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

# PDF generation
def generar_pdf_informe(datos: dict) -> bytes:
    """Genera PDF del informe técnico usando HTML + weasyprint si está disponible,
    o un PDF mínimo con bytes puros como fallback."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        azul = colors.HexColor("#0d2656")
        azul2 = colors.HexColor("#1a56a8")
        gris  = colors.HexColor("#f0f4fa")

        title_style = ParagraphStyle("title", parent=styles["Heading1"],
                                     fontSize=16, textColor=azul,
                                     spaceAfter=4, alignment=TA_CENTER)
        sub_style   = ParagraphStyle("sub", parent=styles["Normal"],
                                     fontSize=9, textColor=colors.grey,
                                     spaceAfter=2, alignment=TA_CENTER)
        sect_style  = ParagraphStyle("sect", parent=styles["Normal"],
                                     fontSize=10, textColor=colors.white,
                                     fontName="Helvetica-Bold", spaceAfter=4)
        body_style  = ParagraphStyle("body", parent=styles["Normal"],
                                     fontSize=9, textColor=colors.HexColor("#222"),
                                     leading=14)
        label_style = ParagraphStyle("label", parent=styles["Normal"],
                                     fontSize=7.5, textColor=colors.grey,
                                     fontName="Helvetica-Bold")

        elems = []

        # ── Header ──────────────────────────────────────────────────────────
        elems.append(Paragraph("HOSPITAL MATERNO INFANTIL &quot;GERMÁN URQUIDI&quot;", sub_style))
        elems.append(Paragraph("Unidad de Bioingeniería · Cochabamba, Bolivia", sub_style))
        elems.append(Spacer(1, 6))
        elems.append(Paragraph(datos.get("tipo_doc","INFORME TÉCNICO"), title_style))
        elems.append(HRFlowable(width="100%", thickness=2, color=azul2))
        elems.append(Spacer(1, 10))

        # ── Datos del equipo ─────────────────────────────────────────────────
        def sec_header(txt):
            t = Table([[Paragraph(txt, sect_style)]], colWidths=[17*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1), azul2),
                ("TOPPADDING",(0,0),(-1,-1),5),
                ("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),8),
            ]))
            return t

        def campo(label, val, w1=4*cm, w2=4*cm):
            return [Paragraph(label, label_style), Paragraph(str(val), body_style)]

        elems.append(sec_header("DATOS DEL EQUIPO"))
        elems.append(Spacer(1,6))
        eq_data = [
            ["EQUIPO", datos.get("equipo",""), "MARCA", datos.get("marca","")],
            ["MODELO", datos.get("modelo",""), "Nº SERIE", datos.get("serie","")],
            ["FECHA",  datos.get("fecha",""),  "ESTADO",  datos.get("estado","")],
            ["SERVICIO", datos.get("servicio",""), "CÓD. BIEN", datos.get("cod_bien","")],
        ]
        col_w = [3*cm, 5.5*cm, 3*cm, 5.5*cm]
        tbl = Table(eq_data, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
            ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("TEXTCOLOR",(0,0),(0,-1),colors.grey),
            ("TEXTCOLOR",(2,0),(2,-1),colors.grey),
            ("BACKGROUND",(0,0),(-1,-1),gris),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, gris]),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
        ]))
        elems.append(tbl)
        elems.append(Spacer(1,10))

        # ── Tipo de mantenimiento ────────────────────────────────────────────
        elems.append(sec_header("TIPO DE MANTENIMIENTO"))
        elems.append(Spacer(1,6))
        tipos_sel = datos.get("tipos",[])
        todos_tipos = ["Revisión Hardware","Revisión Software","Revisión Sistema Eléctrico",
                       "Limpieza y Lubricación Sistema Mecánico","Revisión General Funcionamiento",
                       "Ajuste de Piezas","Inspección Interna del Equipo","Inspección Externa del Equipo"]
        tipo_rows = []
        for i in range(0, len(todos_tipos), 2):
            row = []
            for j in range(2):
                if i+j < len(todos_tipos):
                    t = todos_tipos[i+j]
                    check = "☑" if t in tipos_sel else "☐"
                    row.append(Paragraph(f"{check}  {t}", body_style))
                else:
                    row.append(Paragraph("", body_style))
            tipo_rows.append(row)
        tbl2 = Table(tipo_rows, colWidths=[8.5*cm, 8.5*cm])
        tbl2.setStyle(TableStyle([
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("TOPPADDING",(0,0),(-1,-1),5),
            ("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, gris]),
        ]))
        elems.append(tbl2)
        elems.append(Spacer(1,10))

        # ── Descripción ──────────────────────────────────────────────────────
        elems.append(sec_header("DESCRIPCIÓN DEL TRABAJO REALIZADO"))
        elems.append(Spacer(1,6))
        desc_tbl = Table([[Paragraph(datos.get("descripcion",""), body_style)]],
                          colWidths=[17*cm])
        desc_tbl.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("TOPPADDING",(0,0),(-1,-1),8),
            ("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("MINROWHEIGHT",(0,0),(-1,-1),60),
        ]))
        elems.append(desc_tbl)
        elems.append(Spacer(1,10))

        # ── Recomendaciones ──────────────────────────────────────────────────
        elems.append(sec_header("RECOMENDACIONES"))
        elems.append(Spacer(1,6))
        rec_tbl = Table([[Paragraph(datos.get("recomendaciones",""), body_style)]],
                         colWidths=[17*cm])
        rec_tbl.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("TOPPADDING",(0,0),(-1,-1),8),
            ("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),8),
            ("MINROWHEIGHT",(0,0),(-1,-1),50),
        ]))
        elems.append(rec_tbl)
        elems.append(Spacer(1,16))

        # ── Firmas ───────────────────────────────────────────────────────────
        firma_data = [
            [Paragraph("____________________________", body_style),
             Paragraph("____________________________", body_style)],
            [Paragraph(datos.get("biomed",""), ParagraphStyle("fb",parent=body_style,fontName="Helvetica-Bold",fontSize=9)),
             Paragraph(datos.get("jefe",""), ParagraphStyle("fb",parent=body_style,fontName="Helvetica-Bold",fontSize=9))],
            [Paragraph("Biomédico Responsable", label_style),
             Paragraph("Responsable de la Unidad", label_style)],
        ]
        firma_tbl = Table(firma_data, colWidths=[8.5*cm, 8.5*cm])
        firma_tbl.setStyle(TableStyle([
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("TOPPADDING",(0,0),(-1,-1),4),
        ]))
        elems.append(firma_tbl)

        # ── Footer ───────────────────────────────────────────────────────────
        elems.append(Spacer(1,12))
        elems.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#aaa")))
        elems.append(Paragraph(f"MedTrack v1.0 · 2026 — Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                ParagraphStyle("ft",parent=styles["Normal"],fontSize=7,
                                               textColor=colors.grey,alignment=TA_CENTER)))

        doc.build(elems)
        return buf.getvalue()

    except ImportError:
        # Fallback: plain text PDF-like content wrapped in bytes
        eq   = datos.get("equipo","")
        sep  = "="*50
        desc = datos.get("descripcion","")
        rec  = datos.get("recomendaciones","")
        bio  = datos.get("biomed","")
        txt  = (
            f"INFORME TÉCNICO - H.M.I. GERMAN URQUIDI\n"
            f"Unidad de Bioingeniería\n"
            f"{sep}\n"
            f"Equipo: {eq}\n"
            f"Marca: {datos.get('marca','')} / Modelo: {datos.get('modelo','')}\n"
            f"Serie: {datos.get('serie','')} / Código: {datos.get('cod_bien','')}\n"
            f"Fecha: {datos.get('fecha','')} / Estado: {datos.get('estado','')}\n"
            f"Servicio: {datos.get('servicio','')}\n"
            f"{sep}\nDESCRIPCIÓN:\n{desc}\n"
            f"{sep}\nRECOMENDACIONES:\n{rec}\n"
            f"{sep}\nBiomédico: {bio}\n"
        )
        return txt.encode("utf-8")


def generar_pdf_inicio_proceso(datos: dict) -> bytes:
    """Genera PDF del inicio de proceso de compra."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        azul  = colors.HexColor("#0d2656")
        azul2 = colors.HexColor("#1a56a8")
        gris  = colors.HexColor("#f0f4fa")

        title_s = ParagraphStyle("t",parent=styles["Heading1"],fontSize=14,
                                  textColor=azul,alignment=TA_CENTER,spaceAfter=4)
        sub_s   = ParagraphStyle("s",parent=styles["Normal"],fontSize=8.5,
                                  textColor=colors.grey,alignment=TA_CENTER,spaceAfter=2)
        body_s  = ParagraphStyle("b",parent=styles["Normal"],fontSize=9,leading=13)
        lbl_s   = ParagraphStyle("l",parent=styles["Normal"],fontSize=7.5,
                                  textColor=colors.grey,fontName="Helvetica-Bold")
        bold_s  = ParagraphStyle("bo",parent=styles["Normal"],fontSize=9,
                                  fontName="Helvetica-Bold")
        sect_s  = ParagraphStyle("se",parent=styles["Normal"],fontSize=10,
                                  textColor=colors.white,fontName="Helvetica-Bold")

        def sec_hdr(txt):
            t = Table([[Paragraph(txt, sect_s)]], colWidths=[17*cm])
            t.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,-1),azul2),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),8),
            ]))
            return t

        elems = []
        elems.append(Paragraph("HOSPITAL MATERNO INFANTIL &quot;GERMÁN URQUIDI&quot;", sub_s))
        elems.append(Paragraph("Unidad de Bioingeniería · Cochabamba, Bolivia", sub_s))
        elems.append(Spacer(1,4))
        elems.append(Paragraph("COMUNICACIÓN INTERNA", title_s))
        elems.append(Paragraph("INICIO DE PROCESO DE COMPRA", title_s))
        elems.append(HRFlowable(width="100%",thickness=2,color=azul2))
        elems.append(Spacer(1,8))

        # Encabezado CI
        ci_data = [
            [Paragraph("CITE:", lbl_s), Paragraph(datos.get("cite",""), body_s),
             Paragraph("FECHA:", lbl_s), Paragraph(datos.get("fecha",""), body_s)],
            [Paragraph("A:", lbl_s), Paragraph(datos.get("para",""), body_s), "", ""],
            [Paragraph("VÍA:", lbl_s), Paragraph(datos.get("via",""), body_s), "", ""],
            [Paragraph("DE:", lbl_s), Paragraph(datos.get("de_",""), body_s), "", ""],
            [Paragraph("MOTIVO:", lbl_s), Paragraph(datos.get("motivo",""), bold_s), "", ""],
        ]
        ci_tbl = Table(ci_data, colWidths=[2*cm,7*cm,2*cm,6*cm])
        ci_tbl.setStyle(TableStyle([
            ("SPAN",(1,1),(3,1)),("SPAN",(1,2),(3,2)),
            ("SPAN",(1,3),(3,3)),("SPAN",(1,4),(3,4)),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white, gris]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
        ]))
        elems.append(ci_tbl)
        elems.append(Spacer(1,10))

        elems.append(sec_hdr("DESCRIPCIÓN / JUSTIFICACIÓN TÉCNICA"))
        elems.append(Spacer(1,6))
        cuerpo_tbl = Table([[Paragraph(datos.get("cuerpo",""), body_s)]], colWidths=[17*cm])
        cuerpo_tbl.setStyle(TableStyle([
            ("BOX",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
            ("LEFTPADDING",(0,0),(-1,-1),8),("MINROWHEIGHT",(0,0),(-1,-1),60),
        ]))
        elems.append(cuerpo_tbl)
        elems.append(Spacer(1,10))

        elems.append(sec_hdr("DATOS DE LA SOLICITUD"))
        elems.append(Spacer(1,6))
        sol_data = [
            ["Precio Referencial (Bs.)", datos.get("precio",""), "Plazo entrega", datos.get("plazo","")],
            ["Categoría Prog.", datos.get("cat_prog",""), "Partida Presup.", datos.get("partida","")],
            ["Fuente", datos.get("fuente",""), "Organismo", datos.get("organismo","")],
            ["Método de selección", datos.get("metodo",""), "", ""],
        ]
        sol_tbl = Table(sol_data, colWidths=[4*cm,4.5*cm,4*cm,4.5*cm])
        sol_tbl.setStyle(TableStyle([
            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
            ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8.5),
            ("TEXTCOLOR",(0,0),(0,-1),colors.grey),
            ("TEXTCOLOR",(2,0),(2,-1),colors.grey),
            ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[colors.white,gris]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
            ("SPAN",(1,3),(3,3)),
        ]))
        elems.append(sol_tbl)
        elems.append(Spacer(1,10))

        # Items
        items = datos.get("items",[])
        if items:
            elems.append(sec_hdr("ESPECIFICACIONES TÉCNICAS"))
            elems.append(Spacer(1,6))
            item_rows = [[
                Paragraph("ITEM", lbl_s),
                Paragraph("DESCRIPCIÓN", lbl_s),
                Paragraph("CANT.", lbl_s),
                Paragraph("ESPECIFICACIONES", lbl_s),
            ]]
            for idx, it in enumerate(items):
                item_rows.append([
                    Paragraph(str(idx+1), body_s),
                    Paragraph(it.get("desc",""), body_s),
                    Paragraph(str(it.get("cant","1")), body_s),
                    Paragraph(it.get("esp",""), body_s),
                ])
            it_tbl = Table(item_rows, colWidths=[1.5*cm,5*cm,2*cm,8.5*cm])
            it_tbl.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0),azul),
                ("TEXTCOLOR",(0,0),(-1,0),colors.white),
                ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
                ("GRID",(0,0),(-1,-1),0.5,colors.HexColor("#dde4f0")),
                ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,gris]),
                ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
                ("LEFTPADDING",(0,0),(-1,-1),6),
                ("FONTSIZE",(0,0),(-1,-1),8.5),
            ]))
            elems.append(it_tbl)
            elems.append(Spacer(1,10))

        # Firmas
        firma_data = [
            [Paragraph("____________________________", body_s),
             Paragraph("____________________________", body_s)],
            [Paragraph(datos.get("elaborado",""), bold_s),
             Paragraph("", body_s)],
            [Paragraph(datos.get("cargo",""), lbl_s),
             Paragraph("Jefe Inmediato Superior", lbl_s)],
        ]
        f_tbl = Table(firma_data, colWidths=[8.5*cm,8.5*cm])
        f_tbl.setStyle(TableStyle([("ALIGN",(0,0),(-1,-1),"CENTER"),("TOPPADDING",(0,0),(-1,-1),4)]))
        elems.append(f_tbl)
        elems.append(Spacer(1,10))
        elems.append(HRFlowable(width="100%",thickness=0.5,color=colors.HexColor("#aaa")))
        elems.append(Paragraph(f"MedTrack v1.0 · 2026 — Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}",
                                ParagraphStyle("ft",parent=styles["Normal"],fontSize=7,
                                               textColor=colors.grey,alignment=TA_CENTER)))
        doc.build(elems)
        return buf.getvalue()

    except ImportError:
        txt = f"""INICIO DE PROCESO - H.M.I. GERMAN URQUIDI
CITE: {datos.get('cite','')}  FECHA: {datos.get('fecha','')}
A: {datos.get('para','')}
MOTIVO: {datos.get('motivo','')}
"""
        return txt.encode("utf-8")

# ── Configuración de página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="MedTrack — H.M.I. Germán Urquidi",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Helper: imagen a base64 ────────────────────────────────────────────────────
def img_to_b64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# ── CSS Global ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Reset ─────────────────────────────────────────────────── */
#MainMenu, footer, header { visibility: hidden; }
body, .stApp { background: #f0f4fa !important; }

/* ── Sidebar base ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #0d1b3e !important;
    min-width: 230px !important;
    max-width: 230px !important;
}
[data-testid="stSidebar"] * { color: #c8d6f0 !important; }

/* ── Sidebar nav buttons ────────────────────────────────────── */
[data-testid="stSidebar"] button[kind="secondary"],
[data-testid="stSidebar"] button[kind="primary"],
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.07) !important;
    color: #c8d6f0 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 8px 12px !important;
    margin-bottom: 4px !important;
    text-align: left !important;
    width: 100% !important;
    min-height: 40px !important;
    white-space: normal !important;
    line-height: 1.3 !important;
    transition: all 0.15s !important;
    box-shadow: none !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(26,86,168,0.5) !important;
    color: #ffffff !important;
    border-color: #1a56a8 !important;
}

/* ── Main area buttons ──────────────────────────────────────── */
.main .stButton button,
section[data-testid="stMain"] .stButton button {
    background: #1a56a8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: background 0.2s !important;
}
.main .stButton button:hover,
section[data-testid="stMain"] .stButton button:hover {
    background: #0d3d8a !important;
}

/* ── All form inputs WHITE ──────────────────────────────────── */
input, textarea,
.stTextInput input,
.stTextArea textarea,
div[data-baseweb="base-input"] input,
div[data-baseweb="textarea"] textarea {
    background: #ffffff !important;
    color: #1a2340 !important;
    border: 1.5px solid #c8d4e8 !important;
    border-radius: 8px !important;
}
input::placeholder, textarea::placeholder {
    color: #aab4c8 !important;
}
.stTextInput label, .stTextArea label,
.stSelectbox label, .stDateInput label {
    font-size: 0.8rem !important;
    color: #333 !important;
    font-weight: 600 !important;
}

/* ── Selectbox ──────────────────────────────────────────────── */
div[data-baseweb="select"] > div,
div[data-baseweb="select"] input {
    background: #ffffff !important;
    color: #1a2340 !important;
    border-color: #c8d4e8 !important;
}

/* ── Date input ─────────────────────────────────────────────── */
.stDateInput input {
    background: #ffffff !important;
    color: #1a2340 !important;
}

/* ── Metrics / cards ────────────────────────────────────────── */
.metric-card {
    background: #fff;
    border-radius: 10px;
    padding: 14px 16px;
    box-shadow: 0 1px 6px rgba(0,0,0,0.08);
    text-align: center;
}
.metric-num { font-size: 2rem; font-weight: 700; color: #0d2656; }
.metric-label { font-size: 0.78rem; color: #888; margin-top: 2px; }
.metric-sub { font-size: 0.7rem; color: #aaa; }

/* ── Badges ─────────────────────────────────────────────────── */
.badge { display:inline-block; padding:3px 10px; border-radius:20px; font-size:0.72rem; font-weight:600; }
.badge-pendiente  { background:#fff3cd; color:#856404; }
.badge-revision   { background:#cfe2ff; color:#084298; }
.badge-reparado   { background:#d1e7dd; color:#0a3622; }
.badge-alta       { background:#f8d7da; color:#842029; }
.badge-media      { background:#fff3cd; color:#856404; }
.badge-baja       { background:#d1e7dd; color:#0a3622; }

/* ── Table ──────────────────────────────────────────────────── */
.tabla-header {
    display:grid; background:#f8f9fa; border-radius:8px 8px 0 0;
    padding:10px 14px; font-size:0.78rem; font-weight:700; color:#444;
    border-bottom:2px solid #e0e0e0;
}

/* ── Card / section ─────────────────────────────────────────── */
.card { background:#fff; border-radius:12px; padding:20px; box-shadow:0 1px 8px rgba(0,0,0,0.07); margin-bottom:16px; }
.section-title { font-size:1.5rem; font-weight:700; color:#0d2656; margin-bottom:4px; }
.section-sub { font-size:0.85rem; color:#888; margin-bottom:20px; }

/* ── Activity / critical items ──────────────────────────────── */
.actividad-item { display:flex; gap:10px; align-items:flex-start; padding:8px 0; border-bottom:1px solid #f0f0f0; font-size:0.8rem; color:#444; }
.act-time { color:#aaa; font-size:0.72rem; white-space:nowrap; }
.equipo-critico { display:flex; gap:12px; align-items:flex-start; padding:10px 0; border-bottom:1px solid #f0f0f0; }
.eq-nombre { font-size:0.85rem; font-weight:600; color:#0d2656; }
.eq-detalle { font-size:0.75rem; color:#888; }

/* ── Form sections ──────────────────────────────────────────── */
.form-section { background:#fff; border-radius:10px; padding:18px 20px; box-shadow:0 1px 6px rgba(0,0,0,0.06); margin-bottom:14px; }
.form-title { font-size:0.92rem; font-weight:700; color:#0d2656; border-bottom:2px solid #1a56a8; padding-bottom:6px; margin-bottom:12px; }

/* ── Surgery cards ──────────────────────────────────────────── */
.cirugia-card {
    background:#fff; border-radius:12px; padding:16px 18px;
    box-shadow:0 2px 10px rgba(0,0,0,0.07); margin-bottom:10px;
    border-left:4px solid #1a56a8;
}
.cirugia-card.urgente { border-left-color:#dc3545; }
.cirugia-card.ingenieria { border-left-color:#ffc107; }
.cirugia-hora { font-size:1.1rem; font-weight:700; color:#0d2656; }
.cirugia-nombre { font-size:0.9rem; font-weight:600; color:#1a2340; margin:2px 0; }
.cirugia-detalle { font-size:0.76rem; color:#666; }
.cirugia-badge { display:inline-block; padding:3px 9px; border-radius:20px; font-size:0.7rem; font-weight:700; }
.cb-verde    { background:#d1e7dd; color:#0a3622; }
.cb-amarillo { background:#fff3cd; color:#856404; }
.cb-rojo     { background:#f8d7da; color:#842029; }
.cb-azul     { background:#cfe2ff; color:#084298; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  DATOS DEL SISTEMA
# ══════════════════════════════════════════════════════════════════════════════

USUARIOS = {
    "ing.ramirez":  {"password": "ingeniero1",  "nombre": "Ing. Denis Ramírez", "rol": "Encargado Bioingeniería", "tipo": "ingeniero"},
    "ing.flores":   {"password": "ingeniero2",  "nombre": "Ing. Flores",         "rol": "Bioingeniería",          "tipo": "ingeniero"},
    "dr.garcia":    {"password": "medico123",   "nombre": "Dr. García",          "rol": "Médico",                 "tipo": "medico"},
    "enf.torres":   {"password": "enfermera1",  "nombre": "Enf. Torres",         "rol": "Enfermera/o",            "tipo": "enfermera"},
}

EQUIPOS = [
    {"codigo":"A06032400026","nombre":"Desfibrilador MEDTRONIK LIFEPAK 12","servicio":"Quirófano 3","marca":"MEDTRONIK","modelo":"LIFEPAK 12","serie":"33586958","prioridad":"Alta","estado":"Pendiente","fecha":"23/06/2026 09:00","reporte":"REP-2026-002"},
    {"codigo":"SH2-59120043","nombre":"Bomba de Infusión Volumétrica MINDRAY BeneFusion","servicio":"Neonatología I (UCIN I)","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120043","prioridad":"Media","estado":"En revisión","fecha":"23/06/2026 07:45","reporte":"REP-2026-005"},
    {"codigo":"2C250917116","nombre":"Ventilador Neonatal COMEN V2","servicio":"Neonatología I (UCIN I)","marca":"COMEN","modelo":"V2","serie":"2C250917116","prioridad":"Alta","estado":"Pendiente","fecha":"23/06/2026 06:20","reporte":"REP-2026-001"},
    {"codigo":"DE671Y4710", "nombre":"Monitor Multiparamétrico PHILIPS MX550","servicio":"Terapia Intensiva","marca":"PHILIPS","modelo":"MX550","serie":"DE671Y4710","prioridad":"Baja","estado":"Reparado","fecha":"22/06/2026 14:20","reporte":"REP-2026-003"},
    {"codigo":"DAM053713",  "nombre":"Ecógrafo MINDRAY DC-80","servicio":"Ecografía","marca":"MINDRAY","modelo":"DC-80","serie":"DAM053713","prioridad":"Alta","estado":"Alta prioridad","fecha":"21/06/2026 11:10","reporte":"REP-2026-004"},
]

ACTIVIDAD = [
    {"icono":"🟢","hora":"23/06/2026 10:00","texto":"Nuevo reporte: Desfibrilador LIFEPAK 12"},
    {"icono":"🔵","hora":"23/06/2026 08:30","texto":"REP-2026-005 asignado a Bioingeniería"},
    {"icono":"🟡","hora":"23/06/2026 07:45","texto":"Cambio de estado a 'En revisión'"},
    {"icono":"🟢","hora":"22/06/2026 12:20","texto":"Monitor PHILIPS MX550 marcado como reparado"},
    {"icono":"🟢","hora":"21/06/2026 11:10","texto":"Nuevo reporte: Ecógrafo MINDRAY DC-80"},
]

SERVICIOS = ["Neonatología I (UCIN I)","Neonatología II (UCIN II)","Neonatología III (UCIN III)","Recién Nacidos","Quirófano 2","Quirófano 3","Quirófano 4","Quirófano Área Verde","Esterilización","Terapia Intensiva","Terapia Intermedia","Terapia Materna","Hospitalización","Emergencia","Ecografía","Laboratorio","Fisioterapia","Rayos X","Odontología","Gineco-Obstetricia","Oncología Quirúrgica","Nutrición","Electro-encefalografía","Electrocardiograma","Citología–Patología","Depósito Neonatología"]

PROTOCOLOS = {
    "Ventilador COMEN V2": {
        "equipo": "Ventilador Neonatal", "marca": "COMEN", "modelo": "V2",
        "serie": "2C250917116", "area": "Neonatología I", "frecuencia": "Semestral",
        "items": {
            "APARIENCIA": [
                "Inspeccionar condiciones ambientales (temperatura, humedad, ventilación)",
                "Verificar limpieza externa",
                "Revisar exterior: estructura, carcasa, panel de control y pantalla",
                "Revisar estado de mangueras, circuitos respiratorios y conexiones",
                "Revisar estado de filtros bacterianos y de aire",
                "Limpieza integral externa",
                "Inspeccionar cables, sensores y conectores visibles",
                "Inspeccionar sistema de suministro de gases (O₂ y aire)",
            ],
            "FUNCIONAMIENTO": [
                "Comprobar funcionamiento de botones, controles, pantalla y alarmas",
                "Verificar sistemas de protección (interruptores, fusibles)",
                "Verificar correcto ensamblaje del circuito respiratorio",
                "Encender equipo y verificar activación de indicadores luminosos",
                "Revisar parámetros ventilatorios (volumen, presión, flujo)",
                "Verificar funcionamiento de sensores (flujo, presión, oxígeno)",
                "Comprobar modos de ventilación (controlado, asistido, etc.)",
                "Evaluar respuesta ante cambios de parámetros configurados",
            ],
            "DESEMPEÑO": [
                "Verificación de conexiones eléctricas",
                "Verificación del cumplimiento de indicadores visuales y alarmas",
                "Revisión de pantalla, switches o pulsadores",
                "Verificación del funcionamiento del sistema de ventilación",
                "Verificación de la precisión de parámetros ventilatorios",
                "Comprobación de estabilidad en entrega de volumen y presión",
                "Verificación del funcionamiento continuo sin fallas",
                "Lubricar elementos mecánicos (ruedas, soportes)",
            ],
            "SEGURIDAD": [
                "Verificar antecedentes de mantenimiento preventivo o correctivo",
                "Inspección de posibles daños eléctricos o mecánicos",
                "Verificar correcto funcionamiento de alarmas (alta/baja presión, apnea)",
                "Verificación de sistemas de seguridad del equipo",
                "Verificar estado del sistema eléctrico (cable, tomacorriente)",
                "Verificar integridad del sistema de suministro de gases",
                "Realizar pruebas funcionales generales",
                "Verificar ausencia de fugas, ruidos anormales o fallas",
            ],
        }
    },
    "Monitor Multiparamétrico PHILIPS MX550": {
        "equipo": "Monitor Multiparamétrico", "marca": "PHILIPS", "modelo": "MX550",
        "serie": "DE671Y4710", "area": "Terapia Materna", "frecuencia": "Semestral",
        "items": {
            "APARIENCIA": [
                "Inspección externa general del equipo y accesorios",
                "Verificar limpieza de conectores y puertos",
                "Revisar estado de cables de sensores (SpO₂, PA, FC, Temperatura)",
                "Inspeccionar pantalla y panel de control",
            ],
            "FUNCIONAMIENTO": [
                "Verificar lectura estable del sensor de temperatura",
                "Comprobar medición de presión arterial no invasiva",
                "Verificar oximetría de pulso (SpO₂) y frecuencia cardíaca",
                "Probar alarmas visuales y sonoras",
                "Verificar carga de batería interna",
            ],
            "DESEMPEÑO": [
                "Comprobar precisión de parámetros fisiológicos",
                "Verificar autonomía de batería (mínimo 30 min)",
                "Verificar conectividad con central de monitoreo si aplica",
            ],
            "SEGURIDAD": [
                "Revisar cable de alimentación eléctrica",
                "Verificar sistema de alarmas activas",
                "Comprobar que el equipo queda conectado a la red al finalizar el turno",
            ],
        }
    },
    "Desfibrilador MEDTRONIK LIFEPAK 12": {
        "equipo": "Desfibrilador", "marca": "MEDTRONIK", "modelo": "LIFEPAK 12",
        "serie": "33586958", "area": "Quirófano 3", "frecuencia": "Trimestral",
        "items": {
            "APARIENCIA": [
                "Inspección externa general del equipo",
                "Verificar limpieza de palas y electrodos",
                "Revisar estado de cables y conectores",
                "Inspeccionar pantalla y panel de control",
            ],
            "FUNCIONAMIENTO": [
                "Verificar encendido y auto-diagnóstico",
                "Comprobar carga y descarga de energía (modo prueba interna)",
                "Verificar todos los modos: DEA, sincronizado, marcapasos",
                "Comprobar alarmas visuales y sonoras",
                "Verificar registro de ECG en papel",
                "Comprobar estado y carga de batería",
            ],
            "DESEMPEÑO": [
                "Verificar precisión de energía entregada",
                "Comprobar sincronización con señal ECG",
                "Verificar funcionamiento del marcapasos externo",
            ],
            "SEGURIDAD": [
                "Verificar seguro de carga y descarga",
                "Comprobar aislamiento eléctrico de palas",
                "Verificar disponibilidad inmediata del equipo",
                "Verificar fecha de vencimiento de electrodos y consumibles",
            ],
        }
    },
}

INVENTARIO_COMPLETO = [
    # ── Neonatología I (UCIN I) ──────────────────────────────────────────────
    {"cod":"A0250813759E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813759E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813767E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813767E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813787E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813787E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813792E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813792E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813740E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813740E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813751E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813751E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813782E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813782E","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"C0250813361N","equipo":"Servocuna Neonatal BNG Medical BN300","marca":"BNG Medical","modelo":"BN300","serie":"C0250813361N","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"C0250813350N","equipo":"Servocuna Neonatal BNG Medical BN300","marca":"BNG Medical","modelo":"BN300","serie":"C0250813350N","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"C0250813364N","equipo":"Servocuna Neonatal BNG Medical BN300","marca":"BNG Medical","modelo":"BN300","serie":"C0250813364N","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"2C250916071","equipo":"Ventilador Neonatal COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250916071","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250916060","equipo":"Ventilador Neonatal COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250916060","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250917100","equipo":"Ventilador Neonatal COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250917100","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250917116","equipo":"Ventilador Neonatal Mecánico COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250917116","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250916035","equipo":"Ventilador Neonatal Mecánico COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250916035","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250915030","equipo":"Ventilador Neonatal Mecánico COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250915030","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C350916076","equipo":"Ventilador Neonatal Mecánico COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C350916076","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120043","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120043","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120201","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120201","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120246","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120246","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120415","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120415","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120250","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120250","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120273","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120273","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SM3-59064749","equipo":"Bomba de Infusión a Jeringa MINDRAY BeneFusion uSP","marca":"MINDRAY","modelo":"BeneFusion uSP","serie":"SM3-59064749","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SM3-59064692","equipo":"Bomba de Infusión a Jeringa MINDRAY BeneFusion uSP","marca":"MINDRAY","modelo":"BeneFusion uSP","serie":"SM3-59064692","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SM3-59064610","equipo":"Bomba de Infusión a Jeringa MINDRAY BeneFusion uSP","marca":"MINDRAY","modelo":"BeneFusion uSP","serie":"SM3-59064610","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SM3-59064672","equipo":"Bomba de Infusión a Jeringa MINDRAY BeneFusion uSP","marca":"MINDRAY","modelo":"BeneFusion uSP","serie":"SM3-59064672","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"260597-M25609480023","equipo":"Monitor de Signos Vitales EDAN Elite V6","marca":"EDAN","modelo":"Elite V6","serie":"260597-M25609480023","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"260597-M25609480009","equipo":"Monitor de Signos Vitales EDAN Elite V6","marca":"EDAN","modelo":"Elite V6","serie":"260597-M25609480009","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A-06-0320-00018","equipo":"Monitor Multiparamétrico NIHON KOHDEN BSM-3562","marca":"NIHON KOHDEN","modelo":"BSM-3562","serie":"8280","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A-06-0325-00041","equipo":"Desfibrilador NIHON KOHDEN TEC-5621E","marca":"NIHON KOHDEN","modelo":"TEC-5621E","serie":"561","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A06034100011","equipo":"Incubadora de Transporte Híbrida ATOM DUAL INCU I","marca":"ATOM","modelo":"DUAL INCU I","serie":"2750353","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A06036400064","equipo":"Ventilador Neonatal Alta Frecuencia SLE SLE600","marca":"SLE","modelo":"SLE600","serie":"6030762025","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"3000211120","equipo":"Oxímetro de Pulso Neonatal MASIMO Rad-97","marca":"MASIMO","modelo":"Rad-97","serie":"3000211120","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A06036802347","equipo":"CPAP de Burbuja FANEM 1150S","marca":"FANEM","modelo":"1150S","serie":"JAM046404","servicio":"Neonatología I (UCIN I)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    # ── Neonatología II (UCIN II) ────────────────────────────────────────────
    {"cod":"A0250813741E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813741E","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A0250813748E","equipo":"Incubadora BNG Medical EscoLa 3000","marca":"BNG Medical","modelo":"EscoLa 3000","serie":"A0250813748E","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"2C250915026","equipo":"Ventilador Neonatal COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250915026","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"2C250916031","equipo":"Ventilador Neonatal COMEN V2","marca":"COMEN","modelo":"V2","serie":"2C250916031","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"SH2-59120740","equipo":"Bomba de Infusión Volumétrica MINDRAY BeneFusion eVP","marca":"MINDRAY","modelo":"BeneFusion eVP","serie":"SH2-59120740","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A-06-0325-00040","equipo":"Monitor Multiparamétrico HILLMED HM-9000FP","marca":"HILLMED","modelo":"HM-9000FP","serie":"HM2004T29","servicio":"Neonatología II (UCIN II)","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    # ── Quirófano 2 ──────────────────────────────────────────────────────────
    {"cod":"A06000100001","equipo":"Lámpara Cialítica Doble Cúpula ADVANCED SL 700","marca":"ADVANCED","modelo":"SL 700/700 LC","serie":"17119143","servicio":"Quirófano 2","prioridad":"A","estado":"REGULAR","frecuencia":"ANUAL"},
    {"cod":"A06037900014","equipo":"Equipo de Anestesia DRAGER FABIUS GS","marca":"DRAGER","modelo":"FABIUS GS","serie":"ARYL-0092","servicio":"Quirófano 2","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06039400002","equipo":"Carro Aspirador de Transporte UZUMKU VELA","marca":"UZUMKU","modelo":"VELA","serie":"5129020013","servicio":"Quirófano 2","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06025400001","equipo":"Unidad de Electrocirugía Monopolar/Bipolar ESU-400","marca":"","modelo":"ESU-400","serie":"PEHD16022642S","servicio":"Quirófano 2","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06034900001","equipo":"Mesa Quirúrgica ADVANCED OT 500","marca":"ADVANCED","modelo":"OT 500","serie":"E700A1-00049","servicio":"Quirófano 2","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    # ── Quirófano 3 ──────────────────────────────────────────────────────────
    {"cod":"A06000100002","equipo":"Lámpara Cialítica ADVANCED SL 700","marca":"ADVANCED","modelo":"SL 700/700 LC","serie":"17119144","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"ANUAL"},
    {"cod":"A06032400026","equipo":"Desfibrilador MEDTRONIK LIFEPAK 12","marca":"MEDTRONIK","modelo":"LIFEPAK 12","serie":"33586958","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06032500008","equipo":"Monitor Multiparamétrico MEK MP 1000NT PLUS","marca":"MEK","modelo":"MP 1000NT PLUS","serie":"NTP-10K-0552","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"SEMESTRAL"},
    {"cod":"A06036100019","equipo":"Electrobisturí UZUMCU EK-410","marca":"UZUMCU","modelo":"EK-410","serie":"5220000220","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06036200064","equipo":"Aspirador de Secreciones MEDICAL HEALTHCARE","marca":"MEDICAL HEALTHCARE","modelo":"","serie":"1100071243","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06040000001","equipo":"Carro de Paro TROLEY ET-1000","marca":"TROLEY","modelo":"ET-1000","serie":"160351850EB3026","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06037900020","equipo":"Máquina de Anestesia DRAGER FABIUS PREMIUM","marca":"DRAGER","modelo":"FABIUS PREMIUM","serie":"ASFK-0063","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06038000003","equipo":"Equipo de Laparoscopía STORZ 20212120","marca":"STORZ","modelo":"20212120","serie":"FG604075-P","servicio":"Quirófano 3","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    # ── Quirófano 4 ──────────────────────────────────────────────────────────
    {"cod":"A06033300399","equipo":"Lámpara Cialítica DAIKYO 7725","marca":"DAIKYO","modelo":"7725","serie":"003V039","servicio":"Quirófano 4","prioridad":"A","estado":"REGULAR","frecuencia":"ANUAL"},
    {"cod":"A06035000002","equipo":"Mesa Quirúrgica BARRFAB APG-IPX4","marca":"BARRFAB","modelo":"APG-IPX4","serie":"70661012","servicio":"Quirófano 4","prioridad":"A","estado":"REGULAR","frecuencia":"ANUAL"},
    {"cod":"A06036100015","equipo":"Electrobisturí MIZUHO IKA KOGTO TRC1500B","marca":"MIZUHO IKA KOGTO","modelo":"TRC1500B","serie":"150110723","servicio":"Quirófano 4","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06036801688","equipo":"Monitor Multiparamétrico DRAGER INFINITY C700","marca":"DRAGER","modelo":"INFINITY C700","serie":"TPAA229952","servicio":"Quirófano 4","prioridad":"A","estado":"REGULAR","frecuencia":"SEMESTRAL"},
    {"cod":"A06037900017","equipo":"Equipo de Anestesia DRAGER TITUS","marca":"DRAGER","modelo":"TITUS","serie":"ARMC-0010","servicio":"Quirófano 4","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    # ── Quirófano Área Verde ─────────────────────────────────────────────────
    {"cod":"A06036801647","equipo":"Equipo de Histeroscopia OLYMPUS HYF TYPE 1T","marca":"OLYMPUS","modelo":"HYF TYPE 1T","serie":"1301546","servicio":"Quirófano Área Verde","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    # ── Esterilización ───────────────────────────────────────────────────────
    {"cod":"A06001300025","equipo":"Autoclave SAKURA A-IIIS-B9","marca":"SAKURA","modelo":"A-IIIS-B9","serie":"3078177","servicio":"Esterilización","prioridad":"A","estado":"REGULAR","frecuencia":"CUATRIMESTRAL"},
    {"cod":"A06001300035","equipo":"Autoclave a Vapor PHONIX 39206S","marca":"PHONIX","modelo":"39206S","serie":"7300","servicio":"Esterilización","prioridad":"A","estado":"BUENO","frecuencia":"CUATRIMESTRAL"},
    # ── Recién Nacidos ───────────────────────────────────────────────────────
    {"cod":"A06032000026","equipo":"Monitor de Signos Vitales Neonatal PC-900","marca":"","modelo":"PC-900","serie":"J0100OH01371","servicio":"Recién Nacidos","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06034300002","equipo":"Cuna de Calor Radiante FANEM 2085","marca":"FANEM","modelo":"2085","serie":"SAJ19826","servicio":"Recién Nacidos","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06034300001","equipo":"Incubadora Portátil FANEM IT-158 TS","marca":"FANEM","modelo":"IT-158 TS","serie":"CF7277","servicio":"Recién Nacidos","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06036802315","equipo":"Resucitador Infantil FANEM BABYPUFF 1020","marca":"FANEM","modelo":"BABYPUFF 1020","serie":"TAI 08650","servicio":"Recién Nacidos","prioridad":"A","estado":"REGULAR","frecuencia":"SEMESTRAL"},
    # ── Emergencia ───────────────────────────────────────────────────────────
    {"cod":"A06032000016","equipo":"Monitor de Signos Vitales BIOMET BM5","marca":"BIOMET","modelo":"BM5","serie":"D8P1000125","servicio":"Emergencia","prioridad":"A","estado":"MALO","frecuencia":"SEMESTRAL"},
    {"cod":"A06032000015","equipo":"Monitor Desfibrilador BIOMET BM6","marca":"BIOMET","modelo":"BM6","serie":"D8P0900023","servicio":"Emergencia","prioridad":"A","estado":"MALO","frecuencia":"SEMESTRAL"},
    {"cod":"A06032500004","equipo":"Monitor Multiparamétrico NIHON KOHDEN PVM-2703","marca":"NIHON KOHDEN","modelo":"PVM-2703","serie":"105480","servicio":"Emergencia","prioridad":"A","estado":"MALO","frecuencia":"SEMESTRAL"},
    {"cod":"A06035200014","equipo":"Ecógrafo Doppler Color 4D PRASER K-30","marca":"PRASER","modelo":"K-30","serie":"F02V21DI18664","servicio":"Emergencia","prioridad":"A","estado":"REGULAR","frecuencia":"SEMESTRAL"},
    # ── Ecografía ────────────────────────────────────────────────────────────
    {"cod":"A06036802313","equipo":"Ecógrafo PHILIPS AFFINITY 70","marca":"PHILIPS","modelo":"AFFINITY 70","serie":"USD15F0507","servicio":"Ecografía","prioridad":"A","estado":"MALO","frecuencia":"SEMESTRAL"},
    {"cod":"DAM053713","equipo":"Ecógrafo MINDRAY DC-80","marca":"MINDRAY","modelo":"DC-80","serie":"DAM053713","servicio":"Ecografía","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    # ── Laboratorio ──────────────────────────────────────────────────────────
    {"cod":"A06040600002","equipo":"Contador Hematológico DYMIND DH76","marca":"DYMIND","modelo":"DH76","serie":"DM11052149002","servicio":"Laboratorio","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A06003900003","equipo":"Macrocentrífuga HETTICH ROTOFIX 32A","marca":"HETTICH","modelo":"ROTOFIX 32A","serie":"0027531-03","servicio":"Laboratorio","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06042100001","equipo":"Coagulómetro 4 Canales LABITEC COA DATA 4004","marca":"LABITEC","modelo":"COA DATA 4004","serie":"J2490102","servicio":"Laboratorio","prioridad":"A","estado":"REGULAR","frecuencia":"TRIMESTRAL"},
    {"cod":"A06042500001","equipo":"Analizador Química Sanguínea DIASYS MC-15","marca":"DIASYS","modelo":"MC-15","serie":"1489","servicio":"Laboratorio","prioridad":"A","estado":"BUENO","frecuencia":"TRIMESTRAL"},
    {"cod":"A06042600001","equipo":"Equipo Automatizado BIOERIFUX VITEK 2 COMPACT","marca":"BIOERIFUX","modelo":"VITEK 2 COMPACT","serie":"VK2C9998","servicio":"Laboratorio","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A06043700001","equipo":"Gasómetro con Lactado NOVA BIOMEDICAL","marca":"NOVA BIOMEDICAL","modelo":"#51360","serie":"5010423050310","servicio":"Laboratorio","prioridad":"A","estado":"BUENO","frecuencia":"CUATRIMESTRAL"},
    # ── Patología / Citología ────────────────────────────────────────────────
    {"cod":"A06017601073","equipo":"Microscopio Binocular RBSFA CX-31","marca":"RBSFA","modelo":"CX-31","serie":"1K40921","servicio":"Citología–Patología","prioridad":"B","estado":"MALO","frecuencia":"SEMESTRAL"},
    {"cod":"A06017601065","equipo":"Microscopio OLYMPUS CX31","marca":"OLYMPUS","modelo":"CX31","serie":"7J07369","servicio":"Citología–Patología","prioridad":"B","estado":"MALO","frecuencia":"TRIMESTRAL"},
    # ── Terapia Intensiva / Materna ──────────────────────────────────────────
    {"cod":"DE671Y4710","equipo":"Monitor Multiparamétrico PHILIPS MX550","marca":"PHILIPS","modelo":"MX550","serie":"DE671Y4710","servicio":"Terapia Intensiva","prioridad":"A","estado":"BUENO","frecuencia":"SEMESTRAL"},
    {"cod":"A06036801688","equipo":"Monitor Multiparamétrico DRAGER INFINITY C700","marca":"DRAGER","modelo":"INFINITY C700","serie":"TPAA229952","servicio":"Terapia Materna","prioridad":"A","estado":"REGULAR","frecuencia":"SEMESTRAL"},
]

# ══════════════════════════════════════════════════════════════════════════════
#  BASE DE DATOS SQLite
# ══════════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════════
#  BASE DE DATOS — PostgreSQL (Supabase)
# ══════════════════════════════════════════════════════════════════════════════
import psycopg2
import psycopg2.extras
import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:W1103218j21@db.qykihmlxuecrcupdcjtp.supabase.co:5432/postgres"
)

def get_conn():
    conn = psycopg2.connect(DATABASE_URL, connect_timeout=10)
    return conn


def init_db():
    """Crea las tablas si no existen y carga datos iniciales."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username    TEXT PRIMARY KEY,
            password    TEXT NOT NULL,
            nombre      TEXT NOT NULL,
            rol         TEXT NOT NULL,
            tipo        TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS reportes (
            reporte         TEXT PRIMARY KEY,
            codigo          TEXT,
            nombre          TEXT NOT NULL,
            servicio        TEXT,
            marca           TEXT,
            modelo          TEXT,
            serie           TEXT,
            prioridad       TEXT DEFAULT 'Media',
            estado          TEXT DEFAULT 'Pendiente',
            fecha           TEXT,
            descripcion     TEXT,
            reportado_por   TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS servicios (
            id       SERIAL PRIMARY KEY,
            nombre   TEXT NOT NULL UNIQUE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS inventario_extra (
            cod        TEXT PRIMARY KEY,
            equipo     TEXT NOT NULL,
            marca      TEXT,
            modelo     TEXT,
            serie      TEXT,
            servicio   TEXT,
            estado     TEXT DEFAULT 'BUENO',
            frecuencia TEXT DEFAULT 'SEMESTRAL',
            prioridad  TEXT DEFAULT 'A'
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS cirugias (
            id              TEXT PRIMARY KEY,
            fecha           TEXT NOT NULL,
            hora            TEXT NOT NULL,
            quirofano       TEXT,
            tipo            TEXT,
            cirujano        TEXT,
            anestesia       TEXT,
            estado          TEXT DEFAULT 'Programada',
            requiere_ing    INTEGER DEFAULT 0,
            equipo_esp      TEXT,
            obs             TEXT,
            programado_por  TEXT
        )
    """)

    conn.commit()

    # ── Seed usuarios ─────────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM usuarios")
    if c.fetchone()[0] == 0:
        for uname, udata in USUARIOS.items():
            c.execute(
                """INSERT INTO usuarios VALUES (%s,%s,%s,%s,%s)
                   ON CONFLICT (username) DO NOTHING""",
                (uname, udata["password"], udata["nombre"], udata["rol"], udata["tipo"])
            )
        conn.commit()

    # ── Seed reportes ─────────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM reportes")
    if c.fetchone()[0] == 0:
        for r in EQUIPOS:
            c.execute(
                """INSERT INTO reportes
                   (reporte,codigo,nombre,servicio,marca,modelo,serie,prioridad,estado,fecha,descripcion,reportado_por)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (reporte) DO NOTHING""",
                (r["reporte"], r.get("codigo",""), r["nombre"], r["servicio"],
                 r.get("marca",""), r.get("modelo",""), r.get("serie",""),
                 r["prioridad"], r["estado"], r["fecha"],
                 r.get("descripcion",""), r.get("reportado_por",""))
            )
        conn.commit()

    # ── Seed cirugías ─────────────────────────────────────────────────────────
    c.execute("SELECT COUNT(*) FROM cirugias")
    if c.fetchone()[0] == 0:
        hoy = date.today().strftime("%Y-%m-%d")
        ejemplos = [
            ("CIR-001", hoy, "07:30", "Quirófano 3", "Histerectomía Laparoscópica", "Dr. Mamani", "General", "Programada", 1, "Torre de Laparoscopía STORZ", "Verificar torre STORZ antes de las 07:00", "Sistema"),
            ("CIR-002", hoy, "09:00", "Quirófano 2", "Cesárea", "Dra. Flores", "Raquidea", "Programada", 0, "Monitor DRAGER INFINITY C700", "", "Sistema"),
            ("CIR-003", hoy, "10:30", "Quirófano Área Verde", "Histeroscopía", "Dr. Quiroga", "Sedación", "Programada", 1, "Equipo de Histeroscopía OLYMPUS", "Revisar óptica y fuente de luz", "Sistema"),
            ("CIR-004", hoy, "11:30", "Quirófano 3", "Salpingo-ooforectomía Laparoscópica", "Dr. Mamani", "General", "Programada", 1, "Torre de Laparoscopía STORZ", "Misma torre que CIR-001", "Sistema"),
            ("CIR-005", hoy, "13:00", "Quirófano 2", "Mastectomía Simple", "Dr. Ríos", "General", "Programada", 0, "Electrobisturí UZUMCU EK-410", "", "Sistema"),
        ]
        for e in ejemplos:
            c.execute(
                """INSERT INTO cirugias
                   (id,fecha,hora,quirofano,tipo,cirujano,anestesia,estado,requiere_ing,equipo_esp,obs,programado_por)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO NOTHING""", e
            )
        conn.commit()

    conn.close()


# ── CRUD helpers ──────────────────────────────────────────────────────────────

def _rows_to_dicts(cursor) -> list:
    cols = [d[0] for d in cursor.description]
    return [dict(zip(cols, row)) for row in cursor.fetchall()]


def db_get_inventario_extra() -> list:
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM inventario_extra ORDER BY servicio, equipo")
    rows = _rows_to_dicts(c); conn.close()
    return rows


def db_add_inventario_extra(eq: dict):
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute(
            """INSERT INTO inventario_extra
               (cod,equipo,marca,modelo,serie,servicio,estado,frecuencia,prioridad)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (cod) DO UPDATE SET
               equipo=EXCLUDED.equipo, marca=EXCLUDED.marca, modelo=EXCLUDED.modelo,
               serie=EXCLUDED.serie, servicio=EXCLUDED.servicio""",
            (eq["cod"], eq["equipo"], eq["marca"], eq["modelo"],
             eq["serie"], eq["servicio"], eq.get("estado","BUENO"),
             eq.get("frecuencia","SEMESTRAL"), eq.get("prioridad","A"))
        )
        conn.commit()
    finally:
        conn.close()


def db_get_servicios() -> list:
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT nombre FROM servicios ORDER BY nombre")
    rows = c.fetchall()
    if not rows:
        for s in SERVICIOS:
            c.execute("INSERT INTO servicios (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", (s,))
        conn.commit()
        c.execute("SELECT nombre FROM servicios ORDER BY nombre")
        rows = c.fetchall()
    conn.close()
    return [r[0] for r in rows]


def db_add_servicio(nombre: str):
    conn = get_conn(); c = conn.cursor()
    try:
        c.execute("INSERT INTO servicios (nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", (nombre.strip(),))
        conn.commit()
    finally:
        conn.close()


def db_delete_servicio(nombre: str):
    conn = get_conn(); c = conn.cursor()
    c.execute("DELETE FROM servicios WHERE nombre = %s", (nombre,))
    conn.commit(); conn.close()


def db_get_usuarios() -> dict:
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM usuarios")
    rows = _rows_to_dicts(c); conn.close()
    return {r["username"]: r for r in rows}


def db_add_usuario(username, password, nombre, rol, tipo):
    conn = get_conn(); c = conn.cursor()
    c.execute(
        """INSERT INTO usuarios VALUES (%s,%s,%s,%s,%s)
           ON CONFLICT (username) DO UPDATE SET
           password=EXCLUDED.password, nombre=EXCLUDED.nombre,
           rol=EXCLUDED.rol, tipo=EXCLUDED.tipo""",
        (username, password, nombre, rol, tipo)
    )
    conn.commit(); conn.close()


def db_get_reportes() -> list:
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM reportes ORDER BY fecha DESC")
    rows = _rows_to_dicts(c); conn.close()
    return rows


def db_add_reporte(r: dict):
    conn = get_conn(); c = conn.cursor()
    c.execute(
        """INSERT INTO reportes
           (reporte,codigo,nombre,servicio,marca,modelo,serie,prioridad,estado,fecha,descripcion,reportado_por)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (reporte) DO NOTHING""",
        (r["reporte"], r.get("codigo",""), r["nombre"], r["servicio"],
         r.get("marca",""), r.get("modelo",""), r.get("serie",""),
         r["prioridad"], r["estado"], r["fecha"],
         r.get("descripcion",""), r.get("reportado_por",""))
    )
    conn.commit(); conn.close()


def db_update_reporte(reporte_id: str, estado: str, prioridad: str):
    conn = get_conn(); c = conn.cursor()
    c.execute(
        "UPDATE reportes SET estado=%s, prioridad=%s WHERE reporte=%s",
        (estado, prioridad, reporte_id)
    )
    conn.commit(); conn.close()


def db_get_cirugias() -> list:
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM cirugias ORDER BY fecha, hora")
    rows = _rows_to_dicts(c); conn.close()
    for r in rows:
        r["requiere_ing"] = bool(r.get("requiere_ing", 0))
    return rows


def db_add_cirugia(cir: dict):
    conn = get_conn(); c = conn.cursor()
    c.execute(
        """INSERT INTO cirugias
           (id,fecha,hora,quirofano,tipo,cirujano,anestesia,estado,requiere_ing,equipo_esp,obs,programado_por)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
           ON CONFLICT (id) DO NOTHING""",
        (cir["id"], cir["fecha"], cir["hora"], cir["quirofano"], cir["tipo"],
         cir["cirujano"], cir["anestesia"], cir["estado"],
         1 if cir.get("requiere_ing") else 0,
         cir.get("equipo_esp",""), cir.get("obs",""), cir.get("programado_por",""))
    )
    conn.commit(); conn.close()


def db_update_cirugia_estado(cir_id: str, estado: str):
    conn = get_conn(); c = conn.cursor()
    c.execute("UPDATE cirugias SET estado=%s WHERE id=%s", (estado, cir_id))
    conn.commit(); conn.close()


# Inicializa la base de datos al arrancar
init_db()


# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False
if "pagina" not in st.session_state:
    st.session_state.pagina = "inicio"
if "reportes" not in st.session_state:
    st.session_state.reportes = db_get_reportes()
if "usuarios_sistema" not in st.session_state:
    st.session_state.usuarios_sistema = db_get_usuarios()
if "servicios_lista" not in st.session_state:
    st.session_state.servicios_lista = db_get_servicios()
# Siempre cargar equipos extra desde SQLite y fusionar con inventario base
_extras_db = db_get_inventario_extra()
for _eq in _extras_db:
    if not any(e.get("serie","") == _eq["serie"] for e in INVENTARIO_COMPLETO):
        INVENTARIO_COMPLETO.append(_eq)
st.session_state.inventario_extra = _extras_db
if "cirugias" not in st.session_state:
    st.session_state.cirugias = db_get_cirugias()

# ══════════════════════════════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════════════════════════════
def mostrar_login():
    HOSPITAL_IMG = "la_fotografía_del_hospital.jpeg"
    LOGO_IMG = "el_logo.jpeg"

    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    body, .stApp { background: #f0f4fa !important; }
    [data-testid="stSidebar"] { display: none; }
    .block-container { padding-top: 0 !important; max-width: 480px; margin: auto; }
    .hospital-banner {
        width: 100%; height: 190px; object-fit: cover;
        object-position: center 40%;
        border-radius: 14px 14px 0 0; display: block; margin: 0 auto;
    }
    .logo-wrap { display: flex; justify-content: center; margin-top: -38px; margin-bottom: 6px; }
    .logo-circle {
        width: 76px; height: 76px; border-radius: 50%;
        border: 3px solid #fff; box-shadow: 0 2px 10px rgba(0,0,0,0.18);
        object-fit: cover; background: #fff;
    }
    .main-title { text-align:center; font-size:1.45rem; font-weight:700; color:#0d2656; margin:4px 0 2px; }
    .sub-title { text-align:center; font-size:0.82rem; color:#555; margin-bottom:2px; }
    .hospital-label { text-align:center; font-size:0.73rem; color:#888; margin-bottom:18px; }
    .login-card { background:#fff; border-radius:12px; padding:22px 26px 18px; box-shadow:0 2px 12px rgba(0,0,0,0.08); margin-bottom:14px; }
    .login-card-title { font-size:1rem; font-weight:600; color:#0d2656; margin-bottom:2px; }
    .login-card-sub { font-size:0.76rem; color:#aaa; margin-bottom:14px; }
    .stTextInput > div > div > input {
        background: #1e2a4a !important; color: #e0e6f0 !important;
        border: 1.5px solid #2a3a6e !important; border-radius: 8px !important; padding: 10px 14px !important;
    }
    .stTextInput > div > div > input::placeholder { color: #6a7a9a !important; }
    .stTextInput label { display: none !important; }
    .stButton > button {
        background: #1a56a8 !important; color: #fff !important; border: none !important;
        border-radius: 8px !important; font-weight: 600 !important;
        width: 60% !important; display: block; margin: 0 auto !important;
    }
    .demo-card { background:#fff; border-radius:10px; padding:14px 18px; box-shadow:0 1px 6px rgba(0,0,0,0.07); }
    .demo-card-title { font-size:0.82rem; font-weight:600; color:#0d2656; margin-bottom:8px; }
    .demo-account { display:flex; align-items:center; gap:7px; font-size:0.78rem; color:#444; margin-bottom:4px; }
    .demo-account .usr { color:#1a56a8; font-weight:600; }
    .demo-account .rol { color:#888; }
    </style>
    """, unsafe_allow_html=True)

    if Path(HOSPITAL_IMG).exists():
        b64h = img_to_b64(HOSPITAL_IMG)
        st.markdown(f'<img class="hospital-banner" src="data:image/jpeg;base64,{b64h}" alt="Hospital"/>', unsafe_allow_html=True)

    if Path(LOGO_IMG).exists():
        b64l = img_to_b64(LOGO_IMG)
        st.markdown(f'<div class="logo-wrap"><img class="logo-circle" src="data:image/jpeg;base64,{b64l}"/></div>', unsafe_allow_html=True)

    st.markdown('<p class="main-title">Sistema de Gestión de Equipos Médicos</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">MedTrack — Reporte de Fallas</p>', unsafe_allow_html=True)
    st.markdown('<p class="hospital-label">Hospital Materno Infantil "Germán Urquidi" · Unidad de Bioingeniería · Cochabamba</p>', unsafe_allow_html=True)

    st.markdown('<div class="login-card">', unsafe_allow_html=True)
    st.markdown('<p class="login-card-title">Iniciar sesión</p>', unsafe_allow_html=True)
    st.markdown('<p class="login-card-sub">Ingresa tus credenciales institucionales</p>', unsafe_allow_html=True)

    usuario = st.text_input("u", placeholder="👤  ing.ramirez", key="login_user")
    contrasena = st.text_input("p", type="password", placeholder="••••••••", key="login_pass")

    st.markdown("<div style='margin-top:10px;'>", unsafe_allow_html=True)
    col_l, col_btn, col_r = st.columns([1, 6, 1])
    with col_btn:
        presionado = st.button("Ingresar al sistema →", use_container_width=True, key="btn_login")
    st.markdown("</div>", unsafe_allow_html=True)

    if presionado:
        u_data = st.session_state.usuarios_sistema
        if usuario in u_data and contrasena == u_data[usuario]["password"]:
            st.session_state.autenticado = True
            st.session_state.usuario = usuario
            st.session_state.pagina = "inicio"
            st.rerun()
        else:
            st.error("❌ Usuario o contraseña incorrectos.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div class="demo-card">
      <p class="demo-card-title">Cuentas de demostración</p>
      <div class="demo-account">👤 <span class="usr">dr.garcia</span> / <span>medico123</span> <span class="rol">· médico</span></div>
      <div class="demo-account">👤 <span class="usr">ing.ramirez</span> / <span>ingeniero1</span> <span class="rol">· ing.ramirez / ing.flores</span></div>
      <div class="demo-account">👤 <span class="usr">enf.torres</span> / <span>enfermera1</span> <span class="rol">· enfermera/o</span></div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def mostrar_sidebar():
    LOGO_IMG = "el_logo.jpeg"
    u = st.session_state.usuarios_sistema[st.session_state.usuario]

    with st.sidebar:
        # Logo + nombre app
        if Path(LOGO_IMG).exists():
            b64l = img_to_b64(LOGO_IMG)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:12px 0 6px;">
              <img src="data:image/jpeg;base64,{b64l}" style="width:46px;height:46px;border-radius:50%;object-fit:cover;border:2px solid #3a5a9a;"/>
              <div>
                <div style="font-size:1rem;font-weight:700;color:#fff;">MedTrack</div>
                <div style="font-size:0.7rem;color:#8ab4d8;">H.M.I. Germán Urquidi</div>
                <div style="font-size:0.65rem;color:#7a9abf;">Cochabamba, Bolivia</div>
              </div>
            </div>
            <hr style="border-color:#2a3a6e;margin:8px 0;"/>
            """, unsafe_allow_html=True)

        # Sesión activa
        st.markdown(f"""
        <div style="padding:8px 0 12px;">
          <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">SESIÓN ACTIVA</div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#1a56a8;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">👤</div>
            <div>
              <div style="font-size:0.82rem;font-weight:600;color:#dde8f5;">{u['nombre']}</div>
              <div style="font-size:0.7rem;color:#7a9abf;">{u['rol']}</div>
            </div>
          </div>
        </div>
        <hr style="border-color:#2a3a6e;margin:4px 0 10px;"/>
        <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">NAVEGACIÓN</div>
        """, unsafe_allow_html=True)

        # Menú
        paginas = [
            ("🏠", "inicio",           "Inicio"),
            ("📊", "tablero",          "Tablero General"),
            ("📋", "reportes",         "Gestión de Reportes"),
            ("🏥", "cirugias",         "Cirugías del Día"),
            ("🗓️", "mantenimientos",   "Mantenimientos"),
            ("📦", "inventario",       "Inventario"),
            ("📚", "historial",        "Historial"),
            ("📄", "protocolos",       "Protocolos"),
            ("🔵", "qr",               "Generar Códigos QR"),
            ("📝", "informes",         "Informes Técnicos"),
            ("📨", "inicio_proceso",   "Inicio de Proceso"),
            ("👥", "usuarios",         "Administrar Usuarios"),
        ]

        for icono, pid, nombre in paginas:
            if st.button(f"{icono}  {nombre}", key=f"nav_{pid}",
                         help=nombre,
                         use_container_width=True):
                st.session_state.pagina = pid
                st.rerun()

        st.markdown("<br/><br/>", unsafe_allow_html=True)
        st.markdown('<hr style="border-color:#2a3a6e;margin:6px 0 10px;"/>', unsafe_allow_html=True)

        if st.button("🚪  Cerrar sesión", key="cerrar", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.pagina = "inicio"
            st.rerun()

        st.markdown("""
        <div style="text-align:center;margin-top:12px;">
          <div style="font-size:0.65rem;color:#4a6a9a;">MedTrack v1.0 · 2026</div>
          <div style="font-size:0.6rem;color:#3a5a8a;">Unidad de Bioingeniería · HMIGU</div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  PÁGINAS
# ══════════════════════════════════════════════════════════════════════════════

def badge_estado(estado):
    clases = {
        "Pendiente":     "badge-pendiente",
        "En revisión":   "badge-revision",
        "Reparado":      "badge-reparado",
        "Alta prioridad":"badge-alta",
    }
    clase = clases.get(estado, "badge-pendiente")
    return f'<span class="badge {clase}">{estado}</span>'

def badge_prioridad(p):
    c = {"Alta":"badge-alta","Media":"badge-media","Baja":"badge-baja"}
    clase = c.get(p, "badge-media")
    return f'<span class="badge {clase}">{p}</span>'


# ── INICIO ────────────────────────────────────────────────────────────────────
def pagina_inicio():
    HOSPITAL_IMG = "la_fotografía_del_hospital.jpeg"
    LOGO_IMG = "el_logo.jpeg"
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    hora_actual = datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().strftime("%d de %B de %Y")

    # Hero con imagen del hospital y overlay
    if Path(HOSPITAL_IMG).exists():
        b64h = img_to_b64(HOSPITAL_IMG)
        b64l = img_to_b64(LOGO_IMG) if Path(LOGO_IMG).exists() else ""
        nombre_usuario = u["nombre"]
        rol_usuario = u["rol"]
        logo_html = f'<img src="data:image/jpeg;base64,{b64l}" style="width:60px;height:60px;border-radius:50%;border:3px solid rgba(255,255,255,0.6);object-fit:cover;margin-bottom:10px;"/>' if b64l else ""
        st.markdown(f"""
        <div style="position:relative;border-radius:18px;overflow:hidden;box-shadow:0 6px 30px rgba(0,0,0,0.18);margin-bottom:24px;">
          <img src="data:image/jpeg;base64,{b64h}"
               style="width:100%;height:300px;object-fit:cover;object-position:center 35%;display:block;"/>
          <div style="position:absolute;inset:0;background:linear-gradient(to bottom, rgba(13,27,62,0.3) 0%, rgba(13,27,62,0.78) 100%);"></div>
          <div style="position:absolute;bottom:0;left:0;right:0;padding:28px 32px;color:#fff;">
            {logo_html}
            <div style="font-size:0.75rem;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.7);margin-bottom:4px;">
              Hospital Materno Infantil · Unidad de Bioingeniería
            </div>
            <div style="font-size:1.8rem;font-weight:700;line-height:1.2;">
              Bienvenido, {nombre_usuario} 👋
            </div>
            <div style="font-size:0.9rem;color:rgba(255,255,255,0.8);margin-top:4px;">
              {rol_usuario} &nbsp;·&nbsp; {fecha_actual} &nbsp;·&nbsp; {hora_actual}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Acceso rápido
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#0d2656;margin-bottom:14px;">⚡ Acceso Rápido</div>', unsafe_allow_html=True)

    acc = [
        ("tablero",        "📊", "#1a56a8", "Tablero General",       "Estado de equipos y métricas"),
        ("reportes",       "📋", "#0a7a3e", "Gestión de Reportes",   "Filtrar, actualizar y registrar fallas"),
        ("cirugias",       "🏥", "#6a0d91", "Prog. de Cirugías",     "Cirugías del día y equipos a verificar"),
        ("protocolos",     "📄", "#7a3a8a", "Protocolos",            "Checklists de mantenimiento"),
        ("qr",             "🔵", "#b85c00", "Generar Códigos QR",    "QR de equipos del inventario"),
        ("informes",       "📝", "#0d5a7a", "Informes Técnicos",     "Formato oficial HMIGU"),
        ("inicio_proceso", "📨", "#8a2a2a", "Inicio de Proceso",     "Solicitudes de compra oficiales"),
    ]

    col1, col2, col3 = st.columns(3)
    cols_list = [col1, col2, col3]
    for i, (pid, icono, color, titulo, desc) in enumerate(acc):
        with cols_list[i % 3]:
            st.markdown(f"""
            <div style="background:#fff;border-radius:12px;padding:18px 16px 10px;
                        box-shadow:0 2px 10px rgba(0,0,0,0.07);margin-bottom:6px;
                        border-left:4px solid {color};">
              <div style="font-size:1.5rem;margin-bottom:5px;">{icono}</div>
              <div style="font-size:0.88rem;font-weight:700;color:#0d2656;">{titulo}</div>
              <div style="font-size:0.73rem;color:#888;margin-top:2px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir →", key=f"inicio_{pid}", use_container_width=True):
                st.session_state.pagina = pid
                st.rerun()

    # Mini resumen estadístico
    st.markdown("<br/>", unsafe_allow_html=True)
    reps = st.session_state.reportes
    pendientes = sum(1 for r in reps if r["estado"] == "Pendiente")
    en_rev = sum(1 for r in reps if r["estado"] == "En revisión")
    alta = sum(1 for r in reps if r["prioridad"] == "Alta")
    total_reps = len(reps)
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1b3e 0%,#1a3a6e 100%);
                border-radius:14px;padding:22px 28px;color:#fff;
                display:flex;gap:40px;align-items:center;flex-wrap:wrap;">
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">Total Reportes</div>
        <div style="font-size:2.2rem;font-weight:700;">{total_reps}</div>
      </div>
      <div style="width:1px;height:40px;background:rgba(255,255,255,0.15);"></div>
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">Pendientes</div>
        <div style="font-size:2.2rem;font-weight:700;color:#ffc107;">{pendientes}</div>
      </div>
      <div style="width:1px;height:40px;background:rgba(255,255,255,0.15);"></div>
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">En Revisión</div>
        <div style="font-size:2.2rem;font-weight:700;color:#63b3ff;">{en_rev}</div>
      </div>
      <div style="width:1px;height:40px;background:rgba(255,255,255,0.15);"></div>
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">Alta Prioridad</div>
        <div style="font-size:2.2rem;font-weight:700;color:#ff6b6b;">{alta}</div>
      </div>
      <div style="flex:1;text-align:right;">
        <div style="font-size:0.7rem;color:rgba(255,255,255,0.45);">MedTrack v1.0 · 2026</div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.35);">Unidad de Bioingeniería · HMIGU</div>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ── INICIO MÉDICO / ENFERMERÍA ────────────────────────────────────────────────
def pagina_inicio_medico():
    HOSPITAL_IMG = "la_fotografía_del_hospital.jpeg"
    LOGO_IMG = "el_logo.jpeg"
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    hora_actual = datetime.now().strftime("%H:%M")
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    icono_rol = "🩺" if u["tipo"] == "medico" else "💊"

    if Path(HOSPITAL_IMG).exists():
        b64h = img_to_b64(HOSPITAL_IMG)
        b64l = img_to_b64(LOGO_IMG) if Path(LOGO_IMG).exists() else ""
        nombre_usuario = u["nombre"]
        rol_usuario = u["rol"]
        logo_html = f'<img src="data:image/jpeg;base64,{b64l}" style="width:56px;height:56px;border-radius:50%;border:3px solid rgba(255,255,255,0.5);object-fit:cover;margin-bottom:8px;"/>' if b64l else ""
        st.markdown(f"""
        <div style="position:relative;border-radius:18px;overflow:hidden;box-shadow:0 6px 30px rgba(0,0,0,0.18);margin-bottom:24px;">
          <img src="data:image/jpeg;base64,{b64h}"
               style="width:100%;height:260px;object-fit:cover;object-position:center 35%;display:block;"/>
          <div style="position:absolute;inset:0;background:linear-gradient(to bottom, rgba(13,27,62,0.2) 0%, rgba(13,27,62,0.82) 100%);"></div>
          <div style="position:absolute;bottom:0;left:0;right:0;padding:24px 30px;color:#fff;">
            {logo_html}
            <div style="font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,0.65);margin-bottom:4px;">
              Hospital Materno Infantil · Unidad de Bioingeniería
            </div>
            <div style="font-size:1.7rem;font-weight:700;line-height:1.2;">
              Bienvenido, {nombre_usuario} {icono_rol}
            </div>
            <div style="font-size:0.85rem;color:rgba(255,255,255,0.75);margin-top:4px;">
              {rol_usuario} &nbsp;·&nbsp; {fecha_actual} &nbsp;·&nbsp; {hora_actual}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # Acceso rápido solo para el rol médico/enfermera
    st.markdown('<div style="font-size:1rem;font-weight:700;color:#0d2656;margin-bottom:14px;">⚡ Acceso Rápido</div>', unsafe_allow_html=True)

    acc_medico = [
        ("reportar_falla", "🔴", "#c0392b", "Reportar Falla",    "Registre una falla de equipo"),
        ("mis_reportes",   "📋", "#0a7a3e", "Mis Reportes",      "Estado de sus reportes enviados"),
        ("cirugias",       "🏥", "#1a56a8", "Prog. Cirugías",    "Programme y vea cirugías del día"),
        ("notificaciones", "🔔", "#b85c00", "Notificaciones",    "Actualizaciones de sus reportes"),
        ("mis_equipos",    "🖥️", "#6a0d91", "Estado Equipos",   "Equipos operativos de su área"),
        ("protocolos",     "📄", "#7a3a8a", "Protocolos",        "Protocolos por equipo médico"),
    ]

    col1, col2, col3 = st.columns(3)
    cols_list = [col1, col2, col3]
    for i, (pid, icono, color, titulo, desc) in enumerate(acc_medico):
        with cols_list[i % 3]:
            st.markdown(f"""
            <div style="background:#fff;border-radius:12px;padding:20px 16px 12px;
                        box-shadow:0 2px 12px rgba(0,0,0,0.08);margin-bottom:6px;
                        border-left:4px solid {color};">
              <div style="font-size:1.6rem;margin-bottom:6px;">{icono}</div>
              <div style="font-size:0.9rem;font-weight:700;color:#0d2656;">{titulo}</div>
              <div style="font-size:0.75rem;color:#888;margin-top:3px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("Abrir →", key=f"iniciomedico_{pid}", use_container_width=True):
                st.session_state.pagina = pid
                st.rerun()

    # Mini info
    st.markdown("<br/>", unsafe_allow_html=True)
    reps_mios = sum(1 for r in st.session_state.reportes if r.get("reportado_por") == u["nombre"])
    pendientes_mios = sum(1 for r in st.session_state.reportes
                          if r.get("reportado_por") == u["nombre"] and r["estado"] == "Pendiente")
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,#0d1b3e 0%,#1a3a6e 100%);
                border-radius:14px;padding:20px 28px;color:#fff;display:flex;gap:40px;align-items:center;flex-wrap:wrap;">
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">Mis Reportes</div>
        <div style="font-size:2.2rem;font-weight:700;">{reps_mios}</div>
      </div>
      <div style="width:1px;height:40px;background:rgba(255,255,255,0.15);"></div>
      <div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.55);text-transform:uppercase;letter-spacing:1.5px;">Pendientes</div>
        <div style="font-size:2.2rem;font-weight:700;color:#ffc107;">{pendientes_mios}</div>
      </div>
      <div style="flex:1;text-align:right;">
        <div style="font-size:0.72rem;color:rgba(255,255,255,0.5);">{icono_rol} {rol_usuario}</div>
        <div style="font-size:0.65rem;color:rgba(255,255,255,0.35);">MedTrack v1.0 · HMIGU</div>
      </div>
    </div>
    """, unsafe_allow_html=True)



# ── TABLERO GENERAL ───────────────────────────────────────────────────────────
def pagina_tablero():
    reps = st.session_state.reportes
    total = len(reps)
    pendientes = sum(1 for r in reps if r["estado"] == "Pendiente")
    en_revision = sum(1 for r in reps if r["estado"] == "En revisión")
    reparados = sum(1 for r in reps if r["estado"] == "Reparado")
    alta = sum(1 for r in reps if r["prioridad"] == "Alta")

    hoy = datetime.now().strftime("%d de %B de %Y")
    hora = datetime.now().strftime("%I:%M %p")

    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">
      <div>
        <div class="section-title">📊 Tablero General</div>
        <div class="section-sub">Resumen del estado de los equipos médicos del hospital</div>
      </div>
      <div style="text-align:right;background:#fff;padding:10px 16px;border-radius:10px;box-shadow:0 1px 6px rgba(0,0,0,0.07);">
        <div style="font-size:0.78rem;color:#888;">{hoy}</div>
        <div style="font-size:0.9rem;font-weight:700;color:#0d2656;">{hora}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Métricas
    c1,c2,c3,c4,c5 = st.columns(5)
    metricas = [
        (c1, "📄", total,       "Total de reportes",  "100% del total", "#0d2656"),
        (c2, "⚠️", pendientes,  "Pendientes",          f"{int(pendientes/total*100) if total else 0}% del total", "#856404"),
        (c3, "🔵", en_revision, "En revisión",         f"{int(en_revision/total*100) if total else 0}% del total", "#084298"),
        (c4, "✅", reparados,   "Reparados",           f"{int(reparados/total*100) if total else 0}% del total", "#0a3622"),
        (c5, "🔴", alta,        "Alta prioridad",      f"{int(alta/total*100) if total else 0}% del total", "#842029"),
    ]
    for col, icono, num, label, sub, color in metricas:
        with col:
            st.markdown(f"""
            <div class="metric-card">
              <div style="font-size:1.4rem;">{icono}</div>
              <div class="metric-num" style="color:{color};">{num}</div>
              <div class="metric-label">{label}</div>
              <div class="metric-sub">{sub}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Gráficas
    col_g1, col_g2, col_g3 = st.columns(3)

    with col_g1:
        st.markdown('<div class="card"><b>Reportes por servicio</b>', unsafe_allow_html=True)
        servicios_count = {}
        for r in reps:
            s = r["servicio"].split("(")[0].strip()
            servicios_count[s] = servicios_count.get(s, 0) + 1
        fig1 = go.Figure(go.Bar(
            x=list(servicios_count.keys()),
            y=list(servicios_count.values()),
            marker_color="#1a56a8",
            text=list(servicios_count.values()),
            textposition="outside"
        ))
        fig1.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="white", paper_bgcolor="white",
                           yaxis=dict(title="Nº de reportes", dtick=1),
                           showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        st.markdown('<div class="card"><b>Estado de los reportes</b>', unsafe_allow_html=True)
        estados = {"Pendientes": pendientes, "En revisión": en_revision, "Reparados": reparados}
        fig2 = go.Figure(go.Pie(
            labels=list(estados.keys()),
            values=list(estados.values()),
            hole=0.55,
            marker_colors=["#ffc107","#0d6efd","#198754"],
        ))
        fig2.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0),
                           paper_bgcolor="white",
                           annotations=[dict(text=f"<b>{total}</b><br>Total", x=0.5,y=0.5,font_size=13,showarrow=False)])
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_g3:
        st.markdown('<div class="card"><b>Equipos por prioridad</b>', unsafe_allow_html=True)
        prio = {"Alta": alta, "Media": sum(1 for r in reps if r["prioridad"]=="Media"),
                "Baja": sum(1 for r in reps if r["prioridad"]=="Baja")}
        fig3 = go.Figure(go.Bar(
            x=list(prio.values()),
            y=list(prio.keys()),
            orientation="h",
            marker_color=["#dc3545","#ffc107","#198754"],
            text=list(prio.values()),
            textposition="outside"
        ))
        fig3.update_layout(height=200, margin=dict(l=0,r=0,t=10,b=0),
                           plot_bgcolor="white", paper_bgcolor="white",
                           xaxis=dict(title="Nº de equipos", dtick=1))
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Equipos críticos y actividad
    col_eq, col_act = st.columns(2)

    with col_eq:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">🔴 Equipos Críticos (Alta Prioridad)</div>', unsafe_allow_html=True)
        criticos = [r for r in reps if r["prioridad"] == "Alta"]
        for eq in criticos[:3]:
            st.markdown(f"""
            <div class="equipo-critico">
              <div class="eq-icon">🏥</div>
              <div style="flex:1;">
                <div class="eq-nombre">{eq['nombre']}</div>
                <div class="eq-detalle">Servicio: {eq['servicio']} · Código: {eq['reporte']}</div>
              </div>
              <div>{badge_estado(eq['estado'])}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        if st.button("Ver todos los reportes →", key="ver_reportes_td"):
            st.session_state.pagina = "reportes"; st.rerun()

    with col_act:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">📅 Actividad Reciente</div>', unsafe_allow_html=True)
        for act in ACTIVIDAD:
            st.markdown(f"""
            <div class="actividad-item">
              <span class="act-icon">{act['icono']}</span>
              <div style="flex:1;">{act['texto']}</div>
              <span class="act-time">{act['hora']}</span>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div style="text-align:center;color:#aaa;font-size:0.72rem;margin-top:10px;">🟢 Última actualización hace unos segundos</div>', unsafe_allow_html=True)


# ── GESTIÓN DE REPORTES ───────────────────────────────────────────────────────
def pagina_reportes():
    st.markdown('<div class="section-title">📋 Gestión de Reportes</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Visualice, filtre y actualice el estado de cada reporte</div>', unsafe_allow_html=True)

    reps = st.session_state.reportes

    col1,col2,col3,col4 = st.columns([1,1,1,1.5])
    with col1:
        f_estado = st.selectbox("Estado", ["Todos","Pendiente","En revisión","Reparado","Alta prioridad"])
    with col2:
        f_prio = st.selectbox("Prioridad", ["Todas","Alta","Media","Baja"])
    with col3:
        f_serv = st.selectbox("Servicio", ["Todos"] + sorted(set(r["servicio"] for r in reps)))
    with col4:
        f_buscar = st.text_input("Buscar equipo", placeholder="Escriba para filtrar...")

    filtrados = reps
    if f_estado != "Todos": filtrados = [r for r in filtrados if r["estado"] == f_estado]
    if f_prio != "Todas":   filtrados = [r for r in filtrados if r["prioridad"] == f_prio]
    if f_serv != "Todos":   filtrados = [r for r in filtrados if r["servicio"] == f_serv]
    if f_buscar:            filtrados = [r for r in filtrados if f_buscar.lower() in r["nombre"].lower()]

    st.markdown(f'<div style="margin:12px 0;font-size:0.85rem;color:#555;"><b>{len(filtrados)}</b> reporte(s) encontrado(s)</div>', unsafe_allow_html=True)

    # Cabecera tabla
    st.markdown("""
    <div class="tabla-header" style="grid-template-columns:1.2fr 2.5fr 1.5fr 1.2fr 1fr 0.8fr 0.5fr;">
      <span>Código</span><span>Equipo</span><span>Servicio</span>
      <span>Fecha</span><span>Estado</span><span>Prioridad</span><span>Acción</span>
    </div>
    """, unsafe_allow_html=True)

    for i, r in enumerate(filtrados):
        col_a,col_b,col_c,col_d,col_e,col_f,col_g = st.columns([1.2,2.5,1.5,1.2,1,0.8,0.5])
        with col_a: st.markdown(f'<span style="color:#1a56a8;font-weight:600;font-size:0.8rem;">{r["reporte"]}</span>', unsafe_allow_html=True)
        with col_b: st.markdown(f'<span style="font-size:0.8rem;">{r["nombre"]}</span>', unsafe_allow_html=True)
        with col_c: st.markdown(f'<span style="font-size:0.78rem;color:#555;">{r["servicio"]}</span>', unsafe_allow_html=True)
        with col_d: st.markdown(f'<span style="font-size:0.75rem;color:#777;">{r["fecha"]}</span>', unsafe_allow_html=True)
        with col_e: st.markdown(badge_estado(r["estado"]), unsafe_allow_html=True)
        with col_f: st.markdown(badge_prioridad(r["prioridad"]), unsafe_allow_html=True)
        with col_g:
            if st.button("👁", key=f"ver_{i}", help="Ver detalle"):
                st.session_state[f"detalle_{i}"] = not st.session_state.get(f"detalle_{i}", False)
        st.markdown('<hr style="margin:0;border-color:#f0f0f0;"/>', unsafe_allow_html=True)

        if st.session_state.get(f"detalle_{i}", False):
            with st.expander(f"Detalle: {r['reporte']}", expanded=True):
                c1,c2 = st.columns(2)
                with c1:
                    nuevo_estado = st.selectbox("Cambiar estado", ["Pendiente","En revisión","Reparado","Alta prioridad"], key=f"est_{i}", index=["Pendiente","En revisión","Reparado","Alta prioridad"].index(r["estado"]))
                    nueva_prio = st.selectbox("Cambiar prioridad", ["Alta","Media","Baja"], key=f"pr_{i}", index=["Alta","Media","Baja"].index(r["prioridad"]))
                with c2:
                    st.markdown(f"**Equipo:** {r['nombre']}")
                    st.markdown(f"**Servicio:** {r['servicio']}")
                    st.markdown(f"**Serie:** {r['serie']}")
                    st.markdown(f"**Fecha reporte:** {r['fecha']}")
                if st.button("💾 Guardar cambios", key=f"save_{i}"):
                    db_update_reporte(r["reporte"], nuevo_estado, nueva_prio)
                    st.session_state.reportes = db_get_reportes()
                    st.success("✅ Cambios guardados en la base de datos.")
                    st.rerun()

    st.markdown('<div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px;">', unsafe_allow_html=True)
    st.markdown(f'<span style="font-size:0.78rem;color:#888;">Mostrando 1 a {len(filtrados)} de {len(filtrados)} reportes</span>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("#### ➕ Agregar Nuevo Reporte")
    with st.expander("Registrar nuevo equipo en falla"):
        nc1,nc2 = st.columns(2)
        with nc1:
            nuevo_equipo = st.text_input("Nombre del equipo", key="nuevo_eq")
            nuevo_servicio = st.selectbox("Servicio", sorted(st.session_state.servicios_lista), key="nuevo_serv")
            nuevo_marca = st.text_input("Marca", key="nuevo_marca")
        with nc2:
            nuevo_serie = st.text_input("Nº de Serie", key="nuevo_serie")
            nuevo_modelo = st.text_input("Modelo", key="nuevo_modelo")
            nuevo_prio2 = st.selectbox("Prioridad", ["Alta","Media","Baja"], key="nuevo_prio2")
        nuevo_desc = st.text_area("Descripción de la falla", key="nuevo_desc")
        if st.button("📥 Registrar reporte", key="reg_rep"):
            if nuevo_equipo and nuevo_servicio:
                num = len(st.session_state.reportes)+1
                cod = f"REP-2026-{num:03d}"
                nuevo_r = {
                    "codigo": nuevo_serie,
                    "nombre": nuevo_equipo,
                    "servicio": nuevo_servicio,
                    "marca": nuevo_marca,
                    "modelo": nuevo_modelo,
                    "serie": nuevo_serie,
                    "prioridad": nuevo_prio2,
                    "estado": "Pendiente",
                    "fecha": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "reporte": cod,
                    "descripcion": nuevo_desc,
                    "reportado_por": "",
                }
                db_add_reporte(nuevo_r)
                st.session_state.reportes = db_get_reportes()
                st.success(f"✅ Reporte {cod} registrado y guardado correctamente.")
                st.rerun()
            else:
                st.warning("Complete los campos obligatorios.")


# ── PROTOCOLOS ───────────────────────────────────────────────────────────────
def pagina_protocolos():
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    es_medico = u["tipo"] in ["medico","enfermera"]

    st.markdown('<div class="section-title">📄 Protocolos de Mantenimiento</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Protocolos preventivos y correctivos de los equipos del hospital</div>', unsafe_allow_html=True)

    equipo_sel = st.selectbox("Selecciona un equipo", list(PROTOCOLOS.keys()))
    prot = PROTOCOLOS[equipo_sel]

    st.markdown(f"""
    <div class="card">
      <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:14px;">
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">EQUIPO</span><br/><b style="color:#0d2656;">{prot['equipo']}</b></div>
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">MARCA</span><br/><b style="color:#0d2656;">{prot['marca']}</b></div>
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">MODELO</span><br/><b style="color:#0d2656;">{prot['modelo']}</b></div>
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">Nº SERIE</span><br/><b style="color:#0d2656;">{prot['serie']}</b></div>
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">ÁREA</span><br/><b style="color:#0d2656;">{prot['area']}</b></div>
        <div><span style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;">FRECUENCIA</span><br/><b style="color:#0d2656;">{prot['frecuencia']}</b></div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    if es_medico:
        # ── Modo solo lectura para médicos/enfermeras ─────────────────────────
        st.markdown("""
        <div style="background:#e8f4fd;border-radius:8px;padding:10px 16px;margin-bottom:16px;
                    border-left:4px solid #1a56a8;font-size:0.82rem;color:#084298;">
          📋 <b>Modo consulta</b> — Este protocolo es de uso exclusivo del equipo de Bioingeniería.
          Puede consultarlo como referencia informativa.
        </div>
        """, unsafe_allow_html=True)

        for seccion, items in prot["items"].items():
            st.markdown(f'<div class="form-section"><div class="form-title">{seccion}</div>', unsafe_allow_html=True)
            for i, item in enumerate(items):
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:10px;padding:7px 0;
                            border-bottom:1px solid #f5f5f5;">
                  <span style="font-size:1rem;color:#1a56a8;">•</span>
                  <span style="font-size:0.82rem;color:#333;">{item}</span>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="background:#fff3cd;border-radius:8px;padding:12px 16px;margin-top:8px;
                    border-left:4px solid #ffc107;font-size:0.82rem;color:#856404;">
          ⚠️ <b>Importante:</b> Ante cualquier anomalía en el funcionamiento del equipo,
          repórtelo a la Unidad de Bioingeniería a través del módulo <b>"Reportar Falla"</b>.
        </div>
        """, unsafe_allow_html=True)

    else:
        # ── Modo editable para ingenieros ─────────────────────────────────────
        st.markdown("#### Checklist de Mantenimiento")
        for seccion, items in prot["items"].items():
            st.markdown(f'<div class="form-section"><div class="form-title">{seccion}</div>', unsafe_allow_html=True)
            for idx_item, item in enumerate(items):
                safe_key = f"prot_{equipo_sel[:15]}_{seccion[:10]}_{idx_item}"
                c1,c2,c3 = st.columns([3,0.4,0.4])
                with c1: st.markdown(f'<span style="font-size:0.82rem;">{item}</span>', unsafe_allow_html=True)
                with c2: st.checkbox("✓", key=f"{safe_key}_si")
                with c3: st.checkbox("✗", key=f"{safe_key}_no")
            st.markdown('</div>', unsafe_allow_html=True)

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.text_area("Conclusiones / Recomendaciones", height=100, key="prot_obs")
            st.text_area("Instrumentos de verificación utilizados", height=80, key="prot_inst")
        with col_p2:
            st.text_input("Biomédico Responsable", key="prot_resp")
            st.text_input("Conformidad del Servicio", key="prot_conf")
            st.date_input("Fecha de intervención", key="prot_fecha")
            st.date_input("Próxima intervención", key="prot_prox")

        if st.button("💾 Guardar Protocolo", key="guardar_prot"):
            st.success("✅ Protocolo guardado correctamente.")


# ── CÓDIGOS QR ────────────────────────────────────────────────────────────────
def _generar_qr_bytes(info: str, box_size: int = 5) -> tuple:
    """Genera imagen QR y devuelve (bytes_png, b64_str)."""
    qr = qrcode.QRCode(version=1, box_size=box_size, border=2)
    qr.add_data(info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d2656", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue(), base64.b64encode(buf.getvalue()).decode()


def pagina_qr():
    st.markdown('<div class="section-title">🔵 Generar Códigos QR</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Códigos QR de equipos existentes y generador para nuevos equipos</div>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📦 QR de Equipos Registrados", "➕ Generar y Registrar Nuevo Equipo"])

    # ── TAB 1: equipos registrados ────────────────────────────────────────────
    with tab1:
        servicios_qr = ["Todos"] + sorted(st.session_state.servicios_lista)
        f_serv_qr   = st.selectbox("Filtrar por servicio", servicios_qr, key="qr_serv")
        inv_filtrado = INVENTARIO_COMPLETO if f_serv_qr == "Todos" else [
            e for e in INVENTARIO_COMPLETO if e["servicio"] == f_serv_qr]

        if not inv_filtrado:
            st.info("No hay equipos registrados para este servicio.")
        else:
            st.markdown(f'<div style="font-size:0.82rem;color:#666;margin-bottom:14px;">'
                        f'<b>{len(inv_filtrado)}</b> equipo(s) encontrado(s)</div>',
                        unsafe_allow_html=True)
            cols = st.columns(3)
            for i, equipo in enumerate(inv_filtrado):
                nom  = str(equipo.get("equipo",""))
                mar  = str(equipo.get("marca",""))
                mod  = str(equipo.get("modelo",""))
                ser  = str(equipo.get("serie",""))
                serv = str(equipo.get("servicio",""))
                cod  = str(equipo.get("cod",""))
                info_qr = (f"MEDTRACK-HMIGU\nEquipo: {nom}\nMarca: {mar}\n"
                           f"Modelo: {mod}\nSerie: {ser}\nServicio: {serv}\nCódigo: {cod}")
                qr_bytes, b64_qr = _generar_qr_bytes(info_qr, box_size=5)
                with cols[i % 3]:
                    st.markdown(
                        "<div class=\"card\" style=\"text-align:center;padding:14px;\">"
                        "<img src=\"data:image/png;base64," + b64_qr + "\" style=\"width:120px;height:120px;\"/>"
                        "<div style=\"font-size:0.75rem;font-weight:600;color:#0d2656;margin-top:6px;\">" + nom + "</div>"
                        "<div style=\"font-size:0.68rem;color:#888;\">" + mar + " " + mod + "</div>"
                        "<div style=\"font-size:0.65rem;color:#aaa;\">" + serv + "</div>"
                        "</div>",
                        unsafe_allow_html=True
                    )
                    st.download_button(
                        "⬇ Descargar QR",
                        data=qr_bytes,
                        file_name=f"QR_{nom.replace(' ','_')}_{ser}.png",
                        mime="image/png",
                        key=f"dl_qr_{i}"
                    )

    # ── TAB 2: nuevo equipo ───────────────────────────────────────────────────
    with tab2:
        st.markdown("""
        <div style="background:#e8f4fd;border-radius:8px;padding:10px 16px;margin-bottom:16px;
                    border-left:4px solid #1a56a8;font-size:0.82rem;color:#084298;">
          📋 Complete los datos del equipo, genere el QR y guárdelo en el inventario.
        </div>
        """, unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            nq_equipo = st.text_input("Nombre del equipo *", key="nq_eq",
                                      placeholder="Ej: Ventilador Neonatal")
            nq_marca  = st.text_input("Marca", key="nq_marca",
                                      placeholder="Ej: COMEN")
            nq_modelo = st.text_input("Modelo", key="nq_modelo",
                                      placeholder="Ej: V2")
        with c2:
            nq_serie  = st.text_input("Número de Serie *", key="nq_serie",
                                      placeholder="Ej: 2C250917116")
            nq_cod    = st.text_input("Código de Bien", key="nq_cod",
                                      placeholder="Ej: A06032400026")
            nq_serv   = st.selectbox("Servicio *",
                                     sorted(st.session_state.servicios_lista),
                                     key="nq_serv")
            nq_frec   = st.selectbox("Frecuencia mantenimiento",
                                     ["SEMESTRAL","TRIMESTRAL","ANUAL","CUATRIMESTRAL"],
                                     key="nq_frec")

        # Botón Generar QR
        if st.button("🔵 Generar QR", key="gen_qr", use_container_width=False):
            if nq_equipo.strip() and nq_serie.strip():
                info_new = (f"MEDTRACK-HMIGU\nEquipo: {nq_equipo}\n"
                            f"Marca: {nq_marca}\nModelo: {nq_modelo}\n"
                            f"Serie: {nq_serie}\nServicio: {nq_serv}\nCódigo: {nq_cod}")
                qr_bytes, b64_new = _generar_qr_bytes(info_new, box_size=8)
                st.session_state["qr_preview"] = {
                    "bytes": qr_bytes, "b64": b64_new,
                    "equipo": nq_equipo, "marca": nq_marca,
                    "modelo": nq_modelo, "serie": nq_serie,
                    "servicio": nq_serv, "cod": nq_cod, "frecuencia": nq_frec,
                }
            else:
                st.warning("⚠️ Completa el nombre del equipo y el número de serie.")

        # Vista previa + botones de acción
        prev = st.session_state.get("qr_preview")
        if prev:
            st.markdown("<br/>", unsafe_allow_html=True)
            col_img, col_data = st.columns([1, 2])
            with col_img:
                st.markdown(
                    "<div style=\"text-align:center;background:#fff;border-radius:12px;padding:16px;"
                    "box-shadow:0 2px 10px rgba(0,0,0,0.08);\">"
                    "<img src=\"data:image/png;base64," + prev["b64"] + "\" style=\"width:180px;\"/>"
                    "<div style=\"font-size:0.72rem;color:#aaa;margin-top:6px;\">Vista previa del QR</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            with col_data:
                st.markdown(f"""
                <div class="card" style="padding:14px 18px;">
                  <div style="font-size:0.68rem;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;">Datos del equipo</div>
                  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                    <div><span style="font-size:0.68rem;color:#aaa;">EQUIPO</span><br/><b style="font-size:0.85rem;">{prev["equipo"]}</b></div>
                    <div><span style="font-size:0.68rem;color:#aaa;">MARCA / MODELO</span><br/><b style="font-size:0.85rem;">{prev["marca"]} {prev["modelo"]}</b></div>
                    <div><span style="font-size:0.68rem;color:#aaa;">Nº SERIE</span><br/><b style="font-size:0.85rem;">{prev["serie"]}</b></div>
                    <div><span style="font-size:0.68rem;color:#aaa;">CÓDIGO BIEN</span><br/><b style="font-size:0.85rem;">{prev["cod"] or "—"}</b></div>
                    <div><span style="font-size:0.68rem;color:#aaa;">SERVICIO</span><br/><b style="font-size:0.85rem;">{prev["servicio"]}</b></div>
                    <div><span style="font-size:0.68rem;color:#aaa;">MANTENIMIENTO</span><br/><b style="font-size:0.85rem;">{prev["frecuencia"]}</b></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

                ba1, ba2 = st.columns(2)
                with ba1:
                    st.download_button(
                        "⬇️ Descargar QR",
                        data=prev["bytes"],
                        file_name=f"QR_{prev['equipo'].replace(' ','_')}_{prev['serie']}.png",
                        mime="image/png",
                        key="dl_nuevo_qr",
                        use_container_width=True
                    )
                with ba2:
                    # ── GUARDAR EN INVENTARIO ─────────────────────────────────
                    ya_existe = any(
                        e.get("serie","") == prev["serie"] for e in INVENTARIO_COMPLETO
                    )
                    if ya_existe:
                        st.info("ℹ️ Este equipo ya está en el inventario.")
                    else:
                        if st.button("💾 Guardar en inventario",
                                     key="guardar_inv_btn",
                                     use_container_width=True):
                            nuevo_eq = {
                                "cod":       prev["cod"] or prev["serie"],
                                "equipo":    prev["equipo"],
                                "marca":     prev["marca"],
                                "modelo":    prev["modelo"],
                                "serie":     prev["serie"],
                                "servicio":  prev["servicio"],
                                "estado":    "BUENO",
                                "frecuencia":prev["frecuencia"],
                                "prioridad": "A",
                            }
                            db_add_inventario_extra(nuevo_eq)
                            INVENTARIO_COMPLETO.append(nuevo_eq)
                            st.session_state["inventario_extra"] = db_get_inventario_extra()
                            st.session_state["qr_preview"] = None
                            st.success(f"✅ Equipo '{prev['equipo']}' guardado en el inventario."
                                       f" Ya aparece en QR Equipos Registrados y en Reportar Falla.")
                            st.rerun()


# ── INFORMES TÉCNICOS ─────────────────────────────────────────────────────────
def pagina_informes():
    st.markdown('<div class="section-title">📝 Informe Técnico</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Formato oficial H.M.I.G.U. · Unidad de Bioingeniería</div>', unsafe_allow_html=True)

    u = st.session_state.usuarios_sistema[st.session_state.usuario]

    st.markdown('<div class="form-section"><div class="form-title">DATOS DEL EQUIPO</div>', unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        equipo_inf = st.text_input("Equipo", key="inf_eq")
        marca_inf = st.text_input("Marca", key="inf_marca")
        serie_inf = st.text_input("Nº de Serie", key="inf_serie")
    with c2:
        fecha_inf = st.date_input("Fecha", key="inf_fecha")
        modelo_inf = st.text_input("Modelo", key="inf_modelo")
        cod_bien = st.text_input("Código de Bien", key="inf_cod")
    with c3:
        estado_inf = st.selectbox("Estado", ["OPERATIVO","EN REPARACIÓN","DE BAJA"], key="inf_estado")
        servicio_inf = st.selectbox("Servicio", sorted(st.session_state.servicios_lista), key="inf_serv")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">TIPO DE MANTENIMIENTO</div>', unsafe_allow_html=True)
    c_ch = st.columns(4)
    tipos = ["Revisión Hardware", "Revisión Software", "Revisión Sistema Eléctrico",
             "Limpieza y Lubricación Sistema Mecánico", "Revisión General Funcionamiento",
             "Ajuste de Piezas", "Inspección Interna del Equipo", "Inspección Externa del Equipo"]
    for i, tipo in enumerate(tipos):
        with c_ch[i % 4]:
            st.checkbox(tipo, key=f"tipo_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">DESCRIPCIÓN</div>', unsafe_allow_html=True)
    descripcion = st.text_area("Descripción detallada del trabajo realizado", height=180, key="inf_desc",
                               placeholder="Describa el problema reportado, procedimiento realizado, pruebas efectuadas y resultado final...")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">RECOMENDACIONES</div>', unsafe_allow_html=True)
    recomendaciones = st.text_area("Recomendaciones para el personal y próximas intervenciones", height=120, key="inf_rec")
    st.markdown('</div>', unsafe_allow_html=True)

    c_f1, c_f2 = st.columns(2)
    with c_f1:
        st.text_input("Biomédico Responsable", value=u["nombre"], key="inf_biomed")
    with c_f2:
        st.text_input("Responsable de la Unidad", key="inf_jefe")

    tipos_seleccionados = [tipos[i] for i in range(len(tipos)) if st.session_state.get(f"tipo_{i}", False)]

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("💾 Guardar Informe Técnico", key="guardar_inf", use_container_width=True):
            st.success(f"✅ Informe técnico de '{equipo_inf}' guardado correctamente.")
            st.info(f"📄 Fecha: {fecha_inf} · Estado: {estado_inf} · Servicio: {servicio_inf}")
    with col_btn2:
        if st.button("📄 Generar PDF", key="gen_pdf_inf", use_container_width=True):
            biomed_val  = st.session_state.get("inf_biomed", u["nombre"])
            jefe_val    = st.session_state.get("inf_jefe", "")
            datos_pdf = {
                "tipo_doc":       "INFORME TÉCNICO DE MANTENIMIENTO",
                "equipo":         equipo_inf,
                "marca":          marca_inf,
                "modelo":         modelo_inf,
                "serie":          serie_inf,
                "cod_bien":       cod_bien,
                "fecha":          str(fecha_inf),
                "estado":         estado_inf,
                "servicio":       servicio_inf,
                "tipos":          tipos_seleccionados,
                "descripcion":    descripcion,
                "recomendaciones":recomendaciones,
                "biomed":         biomed_val,
                "jefe":           jefe_val,
            }
            try:
                pdf_bytes = generar_pdf_informe(datos_pdf)
                nombre_archivo = f"InformeTecnico_{equipo_inf.replace(' ','_')}_{str(fecha_inf)}.pdf"
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=nombre_archivo,
                    mime="application/pdf",
                    key="dl_pdf_inf",
                    use_container_width=True
                )
                st.success("✅ PDF generado. Haz clic en 'Descargar PDF' para guardarlo.")
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")


# ── INICIO DE PROCESO ─────────────────────────────────────────────────────────
def pagina_inicio_proceso():
    st.markdown('<div class="section-title">📨 Inicio de Proceso de Compra</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Formato oficial — Comunicación Interna · Gobernación de Cochabamba</div>', unsafe_allow_html=True)

    u = st.session_state.usuarios_sistema[st.session_state.usuario]

    st.markdown('<div class="form-section"><div class="form-title">ENCABEZADO DE COMUNICACIÓN INTERNA</div>', unsafe_allow_html=True)
    c1,c2 = st.columns(2)
    with c1:
        cite = st.text_input("Nº CITE", placeholder="CI / BIOMED- HMIGU / XX / 2026", key="ip_cite")
        para = st.text_input("A:", value="Dr. Antonio J. Pardo Novak — RPA", key="ip_para")
        via = st.text_input("VIA:", value="Tec. Eyver Chambilla Parra — Responsable Bienes y Servicios", key="ip_via")
    with c2:
        de_ = st.text_input("DE:", value=f"{u['nombre']} — Encargado Sección Biomédica", key="ip_de")
        fecha_ip = st.date_input("FECHA:", key="ip_fecha")
        motivo = st.text_input("MOTIVO:", placeholder="SOLICITUD DE INICIO DE PROCESO PARA ...", key="ip_motivo")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">CUERPO DE LA COMUNICACIÓN</div>', unsafe_allow_html=True)
    cuerpo = st.text_area("Descripción del proceso y justificación técnica", height=180, key="ip_cuerpo",
                           placeholder="Describir la necesidad técnica, equipos o insumos afectados, fallas identificadas y justificación de la compra...")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">DATOS DE LA SOLICITUD</div>', unsafe_allow_html=True)
    c3,c4 = st.columns(2)
    with c3:
        descripcion_bien = st.text_area("Descripción del Bien, Obra o Servicio", height=80, key="ip_bien")
        precio_ref = st.text_input("Precio Referencial (Bs.)", placeholder="20.000,00", key="ip_precio")
        cat_prog = st.text_input("Categoría Programática", value="4000099", key="ip_cat")
        partida = st.text_input("Partida Presupuestaria", value="3.9.8 Otros Repuestos y Accesorios", key="ip_partida")
    with c4:
        fuente = st.text_input("Fuente", value="20 recursos específicos", key="ip_fuente")
        organismo = st.text_input("Organismo Financiador", value="230 otros recursos específicos", key="ip_org")
        plazo = st.text_input("Plazo de entrega", value="7 días calendario", key="ip_plazo")
        metodo = st.selectbox("Método de Selección", ["Precio evaluado más bajo","Calidad","Precio y calidad"], key="ip_met")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="form-section"><div class="form-title">ESPECIFICACIONES TÉCNICAS</div>', unsafe_allow_html=True)
    if "ip_items" not in st.session_state:
        st.session_state.ip_items = [{"item":1,"desc":"","cant":"1","esp":""}]

    for idx, item in enumerate(st.session_state.ip_items):
        c_i1,c_i2,c_i3,c_i4 = st.columns([0.4,2,0.5,2.5])
        with c_i1: st.markdown(f"<br/><b>{idx+1}</b>", unsafe_allow_html=True)
        with c_i2: item["desc"] = st.text_input("Descripción", key=f"ip_desc_{idx}", value=item.get("desc",""), label_visibility="collapsed")
        with c_i3: item["cant"] = st.text_input("Cant.", key=f"ip_cant_{idx}", value=item.get("cant","1"), label_visibility="collapsed")
        with c_i4: item["esp"] = st.text_input("Especificaciones", key=f"ip_esp_{idx}", value=item.get("esp",""), label_visibility="collapsed")

    if st.button("➕ Agregar ítem", key="ip_add"):
        st.session_state.ip_items.append({"item":len(st.session_state.ip_items)+1,"desc":"","cant":"1","esp":""})
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    c_f1, c_f2 = st.columns(2)
    with c_f1:
        st.text_input("Elaborado por", value=u["nombre"], key="ip_elab")
    with c_f2:
        st.text_input("Cargo", value=u["rol"], key="ip_cargo")

    col_ip1, col_ip2 = st.columns(2)
    with col_ip1:
        if st.button("💾 Guardar Inicio de Proceso", key="guardar_ip", use_container_width=True):
            st.success(f"✅ Inicio de proceso '{motivo}' guardado correctamente.")
    with col_ip2:
        if st.button("📄 Generar PDF", key="gen_pdf_ip", use_container_width=True):
            elab_val  = st.session_state.get("ip_elab", u["nombre"])
            cargo_val = st.session_state.get("ip_cargo", u["rol"])
            datos_pdf_ip = {
                "cite":      cite,
                "fecha":     str(fecha_ip),
                "para":      para,
                "via":       via,
                "de_":       de_,
                "motivo":    motivo,
                "cuerpo":    cuerpo,
                "precio":    precio_ref,
                "plazo":     plazo,
                "cat_prog":  cat_prog,
                "partida":   partida,
                "fuente":    fuente,
                "organismo": organismo,
                "metodo":    metodo,
                "items":     st.session_state.get("ip_items",[]),
                "elaborado": elab_val,
                "cargo":     cargo_val,
            }
            try:
                pdf_bytes = generar_pdf_inicio_proceso(datos_pdf_ip)
                nombre_ip = f"InicioProceso_{motivo[:30].replace(' ','_')}.pdf"
                st.download_button(
                    label="⬇️ Descargar PDF",
                    data=pdf_bytes,
                    file_name=nombre_ip,
                    mime="application/pdf",
                    key="dl_pdf_ip",
                    use_container_width=True
                )
                st.success("✅ PDF generado. Haz clic en 'Descargar PDF' para guardarlo.")
            except Exception as e:
                st.error(f"Error al generar PDF: {e}")


# ── ADMINISTRAR USUARIOS Y SERVICIOS ──────────────────────────────────────────
def pagina_usuarios():
    st.markdown('<div class="section-title">👥 Administrar</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Gestión de usuarios y servicios del sistema</div>', unsafe_allow_html=True)

    tab_users, tab_servs = st.tabs(["👤 Usuarios", "🏥 Servicios"])

    # ── TAB USUARIOS ──────────────────────────────────────────────────────────
    with tab_users:
        usuarios = st.session_state.usuarios_sistema

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">Usuarios registrados en el sistema</div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="tabla-header" style="grid-template-columns:1.5fr 2fr 1.5fr 1fr 0.6fr;">
          <span>Usuario</span><span>Nombre</span><span>Rol</span><span>Tipo</span><span>Acción</span>
        </div>
        """, unsafe_allow_html=True)
        iconos_t = {"ingeniero":"⚙️","medico":"🩺","enfermera":"💊","administrativo":"🗂️"}
        user_actual = st.session_state.usuario
        for user, data in list(usuarios.items()):
            c1,c2,c3,c4,c5 = st.columns([1.5,2,1.5,1,0.6])
            with c1: st.markdown(f'<span style="color:#1a56a8;font-weight:600;font-size:0.82rem;">{user}</span>', unsafe_allow_html=True)
            with c2: st.markdown(f'<span style="font-size:0.82rem;">{data["nombre"]}</span>', unsafe_allow_html=True)
            with c3: st.markdown(f'<span style="font-size:0.8rem;color:#555;">{data["rol"]}</span>', unsafe_allow_html=True)
            with c4: st.markdown(f'{iconos_t.get(data["tipo"],"👤")} <span style="font-size:0.78rem;">{data["tipo"].capitalize()}</span>', unsafe_allow_html=True)
            with c5:
                if user != user_actual:
                    if st.button("🗑️", key=f"del_user_{user}", help=f"Eliminar {user}"):
                        st.session_state[f"confirm_del_user_{user}"] = True
            st.markdown('<hr style="margin:0;border-color:#f0f0f0;"/>', unsafe_allow_html=True)

            if st.session_state.get(f"confirm_del_user_{user}", False):
                st.warning(f"⚠️ ¿Eliminar al usuario **{user}** ({data['nombre']})? Esta acción no se puede deshacer.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ Sí, eliminar", key=f"yes_del_user_{user}", use_container_width=True):
                        conn = get_conn()
                        conn.execute("DELETE FROM usuarios WHERE username = ?", (user,))
                        conn.commit()
                        conn.close()
                        st.session_state.usuarios_sistema = db_get_usuarios()
                        st.session_state.pop(f"confirm_del_user_{user}", None)
                        st.success(f"✅ Usuario '{user}' eliminado.")
                        st.rerun()
                with cc2:
                    if st.button("❌ Cancelar", key=f"no_del_user_{user}", use_container_width=True):
                        st.session_state.pop(f"confirm_del_user_{user}", None)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### ➕ Agregar Nuevo Usuario")
        with st.expander("Registrar nuevo usuario"):
            c1,c2 = st.columns(2)
            with c1:
                nu_user   = st.text_input("Nombre de usuario", placeholder="ing.apellido", key="nu_user")
                nu_nombre = st.text_input("Nombre completo", key="nu_nombre")
                nu_pass   = st.text_input("Contraseña", type="password", key="nu_pass")
            with c2:
                nu_rol  = st.text_input("Cargo/Rol", key="nu_rol")
                nu_tipo = st.selectbox("Tipo de usuario", ["ingeniero","medico","enfermera","administrativo"], key="nu_tipo")

            if st.button("👤 Registrar usuario", key="reg_user", use_container_width=True):
                if nu_user and nu_nombre and nu_pass:
                    if nu_user not in st.session_state.usuarios_sistema:
                        db_add_usuario(nu_user, nu_pass, nu_nombre, nu_rol, nu_tipo)
                        st.session_state.usuarios_sistema = db_get_usuarios()
                        st.success(f"✅ Usuario '{nu_user}' registrado y guardado.")
                        st.rerun()
                    else:
                        st.warning("⚠️ Ese nombre de usuario ya existe.")
                else:
                    st.warning("Complete usuario, nombre completo y contraseña.")

    # ── TAB SERVICIOS ─────────────────────────────────────────────────────────
    with tab_servs:
        servicios = st.session_state.servicios_lista

        st.markdown(f'<div style="margin-bottom:14px;font-size:0.85rem;color:#555;">'
                    f'<b>{len(servicios)}</b> servicios registrados en el sistema</div>',
                    unsafe_allow_html=True)

        # ── Lista de servicios con botón eliminar ─────────────────────────────
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">Servicios / Áreas del Hospital</div>', unsafe_allow_html=True)
        for idx_s, serv in enumerate(sorted(servicios)):
            cs1, cs2 = st.columns([6, 0.7])
            with cs1:
                st.markdown(
                    f'<div style="padding:8px 0;font-size:0.85rem;color:#333;">' +
                    f'🏥 {serv}</div>',
                    unsafe_allow_html=True
                )
            with cs2:
                if st.button("🗑️", key=f"del_serv_{idx_s}", help=f"Eliminar {serv}"):
                    st.session_state[f"confirm_del_serv_{serv}"] = True
            st.markdown('<hr style="margin:0;border-color:#f0f0f0;"/>', unsafe_allow_html=True)

            if st.session_state.get(f"confirm_del_serv_{serv}", False):
                st.warning(f"⚠️ ¿Eliminar el servicio **{serv}**? Los reportes existentes no se verán afectados.")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("✅ Sí, eliminar", key=f"yes_del_s_{idx_s}", use_container_width=True):
                        db_delete_servicio(serv)
                        st.session_state.servicios_lista = db_get_servicios()
                        st.session_state.pop(f"confirm_del_serv_{serv}", None)
                        st.success(f"✅ Servicio '{serv}' eliminado.")
                        st.rerun()
                with dc2:
                    if st.button("❌ Cancelar", key=f"no_del_s_{idx_s}", use_container_width=True):
                        st.session_state.pop(f"confirm_del_serv_{serv}", None)
                        st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # ── Agregar nuevo servicio ────────────────────────────────────────────
        st.markdown("---")
        st.markdown("#### ➕ Agregar Nuevo Servicio")
        with st.expander("Registrar nuevo servicio o área"):
            nuevo_serv = st.text_input("Nombre del servicio / área",
                                       placeholder="Ej: Unidad de Quemados",
                                       key="nuevo_serv_nombre")
            if st.button("🏥 Agregar servicio", key="add_serv_btn", use_container_width=True):
                if nuevo_serv.strip():
                    if nuevo_serv.strip() in st.session_state.servicios_lista:
                        st.warning("⚠️ Ese servicio ya existe.")
                    else:
                        db_add_servicio(nuevo_serv.strip())
                        st.session_state.servicios_lista = db_get_servicios()
                        st.success(f"✅ Servicio '{nuevo_serv.strip()}' agregado correctamente.")
                        st.rerun()
                else:
                    st.warning("Escriba el nombre del servicio.")




# ══════════════════════════════════════════════════════════════════════════════
#  DATOS: CIRUGÍAS
# ══════════════════════════════════════════════════════════════════════════════

QUIROFANOS = ["Quirófano 1","Quirófano 2","Quirófano 3","Quirófano 4","Quirófano Área Verde"]
TIPOS_CIRUGIA = [
    "Cesárea","Histerectomía Laparoscópica","Histerectomía Abdominal Total",
    "Histeroscopía","Salpingo-ooforectomía Laparoscópica","Salpingo-ooforectomía Abdominal",
    "Laparoscopía Diagnóstica","Laparoscopía Operatoria","Quistectomía Laparoscópica",
    "Quistectomía Ovárica","Legrado Uterino","Colposcopía","Conización Cervical",
    "Mastectomía Simple","Mastectomía Radical Modificada","Nodulectomía","Biopsia Excisional",
    "Cistoscopía","Infiltración","Apendicectomía","Colecistectomía Laparoscópica",
    "Herniorrafia","Otro procedimiento",
]
ESTADOS_CIRUGIA = ["Programada","En curso","Completada","Cancelada","Postpuesta"]
ANESTESIAS = ["General","Raquidea","Epidural","Local","Sedación"]
CIRUGIAS_ING = ["Laparoscopía","Histerectomía Laparoscópica","Histeroscopía",
                "Salpingo-ooforectomía Laparoscópica","Cistoscopía",
                "Laparoscopía Diagnóstica","Quistectomía Laparoscópica",
                "Laparoscopía Operatoria","Colecistectomía Laparoscópica"]

def init_cirugias():
    if "cirugias" not in st.session_state:
        hoy = date.today().strftime("%Y-%m-%d")
        st.session_state.cirugias = [
            {"id":"CIR-001","fecha":hoy,"hora":"07:30","quirofano":"Quirófano 3",
             "tipo":"Histerectomía Laparoscópica","cirujano":"Dr. Mamani","anestesia":"General",
             "estado":"Programada","requiere_ing":True,"equipo_esp":"Torre de Laparoscopía STORZ",
             "obs":"Verificar torre STORZ antes de las 07:00","programado_por":"Dr. García"},
            {"id":"CIR-002","fecha":hoy,"hora":"09:00","quirofano":"Quirófano 2",
             "tipo":"Cesárea","cirujano":"Dra. Flores","anestesia":"Raquidea",
             "estado":"Programada","requiere_ing":False,"equipo_esp":"Monitor DRAGER INFINITY C700",
             "obs":"","programado_por":"Dr. García"},
            {"id":"CIR-003","fecha":hoy,"hora":"10:30","quirofano":"Quirófano Área Verde",
             "tipo":"Histeroscopía","cirujano":"Dr. Quiroga","anestesia":"Sedación",
             "estado":"Programada","requiere_ing":True,"equipo_esp":"Equipo Histeroscopía OLYMPUS",
             "obs":"Revisar óptica y fuente de luz","programado_por":"Dra. Torres"},
            {"id":"CIR-004","fecha":hoy,"hora":"11:30","quirofano":"Quirófano 3",
             "tipo":"Salpingo-ooforectomía Laparoscópica","cirujano":"Dr. Mamani","anestesia":"General",
             "estado":"Programada","requiere_ing":True,"equipo_esp":"Torre de Laparoscopía STORZ",
             "obs":"","programado_por":"Dr. García"},
            {"id":"CIR-005","fecha":hoy,"hora":"13:00","quirofano":"Quirófano 2",
             "tipo":"Mastectomía Simple","cirujano":"Dr. Ríos","anestesia":"General",
             "estado":"Programada","requiere_ing":False,"equipo_esp":"Electrobisturí UZUMCU EK-410",
             "obs":"","programado_por":"Dra. Torres"},
            {"id":"CIR-006","fecha":hoy,"hora":"14:30","quirofano":"Quirófano 4",
             "tipo":"Quistectomía Laparoscópica","cirujano":"Dra. Condori","anestesia":"General",
             "estado":"Programada","requiere_ing":True,"equipo_esp":"Equipo Anestesia DRAGER TITUS",
             "obs":"","programado_por":"Dr. García"},
        ]

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO A: PROGRAMACIÓN DE CIRUGÍAS — MÉDICO (programa) / ING (visualiza)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_reportar_falla():
    """Panel médico: escaneo simulado de QR + formulario de reporte → guarda en SQLite."""
    u = st.session_state.usuarios_sistema[st.session_state.usuario]

    st.markdown('<div class="section-title">🔴 Reportar Falla de Equipo</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Seleccione el área, identifique el equipo y complete el formulario</div>', unsafe_allow_html=True)

    col_form, col_result = st.columns([1.2, 1])

    with col_form:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown('<div class="form-title">📷 Identificar Equipo (Simulador QR)</div>', unsafe_allow_html=True)
        st.markdown('<div style="font-size:0.8rem;color:#666;margin-bottom:14px;">En producción el médico escanea el QR físico del equipo. Aquí selecciónelo manualmente.</div>', unsafe_allow_html=True)

        servicios_inv = sorted(st.session_state.servicios_lista)
        serv_sel = st.selectbox("Área / Servicio", servicios_inv, key="rf_serv")
        equipos_area = [e for e in INVENTARIO_COMPLETO if e["servicio"] == serv_sel]
        nombres_eq   = [e["equipo"] for e in equipos_area]
        eq_sel_nom   = st.selectbox("Equipo", nombres_eq, key="rf_eq")
        eq_sel = next((e for e in equipos_area if e["equipo"] == eq_sel_nom), None)

        if eq_sel:
            import qrcode as _qrcode
            info_qr = (f"MEDTRACK-HMIGU\nEquipo: {eq_sel['equipo']}\n"
                       f"Marca: {eq_sel['marca']}\nModelo: {eq_sel['modelo']}\n"
                       f"Serie: {eq_sel['serie']}\nServicio: {eq_sel['servicio']}\n"
                       f"Código: {eq_sel['cod']}")
            qr = _qrcode.QRCode(version=1, box_size=5, border=2)
            qr.add_data(info_qr)
            qr.make(fit=True)
            img_qr = qr.make_image(fill_color="#0d2656", back_color="white")
            buf_qr = io.BytesIO()
            img_qr.save(buf_qr, format="PNG")
            b64_qr = base64.b64encode(buf_qr.getvalue()).decode()
            st.markdown(f"""
            <div style="border:2px dashed #c8d4e8;border-radius:10px;padding:14px;
                        text-align:center;margin:10px 0;">
              <img src="data:image/png;base64,{b64_qr}" style="width:130px;height:130px;"/>
              <div style="font-weight:700;color:#0d2656;margin-top:8px;font-size:0.85rem;">{eq_sel['equipo']}</div>
              <div style="font-size:0.75rem;color:#888;">{eq_sel['servicio']}</div>
              <div style="font-size:0.68rem;color:#aaa;">H.M.I. Germán Urquidi · MedTrack</div>
            </div>
            """, unsafe_allow_html=True)

        if st.button("✅ Simular escaneo de QR", use_container_width=True, key="sim_qr_btn"):
            st.session_state["qr_escaneado"] = eq_sel
        st.markdown('</div>', unsafe_allow_html=True)

    with col_result:
        eq = st.session_state.get("qr_escaneado")
        if eq:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown('<div class="form-title">✅ Equipo identificado — Completar reporte</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div style="background:#f0f8ff;border-radius:8px;padding:12px;margin-bottom:14px;">
              <div style="font-size:0.9rem;font-weight:700;color:#0d2656;">{eq['equipo']}</div>
              <div style="font-size:0.75rem;color:#555;margin-top:4px;">
                Serie: {eq['serie']} &nbsp;·&nbsp; Código: {eq['cod']}<br/>
                Servicio: {eq['servicio']}
              </div>
            </div>
            """, unsafe_allow_html=True)

            desc_falla = st.text_area("Descripción de la falla observada", height=120,
                                      placeholder="Describa el problema con detalle...",
                                      key="rf_desc_falla")
            prio_rep   = st.selectbox("Prioridad", ["Alta","Media","Baja"], key="rf_prio_rep")

            if st.button("📥 Enviar Reporte a Bioingeniería", use_container_width=True, key="enviar_rep_btn"):
                if desc_falla.strip():
                    num     = len(st.session_state.reportes) + 1
                    cod_rep = f"REP-2026-{num:03d}"
                    nuevo_r = {
                        "reporte":       cod_rep,
                        "codigo":        eq["cod"],
                        "nombre":        eq["equipo"],
                        "servicio":      eq["servicio"],
                        "marca":         eq["marca"],
                        "modelo":        eq["modelo"],
                        "serie":         eq["serie"],
                        "prioridad":     prio_rep,
                        "estado":        "Pendiente",
                        "fecha":         datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "descripcion":   desc_falla,
                        "reportado_por": u["nombre"],
                    }
                    db_add_reporte(nuevo_r)
                    st.session_state.reportes = db_get_reportes()
                    st.session_state["qr_escaneado"] = None
                    st.success(f"✅ Reporte **{cod_rep}** enviado y guardado. Bioingeniería fue notificada.")
                    st.rerun()
                else:
                    st.warning("⚠️ Describa la falla antes de enviar.")
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="card" style="text-align:center;padding:50px 20px;">
              <div style="font-size:3rem;margin-bottom:12px;">📷</div>
              <div style="font-size:1rem;font-weight:700;color:#0d2656;margin-bottom:8px;">
                Escanee primero el código QR
              </div>
              <div style="font-size:0.8rem;color:#aaa;">
                Seleccione el área y equipo a la izquierda,<br/>
                luego haga clic en "Simular escaneo".
              </div>
            </div>
            """, unsafe_allow_html=True)


def pagina_cirugias():
    init_cirugias()
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    es_medico = u["tipo"] in ["medico","enfermera"]
    hoy = date.today()
    hoy_display = hoy.strftime("%d de %B de %Y")

    st.markdown('<div class="section-title">🏥 Programación de Cirugías</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">Cirugías del día · {hoy_display}</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1: fecha_sel = st.date_input("📅 Fecha", value=hoy, key="cir_fecha_v")
    with col_f2: filtro_qx = st.selectbox("Quirófano", ["Todos"]+QUIROFANOS, key="cir_qx_v")
    with col_f3:
        if not es_medico:
            filtro_ing = st.selectbox("Ver", ["Todas","Solo requieren Bioingeniería"], key="cir_filt_ing")
        else:
            filtro_ing = "Todas"

    fecha_str = fecha_sel.strftime("%Y-%m-%d")
    cirugias = [c for c in st.session_state.cirugias if c["fecha"] == fecha_str]
    if filtro_qx != "Todos": cirugias = [c for c in cirugias if c["quirofano"] == filtro_qx]
    if filtro_ing == "Solo requieren Bioingeniería": cirugias = [c for c in cirugias if c.get("requiere_ing")]

    # Resumen
    total = len([c for c in st.session_state.cirugias if c["fecha"] == fecha_str])
    ing_n = sum(1 for c in st.session_state.cirugias if c["fecha"]==fecha_str and c.get("requiere_ing"))
    prog  = sum(1 for c in st.session_state.cirugias if c["fecha"]==fecha_str and c["estado"]=="Programada")
    comp  = sum(1 for c in st.session_state.cirugias if c["fecha"]==fecha_str and c["estado"]=="Completada")

    c1,c2,c3,c4 = st.columns(4)
    for col,num,label,color,ico in [
        (c1,total,"Total del día","#0d2656","🏥"),
        (c2,prog,"Programadas","#084298","📋"),
        (c3,ing_n,"Requieren Bioingeniería","#856404","⚙️"),
        (c4,comp,"Completadas","#0a3622","✅"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div style="font-size:1.3rem;">{ico}</div>'
                        f'<div class="metric-num" style="color:{color};">{num}</div>'
                        f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if not cirugias:
        st.markdown('<div class="card" style="text-align:center;padding:40px;">'
                    '<div style="font-size:2.5rem;">🗓️</div>'
                    '<div style="color:#888;margin-top:10px;">No hay cirugías para esta fecha.</div></div>',
                    unsafe_allow_html=True)
    else:
        estado_cfg = {
            "Programada":  ("cb-azul","📋"),
            "En curso":    ("cb-amarillo","🔄"),
            "Completada":  ("cb-verde","✅"),
            "Cancelada":   ("badge-alta","❌"),
            "Postpuesta":  ("badge-media","⏸️"),
        }
        for c in sorted(cirugias, key=lambda x: x["hora"]):
            req    = bool(c.get("requiere_ing", False))
            borde  = "#ffc107" if req else "#1a56a8"
            ecls, eico = estado_cfg.get(c["estado"], ("cb-azul","📋"))

            # Build HTML parts as plain strings (no f-string nesting)
            hora_v     = str(c.get("hora","") or "")
            tipo_v     = str(c.get("tipo","") or "")
            qx_v       = str(c.get("quirofano","") or "")
            cir_v      = str(c.get("cirujano","") or "")
            anest_v    = str(c.get("anestesia","") or "")
            eq_v       = str(c.get("equipo_esp","") or "")
            obs_v      = str(c.get("obs","") or "")
            prog_v     = str(c.get("programado_por","—") or "—")
            estado_v   = str(c.get("estado","") or "Programada")
            cid_v      = str(c.get("id","") or "")

            ing_html  = '<span style="background:#fff3cd;color:#856404;font-size:0.68rem;font-weight:700;padding:2px 8px;border-radius:20px;margin-left:6px;">⚙️ Bioingeniería</span>' if req else ""
            eq_html   = ('<div style="font-size:0.75rem;color:#555;margin-top:4px;">🔧 <b>' + eq_v + '</b></div>') if eq_v else ""
            obs_html  = ('<div style="font-size:0.72rem;color:#e67e22;margin-top:4px;background:#fff8ee;padding:4px 10px;border-radius:6px;display:inline-block;">⚠️ ' + obs_v + '</div>') if obs_v else ""
            prog_html = '<div style="font-size:0.7rem;color:#aaa;margin-top:4px;">👤 Programado por: ' + prog_v + '</div>'
            badge_html = '<span class="badge ' + ecls + '">' + eico + " " + estado_v + '</span>'

            html_card = (
                '<div style="background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:10px;' +
                'box-shadow:0 2px 10px rgba(0,0,0,0.07);border-left:5px solid ' + borde + ';">' +
                '<div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;">' +
                '<div>' +
                '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">' +
                '<span style="font-size:1.15rem;font-weight:800;color:#0d2656;">' + hora_v + '</span>' +
                '<span style="font-size:1rem;font-weight:700;color:#1a2340;">' + tipo_v + '</span>' +
                ing_html +
                '</div>' +
                '<div style="font-size:0.78rem;color:#555;margin-top:4px;">🏥 <b>' + qx_v + '</b> &nbsp;·&nbsp; 👨‍⚕️ ' + cir_v + ' &nbsp;·&nbsp; 💉 ' + anest_v + '</div>' +
                eq_html + obs_html + prog_html +
                '</div>' +
                '<div style="text-align:right;">' + badge_html +
                '<div style="font-size:0.7rem;color:#aaa;margin-top:4px;">' + cid_v + '</div></div>' +
                '</div></div>'
            )
            st.markdown(html_card, unsafe_allow_html=True)

            if not es_medico:
                ca, cb_, cc = st.columns([2,1,4])
                with ca:
                    nuevo_est = st.selectbox("", ESTADOS_CIRUGIA,
                        index=ESTADOS_CIRUGIA.index(c["estado"]),
                        key="est_cir_" + cid_v, label_visibility="collapsed")
                with cb_:
                    if st.button("💾", key="sv_cir_" + cid_v, help="Guardar estado"):
                        db_update_cirugia_estado(cid_v, nuevo_est)
                        st.session_state.cirugias = db_get_cirugias()
                        st.rerun()

    # ── MÉDICO: Registrar nueva cirugía ─────────────────────────────────────
    if es_medico:
        st.markdown("<br/>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#1a56a8;border-radius:12px;padding:16px 20px;margin-bottom:6px;">
          <div style="color:#fff;font-size:1.1rem;font-weight:700;">➕ Programar Nueva Cirugía</div>
          <div style="color:rgba(255,255,255,0.75);font-size:0.8rem;margin-top:2px;">
            Complete el formulario para agregar una cirugía al programa del día.
            Bioingeniería será notificada automáticamente si requiere su presencia.
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.container():
            st.markdown('<div class="form-section">', unsafe_allow_html=True)

            nc1, nc2 = st.columns(2)
            with nc1:
                n_fecha  = st.date_input("📅 Fecha de la cirugía", value=hoy, key="nc_fecha")
                n_hora   = st.text_input("🕐 Hora (HH:MM)", placeholder="07:30", key="nc_hora")
                n_qx     = st.selectbox("🏥 Quirófano", QUIROFANOS, key="nc_qx")
                n_tipo   = st.selectbox("🔪 Tipo de cirugía", TIPOS_CIRUGIA, key="nc_tipo")
                n_anest  = st.selectbox("💉 Tipo de anestesia", ANESTESIAS, key="nc_anest")
            with nc2:
                n_cir    = st.text_input("👨‍⚕️ Cirujano responsable", key="nc_cir")
                n_equipo = st.text_input("🔧 Equipo especializado requerido", key="nc_equipo")
                n_obs    = st.text_area("📝 Observaciones para Bioingeniería", height=100, key="nc_obs",
                                        placeholder="Ej: Verificar torre de laparoscopía antes de las 07:00...")
                # Auto-detect si requiere ingeniería
                req_auto = n_tipo in CIRUGIAS_ING
                if req_auto:
                    st.markdown("""
                    <div style="background:#fff3cd;border-radius:8px;padding:8px 12px;
                                border-left:3px solid #ffc107;font-size:0.78rem;color:#856404;margin-top:6px;">
                      ⚙️ <b>Esta cirugía requiere presencia de Bioingeniería</b> (detectado automáticamente)
                    </div>
                    """, unsafe_allow_html=True)
                    n_req = True
                else:
                    n_req = st.checkbox("⚙️ Requiere presencia de Bioingeniería", key="nc_req")

            st.markdown('</div>', unsafe_allow_html=True)

            # Botón prominente
            col_reg, col_cancel = st.columns([3, 1])
            with col_reg:
                if st.button("📥 Confirmar y Programar Cirugía", key="reg_cir_med",
                             use_container_width=True):
                    if n_hora and n_cir and n_tipo:
                        num = len(st.session_state.cirugias) + 1
                        nueva_cir = {
                            "id": f"CIR-{num:03d}",
                            "fecha": n_fecha.strftime("%Y-%m-%d"),
                            "hora": n_hora,
                            "quirofano": n_qx,
                            "tipo": n_tipo,
                            "cirujano": n_cir,
                            "anestesia": n_anest,
                            "estado": "Programada",
                            "requiere_ing": n_req,
                            "equipo_esp": n_equipo,
                            "obs": n_obs,
                            "programado_por": u["nombre"],
                        }
                        db_add_cirugia(nueva_cir)
                        st.session_state.cirugias = db_get_cirugias()
                        msg = f"✅ Cirugía **{nueva_cir['id']}** — {n_tipo} — {n_hora}h en {n_qx} programada y guardada."
                        if n_req:
                            msg += " ⚙️ Bioingeniería fue notificada."
                        st.success(msg)
                        st.rerun()
                    else:
                        if not n_hora:
                            st.warning("⚠️ Ingrese la hora de la cirugía.")
                        elif not n_cir:
                            st.warning("⚠️ Ingrese el cirujano responsable.")
                        else:
                            st.warning("⚠️ Seleccione el tipo de cirugía.")

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO B: CALENDARIO DE MANTENIMIENTOS (ingeniero)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_mantenimientos():
    from datetime import timedelta
    st.markdown('<div class="section-title">🔧 Calendario de Mantenimientos</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Equipos con mantenimiento próximo o vencido</div>', unsafe_allow_html=True)

    hoy = date.today()
    # Simulate last maintenance dates and calculate next
    freq_dias = {"TRIMESTRAL":90,"SEMESTRAL":180,"ANUAL":365,"CUATRIMESTRAL":120}

    import random
    random.seed(42)
    equipos_mant = []
    for eq in INVENTARIO_COMPLETO:
        dias = freq_dias.get(eq["frecuencia"], 180)
        dias_desde = random.randint(0, dias)
        ultimo = hoy - timedelta(days=dias_desde)
        proximo = ultimo + timedelta(days=dias)
        dias_faltan = (proximo - hoy).days
        if dias_faltan < 0:   estado_m = "VENCIDO"
        elif dias_faltan <= 15: estado_m = "PRÓXIMO"
        elif dias_faltan <= 30: estado_m = "ALERTA"
        else:                  estado_m = "AL DÍA"
        equipos_mant.append({**eq,
            "ultimo_mant": ultimo.strftime("%d/%m/%Y"),
            "proximo_mant": proximo.strftime("%d/%m/%Y"),
            "dias_faltan": dias_faltan,
            "estado_mant": estado_m
        })

    # KPIs
    vencidos = sum(1 for e in equipos_mant if e["estado_mant"]=="VENCIDO")
    proximos = sum(1 for e in equipos_mant if e["estado_mant"]=="PRÓXIMO")
    alerta   = sum(1 for e in equipos_mant if e["estado_mant"]=="ALERTA")
    al_dia   = sum(1 for e in equipos_mant if e["estado_mant"]=="AL DÍA")

    c1,c2,c3,c4 = st.columns(4)
    for col,num,label,color,ico in [
        (c1,vencidos,"Vencidos","#842029","🔴"),
        (c2,proximos,"Próximos (≤15 días)","#856404","⚠️"),
        (c3,alerta,"Alerta (≤30 días)","#b85c00","🟡"),
        (c4,al_dia,"Al día","#0a3622","✅"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div style="font-size:1.3rem;">{ico}</div>'
                        f'<div class="metric-num" style="color:{color};">{num}</div>'
                        f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    # Filters
    cf1,cf2,cf3 = st.columns(3)
    with cf1: f_serv = st.selectbox("Servicio", ["Todos"]+sorted(st.session_state.servicios_lista), key="mant_serv")
    with cf2: f_est  = st.selectbox("Estado", ["Todos","VENCIDO","PRÓXIMO","ALERTA","AL DÍA"], key="mant_est")
    with cf3: f_freq = st.selectbox("Frecuencia", ["Todas","TRIMESTRAL","SEMESTRAL","CUATRIMESTRAL","ANUAL"], key="mant_freq")

    filtrados = equipos_mant
    if f_serv != "Todos": filtrados = [e for e in filtrados if e["servicio"]==f_serv]
    if f_est  != "Todos": filtrados = [e for e in filtrados if e["estado_mant"]==f_est]
    if f_freq != "Todas": filtrados = [e for e in filtrados if e["frecuencia"]==f_freq]
    filtrados = sorted(filtrados, key=lambda x: x["dias_faltan"])

    color_est = {"VENCIDO":"#f8d7da","PRÓXIMO":"#fff3cd","ALERTA":"#fff8e0","AL DÍA":"#d1e7dd"}
    text_est  = {"VENCIDO":"#842029","PRÓXIMO":"#856404","ALERTA":"#b85c00","AL DÍA":"#0a3622"}

    st.markdown(f'<div style="font-size:0.85rem;color:#555;margin-bottom:10px;"><b>{len(filtrados)}</b> equipo(s)</div>', unsafe_allow_html=True)

    for eq in filtrados:
        c_est  = color_est.get(eq["estado_mant"],"#f0f0f0")
        t_est  = text_est.get(eq["estado_mant"],"#333")
        faltan_txt = f"Vencido hace {abs(eq['dias_faltan'])} días" if eq["dias_faltan"]<0 else f"Faltan {eq['dias_faltan']} días"
        st.markdown(f"""
        <div style="background:#fff;border-radius:10px;padding:14px 18px;margin-bottom:8px;
                    box-shadow:0 1px 6px rgba(0,0,0,0.06);
                    border-left:4px solid {t_est};">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
            <div>
              <div style="font-size:0.88rem;font-weight:700;color:#0d2656;">{eq['equipo']}</div>
              <div style="font-size:0.75rem;color:#666;margin-top:2px;">
                📍 {eq['servicio']} &nbsp;·&nbsp; Serie: {eq['serie']} &nbsp;·&nbsp; {eq['frecuencia']}
              </div>
              <div style="font-size:0.73rem;color:#888;margin-top:2px;">
                Último: {eq['ultimo_mant']} &nbsp;·&nbsp; Próximo: {eq['proximo_mant']}
              </div>
            </div>
            <div style="text-align:right;">
              <span style="background:{c_est};color:{t_est};padding:4px 12px;border-radius:20px;font-size:0.72rem;font-weight:700;">{eq['estado_mant']}</span>
              <div style="font-size:0.72rem;color:{t_est};margin-top:4px;font-weight:600;">{faltan_txt}</div>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO C: HISTORIAL DE INTERVENCIONES (ingeniero)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_historial():
    st.markdown('<div class="section-title">📂 Historial de Intervenciones</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Registro cronológico de todos los informes técnicos y mantenimientos</div>', unsafe_allow_html=True)

    if "historial" not in st.session_state:
        st.session_state.historial = [
            {"id":"INF-001","fecha":"20/06/2026","equipo":"Ventilador Neonatal COMEN V2",
             "serie":"2C250917116","servicio":"Neonatología I (UCIN I)","tipo":"Preventivo",
             "estado":"OPERATIVO","tecnico":"Ing. Denis Ramírez",
             "descripcion":"Revisión semestral completa. Limpieza de filtros, calibración de sensores de flujo y presión. Todas las alarmas funcionando correctamente."},
            {"id":"INF-002","fecha":"18/06/2026","equipo":"Desfibrilador MEDTRONIK LIFEPAK 12",
             "serie":"33586958","servicio":"Quirófano 3","tipo":"Correctivo",
             "estado":"EN REPARACIÓN","tecnico":"Ing. Denis Ramírez",
             "descripcion":"Falla en módulo de carga reportada por personal médico. Se identificó capacitor defectuoso. Equipo en espera de repuesto."},
            {"id":"INF-003","fecha":"15/06/2026","equipo":"Monitor Multiparamétrico PHILIPS MX550",
             "serie":"DE671Y4710","servicio":"Terapia Intensiva","tipo":"Preventivo",
             "estado":"OPERATIVO","tecnico":"Ing. Flores",
             "descripcion":"Mantenimiento semestral. Verificación de todos los módulos. Batería reemplazada. Equipo en óptimas condiciones."},
            {"id":"INF-004","fecha":"10/06/2026","equipo":"Bomba de Infusión MINDRAY BeneFusion",
             "serie":"SH2-59120043","servicio":"Neonatología I (UCIN I)","tipo":"Correctivo",
             "estado":"OPERATIVO","tecnico":"Ing. Denis Ramírez",
             "descripcion":"Error en pantalla de oclusión. Limpieza de sensor de presión. Equipo restaurado y verificado."},
        ]

    hf1, hf2, hf3 = st.columns(3)
    with hf1: f_tipo = st.selectbox("Tipo", ["Todos","Preventivo","Correctivo"], key="hist_tipo")
    with hf2: f_est  = st.selectbox("Estado", ["Todos","OPERATIVO","EN REPARACIÓN","DE BAJA"], key="hist_est")
    with hf3: f_bus  = st.text_input("Buscar equipo", placeholder="Escriba para filtrar...", key="hist_bus")

    hist = st.session_state.historial
    if f_tipo != "Todos": hist = [h for h in hist if h["tipo"]==f_tipo]
    if f_est  != "Todos": hist = [h for h in hist if h["estado"]==f_est]
    if f_bus:             hist = [h for h in hist if f_bus.lower() in h["equipo"].lower()]

    st.markdown(f'<div style="font-size:0.85rem;color:#555;margin:10px 0;"><b>{len(hist)}</b> registro(s)</div>', unsafe_allow_html=True)

    tipo_color = {"Preventivo":"#cfe2ff","Correctivo":"#f8d7da"}
    tipo_text  = {"Preventivo":"#084298","Correctivo":"#842029"}
    est_color  = {"OPERATIVO":"#d1e7dd","EN REPARACIÓN":"#fff3cd","DE BAJA":"#f8d7da"}
    est_text   = {"OPERATIVO":"#0a3622","EN REPARACIÓN":"#856404","DE BAJA":"#842029"}

    for h in hist:
        tc = tipo_color.get(h["tipo"],"#eee"); tt = tipo_text.get(h["tipo"],"#333")
        ec = est_color.get(h["estado"],"#eee"); et = est_text.get(h["estado"],"#333")
        with st.expander(f"📄 {h['id']} — {h['equipo']} · {h['fecha']}"):
            col_a, col_b = st.columns([2,1])
            with col_a:
                st.markdown(f"""
                <div style="margin-bottom:10px;">
                  <div style="font-size:0.9rem;font-weight:700;color:#0d2656;">{h['equipo']}</div>
                  <div style="font-size:0.78rem;color:#666;">📍 {h['servicio']} &nbsp;·&nbsp; Serie: {h['serie']}</div>
                  <div style="font-size:0.78rem;color:#666;">👷 {h['tecnico']} &nbsp;·&nbsp; 📅 {h['fecha']}</div>
                  <div style="margin-top:8px;font-size:0.82rem;color:#333;line-height:1.5;">{h['descripcion']}</div>
                </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                <div style="text-align:center;padding:12px;">
                  <span style="background:{tc};color:{tt};padding:4px 14px;border-radius:20px;font-size:0.75rem;font-weight:700;">{h['tipo']}</span>
                  <br/><br/>
                  <span style="background:{ec};color:{et};padding:4px 14px;border-radius:20px;font-size:0.75rem;font-weight:700;">{h['estado']}</span>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### ➕ Agregar Registro Manual")
    with st.expander("Nuevo registro de intervención"):
        ra1, ra2 = st.columns(2)
        with ra1:
            r_equipo = st.text_input("Equipo", key="r_eq")
            r_serie  = st.text_input("Nº Serie", key="r_serie")
            r_serv   = st.selectbox("Servicio", sorted(st.session_state.servicios_lista), key="r_serv")
            r_tipo   = st.selectbox("Tipo", ["Preventivo","Correctivo"], key="r_tipo")
        with ra2:
            r_fecha  = st.date_input("Fecha", key="r_fecha")
            r_tec    = st.text_input("Técnico responsable", key="r_tec")
            r_est    = st.selectbox("Estado del equipo", ["OPERATIVO","EN REPARACIÓN","DE BAJA"], key="r_est")
            r_desc   = st.text_area("Descripción de la intervención", height=80, key="r_desc")
        if st.button("💾 Guardar Registro", key="save_hist"):
            if r_equipo and r_tec:
                num = len(st.session_state.historial)+1
                st.session_state.historial.insert(0,{
                    "id": f"INF-{num:03d}",
                    "fecha": r_fecha.strftime("%d/%m/%Y"),
                    "equipo": r_equipo, "serie": r_serie, "servicio": r_serv,
                    "tipo": r_tipo, "estado": r_est, "tecnico": r_tec, "descripcion": r_desc
                })
                st.success(f"✅ Registro INF-{num:03d} guardado.")
                st.rerun()
            else:
                st.warning("Complete el equipo y técnico responsable.")

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO D: ESTADO DEL INVENTARIO (ingeniero)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_inventario():
    st.markdown('<div class="section-title">📦 Estado del Inventario</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Todos los equipos del hospital por servicio y estado</div>', unsafe_allow_html=True)

    buenos  = sum(1 for e in INVENTARIO_COMPLETO if e["estado"]=="BUENO")
    regular = sum(1 for e in INVENTARIO_COMPLETO if e["estado"]=="REGULAR")
    malo    = sum(1 for e in INVENTARIO_COMPLETO if e["estado"]=="MALO")
    total   = len(INVENTARIO_COMPLETO)

    c1,c2,c3,c4 = st.columns(4)
    for col,num,label,color,ico in [
        (c1,total,"Total equipos","#0d2656","📦"),
        (c2,buenos,"Estado Bueno","#0a3622","✅"),
        (c3,regular,"Estado Regular","#856404","⚠️"),
        (c4,malo,"Estado Malo","#842029","🔴"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div style="font-size:1.3rem;">{ico}</div>'
                        f'<div class="metric-num" style="color:{color};">{num}</div>'
                        f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if1,if2,if3 = st.columns(3)
    with if1: fi_serv = st.selectbox("Servicio", ["Todos"]+sorted(st.session_state.servicios_lista), key="inv_serv")
    with if2: fi_est  = st.selectbox("Estado", ["Todos","BUENO","REGULAR","MALO"], key="inv_est")
    with if3: fi_bus  = st.text_input("Buscar equipo", placeholder="Nombre, marca, serie...", key="inv_bus")

    inv = INVENTARIO_COMPLETO
    if fi_serv != "Todos": inv = [e for e in inv if e["servicio"]==fi_serv]
    if fi_est  != "Todos": inv = [e for e in inv if e["estado"]==fi_est]
    if fi_bus:             inv = [e for e in inv if fi_bus.lower() in e["equipo"].lower()
                                  or fi_bus.lower() in e["serie"].lower()
                                  or fi_bus.lower() in e["marca"].lower()]

    st.markdown(f'<div style="font-size:0.85rem;color:#555;margin-bottom:10px;"><b>{len(inv)}</b> equipo(s) encontrado(s)</div>', unsafe_allow_html=True)

    # Table header
    st.markdown("""
    <div class="tabla-header" style="grid-template-columns:2.5fr 1fr 1fr 1.5fr 0.8fr 0.8fr;">
      <span>Equipo</span><span>Marca</span><span>Modelo</span><span>Servicio</span><span>Estado</span><span>Frec.</span>
    </div>""", unsafe_allow_html=True)

    est_col = {"BUENO":"#0a3622","REGULAR":"#856404","MALO":"#842029"}
    est_bg  = {"BUENO":"#d1e7dd","REGULAR":"#fff3cd","MALO":"#f8d7da"}

    for eq in inv:
        ec = est_bg.get(eq["estado"],"#eee"); et = est_col.get(eq["estado"],"#333")
        c1,c2,c3,c4,c5,c6 = st.columns([2.5,1,1,1.5,0.8,0.8])
        with c1:
            st.markdown(f'<div style="font-size:0.8rem;font-weight:600;color:#0d2656;">{eq["equipo"]}</div>'
                        f'<div style="font-size:0.7rem;color:#aaa;">Serie: {eq["serie"]}</div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<span style="font-size:0.78rem;">{eq["marca"]}</span>', unsafe_allow_html=True)
        with c3: st.markdown(f'<span style="font-size:0.78rem;">{eq["modelo"]}</span>', unsafe_allow_html=True)
        with c4: st.markdown(f'<span style="font-size:0.75rem;color:#555;">{eq["servicio"]}</span>', unsafe_allow_html=True)
        with c5: st.markdown(f'<span style="background:{ec};color:{et};padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:700;">{eq["estado"]}</span>', unsafe_allow_html=True)
        with c6: st.markdown(f'<span style="font-size:0.72rem;color:#888;">{eq["frecuencia"][:4]}</span>', unsafe_allow_html=True)
        st.markdown('<hr style="margin:0;border-color:#f5f5f5;"/>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO E: ESTADO DE EQUIPOS DE MI ÁREA (médico)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_mis_reportes():
    """Médico/enfermera: lista de reportes propios desde SQLite."""
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    st.markdown('<div class="section-title">📋 Mis Reportes</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Historial de reportes que usted ha enviado a Bioingeniería</div>', unsafe_allow_html=True)

    mis = [r for r in st.session_state.reportes if r.get("reportado_por") == u["nombre"]]

    if not mis:
        st.markdown("""
        <div class="card" style="text-align:center;padding:40px;">
          <div style="font-size:2.5rem;">📭</div>
          <div style="color:#888;margin-top:10px;font-size:0.9rem;">
            Aún no ha enviado ningún reporte.
          </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("➕ Reportar una falla ahora", key="go_rep_falla"):
            st.session_state.pagina = "reportar_falla"
            st.rerun()
        return

    st.markdown(f'<div style="margin-bottom:12px;font-size:0.85rem;color:#555;"><b>{len(mis)}</b> reporte(s) enviado(s)</div>', unsafe_allow_html=True)

    for r in sorted(mis, key=lambda x: x.get("fecha",""), reverse=True):
        estado   = r.get("estado","Pendiente")
        prio     = r.get("prioridad","Media")
        color_b  = {"Alta":"#dc3545","Media":"#ffc107","Baja":"#198754"}.get(prio,"#888")
        est_icon = {"Pendiente":"⏳","En revisión":"🔄","Reparado":"✅","Alta prioridad":"🚨"}.get(estado,"⏳")
        est_bg   = {"Pendiente":"#fff3cd","En revisión":"#cfe2ff","Reparado":"#d1e7dd","Alta prioridad":"#f8d7da"}.get(estado,"#f8f9fa")
        est_col  = {"Pendiente":"#856404","En revisión":"#084298","Reparado":"#0a3622","Alta prioridad":"#842029"}.get(estado,"#333")

        nombre_eq = r.get("nombre", r.get("equipo",""))
        desc = r.get("descripcion","")
        desc_short = (desc[:80] + "...") if len(desc) > 80 else desc

        desc_html = ("<div style='font-size:0.75rem;color:#888;margin-top:4px;font-style:italic;'>&ldquo;" + desc_short + "&rdquo;</div>") if desc_short else ""
        html_r = (
            "<div style='background:#fff;border-radius:12px;padding:16px 20px;margin-bottom:10px;"
            "box-shadow:0 2px 8px rgba(0,0,0,0.07);border-left:5px solid " + color_b + ";'>"
            "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px;'>"
            "<div style='flex:1;'>"
            "<div style='font-size:0.7rem;color:#1a56a8;font-weight:700;margin-bottom:2px;'>" + str(r.get("reporte","")) + "</div>"
            "<div style='font-size:0.9rem;font-weight:700;color:#0d2656;'>" + nombre_eq + "</div>"
            "<div style='font-size:0.75rem;color:#666;margin-top:3px;'>"
            "&#127973; " + str(r.get("servicio","")) + " &nbsp;&middot;&nbsp; &#128197; " + str(r.get("fecha","")) + "</div>"
            + desc_html +
            "</div>"
            "<div style='text-align:right;min-width:100px;'>"
            "<div style='background:" + est_bg + ";color:" + est_col + ";font-size:0.72rem;font-weight:700;"
            "padding:4px 10px;border-radius:20px;display:inline-block;'>"
            + est_icon + " " + estado + "</div>"
            "<div style='font-size:0.7rem;color:" + color_b + ";font-weight:600;margin-top:4px;'>" + prio + "</div>"
            "</div></div></div>"
        )
        st.markdown(html_r, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#e8f4fd;border-radius:8px;padding:10px 16px;margin-top:8px;
                border-left:4px solid #1a56a8;font-size:0.8rem;color:#084298;">
      ℹ️ Bioingeniería actualizará el estado de su reporte. Revise esta sección periódicamente.
    </div>
    """, unsafe_allow_html=True)


def pagina_mis_equipos():
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    st.markdown('<div class="section-title">🖥️ Estado de Equipos de Mi Área</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Consulte el estado operativo de los equipos de su servicio</div>', unsafe_allow_html=True)

    servicios_disp = sorted(st.session_state.servicios_lista)
    area_sel = st.selectbox("Seleccione su área / servicio", servicios_disp, key="mis_eq_area")

    equipos_area = [e for e in INVENTARIO_COMPLETO if e["servicio"] == area_sel]
    reps_area = {r["serie"]: r for r in st.session_state.reportes}

    operativos  = sum(1 for e in equipos_area if e["estado"]=="BUENO" and e["serie"] not in reps_area)
    en_rep      = sum(1 for e in equipos_area if e["serie"] in reps_area and reps_area[e["serie"]]["estado"] in ["Pendiente","En revisión"])
    regulares   = sum(1 for e in equipos_area if e["estado"]=="REGULAR")

    c1,c2,c3 = st.columns(3)
    for col,num,label,color,ico in [
        (c1,len(equipos_area),"Total en área","#0d2656","📦"),
        (c2,operativos,"Operativos","#0a3622","✅"),
        (c3,en_rep,"Con reporte activo","#842029","🔴"),
    ]:
        with col:
            st.markdown(f'<div class="metric-card"><div style="font-size:1.3rem;">{ico}</div>'
                        f'<div class="metric-num" style="color:{color};">{num}</div>'
                        f'<div class="metric-label">{label}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    if not equipos_area:
        st.info("No se encontraron equipos para esta área.")
        return

    for eq in equipos_area:
        rep_activo = reps_area.get(eq["serie"])
        tiene_rep  = bool(rep_activo and rep_activo["estado"] in ["Pendiente","En revisión"])

        if tiene_rep:
            borde      = "#dc3545"
            estado_show= "🔴 En reparación (" + rep_activo["estado"] + ")"
            color_txt  = "#842029"
            rep_html   = ("<div style='font-size:0.72rem;color:#e67e22;margin-top:3px;'>"
                          "⚠️ Reporte: " + rep_activo["reporte"] + " — " + rep_activo["nombre"][:40] + "</div>")
        elif eq["estado"] == "BUENO":
            borde      = "#198754"
            estado_show= "✅ Operativo"
            color_txt  = "#0a3622"
            rep_html   = ""
        else:
            borde      = "#ffc107"
            estado_show= "⚠️ Estado regular"
            color_txt  = "#856404"
            rep_html   = ""

        nombre_eq  = eq["equipo"]
        marca_eq   = eq["marca"]
        modelo_eq  = eq["modelo"]
        serie_eq   = eq["serie"]

        html_eq = (
            "<div style='background:#fff;border-radius:10px;padding:14px 18px;margin-bottom:8px;"
            "box-shadow:0 1px 8px rgba(0,0,0,0.07);border-left:4px solid " + borde + ";'>"
            "<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;'>"
            "<div>"
            "<div style='font-size:0.88rem;font-weight:700;color:#0d2656;'>" + nombre_eq + "</div>"
            "<div style='font-size:0.75rem;color:#666;margin-top:2px;'>"
            "🏷️ " + marca_eq + " " + modelo_eq + " &nbsp;·&nbsp; Serie: " + serie_eq + "</div>"
            + rep_html +
            "</div>"
            "<div style='font-size:0.82rem;font-weight:700;color:" + color_txt + ";'>" + estado_show + "</div>"
            "</div></div>"
        )
        st.markdown(html_eq, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#e8f4fd;border-radius:8px;padding:10px 16px;margin-top:8px;
                border-left:4px solid #1a56a8;font-size:0.8rem;color:#084298;">
      💡 Si detecta una anomalía en algún equipo, repórtela desde el módulo <b>"Reportar Falla"</b>.
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO F: NOTIFICACIONES (médico)
# ══════════════════════════════════════════════════════════════════════════════
def pagina_notificaciones():
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    st.markdown('<div class="section-title">🔔 Notificaciones</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Actualizaciones de sus reportes enviados</div>', unsafe_allow_html=True)

    mis_reps = [r for r in st.session_state.reportes if r.get("reportado_por") == u["nombre"]]

    if not mis_reps:
        st.markdown('<div class="card" style="text-align:center;padding:40px;">'
                    '<div style="font-size:2rem;">🔕</div>'
                    '<div style="color:#888;margin-top:8px;">No tiene reportes enviados aún.</div></div>',
                    unsafe_allow_html=True)
        return

    notif_cfg = {
        "Pendiente":     ("🟡","#fff3cd","#856404","Su reporte está pendiente de atención por Bioingeniería."),
        "En revisión":   ("🔵","#cfe2ff","#084298","Su reporte está siendo revisado por el equipo de Bioingeniería."),
        "Reparado":      ("🟢","#d1e7dd","#0a3622","¡El equipo fue reparado y está operativo!"),
        "Alta prioridad":("🔴","#f8d7da","#842029","Su reporte fue marcado como ALTA PRIORIDAD por Bioingeniería."),
    }

    for r in reversed(mis_reps):
        ico, bg, tc, msg = notif_cfg.get(r["estado"], ("⚪","#f0f0f0","#555","Estado actualizado."))
        st.markdown(f"""
        <div style="background:{bg};border-radius:10px;padding:14px 18px;margin-bottom:10px;
                    border-left:4px solid {tc};">
          <div style="display:flex;gap:12px;align-items:flex-start;">
            <div style="font-size:1.4rem;">{ico}</div>
            <div style="flex:1;">
              <div style="font-size:0.88rem;font-weight:700;color:{tc};">{r['reporte']} — {r['nombre']}</div>
              <div style="font-size:0.78rem;color:#555;margin-top:2px;">{msg}</div>
              <div style="font-size:0.72rem;color:#888;margin-top:4px;">
                Servicio: {r['servicio']} &nbsp;·&nbsp; Fecha: {r['fecha']}
              </div>
            </div>
            <span style="background:rgba(0,0,0,0.08);color:{tc};padding:3px 10px;
                         border-radius:20px;font-size:0.72rem;font-weight:700;white-space:nowrap;">
              {r['estado']}
            </span>
          </div>
        </div>
        """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR MÉDICO ACTUALIZADO
# ══════════════════════════════════════════════════════════════════════════════
def mostrar_sidebar_medico():
    LOGO_IMG = "el_logo.jpeg"
    u = st.session_state.usuarios_sistema[st.session_state.usuario]
    notif_count = len([r for r in st.session_state.reportes if r.get("reportado_por")==u["nombre"]])

    with st.sidebar:
        if Path(LOGO_IMG).exists():
            b64l = img_to_b64(LOGO_IMG)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:12px 0 6px;">
              <img src="data:image/jpeg;base64,{b64l}" style="width:46px;height:46px;border-radius:50%;object-fit:cover;border:2px solid #3a5a9a;"/>
              <div>
                <div style="font-size:1rem;font-weight:700;color:#fff;">MedTrack</div>
                <div style="font-size:0.7rem;color:#8ab4d8;">H.M.I. Germán Urquidi</div>
                <div style="font-size:0.65rem;color:#7a9abf;">Cochabamba, Bolivia</div>
              </div>
            </div>
            <hr style="border-color:#2a3a6e;margin:8px 0;"/>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:8px 0 12px;">
          <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">SESIÓN ACTIVA</div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#1a56a8;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">{"🩺" if u["tipo"]=="medico" else "💊"}</div>
            <div>
              <div style="font-size:0.82rem;font-weight:600;color:#dde8f5;">{u['nombre']}</div>
              <div style="font-size:0.7rem;color:#7a9abf;">{u['rol']}</div>
            </div>
          </div>
        </div>
        <hr style="border-color:#2a3a6e;margin:4px 0 10px;"/>
        <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">NAVEGACIÓN</div>
        """, unsafe_allow_html=True)

        paginas_medico = [
            ("🏠","inicio","Inicio"),
            ("🔴","reportar_falla","Reportar Falla"),
            ("📋","mis_reportes","Mis Reportes"),
            ("🔔","notificaciones",f"Notificaciones"),
            ("🏥","cirugias","Prog. Cirugías"),
            ("🖥️","mis_equipos","Estado de Equipos"),
            ("📄","protocolos","Protocolos"),
        ]
        for icono, pid, nombre in paginas_medico:
            if st.button(f"{icono}  {nombre}", key=f"nav_med_{pid}", use_container_width=True):
                st.session_state.pagina = pid; st.rerun()

        st.markdown('<hr style="border-color:#2a3a6e;margin:14px 0 10px;"/>', unsafe_allow_html=True)
        if st.button("🚪  Cerrar Sesión", key="cerrar_med2", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.pagina = "inicio"
            st.rerun()
        st.markdown("""
        <div style="margin-top:14px;text-align:center;padding-bottom:8px;">
          <div style="font-size:0.65rem;color:#4a6a9a;">MedTrack v1.0 · 2026</div>
          <div style="font-size:0.6rem;color:#3a5a8a;">Unidad de Bioingeniería · HMIGU</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR INGENIERO ACTUALIZADO
# ══════════════════════════════════════════════════════════════════════════════
def mostrar_sidebar():
    LOGO_IMG = "el_logo.jpeg"
    u = st.session_state.usuarios_sistema[st.session_state.usuario]

    with st.sidebar:
        if Path(LOGO_IMG).exists():
            b64l = img_to_b64(LOGO_IMG)
            st.markdown(f"""
            <div style="display:flex;align-items:center;gap:10px;padding:12px 0 6px;">
              <img src="data:image/jpeg;base64,{b64l}" style="width:46px;height:46px;border-radius:50%;object-fit:cover;border:2px solid #3a5a9a;"/>
              <div>
                <div style="font-size:1rem;font-weight:700;color:#fff;">MedTrack</div>
                <div style="font-size:0.7rem;color:#8ab4d8;">H.M.I. Germán Urquidi</div>
                <div style="font-size:0.65rem;color:#7a9abf;">Cochabamba, Bolivia</div>
              </div>
            </div>
            <hr style="border-color:#2a3a6e;margin:8px 0;"/>
            """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="padding:8px 0 12px;">
          <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">SESIÓN ACTIVA</div>
          <div style="display:flex;align-items:center;gap:8px;">
            <div style="width:32px;height:32px;border-radius:50%;background:#1a56a8;display:flex;align-items:center;justify-content:center;font-size:0.9rem;">⚙️</div>
            <div>
              <div style="font-size:0.82rem;font-weight:600;color:#dde8f5;">{u['nombre']}</div>
              <div style="font-size:0.7rem;color:#7a9abf;">{u['rol']}</div>
            </div>
          </div>
        </div>
        <hr style="border-color:#2a3a6e;margin:4px 0 10px;"/>
        <div style="font-size:0.68rem;color:#6a8abf;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">NAVEGACIÓN</div>
        """, unsafe_allow_html=True)

        paginas = [
            ("🏠","inicio","Inicio"),
            ("📊","tablero","Tablero General"),
            ("📋","reportes","Gestión de Reportes"),
            ("🏥","cirugias","Prog. Cirugías"),
            ("🔧","mantenimientos","Calendario Mantenimientos"),
            ("📂","historial","Historial Intervenciones"),
            ("📦","inventario","Estado Inventario"),
            ("📄","protocolos","Protocolos"),
            ("🔵","qr","Generar Códigos QR"),
            ("📝","informes","Informes Técnicos"),
            ("📨","inicio_proceso","Inicio de Proceso"),
            ("👥","usuarios","Administrar Usuarios"),
        ]
        for icono, pid, nombre in paginas:
            if st.button(f"{icono}  {nombre}", key=f"nav_{pid}", use_container_width=True):
                st.session_state.pagina = pid; st.rerun()

        st.markdown('<hr style="border-color:#2a3a6e;margin:14px 0 10px;"/>', unsafe_allow_html=True)
        if st.button("🚪  Cerrar sesión", key="cerrar_ing", use_container_width=True):
            st.session_state.autenticado = False
            st.session_state.pagina = "inicio"
            st.rerun()
        st.markdown("""
        <div style="margin-top:14px;text-align:center;padding-bottom:8px;">
          <div style="font-size:0.65rem;color:#4a6a9a;">MedTrack v1.0 · 2026</div>
          <div style="font-size:0.6rem;color:#3a5a8a;">Unidad de Bioingeniería · HMIGU</div>
        </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  ROUTER PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.autenticado:
    mostrar_login()
else:
    st.markdown("""
    <div style="background:#0d1b3e;color:#8ab4d8;font-size:0.78rem;padding:6px 20px;margin-bottom:0;">
      Hospital Materno Infantil Germán Urquidi &nbsp;·&nbsp; Unidad de Bioingeniería
    </div>
    """, unsafe_allow_html=True)

    u_actual  = st.session_state.usuarios_sistema[st.session_state.usuario]
    es_medico = u_actual["tipo"] in ["medico","enfermera"]
    pagina    = st.session_state.pagina

    if es_medico:
        mostrar_sidebar_medico()
        if   pagina == "inicio":           pagina_inicio_medico()
        elif pagina == "reportar_falla":   pagina_reportar_falla()
        elif pagina == "mis_reportes":     pagina_mis_reportes()
        elif pagina == "notificaciones":   pagina_notificaciones()
        elif pagina == "cirugias":         pagina_cirugias()
        elif pagina == "mis_equipos":      pagina_mis_equipos()
        elif pagina == "protocolos":       pagina_protocolos()
        else:                              pagina_inicio_medico()
    else:
        mostrar_sidebar()
        if   pagina == "inicio":           pagina_inicio()
        elif pagina == "tablero":          pagina_tablero()
        elif pagina == "reportes":         pagina_reportes()
        elif pagina == "cirugias":         pagina_cirugias()
        elif pagina == "mantenimientos":   pagina_mantenimientos()
        elif pagina == "historial":        pagina_historial()
        elif pagina == "inventario":       pagina_inventario()
        elif pagina == "protocolos":       pagina_protocolos()
        elif pagina == "qr":               pagina_qr()
        elif pagina == "informes":         pagina_informes()
        elif pagina == "inicio_proceso":   pagina_inicio_proceso()
        elif pagina == "usuarios":         pagina_usuarios()
        else:                              pagina_inicio()
