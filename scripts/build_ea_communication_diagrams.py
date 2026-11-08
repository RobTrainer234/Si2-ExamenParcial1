# -*- coding: utf-8 -*-
"""
Script maestro para generar los 10 Diagramas de Comunicación (Robustez BCE)
de la Etapa 1 en Enterprise Architect (CasosDeUso_SegundoParcial.eap).

Estructura solicitada:
1. Actores del caso de uso (izquierda).
2. Interfaz / Boundary (primer círculo, con icono de límite |O).
3. Controlador (segundo círculo, con icono de control con bucle circular).
4. Clases Entidades (círculos a la derecha, con icono de entidad _O), basadas
   fielmente en el Diagrama Conceptual Completo de la Base de Datos (FashionStore).
5. Textos con métodos numerados, parámetros y flechas de dirección:
   1: metodo(param) ->, 1.1: submetodo() ->, etc.
"""

import os
import subprocess
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

# ----------------------------------------------------------------------
# Definición de los 10 Casos de Uso Oficiales de la Etapa 1
# ----------------------------------------------------------------------
COMMUNICATION_DIAGRAMS_ETAPA1 = [
    {
        "code": "CU-01",
        "title": "CU-01 Registrar Empresa Contratante (Tenant)",
        "actors": ["Superadmin SaaS"],
        "boundary": "UI_RegistroTenant",
        "control": "ControladorTenant",
        "entities": [
            {
                "name": "Tenant",
                "messages": (
                    "2.1.1: validarUnicidadSubdominio(subdominio) ->\n"
                    "2.1.2: crearRegistroTenant(datos) ->\n"
                    "2.1.3: asignarEsquemaBD(schema_name) ->"
                )
            },
            {
                "name": "SubscriptionPlan",
                "messages": (
                    "1.2.1: obtenerPlanPorCodigo(plan_codigo) ->\n"
                    "1.2.2: consultarLimitesPermitidos() ->"
                )
            },
            {
                "name": "Subscription",
                "messages": (
                    "2.1.4: crearSuscripcionInicial(tenant_id, plan_id) ->\n"
                    "2.1.5: calcularVigenciaPrueba(14_dias) ->"
                )
            },
            {
                "name": "Usuario",
                "messages": (
                    "2.1.6: crearUsuarioAdminTenant(datosAdmin) ->\n"
                    "2.1.7: encriptarContrasena(password) ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "2.1.8: registrarEventoAuditoria(ALTA_TENANT) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: solicitarRegistroEmpresa(datosEmpresa) ->\n"
            "2: confirmarCreacionTenant() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: validarDatosFormulario(datosEmpresa) ->\n"
            "1.2: verificarDisponibilidadSubdominio(subdominio) ->\n"
            "2.1: procesarRegistroTenant(datosValidados) ->\n"
            "2.2: notificarResultadoRegistro() <-"
        )
    },
    {
        "code": "CU-02",
        "title": "CU-02 Gestionar Planes de Suscripción",
        "actors": ["Superadmin SaaS"],
        "boundary": "UI_GestionPlanes",
        "control": "ControladorPlanes",
        "entities": [
            {
                "name": "SubscriptionPlan",
                "messages": (
                    "1.1.1: obtenerTodosLosPlanes() ->\n"
                    "2.1.1: insertarPlanSuscripcion(datosPlan) ->\n"
                    "3.1.1: actualizarCuotasYPrecios(plan_id, cuotas) ->"
                )
            },
            {
                "name": "Subscription",
                "messages": (
                    "3.1.2: verificarSuscripcionesActivas(plan_id) ->\n"
                    "3.1.3: validarImpactoCambioPlan(plan_id) ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "2.1.2: registrarCreacionPlan(plan_id) ->\n"
                    "3.1.4: registrarModificacionPlan(plan_id, cambios) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: listarPlanesExistentes() ->\n"
            "2: guardarNuevoPlan(datosPlan) ->\n"
            "3: modificarLimitesPlan(plan_id, cuotas) ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: solicitarCatalogoPlanes() ->\n"
            "2.1: validarEstructuraPlan(datosPlan) ->\n"
            "3.1: procesarActualizacionPlan(plan_id, cuotas) ->"
        )
    },
    {
        "code": "CU-03",
        "title": "CU-03 Asignar y Renovar Suscripción de Empresa",
        "actors": ["Superadmin SaaS", "Tenant Admin"],
        "boundary": "UI_SuscripcionTenant",
        "control": "ControladorSuscripcion",
        "entities": [
            {
                "name": "Subscription",
                "messages": (
                    "1.1.1: buscarSuscripcionVigente(tenant_id) ->\n"
                    "2.1.1: calcularNuevaFechaVencimiento(periodo) ->\n"
                    "2.1.2: actualizarEstadoSuscripcion(ACTIVA) ->"
                )
            },
            {
                "name": "Tenant",
                "messages": (
                    "1.1.2: validarEstadoEmpresa(tenant_id) ->\n"
                    "2.1.3: habilitarAccesoTenant(tenant_id) ->"
                )
            },
            {
                "name": "SubscriptionPlan",
                "messages": (
                    "1.1.3: obtenerTarifasYBeneficios(plan_id) ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "2.1.4: registrarRenovacionExitosa(suscripcion_id) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: consultarEstadoSuscripcion(tenant_id) ->\n"
            "2: solicitarRenovacion(periodo, metodoPago) ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: obtenerSuscripcionActual(tenant_id) ->\n"
            "2.1: procesarRenovacionSuscripcion(tenant_id, periodo) ->"
        )
    },
    {
        "code": "CU-04",
        "title": "CU-04 Controlar Límites y Restricciones por Plan",
        "actors": ["Tenant Admin", "Cajero / Vendedor"],
        "boundary": "UI_MonitorLimitesPlan",
        "control": "ControladorLimitesPlan",
        "entities": [
            {
                "name": "Tenant",
                "messages": (
                    "1.1.0: obtenerTenant(tenant_id) ->"
                )
            },
            {
                "name": "Subscription",
                "messages": (
                    "1.1.1: obtenerPlanAsociado(tenant_id) ->\n"
                    "1.1.2: validarVigenciaSuscripcion() ->"
                )
            },
            {
                "name": "SubscriptionPlan",
                "messages": (
                    "1.1.3: obtenerLimitesMaximos(plan_id) ->\n"
                    "1.1.4: validarPermisoModuloIA(plan_id) ->"
                )
            },
            {
                "name": "Sucursal",
                "messages": (
                    "2.1.1: contarSucursalesActivas(tenant_id) ->"
                )
            },
            {
                "name": "Usuario",
                "messages": (
                    "2.1.2: contarUsuariosActivos(tenant_id) ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "1.1.5: registrarIntentoExcesoCuota(tenant_id) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: solicitarCreacionRecurso(tipoRecurso) ->\n"
            "2: verificarDisponibilidadCuota() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: validarPermisoOperacion(tenant_id, tipoRecurso) ->\n"
            "2.1: consultarConsumoActualRecursos(tenant_id) ->"
        )
    },
    {
        "code": "CU-05",
        "title": "CU-05 Gestionar Sucursales y Empleados por Tenant",
        "actors": ["Tenant Admin"],
        "boundary": "UI_SucursalesEmpleados",
        "control": "ControladorSucursales",
        "entities": [
            {
                "name": "Sucursal",
                "messages": (
                    "1.1.1: obtenerSucursalesPorTenant(tenant_id) ->\n"
                    "2.1.1: insertarSucursal(datosSucursal) ->\n"
                    "3.1.1: validarExistenciaSucursal(sucursal_id) ->"
                )
            },
            {
                "name": "Usuario",
                "messages": (
                    "1.1.2: obtenerEmpleadosPorTenant(tenant_id) ->\n"
                    "3.1.2: actualizarSucursalAsignada(usuario_id, suc_id) ->"
                )
            },
            {
                "name": "Rol",
                "messages": (
                    "1.1.3: verificarRolEmpleado(rol_id) ->"
                )
            },
            {
                "name": "Tenant",
                "messages": (
                    "2.1.2: validarPertinenciaTenant(tenant_id) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: listarSucursalesYPersonal() ->\n"
            "2: registrarNuevaSucursal(datosSucursal) ->\n"
            "3: asignarEmpleadoASucursal(usuario_id, suc_id) ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: solicitarOrganigramaTenant(tenant_id) ->\n"
            "2.1: procesarAltaSucursal(datosSucursal) ->\n"
            "3.1: procesarAsignacionEmpleado(usuario_id, suc_id) ->"
        )
    },
    {
        "code": "CU-06",
        "title": "CU-06 Descargar y Almacenar Catálogo Offline",
        "actors": ["Cajero / Vendedor"],
        "boundary": "UI_DescargaCatalogo",
        "control": "ControladorSyncCatalogo",
        "entities": [
            {
                "name": "Producto",
                "messages": (
                    "1.1.1: consultarProductosActivos(tenant_id) ->"
                )
            },
            {
                "name": "VarianteProducto",
                "messages": (
                    "1.1.2: consultarVariantesPorProductos() ->\n"
                    "1.1.3: obtenerPreciosYCodigosBarra() ->"
                )
            },
            {
                "name": "Inventario",
                "messages": (
                    "1.1.4: obtenerStockDisponible(sucursal_id) ->"
                )
            },
            {
                "name": "Categoria",
                "messages": (
                    "1.1.5: obtenerCategoriasPrendas() ->"
                )
            },
            {
                "name": "SyncOperation",
                "messages": (
                    "2.1.1: registrarDescargaCompletada(timestamp) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: iniciarDescargaCatalogoOffline(sucursal_id) ->\n"
            "2: verificarProgresoDescarga() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: solicitarInstantaneaCatalogo(sucursal_id) ->\n"
            "2.1: confirmarAlmacenamientoLocal() ->"
        )
    },
    {
        "code": "CU-07",
        "title": "CU-07 Consultar Catálogo y Existencias Offline",
        "actors": ["Cajero / Vendedor", "Cliente"],
        "boundary": "UI_ConsultaCatalogoOffline",
        "control": "ControladorCatalogoOffline",
        "entities": [
            {
                "name": "Producto",
                "messages": (
                    "1.1.1: filtrarProductosLocales(filtro) ->"
                )
            },
            {
                "name": "VarianteProducto",
                "messages": (
                    "1.1.2: buscarVariantesPorSKU(sku) ->\n"
                    "2.1.1: buscarPorCodigoBarras(codigo) ->"
                )
            },
            {
                "name": "Inventario",
                "messages": (
                    "1.1.3: consultarStockDisponibleLocal(variante_id) ->\n"
                    "1.1.4: verificarAlertaStockBajo(umbral_minimo) ->"
                )
            },
            {
                "name": "Categoria",
                "messages": (
                    "1.1.5: agruparPorCategoriaLocal(categoria_id) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: buscarPrendaPorCriterio(filtro, talla, color) ->\n"
            "2: escanearCodigoBarras(codigo) ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: ejecutarBusquedaLocal(filtro, cat_id) ->\n"
            "2.1: resolverVariantePorCodigo(codigo) ->"
        )
    },
    {
        "code": "CU-23",
        "title": "CU-23 Notificar Estado de Conectividad (Semáforo)",
        "actors": ["Cajero / Vendedor"],
        "boundary": "UI_SemaforoConectividad",
        "control": "ControladorSemaforoRed",
        "entities": [
            {
                "name": "SyncOperation",
                "messages": (
                    "2.1.1: contarOperacionesPendientes() ->\n"
                    "2.1.2: listarTransaccionesEnEspera() ->\n"
                    "1.1.1: cambiarModoOperacion(OFFLINE_MODO) ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "1.1.2: registrarCambioEstadoConectividad(evento) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: observarIndicadorConectividad() ->\n"
            "2: consultarDetalleColaPendiente() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: escucharEventosRed(online, offline) ->\n"
            "2.1: solicitarEstadoBandejaSalida() ->"
        )
    },
    {
        "code": "CU-24",
        "title": "CU-24 Instalar y Registrar Service Worker (PWA)",
        "actors": ["Usuario Web"],
        "boundary": "UI_InstalacionPWA",
        "control": "ControladorPWA",
        "entities": [
            {
                "name": "SyncOperation",
                "messages": (
                    "2.1.1: registrarCanalBackgroundSync(tag_sync) ->\n"
                    "2.1.2: inicializarBandejaOffline() ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "2.1.3: registrarInstalacionPWA(navegador, version) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: abrirAplicacionWeb() ->\n"
            "2: aceptarInstalacionPWA() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: verificarSoporteServiceWorker() ->\n"
            "2.1: ejecutarRegistroWorker(sw_url) ->"
        )
    },
    {
        "code": "CU-25",
        "title": "CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "actors": ["Cajero / Vendedor"],
        "boundary": "UI_ConfiguracionSQLite",
        "control": "ControladorSQLiteMovil",
        "entities": [
            {
                "name": "SyncOperation",
                "messages": (
                    "2.1.1: crearTablaOperacionesPendientes() ->\n"
                    "2.1.2: verificarIntegridadTransaccional() ->"
                )
            },
            {
                "name": "Inventario",
                "messages": (
                    "2.1.3: crearTablaInventarioLocal() ->"
                )
            },
            {
                "name": "VarianteProducto",
                "messages": (
                    "2.1.4: crearTablaVariantesLocal() ->"
                )
            },
            {
                "name": "Bitacora",
                "messages": (
                    "1.1.1: consultarVersionPragmaSQLite() ->\n"
                    "2.1.5: registrarMigracionExitosa(versionNueva) ->"
                )
            }
        ],
        "msg_actor_bnd": (
            "1: iniciarAplicacionMovil() ->\n"
            "2: verificarEstadoBaseDatosLocal() ->"
        ),
        "msg_bnd_ctrl": (
            "1.1: comprobarVersionEsquemaSQLite() ->\n"
            "2.1: ejecutarMigracionesPendientes() ->"
        )
    }
]

def build_communication_diagrams():
    print("1. Cerrando cualquier proceso previo de EA...")
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)

    print(f"2. Abriendo repositorio EA: {EAP_PATH} ...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError(f"No se pudo abrir el archivo EA: {EAP_PATH}")

    root_model = rep.Models.GetAt(0)

    # Buscar o crear paquete para Diagramas de Comunicación (Etapa 1)
    pkg_name = "Segundo Parcial - Diagramas de Comunicación (Etapa 1)"
    comm_pkg = None
    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            comm_pkg = p
            break

    if comm_pkg is None:
        comm_pkg = root_model.Packages.AddNew(pkg_name, "")
        comm_pkg.Notes = "Diagramas de Comunicación (Robustez BCE) para los 10 Casos de Uso de la Etapa 1 según la base de datos conceptual."
        comm_pkg.Update()
        root_model.Packages.Refresh()

    print(f"3. Paquete objetivo: '{comm_pkg.Name}' (ID: {comm_pkg.PackageID})")

    # Limpiar diagramas y elementos previos en este paquete para reconstrucción limpia y fiel
    print("4. Limpiando diagramas y elementos anteriores en el paquete...")
    for i in range(comm_pkg.Diagrams.Count - 1, -1, -1):
        comm_pkg.Diagrams.Delete(i)
    comm_pkg.Diagrams.Refresh()

    for i in range(comm_pkg.Elements.Count - 1, -1, -1):
        comm_pkg.Elements.Delete(i)
    comm_pkg.Elements.Refresh()

    elements_cache = {}

    def get_or_create_element(name, elem_type, stereotype=None):
        key = (name, elem_type, stereotype)
        if key in elements_cache:
            return elements_cache[key]

        el = comm_pkg.Elements.AddNew(name, elem_type)
        if stereotype:
            el.Stereotype = stereotype
        el.Update()
        elements_cache[key] = el
        return el

    def add_directed_connector(diag, src, dst):
        con = src.Connectors.AddNew("", "CommunicationPath")
        con.SupplierID = dst.ElementID
        con.Direction = "Source -> Destination"
        con.Update()
        src.Connectors.Refresh()

        lnk = diag.DiagramLinks.AddNew("", "")
        lnk.ConnectorID = con.ConnectorID
        lnk.Update()
        return con

    print(f"5. Construyendo los {len(COMMUNICATION_DIAGRAMS_ETAPA1)} Diagramas de Comunicación de la Etapa 1...")

    for cu in COMMUNICATION_DIAGRAMS_ETAPA1:
        diag_name = cu["title"]
        print(f"   -> Creando diagrama: {diag_name}")

        diag = comm_pkg.Diagrams.AddNew(diag_name, "Communication")
        diag.StyleEx = "HideQuals=1;DocAll=0;"
        diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
        diag.Update()
        comm_pkg.Diagrams.Refresh()

        # 1. Crear elementos de Actores
        actor_elements = []
        for act_name in cu["actors"]:
            el_act = get_or_create_element(act_name, "Actor")
            actor_elements.append(el_act)

        # 2. Crear Boundary (Interfaz)
        el_bnd = get_or_create_element(cu["boundary"], "Class", "boundary")

        # 3. Crear Controller (Controlador)
        el_ctrl = get_or_create_element(cu["control"], "Class", "control")

        # 4. Crear Entities (Entidades)
        entity_elements = []
        for ent_data in cu["entities"]:
            el_ent = get_or_create_element(ent_data["name"], "Class", "entity")
            entity_elements.append((el_ent, ent_data["messages"]))

        # -------------------------------------------------------------
        # Layout Geométrico BCE estilo Referencia:
        # Actores a la izquierda (X ~ 60..140)
        # Boundary UI (X ~ 360..450)
        # Controller (X ~ 680..770)
        # Entidades apiladas a la derecha (X ~ 1060..1150)
        # -------------------------------------------------------------
        num_entities = len(entity_elements)
        ent_spacing = 130
        ent_start_top = -60

        # Posicionar Entidades y sus Conectores con el Controlador
        for idx, (el_ent, ent_msgs) in enumerate(entity_elements):
            top_y = ent_start_top - (idx * ent_spacing)
            bot_y = top_y - 80
            obj = diag.DiagramObjects.AddNew(f"l=1060;r=1150;t={top_y};b={bot_y};", "")
            obj.ElementID = el_ent.ElementID
            obj.Update()

            # Conectar Controlador -> Entidad
            add_directed_connector(diag, el_ctrl, el_ent)

            # Texto con los métodos de la entidad
            t_ent = comm_pkg.Elements.AddNew(ent_msgs, "Text")
            t_ent.Notes = ent_msgs
            t_ent.Update()
            txt_top = top_y + 15
            txt_bot = top_y - 75
            o_tent = diag.DiagramObjects.AddNew(f"l=780;r=1045;t={txt_top};b={txt_bot};", "")
            o_tent.ElementID = t_ent.ElementID
            o_tent.Update()

        # Calcular Y central para Controller y Boundary
        mid_y = ent_start_top - int(((num_entities - 1) * ent_spacing) / 2)
        ctrl_top = mid_y + 40
        ctrl_bot = mid_y - 40

        # Posicionar Controller
        obj_ctrl = diag.DiagramObjects.AddNew(f"l=680;r=770;t={ctrl_top};b={ctrl_bot};", "")
        obj_ctrl.ElementID = el_ctrl.ElementID
        obj_ctrl.Update()

        # Posicionar Boundary
        obj_bnd = diag.DiagramObjects.AddNew(f"l=360;r=450;t={ctrl_top};b={ctrl_bot};", "")
        obj_bnd.ElementID = el_bnd.ElementID
        obj_bnd.Update()

        # Conectar Boundary -> Controller
        add_directed_connector(diag, el_bnd, el_ctrl)

        # Texto con métodos entre Boundary y Controller
        t_bnd_ctrl = comm_pkg.Elements.AddNew(cu["msg_bnd_ctrl"], "Text")
        t_bnd_ctrl.Notes = cu["msg_bnd_ctrl"]
        t_bnd_ctrl.Update()
        o_bnd_ctrl = diag.DiagramObjects.AddNew(f"l=460;r=670;t={ctrl_top + 20};b={ctrl_bot - 20};", "")
        o_bnd_ctrl.ElementID = t_bnd_ctrl.ElementID
        o_bnd_ctrl.Update()

        # Posicionar Actores y conectar a Boundary
        num_actors = len(actor_elements)
        if num_actors == 1:
            el_act = actor_elements[0]
            obj_act = diag.DiagramObjects.AddNew(f"l=60;r=140;t={ctrl_top + 10};b={ctrl_bot - 10};", "")
            obj_act.ElementID = el_act.ElementID
            obj_act.Update()
            add_directed_connector(diag, el_act, el_bnd)
        else:
            act_spacing = 140
            act_start_top = mid_y + int(((num_actors - 1) * act_spacing) / 2) + 20
            for a_idx, el_act in enumerate(actor_elements):
                a_top = act_start_top - (a_idx * act_spacing)
                a_bot = a_top - 80
                obj_act = diag.DiagramObjects.AddNew(f"l=60;r=140;t={a_top};b={a_bot};", "")
                obj_act.ElementID = el_act.ElementID
                obj_act.Update()
                add_directed_connector(diag, el_act, el_bnd)

        # Texto con métodos entre Actor y Boundary
        t_act_bnd = comm_pkg.Elements.AddNew(cu["msg_actor_bnd"], "Text")
        t_act_bnd.Notes = cu["msg_actor_bnd"]
        t_act_bnd.Update()
        o_act_bnd = diag.DiagramObjects.AddNew(f"l=150;r=350;t={ctrl_top + 20};b={ctrl_bot - 20};", "")
        o_act_bnd.ElementID = t_act_bnd.ElementID
        o_act_bnd.Update()

        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        diag.Update()

    comm_pkg.Diagrams.Refresh()
    comm_pkg.Elements.Refresh()

    rep.CloseFile()
    rep.Exit()

    print("=" * 70)
    print("EXITO: LOS 10 DIAGRAMAS DE COMUNICACIÓN DE LA ETAPA 1 FUERON ACTUALIZADOS")
    print(f"Repositorio EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name}")
    print("=" * 70)

if __name__ == "__main__":
    build_communication_diagrams()
