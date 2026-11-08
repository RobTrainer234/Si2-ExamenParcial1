"""
Reconstrucción y Corrección Rigurosa de los 10 Diagramas de Análisis de Clases (Etapa 1)
y Sincronización con el Diagrama Conceptual de la Base de Datos en Enterprise Architect.

Corrige:
1. Cardinalidad Tenant [1] <---> [0..*] Subscription (contrata) tanto en Diagrama 11 como en los 10 diagramas.
2. Cardinalidad SubscriptionPlan [1] <---> [0..*] Subscription (define).
3. Espaciado y posicionamiento no superpuesto (Layout en árbol/rejilla) para evitar colisiones de etiquetas.
4. Cumplimiento estricto del estándar de Robustez BCE y del ejemplo de referencia:
   - Actor -> Formulario («Formulario») -> Controlador («Class», solo métodos) -> Entidad Principal («Entidad») -> Entidades Secundarias («Entidad»).
"""

import subprocess
import win32com.client

EAP_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\CasosDeUso_SegundoParcial.eap"

# Datos detallados de los 10 Casos de Uso
CU_DATA = [
    {
        "code": "CU-01",
        "diag_name": "Analizar una clase CU-01 Registrar Empresa",
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
            "attributes": [],
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
                "pos": "l=660;r=900;t=-100;b=-440;",
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
                "pos": "l=970;r=1210;t=-40;b=-220;",
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
                "pos": "l=1280;r=1520;t=-40;b=-220;",
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
                "pos": "l=970;r=1210;t=-280;b=-480;",
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
                "pos": "l=970;r=1210;t=-540;b=-740;",
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
            ("E_Tenant", "E_Subscription", "1", "0..*"),
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            ("E_Tenant", "E_Usuario", "1", "0..*"),
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-02",
        "diag_name": "Analizar una clase CU-02 Gestionar Planes",
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
                "pos": "l=660;r=900;t=-100;b=-440;",
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
                "pos": "l=970;r=1210;t=-100;b=-300;",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("estado", "string")
                ],
                "methods": [
                    ("asociarPlan()", "void"),
                    ("verificarEstado()", "string")
                ]
            },
            {
                "name": "E_Tenant",
                "pos": "l=1280;r=1520;t=-100;b=-300;",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("subdominio", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("bloquearPorMora()", "void"),
                    ("reactivar()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=1280;r=1520;t=-360;b=-560;",
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
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            ("E_Tenant", "E_Subscription", "1", "0..*"),
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-03",
        "diag_name": "Analizar una clase CU-03 Asignar Renovar Suscripcion",
        "actor": "Superadmin SaaS",
        "form": {
            "name": "FormSuscripcion",
            "attributes": [
                ("tenantId", "integer"),
                ("planId", "integer"),
                ("mesesRenovacion", "integer"),
                ("metodoPago", "string"),
                ("comprobante", "string")
            ],
            "methods": [
                ("solicitarAsignacion()", "void"),
                ("solicitarRenovacion()", "void"),
                ("validarPago()", "boolean"),
                ("imprimirRecibo()", "void")
            ]
        },
        "controller": {
            "name": "SubscriptionController",
            "attributes": [],
            "methods": [
                ("assign_plan_to_tenant(tenant_id, plan_id)", "JsonResponse"),
                ("renew_subscription(subscription_id, meses)", "JsonResponse"),
                ("get_subscription_status(tenant_id)", "JsonResponse"),
                ("cancel_subscription(subscription_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Subscription",
        "entities": [
            {
                "name": "E_Subscription",
                "pos": "l=660;r=900;t=-100;b=-440;",
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
                    ("renovarPeriodo(meses)", "void"),
                    ("cancelar()", "void"),
                    ("cambiarPlan(nuevo_plan_id)", "void")
                ]
            },
            {
                "name": "E_Tenant",
                "pos": "l=970;r=1210;t=-40;b=-240;",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("estado", "string")
                ],
                "methods": [
                    ("actualizarEstadoSuscripcion()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=1280;r=1520;t=-40;b=-240;",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("tenant_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarAuditoria()", "void")
                ]
            },
            {
                "name": "E_SubscriptionPlan",
                "pos": "l=970;r=1210;t=-300;b=-500;",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("nombre", "string"),
                    ("precio_mensual", "decimal")
                ],
                "methods": [
                    ("calcularCosto(meses)", "decimal")
                ]
            }
        ],
        "relationships": [
            ("E_Tenant", "E_Subscription", "1", "0..*"),
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-04",
        "diag_name": "Analizar una clase CU-04 Controlar Limites Plan",
        "actor": "Tenant Admin",
        "form": {
            "name": "FormControlLimites",
            "attributes": [
                ("tipoRecurso", "string"),
                ("totalActual", "integer"),
                ("maximoPermitido", "integer"),
                ("alertaExcedido", "boolean")
            ],
            "methods": [
                ("cargarConsumos()", "void"),
                ("mostrarAlertaLimite()", "void"),
                ("bloquearCreacion()", "void"),
                ("solicitarUpgrade()", "void")
            ]
        },
        "controller": {
            "name": "PlanLimitsController",
            "attributes": [],
            "methods": [
                ("check_user_quota(tenant_id)", "JsonResponse"),
                ("check_branch_quota(tenant_id)", "JsonResponse"),
                ("get_quota_summary(tenant_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Tenant",
        "entities": [
            {
                "name": "E_Tenant",
                "pos": "l=660;r=900;t=-140;b=-480;",
                "attributes": [
                    ("id_tenant", "integer"),
                    ("nombre", "string"),
                    ("max_usuarios", "integer"),
                    ("max_sucursales", "integer")
                ],
                "methods": [
                    ("validarLimiteUsuarios()", "boolean"),
                    ("validarLimiteSucursales()", "boolean")
                ]
            },
            {
                "name": "E_Subscription",
                "pos": "l=970;r=1210;t=-20;b=-200;",
                "attributes": [
                    ("id_suscripcion", "integer"),
                    ("tenant_id", "integer"),
                    ("plan_id", "integer"),
                    ("estado", "string")
                ],
                "methods": [
                    ("verificarVigencia()", "boolean")
                ]
            },
            {
                "name": "E_SubscriptionPlan",
                "pos": "l=1280;r=1520;t=-20;b=-200;",
                "attributes": [
                    ("id_plan", "integer"),
                    ("codigo", "string"),
                    ("max_usuarios", "integer"),
                    ("max_sucursales", "integer")
                ],
                "methods": [
                    ("obtenerLimites()", "object")
                ]
            },
            {
                "name": "E_Sucursal",
                "pos": "l=970;r=1210;t=-250;b=-430;",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("nombre", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("contarActivas(tenant_id)", "integer")
                ]
            },
            {
                "name": "E_Usuario",
                "pos": "l=970;r=1210;t=-480;b=-660;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("tenant_id", "integer"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("contarActivos(tenant_id)", "integer")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=970;r=1210;t=-710;b=-890;",
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
            ("E_Tenant", "E_Subscription", "1", "0..*"),
            ("E_SubscriptionPlan", "E_Subscription", "1", "0..*"),
            ("E_Tenant", "E_Sucursal", "1", "0..*"),
            ("E_Tenant", "E_Usuario", "1", "0..*"),
            ("E_Tenant", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-05",
        "diag_name": "Analizar una clase CU-05 Conmutar Modo Offline",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormModoOffline",
            "attributes": [
                ("estadoRed", "string"),
                ("colaPendienteCount", "integer"),
                ("modoForzado", "boolean"),
                ("ultimoSync", "datetime")
            ],
            "methods": [
                ("cambiarModo(modo)", "void"),
                ("mostrarAlertaConexion()", "void"),
                ("actualizarBadgeOffline()", "void")
            ]
        },
        "controller": {
            "name": "OfflineSyncController",
            "attributes": [],
            "methods": [
                ("toggle_offline_mode(user_id, branch_id)", "JsonResponse"),
                ("get_connection_status()", "JsonResponse"),
                ("process_sync_queue(branch_id)", "JsonResponse")
            ]
        },
        "main_entity": "E_Usuario",
        "entities": [
            {
                "name": "E_Usuario",
                "pos": "l=660;r=900;t=-140;b=-480;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer"),
                    ("nombre", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("iniciarSesionLocal()", "void"),
                    ("cambiarEstadoOperativo()", "void")
                ]
            },
            {
                "name": "E_SyncOperation",
                "pos": "l=970;r=1210;t=-20;b=-200;",
                "attributes": [
                    ("id_operacion", "integer"),
                    ("usuario_id", "integer"),
                    ("tipo_operacion", "string"),
                    ("estado_sync", "string"),
                    ("fecha_creacion", "datetime")
                ],
                "methods": [
                    ("encolarOperacion()", "void"),
                    ("actualizarEstado()", "void")
                ]
            },
            {
                "name": "E_Sucursal",
                "pos": "l=970;r=1210;t=-250;b=-430;",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("verificarCapacidadOffline()", "boolean")
                ]
            },
            {
                "name": "E_Inventario",
                "pos": "l=1280;r=1520;t=-250;b=-430;",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer")
                ],
                "methods": [
                    ("congelarStockLocal()", "void")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "pos": "l=1590;r=1830;t=-250;b=-430;",
                "attributes": [
                    ("id_variante", "integer"),
                    ("sku", "string"),
                    ("codigo_barra", "string")
                ],
                "methods": [
                    ("consultarVariante()", "object")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=970;r=1210;t=-480;b=-660;",
                "attributes": [
                    ("id_bitacora", "integer"),
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
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            ("E_Sucursal", "E_Inventario", "1", "0..*"),
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-06",
        "diag_name": "Analizar una clase CU-06 Sincronizar Catalogo",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormSincronizacionCatalogo",
            "attributes": [
                ("totalProductosSync", "integer"),
                ("porcentajeAvance", "integer"),
                ("versionCatalogo", "string"),
                ("ultimaSincronizacion", "datetime")
            ],
            "methods": [
                ("iniciarDescarga()", "void"),
                ("actualizarProgreso(pct)", "void"),
                ("notificarSincronizacionCompleta()", "void")
            ]
        },
        "controller": {
            "name": "SyncCatalogController",
            "attributes": [],
            "methods": [
                ("pull_catalog_delta(last_version)", "JsonResponse"),
                ("store_products_local(products_json)", "boolean"),
                ("verify_catalog_integrity()", "JsonResponse")
            ]
        },
        "main_entity": "E_Producto",
        "entities": [
            {
                "name": "E_Producto",
                "pos": "l=660;r=900;t=-140;b=-480;",
                "attributes": [
                    ("id_producto", "integer"),
                    ("tenant_id", "integer"),
                    ("categoria_id", "integer"),
                    ("codigo", "string"),
                    ("nombre", "string"),
                    ("precio", "decimal"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("obtenerDetalleCompleto()", "object"),
                    ("actualizarCacheLocal()", "void")
                ]
            },
            {
                "name": "E_Categoria",
                "pos": "l=970;r=1210;t=-20;b=-180;",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("listarCategorias()", "list")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "pos": "l=970;r=1210;t=-240;b=-420;",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("sku", "string"),
                    ("codigo_barra", "string"),
                    ("precio_adicional", "decimal")
                ],
                "methods": [
                    ("obtenerVariantesPorProducto()", "list")
                ]
            },
            {
                "name": "E_Inventario",
                "pos": "l=1280;r=1520;t=-240;b=-420;",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer")
                ],
                "methods": [
                    ("actualizarStockCache()", "void")
                ]
            },
            {
                "name": "E_Sucursal",
                "pos": "l=1590;r=1830;t=-240;b=-420;",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerId()", "integer")
                ]
            },
            {
                "name": "E_Usuario",
                "pos": "l=1590;r=1830;t=-480;b=-660;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer")
                ],
                "methods": [
                    ("obtenerSucursalAsignada()", "integer")
                ]
            },
            {
                "name": "E_SyncOperation",
                "pos": "l=1890;r=2130;t=-480;b=-660;",
                "attributes": [
                    ("id_operacion", "integer"),
                    ("usuario_id", "integer"),
                    ("tipo_operacion", "string"),
                    ("estado_sync", "string")
                ],
                "methods": [
                    ("marcarCompletada()", "void")
                ]
            }
        ],
        "relationships": [
            ("E_Categoria", "E_Producto", "1", "0..*"),
            ("E_Producto", "E_VarianteProducto", "1", "1..*"),
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            ("E_Sucursal", "E_Inventario", "1", "0..*"),
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            ("E_Usuario", "E_SyncOperation", "1", "0..*")
        ]
    },
    {
        "code": "CU-07",
        "diag_name": "Analizar una clase CU-07 Consultar Catalogo Offline",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormCatalogoOffline",
            "attributes": [
                ("terminoBusqueda", "string"),
                ("categoriaSeleccionada", "integer"),
                ("listaProductosLocal", "list"),
                ("indicadorCacheLocal", "boolean")
            ],
            "methods": [
                ("buscarEnCache(criterio)", "list"),
                ("filtrarPorCategoria(idCat)", "void"),
                ("seleccionarProducto(idProd)", "void"),
                ("mostrarFichaLocal()", "void")
            ]
        },
        "controller": {
            "name": "OfflineCatalogController",
            "attributes": [],
            "methods": [
                ("search_indexeddb_catalog(query)", "list"),
                ("get_offline_product_detail(product_id)", "object"),
                ("check_local_stock(variant_id)", "integer")
            ]
        },
        "main_entity": "E_Producto",
        "entities": [
            {
                "name": "E_Producto",
                "pos": "l=660;r=900;t=-140;b=-480;",
                "attributes": [
                    ("id_producto", "integer"),
                    ("codigo", "string"),
                    ("nombre", "string"),
                    ("precio", "decimal"),
                    ("activo", "boolean")
                ],
                "methods": [
                    ("buscarPorNombreOCodigo(query)", "list"),
                    ("obtenerPrecio()", "decimal")
                ]
            },
            {
                "name": "E_Categoria",
                "pos": "l=970;r=1210;t=-20;b=-180;",
                "attributes": [
                    ("id_categoria", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("filtrarProductos()", "list")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "pos": "l=970;r=1210;t=-240;b=-420;",
                "attributes": [
                    ("id_variante", "integer"),
                    ("producto_id", "integer"),
                    ("sku", "string"),
                    ("codigo_barra", "string"),
                    ("precio_adicional", "decimal")
                ],
                "methods": [
                    ("consultarVariantes()", "list")
                ]
            },
            {
                "name": "E_Inventario",
                "pos": "l=1280;r=1520;t=-240;b=-420;",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer")
                ],
                "methods": [
                    ("obtenerStockDisponible()", "integer")
                ]
            },
            {
                "name": "E_Sucursal",
                "pos": "l=1590;r=1830;t=-240;b=-420;",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerSucursalActual()", "integer")
                ]
            }
        ],
        "relationships": [
            ("E_Categoria", "E_Producto", "1", "0..*"),
            ("E_Producto", "E_VarianteProducto", "1", "1..*"),
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            ("E_Sucursal", "E_Inventario", "1", "0..*")
        ]
    },
    {
        "code": "CU-23",
        "diag_name": "Analizar una clase CU-23 Notificar Conectividad",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormSemaforoConectividad",
            "attributes": [
                ("colorSemaforo", "string"),
                ("tiempoRespuestaPingMs", "integer"),
                ("estadoTexto", "string")
            ],
            "methods": [
                ("renderizarSemaforo(color)", "void"),
                ("mostrarModalCambioEstado()", "void"),
                ("emitirSonidoAlerta()", "void")
            ]
        },
        "controller": {
            "name": "NetworkMonitorController",
            "attributes": [],
            "methods": [
                ("start_network_heartbeat()", "void"),
                ("handle_online_event()", "void"),
                ("handle_offline_event()", "void"),
                ("notify_ui_connectivity_change(status)", "void")
            ]
        },
        "main_entity": "E_Usuario",
        "entities": [
            {
                "name": "E_Usuario",
                "pos": "l=660;r=900;t=-100;b=-440;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("nombre", "string"),
                    ("email", "string")
                ],
                "methods": [
                    ("obtenerSesionActiva()", "object")
                ]
            },
            {
                "name": "E_SyncOperation",
                "pos": "l=970;r=1210;t=-50;b=-240;",
                "attributes": [
                    ("id_operacion", "integer"),
                    ("usuario_id", "integer"),
                    ("estado_sync", "string")
                ],
                "methods": [
                    ("contarOperacionesPendientes()", "integer")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=970;r=1210;t=-300;b=-490;",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarEventoConexion()", "void")
                ]
            }
        ],
        "relationships": [
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-24",
        "diag_name": "Analizar una clase CU-24 Instalar Service Worker",
        "actor": "Usuario Web",
        "form": {
            "name": "FormInstaladorPWA",
            "attributes": [
                ("swRegistrado", "boolean"),
                ("versionCaches", "string"),
                ("bannerInstalacionVisible", "boolean")
            ],
            "methods": [
                ("solicitarInstalacionPWA()", "void"),
                ("mostrarPromptInstalacion()", "void"),
                ("ocultarBanner()", "void")
            ]
        },
        "controller": {
            "name": "ServiceWorkerController",
            "attributes": [],
            "methods": [
                ("register_service_worker()", "Promise"),
                ("precache_app_shell(cache_name, assets)", "boolean"),
                ("intercept_fetch_requests(request)", "Response"),
                ("update_cache_version(new_version)", "void")
            ]
        },
        "main_entity": "E_Usuario",
        "entities": [
            {
                "name": "E_Usuario",
                "pos": "l=660;r=900;t=-100;b=-440;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("guardarPreferenciaInstalacion()", "void")
                ]
            },
            {
                "name": "E_SyncOperation",
                "pos": "l=970;r=1210;t=-50;b=-240;",
                "attributes": [
                    ("id_operacion", "integer"),
                    ("usuario_id", "integer"),
                    ("tipo_operacion", "string")
                ],
                "methods": [
                    ("habilitarColaOffline()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=970;r=1210;t=-300;b=-490;",
                "attributes": [
                    ("id_bitacora", "integer"),
                    ("usuario_id", "integer"),
                    ("accion", "string"),
                    ("fecha_hora", "datetime")
                ],
                "methods": [
                    ("registrarInstalacionSW()", "void")
                ]
            }
        ],
        "relationships": [
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    },
    {
        "code": "CU-25",
        "diag_name": "Analizar una clase CU-25 Configurar SQLite Movil",
        "actor": "Cajero / Vendedor",
        "form": {
            "name": "FormConfiguracionSQLite",
            "attributes": [
                ("nombreBaseDatos", "string"),
                ("versionEsquema", "integer"),
                ("espacioUsadoMB", "decimal"),
                ("tablasMigradas", "list")
            ],
            "methods": [
                ("iniciarInicializacionBD()", "void"),
                ("mostrarResumenTablas()", "void"),
                ("purgarDatosLocales()", "void")
            ]
        },
        "controller": {
            "name": "DatabaseMigrationController",
            "attributes": [],
            "methods": [
                ("init_sqlite_database()", "boolean"),
                ("execute_ddl_migrations()", "boolean"),
                ("seed_master_data(branch_id)", "boolean"),
                ("validate_sqlite_schema()", "boolean")
            ]
        },
        "main_entity": "E_Sucursal",
        "entities": [
            {
                "name": "E_Sucursal",
                "pos": "l=660;r=900;t=-140;b=-480;",
                "attributes": [
                    ("id_sucursal", "integer"),
                    ("tenant_id", "integer"),
                    ("nombre", "string")
                ],
                "methods": [
                    ("obtenerConfiguracionTerminal()", "object")
                ]
            },
            {
                "name": "E_Inventario",
                "pos": "l=970;r=1210;t=-20;b=-200;",
                "attributes": [
                    ("id_inventario", "integer"),
                    ("sucursal_id", "integer"),
                    ("variante_id", "integer"),
                    ("stock_fisico", "integer")
                ],
                "methods": [
                    ("crearTablaInventarioLocal()", "void")
                ]
            },
            {
                "name": "E_VarianteProducto",
                "pos": "l=1280;r=1520;t=-20;b=-200;",
                "attributes": [
                    ("id_variante", "integer"),
                    ("sku", "string"),
                    ("codigo_barra", "string")
                ],
                "methods": [
                    ("crearTablaVariantesLocal()", "void")
                ]
            },
            {
                "name": "E_Usuario",
                "pos": "l=970;r=1210;t=-250;b=-430;",
                "attributes": [
                    ("id_usuario", "integer"),
                    ("sucursal_id", "integer")
                ],
                "methods": [
                    ("crearTablaUsuariosLocal()", "void")
                ]
            },
            {
                "name": "E_SyncOperation",
                "pos": "l=1280;r=1520;t=-250;b=-430;",
                "attributes": [
                    ("id_operacion", "integer"),
                    ("usuario_id", "integer"),
                    ("tipo_operacion", "string")
                ],
                "methods": [
                    ("crearTablaSyncQueue()", "void")
                ]
            },
            {
                "name": "E_Bitacora",
                "pos": "l=1280;r=1520;t=-480;b=-660;",
                "attributes": [
                    ("id_bitacora", "integer"),
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
            ("E_Sucursal", "E_Inventario", "1", "0..*"),
            ("E_VarianteProducto", "E_Inventario", "1", "0..*"),
            ("E_Sucursal", "E_Usuario", "0..1", "0..*"),
            ("E_Usuario", "E_SyncOperation", "1", "0..*"),
            ("E_Usuario", "E_Bitacora", "1", "0..*")
        ]
    }
]

def main():
    subprocess.run(['taskkill', '/F', '/IM', 'EA.exe'], capture_output=True)

    rep = win32com.client.Dispatch("EA.Repository")
    rep.OpenFile(EAP_PATH)
    print("Repositorio abierto.")

    # 1. Asegurar sincronización en Diagrama 11 de BD Conceptual
    try:
        diag11 = rep.GetDiagramByID(11)
        if diag11:
            for dl in diag11.DiagramLinks:
                c = rep.GetConnectorByID(dl.ConnectorID)
                src = rep.GetElementByID(c.ClientID)
                tgt = rep.GetElementByID(c.SupplierID)
                # Tenant contrata Subscription debe ser 1 a 0..*
                if src.Name == "Tenant" and tgt.Name == "Subscription":
                    c.ClientEnd.Cardinality = "1"
                    c.SupplierEnd.Cardinality = "0..*"
                    c.Update()
                    print(f"Diagrama 11 corregido: {src.Name} [1] contrata [0..*] {tgt.Name}")
    except Exception as e:
        print("Aviso al verificar Diagrama 11:", e)

    # 2. Localizar o limpiar el paquete de Diagramas de Análisis de Clases (Package ID 187)
    target_pkg = None
    try:
        target_pkg = rep.GetPackageByID(187)
    except Exception:
        pass

    if not target_pkg:
        # Buscar en el árbol
        root = rep.Models.GetAt(0)
        p2 = root.Packages.GetAt(1)
        for i in range(p2.Packages.Count):
            pkg = p2.Packages.GetAt(i)
            if "Análisis de Clases" in pkg.Name or "Analisis de Clases" in pkg.Name:
                target_pkg = pkg
                break

    if not target_pkg:
        print("ERROR: No se encontró el paquete 187")
        rep.CloseFile()
        rep.Exit()
        return

    print(f"Paquete destino encontrado: {target_pkg.Name} (ID: {target_pkg.PackageID})")

    # Limpiar elementos y diagramas anteriores del paquete 187
    for i in range(target_pkg.Diagrams.Count - 1, -1, -1):
        target_pkg.Diagrams.Delete(i)
    target_pkg.Diagrams.Refresh()

    for i in range(target_pkg.Elements.Count - 1, -1, -1):
        target_pkg.Elements.Delete(i)
    target_pkg.Elements.Refresh()

    # Recrear los 10 diagramas
    for cu in CU_DATA:
        print(f"\nGenerando {cu['code']}: {cu['diag_name']}...")
        diag = target_pkg.Diagrams.AddNew(cu["diag_name"], "Logical")
        diag.Update()

        created_elements = {}

        # 1. Actor
        el_act = target_pkg.Elements.AddNew(cu["actor"], "Actor")
        el_act.Update()
        created_elements[cu["actor"]] = el_act
        o_act = diag.DiagramObjects.AddNew("l=40;r=90;t=-180;b=-270;", "")
        o_act.ElementID = el_act.ElementID
        o_act.Update()

        # 2. Formulario («Formulario»)
        el_form = target_pkg.Elements.AddNew(cu["form"]["name"], "Class")
        el_form.Stereotype = "Formulario"
        el_form.Update()
        for aname, atype in cu["form"]["attributes"]:
            att = el_form.Attributes.AddNew(aname, atype)
            att.Update()
        for mname, mret in cu["form"]["methods"]:
            met = el_form.Methods.AddNew(mname, mret)
            met.Update()
        el_form.Attributes.Refresh()
        el_form.Methods.Refresh()
        el_form.Update()
        created_elements[cu["form"]["name"]] = el_form
        o_form = diag.DiagramObjects.AddNew("l=130;r=340;t=-100;b=-420;", "")
        o_form.ElementID = el_form.ElementID
        o_form.Update()

        # 3. Controlador («Class» - solo métodos)
        el_ctrl = target_pkg.Elements.AddNew(cu["controller"]["name"], "Class")
        el_ctrl.Update()
        for mname, mret in cu["controller"]["methods"]:
            met = el_ctrl.Methods.AddNew(mname, mret)
            met.Update()
        el_ctrl.Methods.Refresh()
        el_ctrl.Update()
        created_elements[cu["controller"]["name"]] = el_ctrl
        o_ctrl = diag.DiagramObjects.AddNew("l=390;r=610;t=-140;b=-380;", "")
        o_ctrl.ElementID = el_ctrl.ElementID
        o_ctrl.Update()

        # 4. Entidades («Entidad»)
        for ent_spec in cu["entities"]:
            el_ent = target_pkg.Elements.AddNew(ent_spec["name"], "Class")
            el_ent.Stereotype = "Entidad"
            el_ent.Update()
            for aname, atype in ent_spec["attributes"]:
                att = el_ent.Attributes.AddNew(aname, atype)
                att.Update()
            for mname, mret in ent_spec["methods"]:
                met = el_ent.Methods.AddNew(mname, mret)
                met.Update()
            el_ent.Attributes.Refresh()
            el_ent.Methods.Refresh()
            el_ent.Update()
            created_elements[ent_spec["name"]] = el_ent

            o_ent = diag.DiagramObjects.AddNew(ent_spec["pos"], "")
            o_ent.ElementID = el_ent.ElementID
            o_ent.Update()

        # 5. Conexiones
        # Actor ---> Formulario
        con_af = el_act.Connectors.AddNew("", "Association")
        con_af.SupplierID = el_form.ElementID
        con_af.Update()
        el_act.Connectors.Refresh()
        l_af = diag.DiagramLinks.AddNew("", "")
        l_af.ConnectorID = con_af.ConnectorID
        l_af.Update()

        # Formulario ---> Controlador
        con_fc = el_form.Connectors.AddNew("", "Association")
        con_fc.SupplierID = el_ctrl.ElementID
        con_fc.Update()
        el_form.Connectors.Refresh()
        l_fc = diag.DiagramLinks.AddNew("", "")
        l_fc.ConnectorID = con_fc.ConnectorID
        l_fc.Update()

        # Controlador ---> Entidad Principal
        el_main = created_elements[cu["main_entity"]]
        con_cm = el_ctrl.Connectors.AddNew("", "Association")
        con_cm.SupplierID = el_main.ElementID
        con_cm.Update()
        el_ctrl.Connectors.Refresh()
        l_cm = diag.DiagramLinks.AddNew("", "")
        l_cm.ConnectorID = con_cm.ConnectorID
        l_cm.Update()

        # Conectar Entidades entre sí con cardinalidades exactas de la Base de Datos
        for src_name, tgt_name, card_src, card_tgt in cu["relationships"]:
            el_src = created_elements[src_name]
            el_tgt = created_elements[tgt_name]

            con_rel = el_src.Connectors.AddNew("", "Association")
            con_rel.SupplierID = el_tgt.ElementID
            con_rel.ClientEnd.Cardinality = card_src
            con_rel.SupplierEnd.Cardinality = card_tgt
            con_rel.Update()
            el_src.Connectors.Refresh()

            l_rel = diag.DiagramLinks.AddNew("", "")
            l_rel.ConnectorID = con_rel.ConnectorID
            l_rel.Update()

        diag.DiagramObjects.Refresh()
        diag.DiagramLinks.Refresh()
        diag.Update()

    target_pkg.Diagrams.Refresh()
    target_pkg.Elements.Refresh()

    rep.CloseFile()
    rep.Exit()
    print("\nPROCESO FINALIZADO CON ÉXITO")

if __name__ == "__main__":
    main()
