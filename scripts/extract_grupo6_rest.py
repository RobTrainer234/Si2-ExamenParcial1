import docx
import glob

matches = glob.glob(r"C:\ProyectoSi2_TiendaRopa\*Grupo*.docx")
doc = docx.Document(matches[0])

with open(r"c:\ProyectoSi2_TiendaRopa\scratch_grupo6_cap4_rest.txt", "w", encoding="utf-8") as f:
    f.write("=== REST OF 4.5 ===\n")
    for i in range(1169, 1220):
        f.write(f"P{i} [{doc.paragraphs[i].style.name}]: {doc.paragraphs[i].text}\n")

print("Written rest to scratch_grupo6_cap4_rest.txt")
