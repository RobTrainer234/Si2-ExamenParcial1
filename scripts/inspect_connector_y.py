import win32com.client

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

# Buscar CU-02
pkg = repo.GetPackageByID(193)
diag = None
for d in pkg.Diagrams:
    if "CU-02" in d.Name:
        diag = d
        break

# Inspeccionar conector 1 en t_connector
res = repo.SQLQuery(f"SELECT Connector_ID, Name, SeqNo, PtFromX, PtFromY, PtToX, PtToY, StyleEx FROM t_connector WHERE Diagram_ID = {diag.DiagramID} OR Connector_ID IN (SELECT ConnectorID FROM t_diagramlinks WHERE DiagramID = {diag.DiagramID})")
print("Connectors in DB:")
print(res)

repo.CloseFile()
del repo
del ea
