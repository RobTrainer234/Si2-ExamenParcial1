import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
sql = "SELECT Connector_ID, Name, Connector_Type, SubType, Direction, SeqNo, Style, ActionTag, PDATA1, PDATA2, PDATA3, PDATA4, PDATA5 FROM t_connector WHERE Connector_Type = 'Sequence' AND Name LIKE 'return%'"
xml = rep.SQLQuery(sql)
print(xml[:1500])
rep.CloseFile()
rep.Exit()
