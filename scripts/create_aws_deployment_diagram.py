import win32com.client
import os

def main():
    print("Iniciando creación del Diagrama de Despliegue en AWS (UML 2.5 Ortogonal)...")
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

        diag = target_pkg.Diagrams.AddNew("Diagrama de Despliegue en AWS (UML 2.5) - Etapa 1", "Deployment")
        diag.Update()

        # Nodos y Dispositivos con layout ortogonal sin colisiones
        elements_def = {
            # ZONA 1: CLIENTES Y TERMINALES (Col 1: L=50 .. 320)
            "Dev_Mobile": {
                "name": "Dispositivo Móvil\n(Android / iOS)\n[App Flutter + SQLite Local]",
                "type": "Device",
                "stereotype": "device",
                "coords": (50, 320, -50, -190),
                "notes": "Terminal del vendedor en sucursal con Flutter, réplica local SQLite y monitor de conectividad (Semáforo)."
            },
            "Dev_WebPC": {
                "name": "Navegador Web Cliente\n(PC / Laptop PWA)\n[Angular 21 + IndexedDB]",
                "type": "Device",
                "stereotype": "device",
                "coords": (50, 320, -240, -380),
                "notes": "Cliente web progresivo (PWA) con Angular 21, Service Worker y almacenamiento local en IndexedDB."
            },
            "Dev_AdminPC": {
                "name": "Equipo Administrador\n(PC / Estación SaaS)\n[Dashboard Admin Angular]",
                "type": "Device",
                "stereotype": "device",
                "coords": (50, 320, -430, -570),
                "notes": "Estación de trabajo administrativa para el Superadministrador de la plataforma y Administradores de Tenant."
            },

            # ZONA 2: BORDE Y SEGURIDAD PERIMETRAL AWS (Col 2: L=400 .. 660)
            "AWS_Route53": {
                "name": "Amazon Route 53\n(DNS & Multi-tenant Routing)",
                "type": "Node",
                "stereotype": "service",
                "coords": (400, 660, -50, -170),
                "notes": "Servicio DNS con enrutamiento dinámico para subdominios multi-tenant (*.fashionstore.com)."
            },
            "AWS_WAF_CDN": {
                "name": "AWS WAF + CloudFront\n(Seguridad L7 & CDN Edge)",
                "type": "Node",
                "stereotype": "firewall",
                "coords": (400, 660, -240, -380),
                "notes": "Firewall perimetral y distribución de activos estáticos Angular con mitigación de ataques L7."
            },
            "AWS_ALB": {
                "name": "AWS Application Load Balancer\n(ALB - TLS Termination)",
                "type": "Node",
                "stereotype": "router",
                "coords": (400, 660, -430, -570),
                "notes": "Balanceador de carga elástico con terminación HTTPS/TLS y balanceo hacia contenedores."
            },

            # ZONA 3: CÓMPUTO Y APLICACIÓN (Col 3: L=740 .. 1000)
            "AWS_ECS_Nginx": {
                "name": "Servidor Web Proxy\n(Contenedor Nginx Reverse Proxy)",
                "type": "Node",
                "stereotype": "server",
                "coords": (740, 1000, -430, -570),
                "notes": "Proxy inverso para enrutamiento interno, compresión gzip y despacho hacia la API."
            },
            "AWS_ECS_Backend": {
                "name": "Servidor de Aplicaciones\n(Contenedor FastAPI / Uvicorn)",
                "type": "Node",
                "stereotype": "server",
                "coords": (740, 1000, -620, -780),
                "notes": "Contenedor Docker Python 3.13 con API REST modular, gobernanza multi-tenant y sincronización."
            },

            # ZONA 4: DATOS Y ALMACENAMIENTO (Col 4: L=1080 .. 1360)
            "AWS_RDS_Postgres": {
                "name": "Amazon RDS PostgreSQL 16\n(Multi-AZ Multi-tenant)",
                "type": "Node",
                "stereotype": "database",
                "coords": (1080, 1360, -430, -570),
                "notes": "Base de datos relacional centralizada con particionamiento por tenant_id, réplicas y alta disponibilidad."
            },
            "AWS_S3": {
                "name": "Amazon S3 Bucket\n(Imágenes y Catálogo Multimedia)",
                "type": "Node",
                "stereotype": "storage",
                "coords": (1080, 1360, -620, -780),
                "notes": "Almacenamiento de objetos duradero para imágenes de prendas textiles y comprobantes."
            },
            "AWS_ElastiCache": {
                "name": "Amazon ElastiCache\n(Redis Cluster Rate-Limiter)",
                "type": "Node",
                "stereotype": "cache",
                "coords": (1080, 1360, -820, -960),
                "notes": "Caché en memoria para limitación de tasa (Rate Limiting) y sesiones volátiles."
            }
        }

        element_map = {}
        for key, pdata in elements_def.items():
            el = target_pkg.Elements.AddNew(pdata["name"], pdata["type"])
            el.Stereotype = pdata["stereotype"]
            el.Notes = pdata["notes"]
            el.Update()
            element_map[key] = el

            l, r, t, b = pdata["coords"]
            d_obj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
            d_obj.ElementID = el.ElementID
            d_obj.left = l; d_obj.right = r; d_obj.top = t; d_obj.bottom = b
            d_obj.Update()

        # Conexiones limpias y sin cruces (Communication Paths)
        communication_paths = [
            # Resolución DNS desde el borde
            ("AWS_Route53", "AWS_WAF_CDN", "DNS Resolution : 53"),

            # Clientes hacia WAF / CloudFront (Tráfico Seguro HTTPS)
            ("Dev_Mobile", "AWS_WAF_CDN", "HTTPS : 443 (REST Sync)"),
            ("Dev_WebPC", "AWS_WAF_CDN", "HTTPS : 443 (PWA Web)"),
            ("Dev_AdminPC", "AWS_WAF_CDN", "HTTPS : 443 (Admin Portal)"),

            # WAF/CDN hacia Balanceador de Carga (Vertical)
            ("AWS_WAF_CDN", "AWS_ALB", "HTTPS : 443 (TLS)"),

            # ALB hacia Nginx Proxy (Horizontal)
            ("AWS_ALB", "AWS_ECS_Nginx", "HTTP : 80 (VPC Internal)"),

            # Nginx hacia Backend FastAPI (Vertical)
            ("AWS_ECS_Nginx", "AWS_ECS_Backend", "HTTP : 8000 (ASGI Proxy)"),

            # Backend FastAPI hacia Persistencia y Servicios AWS (Horizontal & Radial limpio)
            ("AWS_ECS_Backend", "AWS_RDS_Postgres", "TCP : 5432 (SQLAlchemy Pool)"),
            ("AWS_ECS_Backend", "AWS_S3", "HTTPS : 443 (Boto3 SDK)"),
            ("AWS_ECS_Backend", "AWS_ElastiCache", "TCP : 6379 (Redis Protocol)")
        ]

        for src_key, dst_key, label in communication_paths:
            src_el = element_map[src_key]
            dst_el = element_map[dst_key]

            conn = src_el.Connectors.AddNew(label, "CommunicationPath")
            conn.SupplierID = dst_el.ElementID
            conn.Direction = "Source -> Destination"
            conn.Update()

        diag.Update()
        repo.SaveDiagram(diag.DiagramID)
        repo.ReloadDiagram(diag.DiagramID)

        out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6'
        img_path = os.path.join(out_dir, "diagrama_despliegue_aws_etapa1_clean.png")
        repo.GetProjectInterface().PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
        print(f"Diagrama de despliegue en AWS limpio exportado a: {img_path}")

    finally:
        try: repo.CloseFile()
        except: pass
        try: ea.Quit()
        except: pass

if __name__ == '__main__':
    main()
