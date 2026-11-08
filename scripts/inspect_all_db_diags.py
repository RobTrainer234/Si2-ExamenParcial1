import win32com.client

rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap")

for i in [1, 2, 3]:
    pkg = rep.Models.GetAt(0).Packages.GetAt(1)
    d = pkg.Diagrams.GetAt(i-1)
    print(f"\n==========================================")
    print(f"Diagram [{i}]: {d.Name} (ID: {d.DiagramID})")
    print(f"==========================================")
    for j in range(d.DiagramLinks.Count):
        dl = d.DiagramLinks.GetAt(j)
        c = rep.GetConnectorByID(dl.ConnectorID)
        src = rep.GetElementByID(c.ClientID)
        tgt = rep.GetElementByID(c.SupplierID)
        if "Tenant" in src.Name or "Tenant" in tgt.Name or "Subscri" in src.Name or "Subscri" in tgt.Name:
            print(f"  {src.Name} [{c.ClientEnd.Cardinality}] ---[{c.Name}]---> {tgt.Name} [{c.SupplierEnd.Cardinality}]")

rep.CloseFile()
rep.Exit()
