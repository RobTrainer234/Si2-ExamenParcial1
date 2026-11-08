import win32com.client

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
if not repo.ConnectionString:
    repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

el = repo.GetElementByID(3253)
print("Name:", el.Name)
print("Stereotype:", el.Stereotype)
print("StereotypeEx:", el.StereotypeEx)
print("Type:", el.Type)
print("Subtype:", el.Subtype)

el2 = repo.GetElementByID(3254)
print("Name2:", el2.Name)
print("Stereotype2:", el2.Stereotype)
print("StereotypeEx2:", el2.StereotypeEx)
