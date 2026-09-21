"""
Generador de Diagramas de Comunicación UML 2.5 para Ciclo 1, Ciclo 2 y Ciclo 3
del sistema FashionStore en Enterprise Architect.

Genera los 18 nuevos diagramas de comunicación (Ciclo 1 y Ciclo 2)
y asegura la integración completa de los 23 Casos de Uso organizados por ciclo.
"""

import os
import sys
import subprocess
import time
import traceback
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

os.makedirs(EXPORT_DIR, exist_ok=True)

CYCLE_1_USE_CASES = [
    {
        "id": "CU01",
        "name": "CU01 Registrar Cliente",
        "filename": "comunicacion-cu01-registrar-cliente.png",
        "actor": "Invitado",
        "boundary": "UI_RegistroCliente",
        "control": "RegistroClienteController",
        "entity": "Cliente",
        "msg_link1": (
            "1: ingresarDatosRegistro(nombre, email, password, telefono)\n"
            "2: aceptarTerminosCondiciones(true)\n"
            "3: confirmarRegistro()"
        ),
        "msg_link2": (
            "1.1: validarCamposFormulario(datos)\n"
            "2.1: verificarDisponibilidadEmail(email)\n"
            "3.1: procesarAltaCliente(datosRegistro)"
        ),
        "msg_link3": (
            "2.2: findByEmail(email)\n"
            "3.2: createCliente(datosRegistro)\n"
            "3.3: hashPassword(password)\n"
            "3.4: save(cliente)"
        ),
    },
    {
        "id": "CU02",
        "name": "CU02 Iniciar y Cerrar Sesión",
        "filename": "comunicacion-cu02-iniciar-cerrar-sesion.png",
        "actor": "Cliente",
        "boundary": "UI_Autenticacion",
        "control": "AuthController",
        "entity": "Usuario",
        "msg_link1": (
            "1: ingresarCredenciales(email, password)\n"
            "2: seleccionarRecordarSesion(true)\n"
            "3: solicitarCierreSesion(token)"
        ),
        "msg_link2": (
            "1.1: autenticarUsuario(email, password)\n"
            "2.1: generarTokenJWT(usuario_id)\n"
            "3.1: invalidarTokenSesion(token)"
        ),
        "msg_link3": (
            "1.2: findByEmail(email)\n"
            "1.3: verifyPassword(password_hash)\n"
            "2.2: updateUltimoAcceso(fecha_hora)\n"
            "3.2: saveBlacklistToken(token)"
        ),
    },
    {
        "id": "CU03",
        "name": "CU03 Gestionar Usuarios y Roles",
        "filename": "comunicacion-cu03-gestionar-usuarios-roles.png",
        "actor": "Administrador",
        "boundary": "UI_GestionUsuarios",
        "control": "UsuarioRolController",
        "entity": "Usuario",
        "msg_link1": (
            "1: listarUsuarios(filtro_rol, estado)\n"
            "2: crearNuevoUsuario(datos_usuario, rol_id)\n"
            "3: actualizarRolPermisos(usuario_id, nuevo_rol_id)\n"
            "4: cambiarEstadoUsuario(usuario_id, activo)"
        ),
        "msg_link2": (
            "1.1: consultarUsuarios(filtro_rol, estado)\n"
            "2.1: validarDatosUsuario(datos_usuario)\n"
            "3.1: reasignarRol(usuario_id, nuevo_rol_id)\n"
            "4.1: toggleActivo(usuario_id, activo)"
        ),
        "msg_link3": (
            "1.2: findWithRoles(filtro)\n"
            "2.2: checkEmailUnique(email)\n"
            "2.3: save(nuevoUsuario)\n"
            "3.2: findById(usuario_id)\n"
            "3.3: setRolId(nuevo_rol_id)\n"
            "4.2: setEstado(activo)"
        ),
    },
    {
        "id": "CU04",
        "name": "CU04 Gestionar Sucursales y Ciudades",
        "filename": "comunicacion-cu04-gestionar-sucursales-ciudades.png",
        "actor": "Administrador",
        "boundary": "UI_GestionSucursal",
        "control": "SucursalController",
        "entity": "Sucursal",
        "msg_link1": (
            "1: consultarSucursales(ciudad_id)\n"
            "2: registrarSucursal(nombre, direccion, ciudad_id)\n"
            "3: editarInformacionSucursal(sucursal_id, datos)\n"
            "4: asignarEncargadoSucursal(sucursal_id, empleado_id)"
        ),
        "msg_link2": (
            "1.1: listarSucursalesPorCiudad(ciudad_id)\n"
            "2.1: validarDatosSucursal(datos)\n"
            "3.1: actualizarDatosSucursal(sucursal_id, datos)\n"
            "4.1: vincularEncargado(sucursal_id, empleado_id)"
        ),
        "msg_link3": (
            "1.2: findByCiudad(ciudad_id)\n"
            "2.2: save(sucursal)\n"
            "3.2: findById(sucursal_id)\n"
            "3.3: update(sucursal)\n"
            "4.2: setEncargadoId(empleado_id)"
        ),
    },
    {
        "id": "CU05",
        "name": "CU05 Gestionar Productos y Prendas",
        "filename": "comunicacion-cu05-gestionar-productos-prendas.png",
        "actor": "Administrador",
        "boundary": "UI_GestionPrendas",
        "control": "PrendaController",
        "entity": "Prenda",
        "msg_link1": (
            "1: consultarCatalogoPrendas(filtros)\n"
            "2: registrarPrenda(datos_prenda, categoria_id)\n"
            "3: modificarPrenda(prenda_id, nuevos_datos)\n"
            "4: deshabilitarPrenda(prenda_id)"
        ),
        "msg_link2": (
            "1.1: listarPrendas(filtros)\n"
            "2.1: procesarAltaPrenda(datos_prenda)\n"
            "3.1: procesarEdicionPrenda(prenda_id, nuevos_datos)\n"
            "4.1: cambiarVisibilidadCatalogo(prenda_id, false)"
        ),
        "msg_link3": (
            "1.2: searchPrendas(filtros)\n"
            "2.2: validateSKU(codigo_sku)\n"
            "2.3: save(prenda)\n"
            "3.2: findById(prenda_id)\n"
            "3.3: update(prenda)\n"
            "4.2: setActivo(false)"
        ),
    },
    {
        "id": "CU06",
        "name": "CU06 Gestionar Catálogo Base",
        "filename": "comunicacion-cu06-gestionar-catalogo-base.png",
        "actor": "Administrador",
        "boundary": "UI_CatalogoBase",
        "control": "CatalogoBaseController",
        "entity": "Categoria",
        "msg_link1": (
            "1: listarCategoriasYTallas()\n"
            "2: agregarCategoria(nombre, genero, descripcion)\n"
            "3: agregarTallaColor(talla, color_hex)\n"
            "4: actualizarCategoria(categoria_id, datos)"
        ),
        "msg_link2": (
            "1.1: obtenerEstructuraCatalogo()\n"
            "2.1: crearCategoria(datos_cat)\n"
            "3.1: registrarVarianteBase(talla, color)\n"
            "4.1: editarCategoria(categoria_id, datos)"
        ),
        "msg_link3": (
            "1.2: findAllCategoriasWithTallas()\n"
            "2.2: save(categoria)\n"
            "3.2: saveVarianteBase(talla, color)\n"
            "4.2: findById(categoria_id)\n"
            "4.3: update(categoria)"
        ),
    },
    {
        "id": "CU07",
        "name": "CU07 Gestionar Proveedores",
        "filename": "comunicacion-cu07-gestionar-proveedores.png",
        "actor": "Administrador",
        "boundary": "UI_GestionProveedores",
        "control": "ProveedorController",
        "entity": "Proveedor",
        "msg_link1": (
            "1: listarProveedores(filtro_rubro)\n"
            "2: registrarProveedor(razon_social, nit, contacto)\n"
            "3: modificarDatosProveedor(proveedor_id, datos)\n"
            "4: consultarHistorialSuministros(proveedor_id)"
        ),
        "msg_link2": (
            "1.1: consultarProveedores(filtro_rubro)\n"
            "2.1: validarDatosProveedor(datos)\n"
            "3.1: actualizarProveedor(proveedor_id, datos)\n"
            "4.1: obtenerSuministros(proveedor_id)"
        ),
        "msg_link3": (
            "1.2: findAll(filtro_rubro)\n"
            "2.2: checkNITUnique(nit)\n"
            "2.3: save(proveedor)\n"
            "3.2: findById(proveedor_id)\n"
            "3.3: update(proveedor)\n"
            "4.2: getOrdenesCompra(proveedor_id)"
        ),
    },
    {
        "id": "CU08",
        "name": "CU08 Consultar Catálogo y Buscar Prendas",
        "filename": "comunicacion-cu08-consultar-catalogo-buscar-prendas.png",
        "actor": "Cliente",
        "boundary": "UI_CatalogoExploracion",
        "control": "CatalogoController",
        "entity": "Prenda",
        "msg_link1": (
            "1: abrirCatalogo()\n"
            "2: aplicarFiltros(categoria, talla, rango_precio)\n"
            "3: buscarPorPalabraClave(termino)\n"
            "4: seleccionarPrenda(prenda_id)"
        ),
        "msg_link2": (
            "1.1: cargarPrendasDestacadas()\n"
            "2.1: filtrarCatalogo(criterios)\n"
            "3.1: ejecutarBusquedaTexto(termino)\n"
            "4.1: obtenerFichaTecnica(prenda_id)"
        ),
        "msg_link3": (
            "1.2: findDestacadosActivos()\n"
            "2.2: queryByCriteria(categoria, talla, precio)\n"
            "3.2: searchByKeywords(termino)\n"
            "4.2: findByIdWithVariantes(prenda_id)"
        ),
    },
    {
        "id": "CU09",
        "name": "CU09 Consultar Disponibilidad en Tiendas",
        "filename": "comunicacion-cu09-consultar-disponibilidad-tiendas.png",
        "actor": "Cliente",
        "boundary": "UI_DisponibilidadStock",
        "control": "DisponibilidadStockController",
        "entity": "Stock",
        "msg_link1": (
            "1: seleccionarPrendaTalla(prenda_id, talla, color)\n"
            "2: seleccionarCiudad(ciudad_id)\n"
            "3: consultarStockSucursales(prenda_id, ciudad_id)\n"
            "4: verUbicacionTienda(sucursal_id)"
        ),
        "msg_link2": (
            "1.1: verificarVariantePrenda(prenda_id, talla, color)\n"
            "2.1: filtrarSucursalesCiudad(ciudad_id)\n"
            "3.1: consultarDisponibilidad(prenda_id, ciudad_id)\n"
            "4.1: obtenerDetalleTienda(sucursal_id)"
        ),
        "msg_link3": (
            "1.2: findVarianteId(prenda_id, talla, color)\n"
            "3.2: getStockBySucursales(variante_id, ciudad_id)\n"
            "4.2: findSucursalById(sucursal_id)"
        ),
    },
]

CYCLE_2_USE_CASES = [
    {
        "id": "CU10",
        "name": "CU10 Realizar Reserva de Prendas",
        "filename": "comunicacion-cu10-realizar-reserva-prendas.png",
        "actor": "Cliente",
        "boundary": "UI_ReservaPrenda",
        "control": "ReservaPrendaController",
        "entity": "Reserva",
        "msg_link1": (
            "1: seleccionarPrendaParaReserva(prenda_id, talla, sucursal_id)\n"
            "2: confirmarDatosReserva(cliente_id, fecha_limite)\n"
            "3: enviarSolicitudReserva()"
        ),
        "msg_link2": (
            "1.1: validarStockDisponible(prenda_id, talla, sucursal_id)\n"
            "2.1: bloquearStockTemporal(variante_id, sucursal_id)\n"
            "3.1: procesarCreacionReserva(datos_reserva)"
        ),
        "msg_link3": (
            "1.2: checkStock(variante_id, sucursal_id)\n"
            "2.2: decrementarStockDisponible(variante_id, 1)\n"
            "3.2: createReserva(cliente_id, sucursal_id, fecha_limite)\n"
            "3.3: save(reserva)"
        ),
    },
    {
        "id": "CU11",
        "name": "CU11 Atender Reservas en Sucursal",
        "filename": "comunicacion-cu11-atender-reservas-sucursal.png",
        "actor": "Encargado de Sucursal",
        "boundary": "UI_AtencionReserva",
        "control": "AtencionReservaController",
        "entity": "Reserva",
        "msg_link1": (
            "1: listarReservasPendientes(sucursal_id)\n"
            "2: buscarReservaPorCodigo(codigo_reserva)\n"
            "3: registrarEntregaPrenda(reserva_id)\n"
            "4: cancelarReservaPorExpiracion(reserva_id)"
        ),
        "msg_link2": (
            "1.1: consultarReservasSucursal(sucursal_id, 'PENDIENTE')\n"
            "2.1: validarCodigoReserva(codigo_reserva)\n"
            "3.1: confirmarEntregaReserva(reserva_id)\n"
            "4.1: liberarStockReserva(reserva_id)"
        ),
        "msg_link3": (
            "1.2: findBySucursalAndEstado(sucursal_id, 'PENDIENTE')\n"
            "2.2: findByCodigo(codigo_reserva)\n"
            "3.2: setEstado('ENTREGADA')\n"
            "4.2: setEstado('CANCELADA')\n"
            "4.3: restaurarStockDisponible(variante_id)"
        ),
    },
    {
        "id": "CU13",
        "name": "CU13 Administrar Carrito de Compras",
        "filename": "comunicacion-cu13-administrar-carrito-compras.png",
        "actor": "Cliente",
        "boundary": "UI_CarritoCompras",
        "control": "CarritoComprasController",
        "entity": "Carrito",
        "msg_link1": (
            "1: agregarPrendaCarrito(prenda_id, talla, cantidad)\n"
            "2: actualizarCantidadItem(item_id, nueva_cantidad)\n"
            "3: eliminarItemCarrito(item_id)\n"
            "4: vaciarCarritoCompras()"
        ),
        "msg_link2": (
            "1.1: validarItemStock(prenda_id, talla, cantidad)\n"
            "2.1: modificarCantidadItem(item_id, nueva_cantidad)\n"
            "3.1: removerItemCarrito(item_id)\n"
            "4.1: limpiarCarrito(cliente_id)"
        ),
        "msg_link3": (
            "1.2: findByClienteId(cliente_id)\n"
            "1.3: addItem(variante_id, cantidad, precio_unit)\n"
            "2.2: updateItemCantidad(item_id, nueva_cantidad)\n"
            "3.2: deleteItem(item_id)\n"
            "4.2: clearItems(carrito_id)"
        ),
    },
    {
        "id": "CU14",
        "name": "CU14 Realizar Compra Digital",
        "filename": "comunicacion-cu14-realizar-compra-digital.png",
        "actor": "Cliente",
        "boundary": "UI_CheckoutDigital",
        "control": "CompraDigitalController",
        "entity": "Venta",
        "msg_link1": (
            "1: iniciarCheckout(carrito_id)\n"
            "2: seleccionarDireccionEnvio(direccion_id)\n"
            "3: seleccionarMetodoPago('STRIPE_ONLINE')\n"
            "4: confirmarOrdenCompra()"
        ),
        "msg_link2": (
            "1.1: verificarItemsValidos(carrito_id)\n"
            "2.1: calcularCostoEnvio(direccion_id)\n"
            "3.1: prepararTransaccionPago(monto_total)\n"
            "4.1: procesarCreacionVenta(datos_checkout)"
        ),
        "msg_link3": (
            "1.2: getCarritoWithPrendas(carrito_id)\n"
            "4.2: createVenta(cliente_id, 'DIGITAL', total)\n"
            "4.3: createDetallesVenta(items)\n"
            "4.4: save(venta)"
        ),
    },
    {
        "id": "CU15",
        "name": "CU15 Realizar Venta Presencial (POS)",
        "filename": "comunicacion-cu15-realizar-venta-presencial-pos.png",
        "actor": "Cajero",
        "boundary": "UI_PuntoVentaPOS",
        "control": "VentaPOSController",
        "entity": "Venta",
        "msg_link1": (
            "1: escanearCodigoBarra(codigo_barra)\n"
            "2: identificarCliente(ci_nit)\n"
            "3: aplicarDescuentoManual(porcentaje)\n"
            "4: cerrarVentaPresencial()"
        ),
        "msg_link2": (
            "1.1: buscarPrendaPorCodigo(codigo_barra)\n"
            "2.1: buscarOcrearCliente(ci_nit)\n"
            "3.1: recalcularTotalVenta(subtotal, porcentaje)\n"
            "4.1: registrarVentaFisica(datos_venta)"
        ),
        "msg_link3": (
            "1.2: findByBarcode(codigo_barra)\n"
            "2.2: findClienteByNIT(ci_nit)\n"
            "4.2: createVenta(cajero_id, sucursal_id, 'POS')\n"
            "4.3: saveDetalles(items)\n"
            "4.4: descontarStockFisico(sucursal_id, items)"
        ),
    },
    {
        "id": "CU16",
        "name": "CU16 Cobro en Caja",
        "filename": "comunicacion-cu16-cobro-en-caja.png",
        "actor": "Cajero",
        "boundary": "UI_CobroCaja",
        "control": "CobroCajaController",
        "entity": "Pago",
        "msg_link1": (
            "1: seleccionarFormaPago(tipo_pago, monto)\n"
            "2: ingresarEfectivoRecibido(monto_efectivo)\n"
            "3: procesarCobroTarjetaOQR(comprobante_ext)\n"
            "4: emitirFacturaComprobante(venta_id)"
        ),
        "msg_link2": (
            "1.1: validarMontoCubierto(total_venta, monto)\n"
            "2.1: calcularCambioEfectivo(monto_efectivo, total)\n"
            "3.1: registrarCobro(venta_id, tipo_pago, monto)\n"
            "4.1: generarFacturaFiscal(venta_id)"
        ),
        "msg_link3": (
            "3.2: createPago(venta_id, metodo_pago, monto)\n"
            "3.3: setEstadoPago('PAGADO')\n"
            "3.4: save(pago)\n"
            "4.2: updateVentaEstado(venta_id, 'COMPLETADA')"
        ),
    },
    {
        "id": "CU17",
        "name": "CU17 Procesar Pago Electrónico Sandbox",
        "filename": "comunicacion-cu17-procesar-pago-electronico-sandbox.png",
        "actor": "Pasarela de Pagos",
        "boundary": "UI_PasarelaPago",
        "control": "PasarelaPagoController",
        "entity": "Pago",
        "msg_link1": (
            "1: enviarTokenPago(card_token, monto)\n"
            "2: solicitarAutorizacionSandbox(transaccion_id)\n"
            "3: notificarWebhookResultado(payload_webhook)"
        ),
        "msg_link2": (
            "1.1: conectarServicioStripe(card_token, monto)\n"
            "2.1: verificarRespuestaGateway(gateway_code)\n"
            "3.1: procesarConfirmacionPago(payload)"
        ),
        "msg_link3": (
            "1.2: createTransaccion(monto, 'STRIPE')\n"
            "3.2: findByTransaccionId(transaccion_id)\n"
            "3.3: setEstado('CONFIRMADO')\n"
            "3.4: update(pago)"
        ),
    },
    {
        "id": "CU18",
        "name": "CU18 Control de Stock y Movimientos",
        "filename": "comunicacion-cu18-control-stock-movimientos.png",
        "actor": "Encargado de Sucursal",
        "boundary": "UI_InventarioStock",
        "control": "InventarioStockController",
        "entity": "MovimientoInventario",
        "msg_link1": (
            "1: consultarStockSucursal(sucursal_id, filtros)\n"
            "2: registrarIngresoMercaderia(lote_prendas, proveedor_id)\n"
            "3: registrarTrasladoEntreSucursales(origen, destino, prendas)\n"
            "4: registrarAjusteInventario(motivo, diferencia)"
        ),
        "msg_link2": (
            "1.1: listarExistencias(sucursal_id, filtros)\n"
            "2.1: procesarEntradaStock(lote_prendas)\n"
            "3.1: procesarTransferenciaStock(origen, destino, prendas)\n"
            "4.1: procesarAjusteFisico(sucursal_id, ajuste)"
        ),
        "msg_link3": (
            "1.2: getStockPorSucursal(sucursal_id)\n"
            "2.2: createMovimiento('INGRESO', lote_prendas)\n"
            "2.3: incrementarStock(sucursal_id, lote_prendas)\n"
            "3.2: createMovimiento('TRASLADO', origen, destino)\n"
            "4.2: createMovimiento('AJUSTE', motivo, diferencia)\n"
            "4.3: save(movimientoInventario)"
        ),
    },
    {
        "id": "CU19",
        "name": "CU19 Gestionar Temporadas y Colecciones",
        "filename": "comunicacion-cu19-gestionar-temporadas-colecciones.png",
        "actor": "Administrador",
        "boundary": "UI_GestionTemporadas",
        "control": "TemporadaController",
        "entity": "Temporada",
        "msg_link1": (
            "1: consultarTemporadas(anio, vigencia)\n"
            "2: crearTemporada(nombre, fecha_inicio, fecha_fin)\n"
            "3: asociarPrendasColeccion(temporada_id, prendas_ids)\n"
            "4: activarTemporadaPrincipal(temporada_id)"
        ),
        "msg_link2": (
            "1.1: listarTemporadas(anio, vigencia)\n"
            "2.1: validarRangoFechas(fecha_inicio, fecha_fin)\n"
            "3.1: vincularPrendas(temporada_id, prendas_ids)\n"
            "4.1: establecerTemporadaActiva(temporada_id)"
        ),
        "msg_link3": (
            "1.2: findByAnio(anio)\n"
            "2.2: save(temporada)\n"
            "3.2: addPrendasToTemporada(temporada_id, prendas_ids)\n"
            "4.2: desactivarOtrasTemporadas()\n"
            "4.3: setEstado('ACTIVA')"
        ),
    },
]

def generate_diagram_group(rep, project, parent_pkg, group_name, uc_list):
    """Crea un subpaquete en EA y genera sus diagramas de comunicación BCE."""
    print(f"\n==========================================")
    print(f"  Procesando: {group_name}")
    print(f"==========================================")

    # Buscar o crear el subpaquete
    target_pkg = None
    for i in range(parent_pkg.Packages.Count):
        p = parent_pkg.Packages.GetAt(i)
        if p.Name == group_name:
            target_pkg = p
            break

    if target_pkg is None:
        target_pkg = parent_pkg.Packages.AddNew(group_name, "")
        target_pkg.Update()
        parent_pkg.Packages.Refresh()

    elements_cache = {}

    def get_or_create_element(name, elem_type, stereotype=""):
        key = f"{name}_{elem_type}_{stereotype}"
        if key in elements_cache:
            return elements_cache[key]
        for i in range(target_pkg.Elements.Count):
            el = target_pkg.Elements.GetAt(i)
            if el.Name == name and el.Type == elem_type:
                elements_cache[key] = el
                return el

        el = target_pkg.Elements.AddNew(name, elem_type)
        if stereotype:
            el.Stereotype = stereotype
        el.Update()
        elements_cache[key] = el
        return el

    for uc in uc_list:
        diag_name = uc["name"]
        print(f"  -> Generando diagrama: {diag_name}...")

        # Buscar si el diagrama ya existe para reutilizarlo o crearlo nuevo
        diag = None
        for i in range(target_pkg.Diagrams.Count):
            d = target_pkg.Diagrams.GetAt(i)
            if d.Name == diag_name:
                diag = d
                break

        if diag is None:
            diag = target_pkg.Diagrams.AddNew(diag_name, "Communication")
            diag.Update()
            target_pkg.Diagrams.Refresh()

        # Configurar marco UML 2.5
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # Limpiar objetos previos del diagrama para redibujar limpios
        while diag.DiagramObjects.Count > 0:
            diag.DiagramObjects.Delete(0)
        diag.DiagramObjects.Refresh()

        while diag.DiagramLinks.Count > 0:
            diag.DiagramLinks.Delete(0)
        diag.DiagramLinks.Refresh()

        # Crear o recuperar elementos BCE
        actor = get_or_create_element(uc["actor"], "Actor")
        boundary = get_or_create_element(uc["boundary"], "Class", "boundary")
        control = get_or_create_element(uc["control"], "Class", "control")
        entity = get_or_create_element(uc["entity"], "Class", "entity")

        # Disposición horizontal alineada
        elements_layout = [
            (actor, 50, 130, -100, -180),
            (boundary, 380, 470, -100, -180),
            (control, 720, 810, -100, -180),
            (entity, 1060, 1150, -100, -180),
        ]

        for el, l, r, t, b in elements_layout:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = l
            obj.right = r
            obj.top = t
            obj.bottom = b
            obj.Update()

        diag.DiagramObjects.Refresh()

        # Conector dirigido izquierda -> derecha
        def add_directed_connector(src, dst):
            # Verificar si ya existe conector
            conn = None
            for c_idx in range(src.Connectors.Count):
                c = src.Connectors.GetAt(c_idx)
                if c.SupplierID == dst.ElementID:
                    conn = c
                    break

            if conn is None:
                conn = src.Connectors.AddNew("", "Association")
                conn.SupplierID = dst.ElementID
                conn.Direction = "Source -> Destination"
                conn.Update()
                src.Connectors.Refresh()

            lnk = diag.DiagramLinks.AddNew("", "")
            lnk.ConnectorID = conn.ConnectorID
            lnk.Update()
            return conn

        add_directed_connector(actor, boundary)
        add_directed_connector(boundary, control)
        add_directed_connector(control, entity)

        # Textos multilínea con mensajes sobre conectores
        t1 = target_pkg.Elements.AddNew(uc["msg_link1"], "Text")
        t1.Notes = uc["msg_link1"]
        t1.Update()
        obj_t1 = diag.DiagramObjects.AddNew("", "")
        obj_t1.ElementID = t1.ElementID
        obj_t1.left = 140
        obj_t1.right = 375
        obj_t1.top = -30
        obj_t1.bottom = -115
        obj_t1.Update()

        t2 = target_pkg.Elements.AddNew(uc["msg_link2"], "Text")
        t2.Notes = uc["msg_link2"]
        t2.Update()
        obj_t2 = diag.DiagramObjects.AddNew("", "")
        obj_t2.ElementID = t2.ElementID
        obj_t2.left = 480
        obj_t2.right = 715
        obj_t2.top = -30
        obj_t2.bottom = -115
        obj_t2.Update()

        t3 = target_pkg.Elements.AddNew(uc["msg_link3"], "Text")
        t3.Notes = uc["msg_link3"]
        t3.Update()
        obj_t3 = diag.DiagramObjects.AddNew("", "")
        obj_t3.ElementID = t3.ElementID
        obj_t3.left = 820
        obj_t3.right = 1055
        obj_t3.top = -15
        obj_t3.bottom = -115
        obj_t3.Update()

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        rep.SaveDiagram(diag.DiagramID)

        # Exportar a PNG
        export_path = os.path.join(EXPORT_DIR, uc["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
        print(f"     Guardado PNG: {export_path}")


CYCLE_3_USE_CASES = [
    {
        "id": "CU12",
        "name": "CU12 Sesion de Probador Virtual",
        "filename": "comunicacion-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "boundary": "UI_VestidorVirtual",
        "control": "VestidorVirtualController",
        "entity": "SesionVestidorVirtual",
        "msg_link1": (
            "1: iniciarSesionProbador(cliente_id, dispositivo)\n"
            "2: seleccionarPrenda(prenda_id, talla)\n"
            "3: procesarAjusteVirtual(pose_data)\n"
            "4: finalizarSesionProbador(sesion_id)"
        ),
        "msg_link2": (
            "1.1: iniciarSesion(cliente_id, dispositivo)\n"
            "2.1: cargarModeloPrenda(prenda_id, talla)\n"
            "3.1: calcularAjuste(pose_data)\n"
            "4.1: cerrarSesion(sesion_id)"
        ),
        "msg_link3": (
            "1.2: createSession(cliente_id, dispositivo)\n"
            "1.3: save(sesion)\n"
            "2.2: findByPrendaId(prenda_id)\n"
            "3.2: updatePuntosClave(pose_data)\n"
            "4.2: findById(sesion_id)\n"
            "4.3: setEstado('FINALIZADA')"
        ),
    },
    {
        "id": "CU20",
        "name": "CU20 Gestionar Promociones",
        "filename": "comunicacion-cu20-gestionar-promociones.png",
        "actor": "Administrador",
        "boundary": "UI_Promocion",
        "control": "PromocionController",
        "entity": "Promocion",
        "msg_link1": (
            "1: consultarPromociones(filtro)\n"
            "2: registrarPromocion(solicitud)\n"
            "3: modificarPromocion(id, solicitud)\n"
            "4: cambiarEstadoPromocion(id, estado)"
        ),
        "msg_link2": (
            "1.1: listarPromociones(filtro)\n"
            "2.1: crearPromocion(solicitud)\n"
            "3.1: actualizarPromocion(id, solicitud)\n"
            "4.1: modificarEstado(id, estado)"
        ),
        "msg_link3": (
            "1.2: buscarConFiltros(filtro)\n"
            "2.2: validarVigencia(fechas)\n"
            "2.3: save(promocion)\n"
            "3.2: findById(id)\n"
            "3.3: update(promocion)\n"
            "4.2: findById(id)\n"
            "4.3: setEstado(estado)"
        ),
    },
    {
        "id": "CU21",
        "name": "CU21 Gestionar Reportes y Dashboards",
        "filename": "comunicacion-cu21-gestionar-reportes.png",
        "actor": "Administrador",
        "boundary": "UI_Reporte",
        "control": "ReporteController",
        "entity": "Reporte",
        "msg_link1": (
            "1: consultarDashboard(periodo, sucursal_id)\n"
            "2: filtrarPorCategoria(categoria_id)\n"
            "3: exportarReporteExcel(tipo, periodo)\n"
            "4: exportarReportePDF(tipo, periodo)"
        ),
        "msg_link2": (
            "1.1: resumenDashboard(periodo, sucursal_id)\n"
            "2.1: filtrarMetricas(categoria_id)\n"
            "3.1: generarExcel(tipo, periodo)\n"
            "4.1: generarPdf(tipo, periodo)"
        ),
        "msg_link3": (
            "1.2: calcularMetricasVentas(periodo)\n"
            "1.3: queryVentasPorSucursal(sucursal_id)\n"
            "2.2: queryProductosMasVendidos(categoria_id)\n"
            "3.2: buildExcelWorkbook(datos)\n"
            "4.2: renderPdfDocument(datos)"
        ),
    },
    {
        "id": "CU22",
        "name": "CU22 Obtener Recomendaciones con IA",
        "filename": "comunicacion-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "boundary": "UI_Recomendacion",
        "control": "RecomendacionController",
        "entity": "RecomendacionIA",
        "msg_link1": (
            "1: solicitarRecomendaciones(cliente_id)\n"
            "2: filtrarPorTemporada(temporada_id)\n"
            "3: verDetalleRecomendado(producto_id)\n"
            "4: registrarInteraccion(feedback_data)"
        ),
        "msg_link2": (
            "1.1: obtenerRecomendaciones(cliente_id)\n"
            "2.1: filtrarCatalogoRecomendado(temporada_id)\n"
            "3.1: consultarDetalleProducto(producto_id)\n"
            "4.1: registrarFeedback(feedback_data)"
        ),
        "msg_link3": (
            "1.2: calcularAfinidades(cliente_id)\n"
            "1.3: rankCatalogByStock()\n"
            "2.2: filterByTemporada(temporada_id)\n"
            "3.2: findById(producto_id)\n"
            "4.2: save(interaccion)\n"
            "4.3: updateScoreModel(feedback_data)"
        ),
    },
    {
        "id": "CU23",
        "name": "CU23 Consultar Historial de Compras",
        "filename": "comunicacion-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "boundary": "UI_HistorialCompras",
        "control": "HistorialComprasController",
        "entity": "Venta",
        "msg_link1": (
            "1: consultarCompras(cliente_id, filtro)\n"
            "2: verDetalleCompra(venta_id)\n"
            "3: descargarComprobante(pago_id)\n"
            "4: filtrarPorEstado(estado)"
        ),
        "msg_link2": (
            "1.1: listarComprasCliente(cliente_id, filtro)\n"
            "2.1: obtenerDetalleVenta(venta_id)\n"
            "3.1: generarComprobante(pago_id)\n"
            "4.1: filtrarVentas(estado)"
        ),
        "msg_link3": (
            "1.2: findByClienteId(cliente_id)\n"
            "1.3: buscarConFiltros(filtro)\n"
            "2.2: findById(venta_id)\n"
            "2.3: getDetallesVenta(venta_id)\n"
            "3.2: getPaymentDetails(pago_id)\n"
            "4.2: filterByEstado(estado)"
        ),
    },
]


def main():
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)
    time.sleep(1)

    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE COMUNICACIÓN (TODOS LOS CICLOS 1, 2 Y 3) — FASHIONSTORE")
    print("=" * 75)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    try:
        project = rep.GetProjectInterface()
        root_model = rep.Models.GetAt(0)  # Model

        pkg_name = "03 - Diagramas de Comunicación"

        # Buscar si ya existe el paquete para recrearlo limpio
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if "Diagramas de Comunicación" in p.Name:
                print(f"Limpiando paquete previo: {p.Name}")
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        main_com_pkg = root_model.Packages.AddNew(pkg_name, "")
        main_com_pkg.Notes = (
            "Diagramas de Comunicación / Análisis de Robustez BCE (UML 2.5) "
            "organizados por ciclos para todos los 23 Casos de Uso del sistema FashionStore."
        )
        main_com_pkg.Update()
        root_model.Packages.Refresh()

        print(f"Paquete contenedor creado: '{main_com_pkg.Name}' (ID: {main_com_pkg.PackageID})")

        # 1. Generar Ciclo 1 (CU01 al CU09)
        generate_diagram_group(
            rep, project, main_com_pkg,
            "Ciclo 1 - Catálogo y Base",
            CYCLE_1_USE_CASES
        )

        # 2. Generar Ciclo 2 (CU10 al CU19)
        generate_diagram_group(
            rep, project, main_com_pkg,
            "Ciclo 2 - Operación Comercial y Logística",
            CYCLE_2_USE_CASES
        )

        # 3. Generar Ciclo 3 (CU12, CU20 al CU23)
        generate_diagram_group(
            rep, project, main_com_pkg,
            "Ciclo 3 - Innovación y Analítica",
            CYCLE_3_USE_CASES
        )

        rep.SaveAllDiagrams()
        print("\n" + "=" * 75)
        print("¡TODOS LOS DIAGRAMAS DE COMUNICACIÓN DE CICLOS 1, 2 Y 3 FUERON GENERADOS!")
        print("=" * 75)
        return 0

    except Exception as e:
        print(f"ERROR: {e}")
        traceback.print_exc()
        return 1
    finally:
        rep.CloseFile()
        del rep


if __name__ == "__main__":
    sys.exit(main())
