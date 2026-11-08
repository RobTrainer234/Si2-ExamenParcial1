# -*- coding: utf-8 -*-
"""
Script maestro para generar los 7 Diagramas de Secuencia UML de la ETAPA 2 en Enterprise Architect.
Paquete: 'Segundo Parcial - Diagramas de Secuencia (Etapa 2)'
Casos de Uso incluidos:
  - CU-08: sd CU-08 Registrar Venta de Contado Offline
  - CU-09: sd CU-09 Registrar Reserva de Prendas Offline
  - CU-10: sd CU-10 Consultar Operaciones Locales Pendientes (Outbox)
  - CU-11: sd CU-11 Sincronizar Operaciones con el Servidor
  - CU-12: sd CU-12 Gestionar Conflictos de Sincronización
  - CU-13: sd CU-13 Gestionar Cambio de Prendas de Vestir (30 Días)
  - CU-22: sd CU-22 Gestionar Datos Mínimos de Clientes Offline

Incluye lifelines (Actores, Boundaries, Controladores, Entidades E_...),
mensajes de llamada y retorno debidamente secuenciados,
y fragmentos combinados UML (alt, opt, loop).
"""

import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

ETAPA2_SEQUENCE_SPECS = [
    # -------------------------------------------------------------
    # CU-08: Registrar Venta de Contado Offline
    # -------------------------------------------------------------
    {
        "code": "CU-08",
        "title": "sd CU-08 Registrar Venta de Contado Offline",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("UI_VentaPOSOffline", "Sequence"),
            ("ControladorVentaOffline", "Sequence"),
            ("E_Venta", "Sequence"),
            ("E_DetalleVenta", "Sequence"),
            ("E_Pago", "Sequence"),
            ("E_Inventario", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Cliente", "Sequence")
        ],
        "fragments": [
            ("loop [para cada prenda en carrito]", 165, 840, -125, -290),
            ("alt [efectivo_recibido >= total]", 165, 1095, -310, -680),
            ("alt [efectivo insuficiente]", 165, 430, -700, -790)
        ],
        "messages": [
            # 1. Búsqueda y validación de stock
            ("Cajero / Vendedor", "UI_VentaPOSOffline", "1: ingresarCarritoPrendas(items)"),
            ("UI_VentaPOSOffline", "ControladorVentaOffline", "1.1: validarDisponibilidadLocal(items)"),
            ("ControladorVentaOffline", "E_Inventario", "1.1.1: consultarStockLocal(variante_id)"),
            ("E_Inventario", "ControladorVentaOffline", "1.1.2: return(stock_disponible)"),
            ("ControladorVentaOffline", "E_Cliente", "1.1.3: asociarClienteOpcional(nit_ci)"),
            ("E_Cliente", "ControladorVentaOffline", "1.1.4: return(cliente_info)"),
            ("ControladorVentaOffline", "UI_VentaPOSOffline", "1.1.5: return(items_agregados)"),
            # 2. Confirmación de venta y pago
            ("Cajero / Vendedor", "UI_VentaPOSOffline", "2: confirmarVentaContado(efectivo_recibido)"),
            ("UI_VentaPOSOffline", "ControladorVentaOffline", "2.1: procesarVentaOffline(datosVenta)"),
            ("ControladorVentaOffline", "E_Venta", "2.1.1: generarCodigoOrdenOffline(UUID)"),
            ("E_Venta", "ControladorVentaOffline", "2.1.2: return(orden_uuid)"),
            ("ControladorVentaOffline", "E_DetalleVenta", "2.1.3: crearDetallesVenta(items, precios)"),
            ("E_DetalleVenta", "ControladorVentaOffline", "2.1.4: return(ok)"),
            ("ControladorVentaOffline", "E_Pago", "2.1.5: registrarPagoEfectivo(monto, cambio)"),
            ("E_Pago", "ControladorVentaOffline", "2.1.6: return(pago_confirmado)"),
            ("ControladorVentaOffline", "E_Inventario", "2.1.7: descontarStockDisponibleLocal(cant)"),
            ("E_Inventario", "ControladorVentaOffline", "2.1.8: return(nuevo_stock)"),
            ("ControladorVentaOffline", "E_SyncOperation", "2.1.9: encolarOperacionOutbox(VENTA_OFFLINE)"),
            ("E_SyncOperation", "ControladorVentaOffline", "2.1.10: return(op_id)"),
            ("ControladorVentaOffline", "UI_VentaPOSOffline", "2.1.11: return(ticket_venta)"),
            ("UI_VentaPOSOffline", "Cajero / Vendedor", "2.2: emitirTicketVentaLocal()"),
            # Alternativo: rechazo por fondos
            ("ControladorVentaOffline", "UI_VentaPOSOffline", "2.3: return(error_monto_insuficiente)"),
            ("UI_VentaPOSOffline", "Cajero / Vendedor", "2.4: notificarErrorMonto()")
        ]
    },

    # -------------------------------------------------------------
    # CU-09: Registrar Reserva de Prendas Offline
    # -------------------------------------------------------------
    {
        "code": "CU-09",
        "title": "sd CU-09 Registrar Reserva de Prendas Offline",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("Cliente", "Actor"),
            ("UI_ReservaPrendasOffline", "Sequence"),
            ("ControladorReservaOffline", "Sequence"),
            ("E_Reserva", "Sequence"),
            ("E_DetalleReserva", "Sequence"),
            ("E_Inventario", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Cliente", "Sequence")
        ],
        "fragments": [
            ("alt [stock disponible >= cantidad solicitada]", 165, 1095, -130, -560),
            ("alt [stock insuficiente para reserva]", 165, 430, -580, -680)
        ],
        "messages": [
            ("Cliente", "UI_ReservaPrendasOffline", "1: solicitarApartadoPrenda(datosCliente, items)"),
            ("UI_ReservaPrendasOffline", "ControladorReservaOffline", "1.1: verificarStockParaApartado(items)"),
            ("ControladorReservaOffline", "E_Inventario", "1.1.1: validarStockDisponible(variante_id)"),
            ("E_Inventario", "ControladorReservaOffline", "1.1.2: return(stock_suficiente)"),
            ("ControladorReservaOffline", "E_Cliente", "1.1.3: verificarIdentidadCliente(ci_nit)"),
            ("E_Cliente", "ControladorReservaOffline", "1.1.4: return(cliente_verificado)"),
            ("ControladorReservaOffline", "UI_ReservaPrendasOffline", "1.1.5: return(habilitado_para_reserva)"),
            ("Cajero / Vendedor", "UI_ReservaPrendasOffline", "2: confirmarRegistroReserva()"),
            ("UI_ReservaPrendasOffline", "ControladorReservaOffline", "2.1: procesarApartadoOffline(datosReserva)"),
            ("ControladorReservaOffline", "E_Reserva", "2.1.1: generarCodigoReserva(UUID, 48_hrs)"),
            ("E_Reserva", "ControladorReservaOffline", "2.1.2: return(codigo_reserva)"),
            ("ControladorReservaOffline", "E_DetalleReserva", "2.1.3: crearDetallesReserva(variante_id, cant)"),
            ("E_DetalleReserva", "ControladorReservaOffline", "2.1.4: return(ok)"),
            ("ControladorReservaOffline", "E_Inventario", "2.1.5: incrementarStockReservado(cant)"),
            ("E_Inventario", "ControladorReservaOffline", "2.1.6: return(stock_actualizado)"),
            ("ControladorReservaOffline", "E_SyncOperation", "2.1.7: encolarOperacionOutbox(RESERVA_OFFLINE)"),
            ("E_SyncOperation", "ControladorReservaOffline", "2.1.8: return(op_id)"),
            ("ControladorReservaOffline", "UI_ReservaPrendasOffline", "2.1.9: return(comprobante_reserva)"),
            ("UI_ReservaPrendasOffline", "Cliente", "2.2: notificarComprobanteReserva()"),
            # Rama alternativa
            ("ControladorReservaOffline", "UI_ReservaPrendasOffline", "2.3: return(error_stock_agotado)"),
            ("UI_ReservaPrendasOffline", "Cliente", "2.4: notificarSinStockParaReserva()")
        ]
    },

    # -------------------------------------------------------------
    # CU-10: Consultar Operaciones Locales Pendientes (Outbox)
    # -------------------------------------------------------------
    {
        "code": "CU-10",
        "title": "sd CU-10 Consultar Operaciones Locales Pendientes (Outbox)",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("UI_OutboxTransacciones", "Sequence"),
            ("ControladorOutboxLocal", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Venta", "Sequence"),
            ("E_Reserva", "Sequence"),
            ("E_CambioPrenda", "Sequence")
        ],
        "fragments": [
            ("loop [para cada operacion en cola outbox]", 165, 960, -130, -420),
            ("opt [aplicar filtro por estado PENDIENTE/ERROR]", 165, 560, -440, -590)
        ],
        "messages": [
            ("Cajero / Vendedor", "UI_OutboxTransacciones", "1: abrirBandejaOutbox()"),
            ("UI_OutboxTransacciones", "ControladorOutboxLocal", "1.1: solicitarOperacionesPendientes()"),
            ("ControladorOutboxLocal", "E_SyncOperation", "1.1.1: listarOperacionesLocales(sucursal_id)"),
            ("E_SyncOperation", "ControladorOutboxLocal", "1.1.2: return(lista_operaciones)"),
            ("ControladorOutboxLocal", "E_Venta", "1.1.3: cargarResumenVentaLocal(client_op_id)"),
            ("E_Venta", "ControladorOutboxLocal", "1.1.4: return(resumen_venta)"),
            ("ControladorOutboxLocal", "E_Reserva", "1.1.5: cargarResumenReservaLocal(client_op_id)"),
            ("E_Reserva", "ControladorOutboxLocal", "1.1.6: return(resumen_reserva)"),
            ("ControladorOutboxLocal", "E_CambioPrenda", "1.1.7: cargarResumenCambioLocal(client_op_id)"),
            ("E_CambioPrenda", "ControladorOutboxLocal", "1.1.8: return(resumen_cambio)"),
            ("ControladorOutboxLocal", "UI_OutboxTransacciones", "1.1.9: return(transacciones_consolidadas)"),
            ("UI_OutboxTransacciones", "Cajero / Vendedor", "1.2: mostrarListaTransaccionesLocales()"),
            ("Cajero / Vendedor", "UI_OutboxTransacciones", "2: filtrarOperacionesPorEstado(estado)"),
            ("UI_OutboxTransacciones", "ControladorOutboxLocal", "2.1: aplicarFiltroCola(filtro)"),
            ("ControladorOutboxLocal", "UI_OutboxTransacciones", "2.1.1: return(lista_filtrada)"),
            ("UI_OutboxTransacciones", "Cajero / Vendedor", "2.2: renderizarBandejaActualizada()")
        ]
    },

    # -------------------------------------------------------------
    # CU-11: Sincronizar Operaciones con el Servidor
    # -------------------------------------------------------------
    {
        "code": "CU-11",
        "title": "sd CU-11 Sincronizar Operaciones con el Servidor",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("MotorSync", "Sequence"),
            ("UI_SincronizacionServidor", "Sequence"),
            ("ControladorSyncEngine", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Venta", "Sequence"),
            ("E_Inventario", "Sequence"),
            ("E_MovimientoInventario", "Sequence"),
            ("E_Bitacora", "Sequence")
        ],
        "fragments": [
            ("loop [para cada lote de 50 operaciones FIFO]", 295, 1230, -170, -600),
            ("alt [sincronizacion confirmada con exito]", 295, 1230, -620, -780),
            ("alt [fallo de red o timeout HTTP]", 295, 560, -800, -890)
        ],
        "messages": [
            ("Cajero / Vendedor", "UI_SincronizacionServidor", "1: dispararSincronizacionManual()"),
            ("MotorSync", "UI_SincronizacionServidor", "1.1: eventoConexionRestablecida()"),
            ("UI_SincronizacionServidor", "ControladorSyncEngine", "1.2: enviarLoteOperacionesOutbox()"),
            ("ControladorSyncEngine", "E_SyncOperation", "1.2.1: obtenerLotePendiente(limit=50)"),
            ("E_SyncOperation", "ControladorSyncEngine", "1.2.2: return(lote_operaciones)"),
            ("ControladorSyncEngine", "E_SyncOperation", "1.2.3: marcarEstadoEnProceso(op_ids)"),
            ("ControladorSyncEngine", "E_Venta", "1.2.4: consolidarVentaEnServidor(payload)"),
            ("E_Venta", "ControladorSyncEngine", "1.2.5: return(venta_guardada)"),
            ("ControladorSyncEngine", "E_Inventario", "1.2.6: conciliarSaldoFisicoServidor()"),
            ("E_Inventario", "ControladorSyncEngine", "1.2.7: return(stock_conciliado)"),
            ("ControladorSyncEngine", "E_MovimientoInventario", "1.2.8: registrarKardexServidor(VENTA_OFFLINE)"),
            ("E_MovimientoInventario", "ControladorSyncEngine", "1.2.9: return(kardex_ok)"),
            ("ControladorSyncEngine", "E_Bitacora", "1.2.10: auditarEventoSync(BATCH_SYNC_OK)"),
            ("ControladorSyncEngine", "E_SyncOperation", "1.2.11: actualizarEstadoSync(SINCRONIZADO)"),
            ("E_SyncOperation", "ControladorSyncEngine", "1.2.12: return(purgado_confirmado)"),
            ("ControladorSyncEngine", "UI_SincronizacionServidor", "1.2.13: return(resumen_sync_exitoso)"),
            ("UI_SincronizacionServidor", "Cajero / Vendedor", "1.3: reportarResultadoSync()"),
            # Rama alternativa de fallo
            ("ControladorSyncEngine", "E_SyncOperation", "1.4: revertirEstadoAPendiente(op_ids)"),
            ("ControladorSyncEngine", "UI_SincronizacionServidor", "1.5: return(error_timeout_red)"),
            ("UI_SincronizacionServidor", "Cajero / Vendedor", "1.6: notificarReintentoProgramado()")
        ]
    },

    # -------------------------------------------------------------
    # CU-12: Gestionar Conflictos de Sincronización
    # -------------------------------------------------------------
    {
        "code": "CU-12",
        "title": "sd CU-12 Gestionar Conflictos de Sincronización",
        "lifelines": [
            ("Tenant Admin", "Actor"),
            ("Cajero / Vendedor", "Actor"),
            ("UI_ResolucionConflictos", "Sequence"),
            ("ControladorConflictosSync", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Inventario", "Sequence"),
            ("E_CuarentenaInventario", "Sequence"),
            ("E_Venta", "Sequence"),
            ("E_Bitacora", "Sequence")
        ],
        "fragments": [
            ("alt [stock consumido concurrentemente - RN06]", 165, 1230, -180, -560),
            ("opt [compensacion o reposicion de stock]", 165, 840, -580, -760)
        ],
        "messages": [
            ("Tenant Admin", "UI_ResolucionConflictos", "1: consultarBandejaConflictos()"),
            ("UI_ResolucionConflictos", "ControladorConflictosSync", "1.1: obtenerOperacionesEnConflicto()"),
            ("ControladorConflictosSync", "E_SyncOperation", "1.1.1: listarOperacionesConConflicto()"),
            ("E_SyncOperation", "ControladorConflictosSync", "1.1.2: return(lista_conflictos)"),
            ("ControladorConflictosSync", "UI_ResolucionConflictos", "1.1.3: return(conflictos_renderizados)"),
            ("Tenant Admin", "UI_ResolucionConflictos", "2: seleccionarEstrategiaResolucion(politica_RN06)"),
            ("UI_ResolucionConflictos", "ControladorConflictosSync", "2.1: procesarResolucion(op_id, politica)"),
            ("ControladorConflictosSync", "E_Inventario", "2.1.1: verificarStockRemanenteServidor()"),
            ("E_Inventario", "ControladorConflictosSync", "2.1.2: return(deficit_detectado)"),
            ("ControladorConflictosSync", "E_CuarentenaInventario", "2.1.3: apartarItemsSinStock(cuarentena)"),
            ("E_CuarentenaInventario", "ControladorConflictosSync", "2.1.4: return(ingreso_cuarentena_ok)"),
            ("ControladorConflictosSync", "E_Venta", "2.1.5: actualizarEstadoTransaccion(CONCILIADA)"),
            ("E_Venta", "ControladorConflictosSync", "2.1.6: return(venta_conciliada)"),
            ("ControladorConflictosSync", "E_SyncOperation", "2.1.7: marcarConflictoResuelto(op_id)"),
            ("ControladorConflictosSync", "E_Bitacora", "2.1.8: registrarResolucionConflicto(auditoria)"),
            ("ControladorConflictosSync", "UI_ResolucionConflictos", "2.1.9: return(resolucion_exitosa)"),
            ("UI_ResolucionConflictos", "Tenant Admin", "2.2: notificarConflictoResuelto()"),
            ("UI_ResolucionConflictos", "Cajero / Vendedor", "2.3: notificarAjusteInventarioCajero()")
        ]
    },

    # -------------------------------------------------------------
    # CU-13: Gestionar Cambio de Prendas de Vestir (30 Días)
    # -------------------------------------------------------------
    {
        "code": "CU-13",
        "title": "sd CU-13 Gestionar Cambio de Prendas de Vestir (30 Días)",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("UI_CambioPrendasPOS", "Sequence"),
            ("ControladorCambioPrenda", "Sequence"),
            ("E_Venta", "Sequence"),
            ("E_DetalleVenta", "Sequence"),
            ("E_CambioPrenda", "Sequence"),
            ("E_DetalleCambio", "Sequence"),
            ("E_CuarentenaInventario", "Sequence"),
            ("E_Inventario", "Sequence")
        ],
        "fragments": [
            ("alt [plazo valido <= 30 dias - RN07]", 165, 1230, -180, -650),
            ("opt [diferencia monetaria a favor tienda]", 165, 560, -670, -780),
            ("alt [garantia vencida > 30 dias]", 165, 430, -800, -890)
        ],
        "messages": [
            ("Cajero / Vendedor", "UI_CambioPrendasPOS", "1: ingresarCodigoVentaOriginal(codigo)"),
            ("UI_CambioPrendasPOS", "ControladorCambioPrenda", "1.1: validarPlazoMaximo30Dias(fecha_venta)"),
            ("ControladorCambioPrenda", "E_Venta", "1.1.1: buscarVentaPorCodigo(codigo_orden)"),
            ("E_Venta", "ControladorCambioPrenda", "1.1.2: return(datos_venta_original)"),
            ("ControladorCambioPrenda", "E_DetalleVenta", "1.1.3: validarItemsOriginalesVendidos()"),
            ("E_DetalleVenta", "ControladorCambioPrenda", "1.1.4: return(items_validos)"),
            ("ControladorCambioPrenda", "UI_CambioPrendasPOS", "1.1.5: return(venta_habilitada_cambio)"),
            ("Cajero / Vendedor", "UI_CambioPrendasPOS", "2: seleccionarPrendaADevolverYNueva(items)"),
            ("UI_CambioPrendasPOS", "ControladorCambioPrenda", "2.1: calcularBalanceDiferenciaPrecios()"),
            ("ControladorCambioPrenda", "E_Inventario", "2.1.1: verificarStockNuevaPrenda()"),
            ("E_Inventario", "ControladorCambioPrenda", "2.1.2: return(stock_disponible_nueva)"),
            ("ControladorCambioPrenda", "UI_CambioPrendasPOS", "2.1.3: return(diferencia_calculada)"),
            ("Cajero / Vendedor", "UI_CambioPrendasPOS", "3: confirmarCambioPrenda(diferencia_pago)"),
            ("UI_CambioPrendasPOS", "ControladorCambioPrenda", "3.1: procesarCambioPrenda(datosCambio)"),
            ("ControladorCambioPrenda", "E_CambioPrenda", "3.1.1: registrarCabeceraCambio(valores, idempotency)"),
            ("E_CambioPrenda", "ControladorCambioPrenda", "3.1.2: return(cambio_id)"),
            ("ControladorCambioPrenda", "E_DetalleCambio", "3.1.3: registrarItemDevueltoYItemNuevo()"),
            ("E_DetalleCambio", "ControladorCambioPrenda", "3.1.4: return(ok)"),
            ("ControladorCambioPrenda", "E_CuarentenaInventario", "3.1.5: enviarPrendaDevueltaACuarentena()"),
            ("E_CuarentenaInventario", "ControladorCambioPrenda", "3.1.6: return(cuarentena_ok)"),
            ("ControladorCambioPrenda", "E_Inventario", "3.1.7: descontarStockNuevaPrendaEntregada()"),
            ("E_Inventario", "ControladorCambioPrenda", "3.1.8: return(stock_actualizado)"),
            ("ControladorCambioPrenda", "UI_CambioPrendasPOS", "3.1.9: return(comprobante_cambio)"),
            ("UI_CambioPrendasPOS", "Cajero / Vendedor", "3.2: emitirComprobanteCambio()"),
            # Rama alternativa de rechazo
            ("ControladorCambioPrenda", "UI_CambioPrendasPOS", "3.3: return(error_plazo_vencido)"),
            ("UI_CambioPrendasPOS", "Cajero / Vendedor", "3.4: alertarPlazoExcedido()")
        ]
    },

    # -------------------------------------------------------------
    # CU-22: Gestionar Datos Mínimos de Clientes Offline
    # -------------------------------------------------------------
    {
        "code": "CU-22",
        "title": "sd CU-22 Gestionar Datos Mínimos de Clientes Offline",
        "lifelines": [
            ("Cajero / Vendedor", "Actor"),
            ("UI_ClientesOffline", "Sequence"),
            ("ControladorClientesOffline", "Sequence"),
            ("E_Cliente", "Sequence"),
            ("E_Usuario", "Sequence"),
            ("E_SyncOperation", "Sequence"),
            ("E_Ciudad", "Sequence")
        ],
        "fragments": [
            ("alt [cliente no existe en cache local]", 165, 960, -180, -560),
            ("alt [cliente ya registrado en cache]", 165, 560, -580, -680)
        ],
        "messages": [
            ("Cajero / Vendedor", "UI_ClientesOffline", "1: buscarClientePorNIToCI(nit_ci)"),
            ("UI_ClientesOffline", "ControladorClientesOffline", "1.1: consultarCacheLocalClientes(nit_ci)"),
            ("ControladorClientesOffline", "E_Cliente", "1.1.1: buscarPorNITLocal(nit_ci)"),
            ("E_Cliente", "ControladorClientesOffline", "1.1.2: return(no_encontrado)"),
            ("ControladorClientesOffline", "UI_ClientesOffline", "1.1.3: return(solicitar_datos_minimos)"),
            ("Cajero / Vendedor", "UI_ClientesOffline", "2: registrarDatosClienteOffline(datosMinimos)"),
            ("UI_ClientesOffline", "ControladorClientesOffline", "2.1: validarCamposObligatorios(datos)"),
            ("ControladorClientesOffline", "E_Cliente", "2.1.1: crearRegistroClienteLocal(datos)"),
            ("E_Cliente", "ControladorClientesOffline", "2.1.2: return(cliente_local_id)"),
            ("ControladorClientesOffline", "E_Usuario", "2.1.3: crearPerfilUsuarioLocal(nombre, email)"),
            ("E_Usuario", "ControladorClientesOffline", "2.1.4: return(usuario_ok)"),
            ("ControladorClientesOffline", "E_Ciudad", "2.1.5: asociarCiudadResidencia(ciudad_id)"),
            ("E_Ciudad", "ControladorClientesOffline", "2.1.6: return(ciudad_ok)"),
            ("ControladorClientesOffline", "E_SyncOperation", "2.1.7: encolarAltaClienteOutbox(CLIENTE_OFFLINE)"),
            ("E_SyncOperation", "ControladorClientesOffline", "2.1.8: return(op_id)"),
            ("ControladorClientesOffline", "UI_ClientesOffline", "2.1.9: return(cliente_disponible)"),
            ("UI_ClientesOffline", "Cajero / Vendedor", "2.2: notificarClienteDisponible()"),
            # Rama alternativa
            ("ControladorClientesOffline", "UI_ClientesOffline", "2.3: return(datos_cliente_existente)"),
            ("UI_ClientesOffline", "Cajero / Vendedor", "2.4: cargarClienteAutocompletado()")
        ]
    }
]

def main():
    print("Iniciando generación de los 7 Diagramas de Secuencia UML de la ETAPA 2 en Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError("No se pudo abrir el archivo EA.")

    model = rep.Models.GetAt(0)
    pkg_name = "Segundo Parcial - Diagramas de Secuencia (Etapa 2)"
    pkg = None
    for p in model.Packages:
        if p.Name == pkg_name:
            pkg = p
            break

    if pkg is None:
        pkg = model.Packages.AddNew(pkg_name, "")
        pkg.Update()
        model.Packages.Refresh()
        print(f"Paquete creado: '{pkg_name}' (ID: {pkg.PackageID})")
    else:
        print(f"Paquete existente encontrado: '{pkg_name}' (ID: {pkg.PackageID})")

    # Mapeo de elementos en el paquete
    def get_or_create_element(name, elem_type):
        for i in range(pkg.Elements.Count):
            el = pkg.Elements.GetAt(i)
            if el.Name == name and el.Type == elem_type:
                return el
        el = pkg.Elements.AddNew(name, elem_type)
        el.Update()
        pkg.Elements.Refresh()
        return el

    for spec in ETAPA2_SEQUENCE_SPECS:
        diag_title = spec["title"]
        print(f"\n--- Procesando Diagrama de Secuencia: {diag_title} ---")

        diag = None
        for d in pkg.Diagrams:
            if d.Name == diag_title:
                diag = d
                break

        if diag is None:
            diag = pkg.Diagrams.AddNew(diag_title, "Sequence")
            diag.Update()
            pkg.Diagrams.Refresh()

        # 1. Posicionar Lifelines
        existing_dobjs = {diag.DiagramObjects.GetAt(i).ElementID: diag.DiagramObjects.GetAt(i) for i in range(diag.DiagramObjects.Count)}
        lifeline_elements = {}

        cur_left = 40
        width = 110
        gap = 25
        bottom_y = -920

        for l_name, l_type in spec["lifelines"]:
            el = get_or_create_element(l_name, l_type)
            lifeline_elements[l_name] = el

            r = cur_left + width
            if el.ElementID in existing_dobjs:
                dobj = existing_dobjs[el.ElementID]
            else:
                dobj = diag.DiagramObjects.AddNew(f"l={cur_left};r={r};t=-40;b={bottom_y};", "")
                dobj.ElementID = el.ElementID
            dobj.left = cur_left
            dobj.right = r
            dobj.top = -40
            dobj.bottom = bottom_y
            dobj.Update()

            cur_left += width + gap

        # 2. Posicionar Fragmentos Combinados (InteractionFragment: alt, loop, opt)
        for frag_name, fl, fr, ft, fb in spec["fragments"]:
            frag_el = get_or_create_element(frag_name, "InteractionFragment")
            if frag_el.ElementID in existing_dobjs:
                dobj_f = existing_dobjs[frag_el.ElementID]
            else:
                dobj_f = diag.DiagramObjects.AddNew(f"l={fl};r={fr};t={ft};b={fb};", "")
                dobj_f.ElementID = frag_el.ElementID
            dobj_f.left = fl
            dobj_f.right = fr
            dobj_f.top = ft
            dobj_f.bottom = fb
            dobj_f.Update()

        # 3. Mensajes de Secuencia
        print(f"  Sincronizando {len(spec['messages'])} mensajes de secuencia...")
        seq_num = 1
        for src_name, dst_name, msg_name in spec["messages"]:
            src_el = lifeline_elements[src_name]
            dst_el = lifeline_elements[dst_name]

            # Verificar si conector ya existe con el mismo nombre y secuencia
            conn_exists = False
            for c in src_el.Connectors:
                if c.SupplierID == dst_el.ElementID and c.Type == "Sequence" and c.Name == msg_name:
                    conn_exists = True
                    break

            if not conn_exists:
                conn = src_el.Connectors.AddNew(msg_name, "Sequence")
                conn.SupplierID = dst_el.ElementID
                conn.Direction = "Source -> Destination"
                conn.SequenceNo = seq_num
                conn.Update()
                src_el.Connectors.Refresh()

            seq_num += 1

        # 4. Estilo UML 2.5 Frame
        current_style = str(diag.StyleEx or "")
        if "ShowFrame=1;" not in current_style:
            diag.StyleEx = current_style + "ShowFrame=1;"
        diag.ExtendedStyle = "HideParents=1;SuppCN=1;HideProps=1;"
        diag.DiagramObjects.Refresh()
        diag.Update()

        rep.SaveDiagram(diag.DiagramID)
        rep.ReloadDiagram(diag.DiagramID)
        print(f"  Diagrama guardado con éxito: {diag_title} (ID: {diag.DiagramID})")

    pkg_id = pkg.PackageID
    pkg.Update()
    rep.CloseFile()
    rep.Exit()

    print("\n" + "=" * 70)
    print("¡LOS 7 DIAGRAMAS DE SECUENCIA DE LA ETAPA 2 FUERON GENERADOS CON ÉXITO!")
    print(f"Archivo EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name} (ID: {pkg_id})")
    print("Diagramas de secuencia generados:")
    for s in ETAPA2_SEQUENCE_SPECS:
        print(f"  - {s['title']}")
    print("=" * 70)

if __name__ == '__main__':
    main()
