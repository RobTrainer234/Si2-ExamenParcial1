import win32com.client
import sys

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

# Buscar paquete 'Segundo Parcial - Diagramas de Secuencia (Etapa 1)'
pkg = None
for p in repo.Models.GetAt(0).Packages:
    if p.Name == "Segundo Parcial - Diagramas de Secuencia (Etapa 1)":
        pkg = p
        break

diag = None
for d in pkg.Diagrams:
    if "CU-02" in d.Name:
        diag = d
        break

print("Diagram:", diag.Name)
for l in diag.DiagramLinks:
    con = repo.GetConnectorByID(l.ConnectorID)
    print(f"Msg: {con.Name} (Seq={con.SequenceNo}) -> Geometry: '{l.Geometry}'")

repo.CloseFile()
del repo
del ea
