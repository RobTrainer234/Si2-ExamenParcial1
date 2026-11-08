import subprocess, win32com.client

subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)

rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap")

diag = rep.GetDiagramByID(11)
print(f"Diagram Name: {diag.Name}")
print("Total links:", diag.DiagramLinks.Count)

for i in range(diag.DiagramLinks.Count):
    dl = diag.DiagramLinks.GetAt(i)
    c = rep.GetConnectorByID(dl.ConnectorID)
    src = rep.GetElementByID(c.ClientID)
    tgt = rep.GetElementByID(c.SupplierID)
    print(f"[{i+1}] {src.Name} ({c.ClientEnd.Cardinality}) ---[{c.Name}]---> {tgt.Name} ({c.SupplierEnd.Cardinality}) | Dir: {c.Direction}")

rep.CloseFile()
rep.Exit()
