# -*- coding: utf-8 -*-
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

def inspect():
    rep = win32com.client.Dispatch("EA.Repository")
    rep.OpenFile(EAP_PATH)

    pkg = rep.GetPackageByID(200)
    print(f"Paquete: '{pkg.Name}' (ID: {pkg.PackageID})")
    print(f"Total diagramas: {pkg.Diagrams.Count}")
    print(f"Total elementos en paquete: {pkg.Elements.Count}\n")

    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        print(f"[{i+1}] Diagrama: '{d.Name}' (ID: {d.DiagramID}, Tipo: {d.Type})")
        print(f"    Total objetos: {d.DiagramObjects.Count} | Total enlaces: {d.DiagramLinks.Count}")
        
        actors = []
        boundaries = []
        controls = []
        entities = []
        texts = []
        for j in range(d.DiagramObjects.Count):
            dobj = d.DiagramObjects.GetAt(j)
            el = rep.GetElementByID(dobj.ElementID)
            if el.Type == 'Actor':
                actors.append(el.Name)
            elif el.Stereotype == 'boundary':
                boundaries.append(el.Name)
            elif el.Stereotype == 'control':
                controls.append(el.Name)
            elif el.Stereotype == 'entity':
                entities.append(el.Name)
            elif el.Type == 'Text':
                texts.append(el.Name.replace('\n', ' // ')[:80])
        print(f"    Actor(es): {', '.join(actors)}")
        print(f"    Boundary: {', '.join(boundaries)}")
        print(f"    Control: {', '.join(controls)}")
        print(f"    Entidades: {', '.join(entities)}")
        print(f"    Mensajes (Textos): {len(texts)} mensajes mapeados")
        print()

    rep.CloseFile()
    rep.Exit()

if __name__ == '__main__':
    inspect()
