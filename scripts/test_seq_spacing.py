import win32com.client

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

pkg = repo.GetPackageByID(193)
# Buscar CU-02
diag = None
for d in pkg.Diagrams:
    if "CU-02" in d.Name:
        diag = d
        break

print("Testing connector Y coordinates and SequenceNo...")
# Ver valores de t_connector para los mensajes de CU-02
sql = f"SELECT Connector_ID, Name, SeqNo, PtFromX, PtFromY, PtToX, PtToY, Top_Edge, Btm_Edge, StyleEx FROM t_connector WHERE Diagram_ID = {diag.DiagramID}"
res = repo.SQLQuery(sql)
print("Query result:")
print(res)

repo.CloseFile()
del repo
del ea
