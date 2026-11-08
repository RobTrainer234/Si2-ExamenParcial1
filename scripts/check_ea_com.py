import win32com.client
import sys

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
print("Connecting...")
sys.stdout.flush()

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

# Buscar paquete 'Segundo Parcial - Diagramas de Secuencia (Etapa 1)'
pkg = None
for p in repo.Models.GetAt(0).Packages:
    if p.Name == "Segundo Parcial - Diagramas de Secuencia (Etapa 1)":
        pkg = p
        break

print(f"Package: {pkg.Name} (ID: {pkg.PackageID})")
for d in pkg.Diagrams:
    print(f"Diagram: {d.Name} (ID: {d.DiagramID})")
    if "CU-02" in d.Name:
        print("  Objects:")
        for obj in d.DiagramObjects:
            el = repo.GetElementByID(obj.ElementID)
            print(f"    {el.Name} ({el.Type}): left={obj.left}, right={obj.right}, top={obj.top}, bottom={obj.bottom}")
        print("  Links:")
        for l in d.DiagramLinks:
            c = repo.GetConnectorByID(l.ConnectorID)
            print(f"    {c.Name} (Seq={c.SequenceNo}): Geometry={l.Geometry}, Path={l.Path}")

repo.CloseFile()
del repo
del ea
print("Done!")
sys.stdout.flush()
