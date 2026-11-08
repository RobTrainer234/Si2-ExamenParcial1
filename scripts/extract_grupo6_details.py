import docx
import glob

matches = glob.glob(r"C:\ProyectoSi2_TiendaRopa\*Grupo*.docx")
doc = docx.Document(matches[0])

# P532 to P752 is 4.3
# P753 to P1140 is 4.4
# P1141 to P1219 is 4.5

with open(r"c:\ProyectoSi2_TiendaRopa\scratch_grupo6_cap4_details.txt", "w", encoding="utf-8") as f:
    f.write("=== SECCIÓN 4.3 ===\n")
    for i in range(532, 570):
        f.write(f"P{i} [{doc.paragraphs[i].style.name}]: {doc.paragraphs[i].text}\n")
    f.write("...\n")
    for i in range(730, 755):
        f.write(f"P{i} [{doc.paragraphs[i].style.name}]: {doc.paragraphs[i].text}\n")

    f.write("\n=== SECCIÓN 4.4 ===\n")
    for i in range(753, 800):
        f.write(f"P{i} [{doc.paragraphs[i].style.name}]: {doc.paragraphs[i].text}\n")
    f.write("...\n")

    f.write("\n=== SECCIÓN 4.5 ===\n")
    for i in range(1141, 1170):
        f.write(f"P{i} [{doc.paragraphs[i].style.name}]: {doc.paragraphs[i].text}\n")

print("Written details to scratch_grupo6_cap4_details.txt")
