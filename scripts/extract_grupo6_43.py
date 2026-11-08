import docx
import glob

matches = glob.glob(r"C:\ProyectoSi2_TiendaRopa\*Grupo*.docx")
doc = docx.Document(matches[0])

with open(r"c:\ProyectoSi2_TiendaRopa\scratch_grupo6_43_overview.txt", "w", encoding="utf-8") as f:
    for i in range(532, 753):
        p = doc.paragraphs[i]
        t = p.text.strip()
        if t.startswith("MÓDULO") or t.startswith("MODULO") or t.startswith("CREATE TABLE") or t.startswith("--") or "TABLE" in t.upper() or p.style.name.startswith("Heading"):
            f.write(f"P{i} [{p.style.name}]: {t}\n")

print("Written 4.3 overview to scratch_grupo6_43_overview.txt")
