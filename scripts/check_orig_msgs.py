import win32com.client

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

pkg = None
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

print("Diagram:", diag_orig.Name)
for l in diag_orig.DiagramLinks:
    con = repo.GetConnectorByID(l.ConnectorID)
    src = repo.GetElementByID(con.ClientID)
    tgt = repo.GetElementByID(con.SupplierID)
    print(f"  Seq={con.SequenceNo}: {src.Name} -> {tgt.Name} : {con.Name}")

repo.CloseFile()
del repo
del ea
