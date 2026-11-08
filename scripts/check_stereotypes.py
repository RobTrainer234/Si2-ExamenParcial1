import win32com.client

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
if not repo.ConnectionString:
    repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

d391 = repo.GetDiagramByID(391)
print(f"Diagram 391: {d391.Name}")
for do in d391.DiagramObjects:
    el = repo.GetElementByID(do.ElementID)
    print(f"  DO: ID={el.ElementID}, Name={el.Name}, Type={el.Type}, Stereotype='{el.Stereotype}'")
