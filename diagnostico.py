# diagnostico2.py
from pypdf import PdfReader

reader = PdfReader("minutaRobledo.pdf")
fields = reader.get_fields()

print("Campos que contienen 'detallar':\n")
for nombre in fields:
    if "detallar" in nombre.lower():
        print(f"  '{nombre}'")