import win32com.client
import os
import shutil

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\sequence"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87\sequence"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

# 12 Casos de Uso con Mensajes Asignados y Coordenadas Dinámicas por Fragmento
SEQUENCE_DATA_FIXED = [
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
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "TenantController", "index()"),
            ("TenantController", "E_Tenant", "get()"),
            ("E_Tenant", "TenantController", "return()"),
            # alt crear (msgs 4..11)
            ("actor", "TenantController", "create()"),
            ("TenantController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "TenantController", "return()"),
            ("TenantController", "V.CrearEmpresa", "view()"),
            ("V.CrearEmpresa", "TenantController", "store(datos)"),
            ("TenantController", "E_Tenant", "create(datos)"),
            ("TenantController", "E_Subscription", "create(plan_id)"),
            ("TenantController", "E_Bitacora", "log(accion)"),
            # alt modificar (msgs 12..16)
            ("actor", "TenantController", "edit(id)"),
            ("TenantController", "V.ModificarEmpresa", "view()"),
            ("V.ModificarEmpresa", "TenantController", "update(id, datos)"),
            ("TenantController", "E_Tenant", "update(datos)"),
            ("TenantController", "E_Bitacora", "log(cambio)"),
            # alt desactivar (msgs 17..20)
            ("actor", "TenantController", "patchDesactivar(id)"),
            ("TenantController", "E_Tenant", "updateEstado(SUSPENDIDO)"),
            ("TenantController", "E_Bitacora", "log(suspension)"),
            ("TenantController", "V.EmpresaIndex", "notify(empresaSuspendida)")
        ],
        "fragments_def": [
            ("alt", "listar", 0, 1, 3, 150, 1290),
            ("alt", "crear", 0, 4, 11, 150, 1290),
            ("alt", "modificar", 0, 12, 16, 150, 1290),
            ("alt", "desactivar", 0, 17, 20, 150, 1290),
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
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "SubscriptionPlanController", "index()"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "SubscriptionPlanController", "return()"),
            # alt crear (msgs 4..7)
            ("actor", "SubscriptionPlanController", "create()"),
            ("SubscriptionPlanController", "V.CrearPlan", "view()"),
            ("V.CrearPlan", "SubscriptionPlanController", "store(datosPlan)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "create(datosPlan)"),
            # alt modificar (msgs 8..11)
            ("actor", "SubscriptionPlanController", "edit(id)"),
            ("SubscriptionPlanController", "V.EditarPlan", "view()"),
            ("V.EditarPlan", "SubscriptionPlanController", "update(id, limites)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "update(limites)"),
            # alt cambiarEstado (msgs 12..15)
            ("actor", "SubscriptionPlanController", "patchEstado(id, nuevoEstado)"),
            ("SubscriptionPlanController", "E_Subscription", "get(plan_id)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "updateEstado(id, nuevoEstado)"),
            ("SubscriptionPlanController", "V.PlanIndex", "notify(estadoActualizado)")
        ],
        "fragments_def": [
            ("alt", "listar", 0, 1, 3, 150, 1140),
            ("alt", "crear", 0, 4, 7, 150, 1140),
            ("alt", "modificar", 0, 8, 11, 150, 1140),
            ("alt", "cambiarEstado", 0, 12, 15, 150, 1140),
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
        "messages": [
            # alt consultar (msgs 1..3)
            ("actor", "SubscriptionController", "index(empresa_id)"),
            ("SubscriptionController", "E_Subscription", "get()"),
            ("E_Subscription", "SubscriptionController", "return()"),
            # alt asignarPlan (msgs 4..9)
            ("actor", "SubscriptionController", "create(empresa_id)"),
            ("SubscriptionController", "E_SubscriptionPlan", "get()"),
            ("SubscriptionController", "V.AsignarSuscripcion", "view()"),
            ("V.AsignarSuscripcion", "SubscriptionController", "store(plan_id)"),
            ("SubscriptionController", "E_Subscription", "create(plan_id)"),
            ("SubscriptionController", "E_Bitacora", "log(asignacion)"),
            # alt renovarPlazo (msgs 10..14)
            ("actor", "SubscriptionController", "edit(id)"),
            ("SubscriptionController", "V.RenovarPlazo", "view()"),
            ("V.RenovarPlazo", "SubscriptionController", "update(id, dias)"),
            ("SubscriptionController", "E_Subscription", "update(vigencia)"),
            ("SubscriptionController", "E_Bitacora", "log(renovacion)"),
            # alt cancelar (msgs 15..18)
            ("actor", "SubscriptionController", "cancel(id)"),
            ("SubscriptionController", "E_Subscription", "updateEstado(CANCELADA)"),
            ("SubscriptionController", "E_Bitacora", "log(cancelacion)"),
            ("SubscriptionController", "V.SuscripcionIndex", "notify(cancelada)")
        ],
        "fragments_def": [
            ("alt", "consultar", 0, 1, 3, 150, 1290),
            ("alt", "asignarPlan", 0, 4, 9, 150, 1290),
            ("alt", "renovarPlazo", 0, 10, 14, 150, 1290),
            ("alt", "cancelar", 0, 15, 18, 150, 1290),
        ]
    },
    {
        "code": "CU-04",
        "diag_name": "sd CU-04 Controlar Límites y Restricciones por Plan",
        "title": "CU-04 Controlar Límites y Restricciones por Plan",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu04-controlar-limites-plan.png",
        "lifelines": [
            ("V.PanelLimites", 160, 260),
            ("PlanLimitsController", 300, 420),
            ("E_Tenant", 460, 580),
            ("E_Subscription", 620, 740),
            ("E_SubscriptionPlan", 780, 900),
            ("E_Sucursal", 940, 1060),
            ("E_Usuario", 1100, 1220)
        ],
        "messages": [
            # alt verificarCuotaSucursales (msgs 1..4)
            ("actor", "PlanLimitsController", "verify_branches(tenant_id)"),
            ("PlanLimitsController", "E_SubscriptionPlan", "get_limits()"),
            ("PlanLimitsController", "E_Sucursal", "count_active(tenant_id)"),
            ("E_Sucursal", "PlanLimitsController", "return(total_sucursales)"),
            # alt verificarCuotaUsuarios (msgs 5..7)
            ("actor", "PlanLimitsController", "verify_users(tenant_id)"),
            ("PlanLimitsController", "E_Usuario", "count_active(tenant_id)"),
            ("E_Usuario", "PlanLimitsController", "return(total_usuarios)"),
            # opt limiteAlcanzadoBloqueo (msgs 8..9)
            ("PlanLimitsController", "V.PanelLimites", "show_limit_exceeded()"),
            ("actor", "PlanLimitsController", "request_upgrade()"),
            # opt cuotaDisponible (msgs 10..11)
            ("PlanLimitsController", "V.PanelLimites", "allow_operation()"),
            ("PlanLimitsController", "E_Tenant", "log_access(tenant_id)")
        ],
        "fragments_def": [
            ("alt", "verificarCuotaSucursales", 0, 1, 4, 150, 1230),
            ("alt", "verificarCuotaUsuarios", 0, 5, 7, 150, 1230),
            ("opt", "limiteAlcanzadoBloqueo", 1, 8, 9, 150, 1230),
            ("opt", "cuotaDisponible", 1, 10, 11, 150, 1230),
        ]
    },
    {
        "code": "CU-05",
        "diag_name": "sd CU-05 Gestionar Sucursales y Empleados por Tenant",
        "title": "CU-05 Gestionar Sucursales y Empleados por Tenant",
        "actor": "Administrador de Tienda",
        "filename": "secuencia-cu05-gestionar-sucursales-empleados.png",
        "lifelines": [
            ("V.SucursalEmpleadoIndex", 160, 280),
            ("V.CrearSucursal", 310, 420),
            ("V.AsignarEmpleado", 450, 560),
            ("TenantBranchEmployeeController", 590, 720),
            ("E_Tenant", 750, 860),
            ("E_Sucursal", 890, 1000),
            ("E_Usuario", 1030, 1140),
            ("E_Bitacora", 1170, 1280)
        ],
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "TenantBranchEmployeeController", "index(tenant_id)"),
            ("TenantBranchEmployeeController", "E_Sucursal", "get(tenant_id)"),
            ("E_Sucursal", "TenantBranchEmployeeController", "return()"),
            # alt registrarSucursal (msgs 4..8)
            ("actor", "TenantBranchEmployeeController", "create_branch()"),
            ("TenantBranchEmployeeController", "V.CrearSucursal", "view()"),
            ("V.CrearSucursal", "TenantBranchEmployeeController", "store_branch(datos)"),
            ("TenantBranchEmployeeController", "E_Sucursal", "create(datos)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(alta_sucursal)"),
            # alt asignarEmpleado (msgs 9..13)
            ("actor", "TenantBranchEmployeeController", "assign_employee(user_id, branch_id)"),
            ("TenantBranchEmployeeController", "V.AsignarEmpleado", "view()"),
            ("V.AsignarEmpleado", "TenantBranchEmployeeController", "store_assignment(datos)"),
            ("TenantBranchEmployeeController", "E_Usuario", "update_branch(user_id, branch_id)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(asignacion)"),
            # alt desactivar (msgs 14..17)
            ("actor", "TenantBranchEmployeeController", "deactivate_branch(id)"),
            ("TenantBranchEmployeeController", "E_Sucursal", "update_status(INACTIVO)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(baja_sucursal)"),
            ("TenantBranchEmployeeController", "V.SucursalEmpleadoIndex", "notify(desactivada)")
        ],
        "fragments_def": [
            ("alt", "listar", 0, 1, 3, 150, 1290),
            ("alt", "registrarSucursal", 0, 4, 8, 150, 1290),
            ("alt", "asignarEmpleado", 0, 9, 13, 150, 1290),
            ("alt", "desactivar", 0, 14, 17, 150, 1290),
        ]
    },
    {
        "code": "CU-06",
        "diag_name": "sd CU-06 Descargar y Almacenar Catálogo Offline",
        "title": "CU-06 Descargar y Almacenar Catálogo Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu06-descargar-catalogo-offline.png",
        "lifelines": [
            ("V.DescargaCatalogoIndex", 160, 280),
            ("CatalogSyncController", 330, 470),
            ("E_CatalogoRemoto", 520, 660),
            ("E_CatalogoLocalIndexedDB", 710, 870),
            ("E_BitacoraSync", 920, 1060)
        ],
        "messages": [
            # alt solicitarDescarga (msgs 1..3)
            ("actor", "CatalogSyncController", "request_catalog(tenant_id)"),
            ("CatalogSyncController", "E_CatalogoRemoto", "fetch_delta(version_local)"),
            ("E_CatalogoRemoto", "CatalogSyncController", "return(prendas_json)"),
            # loop persistirLotePrendas (msgs 4..6 - starts from controller)
            ("CatalogSyncController", "E_CatalogoLocalIndexedDB", "open_transaction()"),
            ("CatalogSyncController", "E_CatalogoLocalIndexedDB", "put_batch(prendas)"),
            ("E_CatalogoLocalIndexedDB", "CatalogSyncController", "ack_batch()"),
            # opt finalizarSincronizacion (msgs 7..8)
            ("CatalogSyncController", "E_BitacoraSync", "record_sync(version_nueva)"),
            ("CatalogSyncController", "V.DescargaCatalogoIndex", "notify_sync_completed()")
        ],
        "fragments_def": [
            ("alt", "solicitarDescarga", 0, 1, 3, 150, 1070),
            ("loop", "persistirLotePrendas", 4, 4, 6, 320, 1070),
            ("opt", "finalizarSincronizacion", 1, 7, 8, 150, 1070),
        ]
    },
    {
        "code": "CU-07",
        "diag_name": "sd CU-07 Consultar Catálogo y Existencias Offline",
        "title": "CU-07 Consultar Catálogo y Existencias Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu07-consultar-catalogo-existencias.png",
        "lifelines": [
            ("V.CatalogoOfflineIndex", 160, 280),
            ("V.DetallePrendaModal", 310, 440),
            ("OfflineCatalogSearchController", 470, 610),
            ("E_CatalogoLocalIndexedDB", 650, 810),
            ("E_StockOffline", 850, 990)
        ],
        "messages": [
            # alt buscarPrendas (msgs 1..3)
            ("actor", "OfflineCatalogSearchController", "search_query(termino, filtros)"),
            ("OfflineCatalogSearchController", "E_CatalogoLocalIndexedDB", "query_index(termino)"),
            ("E_CatalogoLocalIndexedDB", "OfflineCatalogSearchController", "return(articulos)"),
            # alt consultarExistencias (msgs 4..7)
            ("actor", "OfflineCatalogSearchController", "select_item(sku)"),
            ("OfflineCatalogSearchController", "E_StockOffline", "get_stock(sku)"),
            ("E_StockOffline", "OfflineCatalogSearchController", "return(existencias)"),
            ("OfflineCatalogSearchController", "V.DetallePrendaModal", "render(detalle, stock)"),
            # opt alertarStockBajo (msgs 8..9)
            ("OfflineCatalogSearchController", "V.DetallePrendaModal", "show_low_stock_warning()"),
            ("OfflineCatalogSearchController", "V.CatalogoOfflineIndex", "highlight_critical(sku)")
        ],
        "fragments_def": [
            ("alt", "buscarPrendas", 0, 1, 3, 150, 1000),
            ("alt", "consultarExistencias", 0, 4, 7, 150, 1000),
            ("opt", "alertarStockBajo", 1, 8, 9, 150, 1000),
        ]
    },
    {
        "code": "CU-08",
        "diag_name": "sd CU-08 Registrar Venta de Contado Offline",
        "title": "CU-08 Registrar Venta de Contado Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu08-registrar-venta-contado.png",
        "lifelines": [
            ("V.VentaPOSIndex", 160, 260),
            ("V.TicketCobroModal", 290, 410),
            ("OfflinePOSController", 440, 570),
            ("E_StockOffline", 600, 720),
            ("E_VentaLocal", 750, 870),
            ("E_DetalleVentaLocal", 900, 1030),
            ("E_ColaOperacionesSync", 1060, 1200)
        ],
        "messages": [
            # alt agregarItems (msgs 1..4)
            ("actor", "OfflinePOSController", "add_item(sku, cant)"),
            ("OfflinePOSController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflinePOSController", "return(disponible)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "update_total()"),
            # alt confirmarCobroEfectivo (msgs 5..9)
            ("actor", "OfflinePOSController", "confirm_sale(datosCobro)"),
            ("OfflinePOSController", "E_VentaLocal", "create(venta)"),
            ("OfflinePOSController", "E_DetalleVentaLocal", "create(detalles)"),
            ("OfflinePOSController", "E_StockOffline", "deduct_stock(cant)"),
            ("OfflinePOSController", "V.TicketCobroModal", "view_receipt()"),
            # opt encolarOperacionSync (msgs 10..11)
            ("OfflinePOSController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "notify_queued()")
        ],
        "fragments_def": [
            ("alt", "agregarItems", 0, 1, 4, 150, 1210),
            ("alt", "confirmarCobroEfectivo", 0, 5, 9, 150, 1210),
            ("opt", "encolarOperacionSync", 1, 10, 11, 150, 1210),
        ]
    },
    {
        "code": "CU-09",
        "diag_name": "sd CU-09 Registrar Reserva de Prendas Offline",
        "title": "CU-09 Registrar Reserva de Prendas Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu09-registrar-reserva-prendas.png",
        "lifelines": [
            ("V.ReservaPOSIndex", 160, 270),
            ("V.TicketApartadoModal", 300, 420),
            ("OfflineReservationController", 450, 580),
            ("E_StockOffline", 610, 730),
            ("E_ReservaLocal", 760, 880),
            ("E_DetalleReservaLocal", 910, 1040),
            ("E_ColaOperacionesSync", 1070, 1210)
        ],
        "messages": [
            # alt seleccionarPrenda (msgs 1..3)
            ("actor", "OfflineReservationController", "select_item(sku)"),
            ("OfflineReservationController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflineReservationController", "return()"),
            # alt confirmarApartado (msgs 4..8)
            ("actor", "OfflineReservationController", "confirm_reservation(datosCliente)"),
            ("OfflineReservationController", "E_ReservaLocal", "create(reserva)"),
            ("OfflineReservationController", "E_DetalleReservaLocal", "create(detalles)"),
            ("OfflineReservationController", "E_StockOffline", "lock_stock(cant)"),
            ("OfflineReservationController", "V.TicketApartadoModal", "view()"),
            # opt encolarSyncReserva (msgs 9..10)
            ("OfflineReservationController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflineReservationController", "V.ReservaPOSIndex", "notify_queued()")
        ],
        "fragments_def": [
            ("alt", "seleccionarPrenda", 0, 1, 3, 150, 1220),
            ("alt", "confirmarApartado", 0, 4, 8, 150, 1220),
            ("opt", "encolarSyncReserva", 1, 9, 10, 150, 1220),
        ]
    },
    {
        "code": "CU-23",
        "diag_name": "sd CU-23 Notificar Estado de Conectividad (Semáforo)",
        "title": "CU-23 Notificar Estado de Conectividad (Semáforo)",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu23-notificar-estado-conectividad.png",
        "lifelines": [
            ("V.SemaforoBarraIndex", 160, 280),
            ("V.BannerAlertaModal", 310, 440),
            ("NetworkMonitorController", 470, 610),
            ("E_ConfiguracionRed", 640, 770),
            ("E_EstadoConectividad", 800, 930),
            ("E_ColaOperacionesSync", 960, 1100)
        ],
        "messages": [
            # alt monitorearEnlace (msgs 1..4)
            ("actor", "NetworkMonitorController", "poll_status()"),
            ("NetworkMonitorController", "E_ConfiguracionRed", "get_healthcheck_url()"),
            ("NetworkMonitorController", "E_EstadoConectividad", "get_current()"),
            ("E_EstadoConectividad", "NetworkMonitorController", "return()"),
            # alt conmutarEstado (msgs 5..8)
            ("NetworkMonitorController", "E_EstadoConectividad", "update(online_status)"),
            ("NetworkMonitorController", "E_ColaOperacionesSync", "count_pending()"),
            ("E_ColaOperacionesSync", "NetworkMonitorController", "return(total_pendientes)"),
            ("NetworkMonitorController", "V.SemaforoBarraIndex", "update_badge(color, total)"),
            # opt alertaDesconexion (msgs 9..10)
            ("NetworkMonitorController", "V.BannerAlertaModal", "show_offline_warning()"),
            ("NetworkMonitorController", "V.SemaforoBarraIndex", "set_indicator(ROJO)")
        ],
        "fragments_def": [
            ("alt", "monitorearEnlace", 0, 1, 4, 150, 1110),
            ("alt", "conmutarEstado", 0, 5, 8, 150, 1110),
            ("opt", "alertaDesconexion", 1, 9, 10, 150, 1110),
        ]
    },
    {
        "code": "CU-24",
        "diag_name": "sd CU-24 Instalar y Registrar Service Worker (PWA)",
        "title": "CU-24 Instalar y Registrar Service Worker (PWA)",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu24-instalar-service-worker.png",
        "lifelines": [
            ("V.InstaladorIndex", 160, 270),
            ("V.PromptModal", 300, 410),
            ("ServiceWorkerController", 440, 580),
            ("E_ManifiestoPWA", 610, 740),
            ("E_CacheAplicacion", 770, 900),
            ("E_RegistroServiceWorker", 930, 1080)
        ],
        "messages": [
            # alt solicitarInstalacion (msgs 1..4)
            ("actor", "ServiceWorkerController", "trigger_install_prompt()"),
            ("ServiceWorkerController", "E_ManifiestoPWA", "validate()"),
            ("E_ManifiestoPWA", "ServiceWorkerController", "return(valid)"),
            ("ServiceWorkerController", "V.PromptModal", "view()"),
            # loop cachearRecursosEstaticos (msgs 5..6 - starts from controller)
            ("ServiceWorkerController", "E_CacheAplicacion", "store_asset(url)"),
            ("ServiceWorkerController", "E_RegistroServiceWorker", "update_scope()"),
            # opt activarModoOffline (msgs 7..8)
            ("ServiceWorkerController", "E_RegistroServiceWorker", "activate()"),
            ("ServiceWorkerController", "V.InstaladorIndex", "notify_offline_ready()")
        ],
        "fragments_def": [
            ("alt", "solicitarInstalacion", 0, 1, 4, 150, 1090),
            ("loop", "cachearRecursosEstaticos", 4, 5, 6, 430, 1090),
            ("opt", "activarModoOffline", 1, 7, 8, 150, 1090),
        ]
    },
    {
        "code": "CU-25",
        "diag_name": "sd CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "title": "CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu25-configurar-sqlite-movil.png",
        "lifelines": [
            ("V.SQLiteConfigIndex", 160, 280),
            ("DatabaseMigrationController", 320, 470),
            ("E_BaseDatosSQLite", 510, 640),
            ("E_TablaLocal", 680, 800),
            ("E_HistorialMigracion", 840, 970)
        ],
        "messages": [
            # alt verificarEsquema (msgs 1..3)
            ("actor", "DatabaseMigrationController", "check_version()"),
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "get_user_version()"),
            ("E_BaseDatosSQLite", "DatabaseMigrationController", "return(version)"),
            # loop ejecutarScriptsDDL (msgs 4..5 - starts from controller)
            ("DatabaseMigrationController", "E_TablaLocal", "execute_ddl(sql)"),
            ("DatabaseMigrationController", "E_HistorialMigracion", "record_migration(v)"),
            # opt validarIntegridad (msgs 6..7)
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "pragma_integrity_check()"),
            ("DatabaseMigrationController", "V.SQLiteConfigIndex", "notify_ready()")
        ],
        "fragments_def": [
            ("alt", "verificarEsquema", 0, 1, 3, 150, 980),
            ("loop", "ejecutarScriptsDDL", 4, 4, 5, 310, 980),
            ("opt", "validarIntegridad", 1, 6, 7, 150, 980),
        ]
    }
]

def main():
    print("Iniciando conexión con Enterprise Architect...")
    ea = win32com.client.Dispatch("EA.App")
    repo = ea.Repository
    if not repo.OpenFile(EAP_PATH):
        print(f"Error abriendo {EAP_PATH}")
        return

    project = repo.GetProjectInterface()
    root_model = repo.Models.GetAt(0)

    # Buscar paquete 'Segundo Parcial - Diagramas de Secuencia (Etapa 1)'
    seq_pkg = None
    for p in root_model.Packages:
        if p.Name == "Segundo Parcial - Diagramas de Secuencia (Etapa 1)":
            seq_pkg = p
            break

    if not seq_pkg:
        print("Paquete de Secuencia no encontrado.")
        return

    print(f"Paquete encontrado: {seq_pkg.Name}")

    # Paso de mensaje en EA: constante ~45 px
    MSG_PITCH = 45
    BASE_TOP = -75

    for cu in SEQUENCE_DATA_FIXED:
        diag_title = cu["diag_name"]
        print(f"\nProcesando: {cu['code']} - {diag_title}...")

        # 1. Eliminar diagrama viejo si existe
        for i in range(seq_pkg.Diagrams.Count):
            d = seq_pkg.Diagrams.GetAt(i)
            if d.Name == diag_title:
                seq_pkg.Diagrams.Delete(i)
                break
        seq_pkg.Diagrams.Refresh()

        # 2. Crear diagrama nuevo
        diag = seq_pkg.Diagrams.AddNew(diag_title, "Sequence")
        diag.Update()
        seq_pkg.Diagrams.Refresh()

        created_elements = {}

        # 3. Actor (Lifeline rectangular)
        el_act = seq_pkg.Elements.AddNew(cu["actor"], "Actor")
        el_act.Update()
        created_elements["actor"] = el_act
        o_act = diag.DiagramObjects.AddNew("l=40;r=110;t=-40;b=-1100;", "")
        o_act.ElementID = el_act.ElementID
        o_act.Update()

        # 4. Lifelines (Todas rectangulares)
        for lf_name, left, right in cu["lifelines"]:
            el_lf = seq_pkg.Elements.AddNew(lf_name, "Sequence")
            el_lf.Update()
            created_elements[lf_name] = el_lf

            o_lf = diag.DiagramObjects.AddNew(f"l={left};r={right};t=-40;b=-1100;", "")
            o_lf.ElementID = el_lf.ElementID
            o_lf.Update()

        # 5. Fragmentos Calculados Dinámicamente para que NUNCA estén vacíos
        for f_type, f_name, subtype_val, start_m, end_m, fl, fr in cu["fragments_def"]:
            # top justo antes del primer mensaje del fragmento
            ft = BASE_TOP - ((start_m - 1) * MSG_PITCH) - 5
            # bottom justo después del último mensaje del fragmento
            fb = BASE_TOP - (end_m * MSG_PITCH) - 15

            f_el = seq_pkg.Elements.AddNew(f_name, "InteractionFragment")
            f_el.Subtype = subtype_val
            f_el.Update()

            o_f = diag.DiagramObjects.AddNew(f"l={fl};r={fr};t={ft};b={fb};", "")
            o_f.ElementID = f_el.ElementID
            o_f.Update()
            print(f"   -> Fragmento [{f_type}] '{f_name}': msgs {start_m}..{end_m} | top={ft}, bot={fb}")

        # 6. Mensajes de Secuencia
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
        repo.SaveDiagram(diag.DiagramID)

        # 7. Exportar imagen
        png_path = os.path.join(OUT_DIR, cu["filename"])
        art_path = os.path.join(ARTIFACT_DIR, cu["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, png_path, 1)
        shutil.copy2(png_path, art_path)
        print(f"   [OK] Exportado: {png_path} ({os.path.getsize(png_path)} bytes)")

    seq_pkg.Diagrams.Refresh()
    seq_pkg.Elements.Refresh()
    repo.CloseFile()
    del repo
    del ea
    print("\n¡Todos los diagramas de secuencia corregidos y actualizados al 100%!")

if __name__ == "__main__":
    main()
