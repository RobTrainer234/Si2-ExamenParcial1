import win32com.client

rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap")

pkg187 = rep.GetPackageByID(187)
print(f"Package: {pkg187.Name} (ID: {pkg187.PackageID})")
print(f"Diagram count: {pkg187.Diagrams.Count}")

for i in range(pkg187.Diagrams.Count):
    d = pkg187.Diagrams.GetAt(i)
    print(f"\n========================================================")
    print(f"Diagram [{i+1}]: {d.Name} (ID: {d.DiagramID})")
    print(f"========================================================")
    print("  Objects:")
    for j in range(d.DiagramObjects.Count):
        do = d.DiagramObjects.GetAt(j)
        el = rep.GetElementByID(do.ElementID)
        print(f"    - [{el.Stereotype}] {el.Name} (Type: {el.Type}) pos: ({do.left}, {do.top}, {do.right}, {do.bottom})")
    print("  Connectors:")
    for j in range(d.DiagramLinks.Count):
        dl = d.DiagramLinks.GetAt(j)
        c = rep.GetConnectorByID(dl.ConnectorID)
        src = rep.GetElementByID(c.ClientID)
        tgt = rep.GetElementByID(c.SupplierID)
        print(f"    - {src.Name} [{c.ClientEnd.Cardinality}] ---> {tgt.Name} [{c.SupplierEnd.Cardinality}] | Type: {c.Type} | Name: '{c.Name}'")

rep.CloseFile()
rep.Exit()
