import docx

doc = docx.Document(r"c:\ProyectoSi2_TiendaRopa\docsegundoparcialSI2.docx")

p42_idx = None
cap5_idx = None

for i, p in enumerate(doc.paragraphs):
    t = p.text.strip()
    if t.startswith("4.2. Diseño de la arquitectura") or "4.2. Diseño de la arquitectura" in t:
        p42_idx = i
    elif (t.startswith("Capítulo 5:") or t.startswith("Capitulo 5:")) and p42_idx is not None:
        cap5_idx = i
        break

print(f"p42_idx: {p42_idx}, cap5_idx: {cap5_idx}")

for i in range(p42_idx, min(p42_idx + 35, len(doc.paragraphs))):
    p = doc.paragraphs[i]
    print(f"P{i} [{p.style.name}]: '{p.text[:90]}'")

print("...")
for i in range(max(p42_idx, cap5_idx - 15), cap5_idx + 2):
    p = doc.paragraphs[i]
    print(f"P{i} [{p.style.name}]: '{p.text[:90]}'")
