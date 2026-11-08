import win32com.client
import sys

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
print("Connecting...")
sys.stdout.flush()

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

# Query SQL inside EA directly: table t_diagramlinks and t_diagramobjects
sql_diag = "SELECT Diagram_ID, Name FROM t_diagram WHERE Name LIKE '%CU-02%'"
print(repo.SQLQuery(sql_diag))

sql = """
SELECT do.Object_ID, o.Name, o.Object_Type, do.RectTop, do.RectBottom, do.RectLeft, do.RectRight
FROM t_diagramobjects do
INNER JOIN t_object o ON do.Object_ID = o.Object_ID
WHERE do.Diagram_ID IN (SELECT Diagram_ID FROM t_diagram WHERE Name LIKE '%CU-02%')
ORDER BY do.RectTop DESC
"""

xml_res = repo.SQLQuery(sql)
print("--- Diagram Objects (CU-02) ---")
print(xml_res)

sql_links = """
SELECT dl.ConnectorID, c.Name, c.SeqNo, dl.Geometry
FROM t_diagramlinks dl
INNER JOIN t_connector c ON dl.ConnectorID = c.Connector_ID
WHERE dl.DiagramID IN (SELECT Diagram_ID FROM t_diagram WHERE Name LIKE '%CU-02%')
ORDER BY c.SeqNo ASC
"""
xml_links = repo.SQLQuery(sql_links)
print("\n--- Diagram Links (CU-02) ---")
print(xml_links)

repo.CloseFile()
del repo
del ea
print("Done!")
sys.stdout.flush()
