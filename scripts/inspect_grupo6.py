import docx
import sys
import os
import glob

matches = glob.glob(r"C:\ProyectoSi2_TiendaRopa\*Grupo*.docx")
doc_path = matches[0]

doc = docx.Document(doc_path)
print(f"Total paragraphs in Grupo 6 doc: {len(doc.paragraphs)}")
print(f"Total tables in Grupo 6 doc: {len(doc.tables)}")

with open(r"c:\ProyectoSi2_TiendaRopa\scratch_grupo6_headings.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if any(t.startswith(prefix) for prefix in ["4.", "4.1", "4.2", "4.3", "4.4", "4.5", "5."]) or "CAPÍTULO IV" in t.upper() or "CAPITULO IV" in t.upper():
            f.write(f"P{i} [{p.style.name}]: '{t}'\n")

print("Headings written to scratch_grupo6_headings.txt")
