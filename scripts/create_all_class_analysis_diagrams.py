"""
Generador de Diagramas de Análisis de Clases (UML 2.5) para Ciclo 1, Ciclo 2 y Ciclo 3
del sistema FashionStore en Enterprise Architect.

Genera los diagramas de análisis de clases (Formulario -> Controller -> Entidad Principal -> Entidades Secundarias)
con estereotipos, atributos, métodos, parámetros tipados y cardinalidades.
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
# DEFINICIONES DE CASOS DE USO — CICLO 1 (9 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_1_ANALYSIS = [
    {
        "id": "CU01",
        "diagram_name": "Analizar una clase CU01",
        "filename": "analisis-clases-cu01-registrar-cliente.png",
        "actor": "Invitado",
        "form": {
            "name": "FormRegistroCliente",
            "stereotype": "Formulario",
            "attributes": [
                ("nombre", "string"),
                ("apellido", "string"),
                ("email", "string"),
                ("password", "string"),
                ("telefono", "string"),
                ("terminosAceptados", "boolean"),
            ],
            "methods": [
                ("IngresarDatos", "void", []),
                ("ValidarEmail", "boolean", []),
                ("AceptarTerminos", "void", [("aceptado", "boolean")]),
                ("Registrar", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "RegistroClienteController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("register_client", "JsonResponse", []),
                ("verify_email_available", "boolean", [("email", "string")]),
                ("create_user_profile", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Cliente",
            "stereotype": "Entidad",
            "attributes": [
                ("id_cliente", "integer"),
                ("id_usuario", "integer"),
                ("codigo_cliente", "string"),
                ("tipo_cliente", "string"),
                ("puntos_fidelidad", "integer"),
                ("fecha_registro", "datetime"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("actualizarPuntos", "void", [("puntos", "integer")]),
                ("validarRegistro", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("password_hash", "string"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("hashPassword", "string", [("raw", "string")]),
                    ("validarCredenciales", "boolean", []),
                ],
            },
            {
                "name": "E_Rol",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_rol", "integer"),
                    ("nombre", "string"),
                    ("descripcion", "string"),
                ],
                "methods": [
                    ("asignarRolPorDefecto", "void", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha", "datetime"),
                ],
                "methods": [
                    ("registrarEvento", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU02",
        "diagram_name": "Analizar una clase CU02",
        "filename": "analisis-clases-cu02-iniciar-cerrar-sesion.png",
        "actor": "Cliente",
        "form": {
            "name": "FormAutenticacion",
            "stereotype": "Formulario",
            "attributes": [
                ("email", "string"),
                ("password", "string"),
                ("recordarSesion", "boolean"),
                ("tokenSesion", "string"),
                ("estadoLogin", "string"),
            ],
            "methods": [
                ("IngresarCredenciales", "void", []),
                ("SolicitarLogin", "void", []),
                ("CerrarSesion", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "AuthController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("login_access_token", "JsonResponse", []),
                ("logout", "JsonResponse", []),
                ("refresh_token", "JsonResponse", []),
                ("get_current_user", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Usuario",
            "stereotype": "Entidad",
            "attributes": [
                ("id_usuario", "integer"),
                ("email", "string"),
                ("password_hash", "string"),
                ("nombre", "string"),
                ("activo", "boolean"),
                ("ultimo_acceso", "datetime"),
            ],
            "methods": [
                ("verificarPassword", "boolean", [("password", "string")]),
                ("actualizarUltimoAcceso", "void", []),
                ("desactivar", "void", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Rol",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_rol", "integer"),
                    ("nombre", "string"),
                    ("codigo", "string"),
                ],
                "methods": [
                    ("obtenerPermisos", "list", []),
                ],
            },
            {
                "name": "E_SesionUsuario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_sesion", "integer"),
                    ("token_jwt", "string"),
                    ("fecha_expiracion", "datetime"),
                    ("ip_origen", "string"),
                ],
                "methods": [
                    ("invalidarToken", "void", []),
                    ("esValido", "boolean", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("ip", "string"),
                ],
                "methods": [
                    ("registrarLogin", "void", []),
                    ("registrarLogout", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU03",
        "diagram_name": "Analizar una clase CU03",
        "filename": "analisis-clases-cu03-gestionar-usuarios-roles.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormGestionUsuarios",
            "stereotype": "Formulario",
            "attributes": [
                ("filtroRol", "string"),
                ("filtroEstado", "string"),
                ("usuarioSeleccionadoId", "integer"),
                ("nombreUsuario", "string"),
                ("emailUsuario", "string"),
                ("rolAsignadoId", "integer"),
            ],
            "methods": [
                ("Buscar", "void", []),
                ("NuevoUsuario", "void", []),
                ("GuardarUsuario", "void", []),
                ("CambiarRol", "void", [("rol_id", "integer")]),
                ("AlternarEstado", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "UsuarioRolController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_users", "JsonResponse", []),
                ("create_user", "JsonResponse", []),
                ("update_user_role", "JsonResponse", []),
                ("toggle_user_status", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Usuario",
            "stereotype": "Entidad",
            "attributes": [
                ("id_usuario", "integer"),
                ("email", "string"),
                ("nombre", "string"),
                ("apellido", "string"),
                ("telefono", "string"),
                ("activo", "boolean"),
                ("rol_id", "integer"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("setRol", "void", [("rol_id", "integer")]),
                ("toggleActivo", "void", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Rol",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_rol", "integer"),
                    ("nombre", "string"),
                    ("descripcion", "string"),
                    ("permisos_json", "string"),
                ],
                "methods": [
                    ("listarRoles", "list", []),
                    ("validarPermisos", "boolean", []),
                ],
            },
            {
                "name": "E_Empleado",
                "stereotype": "Entidad",
                "card_primary": "0..1",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_empleado", "integer"),
                    ("codigo_empleado", "string"),
                    ("cargo", "string"),
                    ("sucursal_id", "integer"),
                ],
                "methods": [
                    ("asignarSucursal", "void", [("sucursal_id", "integer")]),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("detalle", "string"),
                ],
                "methods": [
                    ("auditarCambioRol", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU04",
        "diagram_name": "Analizar una clase CU04",
        "filename": "analisis-clases-cu04-gestionar-sucursales-ciudades.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormGestionSucursal",
            "stereotype": "Formulario",
            "attributes": [
                ("nombreSucursal", "string"),
                ("direccion", "string"),
                ("telefono", "string"),
                ("ciudadId", "integer"),
                ("encargadoId", "integer"),
                ("estadoActivo", "boolean"),
            ],
            "methods": [
                ("ConsultarSucursales", "void", []),
                ("RegistrarSucursal", "void", []),
                ("ActualizarSucursal", "void", []),
                ("AsignarEncargado", "void", [("empleado_id", "integer")]),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "SucursalController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_branches", "JsonResponse", []),
                ("create_branch", "JsonResponse", []),
                ("update_branch", "JsonResponse", []),
                ("assign_manager", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Sucursal",
            "stereotype": "Entidad",
            "attributes": [
                ("id_sucursal", "integer"),
                ("nombre", "string"),
                ("direccion", "string"),
                ("ciudad_id", "integer"),
                ("encargado_id", "integer"),
                ("telefono", "string"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("asignarEncargado", "void", [("encargado_id", "integer")]),
                ("cambiarEstado", "void", [("activo", "boolean")]),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Ciudad",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_ciudad", "integer"),
                    ("nombre", "string"),
                    ("departamento", "string"),
                    ("codigo_postal", "string"),
                ],
                "methods": [
                    ("listarCiudades", "list", []),
                ],
            },
            {
                "name": "E_Empleado",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_empleado", "integer"),
                    ("ci", "string"),
                    ("nombre_completo", "string"),
                    ("cargo", "string"),
                ],
                "methods": [
                    ("obtenerDetalleEncargado", "string", []),
                ],
            },
            {
                "name": "E_Inventario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("producto_id", "integer"),
                    ("stock_actual", "integer"),
                ],
                "methods": [
                    ("inicializarStockSucursal", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU05",
        "diagram_name": "Analizar una clase CU05",
        "filename": "analisis-clases-cu05-gestionar-productos-prendas.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormGestionPrendas",
            "stereotype": "Formulario",
            "attributes": [
                ("nombrePrenda", "string"),
                ("codigoSKU", "string"),
                ("descripcion", "string"),
                ("precioBase", "decimal"),
                ("categoriaId", "integer"),
                ("marcaId", "integer"),
                ("estadoVisible", "boolean"),
            ],
            "methods": [
                ("BuscarPrendas", "void", []),
                ("NuevaPrenda", "void", []),
                ("GuardarPrenda", "void", []),
                ("ModificarPrenda", "void", []),
                ("Deshabilitar", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "PrendaController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_products", "JsonResponse", []),
                ("create_product", "JsonResponse", []),
                ("update_product", "JsonResponse", []),
                ("delete_product", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Producto",
            "stereotype": "Entidad",
            "attributes": [
                ("id_producto", "integer"),
                ("nombre", "string"),
                ("codigo_sku", "string"),
                ("descripcion", "string"),
                ("precio_base", "decimal"),
                ("categoria_id", "integer"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("desactivar", "void", []),
                ("calcularPrecioConDescuento", "decimal", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Categoria",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string"),
                    ("genero", "string"),
                    ("nivel_arbol", "integer"),
                ],
                "methods": [
                    ("obtenerJerarquia", "string", []),
                ],
            },
            {
                "name": "E_VarianteProducto",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("talla_id", "integer"),
                    ("color_id", "integer"),
                    ("codigo_barra", "string"),
                ],
                "methods": [
                    ("generarVariantes", "void", []),
                ],
            },
            {
                "name": "E_ImagenProducto",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_imagen", "integer"),
                    ("producto_id", "integer"),
                    ("url_imagen", "string"),
                    ("es_portada", "boolean"),
                ],
                "methods": [
                    ("agregarImagen", "void", [("url", "string")]),
                ],
            },
        ],
    },
    {
        "id": "CU06",
        "diagram_name": "Analizar una clase CU06",
        "filename": "analisis-clases-cu06-gestionar-catalogo-base.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormCatalogoBase",
            "stereotype": "Formulario",
            "attributes": [
                ("nombreCategoria", "string"),
                ("genero", "string"),
                ("tallaTexto", "string"),
                ("codigoColorHex", "string"),
                ("descripcionVariante", "string"),
            ],
            "methods": [
                ("ListarCategorias", "void", []),
                ("CrearCategoria", "void", []),
                ("AgregarTalla", "void", []),
                ("RegistrarColor", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "CatalogoBaseController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_categories", "JsonResponse", []),
                ("create_category", "JsonResponse", []),
                ("create_size", "JsonResponse", []),
                ("create_color", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Categoria",
            "stereotype": "Entidad",
            "attributes": [
                ("id_categoria", "integer"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("genero", "string"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("listarSubcategorias", "list", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Talla",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "*",
                "attributes": [
                    ("id_talla", "integer"),
                    ("codigo_talla", "string"),
                    ("tipo_medida", "string"),
                ],
                "methods": [
                    ("listarTallas", "list", []),
                ],
            },
            {
                "name": "E_Color",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "*",
                "attributes": [
                    ("id_color", "integer"),
                    ("nombre", "string"),
                    ("codigo_hex", "string"),
                ],
                "methods": [
                    ("listarColores", "list", []),
                ],
            },
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("categoria_id", "integer"),
                ],
                "methods": [
                    ("contarPrendasAsociadas", "integer", []),
                ],
            },
        ],
    },
    {
        "id": "CU07",
        "diagram_name": "Analizar una clase CU07",
        "filename": "analisis-clases-cu07-gestionar-proveedores.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormGestionProveedores",
            "stereotype": "Formulario",
            "attributes": [
                ("razonSocial", "string"),
                ("nit", "string"),
                ("contactoNombre", "string"),
                ("telefono", "string"),
                ("email", "string"),
                ("direccion", "string"),
                ("rubro", "string"),
            ],
            "methods": [
                ("ListarProveedores", "void", []),
                ("NuevoProveedor", "void", []),
                ("GuardarProveedor", "void", []),
                ("EditarProveedor", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "ProveedorController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_suppliers", "JsonResponse", []),
                ("create_supplier", "JsonResponse", []),
                ("update_supplier", "JsonResponse", []),
                ("get_purchase_history", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Proveedor",
            "stereotype": "Entidad",
            "attributes": [
                ("id_proveedor", "integer"),
                ("razon_social", "string"),
                ("nit", "string"),
                ("telefono", "string"),
                ("email", "string"),
                ("direccion", "string"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("verificarNIT", "boolean", [("nit", "string")]),
                ("desactivar", "void", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_OrdenCompra",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_orden", "integer"),
                    ("proveedor_id", "integer"),
                    ("fecha_pedido", "datetime"),
                    ("monto_total", "decimal"),
                    ("estado", "string"),
                ],
                "methods": [
                    ("listarOrdenes", "list", []),
                ],
            },
            {
                "name": "E_ProductoProveedor",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_relacion", "integer"),
                    ("proveedor_id", "integer"),
                    ("producto_id", "integer"),
                    ("costo_unitario", "decimal"),
                ],
                "methods": [
                    ("vincularCatalogo", "void", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("detalle", "string"),
                ],
                "methods": [
                    ("auditarOperacion", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU08",
        "diagram_name": "Analizar una clase CU08",
        "filename": "analisis-clases-cu08-consultar-catalogo-buscar-prendas.png",
        "actor": "Cliente",
        "form": {
            "name": "FormCatalogoExploracion",
            "stereotype": "Formulario",
            "attributes": [
                ("terminoBusqueda", "string"),
                ("categoriaSeleccionada", "integer"),
                ("rangoPrecioMax", "decimal"),
                ("tallaFiltro", "string"),
                ("ordenarPor", "string"),
            ],
            "methods": [
                ("AbrirCatalogo", "void", []),
                ("AplicarFiltros", "void", []),
                ("BuscarTexto", "void", [("termino", "string")]),
                ("VerFichaPrenda", "void", [("id", "integer")]),
                ("LimpiarFiltros", "void", []),
            ],
        },
        "controller": {
            "name": "CatalogoController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("search_products", "JsonResponse", []),
                ("get_featured", "JsonResponse", []),
                ("get_product_detail", "JsonResponse", []),
                ("filter_by_tags", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Producto",
            "stereotype": "Entidad",
            "attributes": [
                ("id_producto", "integer"),
                ("nombre", "string"),
                ("codigo_sku", "string"),
                ("precio_base", "decimal"),
                ("categoria_id", "integer"),
                ("activo", "boolean"),
            ],
            "methods": [
                ("buscarPorTexto", "list", [("termino", "string")]),
                ("filtrarPorRango", "list", [("min", "decimal"), ("max", "decimal")]),
                ("obtenerDetalleCompleto", "dict", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Categoria",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string"),
                    ("genero", "string"),
                ],
                "methods": [
                    ("obtenerFiltroCategoria", "dict", []),
                ],
            },
            {
                "name": "E_VarianteProducto",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("talla_id", "integer"),
                    ("color_id", "integer"),
                ],
                "methods": [
                    ("consultarTallasDisponibles", "list", []),
                ],
            },
            {
                "name": "E_ImagenProducto",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_imagen", "integer"),
                    ("producto_id", "integer"),
                    ("url_imagen", "string"),
                    ("es_portada", "boolean"),
                ],
                "methods": [
                    ("obtenerGaleria", "list", []),
                ],
            },
        ],
    },
    {
        "id": "CU09",
        "diagram_name": "Analizar una clase CU09",
        "filename": "analisis-clases-cu09-consultar-disponibilidad-tiendas.png",
        "actor": "Cliente",
        "form": {
            "name": "FormDisponibilidadStock",
            "stereotype": "Formulario",
            "attributes": [
                ("prendaId", "integer"),
                ("varianteSeleccionadaId", "integer"),
                ("ciudadId", "integer"),
                ("sucursalId", "integer"),
                ("stockDisponible", "integer"),
            ],
            "methods": [
                ("SeleccionarPrenda", "void", []),
                ("ElegirTallaColor", "void", []),
                ("ConsultarPorCiudad", "void", [("ciudad_id", "integer")]),
                ("VerMapaTienda", "void", [("sucursal_id", "integer")]),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "DisponibilidadStockController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("check_branch_stock", "JsonResponse", []),
                ("get_nearby_stores", "JsonResponse", []),
                ("get_stock_by_variant", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Inventario",
            "stereotype": "Entidad",
            "attributes": [
                ("id_inventario", "integer"),
                ("sucursal_id", "integer"),
                ("variante_id", "integer"),
                ("stock_fisico", "integer"),
                ("stock_reservado", "integer"),
                ("stock_disponible", "integer"),
            ],
            "methods": [
                ("consultarStockReal", "integer", []),
                ("verificarDisponibilidad", "boolean", []),
                ("bloquearTemporal", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Sucursal",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string"),
                    ("direccion", "string"),
                    ("latitud", "decimal"),
                    ("longitud", "decimal"),
                    ("telefono", "string"),
                ],
                "methods": [
                    ("obtenerUbicacion", "dict", []),
                ],
            },
            {
                "name": "E_VarianteProducto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("codigo_barra", "string"),
                    ("sku_variante", "string"),
                ],
                "methods": [
                    ("obtenerDetallesVariante", "dict", []),
                ],
            },
            {
                "name": "E_Ciudad",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_ciudad", "integer"),
                    ("nombre", "string"),
                    ("departamento", "string"),
                ],
                "methods": [
                    ("filtrarSucursales", "list", []),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# DEFINICIONES DE CASOS DE USO — CICLO 2 (9 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_2_ANALYSIS = [
    {
        "id": "CU10",
        "diagram_name": "Analizar una clase CU10",
        "filename": "analisis-clases-cu10-realizar-reserva-prendas.png",
        "actor": "Cliente",
        "form": {
            "name": "FormReservaPrenda",
            "stereotype": "Formulario",
            "attributes": [
                ("clienteId", "integer"),
                ("varianteId", "integer"),
                ("sucursalId", "integer"),
                ("fechaLimiteReserva", "datetime"),
                ("codigoReservaGenerado", "string"),
            ],
            "methods": [
                ("SeleccionarPrenda", "void", []),
                ("ElegirSucursal", "void", []),
                ("ConfirmarReserva", "void", []),
                ("DescargarTicketReserva", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "ReservaPrendaController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("create_reservation", "JsonResponse", []),
                ("check_availability", "JsonResponse", []),
                ("cancel_reservation", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Reserva",
            "stereotype": "Entidad",
            "attributes": [
                ("id_reserva", "integer"),
                ("cliente_id", "integer"),
                ("sucursal_id", "integer"),
                ("codigo_reserva", "string"),
                ("estado", "string"),
                ("fecha_creacion", "datetime"),
                ("fecha_expiracion", "datetime"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("confirmar", "void", []),
                ("cancelar", "void", []),
                ("esExpirada", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleReserva",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle_reserva", "integer"),
                    ("reserva_id", "integer"),
                    ("variante_id", "integer"),
                    ("cantidad", "integer"),
                ],
                "methods": [
                    ("calcularTotalPrendas", "integer", []),
                ],
            },
            {
                "name": "E_Inventario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("stock_reservado", "integer"),
                    ("stock_disponible", "integer"),
                ],
                "methods": [
                    ("incrementarReservado", "void", [("cant", "integer")]),
                    ("decrementarDisponible", "void", [("cant", "integer")]),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("nombre", "string"),
                    ("email", "string"),
                    ("telefono", "string"),
                ],
                "methods": [
                    ("obtenerDatosContactoCliente", "dict", []),
                ],
            },
        ],
    },
    {
        "id": "CU11",
        "diagram_name": "Analizar una clase CU11",
        "filename": "analisis-clases-cu11-atender-reservas-sucursal.png",
        "actor": "Encargado de Sucursal",
        "form": {
            "name": "FormAtencionReserva",
            "stereotype": "Formulario",
            "attributes": [
                ("codigoBusquedaReserva", "string"),
                ("sucursalId", "integer"),
                ("reservaId", "integer"),
                ("estadoReserva", "string"),
                ("clienteNombre", "string"),
                ("prendasDetalle", "string"),
            ],
            "methods": [
                ("BuscarPorCodigo", "void", [("codigo", "string")]),
                ("ListarPendientes", "void", []),
                ("ConfirmarEntrega", "void", []),
                ("CancelarExpirada", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "AtencionReservaController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("get_pending_reservations", "JsonResponse", []),
                ("validate_reservation_code", "JsonResponse", []),
                ("complete_pickup", "JsonResponse", []),
                ("expire_reservation", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Reserva",
            "stereotype": "Entidad",
            "attributes": [
                ("id_reserva", "integer"),
                ("codigo_reserva", "string"),
                ("estado", "string"),
                ("fecha_entrega", "datetime"),
                ("encargado_id", "integer"),
            ],
            "methods": [
                ("marcarEntregada", "void", []),
                ("marcarExpirada", "void", []),
                ("obtenerItems", "list", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleReserva",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle", "integer"),
                    ("reserva_id", "integer"),
                    ("variante_id", "integer"),
                    ("cantidad", "integer"),
                ],
                "methods": [
                    ("verificarItemsFisicos", "boolean", []),
                ],
            },
            {
                "name": "E_Inventario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("stock_reservado", "integer"),
                    ("stock_fisico", "integer"),
                ],
                "methods": [
                    ("descontarStockFisico", "void", []),
                    ("liberarStockReservado", "void", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha", "datetime"),
                ],
                "methods": [
                    ("registrarAtencionReserva", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU13",
        "diagram_name": "Analizar una clase CU13",
        "filename": "analisis-clases-cu13-administrar-carrito-compras.png",
        "actor": "Cliente",
        "form": {
            "name": "FormCarritoCompras",
            "stereotype": "Formulario",
            "attributes": [
                ("clienteId", "integer"),
                ("itemsCount", "integer"),
                ("subtotalCarrito", "decimal"),
                ("descuentoTotal", "decimal"),
                ("totalPagar", "decimal"),
            ],
            "methods": [
                ("AgregarItem", "void", []),
                ("ModificarCantidad", "void", [("item_id", "integer"), ("cant", "integer")]),
                ("EliminarItem", "void", [("item_id", "integer")]),
                ("VaciarCarrito", "void", []),
                ("IrCheckout", "void", []),
            ],
        },
        "controller": {
            "name": "CarritoComprasController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("get_cart", "JsonResponse", []),
                ("add_item", "JsonResponse", []),
                ("update_item_quantity", "JsonResponse", []),
                ("remove_item", "JsonResponse", []),
                ("clear_cart", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Carrito",
            "stereotype": "Entidad",
            "attributes": [
                ("id_carrito", "integer"),
                ("cliente_id", "integer"),
                ("total_items", "integer"),
                ("subtotal", "decimal"),
                ("fecha_actualizacion", "datetime"),
            ],
            "methods": [
                ("calcularTotales", "void", []),
                ("agregarItem", "void", [("variante_id", "integer"), ("cant", "integer")]),
                ("removerItem", "void", [("item_id", "integer")]),
                ("vaciar", "void", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_ItemCarrito",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_item", "integer"),
                    ("carrito_id", "integer"),
                    ("variante_id", "integer"),
                    ("cantidad", "integer"),
                    ("precio_unitario", "decimal"),
                ],
                "methods": [
                    ("calcularSubtotalItem", "decimal", []),
                ],
            },
            {
                "name": "E_VarianteProducto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("talla_id", "integer"),
                    ("color_id", "integer"),
                ],
                "methods": [
                    ("validarStockActual", "boolean", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                ],
                "methods": [
                    ("obtenerCarritoUsuario", "integer", []),
                ],
            },
        ],
    },
    {
        "id": "CU14",
        "diagram_name": "Analizar una clase CU14",
        "filename": "analisis-clases-cu14-realizar-compra-digital.png",
        "actor": "Cliente",
        "form": {
            "name": "FormCheckoutDigital",
            "stereotype": "Formulario",
            "attributes": [
                ("direccionEnvioId", "integer"),
                ("metodoPago", "string"),
                ("costoEnvio", "decimal"),
                ("descuentoCupon", "decimal"),
                ("montoTotal", "decimal"),
            ],
            "methods": [
                ("IniciarCheckout", "void", []),
                ("SeleccionarDireccion", "void", [("id", "integer")]),
                ("ElegirPago", "void", [("metodo", "string")]),
                ("ConfirmarCompra", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "CompraDigitalController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("process_checkout", "JsonResponse", []),
                ("calculate_shipping", "JsonResponse", []),
                ("apply_coupon", "JsonResponse", []),
                ("confirm_order", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Venta",
            "stereotype": "Entidad",
            "attributes": [
                ("id_venta", "integer"),
                ("cliente_id", "integer"),
                ("tipo_venta", "string"),
                ("subtotal", "decimal"),
                ("descuento", "decimal"),
                ("total", "decimal"),
                ("estado", "string"),
                ("fecha_creacion", "datetime"),
            ],
            "methods": [
                ("createVentaDigital", "boolean", []),
                ("calcularTotal", "decimal", []),
                ("confirmarVenta", "void", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleVenta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle", "integer"),
                    ("venta_id", "integer"),
                    ("variante_id", "integer"),
                    ("cantidad", "integer"),
                    ("precio_unitario", "decimal"),
                ],
                "methods": [
                    ("crearDetallesDesdeCarrito", "void", []),
                ],
            },
            {
                "name": "E_Pago",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_pago", "integer"),
                    ("venta_id", "integer"),
                    ("metodo", "string"),
                    ("estado_pago", "string"),
                    ("referencia", "string"),
                ],
                "methods": [
                    ("vincularPago", "void", []),
                ],
            },
            {
                "name": "E_DireccionEnvio",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_direccion", "integer"),
                    ("usuario_id", "integer"),
                    ("direccion_linea", "string"),
                    ("ciudad", "string"),
                ],
                "methods": [
                    ("obtenerDatosEnvio", "dict", []),
                ],
            },
        ],
    },
    {
        "id": "CU15",
        "diagram_name": "Analizar una clase CU15",
        "filename": "analisis-clases-cu15-realizar-venta-presencial-pos.png",
        "actor": "Cajero",
        "form": {
            "name": "FormPuntoVentaPOS",
            "stereotype": "Formulario",
            "attributes": [
                ("codigoBarraEscaneado", "string"),
                ("ciNitCliente", "string"),
                ("descuentoManualPct", "decimal"),
                ("subtotalPOS", "decimal"),
                ("totalPOS", "decimal"),
            ],
            "methods": [
                ("EscanearPrenda", "void", [("barcode", "string")]),
                ("BuscarCliente", "void", [("ci", "string")]),
                ("AplicarDescuento", "void", [("pct", "decimal")]),
                ("FinalizarVenta", "void", []),
                ("CancelarVenta", "void", []),
            ],
        },
        "controller": {
            "name": "VentaPOSController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("scan_barcode", "JsonResponse", []),
                ("lookup_customer", "JsonResponse", []),
                ("register_pos_sale", "JsonResponse", []),
                ("void_sale", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Venta",
            "stereotype": "Entidad",
            "attributes": [
                ("id_venta", "integer"),
                ("sucursal_id", "integer"),
                ("cajero_id", "integer"),
                ("cliente_id", "integer"),
                ("tipo_venta", "string"),
                ("total", "decimal"),
                ("estado", "string"),
            ],
            "methods": [
                ("createVentaPOS", "boolean", []),
                ("anularVenta", "void", []),
                ("obtenerComprobante", "string", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleVenta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle", "integer"),
                    ("venta_id", "integer"),
                    ("variante_id", "integer"),
                    ("cantidad", "integer"),
                    ("precio_unitario", "decimal"),
                ],
                "methods": [
                    ("agregarItemLinea", "void", []),
                ],
            },
            {
                "name": "E_Inventario",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer"),
                ],
                "methods": [
                    ("descontarStockInmediato", "void", []),
                ],
            },
            {
                "name": "E_Cliente",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_cliente", "integer"),
                    ("ci_nit", "string"),
                    ("razon_social", "string"),
                    ("email", "string"),
                ],
                "methods": [
                    ("obtenerOcrearCliente", "integer", []),
                ],
            },
        ],
    },
    {
        "id": "CU16",
        "diagram_name": "Analizar una clase CU16",
        "filename": "analisis-clases-cu16-cobro-en-caja.png",
        "actor": "Cajero",
        "form": {
            "name": "FormCobroCaja",
            "stereotype": "Formulario",
            "attributes": [
                ("ventaId", "integer"),
                ("montoTotal", "decimal"),
                ("metodoPago", "string"),
                ("efectivoRecibido", "decimal"),
                ("cambioCalculado", "decimal"),
                ("comprobanteExt", "string"),
            ],
            "methods": [
                ("SeleccionarMetodo", "void", [("metodo", "string")]),
                ("CalcularCambio", "void", []),
                ("ProcesarPago", "void", []),
                ("EmitirFactura", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "CobroCajaController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("process_cash_payment", "JsonResponse", []),
                ("process_pos_card", "JsonResponse", []),
                ("generate_qr_payment", "JsonResponse", []),
                ("issue_invoice", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Pago",
            "stereotype": "Entidad",
            "attributes": [
                ("id_pago", "integer"),
                ("venta_id", "integer"),
                ("metodo", "string"),
                ("monto", "decimal"),
                ("cambio", "decimal"),
                ("estado", "string"),
                ("fecha_pago", "datetime"),
            ],
            "methods": [
                ("registrarPago", "boolean", []),
                ("validarMontoCompleto", "boolean", []),
                ("emitirRecibo", "string", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Venta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_venta", "integer"),
                    ("total", "decimal"),
                    ("estado", "string"),
                    ("cliente_id", "integer"),
                ],
                "methods": [
                    ("actualizarEstadoVenta", "void", [("nuevo_estado", "string")]),
                ],
            },
            {
                "name": "E_Factura",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_factura", "integer"),
                    ("pago_id", "integer"),
                    ("numero_factura", "string"),
                    ("codigo_control", "string"),
                    ("nit_cliente", "string"),
                ],
                "methods": [
                    ("generarFacturaFiscal", "string", []),
                ],
            },
            {
                "name": "E_CajaSesion",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_caja_sesion", "integer"),
                    ("cajero_id", "integer"),
                    ("monto_apertura", "decimal"),
                    ("monto_cierre", "decimal"),
                ],
                "methods": [
                    ("acumularEnCaja", "void", [("monto", "decimal")]),
                ],
            },
        ],
    },
    {
        "id": "CU17",
        "diagram_name": "Analizar una clase CU17",
        "filename": "analisis-clases-cu17-procesar-pago-electronico-sandbox.png",
        "actor": "Pasarela de Pagos",
        "form": {
            "name": "FormPasarelaPago",
            "stereotype": "Formulario",
            "attributes": [
                ("tokenTarjeta", "string"),
                ("montoTransaccion", "decimal"),
                ("moneda", "string"),
                ("estadoGateway", "string"),
                ("codigoAutorizacion", "string"),
            ],
            "methods": [
                ("RecibirToken", "void", [("token", "string")]),
                ("SolicitarSandbox", "void", []),
                ("NotificarWebhook", "void", [("payload", "string")]),
                ("MostrarResultado", "void", []),
            ],
        },
        "controller": {
            "name": "PasarelaPagoController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("create_payment_intent", "JsonResponse", []),
                ("handle_webhook", "JsonResponse", []),
                ("verify_signature", "boolean", []),
                ("refund_charge", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Pago",
            "stereotype": "Entidad",
            "attributes": [
                ("id_pago", "integer"),
                ("venta_id", "integer"),
                ("metodo", "string"),
                ("proveedor", "string"),
                ("referencia_transaccion", "string"),
                ("estado", "string"),
                ("monto", "decimal"),
            ],
            "methods": [
                ("confirmarPago", "boolean", []),
                ("registrarFallo", "void", [("codigo_error", "string")]),
                ("solicitarReembolso", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_TransaccionPasarela",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_transaccion", "integer"),
                    ("pago_id", "integer"),
                    ("payload_request", "string"),
                    ("payload_response", "string"),
                    ("codigo_http", "integer"),
                ],
                "methods": [
                    ("registrarLogGateway", "void", []),
                ],
            },
            {
                "name": "E_Venta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1",
                "attributes": [
                    ("id_venta", "integer"),
                    ("total", "decimal"),
                    ("estado", "string"),
                ],
                "methods": [
                    ("completarOrden", "void", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("accion", "string"),
                    ("detalle", "string"),
                    ("fecha", "datetime"),
                ],
                "methods": [
                    ("auditarTransaccionSegura", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU18",
        "diagram_name": "Analizar una clase CU18",
        "filename": "analisis-clases-cu18-control-stock-movimientos.png",
        "actor": "Encargado de Sucursal",
        "form": {
            "name": "FormInventarioStock",
            "stereotype": "Formulario",
            "attributes": [
                ("sucursalId", "integer"),
                ("varianteId", "integer"),
                ("tipoMovimiento", "string"),
                ("cantidadMovimiento", "integer"),
                ("motivoAjuste", "string"),
                ("sucursalDestinoId", "integer"),
            ],
            "methods": [
                ("ConsultarStock", "void", []),
                ("RegistrarIngreso", "void", []),
                ("RegistrarTraslado", "void", []),
                ("AjustarInventario", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "InventarioStockController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_stock", "JsonResponse", []),
                ("record_stock_entry", "JsonResponse", []),
                ("transfer_stock", "JsonResponse", []),
                ("adjust_stock", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_MovimientoInventario",
            "stereotype": "Entidad",
            "attributes": [
                ("id_movimiento", "integer"),
                ("tipo_movimiento", "string"),
                ("origen_sucursal_id", "integer"),
                ("destino_sucursal_id", "integer"),
                ("cantidad", "integer"),
                ("motivo", "string"),
                ("fecha", "datetime"),
            ],
            "methods": [
                ("createMovimiento", "boolean", []),
                ("ejecutarTransferencia", "boolean", []),
                ("revertirMovimiento", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Inventario",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer"),
                ],
                "methods": [
                    ("actualizarStockFisico", "void", [("dif", "integer")]),
                ],
            },
            {
                "name": "E_VarianteProducto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("sku_variante", "string"),
                    ("codigo_barra", "string"),
                ],
                "methods": [
                    ("obtenerPrendaAsociada", "dict", []),
                ],
            },
            {
                "name": "E_Sucursal",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string"),
                    ("ciudad_id", "integer"),
                ],
                "methods": [
                    ("validarSucursalesInvolucradas", "boolean", []),
                ],
            },
        ],
    },
    {
        "id": "CU19",
        "diagram_name": "Analizar una clase CU19",
        "filename": "analisis-clases-cu19-gestionar-temporadas-colecciones.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormGestionTemporadas",
            "stereotype": "Formulario",
            "attributes": [
                ("nombreTemporada", "string"),
                ("anio", "integer"),
                ("fechaInicio", "datetime"),
                ("fechaFin", "datetime"),
                ("prendasAsignadasIds", "string"),
                ("estadoActivo", "boolean"),
            ],
            "methods": [
                ("ConsultarTemporadas", "void", []),
                ("CrearTemporada", "void", []),
                ("AsignarPrendas", "void", []),
                ("ActivarTemporada", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "TemporadaController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_seasons", "JsonResponse", []),
                ("create_season", "JsonResponse", []),
                ("assign_products_to_season", "JsonResponse", []),
                ("set_active_season", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Temporada",
            "stereotype": "Entidad",
            "attributes": [
                ("id_temporada", "integer"),
                ("nombre", "string"),
                ("anio", "integer"),
                ("fecha_inicio", "datetime"),
                ("fecha_fin", "datetime"),
                ("estado_activo", "boolean"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("activar", "void", []),
                ("esVigente", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_ProductoTemporada",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_relacion", "integer"),
                    ("temporada_id", "integer"),
                    ("producto_id", "integer"),
                ],
                "methods": [
                    ("vincularPrendasColeccion", "void", []),
                ],
            },
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "*",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("codigo_sku", "string"),
                    ("precio_base", "decimal"),
                ],
                "methods": [
                    ("listarPrendasPorTemporada", "list", []),
                ],
            },
            {
                "name": "E_Promocion",
                "stereotype": "Entidad",
                "card_primary": "0..1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_promocion", "integer"),
                    ("temporada_id", "integer"),
                    ("porcentaje_descuento", "decimal"),
                ],
                "methods": [
                    ("asociarDescuentoEstacional", "void", []),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# DEFINICIONES DE CASOS DE USO — CICLO 3 (5 CUs)
# ─────────────────────────────────────────────────────────────

CYCLE_3_ANALYSIS = [
    {
        "id": "CU12",
        "diagram_name": "Analizar una clase CU12",
        "filename": "analisis-clases-cu12-sesion-probador-virtual.png",
        "actor": "Cliente",
        "form": {
            "name": "FormVestidorVirtual",
            "stereotype": "Formulario",
            "attributes": [
                ("productoId", "integer"),
                ("imagenUsuarioBase64", "string"),
                ("puntosClavePose", "string"),
                ("sesionActivaId", "integer"),
                ("dispositivoInfo", "string"),
                ("estadoSesion", "string"),
            ],
            "methods": [
                ("IniciarSesion", "void", []),
                ("CargarImagen", "void", []),
                ("SeleccionarPrenda", "void", []),
                ("SolicitarAjusteVTON", "void", []),
                ("FinalizarSesion", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "VestidorVirtualController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("start_session", "JsonResponse", []),
                ("finish_session", "JsonResponse", []),
                ("list_mine", "JsonResponse", []),
                ("vton_try_on", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_SesionVestidorVirtual",
            "stereotype": "Entidad",
            "attributes": [
                ("id_sesion", "integer"),
                ("id_cliente", "integer"),
                ("id_producto", "integer"),
                ("estado", "string"),
                ("info_dispositivo", "string"),
                ("fecha_inicio", "datetime"),
                ("fecha_fin", "datetime"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("finish", "boolean", []),
                ("vincularPrenda", "void", [("id_producto", "integer")]),
                ("validarDispositivo", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("codigo_sku", "string"),
                    ("precio_base", "decimal"),
                    ("modelo_3d_url", "string"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("obtenerModelo3D", "string", []),
                    ("verificarDisponibilidad", "boolean", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("apellido", "string"),
                    ("estado", "string"),
                ],
                "methods": [
                    ("obtenerHistorialSesiones", "list", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("tipo_entidad", "string"),
                    ("detalle", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("registrarEventoVTON", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU20",
        "diagram_name": "Analizar una clase CU20",
        "filename": "analisis-clases-cu20-gestionar-promociones.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormPromocion",
            "stereotype": "Formulario",
            "attributes": [
                ("nombre", "string"),
                ("descripcion", "string"),
                ("tipoDescuento", "string"),
                ("valorDescuento", "decimal"),
                ("fechaInicio", "datetime"),
                ("fechaFin", "datetime"),
                ("productosSeleccionados", "string"),
                ("filtroBusqueda", "string"),
                ("estado", "string"),
            ],
            "methods": [
                ("CrearPromocion", "void", []),
                ("ModificarPromocion", "void", []),
                ("PausarPromocion", "void", []),
                ("ActivarPromocion", "void", []),
                ("AsignarProductos", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "PromocionController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_promotions", "JsonResponse", []),
                ("create_promotion", "JsonResponse", []),
                ("update_promotion", "JsonResponse", []),
                ("toggle_status", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Promocion",
            "stereotype": "Entidad",
            "attributes": [
                ("id_promocion", "integer"),
                ("nombre", "string"),
                ("descripcion", "string"),
                ("porcentaje_descuento", "decimal"),
                ("monto_descuento_fijo", "decimal"),
                ("fecha_inicio", "datetime"),
                ("fecha_fin", "datetime"),
                ("estado", "string"),
            ],
            "methods": [
                ("create", "boolean", []),
                ("update", "boolean", []),
                ("esVigente", "boolean", []),
                ("calcularDescuento", "decimal", [("precio_original", "decimal")]),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "*",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("precio_base", "decimal"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("aplicarDescuento", "void", []),
                ],
            },
            {
                "name": "E_Categoria",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string"),
                    ("descripcion", "string"),
                ],
                "methods": [
                    ("aplicarPromocionCategoria", "void", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("detalle", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("auditarCambioPromocion", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU21",
        "diagram_name": "Analizar una clase CU21",
        "filename": "analisis-clases-cu21-gestionar-reportes.png",
        "actor": "Administrador del Sistema",
        "form": {
            "name": "FormReporte",
            "stereotype": "Formulario",
            "attributes": [
                ("tipoReporte", "string"),
                ("fechaInicio", "datetime"),
                ("fechaFin", "datetime"),
                ("sucursalSeleccionadaId", "integer"),
                ("categoriaId", "integer"),
                ("formatoExportacion", "string"),
                ("datosGrafico", "string"),
            ],
            "methods": [
                ("ConsultarMetricas", "void", []),
                ("FiltrarPorFecha", "void", []),
                ("ExportarExcel", "void", []),
                ("ExportarPDF", "void", []),
                ("SolicitarAnalisisIA", "void", []),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "ReporteController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("get_dashboard_summary", "JsonResponse", []),
                ("export_excel", "FileResponse", []),
                ("export_pdf", "FileResponse", []),
                ("get_ai_insights", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Reporte",
            "stereotype": "Entidad",
            "attributes": [
                ("id_reporte", "integer"),
                ("tipo_reporte", "string"),
                ("parametros_json", "string"),
                ("resultado_metricas", "string"),
                ("fecha_generacion", "datetime"),
                ("usuario_generador_id", "integer"),
            ],
            "methods": [
                ("generarMetricas", "dict", []),
                ("construirDataset", "list", []),
                ("almacenarSnapshot", "boolean", []),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Venta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_venta", "integer"),
                    ("total", "decimal"),
                    ("fecha_creacion", "datetime"),
                    ("estado", "string"),
                    ("tipo_venta", "string"),
                ],
                "methods": [
                    ("calcularAgregados", "decimal", []),
                ],
            },
            {
                "name": "E_Sucursal",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string"),
                    ("ciudad_id", "integer"),
                ],
                "methods": [
                    ("obtenerMetricasLocales", "dict", []),
                ],
            },
            {
                "name": "E_Bitacora",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "0..*",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_creacion", "datetime"),
                ],
                "methods": [
                    ("registrarDescargaReporte", "void", []),
                ],
            },
        ],
    },
    {
        "id": "CU22",
        "diagram_name": "Analizar una clase CU22",
        "filename": "analisis-clases-cu22-obtener-recomendaciones-ia.png",
        "actor": "Cliente",
        "form": {
            "name": "FormRecomendacion",
            "stereotype": "Formulario",
            "attributes": [
                ("clienteId", "integer"),
                ("temporadaActualId", "integer"),
                ("categoriaPreferencia", "string"),
                ("prendasRecomendadas", "string"),
                ("scoreConfianza", "decimal"),
                ("motivoRecomendacion", "string"),
            ],
            "methods": [
                ("SolicitarRecomendaciones", "void", []),
                ("FiltrarPorEstilo", "void", []),
                ("VerDetallePrenda", "void", [("id", "integer")]),
                ("DarFeedback", "void", [("util", "boolean")]),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "RecomendacionController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("get_recommendations", "JsonResponse", []),
                ("record_feedback", "JsonResponse", []),
                ("get_personalized_feed", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_RecomendacionIA",
            "stereotype": "Entidad",
            "attributes": [
                ("id_recomendacion", "integer"),
                ("id_cliente", "integer"),
                ("id_producto", "integer"),
                ("score_afinidad", "decimal"),
                ("explicacion_ia", "string"),
                ("fecha_calculo", "datetime"),
            ],
            "methods": [
                ("calcularAfinidad", "decimal", []),
                ("generarExplicacion", "string", []),
                ("actualizarScoreFeedback", "void", [("score", "decimal")]),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_Producto",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_producto", "integer"),
                    ("nombre", "string"),
                    ("precio_base", "decimal"),
                    ("activo", "boolean"),
                ],
                "methods": [
                    ("verificarStockAfinidad", "boolean", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                ],
                "methods": [
                    ("obtenerPreferenciasEstilo", "list", []),
                ],
            },
            {
                "name": "E_Temporada",
                "stereotype": "Entidad",
                "card_primary": "*",
                "card_secondary": "0..1",
                "attributes": [
                    ("id_temporada", "integer"),
                    ("nombre", "string"),
                    ("estado_activo", "boolean"),
                ],
                "methods": [
                    ("obtenerTendenciasTemporada", "list", []),
                ],
            },
        ],
    },
    {
        "id": "CU23",
        "diagram_name": "Analizar una clase CU23",
        "filename": "analisis-clases-cu23-consultar-historial-compras.png",
        "actor": "Cliente",
        "form": {
            "name": "FormHistorialCompras",
            "stereotype": "Formulario",
            "attributes": [
                ("filtroFechaInicio", "datetime"),
                ("filtroFechaFin", "datetime"),
                ("filtroEstadoVenta", "string"),
                ("ventaSeleccionadaId", "integer"),
                ("listaCompras", "string"),
                ("comprobanteUrl", "string"),
            ],
            "methods": [
                ("ConsultarHistorial", "void", []),
                ("FiltrarPorEstado", "void", [("estado", "string")]),
                ("VerDetalleOrden", "void", [("id", "integer")]),
                ("DescargarComprobante", "void", [("id", "integer")]),
                ("SolicitarDevolucion", "void", [("id", "integer")]),
                ("Limpiar", "void", []),
            ],
        },
        "controller": {
            "name": "HistorialComprasController",
            "stereotype": "Class",
            "attributes": [],
            "methods": [
                ("list_my_orders", "JsonResponse", []),
                ("get_order_detail", "JsonResponse", []),
                ("download_receipt", "FileResponse", []),
                ("request_refund", "JsonResponse", []),
            ],
        },
        "primary_entity": {
            "name": "E_Venta",
            "stereotype": "Entidad",
            "attributes": [
                ("id_venta", "integer"),
                ("id_cliente", "integer"),
                ("id_sucursal", "integer"),
                ("tipo_venta", "string"),
                ("estado", "string"),
                ("subtotal", "decimal"),
                ("descuento", "decimal"),
                ("total", "decimal"),
                ("fecha_creacion", "datetime"),
            ],
            "methods": [
                ("calcularTotal", "decimal", []),
                ("obtenerDetalles", "list", []),
                ("cambiarEstado", "void", [("nuevo_estado", "string")]),
                ("solicitarDevolucion", "boolean", [("motivo", "string")]),
            ],
        },
        "secondary_entities": [
            {
                "name": "E_DetalleVenta",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_detalle", "integer"),
                    ("id_venta", "integer"),
                    ("id_variante_producto", "integer"),
                    ("cantidad", "integer"),
                    ("precio_unitario", "decimal"),
                    ("descuento", "decimal"),
                    ("subtotal_linea", "decimal"),
                ],
                "methods": [
                    ("calcularSubtotal", "decimal", []),
                ],
            },
            {
                "name": "E_Pago",
                "stereotype": "Entidad",
                "card_primary": "1",
                "card_secondary": "1..*",
                "attributes": [
                    ("id_pago", "integer"),
                    ("id_venta", "integer"),
                    ("metodo", "string"),
                    ("proveedor", "string"),
                    ("referencia_transaccion", "string"),
                    ("estado", "string"),
                    ("monto", "decimal"),
                    ("fecha_pago", "datetime"),
                ],
                "methods": [
                    ("verificarTransaccion", "boolean", []),
                    ("generarRecibo", "string", []),
                ],
            },
            {
                "name": "E_Usuario",
                "stereotype": "Entidad",
                "card_primary": "0..*",
                "card_secondary": "1",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("apellido", "string"),
                    ("telefono", "string"),
                ],
                "methods": [
                    ("obtenerDireccionEnvio", "string", []),
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────
# HELPERS DE ENTERPRISE ARCHITECT
# ─────────────────────────────────────────────────────────────

def create_class_element(pkg, name, stereotype, attrs, methods):
    el = pkg.Elements.AddNew(name, "Class")
    if stereotype:
        el.Stereotype = stereotype
    el.Update()

    for a_name, a_type in attrs:
        att = el.Attributes.AddNew(a_name, a_type)
        att.Visibility = "Public"
        att.Update()
    el.Attributes.Refresh()

    for m in methods:
        m_name = m[0]
        m_ret = m[1]
        params = m[2] if len(m) > 2 else []
        meth = el.Methods.AddNew(m_name, m_ret)
        meth.ReturnType = m_ret
        meth.Visibility = "Public"
        meth.Update()
        if params:
            for p_name, p_type in params:
                p = meth.Parameters.AddNew(p_name, p_type)
                p.Type = p_type
                p.Update()
            meth.Parameters.Refresh()
    el.Methods.Refresh()
    return el


def connect_classes(diag, src, dst, card_src="", card_dst=""):
    c = src.Connectors.AddNew("", "Association")
    c.SupplierID = dst.ElementID
    c.Direction = "Unspecified"
    if card_src:
        c.ClientEnd.Cardinality = card_src
    if card_dst:
        c.SupplierEnd.Cardinality = card_dst
    c.Update()
    lnk = diag.DiagramLinks.AddNew("", "")
    lnk.ConnectorID = c.ConnectorID
    lnk.Update()
    return c


def generate_analysis_group(rep, project, parent_pkg, group_name, uc_list):
    print(f"\n==========================================")
    print(f"  Procesando Grupo: {group_name}")
    print(f"==========================================")

    # Buscar o crear subpaquete de ciclo
    cycle_pkg = None
    for i in range(parent_pkg.Packages.Count):
        p = parent_pkg.Packages.GetAt(i)
        if p.Name == group_name:
            cycle_pkg = p
            break

    if cycle_pkg is None:
        cycle_pkg = parent_pkg.Packages.AddNew(group_name, "")
        cycle_pkg.Update()
        parent_pkg.Packages.Refresh()

    for uc in uc_list:
        diag_name = uc["diagram_name"]
        print(f"  -> Generando: {diag_name} ({uc['id']})...")

        # Subpaquete por caso de uso para mantener limpio el namespace
        cu_pkg = None
        for i in range(cycle_pkg.Packages.Count):
            p = cycle_pkg.Packages.GetAt(i)
            if p.Name == uc["id"]:
                cu_pkg = p
                break

        if cu_pkg is None:
            cu_pkg = cycle_pkg.Packages.AddNew(uc["id"], "")
            cu_pkg.Update()
            cycle_pkg.Packages.Refresh()

        # Diagrama de Clases
        diag = None
        for i in range(cu_pkg.Diagrams.Count):
            d = cu_pkg.Diagrams.GetAt(i)
            if d.Name == diag_name:
                diag = d
                break

        if diag is None:
            diag = cu_pkg.Diagrams.AddNew(diag_name, "Class")
            diag.Update()
            cu_pkg.Diagrams.Refresh()

        # Marco UML 2.5
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()

        # Limpiar objetos y enlaces previos del diagrama
        while diag.DiagramObjects.Count > 0:
            diag.DiagramObjects.Delete(0)
        diag.DiagramObjects.Refresh()

        while diag.DiagramLinks.Count > 0:
            diag.DiagramLinks.Delete(0)
        diag.DiagramLinks.Refresh()

        # 1. Crear Actor
        actor = cu_pkg.Elements.AddNew(uc["actor"], "Actor")
        actor.Update()

        # 2. Formulario
        f_data = uc["form"]
        form = create_class_element(cu_pkg, f_data["name"], f_data["stereotype"], f_data["attributes"], f_data["methods"])

        # 3. Controller
        c_data = uc["controller"]
        ctrl = create_class_element(cu_pkg, c_data["name"], c_data["stereotype"], c_data["attributes"], c_data["methods"])

        # 4. Entidad Principal
        p_data = uc["primary_entity"]
        ent_p = create_class_element(cu_pkg, p_data["name"], p_data["stereotype"], p_data["attributes"], p_data["methods"])

        # 5. Entidades Secundarias
        sec_elements = []
        for s_data in uc["secondary_entities"]:
            s_el = create_class_element(cu_pkg, s_data["name"], s_data["stereotype"], s_data["attributes"], s_data["methods"])
            sec_elements.append((s_el, s_data["card_primary"], s_data["card_secondary"]))

        # 6. Disposición horizontal equilibrada sin solapamientos
        layout_positions = [
            (actor, 40, 110, -220, -300),
            (form, 150, 320, -110, -410),
            (ctrl, 380, 570, -150, -380),
            (ent_p, 640, 850, -110, -430),
            (sec_elements[0][0], 930, 1140, -40, -190),
            (sec_elements[1][0], 930, 1140, -220, -370),
            (sec_elements[2][0], 930, 1140, -400, -560),
        ]

        for el, l, r, t, b in layout_positions:
            obj = diag.DiagramObjects.AddNew("", "")
            obj.ElementID = el.ElementID
            obj.left = l
            obj.right = r
            obj.top = t
            obj.bottom = b
            obj.Update()

        # 7. Conectar elementos
        connect_classes(diag, actor, form)
        connect_classes(diag, form, ctrl)
        connect_classes(diag, ctrl, ent_p)

        for s_el, card_p, card_s in sec_elements:
            connect_classes(diag, ent_p, s_el, card_p, card_s)

        diag.Update()
        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        rep.SaveDiagram(diag.DiagramID)

        # 8. Exportar PNG de alta resolución
        export_path = os.path.join(EXPORT_DIR, uc["filename"])
        project.PutDiagramImageToFile(diag.DiagramGUID, export_path, 1)
        print(f"     Guardado PNG: {export_path}")


def main():
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)
    time.sleep(1)

    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE ANÁLISIS DE CLASES (CICLOS 1, 2 Y 3) — FASHIONSTORE")
    print("=" * 75)

    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"ERROR: No se pudo abrir {MODEL_PATH}")
        return 1

    try:
        project = rep.GetProjectInterface()
        root_model = rep.Models.GetAt(0)  # Model

        pkg_name = "04 - Diagramas de Analisis de Clases"

        # Buscar si ya existe el paquete para recrearlo limpio
        for i in range(root_model.Packages.Count - 1, -1, -1):
            p = root_model.Packages.GetAt(i)
            if "Diagramas de Analisis de Clases" in p.Name:
                print(f"Limpiando paquete previo: {p.Name}")
                root_model.Packages.Delete(i)
                root_model.Packages.Refresh()
                break

        main_analysis_pkg = root_model.Packages.AddNew(pkg_name, "")
        main_analysis_pkg.Notes = (
            "Diagramas de Análisis de Clases (UML 2.5) — Robustez BCE orientada a clases "
            "organizados por ciclos para todos los 23 Casos de Uso del sistema FashionStore."
        )
        main_analysis_pkg.Update()
        root_model.Packages.Refresh()

        print(f"Paquete contenedor creado: '{main_analysis_pkg.Name}' (ID: {main_analysis_pkg.PackageID})")

        # 1. Ciclo 1 (CU01 al CU09)
        generate_analysis_group(
            rep, project, main_analysis_pkg,
            "Ciclo 1 - Catálogo y Base",
            CYCLE_1_ANALYSIS
        )

        # 2. Ciclo 2 (CU10 al CU19)
        generate_analysis_group(
            rep, project, main_analysis_pkg,
            "Ciclo 2 - Operación Comercial y Logística",
            CYCLE_2_ANALYSIS
        )

        # 3. Ciclo 3 (CU12, CU20 al CU23)
        generate_analysis_group(
            rep, project, main_analysis_pkg,
            "Ciclo 3 - Innovación y Analítica",
            CYCLE_3_ANALYSIS
        )

        rep.SaveAllDiagrams()
        print("\n" + "=" * 75)
        print("¡TODOS LOS DIAGRAMAS DE ANÁLISIS DE CLASES (23 CUs) FUERON GENERADOS CON ÉXITO!")
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
