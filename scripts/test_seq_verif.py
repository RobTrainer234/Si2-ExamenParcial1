import subprocess, os, shutil, win32com.client

subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
rep = win32com.client.Dispatch("EA.Repository")
rep.OpenFile(EAP_PATH)
root = rep.Models.GetAt(0)

pkg = root.Packages.AddNew("TEST_SEQ_VERIF", "")
pkg.Update()
root.Packages.Refresh()

diag = pkg.Diagrams.AddNew("sd Test Sequence", "Sequence")
diag.Update()
pkg.Diagrams.Refresh()

# Lifelines
# 1. Actor
el_act = pkg.Elements.AddNew("Superadmin SaaS", "Actor")
el_act.Update()
o_act = diag.DiagramObjects.AddNew("l=40;r=110;t=-40;b=-850;", "")
o_act.ElementID = el_act.ElementID
o_act.Update()

# 2. V.Index (Rectangular sequence lifeline)
el_vidx = pkg.Elements.AddNew("V.EmpresaIndex", "Sequence")
el_vidx.Update()
o_vidx = diag.DiagramObjects.AddNew("l=160;r=260;t=-40;b=-850;", "")
o_vidx.ElementID = el_vidx.ElementID
o_vidx.Update()

# 3. V.Crear (Rectangular sequence lifeline)
el_vcrear = pkg.Elements.AddNew("V.CrearEmpresa", "Sequence")
el_vcrear.Update()
o_vcrear = diag.DiagramObjects.AddNew("l=290;r=390;t=-40;b=-850;", "")
o_vcrear.ElementID = el_vcrear.ElementID
o_vcrear.Update()

# 4. Controller
el_ctrl = pkg.Elements.AddNew("TenantController", "Sequence")
el_ctrl.Update()
o_ctrl = diag.DiagramObjects.AddNew("l=430;r=550;t=-40;b=-850;", "")
o_ctrl.ElementID = el_ctrl.ElementID
o_ctrl.Update()

# 5. Entity Main
el_m = pkg.Elements.AddNew("E_Tenant", "Sequence")
el_m.Update()
o_m = diag.DiagramObjects.AddNew("l=600;r=710;t=-40;b=-850;", "")
o_m.ElementID = el_m.ElementID
o_m.Update()

# 6. Entity Sec 1
el_s1 = pkg.Elements.AddNew("E_Subscription", "Sequence")
el_s1.Update()
o_s1 = diag.DiagramObjects.AddNew("l=750;r=860;t=-40;b=-850;", "")
o_s1.ElementID = el_s1.ElementID
o_s1.Update()

# 7. Entity Sec 2
el_s2 = pkg.Elements.AddNew("E_SubscriptionPlan", "Sequence")
el_s2.Update()
o_s2 = diag.DiagramObjects.AddNew("l=900;r=1020;t=-40;b=-850;", "")
o_s2.ElementID = el_s2.ElementID
o_s2.Update()

# Fragment alt listar (starts from Interface l=150 to entities r=1030)
f_list = pkg.Elements.AddNew("listar", "InteractionFragment")
f_list.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = 'alt' WHERE Object_ID = {f_list.ElementID}")
o_flist = diag.DiagramObjects.AddNew("l=150;r=1030;t=-90;b=-240;", "")
o_flist.ElementID = f_list.ElementID
o_flist.Update()

# Messages for alt listar
# Msg 1: Actor -> Controller index()
c1 = el_act.Connectors.AddNew("index()", "Sequence")
c1.SupplierID = el_ctrl.ElementID
c1.SequenceNo = 1
c1.Update()
el_act.Connectors.Refresh()
l1 = diag.DiagramLinks.AddNew("", "")
l1.ConnectorID = c1.ConnectorID
l1.Update()

# Msg 2: Controller -> E_Tenant get()
c2 = el_ctrl.Connectors.AddNew("get()", "Sequence")
c2.SupplierID = el_m.ElementID
c2.SequenceNo = 2
c2.Update()
el_ctrl.Connectors.Refresh()
l2 = diag.DiagramLinks.AddNew("", "")
l2.ConnectorID = c2.ConnectorID
l2.Update()

# Msg 3: E_Tenant -> Controller return()
c3 = el_m.Connectors.AddNew("return()", "Sequence")
c3.SupplierID = el_ctrl.ElementID
c3.SequenceNo = 3
c3.Update()
el_m.Connectors.Refresh()
l3 = diag.DiagramLinks.AddNew("", "")
l3.ConnectorID = c3.ConnectorID
l3.Update()

# Fragment alt crear (starts from Interface l=150 to entities r=1030)
f_crear = pkg.Elements.AddNew("crear", "InteractionFragment")
f_crear.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = 'alt' WHERE Object_ID = {f_crear.ElementID}")
o_fcrear = diag.DiagramObjects.AddNew("l=150;r=1030;t=-260;b=-520;", "")
o_fcrear.ElementID = f_crear.ElementID
o_fcrear.Update()

# Msg 4: Actor -> Controller create()
c4 = el_act.Connectors.AddNew("create()", "Sequence")
c4.SupplierID = el_ctrl.ElementID
c4.SequenceNo = 4
c4.Update()
el_act.Connectors.Refresh()
l4 = diag.DiagramLinks.AddNew("", "")
l4.ConnectorID = c4.ConnectorID
l4.Update()

# Msg 5: Controller -> E_SubscriptionPlan get()
c5 = el_ctrl.Connectors.AddNew("get()", "Sequence")
c5.SupplierID = el_s2.ElementID
c5.SequenceNo = 5
c5.Update()
el_ctrl.Connectors.Refresh()
l5 = diag.DiagramLinks.AddNew("", "")
l5.ConnectorID = c5.ConnectorID
l5.Update()

# Msg 6: E_SubscriptionPlan -> Controller return()
c6 = el_s2.Connectors.AddNew("return()", "Sequence")
c6.SupplierID = el_ctrl.ElementID
c6.SequenceNo = 6
c6.Update()
el_s2.Connectors.Refresh()
l6 = diag.DiagramLinks.AddNew("", "")
l6.ConnectorID = c6.ConnectorID
l6.Update()

# Msg 7: Controller -> V.CrearEmpresa view()
c7 = el_ctrl.Connectors.AddNew("view()", "Sequence")
c7.SupplierID = el_vcrear.ElementID
c7.SequenceNo = 7
c7.Update()
el_ctrl.Connectors.Refresh()
l7 = diag.DiagramLinks.AddNew("", "")
l7.ConnectorID = c7.ConnectorID
l7.Update()

# Msg 8: V.CrearEmpresa -> Controller store()
c8 = el_vcrear.Connectors.AddNew("store()", "Sequence")
c8.SupplierID = el_ctrl.ElementID
c8.SequenceNo = 8
c8.Update()
el_vcrear.Connectors.Refresh()
l8 = diag.DiagramLinks.AddNew("", "")
l8.ConnectorID = c8.ConnectorID
l8.Update()

# Msg 9: Controller -> E_Tenant create()
c9 = el_ctrl.Connectors.AddNew("create()", "Sequence")
c9.SupplierID = el_m.ElementID
c9.SequenceNo = 9
c9.Update()
el_ctrl.Connectors.Refresh()
l9 = diag.DiagramLinks.AddNew("", "")
l9.ConnectorID = c9.ConnectorID
l9.Update()

# Fragment loop (starts from Controller l=420 to entities r=1030)
f_loop = pkg.Elements.AddNew("asignarPlan", "InteractionFragment")
f_loop.Update()
rep.Execute(f"UPDATE t_object SET PDATA1 = 'loop' WHERE Object_ID = {f_loop.ElementID}")
o_floop = diag.DiagramObjects.AddNew("l=420;r=1030;t=-540;b=-700;", "")
o_floop.ElementID = f_loop.ElementID
o_floop.Update()

# Msg 10: Controller -> E_Subscription create()
c10 = el_ctrl.Connectors.AddNew("create()", "Sequence")
c10.SupplierID = el_s1.ElementID
c10.SequenceNo = 10
c10.Update()
el_ctrl.Connectors.Refresh()
l10 = diag.DiagramLinks.AddNew("", "")
l10.ConnectorID = c10.ConnectorID
l10.Update()

diag.DiagramObjects.Refresh()
diag.DiagramLinks.Refresh()
diag.Update()

project = rep.GetProjectInterface()
project.PutDiagramImageToFile(diag.DiagramGUID, r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\test_seq_verif.png", 1)

# Cleanup test pkg
for i in range(root.Packages.Count - 1, -1, -1):
    if root.Packages.GetAt(i).Name == "TEST_SEQ_VERIF":
        root.Packages.Delete(i)
        break
root.Packages.Refresh()

rep.CloseFile()
rep.Exit()
print("TEST_SEQ_VERIF_DONE")
