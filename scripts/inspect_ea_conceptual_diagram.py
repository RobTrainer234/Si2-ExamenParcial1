# -*- coding: utf-8 -*-
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

def inspect():
    rep = win32com.client.Dispatch("EA.Repository")
    rep.OpenFile(EAP_PATH)

    pkg = rep.GetPackageByID(8)
    print(f"Paquete: {pkg.Name} (ID: {pkg.PackageID})")
    print(f"Total elementos en paquete: {pkg.Elements.Count}")
    
    classes = []
    for i in range(pkg.Elements.Count):
        el = pkg.Elements.GetAt(i)
        if el.Type == "Class":
            classes.append((el.Name, el.ElementID, el.Attributes.Count, el.Connectors.Count))

    print("\n--- CLASES EN EL PAQUETE ---")
    for name, eid, attr_count, conn_count in sorted(classes):
        print(f"  - {name} (ID: {eid}) | Atributos: {attr_count} | Conectores: {conn_count}")

    print("\n--- DIAGRAMAS EN EL PAQUETE ---")
    for i in range(pkg.Diagrams.Count):
        d = pkg.Diagrams.GetAt(i)
        print(f"  - Diagrama: '{d.Name}' (ID: {d.DiagramID}, Tipo: {d.Type}) | DiagramObjects: {d.DiagramObjects.Count} | DiagramLinks: {d.DiagramLinks.Count}")
        if "CONCEPTUAL" in d.Name.upper():
            print("    Objetos en el diagrama:")
            for j in range(d.DiagramObjects.Count):
                dobj = d.DiagramObjects.GetAt(j)
                el = rep.GetElementByID(dobj.ElementID)
                print(f"      [{j+1}] {el.Name} (L:{dobj.left}, R:{dobj.right}, T:{dobj.top}, B:{dobj.bottom})")

    rep.CloseFile()
    rep.Exit()

if __name__ == '__main__':
    inspect()
