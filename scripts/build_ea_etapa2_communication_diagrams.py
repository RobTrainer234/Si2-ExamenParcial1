# -*- coding: utf-8 -*-
"""
Script maestro para generar los 7 Diagramas de Comunicación UML de la ETAPA 2 en Enterprise Architect.
Paquete: 'Segundo Parcial - Diagramas de Comunicación (Etapa 2)'
Casos de Uso incluidos:
  - CU-08: Registrar Venta de Contado Offline
  - CU-09: Registrar Reserva de Prendas Offline
  - CU-10: Consultar Operaciones Locales Pendientes (Outbox)
  - CU-11: Sincronizar Operaciones con el Servidor
  - CU-12: Gestionar Conflictos de Sincronización
  - CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)
  - CU-22: Gestionar Datos Mínimos de Clientes Offline
"""

import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

ETAPA2_DIAGRAMS = [
    {
        "code": "CU-08",
        "name": "CU-08 Registrar Venta de Contado Offline",
        "actors": [("Cajero / Vendedor", 60, -270)],
        "boundary": ("UI_VentaPOSOffline", 360, -280),
        "control": ("ControladorVentaOffline", 680, -280),
        "entities": [
            ("Venta", 1060, -60),
            ("DetalleVenta", 1060, -190),
            ("Pago", 1060, -320),
            ("Inventario", 1060, -450),
            ("SyncOperation", 1060, -580),
            ("Cliente", 1060, -710)
        ],
        "msg_actor_boundary": "1: ingresarCarritoPrendas(items) ->\n2: confirmarVentaContado(efectivo_recibido) ->",
        "msg_boundary_control": "1.1: validarDisponibilidadLocal(items) ->\n2.1: procesarVentaOffline(datosVenta) ->\n2.2: emitirTicketVentaLocal() <-",
        "msg_control_entities": [
            "2.1.1: generarCodigoOrdenOffline(UUID) ->\n2.1.2: persistirVentaLocal(subtotal, total) ->",
            "2.1.3: crearDetallesVenta(items, precios) ->",
            "2.1.4: registrarPagoEfectivo(monto, cambio) ->",
            "1.1.1: consultarStockLocal(variante_id) ->\n2.1.5: descontarStockDisponibleLocal(cant) ->",
            "2.1.6: encolarOperacionOutbox(VENTA_OFFLINE) ->",
            "1.1.2: asociarClienteOpcional(nit_ci) ->"
        ]
    },
    {
        "code": "CU-09",
        "name": "CU-09 Registrar Reserva de Prendas Offline",
        "actors": [("Cajero / Vendedor", 60, -190), ("Cliente", 60, -330)],
        "boundary": ("UI_ReservaPrendasOffline", 360, -260),
        "control": ("ControladorReservaOffline", 680, -260),
        "entities": [
            ("Reserva", 1060, -60),
            ("DetalleReserva", 1060, -190),
            ("Inventario", 1060, -320),
            ("SyncOperation", 1060, -450),
            ("Cliente", 1060, -580)
        ],
        "msg_actor_boundary": "1: solicitarApartadoPrenda(datosCliente, items) ->\n2: confirmarRegistroReserva() ->",
        "msg_boundary_control": "1.1: verificarStockParaApartado(items) ->\n2.1: procesarApartadoOffline(datosReserva) ->\n2.2: notificarComprobanteReserva() <-",
        "msg_control_entities": [
            "2.1.1: generarCodigoReserva(UUID) ->\n2.1.2: fijarFechaLimiteVencimiento(48_hrs) ->\n2.1.3: persistirReservaLocal(estado=PENDIENTE) ->",
            "2.1.4: crearDetallesReserva(variante_id, cant) ->",
            "1.1.1: validarStockDisponible(variante_id) ->\n2.1.5: incrementarStockReservado(cant) ->\n2.1.6: disminuirStockDisponible(cant) ->",
            "2.1.7: encolarOperacionOutbox(RESERVA_OFFLINE) ->",
            "1.1.2: verificarIdentidadCliente(ci_nit) ->"
        ]
    },
    {
        "code": "CU-10",
        "name": "CU-10 Consultar Operaciones Locales Pendientes (Outbox)",
        "actors": [("Cajero / Vendedor", 60, -200)],
        "boundary": ("UI_OutboxTransacciones", 360, -210),
        "control": ("ControladorOutboxLocal", 680, -210),
        "entities": [
            ("SyncOperation", 1060, -60),
            ("Venta", 1060, -190),
            ("Reserva", 1060, -320),
            ("CambioPrenda", 1060, -450)
        ],
        "msg_actor_boundary": "1: abrirBandejaOutbox() ->\n2: filtrarOperacionesPorEstado(estado) ->",
        "msg_boundary_control": "1.1: solicitarOperacionesPendientes() ->\n2.1: aplicarFiltroCola(filtro) ->\n2.2: mostrarListaTransaccionesLocales() <-",
        "msg_control_entities": [
            "1.1.1: listarOperacionesLocales(sucursal_id) ->\n1.1.2: obtenerConteoPendientes() ->",
            "1.1.3: cargarResumenVentaLocal(client_op_id) ->",
            "1.1.4: cargarResumenReservaLocal(client_op_id) ->",
            "1.1.5: cargarResumenCambioLocal(client_op_id) ->"
        ]
    },
    {
        "code": "CU-11",
        "name": "CU-11 Sincronizar Operaciones con el Servidor",
        "actors": [("Cajero / Vendedor", 60, -190), ("Actores de Sistema (Motor de Sync)", 60, -330)],
        "boundary": ("UI_SincronizacionServidor", 360, -260),
        "control": ("ControladorSyncEngine", 680, -260),
        "entities": [
            ("SyncOperation", 1060, -60),
            ("Venta", 1060, -190),
            ("Inventario", 1060, -320),
            ("MovimientoInventario", 1060, -450),
            ("Bitacora", 1060, -580)
        ],
        "msg_actor_boundary": "1: dispararSincronizacionManual() ->\n2: monitorearProgresoSync() ->",
        "msg_boundary_control": "1.1: verificarConectividadServidor() ->\n1.2: enviarLoteOperacionesOutbox() ->\n2.1: reportarResultadoSync() <-",
        "msg_control_entities": [
            "1.2.1: obtenerLotePendiente(limit=50) ->\n1.2.2: marcarEstadoEnProceso(op_ids) ->\n1.2.3: actualizarEstadoSync(EXITO/FALLO) ->",
            "1.2.4: consolidarVentaEnServidor(payload) ->",
            "1.2.5: conciliarSaldoFisicoServidor() ->",
            "1.2.6: registrarKardexServidor(VENTA_OFFLINE) ->",
            "1.2.7: auditarEventoSync(BATCH_SYNC_COMPLETED) ->"
        ]
    },
    {
        "code": "CU-12",
        "name": "CU-12 Gestionar Conflictos de Sincronización",
        "actors": [("Tenant Admin", 60, -190), ("Cajero / Vendedor", 60, -330)],
        "boundary": ("UI_ResolucionConflictos", 360, -260),
        "control": ("ControladorConflictosSync", 680, -260),
        "entities": [
            ("SyncOperation", 1060, -60),
            ("Inventario", 1060, -190),
            ("CuarentenaInventario", 1060, -320),
            ("Venta", 1060, -450),
            ("Bitacora", 1060, -580)
        ],
        "msg_actor_boundary": "1: consultarBandejaConflictos() ->\n2: seleccionarEstrategiaResolucion(politica) ->",
        "msg_boundary_control": "1.1: obtenerOperacionesEnConflicto() ->\n2.1: procesarResolucion(op_id, politica) ->\n2.2: notificarConflictoResuelto() <-",
        "msg_control_entities": [
            "1.1.1: listarOperacionesConConflicto() ->\n2.1.1: marcarConflictoResuelto(op_id) ->",
            "2.1.2: verificarStockRemanenteServidor() ->\n2.1.3: ajustarInventarioPorPolitica() ->",
            "2.1.4: apartarItemsSinStock(cuarentena) ->",
            "2.1.5: actualizarEstadoTransaccion(CONCILIADA) ->",
            "2.1.6: registrarResolucionConflicto(auditoria) ->"
        ]
    },
    {
        "code": "CU-13",
        "name": "CU-13 Gestionar Cambio de Prendas de Vestir (30 Días)",
        "actors": [("Cajero / Vendedor", 60, -270)],
        "boundary": ("UI_CambioPrendasPOS", 360, -280),
        "control": ("ControladorCambioPrenda", 680, -280),
        "entities": [
            ("Venta", 1060, -60),
            ("DetalleVenta", 1060, -190),
            ("CambioPrenda", 1060, -320),
            ("DetalleCambio", 1060, -450),
            ("CuarentenaInventario", 1060, -580),
            ("Inventario", 1060, -710)
        ],
        "msg_actor_boundary": "1: ingresarCodigoVentaOriginal(codigo) ->\n2: seleccionarPrendaADevolverYNueva(items) ->\n3: confirmarCambioPrenda(diferencia_pago) ->",
        "msg_boundary_control": "1.1: validarPlazoMaximo30Dias(fecha_venta) ->\n2.1: calcularBalanceDiferenciaPrecios() ->\n3.1: procesarCambioPrenda(datosCambio) ->\n3.2: emitirComprobanteCambio() <-",
        "msg_control_entities": [
            "1.1.1: buscarVentaPorCodigo(codigo_orden) ->\n1.1.2: verificarEstadoVenta(PAGADA) ->",
            "2.1.1: validarItemsOriginalesVendidos() ->",
            "3.1.1: registrarCabeceraCambio(valores) ->\n3.1.2: aplicarIdempotencia(idempotency_key) ->",
            "3.1.3: registrarItemDevueltoYItemNuevo() ->",
            "3.1.4: enviarPrendaDevueltaACuarentena() ->",
            "3.1.5: verificarStockNuevaPrenda() ->\n3.1.6: descontarStockNuevaPrendaEntregada() ->"
        ]
    },
    {
        "code": "CU-22",
        "name": "CU-22 Gestionar Datos Mínimos de Clientes Offline",
        "actors": [("Cajero / Vendedor", 60, -200)],
        "boundary": ("UI_ClientesOffline", 360, -210),
        "control": ("ControladorClientesOffline", 680, -210),
        "entities": [
            ("Cliente", 1060, -60),
            ("Usuario", 1060, -190),
            ("SyncOperation", 1060, -320),
            ("Ciudad", 1060, -450)
        ],
        "msg_actor_boundary": "1: buscarClientePorNIToCI(nit_ci) ->\n2: registrarDatosClienteOffline(datosMinimos) ->",
        "msg_boundary_control": "1.1: consultarCacheLocalClientes(nit_ci) ->\n2.1: validarCamposObligatorios(datos) ->\n2.2: persistirClienteLocalmente() ->\n2.3: notificarClienteDisponible() <-",
        "msg_control_entities": [
            "1.1.1: buscarPorNITLocal(nit_ci) ->\n2.2.1: crearRegistroClienteLocal(datos) ->\n2.2.2: asignarPuntosIniciales(0) ->",
            "2.2.3: crearPerfilUsuarioLocal(nombre, email) ->",
            "2.2.4: encolarAltaClienteOutbox(CLIENTE_OFFLINE) ->",
            "2.2.5: asociarCiudadResidencia(ciudad_id) ->"
        ]
    }
]

def main():
    print("Iniciando generación de los Diagramas de Comunicación para la Etapa 2...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    model = rep.Models.GetAt(0)

    # 1. Buscar o crear el Paquete 'Segundo Parcial - Diagramas de Comunicación (Etapa 2)'
    pkg_name = "Segundo Parcial - Diagramas de Comunicación (Etapa 2)"
    pkg = None
    for p in model.Packages:
        if p.Name == pkg_name:
            pkg = p
            break

    if pkg is None:
        pkg = model.Packages.AddNew(pkg_name, "")
        pkg.Update()
        model.Packages.Refresh()
        print(f"Paquete nuevo creado: '{pkg_name}' (ID: {pkg.PackageID})")
    else:
        print(f"Paquete existente encontrado: '{pkg_name}' (ID: {pkg.PackageID})")

    # Mapeo de elementos existentes en el paquete para reutilizar o crear
    elements_map = {pkg.Elements.GetAt(i).Name: pkg.Elements.GetAt(i) for i in range(pkg.Elements.Count)}

    def get_or_create_element(name, elem_type, stereotype=""):
        key = f"{name}_{elem_type}_{stereotype}"
        for i in range(pkg.Elements.Count):
            el = pkg.Elements.GetAt(i)
            if el.Name == name and el.Type == elem_type and el.Stereotype == stereotype:
                return el
        el = pkg.Elements.AddNew(name, elem_type)
        if stereotype:
            el.Stereotype = stereotype
        el.Update()
        pkg.Elements.Refresh()
        return el

    # 2. Generar cada diagrama
    for spec in ETAPA2_DIAGRAMS:
        diag_name = spec["name"]
        print(f"\n--- Procesando: {diag_name} ---")

        # Buscar o crear diagrama
        diag = None
        for d in pkg.Diagrams:
            if d.Name == diag_name:
                diag = d
                break

        if diag is None:
            diag = pkg.Diagrams.AddNew(diag_name, "Communication")
            diag.Update()
            pkg.Diagrams.Refresh()
            print(f"  Diagrama creado: {diag_name} (ID: {diag.DiagramID})")
        else:
            print(f"  Diagrama existente: {diag_name} (ID: {diag.DiagramID})")

        # Limpiar objetos previos del diagrama para asegurar reconstrucción perfecta
        existing_dobjs = {diag.DiagramObjects.GetAt(i).ElementID: diag.DiagramObjects.GetAt(i) for i in range(diag.DiagramObjects.Count)}

        def place_object(el, l, r, t, b):
            if el.ElementID in existing_dobjs:
                dobj = existing_dobjs[el.ElementID]
            else:
                dobj = diag.DiagramObjects.AddNew(f"l={l};r={r};t={t};b={b};", "")
                dobj.ElementID = el.ElementID
            dobj.left = l
            dobj.right = r
            dobj.top = t
            dobj.bottom = b
            dobj.Update()
            return dobj

        def connect(src_el, dst_el):
            for c in src_el.Connectors:
                if c.SupplierID == dst_el.ElementID and c.Type == "CommunicationPath":
                    return c
            conn = src_el.Connectors.AddNew("", "CommunicationPath")
            conn.SupplierID = dst_el.ElementID
            conn.Direction = "Unspecified"
            conn.Update()
            src_el.Connectors.Refresh()
            return conn

        # A. Crear / posicionar Actores
        actor_elements = []
        for a_name, a_l, a_t in spec["actors"]:
            a_el = get_or_create_element(a_name, "Actor")
            place_object(a_el, a_l, a_l + 80, a_t, a_t - 100)
            actor_elements.append(a_el)

        # B. Crear / posicionar Boundary
        b_name, b_l, b_t = spec["boundary"]
        b_el = get_or_create_element(b_name, "Class", "boundary")
        place_object(b_el, b_l, b_l + 90, b_t, b_t - 80)

        # C. Crear / posicionar Control
        c_name, c_l, c_t = spec["control"]
        c_el = get_or_create_element(c_name, "Class", "control")
        place_object(c_el, c_l, c_l + 90, c_t, c_t - 80)

        # Conectar Actores con Boundary
        for a_el in actor_elements:
            connect(a_el, b_el)

        # Conectar Boundary con Control
        connect(b_el, c_el)

        # D. Crear / posicionar Entities y conectar con Control
        entity_elements = []
        for (e_name, e_l, e_t), msg_entity in zip(spec["entities"], spec["msg_control_entities"]):
            e_el = get_or_create_element(e_name, "Class", "entity")
            place_object(e_el, e_l, e_l + 90, e_t, e_t - 80)
            entity_elements.append(e_el)
            connect(c_el, e_el)

            # Texto de mensajes entre Control y Entidad
            txt_el = pkg.Elements.AddNew(msg_entity, "Text")
            txt_el.Notes = msg_entity
            txt_el.Update()
            place_object(txt_el, 780, 1045, e_t + 15, e_t - 75)

        # E. Texto de mensajes Actor -> Boundary
        txt_ab = pkg.Elements.AddNew(spec["msg_actor_boundary"], "Text")
        txt_ab.Notes = spec["msg_actor_boundary"]
        txt_ab.Update()
        mid_actor_t = sum(a[2] for a in spec["actors"]) // len(spec["actors"])
        place_object(txt_ab, 150, 350, mid_actor_t + 10, mid_actor_t - 110)

        # F. Texto de mensajes Boundary -> Control
        txt_bc = pkg.Elements.AddNew(spec["msg_boundary_control"], "Text")
        txt_bc.Notes = spec["msg_boundary_control"]
        txt_bc.Update()
        place_object(txt_bc, 460, 670, b_t + 20, b_t - 100)

        # Estilo del diagrama con Frame UML
        current_style = str(diag.StyleEx or "")
        if "ShowFrame=1;" not in current_style:
            diag.StyleEx = current_style + "ShowFrame=1;"
        diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
        diag.DiagramObjects.Refresh()
        diag.Update()

        rep.SaveDiagram(diag.DiagramID)
        rep.ReloadDiagram(diag.DiagramID)
        print(f"  Diagrama guardado con éxito: {diag_name}")

    pkg_id = pkg.PackageID
    pkg.Update()
    rep.CloseFile()
    rep.Exit()

    print("\n" + "=" * 70)
    print("¡LOS 7 DIAGRAMAS DE COMUNICACIÓN DE LA ETAPA 2 FUERON GENERADOS CON ÉXITO!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print("Diagramas generados:")
    for s in ETAPA2_DIAGRAMS:
        print(f"  - {s['name']}")
    print("=" * 70)

if __name__ == '__main__':
    main()
