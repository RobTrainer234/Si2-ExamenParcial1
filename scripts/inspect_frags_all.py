import subprocess, win32com.client
subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)
rep = win32com.client.Dispatch('EA.Repository')
rep.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')
# Check if there are any existing fragments with opt or loop
sql = "SELECT Object_ID, Name, Object_Type, SubType, NType, Style, PDATA1, PDATA2, PDATA3, PDATA4, PDATA5 FROM t_object WHERE Object_Type = 'InteractionFragment'"
xml = rep.SQLQuery(sql)
import re
rows = re.findall(r'<Row>(.*?)</Row>', xml, re.DOTALL)
for r in rows[:10]:
    print(r)
rep.CloseFile()
rep.Exit()
