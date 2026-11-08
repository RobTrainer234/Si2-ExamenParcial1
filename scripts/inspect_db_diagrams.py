import win32com.client
import json
import sys

eap_path = r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap'
print("Opening EA...")
sys.stdout.flush()

ea = win32com.client.Dispatch('EA.App')
repo = ea.Repository
repo.OpenFile(eap_path)

data = {}

for diag_id in [10, 11]:
    diag = repo.GetDiagramByID(diag_id)
    d_info = {
        'id': diag.DiagramID,
        'name': diag.Name,
        'type': diag.Type,
        'package_id': diag.PackageID,
        'classes': [],
        'links': []
    }
    
    for do in diag.DiagramObjects:
        el = repo.GetElementByID(do.ElementID)
        attrs = []
        for a in el.Attributes:
            attrs.append({
                'name': a.Name,
                'type': a.Type,
                'visibility': a.Visibility,
                'notes': a.Notes
            })
        meths = []
        for m in el.Methods:
            meths.append({
                'name': m.Name,
                'return_type': m.ReturnType
            })
        d_info['classes'].append({
            'id': el.ElementID,
            'name': el.Name,
            'type': el.Type,
            'stereotype': el.Stereotype,
            'attributes': attrs,
            'methods': meths,
            'left': do.left,
            'top': do.top,
            'right': do.right,
            'bottom': do.bottom
        })
        
    for dl in diag.DiagramLinks:
        con = repo.GetConnectorByID(dl.ConnectorID)
        c_el = repo.GetElementByID(con.ClientID)
        s_el = repo.GetElementByID(con.SupplierID)
        d_info['links'].append({
            'id': con.ConnectorID,
            'name': con.Name,
            'type': con.Type,
            'client': c_el.Name,
            'client_cardinality': con.ClientEnd.Cardinality,
            'client_role': con.ClientEnd.Role,
            'supplier': s_el.Name,
            'supplier_cardinality': con.SupplierEnd.Cardinality,
            'supplier_role': con.SupplierEnd.Role
        })
        
    data[f'diag_{diag_id}'] = d_info

with open(r'C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\db_conceptual\db_diagrams_info.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("Saved JSON successfully!")
repo.CloseFile()
del repo
del ea
