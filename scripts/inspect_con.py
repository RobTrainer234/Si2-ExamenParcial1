import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
root = rep.Models.GetAt(0)
def check_con(p):
    for i in range(p.Diagrams.Count):
        d = p.Diagrams.GetAt(i)
        if d.Type == 'Sequence' and d.DiagramLinks.Count > 0:
            print('Diag:', d.Name)
            for j in range(min(5, d.DiagramLinks.Count)):
                dl = d.DiagramLinks.GetAt(j)
                con = rep.GetConnectorByID(dl.ConnectorID)
                src = rep.GetElementByID(con.ClientID)
                dst = rep.GetElementByID(con.SupplierID)
                print(f'  Con: Name={con.Name}, Type={con.Type}, Subtype={con.Subtype}, SeqNo={con.SequenceNo}, Direction={con.Direction} [src={src.Name} -> dst={dst.Name}]')
            return True
    for i in range(p.Packages.Count):
        if check_con(p.Packages.GetAt(i)):
            return True
    return False

check_con(root)
rep.CloseFile()
rep.Exit()
