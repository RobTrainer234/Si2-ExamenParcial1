import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
root = rep.Models.GetAt(0)
pkg = root.Packages.AddNew('TEST_FRAG_TYPES', '')
pkg.Update()
root.Packages.Refresh()

diag = pkg.Diagrams.AddNew('Test Frag Types', 'Sequence')
diag.Update()
pkg.Diagrams.Refresh()

# Alt
f_alt = pkg.Elements.AddNew('casoAlt', 'InteractionFragment')
f_alt.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = '0' WHERE Object_ID = {f_alt.ElementID}")
o1 = diag.DiagramObjects.AddNew('l=100;r=600;t=-50;b=-150;', '')
o1.ElementID = f_alt.ElementID
o1.Update()

# Opt
f_opt = pkg.Elements.AddNew('casoOpt', 'InteractionFragment')
f_opt.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = '1' WHERE Object_ID = {f_opt.ElementID}")
o2 = diag.DiagramObjects.AddNew('l=100;r=600;t=-180;b=-280;', '')
o2.ElementID = f_opt.ElementID
o2.Update()

# Loop
f_loop = pkg.Elements.AddNew('casoLoop', 'InteractionFragment')
f_loop.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = '3' WHERE Object_ID = {f_loop.ElementID}")
o3 = diag.DiagramObjects.AddNew('l=100;r=600;t=-310;b=-410;', '')
o3.ElementID = f_loop.ElementID
o3.Update()

diag.Update()

project = rep.GetProjectInterface()
project.PutDiagramImageToFile(diag.DiagramGUID, r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\test_frag_types.png', 1)

for i in range(root.Packages.Count - 1, -1, -1):
    if root.Packages.GetAt(i).Name == 'TEST_FRAG_TYPES':
        root.Packages.Delete(i)
        break
root.Packages.Refresh()

rep.CloseFile()
rep.Exit()
print('DONE_TYPES')
