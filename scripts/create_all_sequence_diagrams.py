"""
Generador de Diagramas de Secuencia (UML 2.5) para Ciclo 1, Ciclo 2 y Ciclo 3
del sistema FashionStore en Enterprise Architect.

Basado en el estándar UML 2.5 y el modelo formal:
- Marco UML 2.5 con etiqueta pentagonal 'sd CUxx [Nombre]'
- Participantes horizontales: Actor -> Vistas (V.xxx) -> Controller (xxxController) -> Modelos (M.xxx)
- Fragmentos combinados ('alt') que dividen los flujos y casos de uso
- Mensajes síncronos y mensajes de retorno 'return()' con flechas discontinuas
- Subpaquetes organizados: Ciclo 1, Ciclo 2 y Ciclo 3
- Exportación a PNG de alta resolución
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

# ─────────────────────────────────────────────────────────────
# DEFINICIÓN DE CASOS DE USO — CICLO 1 (9 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_1_SEQUENCE = [
    {
        "id": "CU01",
        "diagram_name": "CU01 Registrar Cliente",
        "filename": "secuencia-cu01-registrar-cliente.png",
        "actor": "Invitado",
        "views": ["V.RegistroCliente", "V.TerminosCondiciones", "V.ConfirmacionRegistro"],
        "controller": "RegistroClienteController",
        "models": ["M.Cliente", "M.Usuario", "M.Bitacora"],
        "fragments": [
            {
                "name": "verificarEmail",
                "messages": [
                    ("actor", "controller", "verify_email_available(email)", False),
                    ("controller", "m2", "find_by_email()", False),
                    ("m2", "controller", "return(disponible)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "registrarCliente",
                "messages": [
                    ("actor", "controller", "register_client(datos)", False),
                    ("controller", "m2", "create_user()", False),
                    ("m2", "controller", "return(user_id)", True),
                    ("controller", "m1", "create_client()", False),
                    ("m1", "controller", "return(cliente)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cancelarRegistro",
                "messages": [
                    ("actor", "controller", "cancel_registration()", False),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU02",
        "diagram_name": "CU02 Iniciar y Cerrar Sesion",
        "filename": "secuencia-cu02-iniciar-cerrar-sesion.png",
        "actor": "Usuario",
        "views": ["V.Login", "V.DashboardUsuario", "V.RecuperarPassword"],
        "controller": "LoginController",
        "models": ["M.SesionUsuario", "M.Usuario", "M.Bitacora"],
        "fragments": [
            {
                "name": "autenticarCredenciales",
                "messages": [
                    ("actor", "controller", "login(email, password)", False),
                    ("controller", "m2", "validate_credentials()", False),
                    ("m2", "controller", "return(user)", True),
                    ("controller", "m1", "create_session(jwt)", False),
                    ("m1", "controller", "return(token)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "recuperarPassword",
                "messages": [
                    ("actor", "controller", "request_password_reset(email)", False),
                    ("controller", "m2", "generate_reset_token()", False),
                    ("m2", "controller", "return(ok)", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cerrarSesion",
                "messages": [
                    ("actor", "controller", "logout()", False),
                    ("controller", "m1", "revoke_session()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU03",
        "diagram_name": "CU03 Gestionar Usuarios y Roles",
        "filename": "secuencia-cu03-gestionar-usuarios-roles.png",
        "actor": "Administrador",
        "views": ["V.ListadoUsuarios", "V.FormularioUsuario", "V.AsignarRolSucursal"],
        "controller": "UsuarioController",
        "models": ["M.Usuario", "M.Rol", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarUsuarios",
                "messages": [
                    ("actor", "controller", "get_users()", False),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(usuarios)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "crearUsuario",
                "messages": [
                    ("actor", "controller", "create_user(datos)", False),
                    ("controller", "m2", "find_by_id(rol_id)", False),
                    ("m2", "controller", "return(rol)", True),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(user)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "modificarUsuario",
                "messages": [
                    ("actor", "controller", "update_user(id, datos)", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return(user)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "cambiarEstado",
                "messages": [
                    ("actor", "controller", "toggle_status(id)", False),
                    ("controller", "m1", "update_status()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU04",
        "diagram_name": "CU04 Gestionar Sucursales y Ciudades",
        "filename": "secuencia-cu04-gestionar-sucursales-ciudades.png",
        "actor": "Administrador",
        "views": ["V.ListadoSucursales", "V.FormularioSucursal", "V.MapaUbicacion"],
        "controller": "SucursalController",
        "models": ["M.Sucursal", "M.Ciudad", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarSucursales",
                "messages": [
                    ("actor", "controller", "get_branches()", False),
                    ("controller", "m2", "find_all()", False),
                    ("m2", "controller", "return(ciudades)", True),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(sucursales)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "registrarSucursal",
                "messages": [
                    ("actor", "controller", "create_branch(datos)", False),
                    ("controller", "m2", "find_by_id(ciudad_id)", False),
                    ("m2", "controller", "return(ciudad)", True),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(branch)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "actualizarCoordenadas",
                "messages": [
                    ("actor", "controller", "update_coords(id, lat, lng)", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "desactivarSucursal",
                "messages": [
                    ("actor", "controller", "deactivate_branch(id)", False),
                    ("controller", "m1", "update_status()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU05",
        "diagram_name": "CU05 Gestionar Productos y Prendas",
        "filename": "secuencia-cu05-gestionar-productos-prendas.png",
        "actor": "Administrador",
        "views": ["V.CatalogoAdmin", "V.CrearPrenda", "V.GestionVariantes"],
        "controller": "PrendaController",
        "models": ["M.Producto", "M.VarianteProducto", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarPrendas",
                "messages": [
                    ("actor", "controller", "get_products()", False),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(productos)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "crearPrenda",
                "messages": [
                    ("actor", "controller", "create_product(datos)", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(product_id)", True),
                    ("controller", "m2", "create_variants()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "actualizarVariante",
                "messages": [
                    ("actor", "controller", "update_variant(id, stock, sku)", False),
                    ("controller", "m2", "update()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cambiarEstado",
                "messages": [
                    ("actor", "controller", "toggle_product_status(id)", False),
                    ("controller", "m1", "update_status()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU06",
        "diagram_name": "CU06 Gestionar Catalogo Base",
        "filename": "secuencia-cu06-gestionar-catalogo-base.png",
        "actor": "Administrador",
        "views": ["V.GestionCategorias", "V.GestionTallas", "V.GestionColores"],
        "controller": "CatalogoBaseController",
        "models": ["M.Categoria", "M.Talla", "M.Color"],
        "fragments": [
            {
                "name": "listarCategorias",
                "messages": [
                    ("actor", "controller", "get_categories()", False),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(categorias)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "crearCategoria",
                "messages": [
                    ("actor", "controller", "create_category(datos)", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(cat)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "gestionarTallas",
                "messages": [
                    ("actor", "controller", "save_sizes(sizes)", False),
                    ("controller", "m2", "batch_create()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "gestionarColores",
                "messages": [
                    ("actor", "controller", "save_colors(colors)", False),
                    ("controller", "m3", "batch_create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU07",
        "diagram_name": "CU07 Gestionar Proveedores",
        "filename": "secuencia-cu07-gestionar-proveedores.png",
        "actor": "Administrador",
        "views": ["V.ListadoProveedores", "V.FormularioProveedor", "V.HistorialSuministro"],
        "controller": "ProveedorController",
        "models": ["M.Proveedor", "M.OrdenCompra", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarProveedores",
                "messages": [
                    ("actor", "controller", "get_suppliers()", False),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(proveedores)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "registrarProveedor",
                "messages": [
                    ("actor", "controller", "create_supplier(datos)", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(supplier)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "consultarSuministros",
                "messages": [
                    ("actor", "controller", "get_supplies_history(id)", False),
                    ("controller", "m2", "find_by_supplier_id()", False),
                    ("m2", "controller", "return(ordenes)", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "actualizarProveedor",
                "messages": [
                    ("actor", "controller", "update_supplier(id, datos)", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU08",
        "diagram_name": "CU08 Consultar Catalogo y Buscar Prendas",
        "filename": "secuencia-cu08-consultar-catalogo-buscar-prendas.png",
        "actor": "Cliente",
        "views": ["V.CatalogoPublico", "V.FiltrosPrendas", "V.DetallePrenda"],
        "controller": "CatalogoExploracionController",
        "models": ["M.Producto", "M.VarianteProducto", "M.Categoria"],
        "fragments": [
            {
                "name": "cargarCatalogo",
                "messages": [
                    ("actor", "controller", "browse_catalog()", False),
                    ("controller", "m3", "find_active()", False),
                    ("m3", "controller", "return(categorias)", True),
                    ("controller", "m1", "find_featured()", False),
                    ("m1", "controller", "return(prendas)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "filtrarYBuscar",
                "messages": [
                    ("actor", "controller", "search_catalog(filtros)", False),
                    ("controller", "m1", "query_by_criteria()", False),
                    ("m1", "controller", "return(resultados)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "verFichaTecnica",
                "messages": [
                    ("actor", "controller", "get_product_detail(id)", False),
                    ("controller", "m1", "find_by_id()", False),
                    ("m1", "controller", "return(prenda)", True),
                    ("controller", "m2", "find_variants()", False),
                    ("m2", "controller", "return(variantes)", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU09",
        "diagram_name": "CU09 Consultar Disponibilidad en Tiendas",
        "filename": "secuencia-cu09-consultar-disponibilidad-tiendas.png",
        "actor": "Cliente",
        "views": ["V.SelectorPrendaTalla", "V.MapaStockSucursales", "V.DetalleTienda"],
        "controller": "DisponibilidadStockController",
        "models": ["M.Inventario", "M.Sucursal", "M.VarianteProducto"],
        "fragments": [
            {
                "name": "seleccionarVariante",
                "messages": [
                    ("actor", "controller", "select_variant(prenda_id, talla, color)", False),
                    ("controller", "m3", "find_sku()", False),
                    ("m3", "controller", "return(variante)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "consultarStock",
                "messages": [
                    ("actor", "controller", "check_stock_all_branches(variante_id)", False),
                    ("controller", "m1", "get_stock_by_variant()", False),
                    ("m1", "controller", "return(stock_list)", True),
                    ("controller", "m2", "get_branch_info()", False),
                    ("m2", "controller", "return(branches)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "verDetalleTienda",
                "messages": [
                    ("actor", "controller", "get_branch_details(branch_id)", False),
                    ("controller", "m2", "find_by_id()", False),
                    ("m2", "controller", "return(sucursal)", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# DEFINICIÓN DE CASOS DE USO — CICLO 2 (9 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_2_SEQUENCE = [
    {
        "id": "CU10",
        "diagram_name": "CU10 Realizar Reserva de Prendas",
        "filename": "secuencia-cu10-realizar-reserva-prendas.png",
        "actor": "Cliente",
        "views": ["V.FichaReserva", "V.SeleccionSucursal", "V.ConfirmacionTicket"],
        "controller": "ReservaPrendaController",
        "models": ["M.Reserva", "M.Inventario", "M.Bitacora"],
        "fragments": [
            {
                "name": "seleccionarSucursal",
                "messages": [
                    ("actor", "controller", "check_branch_availability(branch_id, items)", False),
                    ("controller", "m2", "validate_stock()", False),
                    ("m2", "controller", "return(disponible)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "confirmarReserva",
                "messages": [
                    ("actor", "controller", "create_reservation(datos)", False),
                    ("controller", "m2", "lock_stock()", False),
                    ("m2", "controller", "return(ok)", True),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(reserva)", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cancelarReserva",
                "messages": [
                    ("actor", "controller", "cancel_reservation(code)", False),
                    ("controller", "m1", "update_status('CANCELADA')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "unlock_stock()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU11",
        "diagram_name": "CU11 Atender Reservas en Sucursal",
        "filename": "secuencia-cu11-atender-reservas-sucursal.png",
        "actor": "Encargado de Sucursal",
        "views": ["V.ListadoReservas", "V.ValidacionCodigo", "V.EntregaReserva"],
        "controller": "AtencionReservaController",
        "models": ["M.Reserva", "M.Inventario", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarPendientes",
                "messages": [
                    ("actor", "controller", "get_pending_reservations(branch_id)", False),
                    ("controller", "m1", "find_by_branch_and_status()", False),
                    ("m1", "controller", "return(reservas)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "buscarPorCodigo",
                "messages": [
                    ("actor", "controller", "verify_reservation_code(code)", False),
                    ("controller", "m1", "find_by_code()", False),
                    ("m1", "controller", "return(reserva)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "entregarPrenda",
                "messages": [
                    ("actor", "controller", "deliver_reservation(reserva_id)", False),
                    ("controller", "m1", "update_status('ENTREGADA')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "liberarExpirada",
                "messages": [
                    ("actor", "controller", "expire_reservation(reserva_id)", False),
                    ("controller", "m1", "update_status('EXPIRADA')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "unlock_stock()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU13",
        "diagram_name": "CU13 Administrar Carrito de Compras",
        "filename": "secuencia-cu13-administrar-carrito-compras.png",
        "actor": "Cliente",
        "views": ["V.CarritoDrawer", "V.ResumenPedido", "V.AlertaStock"],
        "controller": "CarritoComprasController",
        "models": ["M.Carrito", "M.ItemCarrito", "M.VarianteProducto"],
        "fragments": [
            {
                "name": "agregarItem",
                "messages": [
                    ("actor", "controller", "add_item(variante_id, cantidad)", False),
                    ("controller", "m3", "check_stock()", False),
                    ("m3", "controller", "return(stock)", True),
                    ("controller", "m1", "get_or_create_cart()", False),
                    ("m1", "controller", "return(cart)", True),
                    ("controller", "m2", "create_or_update_item()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "modificarCantidad",
                "messages": [
                    ("actor", "controller", "update_quantity(item_id, qty)", False),
                    ("controller", "m2", "update()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "recalculate_totals()", False),
                    ("m1", "controller", "return(cart)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "eliminarItem",
                "messages": [
                    ("actor", "controller", "remove_item(item_id)", False),
                    ("controller", "m2", "delete()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "vaciarCarrito",
                "messages": [
                    ("actor", "controller", "clear_cart()", False),
                    ("controller", "m2", "clear_items()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU14",
        "diagram_name": "CU14 Realizar Compra Digital",
        "filename": "secuencia-cu14-realizar-compra-digital.png",
        "actor": "Cliente",
        "views": ["V.CheckoutEnvio", "V.MetodoPagoDigital", "V.ComprobanteCompra"],
        "controller": "CompraDigitalController",
        "models": ["M.Venta", "M.DetalleVenta", "M.Pago"],
        "fragments": [
            {
                "name": "iniciarCheckout",
                "messages": [
                    ("actor", "controller", "init_checkout()", False),
                    ("controller", "m1", "validate_cart_checkout()", False),
                    ("m1", "controller", "return(summary)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "seleccionarEnvio",
                "messages": [
                    ("actor", "controller", "set_shipping_address(direccion)", False),
                    ("controller", "m1", "calculate_shipping_cost()", False),
                    ("m1", "controller", "return(cost)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "confirmarVenta",
                "messages": [
                    ("actor", "controller", "create_digital_sale(datos)", False),
                    ("controller", "m1", "create(status='PENDING')", False),
                    ("m1", "controller", "return(venta_id)", True),
                    ("controller", "m2", "create_items()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m3", "create(status='PENDING')", False),
                    ("m3", "controller", "return(pago_id)", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU15",
        "diagram_name": "CU15 Realizar Venta Presencial POS",
        "filename": "secuencia-cu15-realizar-venta-presencial-pos.png",
        "actor": "Cajero",
        "views": ["V.PuntoVentaPOS", "V.BuscarClienteModal", "V.TicketVenta"],
        "controller": "VentaPOSController",
        "models": ["M.Venta", "M.DetalleVenta", "M.Inventario"],
        "fragments": [
            {
                "name": "escanearCodigo",
                "messages": [
                    ("actor", "controller", "scan_barcode(code)", False),
                    ("controller", "m3", "find_by_barcode()", False),
                    ("m3", "controller", "return(variante)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "asociarCliente",
                "messages": [
                    ("actor", "controller", "find_or_create_client(nit_ci)", False),
                    ("controller", "m1", "find_client()", False),
                    ("m1", "controller", "return(client)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "completarVenta",
                "messages": [
                    ("actor", "controller", "complete_pos_sale(items, client_id)", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return(sale)", True),
                    ("controller", "m2", "batch_create_items()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m3", "decrease_stock()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cancelarVenta",
                "messages": [
                    ("actor", "controller", "void_sale_draft()", False),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU16",
        "diagram_name": "CU16 Cobro en Caja",
        "filename": "secuencia-cu16-cobro-en-caja.png",
        "actor": "Cajero",
        "views": ["V.SelectorFormaPago", "V.CalculoCambio", "V.FacturaFiscal"],
        "controller": "CobroCajaController",
        "models": ["M.Pago", "M.Venta", "M.Factura"],
        "fragments": [
            {
                "name": "seleccionarMetodo",
                "messages": [
                    ("actor", "controller", "select_payment_method(tipo)", False),
                    ("controller", "m2", "get_total_due()", False),
                    ("m2", "controller", "return(total)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "cobroEfectivo",
                "messages": [
                    ("actor", "controller", "process_cash_payment(monto_recibido)", False),
                    ("controller", "m1", "create(tipo='EFECTIVO')", False),
                    ("m1", "controller", "return(cambio)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "cobroTarjetaOQR",
                "messages": [
                    ("actor", "controller", "process_pos_payment(tipo, auth_code)", False),
                    ("controller", "m1", "create(tipo=tipo)", False),
                    ("m1", "controller", "return(pago)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "emitirFactura",
                "messages": [
                    ("actor", "controller", "generate_fiscal_invoice(pago_id)", False),
                    ("controller", "m3", "create_invoice()", False),
                    ("m3", "controller", "return(invoice)", True),
                    ("controller", "m2", "update_status('PAGADA')", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU17",
        "diagram_name": "CU17 Procesar Pago Electronico Sandbox",
        "filename": "secuencia-cu17-procesar-pago-electronico-sandbox.png",
        "actor": "Pasarela de Pagos",
        "views": ["V.StripeSandboxUI", "V.WebhookReceiver", "V.ConfirmacionPago"],
        "controller": "PasarelaPagoController",
        "models": ["M.Pago", "M.TransaccionGateway", "M.Venta"],
        "fragments": [
            {
                "name": "iniciarTransaccion",
                "messages": [
                    ("actor", "controller", "create_payment_intent(sale_id, amount)", False),
                    ("controller", "m3", "get_sale()", False),
                    ("m3", "controller", "return(sale)", True),
                    ("controller", "m2", "create(status='INIT')", False),
                    ("m2", "controller", "return(client_secret)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "procesarWebhook",
                "messages": [
                    ("actor", "controller", "handle_stripe_webhook(payload, sig)", False),
                    ("controller", "m2", "update_status('SUCCESS')", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "update_status('COMPLETED')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "update_status('PAID')", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "pagoFallido",
                "messages": [
                    ("actor", "controller", "handle_payment_failure(error)", False),
                    ("controller", "m2", "update_status('FAILED')", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU18",
        "diagram_name": "CU18 Control de Stock y Movimientos",
        "filename": "secuencia-cu18-control-stock-movimientos.png",
        "actor": "Encargado de Sucursal",
        "views": ["V.KardexInventario", "V.RegistrarMovimiento", "V.AjusteStockModal"],
        "controller": "InventarioStockController",
        "models": ["M.MovimientoInventario", "M.Inventario", "M.Bitacora"],
        "fragments": [
            {
                "name": "consultarKardex",
                "messages": [
                    ("actor", "controller", "get_stock_movements(branch_id)", False),
                    ("controller", "m1", "find_by_branch()", False),
                    ("m1", "controller", "return(movimientos)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "ingresoMercaderia",
                "messages": [
                    ("actor", "controller", "record_stock_entry(branch_id, items)", False),
                    ("controller", "m2", "increase_stock()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "create(tipo='INGRESO')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "trasladoEntreSucursales",
                "messages": [
                    ("actor", "controller", "transfer_stock(src, dst, items)", False),
                    ("controller", "m2", "transfer_stock()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "create(tipo='TRASLADO')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "ajusteFisico",
                "messages": [
                    ("actor", "controller", "adjust_physical_stock(branch_id, item_id, real_qty)", False),
                    ("controller", "m2", "set_physical_stock()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "create(tipo='AJUSTE')", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU19",
        "diagram_name": "CU19 Gestionar Temporadas y Colecciones",
        "filename": "secuencia-cu19-gestionar-temporadas-colecciones.png",
        "actor": "Administrador",
        "views": ["V.ListadoTemporadas", "V.CrearColeccion", "V.VincularPrendas"],
        "controller": "TemporadaController",
        "models": ["M.Temporada", "M.Coleccion", "M.Producto"],
        "fragments": [
            {
                "name": "listarTemporadas",
                "messages": [
                    ("actor", "controller", "get_seasons()", False),
                    ("controller", "m1", "find_all()", False),
                    ("m1", "controller", "return(temporadas)", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "crearColeccion",
                "messages": [
                    ("actor", "controller", "create_collection(temporada_id, datos)", False),
                    ("controller", "m2", "create()", False),
                    ("m2", "controller", "return(coleccion)", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "asociarPrendas",
                "messages": [
                    ("actor", "controller", "assign_products(coleccion_id, product_ids)", False),
                    ("controller", "m3", "batch_update_collection()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "activarTemporada",
                "messages": [
                    ("actor", "controller", "set_active_season(id)", False),
                    ("controller", "m1", "set_active()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# DEFINICIÓN DE CASOS DE USO — CICLO 3 (5 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_3_SEQUENCE = [
    {
        "id": "CU12",
        "diagram_name": "CU12 Sesion de Probador Virtual",
        "filename": "secuencia-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "views": ["V.index", "V.CapturaPose", "V.ResultadoVTON"],
        "controller": "VestidorVirtualController",
        "models": ["M.SesionVestidorVirtual", "M.Prenda", "M.Bitacora"],
        "fragments": [
            {
                "name": "iniciarSesionProbador",
                "messages": [
                    ("actor", "controller", "start_session()", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "seleccionarPrenda",
                "messages": [
                    ("actor", "controller", "selectPrenda()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "procesarAjusteVTON",
                "messages": [
                    ("actor", "controller", "vton_try_on()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "finalizarSesion",
                "messages": [
                    ("actor", "controller", "finish_session()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU20",
        "diagram_name": "CU20 Gestionar Promociones y Descuentos",
        "filename": "secuencia-cu20-gestionar-promociones.png",
        "actor": "Administrador",
        "views": ["V.index", "V.CrearPromocion", "V.DetallePromocion"],
        "controller": "PromocionController",
        "models": ["M.Promocion", "M.ProductoPromocion", "M.Bitacora"],
        "fragments": [
            {
                "name": "listarPromociones",
                "messages": [
                    ("actor", "controller", "index()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "registrarPromocion",
                "messages": [
                    ("actor", "controller", "store()", False),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "create()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "modificarPromocion",
                "messages": [
                    ("actor", "controller", "update()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "cambiarEstado",
                "messages": [
                    ("actor", "controller", "set_status()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU21",
        "diagram_name": "CU21 Gestionar Reportes y Dashboards",
        "filename": "secuencia-cu21-gestionar-reportes.png",
        "actor": "Administrador",
        "views": ["V.Dashboard", "V.FiltrosReporte", "V.AsistenteIA"],
        "controller": "ReporteController",
        "models": ["M.Reporte", "M.Venta", "M.Bitacora"],
        "fragments": [
            {
                "name": "consultarDashboard",
                "messages": [
                    ("actor", "controller", "dashboard()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "filtrarPorSucursal",
                "messages": [
                    ("actor", "controller", "sales_by_branch()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "asistenteIA",
                "messages": [
                    ("actor", "controller", "report_assistant()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "exportarReporte",
                "messages": [
                    ("actor", "controller", "export_report()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m3", "create()", False),
                    ("m3", "controller", "return()", True),
                ],
            },
        ],
    },
    {
        "id": "CU22",
        "diagram_name": "CU22 Obtener Recomendaciones con IA",
        "filename": "secuencia-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "views": ["V.CatalogoRecomendado", "V.DetalleRecomendacion", "V.FeedbackModal"],
        "controller": "RecomendacionController",
        "models": ["M.RecomendacionIA", "M.Prenda", "M.HistorialCliente"],
        "fragments": [
            {
                "name": "solicitarRecomendaciones",
                "messages": [
                    ("actor", "controller", "mine()", False),
                    ("controller", "m3", "get()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "m1", "create()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "filtrarPorTemporada",
                "messages": [
                    ("actor", "controller", "filterBySeason()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "verDetalleRecomendado",
                "messages": [
                    ("actor", "controller", "selectProduct()", False),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "registrarFeedback",
                "messages": [
                    ("actor", "controller", "record_feedback()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
        ],
    },
    {
        "id": "CU23",
        "diagram_name": "CU23 Consultar Historial de Compras",
        "filename": "secuencia-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "views": ["V.HistorialCompras", "V.DetalleCompra", "V.ComprobanteDigital"],
        "controller": "HistorialComprasController",
        "models": ["M.Venta", "M.DetalleVenta", "M.Pago"],
        "fragments": [
            {
                "name": "listarCompras",
                "messages": [
                    ("actor", "controller", "purchase_history()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v1", "view()", False),
                ],
            },
            {
                "name": "verDetalleCompra",
                "messages": [
                    ("actor", "controller", "purchase_detail()", False),
                    ("controller", "m1", "get()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "m2", "get()", False),
                    ("m2", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
            {
                "name": "descargarComprobante",
                "messages": [
                    ("actor", "controller", "download_receipt()", False),
                    ("controller", "m3", "get()", False),
                    ("m3", "controller", "return()", True),
                    ("controller", "v3", "view()", False),
                ],
            },
            {
                "name": "solicitarDevolucion",
                "messages": [
                    ("actor", "controller", "return_sale()", False),
                    ("controller", "m1", "update()", False),
                    ("m1", "controller", "return()", True),
                    ("controller", "v2", "view()", False),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# FUNCIONES DE CREACIÓN EN ENTERPRISE ARCHITECT
# ─────────────────────────────────────────────────────────────

def create_sequence_diagram_for_cu(rep, project, cycle_pkg, uc):
    """Crea un diagrama de secuencia para un Caso de Uso específico."""
    print(f"  -> Generando: {uc['diagram_name']} ({uc['id']})...")

    cu_pkg = cycle_pkg.Packages.AddNew(uc["id"], "")
    cu_pkg.Update()
    cycle_pkg.Packages.Refresh()

    # 1. Crear diagrama de secuencia
    diag = cu_pkg.Diagrams.AddNew(uc["diagram_name"], "Sequence")
    diag.Update()
    cu_pkg.Diagrams.Refresh()

    # Marco UML 2.5
    diag.StyleEx = "ShowFrame=1;"
    diag.Update()

    # 2. Crear elementos participantes
    actor = cu_pkg.Elements.AddNew(uc["actor"], "Actor")
    actor.Update()

    v1 = cu_pkg.Elements.AddNew(uc["views"][0], "Sequence")
    v1.Update()
    v2 = cu_pkg.Elements.AddNew(uc["views"][1], "Sequence")
    v2.Update()
    v3 = cu_pkg.Elements.AddNew(uc["views"][2], "Sequence")
    v3.Update()

    ctrl = cu_pkg.Elements.AddNew(uc["controller"], "Sequence")
    ctrl.Update()

    m1 = cu_pkg.Elements.AddNew(uc["models"][0], "Sequence")
    m1.Update()
    m2 = cu_pkg.Elements.AddNew(uc["models"][1], "Sequence")
    m2.Update()
    m3 = cu_pkg.Elements.AddNew(uc["models"][2], "Sequence")
    m3.Update()

    participant_map = {
        "actor": actor,
        "v1": v1,
        "v2": v2,
        "v3": v3,
        "controller": ctrl,
        "m1": m1,
        "m2": m2,
        "m3": m3,
    }

    # 3. Disposición horizontal de las líneas de vida (Lifelines)
    lifeline_positions = [
        (actor, 40, 130),
        (v1, 140, 230),
        (v2, 250, 355),
        (v3, 370, 480),
        (ctrl, 500, 625),
        (m1, 645, 755),
        (m2, 775, 885),
        (m3, 905, 1010),
    ]

    # Calcular coordenadas dinámicas de los fragmentos según la cantidad de mensajes
    current_y = -90
    computed_fragments = []
    for frag in uc["fragments"]:
        msg_count = len(frag["messages"])
        frag_height = max(110, msg_count * 32 + 25)
        frag_top = current_y
        frag_bottom = frag_top - frag_height
        computed_fragments.append({
            "name": frag["name"],
            "top": frag_top,
            "bottom": frag_bottom,
            "messages": frag["messages"]
        })
        current_y = frag_bottom - 15

    max_bottom = current_y - 30

    for el, left, right in lifeline_positions:
        obj = diag.DiagramObjects.AddNew("", "")
        obj.ElementID = el.ElementID
        obj.left = left
        obj.right = right
        obj.top = -40
        obj.bottom = max_bottom
        obj.Update()

    # 4. Crear fragmentos combinados ('alt') y mensajes
    seq_counter = 1
    for frag in computed_fragments:
        frag_el = cu_pkg.Elements.AddNew(frag["name"], "InteractionFragment")
        frag_el.Subtype = 0  # 0 = alt
        frag_el.Update()

        obj_frag = diag.DiagramObjects.AddNew("", "")
        obj_frag.ElementID = frag_el.ElementID
        obj_frag.left = 20
        obj_frag.right = 1030
        obj_frag.top = frag["top"]
        obj_frag.bottom = frag["bottom"]
        obj_frag.Update()

        for src_key, dst_key, msg_text, is_return in frag["messages"]:
            src = participant_map[src_key]
            dst = participant_map[dst_key]

            c = src.Connectors.AddNew(msg_text, "Sequence")
            c.SupplierID = dst.ElementID
            c.SequenceNo = seq_counter
            c.Direction = "Source -> Destination"

            if is_return:
                c.StyleEx = "IsReturn=1;"
            c.Update()

            lnk = diag.DiagramLinks.AddNew("", "")
            lnk.ConnectorID = c.ConnectorID
            lnk.Update()

            seq_counter += 1

    diag.Update()
    diag.DiagramObjects.Refresh()
    diag.DiagramLinks.Refresh()

    # 5. Exportar imagen PNG
    export_path = os.path.join(EXPORT_DIR, uc["filename"])
    project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
    print(f"     Guardado PNG: {export_path}")


def generate_sequence_group(rep, project, main_pkg, group_name, uc_list):
    """Genera un subpaquete de ciclo con sus respectivos diagramas."""
    print(f"\n==========================================")
    print(f"  Procesando Grupo: {group_name}")
    print(f"==========================================")

    group_pkg = main_pkg.Packages.AddNew(group_name, "")
    group_pkg.Update()
    main_pkg.Packages.Refresh()

    for uc in uc_list:
        create_sequence_diagram_for_cu(rep, project, group_pkg, uc)

    group_pkg.Update()
    main_pkg.Packages.Refresh()


def main():
    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE SECUENCIA (CICLOS 1, 2 Y 3) — FASHIONSTORE")
    print("=" * 75)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    try:
        project = rep.GetProjectInterface()
        root_model = rep.Models.GetAt(0)

        pkg_name = "05 - Diagramas de Secuencia"

        # Buscar si ya existe el paquete para recrearlo limpio sin diálogos modales
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if "Diagramas de Secuencia" in p.Name:
                print(f"Limpiando paquete previo: {p.Name}")
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        main_seq_pkg = root_model.Packages.AddNew(pkg_name, "")
        main_seq_pkg.Notes = (
            "Diagramas de Secuencia UML 2.5 organizados por ciclos para todos los "
            "23 Casos de Uso del sistema FashionStore (Actor -> Vistas -> Controller -> Modelos)."
        )
        main_seq_pkg.Update()
        root_model.Packages.Refresh()

        print(f"Paquete contenedor creado: '{main_seq_pkg.Name}' (ID: {main_seq_pkg.PackageID})")

        # 1. Ciclo 1 (CU01 al CU09)
        generate_sequence_group(
            rep, project, main_seq_pkg,
            "Ciclo 1 - Catálogo y Base",
            CYCLE_1_SEQUENCE
        )

        # 2. Ciclo 2 (CU10 al CU19)
        generate_sequence_group(
            rep, project, main_seq_pkg,
            "Ciclo 2 - Operación Comercial y Logística",
            CYCLE_2_SEQUENCE
        )

        # 3. Ciclo 3 (CU12, CU20 al CU23)
        generate_sequence_group(
            rep, project, main_seq_pkg,
            "Ciclo 3 - Innovación y Analítica",
            CYCLE_3_SEQUENCE
        )

        rep.SaveAllDiagrams()
        print("\n" + "=" * 75)
        print("¡TODOS LOS DIAGRAMAS DE SECUENCIA (23 CUs) FUERON GENERADOS CON ÉXITO!")
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
