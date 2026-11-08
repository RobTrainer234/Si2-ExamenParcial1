import win32com.client
import os

def main():
    print("Iniciando corrección de nombres y subtipos de fragmentos en todos los diagramas...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    pkg193 = repo.GetPackageByID(193)
    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1'
    os.makedirs(out_dir, exist_ok=True)
    project = repo.GetProjectInterface()

    # In Enterprise Architect:
    # Subtype 0 = alt
    # Subtype 1 = opt
    # Subtype 4 = loop
    # Name should NOT contain 'alt', 'opt', 'loop' because EA automatically displays the operator!
    fixed_count = 0
    for el in pkg193.Elements:
        if el.Type == 'InteractionFragment':
            old_name = el.Name
            new_name = old_name
            # Check what operator it was intended to have
            if 'alt' in old_name.lower():
                el.Subtype = 0 # alt
                new_name = old_name.replace('alt', '').replace('opt', '').replace('break', '').strip()
            elif 'loop' in old_name.lower():
                el.Subtype = 4 # loop
                new_name = old_name.replace('loop', '').strip()
            elif 'opt' in old_name.lower():
                el.Subtype = 1 # opt
                new_name = old_name.replace('opt', '').replace('break', '').strip()

            # Clean up double brackets or spaces
            new_name = new_name.replace('[', '').replace(']', '').strip()
            el.Name = f"[{new_name}]"
            el.Update()
            fixed_count += 1
            print(f"Fragmento corregido: '{old_name}' -> Subtype={el.Subtype}, Nombre='{el.Name}'")

    print(f"Total fragmentos corregidos: {fixed_count}")
    repo.RefreshModelView(pkg193.PackageID)

    for d in pkg193.Diagrams:
        repo.SaveDiagram(d.DiagramID)
        repo.ReloadDiagram(d.DiagramID)
        clean_name = d.Name.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace(':', '')[:30] + '.png'
        img_path = os.path.join(out_dir, clean_name)
        project.PutDiagramImageToFile(d.DiagramGUID, img_path, 1)
        print(f"Diagrama actualizado y re-exportado: {d.Name} -> {clean_name}")

    print("\n¡Corrección completada exitosamente!")

if __name__ == '__main__':
    main()
