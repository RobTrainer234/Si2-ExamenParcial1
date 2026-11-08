import docx

doc = docx.Document(r"c:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx")

with open(r"c:\ProyectoSi2_TiendaRopa\scratch_doc_cap4_headings.txt", "w", encoding="utf-8") as f:
    for i, p in enumerate(doc.paragraphs):
        t = p.text.strip()
        if any(t.startswith(prefix) for prefix in ["4.", "4.1", "4.2", "4.3", "4.4", "4.5", "5."]) or "CAPÍTULO IV" in t.upper() or "CAPITULO IV" in t.upper() or "CAPÍTULO 4" in t.upper() or "CAPITULO 4" in t.upper():
            f.write(f"P{i} [{p.style.name}]: '{t}'\n")

print("Headings written to scratch_doc_cap4_headings.txt")
