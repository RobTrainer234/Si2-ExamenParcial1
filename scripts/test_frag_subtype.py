import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
root = rep.Models.GetAt(0)
pkg = root.Packages.AddNew('TEST_FRAG_SUBTYPE', '')
pkg.Update()
root.Packages.Refresh()

diag = pkg.Diagrams.AddNew('Test Frag Subtype', 'Sequence')
diag.Update()
pkg.Diagrams.Refresh()

# Alt (subtype 0)
f_alt = pkg.Elements.AddNew('casoAlt', 'InteractionFragment')
f_alt.Subtype = 0
f_alt.Update()
o1 = diag.DiagramObjects.AddNew('l=100;r=600;t=-50;b=-150;', '')
o1.ElementID = f_alt.ElementID
o1.Update()

# Opt (subtype 1)
f_opt = pkg.Elements.AddNew('casoOpt', 'InteractionFragment')
f_opt.Subtype = 1
f_opt.Update()
o2 = diag.DiagramObjects.AddNew('l=100;r=600;t=-180;b=-280;', '')
o2.ElementID = f_opt.ElementID
o2.Update()

# Loop (subtype 3)
f_loop = pkg.Elements.AddNew('casoLoop', 'InteractionFragment')
f_loop.Subtype = 3
f_loop.Update()
o3 = diag.DiagramObjects.AddNew('l=100;r=600;t=-310;b=-410;', '')
o3.ElementID = f_loop.ElementID
o3.Update()

diag.Update()

project = rep.GetProjectInterface()
project.PutDiagramImageToFile(diag.DiagramGUID, r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\test_frag_subtype.png', 1)

for i in range(root.Packages.Count - 1, -1, -1):
    if root.Packages.GetAt(i).Name == 'TEST_FRAG_SUBTYPE':
        root.Packages.Delete(i)
        break
root.Packages.Refresh()

rep.CloseFile()
rep.Exit()
print('DONE_SUBTYPE')
