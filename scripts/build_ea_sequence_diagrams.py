# -*- coding: utf-8 -*-
"""
Script maestro para generar los Diagramas de Secuencia para todos los Casos de Uso
de la Etapa 1 en Enterprise Architect.

Reglas del docente estrictamente implementadas:
1. Actor a la izquierda.
2. V.Index y vistas de interfaz a continuación (RECTANGULARES, no circulares).
3. Controlador del caso de uso a continuación (RECTANGULAR).
4. Entidades del caso de uso a la derecha (las MISMAS que en los diagramas de análisis de clase).
5. Fragmentos 'alt' y 'opt' comienzan desde la INTERFAZ (l=150) hasta las entidades que interactúan.
6. Fragmentos 'loop' comienzan desde el CONTROLADOR (l=540) hasta las entidades que interactúan.
7. Todos los lifelines son elementos rectangulares (Type = 'Sequence').

Archivo destino: 'docs/uml/FashioStore/CasosDeUso_SegundoParcial.eap'
Paquete destino: 'Segundo Parcial - Diagramas de Secuencia (Etapa 1)'
"""

import os
import shutil
import subprocess
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\sequence"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87\sequence"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# Definición exhaustiva de los 12 Diagramas de Secuencia
SEQUENCE_DATA = [
    {
        "code": "CU-01",
        "diag_name": "sd CU-01 Registrar Empresa Contratante (Tenant)",
        "title": "CU-01 Registrar Empresa Contratante (Tenant)",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu01-registrar-empresa.png",
        "lifelines": [
            ("V.EmpresaIndex", 160, 260),
            ("V.CrearEmpresa", 290, 390),
            ("V.ModificarEmpresa", 420, 520),
            ("TenantController", 550, 670),
            ("E_Tenant", 710, 830),
            ("E_Subscription", 860, 980),
            ("E_SubscriptionPlan", 1010, 1130),
            ("E_Bitacora", 1160, 1280)
        ],
        "fragments": [
            ("alt", "listar", 0, 150, 1290, -90, -240),
            ("alt", "crear", 0, 150, 1290, -255, -470),
            ("alt", "modificar", 0, 150, 1290, -485, -680),
            ("alt", "desactivar", 0, 150, 1290, -695, -835)
        ],
        "messages": [
            ("actor", "TenantController", "index()"),
            ("TenantController", "E_Tenant", "get()"),
            ("E_Tenant", "TenantController", "return()"),
            ("actor", "TenantController", "create()"),
            ("TenantController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "TenantController", "return()"),
            ("TenantController", "V.CrearEmpresa", "view()"),
            ("V.CrearEmpresa", "TenantController", "store(datos)"),
            ("TenantController", "E_Tenant", "create(datos)"),
            ("TenantController", "E_Subscription", "create(plan_id)"),
            ("TenantController", "E_Bitacora", "log(accion)"),
            ("actor", "TenantController", "edit(id)"),
            ("TenantController", "V.ModificarEmpresa", "view()"),
            ("V.ModificarEmpresa", "TenantController", "update(id, datos)"),
            ("TenantController", "E_Tenant", "update(datos)"),
            ("TenantController", "E_Bitacora", "log(cambio)"),
            ("actor", "TenantController", "destroy(id)"),
            ("TenantController", "E_Tenant", "delete(id)"),
            ("TenantController", "E_Bitacora", "log(baja)")
        ]
    },
    {
        "code": "CU-02",
        "diag_name": "sd CU-02 Gestionar Planes de Suscripción",
        "title": "CU-02 Gestionar Planes de Suscripción",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu02-gestionar-planes.png",
        "lifelines": [
            ("V.PlanIndex", 160, 260),
            ("V.CrearPlan", 290, 390),
            ("V.EditarPlan", 420, 520),
            ("SubscriptionPlanController", 550, 670),
            ("E_SubscriptionPlan", 710, 830),
            ("E_Subscription", 860, 980),
            ("E_Tenant", 1010, 1130)
        ],
        "fragments": [
            ("alt", "listar", 0, 150, 1140, -90, -240),
            ("alt", "crear", 0, 150, 1140, -255, -460),
            ("alt", "modificar", 0, 150, 1140, -475, -670),
            ("alt", "cambiarEstado", 0, 150, 1140, -685, -835)
        ],
        "messages": [
            ("actor", "SubscriptionPlanController", "index()"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "SubscriptionPlanController", "return()"),
            ("actor", "SubscriptionPlanController", "create()"),
            ("SubscriptionPlanController", "V.CrearPlan", "view()"),
            ("V.CrearPlan", "SubscriptionPlanController", "store(datosPlan)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "create(datosPlan)"),
            ("actor", "SubscriptionPlanController", "edit(id)"),
            ("SubscriptionPlanController", "V.EditarPlan", "view()"),
            ("V.EditarPlan", "SubscriptionPlanController", "update(id, limites)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "update(limites)"),
            ("actor", "SubscriptionPlanController", "destroy(id)"),
            ("SubscriptionPlanController", "E_Subscription", "get(plan_id)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "delete(id)")
        ]
    },
    {
        "code": "CU-03",
        "diag_name": "sd CU-03 Asignar y Renovar Suscripción de Empresa",
        "title": "CU-03 Asignar y Renovar Suscripción de Empresa",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu03-asignar-renovar-suscripcion.png",
        "lifelines": [
            ("V.SuscripcionIndex", 160, 260),
            ("V.AsignarSuscripcion", 290, 390),
            ("V.RenovarPlazo", 420, 520),
            ("SubscriptionController", 550, 670),
            ("E_Subscription", 710, 830),
            ("E_Tenant", 860, 980),
            ("E_SubscriptionPlan", 1010, 1130),
            ("E_Bitacora", 1160, 1280)
        ],
        "fragments": [
            ("alt", "consultar", 0, 150, 1290, -90, -240),
            ("alt", "asignarPlan", 0, 150, 1290, -255, -470),
            ("alt", "renovarPlazo", 0, 150, 1290, -485, -680),
            ("alt", "cancelar", 0, 150, 1290, -695, -835)
        ],
        "messages": [
            ("actor", "SubscriptionController", "index(empresa_id)"),
            ("SubscriptionController", "E_Subscription", "get()"),
            ("E_Subscription", "SubscriptionController", "return()"),
            ("actor", "SubscriptionController", "create(empresa_id)"),
            ("SubscriptionController", "E_SubscriptionPlan", "get()"),
            ("SubscriptionController", "V.AsignarSuscripcion", "view()"),
            ("V.AsignarSuscripcion", "SubscriptionController", "store(plan_id)"),
            ("SubscriptionController", "E_Subscription", "create(plan_id)"),
            ("SubscriptionController", "E_Bitacora", "log(asignacion)"),
            ("actor", "SubscriptionController", "edit(id)"),
            ("SubscriptionController", "V.RenovarPlazo", "view()"),
            ("V.RenovarPlazo", "SubscriptionController", "update(id, dias)"),
            ("SubscriptionController", "E_Subscription", "update(vigencia)"),
            ("SubscriptionController", "E_Bitacora", "log(renovacion)"),
            ("actor", "SubscriptionController", "destroy(id)"),
            ("SubscriptionController", "E_Subscription", "delete(id)")
        ]
    },
    {
        "code": "CU-04",
        "diag_name": "sd CU-04 Controlar Límites y Restricciones por Plan",
        "title": "CU-04 Controlar Límites y Restricciones por Plan",
        "actor": "Tenant Admin",
        "filename": "secuencia-cu04-controlar-limites-plan.png",
        "lifelines": [
            ("V.ControlLimitesIndex", 160, 260),
            ("V.AlertaExcesoModal", 290, 390),
            ("PlanLimitsController", 550, 670),
            ("E_SubscriptionPlan", 710, 830),
            ("E_Subscription", 860, 980),
            ("E_Branch", 1010, 1130),
            ("E_Bitacora", 1160, 1280)
        ],
        "fragments": [
            ("alt", "verificarCuotaSucursales", 0, 150, 1290, -90, -280),
            ("alt", "verificarAccesoIA", 0, 150, 1290, -295, -490),
            ("opt", "limiteAlcanzadoBloqueo", 1, 150, 1290, -505, -700),
            ("opt", "cuotaDisponible", 1, 150, 1290, -715, -835)
        ],
        "messages": [
            ("actor", "PlanLimitsController", "verify_branches(tenant_id)"),
            ("PlanLimitsController", "E_Branch", "count_active()"),
            ("E_Branch", "PlanLimitsController", "return(total)"),
            ("PlanLimitsController", "E_SubscriptionPlan", "get_max_quota()"),
            ("E_SubscriptionPlan", "PlanLimitsController", "return(max_quota)"),
            ("actor", "PlanLimitsController", "verify_ai_access(tenant_id)"),
            ("PlanLimitsController", "E_SubscriptionPlan", "get_ai_enabled()"),
            ("E_SubscriptionPlan", "PlanLimitsController", "return(habilitado)"),
            ("PlanLimitsController", "V.AlertaExcesoModal", "view_alert()"),
            ("PlanLimitsController", "E_Bitacora", "log_violation(evento)"),
            ("PlanLimitsController", "V.ControlLimitesIndex", "allow_operation()")
        ]
    },
    {
        "code": "CU-05",
        "diag_name": "sd CU-05 Gestionar Sucursales y Empleados por Tenant",
        "title": "CU-05 Gestionar Sucursales y Empleados por Tenant",
        "actor": "Tenant Admin",
        "filename": "secuencia-cu05-gestionar-sucursales-empleados.png",
        "lifelines": [
            ("V.SucursalIndex", 160, 260),
            ("V.CrearSucursal", 290, 390),
            ("V.AsignarPersonal", 420, 520),
            ("BranchEmployeeController", 550, 670),
            ("E_Branch", 710, 830),
            ("E_User", 860, 980),
            ("E_City", 1010, 1130),
            ("E_UserBranch", 1160, 1280)
        ],
        "fragments": [
            ("alt", "listar", 0, 150, 1290, -90, -240),
            ("alt", "registrarSucursal", 0, 150, 1290, -255, -470),
            ("alt", "asignarEmpleado", 0, 150, 1290, -485, -680),
            ("alt", "desactivar", 0, 150, 1290, -695, -835)
        ],
        "messages": [
            ("actor", "BranchEmployeeController", "index(tenant_id)"),
            ("BranchEmployeeController", "E_Branch", "get()"),
            ("E_Branch", "BranchEmployeeController", "return()"),
            ("actor", "BranchEmployeeController", "create()"),
            ("BranchEmployeeController", "E_City", "get()"),
            ("BranchEmployeeController", "V.CrearSucursal", "view()"),
            ("V.CrearSucursal", "BranchEmployeeController", "store(datos)"),
            ("BranchEmployeeController", "E_Branch", "create(datos)"),
            ("actor", "BranchEmployeeController", "edit(branch_id)"),
            ("BranchEmployeeController", "E_User", "get()"),
            ("BranchEmployeeController", "V.AsignarPersonal", "view()"),
            ("V.AsignarPersonal", "BranchEmployeeController", "assign(user_id)"),
            ("BranchEmployeeController", "E_UserBranch", "create(user_id, branch_id)"),
            ("actor", "BranchEmployeeController", "destroy(branch_id)"),
            ("BranchEmployeeController", "E_Branch", "delete(branch_id)")
        ]
    },
    {
        "code": "CU-06",
        "diag_name": "sd CU-06 Descargar y Almacenar Catálogo Offline",
        "title": "CU-06 Descargar y Almacenar Catálogo Offline",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu06-descargar-catalogo-offline.png",
        "lifelines": [
            ("V.SyncIndex", 160, 260),
            ("V.ProgresoDescarga", 290, 390),
            ("SyncCatalogController", 550, 670),
            ("E_CatalogoLocal", 710, 830),
            ("E_VarianteLocal", 860, 980),
            ("E_StockLocal", 1010, 1130),
            ("E_MetadatosSync", 1160, 1280)
        ],
        "fragments": [
            ("alt", "solicitarDescarga", 0, 150, 1290, -90, -280),
            # loop comienza en el controlador (l=540)
            ("loop", "persistirLotePrendas", 4, 540, 1290, -295, -560),
            ("opt", "finalizarSincronizacion", 1, 150, 1290, -575, -760)
        ],
        "messages": [
            ("actor", "SyncCatalogController", "request_catalog(branch_id)"),
            ("SyncCatalogController", "E_MetadatosSync", "get_last_sync()"),
            ("E_MetadatosSync", "SyncCatalogController", "return(timestamp)"),
            ("SyncCatalogController", "V.ProgresoDescarga", "view()"),
            ("SyncCatalogController", "E_CatalogoLocal", "create(prenda)"),
            ("SyncCatalogController", "E_VarianteLocal", "create(variante)"),
            ("SyncCatalogController", "E_StockLocal", "update(stock)"),
            ("SyncCatalogController", "E_MetadatosSync", "update(timestamp)"),
            ("SyncCatalogController", "E_CatalogoLocal", "purge_obsolete()"),
            ("SyncCatalogController", "V.SyncIndex", "notify_completed()")
        ]
    },
    {
        "code": "CU-07",
        "diag_name": "sd CU-07 Consultar Catálogo y Existencias Offline",
        "title": "CU-07 Consultar Catálogo y Existencias Offline",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu07-consultar-catalogo-existencias.png",
        "lifelines": [
            ("V.CatalogoOfflineIndex", 160, 260),
            ("V.DetallePrendaModal", 290, 390),
            ("OfflineCatalogController", 550, 670),
            ("E_ProductoOffline", 710, 830),
            ("E_VarianteOffline", 860, 980),
            ("E_StockOffline", 1010, 1130)
        ],
        "fragments": [
            ("alt", "buscarPrendas", 0, 150, 1140, -90, -280),
            ("alt", "consultarExistencias", 0, 150, 1140, -295, -520),
            ("opt", "alertarStockBajo", 1, 150, 1140, -535, -740)
        ],
        "messages": [
            ("actor", "OfflineCatalogController", "search(filtro, categoria)"),
            ("OfflineCatalogController", "E_ProductoOffline", "get()"),
            ("E_ProductoOffline", "OfflineCatalogController", "return()"),
            ("actor", "OfflineCatalogController", "select_item(sku)"),
            ("OfflineCatalogController", "E_VarianteOffline", "get(sku)"),
            ("OfflineCatalogController", "E_StockOffline", "get(variant_id)"),
            ("E_StockOffline", "OfflineCatalogController", "return(stock)"),
            ("OfflineCatalogController", "V.DetallePrendaModal", "view()"),
            ("OfflineCatalogController", "E_StockOffline", "check_low_stock()"),
            ("OfflineCatalogController", "V.DetallePrendaModal", "show_warning()")
        ]
    },
    {
        "code": "CU-08",
        "diag_name": "sd CU-08 Registrar Venta de Contado Offline",
        "title": "CU-08 Registrar Venta de Contado Offline",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu08-registrar-venta-contado.png",
        "lifelines": [
            ("V.VentaPOSIndex", 160, 260),
            ("V.TicketCobroModal", 290, 390),
            ("OfflinePOSController", 550, 670),
            ("E_VentaLocal", 710, 830),
            ("E_DetalleVentaLocal", 860, 980),
            ("E_StockOffline", 1010, 1130),
            ("E_ColaOperacionesSync", 1160, 1280)
        ],
        "fragments": [
            ("alt", "agregarItems", 0, 150, 1290, -90, -280),
            ("alt", "confirmarCobroEfectivo", 0, 150, 1290, -295, -560),
            ("opt", "encolarOperacionSync", 1, 150, 1290, -575, -760)
        ],
        "messages": [
            ("actor", "OfflinePOSController", "add_item(sku, cant)"),
            ("OfflinePOSController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflinePOSController", "return(disponible)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "update_total()"),
            ("actor", "OfflinePOSController", "confirm_sale(datosCobro)"),
            ("OfflinePOSController", "E_VentaLocal", "create(venta)"),
            ("OfflinePOSController", "E_DetalleVentaLocal", "create(detalles)"),
            ("OfflinePOSController", "E_StockOffline", "deduct_stock(cant)"),
            ("OfflinePOSController", "V.TicketCobroModal", "view_receipt()"),
            ("OfflinePOSController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "notify_queued()")
        ]
    },
    {
        "code": "CU-09",
        "diag_name": "sd CU-09 Registrar Reserva de Prendas Offline",
        "title": "CU-09 Registrar Reserva de Prendas Offline",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu09-registrar-reserva-prendas.png",
        "lifelines": [
            ("V.ReservaPOSIndex", 160, 260),
            ("V.TicketApartadoModal", 290, 390),
            ("OfflineReservationController", 550, 670),
            ("E_ReservaLocal", 710, 830),
            ("E_DetalleReservaLocal", 860, 980),
            ("E_StockOffline", 1010, 1130),
            ("E_ColaOperacionesSync", 1160, 1280)
        ],
        "fragments": [
            ("alt", "seleccionarPrenda", 0, 150, 1290, -90, -280),
            ("alt", "confirmarApartado", 0, 150, 1290, -295, -560),
            ("opt", "encolarSyncReserva", 1, 150, 1290, -575, -760)
        ],
        "messages": [
            ("actor", "OfflineReservationController", "select_item(sku)"),
            ("OfflineReservationController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflineReservationController", "return()"),
            ("actor", "OfflineReservationController", "confirm_reservation(datosCliente)"),
            ("OfflineReservationController", "E_ReservaLocal", "create(reserva)"),
            ("OfflineReservationController", "E_DetalleReservaLocal", "create(detalles)"),
            ("OfflineReservationController", "E_StockOffline", "lock_stock(cant)"),
            ("OfflineReservationController", "V.TicketApartadoModal", "view()"),
            ("OfflineReservationController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflineReservationController", "V.ReservaPOSIndex", "notify_queued()")
        ]
    },
    {
        "code": "CU-23",
        "diag_name": "sd CU-23 Notificar Estado de Conectividad (Semáforo)",
        "title": "CU-23 Notificar Estado de Conectividad (Semáforo)",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu23-notificar-estado-conectividad.png",
        "lifelines": [
            ("V.SemaforoBarraIndex", 160, 260),
            ("V.BannerAlertaModal", 290, 390),
            ("NetworkMonitorController", 550, 670),
            ("E_EstadoConectividad", 710, 830),
            ("E_ColaOperacionesSync", 860, 980),
            ("E_ConfiguracionRed", 1010, 1130)
        ],
        "fragments": [
            ("alt", "monitorearEnlace", 0, 150, 1140, -90, -280),
            ("alt", "conmutarEstado", 0, 150, 1140, -295, -520),
            ("opt", "alertaDesconexion", 1, 150, 1140, -535, -740)
        ],
        "messages": [
            ("actor", "NetworkMonitorController", "poll_status()"),
            ("NetworkMonitorController", "E_ConfiguracionRed", "get_healthcheck_url()"),
            ("NetworkMonitorController", "E_EstadoConectividad", "get_current()"),
            ("E_EstadoConectividad", "NetworkMonitorController", "return()"),
            ("NetworkMonitorController", "E_EstadoConectividad", "update(online_status)"),
            ("NetworkMonitorController", "E_ColaOperacionesSync", "count_pending()"),
            ("E_ColaOperacionesSync", "NetworkMonitorController", "return(total_pendientes)"),
            ("NetworkMonitorController", "V.SemaforoBarraIndex", "update_badge(color, total)"),
            ("NetworkMonitorController", "V.BannerAlertaModal", "show_offline_warning()")
        ]
    },
    {
        "code": "CU-24",
        "diag_name": "sd CU-24 Instalar y Registrar Service Worker (PWA)",
        "title": "CU-24 Instalar y Registrar Service Worker (PWA)",
        "actor": "Cliente",
        "filename": "secuencia-cu24-instalar-service-worker.png",
        "lifelines": [
            ("V.InstaladorIndex", 160, 260),
            ("V.PromptModal", 290, 390),
            ("ServiceWorkerController", 550, 670),
            ("E_CacheAplicacion", 710, 830),
            ("E_RegistroServiceWorker", 860, 980),
            ("E_ManifiestoPWA", 1010, 1130)
        ],
        "fragments": [
            ("alt", "solicitarInstalacion", 0, 150, 1140, -90, -280),
            # loop comienza en el controlador (l=540)
            ("loop", "cachearRecursosEstaticos", 4, 540, 1140, -295, -520),
            ("opt", "activarModoOffline", 1, 150, 1140, -535, -740)
        ],
        "messages": [
            ("actor", "ServiceWorkerController", "trigger_install_prompt()"),
            ("ServiceWorkerController", "E_ManifiestoPWA", "validate()"),
            ("E_ManifiestoPWA", "ServiceWorkerController", "return(valid)"),
            ("ServiceWorkerController", "V.PromptModal", "view()"),
            ("ServiceWorkerController", "E_CacheAplicacion", "store_asset(url)"),
            ("ServiceWorkerController", "E_RegistroServiceWorker", "update_scope()"),
            ("ServiceWorkerController", "E_RegistroServiceWorker", "activate()"),
            ("ServiceWorkerController", "V.InstaladorIndex", "notify_offline_ready()")
        ]
    },
    {
        "code": "CU-25",
        "diag_name": "sd CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "title": "CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "actor": "Cajero / Vendedor",
        "filename": "secuencia-cu25-configurar-sqlite-movil.png",
        "lifelines": [
            ("V.SQLiteConfigIndex", 160, 260),
            ("V.ProgresoMigracion", 290, 390),
            ("DatabaseMigrationController", 550, 670),
            ("E_BaseDatosSQLite", 710, 830),
            ("E_HistorialMigracion", 860, 980),
            ("E_TablaLocal", 1010, 1130)
        ],
        "fragments": [
            ("alt", "verificarEsquema", 0, 150, 1140, -90, -280),
            # loop comienza en el controlador (l=540)
            ("loop", "ejecutarScriptsDDL", 4, 540, 1140, -295, -520),
            ("opt", "validarIntegridad", 1, 150, 1140, -535, -740)
        ],
        "messages": [
            ("actor", "DatabaseMigrationController", "check_version()"),
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "get_user_version()"),
            ("E_BaseDatosSQLite", "DatabaseMigrationController", "return(version)"),
            ("DatabaseMigrationController", "E_TablaLocal", "execute_ddl(sql)"),
            ("DatabaseMigrationController", "E_HistorialMigracion", "record_migration(v)"),
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "pragma_integrity_check()"),
            ("DatabaseMigrationController", "V.SQLiteConfigIndex", "notify_ready()")
        ]
    }
]

def build_sequence_diagrams():
    print("1. Limpiando procesos previos de EA...")
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)

    print(f"2. Abriendo repositorio EA: {EAP_PATH} ...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError(f"No se pudo abrir el archivo EA: {EAP_PATH}")

    project = rep.GetProjectInterface()
    root_model = rep.Models.GetAt(0)

    # Buscar o crear paquete para Diagramas de Secuencia
    pkg_name = "Segundo Parcial - Diagramas de Secuencia (Etapa 1)"
    seq_pkg = None
    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            seq_pkg = p
            break

    if seq_pkg is None:
        seq_pkg = root_model.Packages.AddNew(pkg_name, "")
        seq_pkg.Notes = "Diagramas de Secuencia con fragmentos alt, opt y loop alineados a las reglas de la cátedra para la Etapa 1."
        seq_pkg.Update()
        root_model.Packages.Refresh()

    print(f"3. Paquete objetivo: '{seq_pkg.Name}'")

    # Limpiar elementos previos en este paquete para evitar duplicados
    for i in range(seq_pkg.Diagrams.Count - 1, -1, -1):
        seq_pkg.Diagrams.Delete(i)
    seq_pkg.Diagrams.Refresh()

    for i in range(seq_pkg.Elements.Count - 1, -1, -1):
        seq_pkg.Elements.Delete(i)
    seq_pkg.Elements.Refresh()

    print(f"4. Generando los {len(SEQUENCE_DATA)} Diagramas de Secuencia en Enterprise Architect...")

    for cu in SEQUENCE_DATA:
        diag_title = cu["diag_name"]
        print(f"   -> Creando: {diag_title} ({cu['title']})...")

        # Diagrama de Secuencia
        diag = seq_pkg.Diagrams.AddNew(diag_title, "Sequence")
        diag.Update()
        seq_pkg.Diagrams.Refresh()

        created_elements = {}

        # 1. Actor (Izquierda)
        el_act = seq_pkg.Elements.AddNew(cu["actor"], "Actor")
        el_act.Update()
        created_elements["actor"] = el_act
        o_act = diag.DiagramObjects.AddNew("l=40;r=110;t=-40;b=-870;", "")
        o_act.ElementID = el_act.ElementID
        o_act.Update()

        # 2. Lifelines (Todos rectangulares: Type = 'Sequence')
        for lf_name, left, right in cu["lifelines"]:
            el_lf = seq_pkg.Elements.AddNew(lf_name, "Sequence")
            el_lf.Update()
            created_elements[lf_name] = el_lf

            o_lf = diag.DiagramObjects.AddNew(f"l={left};r={right};t=-40;b=-870;", "")
            o_lf.ElementID = el_lf.ElementID
            o_lf.Update()

        # 3. Fragmentos Combinados (alt, opt, loop)
        for frag_type, frag_name, subtype_val, fl, fr, ft, fb in cu["fragments"]:
            f_el = seq_pkg.Elements.AddNew(frag_name, "InteractionFragment")
            f_el.Subtype = subtype_val
            f_el.Update()

            o_f = diag.DiagramObjects.AddNew(f"l={fl};r={fr};t={ft};b={fb};", "")
            o_f.ElementID = f_el.ElementID
            o_f.Update()

        # 4. Mensajes de Secuencia
        for seq_idx, (src_key, dst_key, msg_name) in enumerate(cu["messages"], start=1):
            src_el = created_elements[src_key]
            dst_el = created_elements[dst_key]

            con = src_el.Connectors.AddNew(msg_name, "Sequence")
            con.SupplierID = dst_el.ElementID
            con.SequenceNo = seq_idx
            con.Direction = "Source -> Destination"
            con.Update()
            src_el.Connectors.Refresh()

            l_msg = diag.DiagramLinks.AddNew("", "")
            l_msg.ConnectorID = con.ConnectorID
            l_msg.Update()

        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        diag.Update()

        # Exportar PNG de alta resolución
        png_path = os.path.join(OUT_DIR, cu["filename"])
        art_path = os.path.join(ARTIFACT_DIR, cu["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, png_path, 1)
        shutil.copy2(png_path, art_path)
        print(f"      -> Diagrama exportado: {png_path}")

    seq_pkg.Diagrams.Refresh()
    seq_pkg.Elements.Refresh()

    rep.CloseFile()
    rep.Exit()
    print("=" * 70)
    print("DIAGRAMAS DE SECUENCIA GUARDADOS EN ENTERPRISE ARCHITECT!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Total diagramas creados: {len(SEQUENCE_DATA)}")
    print("=" * 70)

if __name__ == "__main__":
    build_sequence_diagrams()
