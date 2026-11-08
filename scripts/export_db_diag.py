import subprocess, win32com.client, os
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)

rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap")
root = rep.Models.GetAt(0)
pkg = root.Packages.GetAt(1)
project = rep.GetProjectInterface()

out_dir = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\db_conceptual"
os.makedirs(out_dir, exist_ok=True)

for i in range(pkg.Diagrams.Count):
    d = pkg.Diagrams.GetAt(i)
    png_path = os.path.join(out_dir, f"diag_db_{i+1}.png")
    project.PutDiagramImageToFile(d.DiagramGUID, png_path, 1)
    print(f"Exportado: {d.Name} -> {png_path}")

rep.CloseFile()
rep.Exit()
