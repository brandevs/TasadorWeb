"""
app.py — TasadorWeb
"""

import os
from datetime import datetime
from flask import Flask, render_template, request, send_file
from pypdf import PdfReader, PdfWriter
from pypdf.generic import BooleanObject, NameObject

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PDF_BASE = os.path.join(BASE_DIR, "minutaRobledo.pdf")
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
    # Campo chico "Detallar:" al lado del checkbox "Otros"
    "detallar_otros":   "topmostSubform[0].Page1[0].detallar[0]",
}

LIMITE_H1 = 500  # caracteres para hoja 1, el resto va a hoja 2

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

    # ✅ Forma correcta de setear NeedAppearances en pypdf moderno
    if "/AcroForm" in writer._root_object:
        writer._root_object["/AcroForm"][NameObject("/NeedAppearances")] = BooleanObject(True)

    datos = {}
    for campo_web, campo_pdf in CAMPOS_MAP.items():
        datos[campo_pdf] = request.form.get(campo_web, "")

    # ✅ Descripción: detallar[1] = hoja 1, detallar2[0] = hoja 2
    descripcion = request.form.get("detallar", "").strip()
    datos["topmostSubform[0].Page1[0].detallar[1]"] = descripcion[:LIMITE_H1]
    datos["topmostSubform[0].Page2[0].detallar2[0]"] = descripcion[LIMITE_H1:]

    for page in writer.pages:
        writer.update_page_form_field_values(page, datos)

    nombre = f"tasacion_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    ruta = os.path.join(OUTPUT_DIR, nombre)

    with open(ruta, "wb") as f:
        writer.write(f)

    return send_file(ruta, as_attachment=True)

if __name__ == "__main__":
    print("✅ TasadorWeb corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)