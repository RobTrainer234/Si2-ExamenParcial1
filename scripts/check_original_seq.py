import win32com.client
import sys

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

# Buscar diag CU01 de Ciclo 1 (que ya existía en el proyecto original del primer parcial)
diag_orig = None
for p in repo.Models.GetAt(0).Packages:
    if "05 - Diagramas de Secuencia" in p.Name:
        for sub in p.Packages:
            for sub2 in sub.Packages:
                for d in sub2.Diagrams:
                    diag_orig = d
                    break
                if diag_orig: break
            if diag_orig: break
        if diag_orig: break

print("Found original diagram from 1st partial:", diag_orig.Name if diag_orig else "None")
if diag_orig:
    print("Links count:", diag_orig.DiagramLinks.Count)
    for l in diag_orig.DiagramLinks:
        con = repo.GetConnectorByID(l.ConnectorID)
        print(f"  {con.Name} (Seq={con.SequenceNo}): Geometry='{l.Geometry}', Path='{l.Path}'")
    for obj in diag_orig.DiagramObjects:
        el = repo.GetElementByID(obj.ElementID)
        print(f"  Obj: {el.Name} ({el.Type}): top={obj.top}, bot={obj.bottom}, left={obj.left}, right={obj.right}")

repo.CloseFile()
del repo
del ea
