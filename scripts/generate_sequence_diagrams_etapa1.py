import win32com.client
import os
import sys

def main():
    print("Iniciando generación y pulido final de Diagramas de Secuencia (Etapa 1)...")
    ea = win32com.client.Dispatch('EA.App')
    repo = ea.Repository
    if not repo.ConnectionString:
        repo.OpenFile(r'C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap')

    pkg193 = repo.GetPackageByID(193)
    out_dir = r'C:\Users\ASUS\.gemini\antigravity\brain\978138ae-9c86-4368-913c-8caecc04e1e6\secuencia_etapa1'
    os.makedirs(out_dir, exist_ok=True)
    project = repo.GetProjectInterface()

    # WIPE existing diagrams and elements in Package 193 cleanly
    print("Limpiando paquete 193...")
    for i in range(pkg193.Diagrams.Count - 1, -1, -1):
        pkg193.Diagrams.Delete(i)
    pkg193.Diagrams.Refresh()

    for i in range(pkg193.Elements.Count - 1, -1, -1):
        pkg193.Elements.Delete(i)
    pkg193.Elements.Refresh()

    cu_definitions = [
        {
            "code": "CU-01",
            "title": "sd CU-01 Registrar Empresa Contratante (Tenant)",
            "actor": "Superadmin SaaS",
            "boundary": "FormRegistroTenant",
            "controller": "ControladorTenant",
            "entities": ["E_Tenant", "E_Subscription", "E_SubscriptionPlan", "E_Usuario", "E_Bitacora"],
            "messages": [
                ("Superadmin SaaS", "FormRegistroTenant", "1: solicitarRegistro(datos)", 1),
                ("FormRegistroTenant", "ControladorTenant", "1.1: register_tenant(datos)", 2),
                ("ControladorTenant", "E_Tenant", "1.1.1: validarSubdominio(subdominio)", 3),
                ("E_Tenant", "ControladorTenant", "1.1.2: return(disponible)", 4),
                ("ControladorTenant", "E_SubscriptionPlan", "1.1.3: obtenerLimitesPlan(codigoPlan)", 5),
                ("E_SubscriptionPlan", "ControladorTenant", "1.1.4: return(limites)", 6),
                ("ControladorTenant", "E_Tenant", "1.1.5: crearTenant(datos)", 7),
                ("E_Tenant", "ControladorTenant", "1.1.6: return(tenant_id)", 8),
                ("ControladorTenant", "E_Subscription", "1.1.7: crearSuscripcionInicial(plan_id, tenant_id)", 9),
                ("E_Subscription", "ControladorTenant", "1.1.8: return(sub_id)", 10),
                ("ControladorTenant", "E_Usuario", "1.1.9: crearUsuarioAdmin(email, password, tenant_id)", 11),
                ("E_Usuario", "ControladorTenant", "1.1.10: return(user_id)", 12),
                ("ControladorTenant", "E_Bitacora", "1.1.11: registrarAuditoria('REGISTRO_TENANT', tenant_id)", 13),
                ("E_Bitacora", "ControladorTenant", "1.1.12: return(ok)", 14),
                ("ControladorTenant", "FormRegistroTenant", "1.1.13: return(JsonResponse(success))", 15),
                ("FormRegistroTenant", "Superadmin SaaS", "1.2: mostrarNotificacionExito()", 16)
            ],
            "fragments": [
                ("opt [validarDisponibilidadSubdominio]", 2, -140, -230, False, "E_Tenant"),
                ("alt [crearEmpresaYSuscripcion]", 1, -245, -670, False, "E_Bitacora")
            ]
        },
        {
            "code": "CU-02",
            "title": "sd CU-02 Gestionar Planes de Suscripción",
            "actor": "Superadmin SaaS",
            "boundary": "FormPlanSuscripcion",
            "controller": "ControladorPlanes",
            "entities": ["E_SubscriptionPlan", "E_Subscription", "E_Bitacora"],
            "messages": [
                ("Superadmin SaaS", "FormPlanSuscripcion", "1: solicitarListaPlanes()", 1),
                ("FormPlanSuscripcion", "ControladorPlanes", "1.1: list_plans()", 2),
                ("ControladorPlanes", "E_SubscriptionPlan", "1.1.1: getActivos()", 3),
                ("E_SubscriptionPlan", "ControladorPlanes", "1.1.2: return(planes)", 4),
                ("ControladorPlanes", "FormPlanSuscripcion", "1.1.3: return(JsonResponse(planes))", 5),
                ("Superadmin SaaS", "FormPlanSuscripcion", "2: ingresarDatosPlan(datos)", 6),
                ("FormPlanSuscripcion", "ControladorPlanes", "2.1: save_plan(datos)", 7),
                ("ControladorPlanes", "E_SubscriptionPlan", "2.1.1: guardarPlan(datos)", 8),
                ("E_SubscriptionPlan", "ControladorPlanes", "2.1.2: return(plan_id)", 9),
                ("ControladorPlanes", "E_Bitacora", "2.1.3: registrarAuditoria('GESTION_PLAN', plan_id)", 10),
                ("E_Bitacora", "ControladorPlanes", "2.1.4: return(ok)", 11),
                ("ControladorPlanes", "FormPlanSuscripcion", "2.1.5: return(JsonResponse(success))", 12),
                ("ControladorPlanes", "E_Subscription", "2.1.6: contarSuscripcionesActivas(plan_id)", 13),
                ("E_Subscription", "ControladorPlanes", "2.1.7: return(totalActivas)", 14),
                ("FormPlanSuscripcion", "Superadmin SaaS", "2.2: mostrarNotificacionPlan()", 15)
            ],
            "fragments": [
                ("alt [listarPlanes]", 1, -125, -270, False, "E_SubscriptionPlan"),
                ("alt [crearOActualizarPlan]", 1, -285, -580, False, "E_Bitacora"),
                ("opt [verificarSuscripcionesActivas]", 2, -595, -700, False, "E_Subscription")
            ]
        },
        {
            "code": "CU-03",
            "title": "sd CU-03 Asignar y Renovar Suscripción de Empresa",
            "actor": "Superadmin SaaS",
            "boundary": "FormSuscripcion",
            "controller": "ControladorSuscripcion",
            "entities": ["E_Subscription", "E_Tenant", "E_SubscriptionPlan", "E_Bitacora"],
            "messages": [
                ("Superadmin SaaS", "FormSuscripcion", "1: consultarVigencia(tenant_id)", 1),
                ("FormSuscripcion", "ControladorSuscripcion", "1.1: get_tenant_subscription(tenant_id)", 2),
                ("ControladorSuscripcion", "E_Tenant", "1.1.1: validarEstado()", 3),
                ("E_Tenant", "ControladorSuscripcion", "1.1.2: return(activo)", 4),
                ("ControladorSuscripcion", "E_Subscription", "1.1.3: obtenerSuscripcionVigente(tenant_id)", 5),
                ("E_Subscription", "ControladorSuscripcion", "1.1.4: return(suscripcion)", 6),
                ("ControladorSuscripcion", "E_SubscriptionPlan", "1.1.5: obtenerDetalles(plan_id)", 7),
                ("E_SubscriptionPlan", "ControladorSuscripcion", "1.1.6: return(plan)", 8),
                ("ControladorSuscripcion", "FormSuscripcion", "1.1.7: return(JsonResponse(info))", 9),
                ("Superadmin SaaS", "FormSuscripcion", "2: solicitarRenovacion(tenant_id, nuevo_plan_id, periodo)", 10),
                ("FormSuscripcion", "ControladorSuscripcion", "2.1: renew_subscription(datos)", 11),
                ("ControladorSuscripcion", "E_Subscription", "2.1.1: renovarVigencia(periodo)", 12),
                ("E_Subscription", "ControladorSuscripcion", "2.1.2: return(nueva_fecha_fin)", 13),
                ("ControladorSuscripcion", "E_Bitacora", "2.1.3: registrarAuditoria('RENOVACION_PLAN', tenant_id)", 14),
                ("E_Bitacora", "ControladorSuscripcion", "2.1.4: return(ok)", 15),
                ("ControladorSuscripcion", "FormSuscripcion", "2.1.5: return(JsonResponse(success))", 16),
                ("FormSuscripcion", "Superadmin SaaS", "2.2: notificarRenovacionExitosa()", 17)
            ],
            "fragments": [
                ("alt [consultarEstadoActual]", 1, -125, -370, False, "E_SubscriptionPlan"),
                ("alt [renovarOAsignarPlan]", 1, -390, -670, False, "E_Bitacora")
            ]
        },
        {
            "code": "CU-04",
            "title": "sd CU-04 Controlar Límites y Restricciones por Plan",
            "actor": "Tenant Admin",
            "boundary": "FormControlLimites",
            "controller": "ControladorLimitesPlan",
            "entities": ["E_Tenant", "E_Subscription", "E_SubscriptionPlan", "E_Sucursal", "E_Usuario", "E_Bitacora"],
            "messages": [
                ("Tenant Admin", "FormControlLimites", "1: verificarCapacidadOperativa()", 1),
                ("FormControlLimites", "ControladorLimitesPlan", "1.1: verify_limits(tenant_id)", 2),
                ("ControladorLimitesPlan", "E_Tenant", "1.1.1: obtenerTenantId()", 3),
                ("E_Tenant", "ControladorLimitesPlan", "1.1.2: return(tenant_id)", 4),
                ("ControladorLimitesPlan", "E_Subscription", "1.1.3: obtenerPlanActivo(tenant_id)", 5),
                ("E_Subscription", "ControladorLimitesPlan", "1.1.4: return(plan_id)", 6),
                ("ControladorLimitesPlan", "E_SubscriptionPlan", "1.1.5: obtenerLimites(plan_id)", 7),
                ("E_SubscriptionPlan", "ControladorLimitesPlan", "1.1.6: return(max_sucursales, max_usuarios)", 8),
                ("ControladorLimitesPlan", "E_Sucursal", "1.1.7: contarSucursales(tenant_id)", 9),
                ("E_Sucursal", "ControladorLimitesPlan", "1.1.8: return(total_sucursales)", 10),
                ("ControladorLimitesPlan", "E_Usuario", "1.1.9: contarUsuariosActivos(tenant_id)", 11),
                ("E_Usuario", "ControladorLimitesPlan", "1.1.10: return(total_usuarios)", 12),
                ("ControladorLimitesPlan", "E_Bitacora", "1.1.11: registrarAlertaLimite('LIMITE_EXCEDIDO', tenant_id)", 13),
                ("E_Bitacora", "ControladorLimitesPlan", "1.1.12: return(ok)", 14),
                ("ControladorLimitesPlan", "FormControlLimites", "1.1.13: return(JsonResponse(bloqueado))", 15),
                ("FormControlLimites", "Tenant Admin", "1.2: mostrarAlertaExceso()", 16)
            ],
            "fragments": [
                ("opt [limiteAlcanzadoBloqueo]", 2, -490, -680, False, "E_Bitacora")
            ]
        },
        {
            "code": "CU-05",
            "title": "sd CU-05 Gestionar Sucursales y Empleados por Tenant",
            "actor": "Tenant Admin",
            "boundary": "FormSucursalesEmpleados",
            "controller": "ControladorSucursales",
            "entities": ["E_Tenant", "E_Sucursal", "E_Usuario", "E_Rol"],
            "messages": [
                ("Tenant Admin", "FormSucursalesEmpleados", "1: solicitarListado()", 1),
                ("FormSucursalesEmpleados", "ControladorSucursales", "1.1: list_branches_and_staff(tenant_id)", 2),
                ("ControladorSucursales", "E_Tenant", "1.1.1: validarTenantActivo()", 3),
                ("E_Tenant", "ControladorSucursales", "1.1.2: return(activo)", 4),
                ("ControladorSucursales", "E_Sucursal", "1.1.3: listarPorTenant(tenant_id)", 5),
                ("E_Sucursal", "ControladorSucursales", "1.1.4: return(sucursales)", 6),
                ("ControladorSucursales", "E_Usuario", "1.1.5: listarEmpleadosPorTenant(tenant_id)", 7),
                ("E_Usuario", "ControladorSucursales", "1.1.6: return(empleados)", 8),
                ("ControladorSucursales", "FormSucursalesEmpleados", "1.1.7: return(JsonResponse(data))", 9),
                ("Tenant Admin", "FormSucursalesEmpleados", "2: ingresarDatosSucursal(datos)", 10),
                ("FormSucursalesEmpleados", "ControladorSucursales", "2.1: create_branch(datos)", 11),
                ("ControladorSucursales", "E_Sucursal", "2.1.1: crearSucursal(datos)", 12),
                ("E_Sucursal", "ControladorSucursales", "2.1.2: return(sucursal_id)", 13),
                ("ControladorSucursales", "FormSucursalesEmpleados", "2.1.3: return(JsonResponse(success))", 14),
                ("Tenant Admin", "FormSucursalesEmpleados", "3: asignarEmpleado(usuario_id, sucursal_id, rol_id)", 15),
                ("FormSucursalesEmpleados", "ControladorSucursales", "3.1: assign_staff(datos)", 16),
                ("ControladorSucursales", "E_Rol", "3.1.1: validarRol(rol_id)", 17),
                ("E_Rol", "ControladorSucursales", "3.1.2: return(rol_valido)", 18),
                ("ControladorSucursales", "E_Usuario", "3.1.3: asignarSucursalYRol(sucursal_id, rol_id)", 19),
                ("E_Usuario", "ControladorSucursales", "3.1.4: return(asignado_ok)", 20),
                ("ControladorSucursales", "FormSucursalesEmpleados", "3.1.5: return(JsonResponse(success))", 21),
                ("FormSucursalesEmpleados", "Tenant Admin", "3.2: notificarAsignacionExitosa()", 22)
            ],
            "fragments": [
                ("alt [listarSucursalesYPersonal]", 1, -125, -340, False, "E_Usuario"),
                ("alt [registrarNuevaSucursal]", 1, -360, -490, False, "E_Sucursal"),
                ("alt [asignarEmpleado]", 1, -510, -740, False, "E_Rol")
            ]
        },
        {
            "code": "CU-06",
            "title": "sd CU-06 Descargar y Almacenar Catálogo Offline",
            "actor": "Cajero / Vendedor",
            "boundary": "FormDescargaCatalogo",
            "controller": "ControladorSyncCatalogo",
            "entities": ["E_Producto", "E_Categoria", "E_VarianteProducto", "E_Inventario", "E_SyncOperation"],
            "messages": [
                ("Cajero / Vendedor", "FormDescargaCatalogo", "1: solicitarDescarga(sucursal_id)", 1),
                ("FormDescargaCatalogo", "ControladorSyncCatalogo", "1.1: sync_catalog_download(sucursal_id)", 2),
                ("ControladorSyncCatalogo", "E_Categoria", "1.1.1: obtenerCategoriasActivas()", 3),
                ("E_Categoria", "ControladorSyncCatalogo", "1.1.2: return(categorias)", 4),
                ("ControladorSyncCatalogo", "E_Producto", "1.1.3: obtenerPrendasCatalogo()", 5),
                ("E_Producto", "ControladorSyncCatalogo", "1.1.4: return(productos)", 6),
                ("ControladorSyncCatalogo", "E_VarianteProducto", "1.1.5: obtenerVariantes(producto_id)", 7),
                ("E_VarianteProducto", "ControladorSyncCatalogo", "1.1.6: return(variantes)", 8),
                ("ControladorSyncCatalogo", "E_Inventario", "1.1.7: consultarStockDisponible(sucursal_id)", 9),
                ("E_Inventario", "ControladorSyncCatalogo", "1.1.8: return(stock)", 10),
                ("ControladorSyncCatalogo", "E_SyncOperation", "1.1.9: registrarOperacionSync('CATALOG_DOWNLOAD', sucursal_id)", 11),
                ("E_SyncOperation", "ControladorSyncCatalogo", "1.1.10: return(sync_id)", 12),
                ("ControladorSyncCatalogo", "FormDescargaCatalogo", "1.1.11: return(JsonResponse(descargaCompleta))", 13),
                ("FormDescargaCatalogo", "Cajero / Vendedor", "1.2: notificarDescargaExitosa()", 14)
            ],
            "fragments": [
                ("loop [procesarLotePrendas]", 4, -220, -480, True, "E_Inventario")
            ]
        },
        {
            "code": "CU-07",
            "title": "sd CU-07 Consultar Catálogo y Existencias Offline",
            "actor": "Cajero / Vendedor",
            "boundary": "FormConsultaCatalogoOffline",
            "controller": "ControladorCatalogoOffline",
            "entities": ["E_Producto", "E_Categoria", "E_VarianteProducto", "E_Inventario"],
            "messages": [
                ("Cajero / Vendedor", "FormConsultaCatalogoOffline", "1: filtrarPorCategoria(categoria_id)", 1),
                ("FormConsultaCatalogoOffline", "ControladorCatalogoOffline", "1.1: filter_local_catalog(categoria_id)", 2),
                ("ControladorCatalogoOffline", "E_Categoria", "1.1.1: getDetalle(categoria_id)", 3),
                ("E_Categoria", "ControladorCatalogoOffline", "1.1.2: return(categoria)", 4),
                ("ControladorCatalogoOffline", "E_Producto", "1.1.3: buscarPrendasLocales(categoria_id)", 5),
                ("E_Producto", "ControladorCatalogoOffline", "1.1.4: return(listaPrendas)", 6),
                ("ControladorCatalogoOffline", "FormConsultaCatalogoOffline", "1.1.5: return(JsonResponse(prendas))", 7),
                ("Cajero / Vendedor", "FormConsultaCatalogoOffline", "2: seleccionarPrenda(producto_id)", 8),
                ("FormConsultaCatalogoOffline", "ControladorCatalogoOffline", "2.1: get_stock_matrix(producto_id)", 9),
                ("ControladorCatalogoOffline", "E_VarianteProducto", "2.1.1: obtenerVariantesPorPrenda(producto_id)", 10),
                ("E_VarianteProducto", "ControladorCatalogoOffline", "2.1.2: return(variantes)", 11),
                ("ControladorCatalogoOffline", "E_Inventario", "2.1.3: consultarExistenciasLocales(variante_id)", 12),
                ("E_Inventario", "ControladorCatalogoOffline", "2.1.4: return(stock_fisico, stock_reservado)", 13),
                ("ControladorCatalogoOffline", "FormConsultaCatalogoOffline", "2.1.5: return(JsonResponse(matrizStock))", 14),
                ("FormConsultaCatalogoOffline", "Cajero / Vendedor", "2.2: mostrarDisponibilidadPrenda()", 15)
            ],
            "fragments": [
                ("alt [buscarPorFiltros]", 1, -125, -340, False, "E_Producto"),
                ("opt [consultarStockPorTallaYColor]", 2, -360, -630, False, "E_Inventario")
            ]
        },
        {
            "code": "CU-23",
            "title": "sd CU-23 Notificar Estado de Conectividad (Semáforo)",
            "actor": "Cajero / Vendedor",
            "boundary": "FormSemaforoConectividad",
            "controller": "ControladorSemaforoRed",
            "entities": ["E_SyncOperation", "E_Bitacora"],
            "messages": [
                ("Cajero / Vendedor", "FormSemaforoConectividad", "1: verificarEstadoEnlace()", 1),
                ("FormSemaforoConectividad", "ControladorSemaforoRed", "1.1: check_network_status()", 2),
                ("ControladorSemaforoRed", "E_SyncOperation", "1.1.1: actualizarEstadoConexion('ONLINE')", 3),
                ("E_SyncOperation", "ControladorSemaforoRed", "1.1.2: return(estado_actualizado)", 4),
                ("ControladorSemaforoRed", "FormSemaforoConectividad", "1.1.3: return(JsonResponse(status='ONLINE'))", 5),
                ("FormSemaforoConectividad", "Cajero / Vendedor", "1.2: mostrarSemaforoVerde()", 6),
                ("ControladorSemaforoRed", "E_SyncOperation", "1.1.4: actualizarEstadoConexion('OFFLINE')", 7),
                ("E_SyncOperation", "ControladorSemaforoRed", "1.1.5: return(estado_actualizado)", 8),
                ("ControladorSemaforoRed", "E_Bitacora", "1.1.6: registrarIncidenciaRed('DISCONNECTION_DETECTED')", 9),
                ("E_Bitacora", "ControladorSemaforoRed", "1.1.7: return(ok)", 10),
                ("ControladorSemaforoRed", "FormSemaforoConectividad", "1.1.8: return(JsonResponse(status='OFFLINE'))", 11),
                ("FormSemaforoConectividad", "Cajero / Vendedor", "1.3: activarModoOfflineVisual()", 12)
            ],
            "fragments": [
                ("alt [conexionDisponibleOnline]", 1, -125, -315, False, "E_SyncOperation"),
                ("alt [conexionPerdidaOffline]", 1, -335, -570, False, "E_Bitacora")
            ]
        },
        {
            "code": "CU-24",
            "title": "sd CU-24 Instalar y Registrar Service Worker (PWA)",
            "actor": "Usuario Web",
            "boundary": "FormInstaladorPWA",
            "controller": "ControladorPWA",
            "entities": ["E_SyncOperation", "E_Bitacora"],
            "messages": [
                ("Usuario Web", "FormInstaladorPWA", "1: solicitarInstalacionPWA()", 1),
                ("FormInstaladorPWA", "ControladorPWA", "1.1: register_service_worker()", 2),
                ("ControladorPWA", "E_SyncOperation", "1.1.1: registrarVersionSW('v1.0.0', 'INSTALLED')", 3),
                ("E_SyncOperation", "ControladorPWA", "1.1.2: return(registro_ok)", 4),
                ("ControladorPWA", "FormInstaladorPWA", "1.1.3: return(JsonResponse(sw_ready))", 5),
                ("FormInstaladorPWA", "Usuario Web", "1.2: mostrarPromptInstalado()", 6),
                ("ControladorPWA", "E_Bitacora", "1.1.4: registrarEventoPWA('CACHE_PRECACHE_COMPLETED')", 7),
                ("E_Bitacora", "ControladorPWA", "1.1.5: return(ok)", 8),
                ("ControladorPWA", "FormInstaladorPWA", "1.1.6: return(JsonResponse(cache_ready))", 9),
                ("FormInstaladorPWA", "Usuario Web", "1.3: notificarOfflineDisponible()", 10)
            ],
            "fragments": [
                ("alt [registroExitosoServiceWorker]", 1, -125, -315, False, "E_SyncOperation"),
                ("opt [cachearRecursosOffline]", 2, -335, -530, False, "E_Bitacora")
            ]
        },
        {
            "code": "CU-25",
            "title": "sd CU-25 Configurar y Migrar Persistencia SQLite Móvil",
            "actor": "Cajero / Vendedor",
            "boundary": "FormConfiguracionSQLite",
            "controller": "ControladorSQLiteMovil",
            "entities": ["E_Inventario", "E_VarianteProducto", "E_SyncOperation", "E_Bitacora"],
            "messages": [
                ("Cajero / Vendedor", "FormConfiguracionSQLite", "1: inicializarAlmacenamientoLocal()", 1),
                ("FormConfiguracionSQLite", "ControladorSQLiteMovil", "1.1: init_local_database()", 2),
                ("ControladorSQLiteMovil", "E_Inventario", "1.1.1: verificarEsquemaTablas()", 3),
                ("E_Inventario", "ControladorSQLiteMovil", "1.1.2: return(esquema_ok)", 4),
                ("ControladorSQLiteMovil", "E_VarianteProducto", "1.1.3: verificarEsquemaVariantes()", 5),
                ("E_VarianteProducto", "ControladorSQLiteMovil", "1.1.4: return(esquema_ok)", 6),
                ("ControladorSQLiteMovil", "E_SyncOperation", "1.1.5: aplicarMigracionLote(version_db=1)", 7),
                ("E_SyncOperation", "ControladorSQLiteMovil", "1.1.6: return(lote_migrado)", 8),
                ("ControladorSQLiteMovil", "E_Bitacora", "1.1.7: registrarConfiguracionDB('SQLITE_INIT_SUCCESS')", 9),
                ("E_Bitacora", "ControladorSQLiteMovil", "1.1.8: return(ok)", 10),
                ("ControladorSQLiteMovil", "FormConfiguracionSQLite", "1.1.9: return(JsonResponse(db_ready))", 11),
                ("FormConfiguracionSQLite", "Cajero / Vendedor", "1.2: notificarDispositivoListo()", 12)
            ],
            "fragments": [
                ("loop [migracionDatosIniciales]", 4, -300, -420, True, "E_SyncOperation"),
                ("opt [auditoriaConfiguracion]", 2, -435, -570, False, "E_Bitacora")
            ]
        }
    ]

    for cu in cu_definitions:
        diag = pkg193.Diagrams.AddNew(cu['title'], "Sequence")
        diag.Update()

        element_map = {}
        lifeline_x_coords = {}

        # 1. Actor
        actor_name = cu['actor']
        actor_el = pkg193.Elements.AddNew(actor_name, "Actor")
        actor_el.Update()
        element_map[actor_name] = actor_el

        # 2. Boundary (Circle icon with vertical line)
        boundary_name = cu['boundary']
        boundary_el = pkg193.Elements.AddNew(boundary_name, "Sequence")
        boundary_el.Stereotype = "boundary"
        boundary_el.StereotypeEx = "boundary"
        boundary_el.Update()
        element_map[boundary_name] = boundary_el

        # 3. Controller (MUST BE RECTANGULAR: empty Stereotype and StereotypeEx)
        controller_name = cu['controller']
        controller_el = pkg193.Elements.AddNew(controller_name, "Sequence")
        controller_el.Stereotype = ""
        controller_el.StereotypeEx = ""
        controller_el.Update()
        element_map[controller_name] = controller_el

        # 4..N. Entities (MUST BE RECTANGULAR: empty Stereotype and StereotypeEx)
        for ent_name in cu['entities']:
            ent_el = pkg193.Elements.AddNew(ent_name, "Sequence")
            ent_el.Stereotype = ""
            ent_el.StereotypeEx = ""
            ent_el.Update()
            element_map[ent_name] = ent_el

        # Place Lifelines
        all_ordered = [actor_name, boundary_name, controller_name] + cu['entities']
        start_x = 40
        spacing = 135
        y_top = -40
        y_bottom = -720

        for idx, l_name in enumerate(all_ordered):
            l_el = element_map[l_name]
            l_left = start_x + (idx * spacing)
            l_right = l_left + 110
            lifeline_x_coords[l_name] = (l_left, l_right)

            d_obj = diag.DiagramObjects.AddNew(f"l={l_left};r={l_right};t={y_top};b={y_bottom};", "")
            d_obj.ElementID = l_el.ElementID
            d_obj.left = l_left
            d_obj.right = l_right
            d_obj.top = y_top
            d_obj.bottom = y_bottom
            d_obj.Update()

        # Add CombinedFragments
        for frag_name, subtype, f_top, f_bottom, start_from_controller, rightmost_ent in cu['fragments']:
            f_el = pkg193.Elements.AddNew(frag_name, "InteractionFragment")
            f_el.Subtype = subtype
            f_el.Update()

            if start_from_controller:
                f_left = lifeline_x_coords[controller_name][0] - 15
            else:
                f_left = lifeline_x_coords[boundary_name][0] - 15

            f_right = lifeline_x_coords[rightmost_ent][1] + 15

            f_obj = diag.DiagramObjects.AddNew(f"l={f_left};r={f_right};t={f_top};b={f_bottom};", "")
            f_obj.ElementID = f_el.ElementID
            f_obj.left = f_left
            f_obj.right = f_right
            f_obj.top = f_top
            f_obj.bottom = f_bottom
            f_obj.Update()

        # Add Messages
        for src_name, dst_name, msg_name, seq_no in cu['messages']:
            src_el = element_map[src_name]
            dst_el = element_map[dst_name]

            conn = src_el.Connectors.AddNew(msg_name, "Sequence")
            conn.SupplierID = dst_el.ElementID
            conn.SequenceNo = seq_no
            conn.Update()

        diag.Update()
        repo.SaveDiagram(diag.DiagramID)
        repo.ReloadDiagram(diag.DiagramID)

        clean_name = cu['title'].replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').replace(':', '')[:30] + '.png'
        img_path = os.path.join(out_dir, clean_name)
        project.PutDiagramImageToFile(diag.DiagramGUID, img_path, 1)
        print(f"  OK: {cu['title']} generado y exportado con éxito.")

    pkg193.Elements.Refresh()
    pkg193.Diagrams.Refresh()
    print("\n¡Los 10 Diagramas de Secuencia fueron generados y verificados con éxito!")

if __name__ == '__main__':
    main()
