"""
app.py - TasadorWeb
"""

import os
import io
from datetime import datetime
from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject, NameObject as PDF_Name
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit, ImageReader

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_BASE = os.path.join(BASE_DIR, "minutaRobledo.pdf")
FIRMA_IMG = os.path.join(BASE_DIR, "firma.png")
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "tasaciones_generadas")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CAMPOS_MAP = {
    "ApellidoYNombre":  "topmostSubform[0].Page1[0].ApellidoYNombre[0]",
    "Documento":        "topmostSubform[0].Page1[0].Documento[0]",
    "domicilio":        "topmostSubform[0].Page1[0].domicilio[0]",
    "caracter":         "topmostSubform[0].Page1[0].caracter[0]",
    "localidad":        "topmostSubform[0].Page1[0].localidad[0]",
    "paraje":           "topmostSubform[0].Page1[0].paraje[0]",
    "partido":          "topmostSubform[0].Page1[0].pardtido[0]",
    "provincia":        "topmostSubform[0].Page1[0].provincia[0]",
    "Nomenclatura":     "topmostSubform[0].Page1[0].Nomenclatura[0]",
    "partida":          "topmostSubform[0].Page1[0].partida[0]",
    "matricula":        "topmostSubform[0].Page1[0].matricula[0]",
    "titular":          "topmostSubform[0].Page1[0].titular[0]",
    "medidaLote":       "topmostSubform[0].Page1[0].medidaLote[0]",
    "SupCubierta":      "topmostSubform[0].Page1[0].SupCubierta[0]",
    "SupSemiCubierta":  "topmostSubform[0].Page1[0].SupSemiCubierta[0]",
    "usoSuelo":         "topmostSubform[0].Page1[0].usoSuelo[0]",
    "ValorMercado":     "topmostSubform[0].Page1[0].ValorMercado[0]",
    "calle":            "topmostSubform[0].Page1[0].calle[0]",
    "nro":              "topmostSubform[0].Page1[0].nro[0]",
    "entreCalles":      "topmostSubform[0].Page1[0].entreCalles[0]",
    "Fos":              "topmostSubform[0].Page1[0].Fos[0]",
    "Fot":              "topmostSubform[0].Page1[0].Fot[0]",
    "Densidad":         "topmostSubform[0].Page1[0].Densidad[0]",
    "FECHA":            "topmostSubform[0].Page1[0].FECHA[0]",
    "hojas":            "topmostSubform[0].Page2[0].hojas[0]",
    "detallar_otros":   "topmostSubform[0].Page1[0].detallar[0]",
}

CHECKBOXES = {
    "VF": "topmostSubform[0].Page1[0].VF[0]",
    "DC": "topmostSubform[0].Page1[0].DC[0]",
    "DI": "topmostSubform[0].Page1[0].DI[0]",
    "OT": "topmostSubform[0].Page1[0].OT[0]",
}

# Overlay descripcion
X_INICIO     = 46
Y_INICIO     = 162
Y_FIN        = 38
ANCHO        = 500
FONT_SIZE    = 8
INTERLINEADO = 10
X_H2         = 44
Y_H2_INICIO  = 775
Y_H2_FIN     = 295

# Coordenadas grilla croquis
MAPA_X      = 120
MAPA_Y      = 468
MAPA_ANCHO  = 350
MAPA_ALTO   = 108

# Coordenadas firma (pagina 2)
H_PAGE        = 841.89
Y_FIRMA_LABEL = H_PAGE - 711.6
Y_CUIT_LABEL  = H_PAGE - 740.3
Y_DOM_LABEL   = H_PAGE - 770.6

PROFESIONAL_NOMBRE = "Horacio Walter Robledo - Leg. 37735"
PROFESIONAL_CUIT   = "23-20555543-9"
PROFESIONAL_DOM    = "Espana N° 4237 - Mar del Plata"


def generar_overlay_descripcion(descripcion):
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    can.setFont("Helvetica", FONT_SIZE)

    lineas_todas = []
    for parrafo in descripcion.split("\n"):
        parrafo = parrafo.strip()
        if parrafo:
            lineas_todas.extend(simpleSplit(parrafo, "Helvetica", FONT_SIZE, ANCHO))
        else:
            lineas_todas.append("")

    y = Y_INICIO
    lineas_h1 = []
    lineas_h2 = []

    for linea in lineas_todas:
        if y >= Y_FIN:
            lineas_h1.append((y, linea))
            y -= INTERLINEADO
        else:
            lineas_h2.append(linea)

    for (ypos, linea) in lineas_h1:
        if linea:
            can.drawString(X_INICIO, ypos, linea)

    can.showPage()

    can.setFont("Helvetica", FONT_SIZE)
    y2 = Y_H2_INICIO
    for linea in lineas_h2:
        if y2 >= Y_H2_FIN:
            if linea:
                can.drawString(X_H2, y2, linea)
            y2 -= INTERLINEADO

    can.save()
    packet.seek(0)
    return packet


def generar_overlay_mapa(img_bytes):
    from PIL import Image

    px_ancho = int(MAPA_ANCHO * 150 / 72)
    px_alto  = int(MAPA_ALTO  * 150 / 72)

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_w, img_h = img.size

    escala = min(px_ancho / img_w, px_alto / img_h)
    nuevo_ancho = int(img_w * escala)
    nuevo_alto  = int(img_h * escala)
    img = img.resize((nuevo_ancho, nuevo_alto), Image.LANCZOS)

    canvas_img = Image.new("RGB", (px_ancho, px_alto), (255, 255, 255))
    offset_x = (px_ancho - nuevo_ancho) // 2
    offset_y = (px_alto  - nuevo_alto)  // 2
    canvas_img.paste(img, (offset_x, offset_y))

    buf = io.BytesIO()
    canvas_img.save(buf, format="PNG")
    buf.seek(0)

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    img_reader = ImageReader(buf)
    can.drawImage(
        img_reader,
        MAPA_X, MAPA_Y,
        width=MAPA_ANCHO, height=MAPA_ALTO,
        preserveAspectRatio=False,
    )
    can.save()
    packet.seek(0)
    return packet


def generar_overlay_firma():
    """
    Overlay pagina 2: firma imagen, nombre, CUIT y domicilio del profesional.
    Requiere firma.png en la raiz del proyecto.
    """
    from PIL import Image

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)

    # Imagen firma
    if os.path.exists(FIRMA_IMG):
        img = Image.open(FIRMA_IMG).convert("RGBA")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        buf = io.BytesIO()
        bg.save(buf, format="PNG")
        buf.seek(0)
        can.drawImage(
            ImageReader(buf), 44, Y_FIRMA_LABEL + 28,
            width=100, height=35,
            preserveAspectRatio=True
        )

    # Nombre
    can.setFont("Helvetica", 7)
    can.drawString(44, Y_FIRMA_LABEL + 13, PROFESIONAL_NOMBRE)

    # CUIT
    can.setFont("Helvetica", 8)
    can.drawString(75, Y_CUIT_LABEL + 13, PROFESIONAL_CUIT)

    # Domicilio
    can.drawString(44, Y_DOM_LABEL + 13, PROFESIONAL_DOM)

    can.save()
    packet.seek(0)
    return packet


def marcar_checkboxes(writer, checkboxes_marcados):
    from pypdf.generic import NameObject as N

    for page in writer.pages:
        if "/Annots" not in page:
            continue
        for annot_ref in page["/Annots"]:
            annot = annot_ref.get_object()
            campo = str(annot.get("/T", ""))
            for nombre_form, nombre_pdf_suffix in CHECKBOXES.items():
                if campo == f"{nombre_form}[0]":
                    if nombre_form in checkboxes_marcados:
                        annot[N("/V")]  = N("/1")
                        annot[N("/AS")] = N("/1")
                    else:
                        annot[N("/V")]  = N("/Off")
                        annot[N("/AS")] = N("/Off")


@app.route("/")
def index():
    return render_template("formulario.html")


@app.route("/generar-pdf", methods=["POST"])
def generar_pdf():
    if not os.path.exists(PDF_BASE):
        return "No se encuentra el PDF base", 404

    reader = PdfReader(PDF_BASE)
    writer = PdfWriter()
    writer.append(reader)

    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    # Campos de texto
    datos = {}
    for campo_web, campo_pdf in CAMPOS_MAP.items():
        datos[campo_pdf] = request.form.get(campo_web, "")

    for page in writer.pages:
        writer.update_page_form_field_values(page, datos)

    # Checkboxes
    checkboxes_marcados = set()
    for nombre in CHECKBOXES:
        if request.form.get(nombre):
            checkboxes_marcados.add(nombre)
    marcar_checkboxes(writer, checkboxes_marcados)

    # Overlay descripcion
    descripcion = request.form.get("detallar", "").strip()
    if descripcion:
        overlay_packet = generar_overlay_descripcion(descripcion)
        overlay = PdfReader(overlay_packet)
        writer.pages[0].merge_page(overlay.pages[0])
        if len(writer.pages) > 1 and len(overlay.pages) > 1:
            writer.pages[1].merge_page(overlay.pages[1])

    # Overlay imagen del mapa
    imagen_mapa = request.files.get("imagen_mapa")
    if imagen_mapa and imagen_mapa.filename:
        try:
            img_bytes = imagen_mapa.read()
            mapa_packet = generar_overlay_mapa(img_bytes)
            mapa_overlay = PdfReader(mapa_packet)
            writer.pages[0].merge_page(mapa_overlay.pages[0])
        except Exception as e:
            print(f"Error insertando imagen del mapa: {e}")

    # Overlay firma profesional (pagina 2)
    try:
        firma_packet = generar_overlay_firma()
        firma_overlay = PdfReader(firma_packet)
        if len(writer.pages) > 1:
            writer.pages[1].merge_page(firma_overlay.pages[0])
    except Exception as e:
        print(f"Error insertando firma: {e}")

    nombre = f"tasacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join(OUTPUT_DIR, nombre)

    with open(ruta, "wb") as f:
        writer.write(f)

    return send_file(ruta, as_attachment=True)


if __name__ == "__main__":
    print("TasadorWeb corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)