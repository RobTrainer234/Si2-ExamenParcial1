import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
root = rep.Models.GetAt(0)
pkg = root.Packages.AddNew('TEST_LOOP_SUBTYPE', '')
pkg.Update()
root.Packages.Refresh()

diag = pkg.Diagrams.AddNew('Test Loop Subtype', 'Sequence')
diag.Update()
pkg.Diagrams.Refresh()

# Test subtypes 2, 4, 5, 6
for idx, st in enumerate([2, 4, 5, 6, 7]):
    f = pkg.Elements.AddNew(f'st_{st}', 'InteractionFragment')
    f.Subtype = st
    f.Update()
    top = -40 - (idx * 120)
    bot = top - 90
    o = diag.DiagramObjects.AddNew(f'l=100;r=600;t={top};b={bot};', '')
    o.ElementID = f.ElementID
    o.Update()

diag.Update()
project = rep.GetProjectInterface()
project.PutDiagramImageToFile(diag.DiagramGUID, r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\test_loop_subtypes.png', 1)

for i in range(root.Packages.Count - 1, -1, -1):
    if root.Packages.GetAt(i).Name == 'TEST_LOOP_SUBTYPE':
        root.Packages.Delete(i)
        break
root.Packages.Refresh()

rep.CloseFile()
rep.Exit()
print('DONE_LOOP_TEST')
