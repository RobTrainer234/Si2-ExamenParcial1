import win32com.client
import os
import sys

def main():
    print("Conectando con Enterprise Architect...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    pkg193 = repo.GetPackageByID(193)
    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1'
    os.makedirs(out_dir, exist_ok=True)
    project = repo.GetProjectInterface()

    print(f"Paquete 193: {pkg193.Name}")
    count = 0
    for el in pkg193.Elements:
        if el.Type == 'Sequence':
            if el.Name.startswith('Form') or el.Name.startswith('UI_') or el.Name.startswith('V.'):
                el.Stereotype = 'boundary'
                el.StereotypeEx = 'boundary'
            else:
                el.Stereotype = ''
                el.StereotypeEx = ''
            el.Update()
            count += 1

    print(f"Se actualizaron {count} elementos Lifeline en Paquete 193.")
    repo.RefreshModelView(pkg193.PackageID)

    for d in pkg193.Diagrams:
        repo.SaveDiagram(d.DiagramID)
        repo.ReloadDiagram(d.DiagramID)
        clean_name = d.Name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace(':', '')[:30] + '.png'
        img_path = os.path.join(out_dir, clean_name)
        project.PutDiagramImageToFile(d.DiagramGUID, img_path, 1)
        print(f"Exportado correctamente con rectángulos: {d.Name} -> {clean_name}")

    print("Proceso completado exitosamente.")

if __name__ == '__main__':
    main()
