import win32com.client

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
try:
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    xml = repo.SQLQuery("SELECT Diagram_ID, Package_ID, Name, Diagram_Type FROM t_diagram WHERE Name LIKE '%Despliegue%' OR Name LIKE '%AWS%'")
    print("CasosDeUso_SegundoParcial.eap:")
    print(xml)
finally:
    try: repo.CloseFile()
    except: pass
    try: ea.Quit()
    except: pass
