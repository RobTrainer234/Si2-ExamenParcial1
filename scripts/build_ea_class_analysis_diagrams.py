# -*- coding: utf-8 -*-
"""
Script maestro para generar los 10 Diagramas de Análisis de Clases (Robustez BCE)
de la Etapa 1 en Enterprise Architect (CasosDeUso_SegundoParcial.eap).

Reglas de Negocio y Metodología Estricta:
1. Clases Entidad con prefijo «E_» y estereotipo «Entidad», idénticas al modelo canónico.
2. Clase Formulario («Formulario») con atributos y métodos de interfaz.
3. Clase Controlador («Class») con SOLO MÉTODOS (sin atributos).
4. TODAS las relaciones y cardinalidades son 100% IDÉNTICAS al Diagrama Conceptual de la BD (Diagrama 11):
   - Tenant [1] <---> Subscription [1..*]
   - SubscriptionPlan [1] <---> Subscription [0..*]
   - Tenant [1] <---> Usuario [0..*]
   - Tenant [1] <---> Sucursal [0..*]
   - Sucursal [0..1] <---> Usuario [0..*]
   - Rol [1] <---> Usuario [0..*]
   - Tenant [1] <---> Bitacora [0..*]
   - Usuario [1] <---> Bitacora [0..*]
   - Usuario [1] <---> SyncOperation [0..*]
   - Categoria [1] <---> Producto [0..*]
   - Producto [1] <---> VarianteProducto [1..*]
   - VarianteProducto [1] <---> Inventario [0..*]
   - Sucursal [1] <---> Inventario [0..*]
5. Se respetan las tablas intermedias de relaciones N:M (ej. Inventario entre VarianteProducto y Sucursal, Subscription entre Tenant y SubscriptionPlan).

Archivo destino: 'docs/uml/FashioStore/CasosDeUso_SegundoParcial.eap'
Paquete destino: 'Segundo Parcial - Diagramas de Análisis de Clases (Etapa 1)'
"""

import os
import subprocess
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

# ----------------------------------------------------------------------
# Definición de los 10 Casos de Uso con relaciones y cardinalidades exactas de la BD
# ----------------------------------------------------------------------
CLASS_ANALYSIS_DATA = [
    {
        "code": "CU-01",
        "diag_name": "Analizar una clase CU-01 Registrar Empresa",
        "title": "CU-01 Registrar Empresa Contratante (Tenant)",
        "actor": "Superadmin SaaS",
        "form": {
            "name": "FormRegistroTenant",
            "attributes": [
                ("nombreEmpresa", "string"),
                ("subdominio", "string"),
                ("emailAdmin", "string"),
                ("passwordAdmin", "string"),
                ("codigoPlan", "string"),
                ("estaCargando", "boolean")
            ],
            "methods": [
                ("solicitarRegistro()", "void"),
                ("validarFormulario()", "boolean"),
                ("limpiarCampos()", "void"),
                ("mostrarNotificacion(mensaje)", "void")
            ]
        },
        "controller": {
            "name": "TenantController",
            "attributes": [],  # SOLO METODOS
            "methods": [
                ("register_tenant(datos)", "JsonResponse"),
                ("verify_subdomain_availability(subdominio)", "JsonResponse"),
                ("list_tenants()", "JsonResponse"),
                ("update_tenant_status(id, estado)", "JsonResponse")
            ]
        },
        "main_entity": "E_Tenant",
        "entities": [
            {
                "name": "E_Tenant",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("subdominio", "string"),
                    ("ruc_nit", "string"),
                    ("estado", "string"),
                    ("fecha_registro", "datetime")
                ],
                "methods": [
                    ("crearTenant()", "void"),
                    ("validarSubdominio()", "boolean"),
                    ("activarTenant()", "void"),
                    ("desactivarTenant()", "void")
                ]
            },
            {
                "name": "E_Subscription",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("fecha_inicio", "date"),
                    ("fecha_fin", "date"),
                    ("estado", "string")
                ],
                "methods": [
                    ("crearSuscripcionInicial()", "void"),
                    ("verificarVigencia()", "boolean")
                ]
            },
            {
                "name": "E_SubscriptionPlan",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("nombre", "string"),
                    ("max_sucursales", "integer"),
                    ("max_usuarios", "integer"),
                    ("soporte_ia", "boolean")
                ],
                "methods": [
                    ("obtenerLimitesPlan()", "object")
                ]
            },
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("tenant_id", "integer"),
                    ("email", "string"),
                    ("password_hash", "string"),
                    ("rol_id", "integer"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("crearUsuarioAdmin()", "void"),
                    ("encriptarPassword()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("tenant_id", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarAuditoria()", "void")
                ]
            }
        ],
        "relationships": [
            # Tenant [1] <---> [1..*] Subscription
            ("E_Tenant", "E_Subscription", "1", "1..*"),
            # SubscriptionPlan [1] <---> [0..*] Subscription
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            # Tenant [1] <---> [0..*] Usuario
            ("E_Tenant", "E_Usuario", "1", "0..*"),
            # Tenant [1] <---> [0..*] Bitacora
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-02",
        "diag_name": "Analizar una clase CU-02 Gestionar Planes",
        "title": "CU-02 Gestionar Planes de Suscripción",
        "actor": "Superadmin SaaS",
        "form": {
            "name": "FormPlanSuscripcion",
            "attributes": [
                ("codigoPlan", "string"),
                ("nombrePlan", "string"),
                ("precioMensual", "decimal"),
                ("precioAnual", "decimal"),
                ("limiteSucursales", "integer"),
                ("habilitaIA", "boolean")
            ],
            "methods": [
                ("guardarPlan()", "void"),
                ("actualizarLimites()", "void"),
                ("cambiarEstado()", "void"),
                ("listarPlanes()", "void")
            ]
        },
        "controller": {
            "name": "SubscriptionPlanController",
            "attributes": [],
            "methods": [
                ("list_all_plans()", "JsonResponse"),
                ("create_subscription_plan(datos)", "JsonResponse"),
                ("update_plan_quotas(plan_id, cuotas)", "JsonResponse"),
                ("toggle_plan_status(plan_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_SubscriptionPlan",
        "entities": [
            {
                "name": "E_SubscriptionPlan",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("nombre", "string"),
                    ("precio_mensual", "decimal"),
                    ("precio_anual", "decimal"),
                    ("max_sucursales", "integer"),
                    ("max_usuarios", "integer"),
                    ("soporte_ia", "boolean"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("insertarPlan()", "void"),
                    ("modificarCuotas()", "void"),
                    ("desactivarPlan()", "void"),
                    ("listarActivos()", "list")
                ]
            },
            {
                "name": "E_Subscription",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("estado", "string")
                ],
                "methods": [
                    ("contarEmpresasSuscritas()", "integer")
                ]
            },
            {
                "name": "E_Tenant",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("obtenerDatosEmpresa()", "object")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("tenant_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarAuditoria()", "void")
                ]
            }
        ],
        "relationships": [
            # SubscriptionPlan [1] <---> [0..*] Subscription
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            # Tenant [1] <---> [1..*] Subscription
            ("E_Tenant", "E_Subscription", "1", "1..*"),
            # Tenant [1] <---> [0..*] Bitacora
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-03",
        "diag_name": "Analizar una clase CU-03 Asignar Renovar Suscripcion",
        "title": "CU-03 Asignar y Renovar Suscripción de Empresa",
        "actor": "Superadmin SaaS",
        "form": {
            "name": "FormSuscripcion",
            "attributes": [
                ("idTenant", "integer"),
                ("codigoPlan", "string"),
                ("periodoMeses", "integer"),
                ("metodoPago", "string"),
                ("estadoActual", "string")
            ],
            "methods": [
                ("SolicitarRenovacion()", "void"),
                ("CambiarPlan()", "void"),
                ("CancelarSuscripcion()", "void"),
                ("ConsultarEstado()", "void")
            ]
        },
        "controller": {
            "name": "SubscriptionController",
            "attributes": [],
            "methods": [
                ("assign_or_renew_subscription(tenant_id, datos)", "JsonResponse"),
                ("get_subscription_status(tenant_id)", "JsonResponse"),
                ("cancel_subscription(subscription_id)", "JsonResponse"),
                ("list_subscription_history(tenant_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Subscription",
        "entities": [
            {
                "name": "E_Subscription",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("fecha_inicio", "date"),
                    ("fecha_fin", "date"),
                    ("estado", "string"),
                    ("auto_renovar", "boolean")
                ],
                "methods": [
                    ("asignarNuevoPlan()", "void"),
                    ("extenderVigencia(meses)", "void"),
                    ("cancelarSuscripcion()", "void"),
                    ("estaVigente()", "boolean")
                ]
            },
            {
                "name": "E_Tenant",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("actualizarEstadoAcceso(estado)", "void")
                ]
            },
            {
                "name": "E_SubscriptionPlan",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("precio_mensual", "decimal"),
                    ("precio_anual", "decimal")
                ],
                "methods": [
                    ("calcularCostoRenovacion(periodo)", "decimal")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("tenant_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarAuditoria()", "void")
                ]
            }
        ],
        "relationships": [
            # Tenant [1] <---> [1..*] Subscription
            ("E_Tenant", "E_Subscription", "1", "1..*"),
            # SubscriptionPlan [1] <---> [0..*] Subscription
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            # Tenant [1] <---> [0..*] Bitacora
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-04",
        "diag_name": "Analizar una clase CU-04 Controlar Limites Plan",
        "title": "CU-04 Controlar Límites y Restricciones por Plan",
        "actor": "Tenant Admin",
        "form": {
            "name": "FormControlLimites",
            "attributes": [
                ("tipoRecurso", "string"),
                ("cuotaActual", "integer"),
                ("cuotaMaxima", "integer"),
                ("alertaBloqueo", "string")
            ],
            "methods": [
                ("verificarCuota()", "boolean"),
                ("mostrarModalAlertaBloqueo()", "void"),
                ("solicitarUpgradePlan()", "void")
            ]
        },
        "controller": {
            "name": "PlanLimitsController",
            "attributes": [],
            "methods": [
                ("verify_resource_quota(tenant_id, recurso)", "JsonResponse"),
                ("get_usage_metrics(tenant_id)", "JsonResponse"),
                ("check_ia_module_permission(tenant_id)", "JsonResponse"),
                ("log_quota_exceeded(tenant_id, recurso)", "JsonResponse")
            ]
        },
        "main_entity": "E_Tenant",
        "entities": [
            {
                "name": "E_Tenant",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("consultarConsumoRecursos()", "object"),
                    ("bloquearAccionesPorCuota()", "void")
                ]
            },
            {
                "name": "E_Subscription",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("estado", "string")
                ],
                "methods": [
                    ("verificarEstadoActivo()", "boolean")
                ]
            },
            {
                "name": "E_SubscriptionPlan",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("max_sucursales", "integer"),
                    ("max_usuarios", "integer"),
                    ("soporte_ia", "boolean")
                ],
                "methods": [
                    ("validarLimiteSucursales(actual)", "boolean"),
                    ("validarLimiteUsuarios(actual)", "boolean"),
                    ("validarAccesoIA()", "boolean")
                ]
            },
            {
                "name": "E_Sucursal",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("contarSucursalesActivas()", "integer")
                ]
            },
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("contarUsuariosActivos()", "integer")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("tenant_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarIntentoExceso()", "void")
                ]
            }
        ],
        "relationships": [
            # Tenant [1] <---> [1..*] Subscription
            ("E_Tenant", "E_Subscription", "1", "1..*"),
            # SubscriptionPlan [1] <---> [0..*] Subscription
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            # Tenant [1] <---> [0..*] Sucursal
            ("E_Tenant", "E_Sucursal", "1", "0..*"),
            # Sucursal [0..1] <---> [0..*] Usuario
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            # Tenant [1] <---> [0..*] Bitacora
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-05",
        "diag_name": "Analizar una clase CU-05 Gestionar Sucursales Empleados",
        "title": "CU-05 Gestionar Sucursales y Empleados por Tenant",
        "actor": "Tenant Admin",
        "form": {
            "name": "FormSucursalEmpleado",
            "attributes": [
                ("nombreSucursal", "string"),
                ("direccion", "string"),
                ("ciudadId", "integer"),
                ("telefono", "string"),
                ("empleadoId", "integer"),
                ("rolEmpleado", "string")
            ],
            "methods": [
                ("RegistrarSucursal()", "void"),
                ("ModificarSucursal()", "void"),
                ("AsignarEmpleado()", "void"),
                ("DesactivarSucursal()", "void")
            ]
        },
        "controller": {
            "name": "BranchEmployeeController",
            "attributes": [],
            "methods": [
                ("list_branches(tenant_id)", "JsonResponse"),
                ("create_branch(datos)", "JsonResponse"),
                ("assign_employee_branch(user_id, branch_id)", "JsonResponse"),
                ("toggle_branch_status(branch_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Sucursal",
        "entities": [
            {
                "name": "E_Sucursal",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("nombre", "string"),
                    ("direccion", "string"),
                    ("telefono", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("crearSucursal()", "void"),
                    ("actualizarDatos()", "void"),
                    ("cambiarEstado(activo)", "void"),
                    ("obtenerPorTenant(tenant_id)", "list")
                ]
            },
            {
                "name": "E_Tenant",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("validarPertenenciaTenant()", "boolean")
                ]
            },
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer"),
                    ("rol_id", "integer"),
                    ("nombre", "string"),
                    ("email", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("reasignarSucursal(suc_id)", "void"),
                    ("listarEmpleadosPorSucursal()", "list")
                ]
            },
            {
                "name": "E_Rol",
                "attributes": [
                    ("id_rol", "integer"),
                    ("nombre", "string"),
                    ("descripcion", "string")
                ],
                "methods": [
                    ("verificarRolOperativo()", "boolean")
                ]
            }
        ],
        "relationships": [
            # Tenant [1] <---> [0..*] Sucursal
            ("E_Tenant", "E_Sucursal", "1", "0..*"),
            # Sucursal [0..1] <---> [0..*] Usuario
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            # Rol [1] <---> [0..*] Usuario
            ("E_Rol", "E_Usuario", "1", "0..*")
        ]
    },
    {
        "code": "CU-06",
        "diag_name": "Analizar una clase CU-06 Descargar Catalogo Offline",
        "title": "CU-06 Descargar y Almacenar Catálogo Offline",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormSincronizacionCatalogo",
            "attributes": [
                ("idSucursal", "integer"),
                ("fechaUltimaSync", "datetime"),
                ("totalPrendasDescargadas", "integer"),
                ("porcentajeProgreso", "integer")
            ],
            "methods": [
                ("IniciarDescarga()", "void"),
                ("LimpiarAlmacenamientoLocal()", "void"),
                ("MostrarProgresoDescarga(pct)", "void")
            ]
        },
        "controller": {
            "name": "SyncCatalogController",
            "attributes": [],
            "methods": [
                ("fetch_catalog_snapshot(sucursal_id, timestamp)", "JsonResponse"),
                ("acknowledge_sync_completion(sucursal_id, op_id)", "JsonResponse"),
                ("get_delta_catalog(sucursal_id, last_timestamp)", "JsonResponse")
            ]
        },
        "main_entity": "E_Producto",
        "entities": [
            {
                "name": "E_Producto",
                "attributes": [
                    ("id_producto", "integer"),
                    ("tenant_id", "integer"),
                    ("categoria_id", "integer"),
                    ("codigo_base", "string"),
                    ("nombre", "string"),
                    ("precio_base", "decimal"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("obtenerCatalogoParaDescarga()", "list"),
                    ("persistirCatalogoLocal()", "void")
                ]
            },
            {
                "name": "E_Categoria",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerCategoriasActivas()", "list")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("sku", "string"),
                    ("codigo_barras", "string"),
                    ("talla_id", "integer"),
                    ("color_id", "integer"),
                    ("precio", "decimal")
                ],
                "methods": [
                    ("obtenerVariantesPorProducto()", "list"),
                    ("guardarVariantesLocales()", "void")
                ]
            },
            {
                "name": "E_Inventario",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("variante_id", "integer"),
                    ("sucursal_id", "integer"),
                    ("stock_fisico", "integer"),
                    ("stock_reservado", "integer")
                ],
                "methods": [
                    ("guardarStockLocal()", "void"),
                    ("consultarStockSucursal(suc_id)", "integer")
                ]
            },
            {
                "name": "E_Sucursal",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerDatosSucursal()", "object")
                ]
            },
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerUsuarioOperador()", "object")
                ]
            },
            {
                "name": "E_SyncOperation",
                "attributes": [
                    ("id_sync_op", "integer"),
                    ("usuario_id", "integer"),
                    ("operacion_tipo", "string"),
                    ("timestamp_local", "datetime"),
                    ("estado", "string")
                ],
                "methods": [
                    ("registrarDescargaExitosa()", "void")
                ]
            }
        ],
        "relationships": [
            # Categoria [1] <---> [0..*] Producto
            ("E_Categoria", "E_Producto", "1", "0..*"),
            # Producto [1] <---> [1..*] VarianteProducto
            ("E_Producto", "E_VarianteProducto", "1", "1..*"),
            # VarianteProducto [1] <---> [0..*] Inventario
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            # Sucursal [1] <---> [0..*] Inventario (Clase intermedia N:M Inventario)
            ("E_Sucursal", "E_Inventario", "1", "0..*"),
            # Sucursal [0..1] <---> [0..*] Usuario
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            # Usuario [1] <---> [0..*] SyncOperation
            ("E_Usuario", "E_SyncOperation", "1", "0..*")
        ]
    },
    {
        "code": "CU-07",
        "diag_name": "Analizar una clase CU-07 Consultar Catalogo Existencias",
        "title": "CU-07 Consultar Catálogo y Existencias Offline",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormCatalogoOffline",
            "attributes": [
                ("textoBusqueda", "string"),
                ("categoriaSeleccionada", "integer"),
                ("filtroTalla", "string"),
                ("filtroColor", "string"),
                ("codigoEscaneado", "string")
            ],
            "methods": [
                ("BuscarPorFiltro()", "void"),
                ("EscanearCodigoBarras()", "void"),
                ("SeleccionarPrenda()", "void"),
                ("MostrarAlertaStockBajo()", "void")
            ]
        },
        "controller": {
            "name": "OfflineCatalogController",
            "attributes": [],
            "methods": [
                ("query_local_products(filtro, cat_id)", "JsonResponse"),
                ("get_variant_by_barcode(codigo)", "JsonResponse"),
                ("check_local_stock_level(variante_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Producto",
        "entities": [
            {
                "name": "E_Producto",
                "attributes": [
                    ("id_producto", "integer"),
                    ("categoria_id", "integer"),
                    ("codigo_base", "string"),
                    ("nombre", "string"),
                    ("precio_base", "decimal")
                ],
                "methods": [
                    ("buscarEnCatalogoLocal(query)", "list"),
                    ("obtenerDetalleProducto(id)", "object")
                ]
            },
            {
                "name": "E_Categoria",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("filtrarJerarquiaLocal()", "list")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("sku", "string"),
                    ("codigo_barras", "string"),
                    ("precio", "decimal")
                ],
                "methods": [
                    ("buscarPorSKUOBarra(cod)", "object"),
                    ("filtrarPorTallaColor(t, c)", "list")
                ]
            },
            {
                "name": "E_Inventario",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("variante_id", "integer"),
                    ("sucursal_id", "integer"),
                    ("stock_fisico", "integer"),
                    ("stock_reservado", "integer")
                ],
                "methods": [
                    ("calcularStockDisponible()", "integer"),
                    ("estaBajoMinimo(umbral)", "boolean")
                ]
            },
            {
                "name": "E_Sucursal",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerSucursalActual()", "object")
                ]
            }
        ],
        "relationships": [
            # Categoria [1] <---> [0..*] Producto
            ("E_Categoria", "E_Producto", "1", "0..*"),
            # Producto [1] <---> [1..*] VarianteProducto
            ("E_Producto", "E_VarianteProducto", "1", "1..*"),
            # VarianteProducto [1] <---> [0..*] Inventario
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            # Sucursal [1] <---> [0..*] Inventario (Clase intermedia N:M Inventario)
            ("E_Sucursal", "E_Inventario", "1", "0..*")
        ]
    },
    {
        "code": "CU-23",
        "diag_name": "Analizar una clase CU-23 Notificar Conectividad",
        "title": "CU-23 Notificar Estado de Conectividad (Semáforo)",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormSemaforoConectividad",
            "attributes": [
                ("estadoRed", "string"),
                ("latenciaMs", "integer"),
                ("transaccionesEnCola", "integer"),
                ("mensajeAlerta", "string")
            ],
            "methods": [
                ("ActualizarSemaforo(estado)", "void"),
                ("DesplegarPanelColaPendiente()", "void"),
                ("ReintentarConexion()", "void")
            ]
        },
        "controller": {
            "name": "NetworkMonitorController",
            "attributes": [],
            "methods": [
                ("detect_connection_state()", "JsonResponse"),
                ("get_outbox_queue_count(sucursal_id)", "JsonResponse"),
                ("trigger_network_reconnect()", "JsonResponse")
            ]
        },
        "main_entity": "E_Usuario",
        "entities": [
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("verificarSesionOperador()", "boolean")
                ]
            },
            {
                "name": "E_SyncOperation",
                "attributes": [
                    ("id_sync_op", "integer"),
                    ("usuario_id", "integer"),
                    ("tipo_transaccion", "string"),
                    ("payload_json", "string"),
                    ("estado_sync", "string"),
                    ("fecha_registro", "datetime")
                ],
                "methods": [
                    ("contarPendientesPorUsuario(usr_id)", "integer"),
                    ("listarColaSalida(usr_id)", "list"),
                    ("marcarEnProcesamiento(id)", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarCambioRed(evento)", "void")
                ]
            }
        ],
        "relationships": [
            # Usuario [1] <---> [0..*] SyncOperation
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            # Usuario [1] <---> [0..*] Bitacora
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-24",
        "diag_name": "Analizar una clase CU-24 Instalar Service Worker",
        "title": "CU-24 Instalar y Registrar Service Worker (PWA)",
        "actor": "Usuario Web",
        "form": {
            "name": "FormInstaladorPWA",
            "attributes": [
                ("bannerInstalacionVisible", "boolean"),
                ("soporteWorkerDetectado", "boolean"),
                ("versionCachada", "string")
            ],
            "methods": [
                ("MostrarPromptInstalacion()", "void"),
                ("AceptarInstalacion()", "void"),
                ("NotificarModoOfflineListo()", "void")
            ]
        },
        "controller": {
            "name": "ServiceWorkerController",
            "attributes": [],
            "methods": [
                ("register_service_worker(scope_url)", "JsonResponse"),
                ("precache_static_app_shell()", "JsonResponse"),
                ("handle_background_sync_tag(tag)", "JsonResponse")
            ]
        },
        "main_entity": "E_Usuario",
        "entities": [
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("email", "string"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerUsuarioWeb()", "object")
                ]
            },
            {
                "name": "E_SyncOperation",
                "attributes": [
                    ("id_sync_op", "integer"),
                    ("usuario_id", "integer"),
                    ("sync_tag", "string"),
                    ("payload_json", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("registrarCanalBackgroundSync()", "void"),
                    ("procesarColaSincronizacion()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarEventoPWA()", "void")
                ]
            }
        ],
        "relationships": [
            # Usuario [1] <---> [0..*] SyncOperation
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            # Usuario [1] <---> [0..*] Bitacora
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-25",
        "diag_name": "Analizar una clase CU-25 Configurar SQLite Movil",
        "title": "CU-25 Configurar y Migrar Persistencia SQLite Móvil",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormConfiguracionSQLite",
            "attributes": [
                ("versionEsquemaActual", "integer"),
                ("migracionPendiente", "boolean"),
                ("integridadOK", "boolean")
            ],
            "methods": [
                ("ValidarIntegridad()", "void"),
                ("AplicarMigracion()", "void"),
                ("MostrarEstadoBD()", "void")
            ]
        },
        "controller": {
            "name": "DatabaseMigrationController",
            "attributes": [],
            "methods": [
                ("check_sqlite_schema_version()", "JsonResponse"),
                ("execute_pending_migrations()", "JsonResponse"),
                ("verify_database_pragmas()", "JsonResponse")
            ]
        },
        "main_entity": "E_Sucursal",
        "entities": [
            {
                "name": "E_Sucursal",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string"),
                    ("ciudad_id", "integer")
                ],
                "methods": [
                    ("obtenerSucursalLocal()", "object")
                ]
            },
            {
                "name": "E_Inventario",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("variante_id", "integer"),
                    ("sucursal_id", "integer"),
                    ("stock_fisico", "integer")
                ],
                "methods": [
                    ("crearTablaInventarioSQLite()", "void")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "attributes": [
                    ("id_variante", "integer"),
                    ("sku", "string"),
                    ("codigo_barras", "string"),
                    ("precio", "decimal")
                ],
                "methods": [
                    ("crearTablaVariantesSQLite()", "void")
                ]
            },
            {
                "name": "E_Usuario",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer"),
                    ("email", "string")
                ],
                "methods": [
                    ("obtenerOperadorDispositivo()", "object")
                ]
            },
            {
                "name": "E_SyncOperation",
                "attributes": [
                    ("id_sync_op", "integer"),
                    ("usuario_id", "integer"),
                    ("uuid_transaccion", "string"),
                    ("operacion_tipo", "string"),
                    ("payload_json", "string")
                ],
                "methods": [
                    ("crearTablaSyncOperationsSQLite()", "void"),
                    ("verificarIntegridadTransaccional()", "boolean")
                ]
            },
            {
                "name": "E_Bitacora",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("detalle_version", "string")
                ],
                "methods": [
                    ("registrarMigracionSQLite()", "void")
                ]
            }
        ],
        "relationships": [
            # Sucursal [1] <---> [0..*] Inventario
            ("E_Sucursal", "E_Inventario", "1", "0..*"),
            # VarianteProducto [1] <---> [0..*] Inventario
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            # Sucursal [0..1] <---> [0..*] Usuario
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            # Usuario [1] <---> [0..*] SyncOperation
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            # Usuario [1] <---> [0..*] Bitacora
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    }
]

def build_class_analysis_diagrams():
    print("1. Limpiando procesos previos de EA...")
    subprocess.run(["taskkill", "/F", "/IM", "EA.exe"], capture_output=True)

    print(f"2. Abriendo repositorio EA: {EAP_PATH} ...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(EAP_PATH):
        raise RuntimeError(f"No se pudo abrir el archivo EA: {EAP_PATH}")

    root_model = rep.Models.GetAt(0)

    # Buscar paquete para Diagramas de Análisis de Clases (Etapa 1)
    pkg_name = "Segundo Parcial - Diagramas de Análisis de Clases (Etapa 1)"
    class_pkg = None
    for i in range(root_model.Packages.Count):
        p = root_model.Packages.GetAt(i)
        if p.Name == pkg_name:
            class_pkg = p
            break

    if class_pkg is None:
        class_pkg = root_model.Packages.AddNew(pkg_name, "")
        class_pkg.Notes = "Diagramas de Análisis de Clases (Robustez BCE) para los 10 Casos de Uso de la Etapa 1 con cardinalidades de la BD."
        class_pkg.Update()
        root_model.Packages.Refresh()

    print(f"3. Paquete objetivo: '{class_pkg.Name}' (ID: {class_pkg.PackageID})")

    # Limpiar diagramas y elementos anteriores en este paquete para reconstrucción limpia
    print("4. Limpiando diagramas y elementos anteriores en el paquete...")
    for i in range(class_pkg.Diagrams.Count - 1, -1, -1):
        class_pkg.Diagrams.Delete(i)
    class_pkg.Diagrams.Refresh()

    for i in range(class_pkg.Elements.Count - 1, -1, -1):
        class_pkg.Elements.Delete(i)
    class_pkg.Elements.Refresh()

    print(f"5. Generando los {len(CLASS_ANALYSIS_DATA)} Diagramas de Análisis de Clases con cardinalidades exactas de la BD...")

    for cu in CLASS_ANALYSIS_DATA:
        diag_title = cu["diag_name"]
        print(f"   -> Creando diagrama: {diag_title} ({cu['title']})...")

        diag = class_pkg.Diagrams.AddNew(diag_title, "Logical")
        diag.Update()
        class_pkg.Diagrams.Refresh()

        created_elements = {}

        # 1. Actor
        el_act = class_pkg.Elements.AddNew(cu["actor"], "Actor")
        el_act.Update()
        created_elements["actor"] = el_act
        o_act = diag.DiagramObjects.AddNew("l=40;r=90;t=-200;b=-290;", "")
        o_act.ElementID = el_act.ElementID
        o_act.Update()

        # 2. Formulario («Formulario»)
        form_spec = cu["form"]
        el_form = class_pkg.Elements.AddNew(form_spec["name"], "Class")
        el_form.Stereotype = "Formulario"
        el_form.Update()
        for attr_name, attr_type in form_spec["attributes"]:
            att = el_form.Attributes.AddNew(attr_name, attr_type)
            att.Update()
        for met_name, met_ret in form_spec["methods"]:
            met = el_form.Methods.AddNew(met_name, met_ret)
            met.Update()
        el_form.Attributes.Refresh()
        el_form.Methods.Refresh()
        el_form.Update()
        created_elements["form"] = el_form

        o_form = diag.DiagramObjects.AddNew("l=140;r=340;t=-100;b=-420;", "")
        o_form.ElementID = el_form.ElementID
        o_form.Update()

        # 3. Controlador («Class» / Controlador) - SOLO METODOS (sin atributos)
        ctrl_spec = cu["controller"]
        el_ctrl = class_pkg.Elements.AddNew(ctrl_spec["name"], "Class")
        el_ctrl.Stereotype = "Class"
        el_ctrl.Update()
        for met_name, met_ret in ctrl_spec["methods"]:
            met = el_ctrl.Methods.AddNew(met_name, met_ret)
            met.Update()
        el_ctrl.Methods.Refresh()
        el_ctrl.Update()
        created_elements["controller"] = el_ctrl

        o_ctrl = diag.DiagramObjects.AddNew("l=390;r=610;t=-140;b=-380;", "")
        o_ctrl.ElementID = el_ctrl.ElementID
        o_ctrl.Update()

        # 4. Entidades («Entidad») con prefijo E_
        main_ent_name = cu["main_entity"]
        el_main = None

        sec_layout_coords = [
            ("l=970;r=1220;t=-30;b=-180;"),
            ("l=970;r=1220;t=-200;b=-350;"),
            ("l=970;r=1220;t=-370;b=-520;"),
            ("l=970;r=1220;t=-540;b=-690;"),
            ("l=970;r=1220;t=-710;b=-860;"),
            ("l=970;r=1220;t=-880;b=-1030;")
        ]
        sec_idx = 0

        for ent_spec in cu["entities"]:
            el_ent = class_pkg.Elements.AddNew(ent_spec["name"], "Class")
            el_ent.Stereotype = "Entidad"
            el_ent.Update()
            for attr_name, attr_type in ent_spec["attributes"]:
                att = el_ent.Attributes.AddNew(attr_name, attr_type)
                att.Update()
            for met_name, met_ret in ent_spec["methods"]:
                met = el_ent.Methods.AddNew(met_name, met_ret)
                met.Update()
            el_ent.Attributes.Refresh()
            el_ent.Methods.Refresh()
            el_ent.Update()
            created_elements[ent_spec["name"]] = el_ent

            if ent_spec["name"] == main_ent_name:
                el_main = el_ent
                o_main = diag.DiagramObjects.AddNew("l=660;r=900;t=-100;b=-440;", "")
                o_main.ElementID = el_main.ElementID
                o_main.Update()
            else:
                coord = sec_layout_coords[sec_idx % len(sec_layout_coords)]
                sec_idx += 1
                o_sec = diag.DiagramObjects.AddNew(coord, "")
                o_sec.ElementID = el_ent.ElementID
                o_sec.Update()

        # Conectar Actor -> Formulario
        con_act_form = el_act.Connectors.AddNew("", "Association")
        con_act_form.SupplierID = el_form.ElementID
        con_act_form.Update()
        el_act.Connectors.Refresh()
        l_af = diag.DiagramLinks.AddNew("", "")
        l_af.ConnectorID = con_act_form.ConnectorID
        l_af.Update()

        # Conectar Formulario -> Controlador
        con_form_ctrl = el_form.Connectors.AddNew("", "Association")
        con_form_ctrl.SupplierID = el_ctrl.ElementID
        con_form_ctrl.Update()
        el_form.Connectors.Refresh()
        l_fc = diag.DiagramLinks.AddNew("", "")
        l_fc.ConnectorID = con_form_ctrl.ConnectorID
        l_fc.Update()

        # Conectar Controlador -> Entidad Principal
        con_ctrl_main = el_ctrl.Connectors.AddNew("", "Association")
        con_ctrl_main.SupplierID = el_main.ElementID
        con_ctrl_main.Update()
        el_ctrl.Connectors.Refresh()
        l_cm = diag.DiagramLinks.AddNew("", "")
        l_cm.ConnectorID = con_ctrl_main.ConnectorID
        l_cm.Update()

        # Conectar Entidades entre sí con las cardinalidades exactas de la Base de Datos
        for src_name, dst_name, card_src, card_dst in cu["relationships"]:
            el_src = created_elements[src_name]
            el_dst = created_elements[dst_name]

            con_rel = el_src.Connectors.AddNew("", "Association")
            con_rel.SupplierID = el_dst.ElementID
            con_rel.ClientEnd.Cardinality = card_src
            con_rel.SupplierEnd.Cardinality = card_dst
            con_rel.Update()
            el_src.Connectors.Refresh()

            l_rel = diag.DiagramLinks.AddNew("", "")
            l_rel.ConnectorID = con_rel.ConnectorID
            l_rel.Update()

        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        diag.Update()

    class_pkg.Diagrams.Refresh()
    class_pkg.Elements.Refresh()

    rep.CloseFile()
    rep.Exit()
    print("=" * 70)
    print("EXITO: LOS 10 DIAGRAMAS DE ANÁLISIS DE CLASES FUERON GENERADOS CON CARDINALIDADES EXACTAS")
    print(f"Repositorio EA: {EAP_PATH}")
    print(f"Paquete EA: {pkg_name}")
    print("=" * 70)

if __name__ == "__main__":
    build_class_analysis_diagrams()
