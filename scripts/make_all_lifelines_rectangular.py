import win32com.client
import os

def main():
    print("Iniciando conversión de TODAS las líneas de vida a rectangulares...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    pkg193 = repo.GetPackageByID(193)
    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1'
    os.makedirs(out_dir, exist_ok=True)
    project = repo.GetProjectInterface()

    print(f"Paquete 193: {pkg193.Name}")
    updated_count = 0
    for el in pkg193.Elements:
        # If it is a Sequence element (Boundary, Controller, Entity), make it 100% RECTANGULAR
        if el.Type == 'Sequence':
            el.Stereotype = ''
            el.StereotypeEx = ''
            el.Update()
            updated_count += 1

    print(f"Total elementos Sequence convertidos a rectangulares (sin estereotipo circular): {updated_count}")
    repo.RefreshModelView(pkg193.PackageID)

    for d in pkg193.Diagrams:
        repo.SaveDiagram(d.DiagramID)
        repo.ReloadDiagram(d.DiagramID)
        clean_name = d.Name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace(':', '')[:30] + '.png'
        img_path = os.path.join(out_dir, clean_name)
        project.PutDiagramImageToFile(d.DiagramGUID, img_path, 1)
        print(f"Diagrama actualizado y exportado 100% rectangular: {d.Name} -> {clean_name}")

    print("\n¡Todos los 10 Diagramas de Secuencia tienen ahora interfaces, controladores y entidades en formato rectangular!")

if __name__ == '__main__':
    main()
