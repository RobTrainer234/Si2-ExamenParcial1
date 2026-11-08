import win32com.client

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
if not repo.ConnectionString:
    repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

pkg193 = repo.GetPackageByID(193)
for el in pkg193.Elements:
    if el.Type == 'Sequence':
        if el.Name.startswith('Form') or el.Name.startswith('UI_') or el.Name.startswith('V.'):
            # Boundary
            el.Stereotype = 'boundary'
            el.StereotypeEx = 'boundary'
        else:
            # Clear completely so it renders as RECTANGLE
            el.Stereotype = ''
            el.StereotypeEx = ''
        el.Update()

d = pkg193.Diagrams.GetAt(0)
repo.SaveDiagram(d.DiagramID)
repo.ReloadDiagram(d.DiagramID)

out_png = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1\test_rectangles_fixed.png'
repo.GetProjectInterface().PutDiagramImageToFile(d.DiagramGUID, out_png, 1)
print('Exported fixed test to:', out_png)
