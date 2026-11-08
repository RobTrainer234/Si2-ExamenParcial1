# -*- coding: utf-8 -*-
"""
Script maestro para estructurar e insertar los puntos 4.3, 4.4 y 4.5
en 'docsegundoparcialSI2.docx' adaptando fielmente la estructura y contenido
de 'Grupo #6 -2daPresentación.docx'.
"""

import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from cap4_builder_base import Cap4Builder, DOC_PATH

def run_cap4_update():
    print("=== Iniciando actualización de puntos 4.3, 4.4 y 4.5 en docsegundoparcialSI2.docx ===")
    
    doc = docx.Document(DOC_PATH)
    body = doc._body._element
    
    start_node = None # P1393 ('4.4. Desarrollo de los módulos del sistema')
    end_node = None   # P1417 ('Capítulo 5: Pruebas y Resultados')
    
    for child in body:
        if child.tag.endswith('p'):
            t = ''.join(child.itertext()).strip()
            if t.startswith("4.4. Desarrollo de los módulos") or "4.4. Desarrollo de los módulos" in t:
                if start_node is None:
                    start_node = child
            elif (t.startswith("Capítulo 5:") or t.startswith("Capitulo 5:")) and start_node is not None:
                end_node = child
                break
                
    if start_node is None or end_node is None:
        raise ValueError("No se encontraron los delimitadores para reemplazar 4.3/4.4/4.5 en el documento.")
        
    # Recolectar nodos a remover
    to_remove = []
    cur = start_node
    while cur is not None and cur != end_node:
        to_remove.append(cur)
        cur = cur.getnext()
        
    print(f"Delimitadores localizados. Se removerán {len(to_remove)} párrafos antiguos y se insertarán 4.3, 4.4 y 4.5.")
    
    # Instanciar constructor que insertará antes de end_node
    b = Cap4Builder(doc, end_node)
    
    # =========================================================================
    # 4.3. IMPLEMENTACIÓN DE LA BASE DE DATOS
    # =========================================================================
    b.add_heading_2("4.3. Implementación de la base de datos")
    b.add_p(
        "La base de datos relacional de FashionStore fue implementada en PostgreSQL 16 bajo una arquitectura "
        "multitenant con aislamiento lógico estricto. Cada tabla troncal incorpora el discriminador 'empresa_id' "
        "(o 'tenant_id') con restricciones de clave foránea e índices compuestos para asegurar que los datos "
        "de una empresa jamás se mezclen con los de otra. Asimismo, el esquema incorpora las estructuras "
        "necesarias para soportar la persistencia offline-first, la reconciliación transaccional con idempotencia, "
        "el circuito logístico de traspasos en dos fases y la analítica predictiva con IA."
    )
    b.add_p(
        "A continuación se presenta la definición formal DDL (Data Definition Language) de las tablas implementadas, "
        "organizadas por subsistemas de negocio:"
    )
    
    # Modulo 7: SaaS Multitenant y Suscripciones
    b.add_p(bold_prefix="MÓDULO 7: PLATAFORMA SAAS MULTITENANT Y PLANES DE SUSCRIPCIÓN", text="")
    b.add_p(
        "Permite que la plataforma opere como un servicio comercializable donde múltiples empresas conviven "
        "en la misma base de datos con aislamiento lógico estricto, cuotas de sucursales y vigencias temporales:"
    )
    sql_m7 = [
        "-- -----------------------------------------------------------------------------",
        "-- MÓDULO 7: SAAS MULTITENANT Y PLANES DE SUSCRIPCIÓN",
        "-- -----------------------------------------------------------------------------",
        "CREATE TABLE plan_suscripcion (",
        "    id SERIAL PRIMARY KEY,",
        "    codigo VARCHAR(30) NOT NULL UNIQUE,          -- 'BASICO', 'PROFESIONAL', 'ENTERPRISE'",
        "    nombre VARCHAR(100) NOT NULL,",
        "    descripcion TEXT,",
        "    precio_mensual NUMERIC(10, 2) NOT NULL CHECK (precio_mensual >= 0),",
        "    limite_sucursales INT NOT NULL DEFAULT 1,     -- Básico: 2, Profesional: 10, Enterprise: 999",
        "    permite_ia BOOLEAN DEFAULT FALSE,            -- Solo Profesional y Enterprise",
        "    permite_offline BOOLEAN DEFAULT FALSE,       -- Solo Profesional y Enterprise",
        "    activo BOOLEAN DEFAULT TRUE,",
        "    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
        ");",
        "",
        "CREATE TABLE empresa (",
        "    id SERIAL PRIMARY KEY,                       -- Este id funge como tenant_id del sistema",
        "    razon_social VARCHAR(150) NOT NULL,",
        "    nit VARCHAR(30) NOT NULL UNIQUE,",
        "    subdominio VARCHAR(50) NOT NULL UNIQUE,      -- ej: 'boutiqueaurora.fashionstore.com'",
        "    email_corporativo VARCHAR(150) NOT NULL,",
        "    telefono VARCHAR(30),",
        "    direccion_fiscal TEXT,",
        "    activo BOOLEAN DEFAULT TRUE,",
        "    creado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
        ");",
        "",
        "CREATE TABLE suscripcion (",
        "    id SERIAL PRIMARY KEY,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id) ON DELETE CASCADE,",
        "    plan_id INT NOT NULL REFERENCES plan_suscripcion(id),",
        "    fecha_inicio DATE NOT NULL,",
        "    fecha_fin DATE NOT NULL,",
        "    estado VARCHAR(20) NOT NULL DEFAULT 'ACTIVA' CHECK (",
        "        estado IN ('PRUEBA', 'ACTIVA', 'VENCIDA', 'CANCELADA', 'SUSPENDIDA')",
        "    ),",
        "    monto_pago NUMERIC(10, 2) NOT NULL CHECK (monto_pago >= 0),",
        "    renovacion_automatica BOOLEAN DEFAULT TRUE,",
        "    actualizado_en TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,",
        "    CONSTRAINT chk_fechas_suscripcion CHECK (fecha_fin >= fecha_inicio)",
        ");"
    ]
    b.add_code_block("Estructura SQL DDL: Módulo de Plataforma SaaS y Suscripciones", sql_m7, "sql")

    # Modulo 8: Calce Corporal, Garantías y Devoluciones
    b.add_p(bold_prefix="MÓDULO 8: GUÍA ANATÓMICA DE MEDIDAS, GARANTÍAS Y DEVOLUCIONES", text="")
    b.add_p(
        "Resuelve la problemática de calce corporal en compras de moda en línea. El cliente consulta las medidas "
        "en centímetros y dispone de un plazo parametrizable (ej. 30 días) para solicitar cambio por talla, "
        "sin reembolso de dinero en efectivo. La prenda devuelta reingresa al inventario y se entrega otra prenda:"
    )
    sql_m8 = [
        "-- -----------------------------------------------------------------------------",
        "-- MÓDULO 8: CALCE CORPORAL, GARANTÍAS Y CAMBIOS DE PRENDA",
        "-- -----------------------------------------------------------------------------",
        "CREATE TABLE guia_medida (",
        "    id SERIAL PRIMARY KEY,",
        "    producto_id INT NOT NULL REFERENCES producto(id) ON DELETE CASCADE,",
        "    talla_id INT NOT NULL REFERENCES talla(id),",
        "    pecho_cm NUMERIC(6, 2),",
        "    cintura_cm NUMERIC(6, 2),",
        "    cadera_cm NUMERIC(6, 2),",
        "    largo_cm NUMERIC(6, 2),",
        "    manga_cm NUMERIC(6, 2),",
        "    observacion_calce VARCHAR(150),              -- 'Corte entallado', 'Calce holgado'",
        "    UNIQUE (producto_id, talla_id)",
        ");",
        "",
        "CREATE TABLE politica_garantia (",
        "    id SERIAL PRIMARY KEY,",
        "    empresa_id INT NOT NULL UNIQUE REFERENCES empresa(id) ON DELETE CASCADE,",
        "    plazo_dias_cambio INT NOT NULL DEFAULT 30,   -- Plazo límite reglamentario",
        "    permite_cambio_talla BOOLEAN DEFAULT TRUE,",
        "    admite_reembolso_dinero BOOLEAN DEFAULT FALSE, -- Regla RN07: Prohibido reintegro de dinero",
        "    requiere_etiqueta_original BOOLEAN DEFAULT TRUE,",
        "    activo BOOLEAN DEFAULT TRUE",
        ");",
        "",
        "CREATE TABLE nota_devolucion (",
        "    id SERIAL PRIMARY KEY,",
        "    codigo_devolucion VARCHAR(30) NOT NULL UNIQUE,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    venta_id INT NOT NULL REFERENCES venta(id),",
        "    sucursal_id INT NOT NULL REFERENCES sucursal(id),",
        "    usuario_id INT NOT NULL REFERENCES usuario(id), -- Cajero/empleado receptor",
        "    cliente_id INT NOT NULL REFERENCES cliente(id),",
        "    motivo VARCHAR(50) NOT NULL CHECK (",
        "        motivo IN ('TALLA_CHICA', 'TALLA_GRANDE', 'DESAJUSTE_MEDIDA', 'DEFECTO_FABRICA', 'DISCONFORMIDAD_COLOR')",
        "    ),",
        "    estado VARCHAR(20) NOT NULL DEFAULT 'COMPLETADA' CHECK (",
        "        estado IN ('SOLICITADA', 'COMPLETADA', 'RECHAZADA')",
        "    ),",
        "    observaciones TEXT,",
        "    fecha_hora TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
        ");",
        "",
        "CREATE TABLE detalle_nota_devolucion (",
        "    id SERIAL PRIMARY KEY,",
        "    nota_devolucion_id INT NOT NULL REFERENCES nota_devolucion(id) ON DELETE CASCADE,",
        "    variante_devuelta_id INT NOT NULL REFERENCES producto_variante(id),  -- Reingresa al stock",
        "    cantidad_devuelta INT NOT NULL CHECK (cantidad_devuelta > 0),",
        "    variante_entregada_id INT NOT NULL REFERENCES producto_variante(id), -- Sale del stock",
        "    cantidad_entregada INT NOT NULL CHECK (cantidad_entregada > 0),",
        "    diferencia_monetaria NUMERIC(10, 2) DEFAULT 0.00                    -- Ajuste si varía precio",
        ");"
    ]
    b.add_code_block("Estructura SQL DDL: Módulo de Guías Anatómicas y Notas de Devolución", sql_m8, "sql")

    # Modulo 9: Logística de Traspasos en Dos Fases
    b.add_p(bold_prefix="MÓDULO 9: LOGÍSTICA DE TRASPASOS ENTRE SUCURSALES (EN DOS FASES)", text="")
    b.add_p(
        "Permite transferir existencias entre sucursales de una misma empresa cuando una tienda no dispone de "
        "stock. La sucursal emisora descuenta el stock pasándolo al estado 'En Tránsito', y la sucursal receptora "
        "confirma la recepción física para ingresarlo a su inventario disponible:"
    )
    sql_m9 = [
        "-- -----------------------------------------------------------------------------",
        "-- MÓDULO 9: TRASPASOS MULTI-SUCURSAL EN DOS FASES",
        "-- -----------------------------------------------------------------------------",
        "CREATE TABLE traspaso_inventario (",
        "    id SERIAL PRIMARY KEY,",
        "    codigo_traspaso VARCHAR(30) NOT NULL UNIQUE,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    sucursal_origen_id INT NOT NULL REFERENCES sucursal(id),",
        "    sucursal_destino_id INT NOT NULL REFERENCES sucursal(id),",
        "    usuario_despacha_id INT NOT NULL REFERENCES usuario(id),",
        "    usuario_recibe_id INT REFERENCES usuario(id),",
        "    estado VARCHAR(30) NOT NULL DEFAULT 'SOLICITADO' CHECK (",
        "        estado IN ('SOLICITADO', 'EN_TRANSITO', 'RECEPCIONADO', 'CANCELADO', 'OBSERVADO')",
        "    ),",
        "    motivo TEXT,",
        "    fecha_solicitud TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,",
        "    fecha_despacho TIMESTAMP WITH TIME ZONE,",
        "    fecha_recepcion TIMESTAMP WITH TIME ZONE,",
        "    CONSTRAINT chk_sucursales_distintas CHECK (sucursal_origen_id <> sucursal_destino_id)",
        ");",
        "",
        "CREATE TABLE detalle_traspaso (",
        "    id SERIAL PRIMARY KEY,",
        "    traspaso_id INT NOT NULL REFERENCES traspaso_inventario(id) ON DELETE CASCADE,",
        "    producto_variante_id INT NOT NULL REFERENCES producto_variante(id),",
        "    cantidad_enviada INT NOT NULL CHECK (cantidad_enviada > 0),",
        "    cantidad_recibida INT DEFAULT 0 CHECK (cantidad_recibida >= 0)",
        ");"
    ]
    b.add_code_block("Estructura SQL DDL: Módulo de Logística de Traspasos Multi-Sucursal", sql_m9, "sql")

    # Modulo 10: Persistencia Offline y Sincronización
    b.add_p(bold_prefix="MÓDULO 10: PERSISTENCIA OFFLINE Y SINCRONIZACIÓN IDEMPOTENTE", text="")
    b.add_p(
        "Diseñado para soportar caídas de conexión en el navegador PWA (IndexedDB) y en la app móvil (SQLite). "
        "Utiliza identificadores UUIDv4 para garantizar idempotencia transaccional y registra los conflictos de sobreventa:"
    )
    sql_m10 = [
        "-- -----------------------------------------------------------------------------",
        "-- MÓDULO 10: SINCRONIZACIÓN OFFLINE-FIRST (PWA / FLUTTER)",
        "-- -----------------------------------------------------------------------------",
        "CREATE TABLE sincronizacion_offline (",
        "    id BIGSERIAL PRIMARY KEY,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    sucursal_id INT NOT NULL REFERENCES sucursal(id),",
        "    usuario_id INT NOT NULL REFERENCES usuario(id),",
        "    uuid_operacion VARCHAR(64) NOT NULL UNIQUE,  -- UUIDv4 generado en el cliente",
        "    tipo_operacion VARCHAR(30) NOT NULL CHECK (",
        "        tipo_operacion IN ('VENTA_LOCAL', 'RESERVA_LOCAL', 'CAMBIO_PRENDA_LOCAL')",
        "    ),",
        "    payload_json JSONB NOT NULL,                 -- Contenido íntegro de la orden offline",
        "    estado VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE' CHECK (",
        "        estado IN ('PENDIENTE', 'SINCRONIZADO', 'CONFLICTO_STOCK', 'ERROR_VALIDACION')",
        "    ),",
        "    fecha_registro_local TIMESTAMP WITH TIME ZONE NOT NULL,",
        "    fecha_sincronizacion TIMESTAMP WITH TIME ZONE,",
        "    error_detalle TEXT",
        ");",
        "",
        "CREATE TABLE conflicto_inventario (",
        "    id SERIAL PRIMARY KEY,",
        "    sincronizacion_id BIGINT NOT NULL REFERENCES sincronizacion_offline(id) ON DELETE CASCADE,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    sucursal_id INT NOT NULL REFERENCES sucursal(id),",
        "    producto_variante_id INT NOT NULL REFERENCES producto_variante(id),",
        "    cantidad_solicitada INT NOT NULL,",
        "    stock_disponible_servidor INT NOT NULL,",
        "    resuelto BOOLEAN DEFAULT FALSE,",
        "    fecha_resolucion TIMESTAMP WITH TIME ZONE,",
        "    usuario_resuelve_id INT REFERENCES usuario(id)",
        ");"
    ]
    b.add_code_block("Estructura SQL DDL: Módulo de Sincronización Offline e Idempotencia", sql_m10, "sql")

    # Modulo 11: IA Generativa y Machine Learning
    b.add_p(bold_prefix="MÓDULO 11: INTELIGENCIA ARTIFICIAL GENERATIVA Y MACHINE LEARNING", text="")
    b.add_p(
        "Almacena las consultas analíticas generadas por IA mediante lenguaje natural (Text-to-SQL) "
        "y los artefactos de entrenamiento de modelos supervisados y no supervisados de demanda y clustering:"
    )
    sql_m11 = [
        "-- -----------------------------------------------------------------------------",
        "-- MÓDULO 11: ANALÍTICA AVANZADA E IA GENERATIVA",
        "-- -----------------------------------------------------------------------------",
        "CREATE TABLE reporte_generativo_ia (",
        "    id SERIAL PRIMARY KEY,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    usuario_id INT NOT NULL REFERENCES usuario(id),",
        "    prompt_usuario TEXT NOT NULL,                -- Pregunta en lenguaje natural",
        "    sql_generado TEXT NOT NULL,                  -- Consulta SQL con filtro tenant_id inyectado",
        "    resultado_json JSONB,                        -- Datos analíticos consolidados",
        "    tipo_visualizacion VARCHAR(30) DEFAULT 'TABLA' CHECK (",
        "        tipo_visualizacion IN ('TABLA', 'BARRAS', 'LINEAS', 'CIRCULAR', 'KPIS')",
        "    ),",
        "    fecha_consulta TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP",
        ");",
        "",
        "CREATE TABLE modelo_analitico_ml (",
        "    id SERIAL PRIMARY KEY,",
        "    empresa_id INT NOT NULL REFERENCES empresa(id),",
        "    tipo_modelo VARCHAR(50) NOT NULL CHECK (",
        "        tipo_modelo IN ('DEMANDA_FORECASTING', 'SEGMENTACION_RFM', 'RECOMENDACION_PRENDAS')",
        "    ),",
        "    algoritmo VARCHAR(50) NOT NULL,              -- 'RandomForestRegressor', 'KMeans', etc.",
        "    metricas_evaluacion JSONB NOT NULL,          -- {'MAE': 2.14, 'RMSE': 3.05, 'R2': 0.89, 'Silhouette': 0.68}",
        "    parametros_json JSONB,",
        "    fecha_entrenamiento TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,",
        "    activo BOOLEAN DEFAULT TRUE",
        ");"
    ]
    b.add_code_block("Estructura SQL DDL: Módulo de Inteligencia Artificial y Machine Learning", sql_m11, "sql")

    # Inyecciones de Multitenancy y Trazabilidad
    b.add_p(bold_prefix="INYECCIÓN DE MULTITENANCY Y TRAZABILIDAD EN TABLAS TRONCALES", text="")
    b.add_p(
        "Para consolidar el modelo multi-inquilino y la trazabilidad de operaciones fuera de línea, "
        "las entidades principales fueron enriquecidas mediante sentencias DDL de alteración:"
    )
    sql_alter = [
        "-- 1. Inyección de multitenancy en entidades troncales:",
        "ALTER TABLE usuario ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE sucursal ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE producto ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE proveedor ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE venta ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "ALTER TABLE bitacora_auditoria ADD COLUMN IF NOT EXISTS empresa_id INT REFERENCES empresa(id);",
        "",
        "-- 2. Trazabilidad offline en Ventas y Reservas:",
        "ALTER TABLE venta ADD COLUMN IF NOT EXISTS uuid_operacion VARCHAR(64) UNIQUE;",
        "ALTER TABLE venta ADD COLUMN IF NOT EXISTS es_offline BOOLEAN DEFAULT FALSE;",
        "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS uuid_operacion VARCHAR(64) UNIQUE;",
        "ALTER TABLE reserva ADD COLUMN IF NOT EXISTS es_offline BOOLEAN DEFAULT FALSE;",
        "",
        "-- 3. Stock en tránsito en el inventario multi-sucursal:",
        "ALTER TABLE inventario ADD COLUMN IF NOT EXISTS stock_en_transito INT NOT NULL DEFAULT 0 CHECK (stock_en_transito >= 0);"
    ]
    b.add_code_block("Sentencias DDL: Inyección de Aislamiento Multi-Tenant y Soporte Offline", sql_alter, "sql")

    # =========================================================================
    # 4.4. DESARROLLO DE LOS MÓDULOS DEL SISTEMA
    # =========================================================================
    b.add_heading_2("4.4. Desarrollo de los módulos del sistema")
    
    # 4.4.1
    b.add_heading_3("4.4.1. Reglas Críticas de Inventario, Reserva, Compra de Reserva y Sincronización Offline")
    b.add_p(
        "El servicio transaccional en el backend implementa de manera atómica las transiciones entre stock disponible, "
        "stock reservado y stock vendido, asegurando mediante bloqueos a nivel de fila (SELECT ... FOR UPDATE) que una reserva "
        "comprada nunca descuente dos veces el stock disponible, que no ocurran sobreventas en concurrencia y que toda operación "
        "sincronizada desde la PWA o desde SQLite en Flutter sea idempotente:"
    )
    code_41 = [
        "# backend/services/inventory_sync_service.py",
        "from sqlalchemy.orm import Session",
        "from backend.models.inventory import Inventario",
        "from backend.core.exceptions import ConflictStockError",
        "",
        "def aplicar_operacion_inventario(",
        "    db: Session, id_tenant: str, id_sucursal: int, id_variante: int,",
        "    tipo_op: str, cantidad: int, origen_reserva: bool = False",
        "):",
        "    \"\"\"",
        "    Ejecuta transiciones de estado de inventario de forma atómica y pesimista.",
        "    Garantiza consistencia entre stock_disponible, stock_reservado y stock_vendido.",
        "    \"\"\"",
        "    # Bloqueo pesimista de fila para evitar condiciones de carrera concurrentes",
        "    inv = db.query(Inventario).filter_by(",
        "        id_tenant=id_tenant, id_sucursal=id_sucursal, id_variante=id_variante",
        "    ).with_for_update().first()",
        "",
        "    if not inv:",
        "        raise ConflictStockError(f'Registro de inventario no encontrado para variante {id_variante}')",
        "",
        "    if tipo_op == 'RESERVAR':",
        "        # RN05: Apartado de prendas para prueba física",
        "        if inv.stock_disponible < cantidad:",
        "            raise ConflictStockError(f'Stock disponible insuficiente ({inv.stock_disponible}) para reservar')",
        "        inv.stock_disponible -= cantidad",
        "        inv.stock_reservado += cantidad",
        "",
        "    elif tipo_op == 'CANCELAR_RESERVA':",
        "        # Liberación por expiración de tiempo (24-48 hrs) o anulación voluntaria",
        "        if inv.stock_reservado < cantidad:",
        "            raise ConflictStockError('La cantidad a cancelar supera el stock actualmente reservado')",
        "        inv.stock_reservado -= cantidad",
        "        inv.stock_disponible += cantidad",
        "",
        "    elif tipo_op == 'VENTA_DIRECTA':",
        "        # Venta presencial o en línea sin reserva previa",
        "        if inv.stock_disponible < cantidad:",
        "            raise ConflictStockError(f'Stock disponible insuficiente ({inv.stock_disponible}) para venta directa')",
        "        inv.stock_disponible -= cantidad",
        "        inv.stock_vendido += cantidad",
        "",
        "    elif tipo_op == 'COMPRAR_RESERVA' and origen_reserva:",
        "        # Regla crítica: descuenta exclusivamente del stock_reservado, NO vuelve a descontar disponible",
        "        if inv.stock_reservado < cantidad:",
        "            raise ConflictStockError('La reserva no posee unidades comprometidas suficientes en stock reservado')",
        "        inv.stock_reservado -= cantidad",
        "        inv.stock_vendido += cantidad",
        "",
        "    # Verificación final de invariante física: total_stock = disponible + reservado",
        "    inv.stock_total = inv.stock_disponible + inv.stock_reservado",
        "    db.flush()",
        "    return inv"
    ]
    b.add_code_block("Fragmento 4.1: Servicio de Consistencia de Inventario (Disponible, Reservado, Vendido y Total)", code_41, "python")

    # 4.4.2
    b.add_heading_3("4.4.2. Circuito Logístico de Traspaso entre Sucursales y Notas de Devolución por Talla")
    b.add_p(
        "Para dar respuesta a los desajustes corporales y las solicitudes de cambio de talla frecuentes en confección textil "
        "(RN06, RN07, RN08), así como al rebalanceo entre tiendas (RN09), se implementó el circuito logístico sin devolución "
        "de dinero en efectivo y el traspaso en dos fases:"
    )
    code_42 = [
        "# backend/services/transfer_return_service.py",
        "from datetime import datetime, timezone, timedelta",
        "from sqlalchemy.orm import Session",
        "from backend.models.logistica import OrdenTraspaso, DetalleTraspaso, NotaDevolucion",
        "from backend.models.inventory import Inventario",
        "from backend.core.exceptions import BusinessRuleViolationException",
        "",
        "def ejecutar_traspaso_fase1_despacho(db: Session, id_tenant: str, id_origen: int, id_destino: int, variante_id: int, cant: int):",
        "    \"\"\"RN09 - Fase 1: Descuenta de origen y pasa mercadería al estado 'En Tránsito'.\"\"\"",
        "    inv_origen = db.query(Inventario).filter_by(id_tenant=id_tenant, id_sucursal=id_origen, id_variante=variante_id).with_for_update().first()",
        "    if inv_origen.stock_disponible < cant:",
        "        raise BusinessRuleViolationException('Stock insuficiente en sucursal emisora para iniciar traspaso')",
        "    ",
        "    inv_origen.stock_disponible -= cant",
        "    inv_origen.stock_total -= cant",
        "    ",
        "    traspaso = OrdenTraspaso(",
        "        id_tenant=id_tenant, sucursal_origen_id=id_origen, sucursal_destino_id=id_destino,",
        "        estado='EN_TRANSITO', fecha_despacho=datetime.now(timezone.utc)",
        "    )",
        "    db.add(traspaso)",
        "    db.flush()",
        "    db.add(DetalleTraspaso(id_traspaso=traspaso.id, id_variante=variante_id, cantidad=cant))",
        "    return traspaso",
        "",
        "def procesar_nota_devolucion_talla(db: Session, id_tenant: str, id_sucursal: int, venta_origen, id_var_devuelta: int, id_var_nueva: int):",
        "    \"\"\"RN06, RN07, RN08: Cambio de prenda por talla sin retorno de dinero y balance atómico de stock.\"\"\"",
        "    # Validación de plazo de garantía legal (30 días)",
        "    plazo_limite = venta_origen.fecha_hora + timedelta(days=30)",
        "    if datetime.now(timezone.utc) > plazo_limite:",
        "        raise BusinessRuleViolationException('El plazo de garantía legal (30 días) ha vencido para cambios de prenda')",
        "    ",
        "    inv_devuelto = db.query(Inventario).filter_by(id_tenant=id_tenant, id_sucursal=id_sucursal, id_variante=id_var_devuelta).with_for_update().first()",
        "    inv_nuevo = db.query(Inventario).filter_by(id_tenant=id_tenant, id_sucursal=id_sucursal, id_variante=id_var_nueva).with_for_update().first()",
        "    if inv_nuevo.stock_disponible < 1:",
        "        raise BusinessRuleViolationException('No existe disponibilidad física de la nueva talla solicitada')",
        "    ",
        "    # RN08: Reingreso inmediato de la prenda devuelta y despacho de la nueva talla",
        "    inv_devuelto.stock_disponible += 1",
        "    inv_devuelto.stock_total += 1",
        "    inv_nuevo.stock_disponible -= 1",
        "    inv_nuevo.stock_total -= 1",
        "    ",
        "    nota = NotaDevolucion(",
        "        id_tenant=id_tenant, id_sucursal=id_sucursal, id_venta_original=venta_origen.id,",
        "        variante_devuelta_id=id_var_devuelta, variante_entregada_id=id_var_nueva,",
        "        monto_reembolsado=0.00, motivo='Discrepancia anatómica / cambio de talla'",
        "    )",
        "    db.add(nota)",
        "    return nota"
    ]
    b.add_code_block("Fragmento 4.2: Gestión Logística de Traspasos en Dos Fases y Devolución Equitativa", code_42, "python")

    # 4.4.3
    b.add_heading_3("4.4.3. Módulo de Aislamiento Multitenant y Seguridad SaaS")
    b.add_p(
        "El control de aislamiento de inquilinos es el núcleo del esquema SaaS (RNF02). Ninguna consulta, mutación "
        "o proceso puede acceder a datos ajenos al inquilino validado. Se aplica un patrón de interceptación de contexto (Depends) "
        "y middleware que extrae el id_tenant verificado criptográficamente en el token JWT y evalúa los límites del plan contratado (RN01, RN02):"
    )
    code_43 = [
        "# backend/core/tenant_middleware.py",
        "from fastapi import Request, Depends, HTTPException, status",
        "from sqlalchemy.orm import Session",
        "from backend.core.database import get_db",
        "from backend.core.security import decodificar_token_jwt",
        "from backend.models.tenant import EmpresaSaaS, PlanSuscripcion",
        "",
        "class TenantContext:",
        "    def __init__(self, tenant_id: str, plan_nombre: str, max_sucursales: int, permite_ia: bool):",
        "        self.tenant_id = tenant_id",
        "        self.plan_nombre = plan_nombre",
        "        self.max_sucursales = max_sucursales",
        "        self.permite_ia = permite_ia",
        "",
        "def obtener_tenant_actual(request: Request, db: Session = Depends(get_db)) -> TenantContext:",
        "    \"\"\"Extrae y valida el inquilino autenticado desde las credenciales del request.\"\"\"",
        "    auth_header = request.headers.get('Authorization')",
        "    if not auth_header or not auth_header.startswith('Bearer '):",
        "        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token no suministrado')",
        "    token = auth_header.split(' ')[1]",
        "    payload = decodificar_token_jwt(token)",
        "    tenant_id = payload.get('tenant_id')",
        "    tenant = db.query(EmpresaSaaS).filter_by(id=tenant_id, activo=True).first()",
        "    if not tenant:",
        "        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Empresa tenant inactiva o no registrada')",
        "    plan = db.query(PlanSuscripcion).filter_by(id=tenant.plan_id).first()",
        "    return TenantContext(",
        "        tenant_id=tenant.id, plan_nombre=plan.nombre,",
        "        max_sucursales=plan.limite_sucursales, permite_ia=plan.habilita_ia",
        "    )",
        "",
        "def verificar_acceso_ia(tenant: TenantContext = Depends(obtener_tenant_actual)):",
        "    \"\"\"RN02: Restringe capacidades de IA exclusivamente a planes Profesional o Enterprise.\"\"\"",
        "    if not tenant.permite_ia:",
        "        raise HTTPException(",
        "            status_code=status.HTTP_403_FORBIDDEN,",
        "            detail='Su plan de suscripción actual no incluye el módulo analítico de Inteligencia Artificial'",
        "        )",
        "    return tenant"
    ]
    b.add_code_block("Fragmento 4.3: Inyección de Dependencia de Aislamiento Tenant y Cuotas de Plan", code_43, "python")

    # 4.4.4
    b.add_heading_3("4.4.4. Módulo de Persistencia Offline y Sincronización en Angular PWA (IndexedDB)")
    b.add_p(
        "La aplicación web PWA permite al personal de ventas continuar emitiendo órdenes de compra de contado (RN03) "
        "y reservas para prueba cuando el enlace de red se interrumpe. El servicio orquesta la base de datos IndexedDB a través "
        "de un esquema local que encola las órdenes selladas con un identificador único UUIDv4 para garantizar idempotencia:"
    )
    code_44 = [
        "// frontend/src/app/core/services/offline_sync.service.ts",
        "import { Injectable } from '@angular/core';",
        "import { openDB, IDBPDatabase } from 'idb';",
        "import { HttpClient } from '@angular/common/http';",
        "import { v4 as uuidv4 } from 'uuid';",
        "",
        "export interface VentaOfflinePayload {",
        "  uuid_local: string;",
        "  tenant_id: string;",
        "  sucursal_id: number;",
        "  tipo_pago: 'EFECTIVO';",
        "  items: Array<{ variante_id: number; cantidad: number; precio_unitario: number }>;",
        "  fecha_utc: string;",
        "  estado_sync: 'PENDIENTE' | 'SINCRONIZADO' | 'RECHAZADO';",
        "}",
        "",
        "@Injectable({ providedIn: 'root' })",
        "export class OfflineSyncService {",
        "  private dbPromise: Promise<IDBPDatabase>;",
        "  constructor(private http: HttpClient) {",
        "    this.dbPromise = openDB('FashionStoreOfflineDB', 1, {",
        "      upgrade(db) {",
        "        if (!db.objectStoreNames.contains('cola_ventas')) {",
        "          db.createObjectStore('cola_ventas', { keyPath: 'uuid_local' });",
        "        }",
        "      }",
        "    });",
        "  }",
        "  async registrarVentaContadoOffline(tenantId: string, sucursalId: number, items: any[]): Promise<string> {",
        "    const db = await this.dbPromise;",
        "    const ventaLocal: VentaOfflinePayload = {",
        "      uuid_local: uuidv4(),",
        "      tenant_id: tenantId,",
        "      sucursal_id: sucursalId,",
        "      tipo_pago: 'EFECTIVO', // RN03: Restricción estricta a solo efectivo en offline",
        "      items: items,",
        "      fecha_utc: new Date().toISOString(),",
        "      estado_sync: 'PENDIENTE'",
        "    };",
        "    await db.put('cola_ventas', ventaLocal);",
        "    return ventaLocal.uuid_local;",
        "  }",
        "  async vaciarColaSincronizacion(apiUrl: string): Promise<void> {",
        "    const db = await this.dbPromise;",
        "    const tx = db.transaction('cola_ventas', 'readwrite');",
        "    const store = tx.objectStore('cola_ventas');",
        "    const pendientes: VentaOfflinePayload[] = await store.getAll();",
        "    for (const venta of pendientes.filter(v => v.estado_sync === 'PENDIENTE')) {",
        "      try {",
        "        await this.http.post(`${apiUrl}/api/v1/sync/ventas-offline`, venta).toPromise();",
        "        venta.estado_sync = 'SINCRONIZADO';",
        "        await store.put(venta);",
        "      } catch (error) {",
        "        console.error(`Fallo de sincronización para UUID: ${venta.uuid_local}`, error);",
        "      }",
        "    }",
        "    await tx.done;",
        "  }",
        "}"
    ]
    b.add_code_block("Fragmento 4.4: Servicio de Persistencia Offline y Encolado en PWA (TypeScript / Angular)", code_44, "typescript")

    # 4.4.5
    b.add_heading_3("4.4.5. Módulo Móvil de Ventas Desconectadas en Flutter (SQLite)")
    b.add_p(
        "El aplicativo móvil Flutter proporciona a los agentes de venta en tienda y ferias una base de datos "
        "embebida mediante sqflite. Los registros locales quedan blindados contra cierres forzosos de la aplicación "
        "y se sincronizan reactivamente al detectar restablecimiento de red:"
    )
    code_45 = [
        "// mobile/lib/services/offline_sales_database.dart",
        "import 'package:sqflite/sqflite.dart';",
        "import 'package:path/path.dart';",
        "import 'package:uuid/uuid.dart';",
        "",
        "class OfflineSalesDatabase {",
        "  static final OfflineSalesDatabase instance = OfflineSalesDatabase._init();",
        "  static Database? _database;",
        "  OfflineSalesDatabase._init();",
        "  Future<Database> get database async {",
        "    if (_database != null) return _database!;",
        "    _database = await _initDB('fashionstore_offline.db');",
        "    return _database!;",
        "  }",
        "  Future<Database> _initDB(String filePath) async {",
        "    final dbPath = await getDatabasesPath();",
        "    final path = join(dbPath, filePath);",
        "    return await openDatabase(",
        "      path, version: 1,",
        "      onCreate: (db, version) async {",
        "        await db.execute('''",
        "          CREATE TABLE ventas_locales (",
        "            uuid TEXT PRIMARY KEY,",
        "            tenant_id TEXT NOT NULL,",
        "            sucursal_id INTEGER NOT NULL,",
        "            monto_total REAL NOT NULL,",
        "            metodo_pago TEXT NOT NULL,",
        "            creado_utc TEXT NOT NULL,",
        "            sincronizado INTEGER NOT NULL",
        "          )",
        "        ''');",
        "      },",
        "    );",
        "  }",
        "  Future<String> registrarVentaEfectivo(String tenantId, int sucursalId, double total) async {",
        "    final db = await instance.database;",
        "    final String nuevoUuid = const Uuid().v4();",
        "    await db.insert('ventas_locales', {",
        "      'uuid': nuevoUuid, 'tenant_id': tenantId, 'sucursal_id': sucursalId,",
        "      'monto_total': total, 'metodo_pago': 'EFECTIVO',",
        "      'creado_utc': DateTime.now().toUtc().toIso8601String(), 'sincronizado': 0",
        "    });",
        "    return nuevoUuid;",
        "  }",
        "}"
    ]
    b.add_code_block("Fragmento 4.5: Repositorio SQLite y Detección de Conectividad en Flutter (Dart)", code_45, "dart")

    # 4.4.6
    b.add_heading_3("4.4.6. Controlador Backend de Conciliación Idempotente y Detección de Conflictos")
    b.add_p(
        "En el backend, el endpoint de sincronización recibe los lotes emitidos tanto por la PWA como por la app Flutter. "
        "Se verifica la presencia del uuid_local en la base de datos central de PostgreSQL para prevenir ejecuciones duplicadas "
        "(RN04, RNF05). En caso de existir conflicto por stock insuficiente, se segrega la transacción y se registra en la bitácora de auditoría:"
    )
    code_46 = [
        "# backend/api/v1/sync_controller.py",
        "from fastapi import APIRouter, Depends, status",
        "from sqlalchemy.orm import Session",
        "from pydantic import BaseModel",
        "from typing import List",
        "from backend.core.database import get_db",
        "from backend.core.tenant_middleware import obtener_tenant_actual, TenantContext",
        "from backend.models.ventas import Venta, DetalleVenta",
        "from backend.services.inventory_sync_service import aplicar_operacion_inventario",
        "from backend.core.exceptions import ConflictStockError",
        "",
        "router = APIRouter(prefix='/api/v1/sync', tags=['Sincronización Offline'])",
        "",
        "class ItemSyncDTO(BaseModel):",
        "    variante_id: int",
        "    cantidad: int",
        "    precio_unitario: float",
        "",
        "class VentaSyncRequest(BaseModel):",
        "    uuid_local: str",
        "    sucursal_id: int",
        "    tipo_pago: str",
        "    items: List[ItemSyncDTO]",
        "    fecha_utc: str",
        "",
        "@router.post('/ventas-offline', status_code=status.HTTP_200_OK)",
        "def sincronizar_venta_offline(",
        "    payload: VentaSyncRequest, db: Session = Depends(get_db), tenant: TenantContext = Depends(obtener_tenant_actual)",
        "):",
        "    \"\"\"RN04 & RNF05: Idempotencia estricta. Si el UUID ya existe, retorna estado existente sin duplicar asientos.\"\"\"",
        "    venta_existente = db.query(Venta).filter_by(id_tenant=tenant.tenant_id, uuid_transaccion=payload.uuid_local).first()",
        "    if venta_existente:",
        "        return {'resultado': 'IGNORADO_DUPLICADO', 'mensaje': 'Transacción previamente asentada', 'venta_id': venta_existente.id}",
        "",
        "    try:",
        "        nueva_venta = Venta(",
        "            id_tenant=tenant.tenant_id, id_sucursal=payload.sucursal_id,",
        "            uuid_transaccion=payload.uuid_local, metodo_pago=payload.tipo_pago, estado='CONFIRMADA'",
        "        )",
        "        db.add(nueva_venta)",
        "        db.flush()",
        "        for it in payload.items:",
        "            aplicar_operacion_inventario(",
        "                db=db, id_tenant=tenant.tenant_id, id_sucursal=payload.sucursal_id,",
        "                id_variante=it.variante_id, tipo_op='VENTA_DIRECTA', cantidad=it.cantidad",
        "            )",
        "            db.add(DetalleVenta(",
        "                id_venta=nueva_venta.id, id_variante=it.variante_id,",
        "                cantidad=it.cantidad, precio_unitario=it.precio_unitario",
        "            ))",
        "        db.commit()",
        "        return {'resultado': 'EXITO', 'mensaje': 'Venta offline conciliada exitosamente', 'venta_id': nueva_venta.id}",
        "    except ConflictStockError as ce:",
        "        db.rollback()",
        "        return {'resultado': 'CONFLICTO_STOCK', 'mensaje': str(ce), 'uuid': payload.uuid_local}"
    ]
    b.add_code_block("Fragmento 4.6: Endpoint de Sincronización Idempotente con Detección de Conflictos", code_46, "python")

    # 4.4.7
    b.add_heading_3("4.4.7. Módulo de Consultas Inteligentes con IA Generativa (Text-to-SQL) y Aislamiento Forzado")
    b.add_p(
        "El componente de analítica con Inteligencia Artificial permite formular preguntas en lenguaje natural "
        "(ej. '¿Cuáles son las 3 prendas con mayor rotación en la sucursal central este mes?'). La arquitectura inyecta "
        "de manera forzosa la cláusula WHERE tenant_id = :tenant_id en el árbol de sintaxis de la consulta SQL generada antes "
        "de ejecutarla contra PostgreSQL (RN10), imposibilitando cualquier filtración cruzada de información:"
    )
    code_47 = [
        "# backend/services/ai_analytics_service.py",
        "import re",
        "from sqlalchemy import text",
        "from sqlalchemy.orm import Session",
        "from backend.core.tenant_middleware import TenantContext",
        "from backend.core.exceptions import SecurityTenantViolationException",
        "",
        "class AIAnalyticsService:",
        "    def __init__(self, gemini_client):",
        "        self.client = gemini_client",
        "",
        "    def ejecutar_consulta_lenguaje_natural(self, db: Session, pregunta_usuario: str, tenant: TenantContext):",
        "        \"\"\"RN10: Genera la consulta SQL e impone obligatoriamente el filtro de tenant_id autenticado.\"\"\"",
        "        prompt = f'''",
        "        Actúa como un experto en SQL para PostgreSQL. Convierte la siguiente solicitud en una consulta SQL SELECT válida.",
        "        Esquema de tablas:",
        "        - ventas (id, id_tenant, id_sucursal, fecha_hora, total, estado)",
        "        - detalles_venta (id_venta, id_variante, cantidad, precio_unitario)",
        "        - productos (id, id_tenant, nombre, categoria)",
        "        Solicitud: {pregunta_usuario}",
        "        Retorna ÚNICAMENTE el bloque SQL sin explicaciones.",
        "        '''",
        "        respuesta_llm = self.client.generate_content(prompt).text.strip()",
        "        sql_generado = re.sub(r'```(sql)?', '', respuesta_llm).strip()",
        "",
        "        # RN10: Verificación y forzado estricto de seguridad multi-inquilino",
        "        if 'where' in sql_generado.lower():",
        "            sql_seguro = re.sub(",
        "                r'(?i)\\bwhere\\b', f\"WHERE ventas.id_tenant = '{tenant.tenant_id}' AND \", sql_generado, count=1",
        "            )",
        "        else:",
        "            sql_seguro = f\"{sql_generado} WHERE ventas.id_tenant = '{tenant.tenant_id}'\"",
        "",
        "        # Blindaje contra sentencias destructivas o inyecciones",
        "        if any(keyword in sql_seguro.upper() for keyword in ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER']):",
        "            raise SecurityTenantViolationException('Instrucción SQL no permitida en módulo analítico')",
        "",
        "        resultado = db.execute(text(sql_seguro)).mappings().all()",
        "        return {'query_ejecutado': sql_seguro, 'data': [dict(r) for r in resultado]}"
    ]
    b.add_code_block("Fragmento 4.7: Servicio de Generación de Consultas Text-to-SQL con Cláusula de Aislamiento Inyectada", code_47, "python")

    # =========================================================================
    # 4.5. INTEGRACIÓN DE COMPONENTES
    # =========================================================================
    b.add_heading_2("4.5. Integración de componentes")
    
    # 4.5.1
    b.add_heading_3("4.5.1. Integración del Frontend Web y la Aplicación Móvil con el Backend")
    b.add_p(
        "FashionStore contempla dos aplicaciones cliente: una aplicación web progresiva desarrollada con Angular 21 "
        "y una aplicación móvil desarrollada con Flutter 3.29. Ambas aplicaciones se comunican con el backend mediante "
        "solicitudes HTTP/2 a los endpoints de la API REST de FastAPI. Esta estructura permite compartir los servicios "
        "de autenticación, catálogo, inventario, ventas, reservas y administración de sucursales, independientemente "
        "del dispositivo empleado."
    )
    b.add_p(
        "La aplicación Angular PWA proporciona interfaces para la administración de empresas, suscripciones, usuarios, "
        "productos e inventarios. Por su parte, Flutter permite acceder a funcionalidades comerciales desde dispositivos "
        "Android e iOS. El proceso de comunicación comprende las siguientes etapas:"
    )
    b.add_bullet("El usuario realiza una operación desde la aplicación web o móvil.")
    b.add_bullet("El cliente envía una solicitud HTTP al endpoint correspondiente de FastAPI con el token Bearer JWT.")
    b.add_bullet("El backend verifica la autenticación y los permisos del usuario mediante middleware.")
    b.add_bullet("El servicio de aplicación ejecuta las validaciones y reglas de negocio.")
    b.add_bullet("Cuando la operación requiere persistencia, el backend consulta o actualiza PostgreSQL 16.")
    b.add_bullet("La API devuelve una respuesta estructurada (JSON) al cliente.")
    b.add_bullet("La aplicación cliente actualiza de forma reactiva la información presentada en la interfaz de usuario.")

    # 4.5.2
    b.add_heading_3("4.5.2. Integración de los Módulos de Negocio y Seguridad Multitenant")
    b.add_p(
        "Los módulos funcionales de FashionStore comparten servicios centrales de autenticación, autorización y administración "
        "del contexto empresarial. La plataforma emplea tokens JWT para identificar a los usuarios y establecer sus permisos de acceso. "
        "Estos tokens incorporan información relacionada con la empresa contratante, el rol y el contexto operativo de la sesión."
    )
    b.add_p(
        "El identificador tenant_id constituye un elemento fundamental de integración, debido a su participación en las operaciones "
        "de los diferentes módulos. Por ejemplo, cuando un administrador registra una nueva prenda, el módulo de catálogo recibe "
        "la solicitud y el backend identifica la empresa correspondiente mediante el contexto de autenticación. Posteriormente, "
        "el sistema registra la prenda asociándola al tenant_id autorizado. El mismo procedimiento se aplica en las consultas de "
        "inventario, ventas, reservas, sucursales y reportes analíticos."
    )
    b.add_p(
        "Asimismo, el módulo de suscripciones proporciona las condiciones necesarias para controlar las funcionalidades disponibles "
        "en cada empresa: antes de registrar nuevas sucursales, el sistema verifica los límites del plan contratado; de igual manera, "
        "el acceso a las consultas avanzadas mediante inteligencia artificial se restringe a los planes autorizados."
    )

    # 4.5.3
    b.add_heading_3("4.5.3. Integración del Backend con PostgreSQL")
    b.add_p(
        "La comunicación entre FastAPI y PostgreSQL 16 se estructura mediante SQLAlchemy 2.0 como herramienta de mapeo objeto-relacional "
        "y asyncpg como controlador de acceso asíncrono a la base de datos. Los modelos de persistencia representan las entidades del negocio, "
        "entre ellas Empresa, Suscripción, Sucursal, Usuario, Prenda, Variante, Inventario, Venta, Reserva, Traspaso y Nota de Devolución."
    )
    b.add_p(
        "La integración con PostgreSQL cumple tres condiciones principales:"
    )
    b.add_bullet("Aislamiento lógico de los datos mediante tenant_id en todas las entidades empresariales.", bold_prefix="1. ")
    b.add_bullet("Integridad referencial y claves foráneas compuestas entre empresas, sucursales, productos y operaciones.", bold_prefix="2. ")
    b.add_bullet("Consistencia transaccional mediante propiedades ACID estrictas en ventas, traspasos y cambios de prendas.", bold_prefix="3. ")

    # 4.5.4
    b.add_heading_3("4.5.4. Integración del Sistema Offline y el Motor de Sincronización")
    b.add_p(
        "Uno de los componentes principales de FashionStore corresponde al mecanismo de sincronización de operaciones "
        "realizadas sin conexión a Internet. La aplicación Angular PWA contempla almacenamiento local mediante IndexedDB, "
        "mientras que Flutter emplea SQLite para conservar información comercial en el dispositivo. Ambos mecanismos permiten "
        "almacenar catálogos descargados, reservas y ventas presenciales de contado durante interrupciones de conectividad."
    )
    b.add_p(
        "La integración entre los componentes locales y el backend se organiza mediante el siguiente flujo:"
    )
    b.add_bullet("El usuario registra una venta de contado o reserva mientras el dispositivo permanece desconectado.")
    b.add_bullet("La aplicación genera un identificador único UUIDv4 para la operación.")
    b.add_bullet("Los datos se almacenan en IndexedDB o SQLite, según la plataforma.")
    b.add_bullet("La operación permanece registrada en la cola local de sincronización (Outbox).")
    b.add_bullet("Cuando se recupera la conexión, el motor de sincronización envía los registros pendientes a FastAPI.")
    b.add_bullet("El backend verifica el token, el tenant_id y la existencia previa del UUID para garantizar idempotencia.")
    b.add_bullet("El sistema valida las reglas de negocio y la disponibilidad del inventario central.")
    b.add_bullet("Si la operación resulta válida, se confirma su registro en PostgreSQL; de lo contrario, se marca en conflicto.")
    b.add_bullet("El cliente recibe la respuesta del servidor y actualiza el estado de la operación local.")

    # 4.5.5
    b.add_heading_3("4.5.5. Integración de Inventarios, Ventas, Traspasos y Postventa")
    b.add_p(
        "Los módulos de inventario, operaciones comerciales y postventa mantienen una relación directa, debido a su responsabilidad "
        "compartida sobre las existencias de productos. Cuando se confirma una venta, el sistema actualiza las unidades disponibles "
        "de la variante correspondiente en la sucursal donde se realizó la operación. De forma similar, las reservas requieren "
        "identificar las cantidades comprometidas en stock_reservado para evitar su asignación a otras compras."
    )
    b.add_p(
        "En el proceso de traspasos entre sucursales, el módulo logístico interactúa con inventario para registrar la salida de mercadería "
        "desde el establecimiento de origen y su posterior recepción en el destino. Durante el traslado, las cantidades correspondientes "
        "permanecen identificadas como inventario en tránsito hasta confirmar la recepción física. En el módulo de postventa, la emisión "
        "de una Nota de Devolución también requiere comunicación con inventario ejecutando dos movimientos atómicos: "
        "(1) reingreso de la prenda devuelta al inventario disponible, y (2) salida de la nueva variante entregada al cliente."
    )

    # 4.5.6
    b.add_heading_3("4.5.6. Integración de Inteligencia Artificial y Analítica Predictiva")
    b.add_p(
        "FashionStore contempla la integración de servicios de inteligencia artificial generativa y modelos de Machine Learning "
        "mediante componentes especializados del backend. Para las consultas en lenguaje natural se considera Google Gemini API, "
        "encargada de interpretar las solicitudes formuladas por los administradores mediante texto o voz."
    )
    b.add_p(
        "El proceso de integración comprende la recepción de la consulta, su interpretación mediante el servicio de IA, "
        "la validación de los parámetros de seguridad e inyección forzada del tenant_id, y la obtención de información desde PostgreSQL. "
        "Para la exportación de reportes se consideran las bibliotecas ReportLab y OpenPyXL, destinadas a generar documentos PDF y "
        "archivos Excel. En el componente de Machine Learning se emplean Pandas y Scikit-Learn para el procesamiento de datos, "
        "entrenamiento y evaluación de modelos predictivos de demanda y segmentación RFM con K-Means."
    )

    # 4.5.7
    b.add_heading_3("4.5.7. Integración y Despliegue de la Plataforma")
    b.add_p(
        "La arquitectura de FashionStore contempla el despliegue de sus componentes mediante servicios en la nube en AWS "
        "(Amazon ECS Fargate para backend, Amazon RDS PostgreSQL 16 Multi-AZ para la base de datos central, y Amazon S3 / CloudFront "
        "para el frontend web PWA y almacenamiento multimedia), complementado con Render Cloud y Git/GitHub para control de versiones."
    )
    b.add_p(
        "La integración de las aplicaciones web y móvil administra variables de entorno de endpoints REST, claves JWT y credenciales "
        "seguras a través de AWS Secrets Manager, asegurando alta disponibilidad, resiliencia y monitorización continua."
    )

    # 2. Remover los nodos antiguos de 4.4 y 4.5
    print("Removiendo los párrafos antiguos de 4.4 y 4.5...")
    for elem in to_remove:
        body.remove(elem)
        
    print("Guardando documento final...")
    doc.save(DOC_PATH)
    print(f"Documento guardado exitosamente en: {DOC_PATH}")

if __name__ == "__main__":
    run_cap4_update()
