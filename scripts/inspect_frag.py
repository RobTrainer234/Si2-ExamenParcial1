import win32com.client
rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap")
sql = "SELECT Object_ID, Name, Object_Type, NType, Subtype, Style, PDATA1, PDATA2, PDATA3, PDATA4, PDATA5 FROM t_object WHERE Object_Type = 'InteractionFragment'"
xml = rep.SQLQuery(sql)
print(xml[:1000])
rep.CloseFile()
rep.Exit()
