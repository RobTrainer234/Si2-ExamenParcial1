import win32com.client
import os
import shutil

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"
OUT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams\sequence"
ARTIFACT_DIR = r"C:\Users\ASUS\.gemini\antigravity\brain\0c84ba0d-3a55-4d70-91ad-2a76b3c98f87\sequence"

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(ARTIFACT_DIR, exist_ok=True)

SEQUENCE_SPECS = [
    # ----------------------------------------------------
    # CU-01
    # ----------------------------------------------------
    {
        "code": "CU-01",
        "diag_name": "sd CU-01 Registrar Empresa Contratante (Tenant)",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu01-registrar-empresa.png",
        "lifeline_bottom": -920,
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
            ("alt", "listar", 0, -90, -205, 150, 1290),
            ("alt", "crear", 0, -250, -525, 150, 1290),
            ("alt", "modificar", 0, -570, -725, 150, 1290),
            ("alt", "desactivar", 0, -770, -885, 150, 1290),
        ],
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "TenantController", "index()"),
            ("TenantController", "E_Tenant", "get()"),
            ("E_Tenant", "TenantController", "return()"),
            # Gap (msg 4)
            ("actor", "TenantController", "create()"),
            # alt crear (msgs 5..11)
            ("TenantController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "TenantController", "return()"),
            ("TenantController", "V.CrearEmpresa", "view()"),
            ("V.CrearEmpresa", "TenantController", "store(datos)"),
            ("TenantController", "E_Tenant", "create(datos)"),
            ("TenantController", "E_Subscription", "create(plan_id)"),
            ("TenantController", "E_Bitacora", "log(accion)"),
            # Gap (msg 12)
            ("actor", "TenantController", "edit(id)"),
            # alt modificar (msgs 13..16)
            ("TenantController", "V.ModificarEmpresa", "view()"),
            ("V.ModificarEmpresa", "TenantController", "update(id, datos)"),
            ("TenantController", "E_Tenant", "update(datos)"),
            ("TenantController", "E_Bitacora", "log(cambio)"),
            # Gap (msg 17)
            ("actor", "TenantController", "patchDesactivar(id)"),
            # alt desactivar (msgs 18..20)
            ("TenantController", "E_Tenant", "updateEstado(SUSPENDIDO)"),
            ("TenantController", "E_Bitacora", "log(suspension)"),
            ("TenantController", "V.EmpresaIndex", "notify(empresaSuspendida)")
        ]
    },

    # ----------------------------------------------------
    # CU-02
    # ----------------------------------------------------
    {
        "code": "CU-02",
        "diag_name": "sd CU-02 Gestionar Planes de Suscripción",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu02-gestionar-planes.png",
        "lifeline_bottom": -720,
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
            ("alt", "listar", 0, -90, -205, 150, 1140),
            ("alt", "crear", 0, -250, -365, 150, 1140),
            ("alt", "modificar", 0, -410, -525, 150, 1140),
            ("alt", "cambiarEstado", 0, -570, -685, 150, 1140)
        ],
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "SubscriptionPlanController", "index()"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "get()"),
            ("E_SubscriptionPlan", "SubscriptionPlanController", "return()"),
            # Gap (msg 4)
            ("actor", "SubscriptionPlanController", "create()"),
            # alt crear (msgs 5..7)
            ("SubscriptionPlanController", "V.CrearPlan", "view()"),
            ("V.CrearPlan", "SubscriptionPlanController", "store(datosPlan)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "create(datosPlan)"),
            # Gap (msg 8)
            ("actor", "SubscriptionPlanController", "edit(id)"),
            # alt modificar (msgs 9..11)
            ("SubscriptionPlanController", "V.EditarPlan", "view()"),
            ("V.EditarPlan", "SubscriptionPlanController", "update(id, limites)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "update(limites)"),
            # Gap (msg 12)
            ("actor", "SubscriptionPlanController", "patchEstado(id, nuevoEstado)"),
            # alt cambiarEstado (msgs 13..15)
            ("SubscriptionPlanController", "E_Subscription", "get(plan_id)"),
            ("SubscriptionPlanController", "E_SubscriptionPlan", "updateEstado(id, nuevoEstado)"),
            ("SubscriptionPlanController", "V.PlanIndex", "notify(estadoActualizado)")
        ]
    },

    # ----------------------------------------------------
    # CU-03
    # ----------------------------------------------------
    {
        "code": "CU-03",
        "diag_name": "sd CU-03 Asignar y Renovar Suscripción de Empresa",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu03-asignar-renovar-suscripcion.png",
        "lifeline_bottom": -840,
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
            ("alt", "consultar", 0, -90, -205, 150, 1290),
            ("alt", "asignarPlan", 0, -250, -445, 150, 1290),
            ("alt", "renovarPlazo", 0, -490, -645, 150, 1290),
            ("alt", "cancelar", 0, -690, -805, 150, 1290)
        ],
        "messages": [
            # alt consultar (msgs 1..3)
            ("actor", "SubscriptionController", "index(empresa_id)"),
            ("SubscriptionController", "E_Subscription", "get()"),
            ("E_Subscription", "SubscriptionController", "return()"),
            # Gap (msg 4)
            ("actor", "SubscriptionController", "create(empresa_id)"),
            # alt asignarPlan (msgs 5..9)
            ("SubscriptionController", "E_SubscriptionPlan", "get()"),
            ("SubscriptionController", "V.AsignarSuscripcion", "view()"),
            ("V.AsignarSuscripcion", "SubscriptionController", "store(plan_id)"),
            ("SubscriptionController", "E_Subscription", "create(plan_id)"),
            ("SubscriptionController", "E_Bitacora", "log(asignacion)"),
            # Gap (msg 10)
            ("actor", "SubscriptionController", "edit(id)"),
            # alt renovarPlazo (msgs 11..14)
            ("SubscriptionController", "V.RenovarPlazo", "view()"),
            ("V.RenovarPlazo", "SubscriptionController", "update(id, dias)"),
            ("SubscriptionController", "E_Subscription", "update(vigencia)"),
            ("SubscriptionController", "E_Bitacora", "log(renovacion)"),
            # Gap (msg 15)
            ("actor", "SubscriptionController", "cancel(id)"),
            # alt cancelar (msgs 16..18)
            ("SubscriptionController", "E_Subscription", "updateEstado(CANCELADA)"),
            ("SubscriptionController", "E_Bitacora", "log(cancelacion)"),
            ("SubscriptionController", "V.SuscripcionIndex", "notify(cancelada)")
        ]
    },

    # ----------------------------------------------------
    # CU-04
    # ----------------------------------------------------
    {
        "code": "CU-04",
        "diag_name": "sd CU-04 Controlar Límites y Restricciones por Plan",
        "actor": "Superadmin SaaS",
        "filename": "secuencia-cu04-controlar-limites-plan.png",
        "lifeline_bottom": -640,
        "lifelines": [
            ("V.PanelLimites", 160, 260),
            ("PlanLimitsController", 300, 420),
            ("E_Tenant", 460, 580),
            ("E_Subscription", 620, 740),
            ("E_SubscriptionPlan", 780, 900),
            ("E_Sucursal", 940, 1060),
            ("E_Usuario", 1100, 1220)
        ],
        "fragments": [
            ("alt", "verificarCuotaSucursales", 0, -90, -245, 150, 1230),
            ("alt", "verificarCuotaUsuarios", 0, -290, -365, 150, 1230),
            ("opt", "limiteAlcanzadoBloqueo", 1, -410, -485, 150, 1230),
            ("opt", "cuotaDisponible", 1, -530, -605, 150, 1230)
        ],
        "messages": [
            # alt verificarCuotaSucursales (msgs 1..4)
            ("actor", "PlanLimitsController", "verify_branches(tenant_id)"),
            ("PlanLimitsController", "E_SubscriptionPlan", "get_limits()"),
            ("PlanLimitsController", "E_Sucursal", "count_active(tenant_id)"),
            ("E_Sucursal", "PlanLimitsController", "return(total_sucursales)"),
            # Gap (msg 5)
            ("actor", "PlanLimitsController", "verify_users(tenant_id)"),
            # alt verificarCuotaUsuarios (msgs 6..7)
            ("PlanLimitsController", "E_Usuario", "count_active(tenant_id)"),
            ("E_Usuario", "PlanLimitsController", "return(total_usuarios)"),
            # Gap (msg 8)
            ("actor", "PlanLimitsController", "request_upgrade()"),
            # opt limiteAlcanzadoBloqueo (msgs 9..10)
            ("PlanLimitsController", "V.PanelLimites", "show_limit_exceeded()"),
            ("PlanLimitsController", "E_Tenant", "log_access(tenant_id)"),
            # Gap (msg 11)
            ("actor", "PlanLimitsController", "confirm_access()"),
            # opt cuotaDisponible (msgs 12..13)
            ("PlanLimitsController", "V.PanelLimites", "allow_operation()"),
            ("PlanLimitsController", "E_Tenant", "log_access(tenant_id)")
        ]
    },

    # ----------------------------------------------------
    # CU-05
    # ----------------------------------------------------
    {
        "code": "CU-05",
        "diag_name": "sd CU-05 Gestionar Sucursales y Empleados por Tenant",
        "actor": "Administrador de Tienda",
        "filename": "secuencia-cu05-gestionar-sucursales-empleados.png",
        "lifeline_bottom": -800,
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
        "fragments": [
            ("alt", "listar", 0, -90, -205, 150, 1290),
            ("alt", "registrarSucursal", 0, -250, -405, 150, 1290),
            ("alt", "asignarEmpleado", 0, -450, -605, 150, 1290),
            ("alt", "desactivar", 0, -650, -765, 150, 1290)
        ],
        "messages": [
            # alt listar (msgs 1..3)
            ("actor", "TenantBranchEmployeeController", "index(tenant_id)"),
            ("TenantBranchEmployeeController", "E_Sucursal", "get(tenant_id)"),
            ("E_Sucursal", "TenantBranchEmployeeController", "return()"),
            # Gap (msg 4)
            ("actor", "TenantBranchEmployeeController", "create_branch()"),
            # alt registrarSucursal (msgs 5..8)
            ("TenantBranchEmployeeController", "V.CrearSucursal", "view()"),
            ("V.CrearSucursal", "TenantBranchEmployeeController", "store_branch(datos)"),
            ("TenantBranchEmployeeController", "E_Sucursal", "create(datos)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(alta_sucursal)"),
            # Gap (msg 9)
            ("actor", "TenantBranchEmployeeController", "assign_employee(user_id, branch_id)"),
            # alt asignarEmpleado (msgs 10..13)
            ("TenantBranchEmployeeController", "V.AsignarEmpleado", "view()"),
            ("V.AsignarEmpleado", "TenantBranchEmployeeController", "store_assignment(datos)"),
            ("TenantBranchEmployeeController", "E_Usuario", "update_branch(user_id, branch_id)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(asignacion)"),
            # Gap (msg 14)
            ("actor", "TenantBranchEmployeeController", "deactivate_branch(id)"),
            # alt desactivar (msgs 15..17)
            ("TenantBranchEmployeeController", "E_Sucursal", "update_status(INACTIVO)"),
            ("TenantBranchEmployeeController", "E_Bitacora", "log(baja_sucursal)"),
            ("TenantBranchEmployeeController", "V.SucursalEmpleadoIndex", "notify(desactivada)")
        ]
    },

    # ----------------------------------------------------
    # CU-06
    # ----------------------------------------------------
    {
        "code": "CU-06",
        "diag_name": "sd CU-06 Descargar y Almacenar Catálogo Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu06-descargar-catalogo-offline.png",
        "lifeline_bottom": -480,
        "lifelines": [
            ("V.DescargaCatalogoIndex", 160, 280),
            ("CatalogSyncController", 330, 470),
            ("E_CatalogoRemoto", 520, 660),
            ("E_CatalogoLocalIndexedDB", 710, 870),
            ("E_BitacoraSync", 920, 1060)
        ],
        "fragments": [
            ("alt", "solicitarDescarga", 0, -90, -205, 150, 1070),
            ("loop", "persistirLotePrendas", 4, -230, -345, 320, 1070),
            ("opt", "finalizarSincronizacion", 1, -370, -445, 150, 1070)
        ],
        "messages": [
            # alt solicitarDescarga (msgs 1..3)
            ("actor", "CatalogSyncController", "request_catalog(tenant_id)"),
            ("CatalogSyncController", "E_CatalogoRemoto", "fetch_delta(version_local)"),
            ("E_CatalogoRemoto", "CatalogSyncController", "return(prendas_json)"),
            # loop persistirLotePrendas (msgs 4..6 - starts from Controller)
            ("CatalogSyncController", "E_CatalogoLocalIndexedDB", "open_transaction()"),
            ("CatalogSyncController", "E_CatalogoLocalIndexedDB", "put_batch(prendas)"),
            ("E_CatalogoLocalIndexedDB", "CatalogSyncController", "ack_batch()"),
            # opt finalizarSincronizacion (msgs 7..8 - starts from Interface)
            ("CatalogSyncController", "E_BitacoraSync", "record_sync(version_nueva)"),
            ("CatalogSyncController", "V.DescargaCatalogoIndex", "notify_sync_completed()")
        ]
    },

    # ----------------------------------------------------
    # CU-07
    # ----------------------------------------------------
    {
        "code": "CU-07",
        "diag_name": "sd CU-07 Consultar Catálogo y Existencias Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu07-consultar-catalogo-existencias.png",
        "lifeline_bottom": -500,
        "lifelines": [
            ("V.CatalogoOfflineIndex", 160, 280),
            ("V.DetallePrendaModal", 310, 440),
            ("OfflineCatalogSearchController", 470, 610),
            ("E_CatalogoLocalIndexedDB", 650, 810),
            ("E_StockOffline", 850, 990)
        ],
        "fragments": [
            ("alt", "buscarPrendas", 0, -90, -205, 150, 1000),
            ("alt", "consultarExistencias", 0, -250, -365, 150, 1000),
            ("opt", "alertarStockBajo", 1, -390, -465, 150, 1000)
        ],
        "messages": [
            # alt buscarPrendas (msgs 1..3)
            ("actor", "OfflineCatalogSearchController", "search_query(termino, filtros)"),
            ("OfflineCatalogSearchController", "E_CatalogoLocalIndexedDB", "query_index(termino)"),
            ("E_CatalogoLocalIndexedDB", "OfflineCatalogSearchController", "return(articulos)"),
            # Gap (msg 4)
            ("actor", "OfflineCatalogSearchController", "select_item(sku)"),
            # alt consultarExistencias (msgs 5..7)
            ("OfflineCatalogSearchController", "E_StockOffline", "get_stock(sku)"),
            ("E_StockOffline", "OfflineCatalogSearchController", "return(existencias)"),
            ("OfflineCatalogSearchController", "V.DetallePrendaModal", "render(detalle, stock)"),
            # opt alertarStockBajo (msgs 8..9)
            ("OfflineCatalogSearchController", "V.DetallePrendaModal", "show_low_stock_warning()"),
            ("OfflineCatalogSearchController", "V.CatalogoOfflineIndex", "highlight_critical(sku)")
        ]
    },

    # ----------------------------------------------------
    # CU-08
    # ----------------------------------------------------
    {
        "code": "CU-08",
        "diag_name": "sd CU-08 Registrar Venta de Contado Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu08-registrar-venta-contado.png",
        "lifeline_bottom": -580,
        "lifelines": [
            ("V.VentaPOSIndex", 160, 260),
            ("V.TicketCobroModal", 290, 410),
            ("OfflinePOSController", 440, 570),
            ("E_StockOffline", 600, 720),
            ("E_VentaLocal", 750, 870),
            ("E_DetalleVentaLocal", 900, 1030),
            ("E_ColaOperacionesSync", 1060, 1200)
        ],
        "fragments": [
            ("alt", "agregarItems", 0, -90, -245, 150, 1210),
            ("alt", "confirmarCobroEfectivo", 0, -290, -445, 150, 1210),
            ("opt", "encolarOperacionSync", 1, -470, -545, 150, 1210)
        ],
        "messages": [
            # alt agregarItems (msgs 1..4)
            ("actor", "OfflinePOSController", "add_item(sku, cant)"),
            ("OfflinePOSController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflinePOSController", "return(disponible)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "update_total()"),
            # Gap (msg 5)
            ("actor", "OfflinePOSController", "confirm_sale(datosCobro)"),
            # alt confirmarCobroEfectivo (msgs 6..9)
            ("OfflinePOSController", "E_VentaLocal", "create(venta)"),
            ("OfflinePOSController", "E_DetalleVentaLocal", "create(detalles)"),
            ("OfflinePOSController", "E_StockOffline", "deduct_stock(cant)"),
            ("OfflinePOSController", "V.TicketCobroModal", "view_receipt()"),
            # opt encolarOperacionSync (msgs 10..11)
            ("OfflinePOSController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflinePOSController", "V.VentaPOSIndex", "notify_queued()")
        ]
    },

    # ----------------------------------------------------
    # CU-09
    # ----------------------------------------------------
    {
        "code": "CU-09",
        "diag_name": "sd CU-09 Registrar Reserva de Prendas Offline",
        "actor": "Vendedor",
        "filename": "secuencia-cu09-registrar-reserva-prendas.png",
        "lifeline_bottom": -540,
        "lifelines": [
            ("V.ReservaPOSIndex", 160, 270),
            ("V.TicketApartadoModal", 300, 420),
            ("OfflineReservationController", 450, 580),
            ("E_StockOffline", 610, 730),
            ("E_ReservaLocal", 760, 880),
            ("E_DetalleReservaLocal", 910, 1040),
            ("E_ColaOperacionesSync", 1070, 1210)
        ],
        "fragments": [
            ("alt", "seleccionarPrenda", 0, -90, -205, 150, 1220),
            ("alt", "confirmarApartado", 0, -250, -405, 150, 1220),
            ("opt", "encolarSyncReserva", 1, -430, -505, 150, 1220)
        ],
        "messages": [
            # alt seleccionarPrenda (msgs 1..3)
            ("actor", "OfflineReservationController", "select_item(sku)"),
            ("OfflineReservationController", "E_StockOffline", "get_available()"),
            ("E_StockOffline", "OfflineReservationController", "return()"),
            # Gap (msg 4)
            ("actor", "OfflineReservationController", "confirm_reservation(datosCliente)"),
            # alt confirmarApartado (msgs 5..8)
            ("OfflineReservationController", "E_ReservaLocal", "create(reserva)"),
            ("OfflineReservationController", "E_DetalleReservaLocal", "create(detalles)"),
            ("OfflineReservationController", "E_StockOffline", "lock_stock(cant)"),
            ("OfflineReservationController", "V.TicketApartadoModal", "view()"),
            # opt encolarSyncReserva (msgs 9..10)
            ("OfflineReservationController", "E_ColaOperacionesSync", "enqueue(uuid, payload)"),
            ("OfflineReservationController", "V.ReservaPOSIndex", "notify_queued()")
        ]
    },

    # ----------------------------------------------------
    # CU-23
    # ----------------------------------------------------
    {
        "code": "CU-23",
        "diag_name": "sd CU-23 Notificar Estado de Conectividad (Semáforo)",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu23-notificar-estado-conectividad.png",
        "lifeline_bottom": -560,
        "lifelines": [
            ("V.SemaforoBarraIndex", 160, 280),
            ("V.BannerAlertaModal", 310, 440),
            ("NetworkMonitorController", 470, 610),
            ("E_ConfiguracionRed", 640, 770),
            ("E_EstadoConectividad", 800, 930),
            ("E_ColaOperacionesSync", 960, 1100)
        ],
        "fragments": [
            ("alt", "monitorearEnlace", 0, -90, -245, 150, 1110),
            ("alt", "conmutarEstado", 0, -270, -425, 150, 1110),
            ("opt", "alertaDesconexion", 1, -450, -525, 150, 1110)
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
        ]
    },

    # ----------------------------------------------------
    # CU-24
    # ----------------------------------------------------
    {
        "code": "CU-24",
        "diag_name": "sd CU-24 Instalar y Registrar Service Worker (PWA)",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu24-instalar-service-worker.png",
        "lifeline_bottom": -480,
        "lifelines": [
            ("V.InstaladorIndex", 160, 270),
            ("V.PromptModal", 300, 410),
            ("ServiceWorkerController", 440, 580),
            ("E_ManifiestoPWA", 610, 740),
            ("E_CacheAplicacion", 770, 900),
            ("E_RegistroServiceWorker", 930, 1080)
        ],
        "fragments": [
            ("alt", "solicitarInstalacion", 0, -90, -245, 150, 1090),
            ("loop", "cachearRecursosEstaticos", 4, -270, -345, 430, 1090),
            ("opt", "activarModoOffline", 1, -370, -445, 150, 1090)
        ],
        "messages": [
            # alt solicitarInstalacion (msgs 1..4)
            ("actor", "ServiceWorkerController", "trigger_install_prompt()"),
            ("ServiceWorkerController", "E_ManifiestoPWA", "validate()"),
            ("E_ManifiestoPWA", "ServiceWorkerController", "return(valid)"),
            ("ServiceWorkerController", "V.PromptModal", "view()"),
            # loop cachearRecursosEstaticos (msgs 5..6 - starts from Controller)
            ("ServiceWorkerController", "E_CacheAplicacion", "store_asset(url)"),
            ("ServiceWorkerController", "E_RegistroServiceWorker", "update_scope()"),
            # opt activarModoOffline (msgs 7..8)
            ("ServiceWorkerController", "E_RegistroServiceWorker", "activate()"),
            ("ServiceWorkerController", "V.InstaladorIndex", "notify_offline_ready()")
        ]
    },

    # ----------------------------------------------------
    # CU-25
    # ----------------------------------------------------
    {
        "code": "CU-25",
        "diag_name": "sd CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "actor": "Personal de Tienda",
        "filename": "secuencia-cu25-configurar-sqlite-movil.png",
        "lifeline_bottom": -440,
        "lifelines": [
            ("V.SQLiteConfigIndex", 160, 280),
            ("DatabaseMigrationController", 320, 470),
            ("E_BaseDatosSQLite", 510, 640),
            ("E_TablaLocal", 680, 800),
            ("E_HistorialMigracion", 840, 970)
        ],
        "fragments": [
            ("alt", "verificarEsquema", 0, -90, -205, 150, 980),
            ("loop", "ejecutarScriptsDDL", 4, -230, -305, 310, 980),
            ("opt", "validarIntegridad", 1, -330, -405, 150, 980)
        ],
        "messages": [
            # alt verificarEsquema (msgs 1..3)
            ("actor", "DatabaseMigrationController", "check_version()"),
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "get_user_version()"),
            ("E_BaseDatosSQLite", "DatabaseMigrationController", "return(version)"),
            # loop ejecutarScriptsDDL (msgs 4..5 - starts from Controller)
            ("DatabaseMigrationController", "E_TablaLocal", "execute_ddl(sql)"),
            ("DatabaseMigrationController", "E_HistorialMigracion", "record_migration(v)"),
            # opt validarIntegridad (msgs 6..7)
            ("DatabaseMigrationController", "E_BaseDatosSQLite", "pragma_integrity_check()"),
            ("DatabaseMigrationController", "V.SQLiteConfigIndex", "notify_ready()")
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
        print("Paquete no encontrado.")
        return

    print(f"Paquete encontrado: {seq_pkg.Name} (ID: {seq_pkg.PackageID})")

    for spec in SEQUENCE_SPECS:
        code = spec["code"]
        diag_title = spec["diag_name"]
        print(f"\nProcesando: {code} - {diag_title}...")

        # 1. Eliminar diagrama previo si existe
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
        ll_bot = spec["lifeline_bottom"]

        # 3. Actor (Lifeline rectangular tipo Actor a la izquierda)
        el_act = seq_pkg.Elements.AddNew(spec["actor"], "Actor")
        el_act.Update()
        created_elements["actor"] = el_act
        o_act = diag.DiagramObjects.AddNew(f"l=40;r=110;t=-40;b={ll_bot};", "")
        o_act.ElementID = el_act.ElementID
        o_act.left = 40
        o_act.right = 110
        o_act.top = -40
        o_act.bottom = ll_bot
        o_act.Update()

        # 4. Lifelines (Todas rectangulares con longitud ajustada al final del caso de uso)
        for lf_name, left, right in spec["lifelines"]:
            el_lf = seq_pkg.Elements.AddNew(lf_name, "Sequence")
            el_lf.Update()
            created_elements[lf_name] = el_lf

            o_lf = diag.DiagramObjects.AddNew(f"l={left};r={right};t=-40;b={ll_bot};", "")
            o_lf.ElementID = el_lf.ElementID
            o_lf.left = left
            o_lf.right = right
            o_lf.top = -40
            o_lf.bottom = ll_bot
            o_lf.Update()

        # 5. Fragmentos (Con separación limpia, cero solapamiento, pestañas intactas y 100% poblados)
        for f_type, f_name, subtype_val, top, bot, left, right in spec["fragments"]:
            f_el = seq_pkg.Elements.AddNew(f_name, "InteractionFragment")
            f_el.Subtype = subtype_val
            f_el.Update()

            o_f = diag.DiagramObjects.AddNew(f"l={left};r={right};t={top};b={bot};", "")
            o_f.ElementID = f_el.ElementID
            o_f.left = left
            o_f.right = right
            o_f.top = top
            o_f.bottom = bot
            o_f.Update()

        # 6. Mensajes en secuencia exacta
        for seq_idx, (src_key, dst_key, msg_name) in enumerate(spec["messages"], start=1):
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

        # 7. Exportar imagen a docs y carpeta de artefactos
        png_path = os.path.join(OUT_DIR, spec["filename"])
        art_path = os.path.join(ARTIFACT_DIR, spec["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, png_path, 1)
        shutil.copy2(png_path, art_path)
        print(f"   [OK] Exportado: {png_path} ({os.path.getsize(png_path)} bytes)")

    seq_pkg.Diagrams.Refresh()
    seq_pkg.Elements.Refresh()
    repo.CloseFile()
    del repo
    del ea
    print("\n¡Todos los 12 diagramas de secuencia han sido reconstruidos y exportados con éxito!")

if __name__ == "__main__":
    main()
