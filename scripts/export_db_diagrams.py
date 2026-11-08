import win32com.client
import os

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
art_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87'
out_dir = r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\db_conceptual'

os.makedirs(out_dir, exist_ok=True)
os.makedirs(art_dir, exist_ok=True)

print("Opening EA...")
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)
project = repo.GetProjectInterface()

# Export diagram 11 (completo)
diag11 = repo.GetDiagramByID(11)
guid11 = diag11.DiagramGUID
file11 = os.path.join(out_dir, 'diagrama_clases_bd_completo.png')
file11_art = os.path.join(art_dir, 'diagrama_clases_bd_completo.png')

project.PutDiagramImageToFile(guid11, file11, 1)
project.PutDiagramImageToFile(guid11, file11_art, 1)
print(f"Exported Diagram 11: {file11} ({os.path.getsize(file11)} bytes)")

# Export diagram 10 (base)
diag10 = repo.GetDiagramByID(10)
guid10 = diag10.DiagramGUID
file10 = os.path.join(out_dir, 'diagrama_clases_bd_base.png')
file10_art = os.path.join(art_dir, 'diagrama_clases_bd_base.png')

project.PutDiagramImageToFile(guid10, file10, 1)
project.PutDiagramImageToFile(guid10, file10_art, 1)
print(f"Exported Diagram 10: {file10} ({os.path.getsize(file10)} bytes)")

repo.CloseFile()
del repo
del ea
print("All exported successfully!")
