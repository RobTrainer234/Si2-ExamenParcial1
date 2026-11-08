import win32com.client
import os

def main():
    print("Iniciando creación del Diagrama de Despliegue AWS idéntico al ejemplo...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    try:
        if not repo.ConnectionString:
            repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

        root_model = repo.Models.GetAt(0)

        # Buscar o crear paquete de despliegue
        target_pkg = None
        for p in root_model.Packages:
            if 'Despliegue' in p.Name and 'Segundo Parcial' in p.Name:
                target_pkg = p
                break

        if target_pkg is None:
            target_pkg = root_model.Packages.AddNew("Segundo Parcial - Diagrama de Despliegue (AWS)", "Package")
            target_pkg.Update()
            root_model.Packages.Refresh()

        # Limpiar
        for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
            target_pkg.Diagrams.Delete(i)
        target_pkg.Diagrams.Refresh()

        for i in range(target_pkg.Elements.Count - 1, -1, -1):
            target_pkg.Elements.Delete(i)
        target_pkg.Elements.Refresh()

        diag = target_pkg.Diagrams.AddNew("Diagrama de Despliegue - AWS Cloud Multi-Tenant", "Deployment")
        diag.Update()

        # 1. Crear Nodos Principales
        # Dispositivos Clientes
        dev_movil = target_pkg.Elements.AddNew("Dispositivo Movil\n(Android / iOS)", "Device")
        dev_movil.Stereotype = "device"
        dev_movil.Update()

        dev_user = target_pkg.Elements.AddNew("Dispositivo del Usuario\n(PC / Laptop / Tablet)", "Device")
        dev_user.Stereotype = "device"
        dev_user.Update()

        env_browser = target_pkg.Elements.AddNew("Navegador Web\n(Chrome / Firefox / Edge)", "ExecutionEnvironment")
        env_browser.Update()

        art_angular = target_pkg.Elements.AddNew("Frontend Web Angular 21\n(SPA Build / Dist)", "Artifact")
        art_angular.Update()

        # Nodo de Red Internet
        net_internet = target_pkg.Elements.AddNew("Internet\n(HTTPS / WSS / TLS)", "Node")
        net_internet.Stereotype = "network"
        net_internet.Update()

        # Nube AWS (Boundary / Cloud)
        aws_cloud = target_pkg.Elements.AddNew("AWS Cloud", "Boundary")
        aws_cloud.Update()
        repo.Execute(f"UPDATE t_object SET PDATA1 = 'Cloud' WHERE Object_ID = {aws_cloud.ElementID}")

        # AWS Load Balancer
        alb = target_pkg.Elements.AddNew("AWS Application Load Balancer\n(ALB / SSL / Reverse Proxy)", "Node")
        alb.Stereotype = "loadBalancer"
        alb.Update()

        # Cluster ECS / EC2
        cluster = target_pkg.Elements.AddNew("AWS EC2 / ECS Cluster\n(Docker Runtime)", "Node")
        cluster.Update()

        # Contenedores dentro del Cluster
        cont_backend = target_pkg.Elements.AddNew("Contenedor Backend\n(FastAPI / Python 3.13 / REST & WSS)", "Component")
        cont_backend.Update()

        cont_ia = target_pkg.Elements.AddNew("Contenedor Servicio IA\n(FastAPI / Python 3.13 / ML)", "Component")
        cont_ia.Update()

        # Nodos a la derecha del Cluster
        rds = target_pkg.Elements.AddNew("Amazon RDS PostgreSQL 16\n(BD Multi-Tenant Aislada)", "Node")
        rds.Stereotype = "database"
        rds.Update()

        kms = target_pkg.Elements.AddNew("AWS KMS\n(Cifrado Bitacora y Llaves)", "Node")
        kms.Stereotype = "security"
        kms.Update()

        s3 = target_pkg.Elements.AddNew("Amazon S3 Bucket\n(Backups y Assets)", "Node")
        s3.Update()

        # Nodos externos abajo
        stripe = target_pkg.Elements.AddNew("Stripe API Cloud\n(Pasarela de Pagos SaaS)", "Node")
        stripe.Stereotype = "external"
        stripe.Update()

        brevo = target_pkg.Elements.AddNew("Brevo Cloud API\n(SMTP / Email Transaccional)", "Node")
        brevo.Stereotype = "external"
        brevo.Update()

        # 2. Agregar elementos al diagrama con coordenadas y Sequence (Z-order)
        # Background: AWS Cloud (Sequence=100)
        d_cloud = diag.DiagramObjects.AddNew("l=420;r=1240;t=-30;b=-870;", "")
        d_cloud.ElementID = aws_cloud.ElementID
        d_cloud.left = 420; d_cloud.right = 1240; d_cloud.top = -30; d_cloud.bottom = -870
        d_cloud.Sequence = 100
        d_cloud.Update()

        # Cluster (Sequence=50)
        d_cluster = diag.DiagramObjects.AddNew("l=660;r=960;t=-120;b=-560;", "")
        d_cluster.ElementID = cluster.ElementID
        d_cluster.left = 660; d_cluster.right = 960; d_cluster.top = -120; d_cluster.bottom = -560
        d_cluster.Sequence = 50
        d_cluster.Update()

        # Dispositivo del Usuario (Sequence=50)
        d_user = diag.DiagramObjects.AddNew("l=30;r=240;t=-330;b=-590;", "")
        d_user.ElementID = dev_user.ElementID
        d_user.left = 30; d_user.right = 240; d_user.top = -330; d_user.bottom = -590
        d_user.Sequence = 50
        d_user.Update()

        # Elementos de Primer Plano (Sequence=1..20)
        foreground_objs = [
            (dev_movil, 30, 240, -90, -280),
            (env_browser, 45, 225, -395, -485),
            (art_angular, 55, 215, -505, -575),
            (net_internet, 270, 400, -240, -360),
            (alb, 460, 625, -240, -360),
            (cont_backend, 690, 930, -210, -345),
            (cont_ia, 690, 930, -385, -520),
            (rds, 1010, 1210, -120, -260),
            (kms, 1010, 1210, -340, -460),
            (s3, 1010, 1210, -590, -760),
            (stripe, 470, 670, -640, -800),
            (brevo, 715, 915, -640, -800)
        ]

        seq = 1
        for el, l, r, t, b in foreground_objs:
            d = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d.ElementID = el.ElementID
            d.left = l; d.right = r; d.top = t; d.bottom = b
            d.Sequence = seq
            seq += 1
            d.Update()

        # 3. Conexiones (Communication Paths / Dependencies) exactamente como en la imagen
        connections = [
            (dev_movil, net_internet, "HTTPS / WSS"),
            (dev_user, net_internet, "HTTPS"),
            (net_internet, alb, "TLS 443"),
            (alb, cont_backend, "Reverse Proxy (HTTP/WSS)"),
            (cont_backend, cont_ia, "REST Inter-service"),
            (cont_backend, rds, "TCP 5432"),
            (cont_ia, rds, "Postgres Driver"),
            (cont_backend, kms, "AWS SDK Cifrado"),
            (cont_backend, s3, "AWS S3 SDK"),
            (cont_backend, stripe, "Stripe Webhooks / HTTPS"),
            (cont_backend, brevo, "SMTP 587 / REST")
        ]

        for src, dst, label in connections:
            conn = src.Connectors.AddNew(label, "CommunicationPath")
            conn.SupplierID = dst.ElementID
            conn.Direction = "Source -> Destination"
            conn.Update()

        diag.Update()
        repo.SaveDiagram(diag.DiagramID)
        repo.ReloadDiagram(diag.DiagramID)

        out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
        img_path = os.path.join(out_dir, "diagrama_despliegue_aws_exacto_ejemplo.png")
        repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
        print(f"Diagrama de despliegue exacto al ejemplo exportado a: {img_path}")

    finally:
        try: repo.CloseFile()
        except: pass
        try: ea.Quit()
        except: pass

if __name__ == '__main__':
    main()
