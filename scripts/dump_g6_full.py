import docx
import glob

matches = glob.glob(r"C:\ProyectoSi2_TiendaRopa\*Grupo*.docx")
doc = docx.Document(matches[0])

# Dump 4.3 (P532 to P752)
with open(r"c:\ProyectoSi2_TiendaRopa\scratch_g6_43_full.txt", "w", encoding="utf-8") as f:
    for i in range(532, 753):
        p = doc.paragraphs[i]
        f.write(f"P{i} [{p.style.name}]: {p.text}\n")

# Dump 4.4 (P753 to P1140)
with open(r"c:\ProyectoSi2_TiendaRopa\scratch_g6_44_full.txt", "w", encoding="utf-8") as f:
    for i in range(753, 1141):
        p = doc.paragraphs[i]
        f.write(f"P{i} [{p.style.name}]: {p.text}\n")

# Dump 4.5 (P1141 to P1219)
with open(r"c:\ProyectoSi2_TiendaRopa\scratch_g6_45_full.txt", "w", encoding="utf-8") as f:
    for i in range(1141, 1220):
        p = doc.paragraphs[i]
        f.write(f"P{i} [{p.style.name}]: {p.text}\n")

print("Dumped 4.3, 4.4, 4.5 successfully!")
