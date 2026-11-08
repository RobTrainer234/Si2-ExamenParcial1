import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
sql = "SELECT DISTINCT PDATA1 FROM t_object WHERE Object_Type = 'InteractionFragment'"
xml = rep.SQLQuery(sql)
print(xml)
rep.CloseFile()
rep.Exit()
