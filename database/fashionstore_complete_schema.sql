-- ============================================================================
-- SCRIPT DDL COMPLETO DE BASE DE DATOS - PLATAFORMA FASHIONSTORE SAAS
-- Motor de Base de Datos: PostgreSQL 15+ / 16+
-- Modelo Arquitectónico: SaaS Multi-tenant con esquema compartido e ID discriminador
-- Resiliencia: Arquitectura Offline-First con sincronización transaccional Outbox
-- Total de Tablas: 38
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ----------------------------------------------------------------------------
-- ELIMINACIÓN PREVENTIVA DE TABLAS (ORDEN INVERSO DE DEPENDENCIAS)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS "movimientos_inventario" CASCADE;
DROP TABLE IF EXISTS "ofertas_abastecimiento" CASCADE;
DROP TABLE IF EXISTS "detalles_venta" CASCADE;
DROP TABLE IF EXISTS "detalles_carrito" CASCADE;
DROP TABLE IF EXISTS "detalles_reserva" CASCADE;
DROP TABLE IF EXISTS "inventario" CASCADE;
DROP TABLE IF EXISTS "pagos" CASCADE;
DROP TABLE IF EXISTS "envios_venta" CASCADE;
DROP TABLE IF EXISTS "sync_operations" CASCADE;
DROP TABLE IF EXISTS "variantes_producto" CASCADE;
DROP TABLE IF EXISTS "recomendaciones_ia" CASCADE;
DROP TABLE IF EXISTS "sesiones_vestidor_virtual" CASCADE;
DROP TABLE IF EXISTS "productos_promocion" CASCADE;
DROP TABLE IF EXISTS "producto_proveedores" CASCADE;
DROP TABLE IF EXISTS "imagenes_producto" CASCADE;
DROP TABLE IF EXISTS "ventas" CASCADE;
DROP TABLE IF EXISTS "productos" CASCADE;
DROP TABLE IF EXISTS "bitacora" CASCADE;
DROP TABLE IF EXISTS "sesiones_actualizacion" CASCADE;
DROP TABLE IF EXISTS "carritos" CASCADE;
DROP TABLE IF EXISTS "usuario_sucursales" CASCADE;
DROP TABLE IF EXISTS "reservas" CASCADE;
DROP TABLE IF EXISTS "colecciones" CASCADE;
DROP TABLE IF EXISTS "usuarios" CASCADE;
DROP TABLE IF EXISTS "sucursales" CASCADE;
DROP TABLE IF EXISTS "rol_permisos" CASCADE;
DROP TABLE IF EXISTS "subscriptions" CASCADE;
DROP TABLE IF EXISTS "temporadas" CASCADE;
DROP TABLE IF EXISTS "proveedores" CASCADE;
DROP TABLE IF EXISTS "promociones" CASCADE;
DROP TABLE IF EXISTS "categorias" CASCADE;
DROP TABLE IF EXISTS "colores" CASCADE;
DROP TABLE IF EXISTS "tallas" CASCADE;
DROP TABLE IF EXISTS "ciudades" CASCADE;
DROP TABLE IF EXISTS "permisos" CASCADE;
DROP TABLE IF EXISTS "roles" CASCADE;
DROP TABLE IF EXISTS "subscription_plans" CASCADE;
DROP TABLE IF EXISTS "tenants" CASCADE;

-- ============================================================================
-- 1. TABLA: tenants
-- ============================================================================
CREATE TABLE tenants (
	id SERIAL NOT NULL, 
	name VARCHAR(150) NOT NULL, 
	status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);


-- ============================================================================
-- 2. TABLA: subscription_plans
-- ============================================================================
CREATE TABLE subscription_plans (
	id SERIAL NOT NULL, 
	code VARCHAR(32) NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	price_monthly NUMERIC(12, 2) DEFAULT '0.00' NOT NULL, 
	price_annual NUMERIC(12, 2) DEFAULT '0.00' NOT NULL, 
	currency VARCHAR(10) DEFAULT 'BOB' NOT NULL, 
	max_active_branches INTEGER NOT NULL, 
	generative_reports_enabled BOOLEAN DEFAULT FALSE NOT NULL, 
	is_active BOOLEAN DEFAULT TRUE NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_subscription_plans_code UNIQUE (code), 
	CONSTRAINT ck_subscription_plans_branch_limit_positive CHECK (max_active_branches > 0), 
	CONSTRAINT ck_subscription_plans_price_monthly_non_negative CHECK (price_monthly >= 0), 
	CONSTRAINT ck_subscription_plans_price_annual_non_negative CHECK (price_annual >= 0)
);


-- ============================================================================
-- 3. TABLA: roles
-- ============================================================================
CREATE TABLE roles (
	id SERIAL NOT NULL, 
	code VARCHAR(32) NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);


-- ============================================================================
-- 4. TABLA: permisos
-- ============================================================================
CREATE TABLE permisos (
	id SERIAL NOT NULL, 
	code VARCHAR(80) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code)
);


-- ============================================================================
-- 5. TABLA: ciudades
-- ============================================================================
CREATE TABLE ciudades (
	id SERIAL NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);


-- ============================================================================
-- 6. TABLA: tallas
-- ============================================================================
CREATE TABLE tallas (
	id SERIAL NOT NULL, 
	name VARCHAR(20) NOT NULL, 
	size_type VARCHAR(16) DEFAULT 'ALPHA' NOT NULL, 
	sort_order INTEGER DEFAULT '0' NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);


-- ============================================================================
-- 7. TABLA: colores
-- ============================================================================
CREATE TABLE colores (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	hex_code VARCHAR(7), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);


-- ============================================================================
-- 8. TABLA: categorias
-- ============================================================================
CREATE TABLE categorias (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	name VARCHAR(100) NOT NULL, 
	description VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_categories_tenant_name UNIQUE (tenant_id, name), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_categorias_tenant_id ON categorias (tenant_id);

-- ============================================================================
-- 9. TABLA: promociones
-- ============================================================================
CREATE TABLE promociones (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	name VARCHAR(150) NOT NULL, 
	description TEXT, 
	discount_type VARCHAR(20) NOT NULL, 
	discount_value NUMERIC(12, 2) NOT NULL, 
	starts_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	ends_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_promotion_discount_positive CHECK (discount_value > 0), 
	CONSTRAINT ck_promotion_dates_valid CHECK (ends_at > starts_at), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_promociones_tenant_id ON promociones (tenant_id);

-- ============================================================================
-- 10. TABLA: proveedores
-- ============================================================================
CREATE TABLE proveedores (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	trade_name VARCHAR(150) NOT NULL, 
	legal_name VARCHAR(200), 
	tax_id VARCHAR(50), 
	email VARCHAR(255), 
	phone VARCHAR(30), 
	address VARCHAR(255), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_suppliers_tenant_tax_id UNIQUE (tenant_id, tax_id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_proveedores_tenant_id ON proveedores (tenant_id);

-- ============================================================================
-- 11. TABLA: temporadas
-- ============================================================================
CREATE TABLE temporadas (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	name VARCHAR(100) NOT NULL, 
	starts_on DATE, 
	ends_on DATE, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_seasons_tenant_name UNIQUE (tenant_id, name), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE
);

CREATE INDEX ix_temporadas_tenant_id ON temporadas (tenant_id);

-- ============================================================================
-- 12. TABLA: subscriptions
-- ============================================================================
CREATE TABLE subscriptions (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	plan_id INTEGER NOT NULL, 
	status VARCHAR(20) DEFAULT 'ACTIVE' NOT NULL, 
	valid_from TIMESTAMP WITH TIME ZONE NOT NULL, 
	valid_until TIMESTAMP WITH TIME ZONE, 
	paused_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_subscriptions_status_valid CHECK (status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED', 'PAUSED')), 
	CONSTRAINT ck_subscriptions_valid_interval CHECK (valid_until IS NULL OR valid_until > valid_from), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(plan_id) REFERENCES subscription_plans (id) ON DELETE RESTRICT
);

CREATE INDEX ix_subscriptions_plan_id ON subscriptions (plan_id);
CREATE INDEX ix_subscriptions_tenant_id ON subscriptions (tenant_id);

-- ============================================================================
-- 13. TABLA: rol_permisos
-- ============================================================================
CREATE TABLE rol_permisos (
	role_id INTEGER NOT NULL, 
	permission_id INTEGER NOT NULL, 
	PRIMARY KEY (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE CASCADE, 
	FOREIGN KEY(permission_id) REFERENCES permisos (id) ON DELETE CASCADE
);


-- ============================================================================
-- 14. TABLA: sucursales
-- ============================================================================
CREATE TABLE sucursales (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	city_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	address VARCHAR(255) NOT NULL, 
	phone VARCHAR(30) NOT NULL, 
	latitude NUMERIC(9, 6), 
	longitude NUMERIC(9, 6), 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_branches_tenant_city_name UNIQUE (tenant_id, city_id, name), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(city_id) REFERENCES ciudades (id) ON DELETE RESTRICT
);

CREATE INDEX ix_sucursales_city_id ON sucursales (city_id);
CREATE INDEX ix_sucursales_tenant_id ON sucursales (tenant_id);

-- ============================================================================
-- 15. TABLA: usuarios
-- ============================================================================
CREATE TABLE usuarios (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	role_id INTEGER NOT NULL, 
	supplier_id INTEGER, 
	first_name VARCHAR(100) NOT NULL, 
	last_name VARCHAR(100) NOT NULL, 
	email VARCHAR(255) NOT NULL, 
	phone VARCHAR(30) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_users_tenant_email UNIQUE (tenant_id, email), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(role_id) REFERENCES roles (id) ON DELETE RESTRICT, 
	FOREIGN KEY(supplier_id) REFERENCES proveedores (id) ON DELETE SET NULL
);

CREATE INDEX ix_usuarios_role_id ON usuarios (role_id);
CREATE INDEX ix_usuarios_tenant_id ON usuarios (tenant_id);
CREATE UNIQUE INDEX ix_usuarios_supplier_id ON usuarios (supplier_id);
CREATE INDEX ix_usuarios_email ON usuarios (email);

-- ============================================================================
-- 16. TABLA: colecciones
-- ============================================================================
CREATE TABLE colecciones (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	season_id INTEGER NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description TEXT, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_collections_season_name UNIQUE (season_id, name), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(season_id) REFERENCES temporadas (id) ON DELETE RESTRICT
);

CREATE INDEX ix_colecciones_season_id ON colecciones (season_id);
CREATE INDEX ix_colecciones_tenant_id ON colecciones (tenant_id);

-- ============================================================================
-- 17. TABLA: reservas
-- ============================================================================
CREATE TABLE reservas (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	customer_id INTEGER NOT NULL, 
	branch_id INTEGER NOT NULL, 
	scheduled_for TIMESTAMP WITH TIME ZONE, 
	status VARCHAR(30) NOT NULL, 
	notes TEXT, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(branch_id) REFERENCES sucursales (id) ON DELETE RESTRICT
);

CREATE INDEX ix_reservations_tenant_branch_status ON reservas (tenant_id, branch_id, status);
CREATE INDEX ix_reservas_tenant_id ON reservas (tenant_id);
CREATE INDEX ix_reservations_customer_status ON reservas (customer_id, status);
CREATE INDEX ix_reservas_customer_id ON reservas (customer_id);
CREATE INDEX ix_reservas_branch_id ON reservas (branch_id);

-- ============================================================================
-- 18. TABLA: usuario_sucursales
-- ============================================================================
CREATE TABLE usuario_sucursales (
	user_id INTEGER NOT NULL, 
	branch_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, branch_id), 
	FOREIGN KEY(user_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES sucursales (id) ON DELETE CASCADE
);


-- ============================================================================
-- 19. TABLA: carritos
-- ============================================================================
CREATE TABLE carritos (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	customer_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_carts_tenant_customer UNIQUE (tenant_id, customer_id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES usuarios (id) ON DELETE CASCADE
);

CREATE INDEX ix_carritos_customer_id ON carritos (customer_id);
CREATE INDEX ix_carritos_tenant_id ON carritos (tenant_id);

-- ============================================================================
-- 20. TABLA: sesiones_actualizacion
-- ============================================================================
CREATE TABLE sesiones_actualizacion (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	session_id VARCHAR(64), 
	token_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	revoked_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES usuarios (id) ON DELETE CASCADE, 
	UNIQUE (token_hash)
);

CREATE INDEX ix_sesiones_actualizacion_user_id ON sesiones_actualizacion (user_id);
CREATE UNIQUE INDEX ix_sesiones_actualizacion_session_id ON sesiones_actualizacion (session_id);

-- ============================================================================
-- 21. TABLA: bitacora
-- ============================================================================
CREATE TABLE bitacora (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	usuario_id INTEGER, 
	accion VARCHAR(30) NOT NULL, 
	tipo_entidad VARCHAR(100) NOT NULL, 
	entidad_id INTEGER, 
	descripcion TEXT, 
	valores_anteriores JSON, 
	valores_nuevos JSON, 
	direccion_ip VARCHAR(45), 
	agente_usuario VARCHAR(500), 
	fecha_creacion TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE SET NULL, 
	FOREIGN KEY(usuario_id) REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE INDEX ix_bitacora_entity ON bitacora (tipo_entidad, entidad_id);
CREATE INDEX ix_bitacora_created_at ON bitacora (fecha_creacion);
CREATE INDEX ix_bitacora_tenant_id ON bitacora (tenant_id);
CREATE INDEX ix_bitacora_tenant_created_at ON bitacora (tenant_id, fecha_creacion);
CREATE INDEX ix_bitacora_usuario_id ON bitacora (usuario_id);
CREATE INDEX ix_bitacora_tenant_entity ON bitacora (tenant_id, tipo_entidad, entidad_id);

-- ============================================================================
-- 22. TABLA: productos
-- ============================================================================
CREATE TABLE productos (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	category_id INTEGER NOT NULL, 
	season_id INTEGER, 
	collection_id INTEGER, 
	audience VARCHAR(16) DEFAULT 'UNISEX' NOT NULL, 
	size_system VARCHAR(16) DEFAULT 'ALPHA' NOT NULL, 
	code VARCHAR(50) NOT NULL, 
	name VARCHAR(180) NOT NULL, 
	slug VARCHAR(200) NOT NULL, 
	description TEXT, 
	price NUMERIC(12, 2) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_products_tenant_code UNIQUE (tenant_id, code), 
	CONSTRAINT uq_products_tenant_slug UNIQUE (tenant_id, slug), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(category_id) REFERENCES categorias (id) ON DELETE RESTRICT, 
	FOREIGN KEY(season_id) REFERENCES temporadas (id) ON DELETE RESTRICT, 
	FOREIGN KEY(collection_id) REFERENCES colecciones (id) ON DELETE RESTRICT
);

CREATE INDEX ix_productos_audience ON productos (audience);
CREATE INDEX ix_productos_collection_id ON productos (collection_id);
CREATE INDEX ix_productos_category_id ON productos (category_id);
CREATE INDEX ix_productos_name ON productos (name);
CREATE INDEX ix_productos_season_id ON productos (season_id);
CREATE INDEX ix_productos_size_system ON productos (size_system);
CREATE INDEX ix_productos_tenant_id ON productos (tenant_id);
CREATE INDEX ix_productos_tenant_name ON productos (tenant_id, name);

-- ============================================================================
-- 23. TABLA: ventas
-- ============================================================================
CREATE TABLE ventas (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	order_number VARCHAR(30) NOT NULL, 
	customer_id INTEGER, 
	branch_id INTEGER, 
	cashier_id INTEGER, 
	reservation_id INTEGER, 
	channel VARCHAR(20) NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	fulfillment_type VARCHAR(20) DEFAULT 'PICKUP' NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	discount NUMERIC(12, 2) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sales_tenant_order_number UNIQUE (tenant_id, order_number), 
	CONSTRAINT ck_sales_fulfillment_type CHECK (fulfillment_type IN ('PICKUP', 'DELIVERY')), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(branch_id) REFERENCES sucursales (id) ON DELETE RESTRICT, 
	FOREIGN KEY(cashier_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(reservation_id) REFERENCES reservas (id) ON DELETE RESTRICT
);

CREATE INDEX ix_ventas_order_number ON ventas (order_number);
CREATE INDEX ix_sales_customer_created ON ventas (customer_id, created_at);
CREATE INDEX ix_sales_tenant_created ON ventas (tenant_id, created_at);
CREATE INDEX ix_ventas_tenant_id ON ventas (tenant_id);
CREATE INDEX ix_ventas_reservation_id ON ventas (reservation_id);
CREATE INDEX ix_ventas_cashier_id ON ventas (cashier_id);
CREATE INDEX ix_ventas_branch_id ON ventas (branch_id);
CREATE INDEX ix_ventas_customer_id ON ventas (customer_id);

-- ============================================================================
-- 24. TABLA: imagenes_producto
-- ============================================================================
CREATE TABLE imagenes_producto (
	id SERIAL NOT NULL, 
	product_id INTEGER NOT NULL, 
	image_url VARCHAR(500) NOT NULL, 
	is_primary BOOLEAN NOT NULL, 
	sort_order INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_product_image_order UNIQUE (product_id, sort_order), 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE CASCADE
);

CREATE INDEX ix_imagenes_producto_product_id ON imagenes_producto (product_id);

-- ============================================================================
-- 25. TABLA: producto_proveedores
-- ============================================================================
CREATE TABLE producto_proveedores (
	product_id INTEGER NOT NULL, 
	supplier_id INTEGER NOT NULL, 
	PRIMARY KEY (product_id, supplier_id), 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE CASCADE, 
	FOREIGN KEY(supplier_id) REFERENCES proveedores (id) ON DELETE RESTRICT
);


-- ============================================================================
-- 26. TABLA: productos_promocion
-- ============================================================================
CREATE TABLE productos_promocion (
	promotion_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	PRIMARY KEY (promotion_id, product_id), 
	FOREIGN KEY(promotion_id) REFERENCES promociones (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE CASCADE
);


-- ============================================================================
-- 27. TABLA: sesiones_vestidor_virtual
-- ============================================================================
CREATE TABLE sesiones_vestidor_virtual (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	customer_id INTEGER, 
	product_id INTEGER NOT NULL, 
	status VARCHAR(20) NOT NULL, 
	device_info VARCHAR(255), 
	started_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	ended_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE RESTRICT
);

CREATE INDEX ix_sesiones_vestidor_virtual_tenant_id ON sesiones_vestidor_virtual (tenant_id);
CREATE INDEX ix_sesiones_vestidor_virtual_product_id ON sesiones_vestidor_virtual (product_id);
CREATE INDEX ix_sesiones_vestidor_virtual_customer_id ON sesiones_vestidor_virtual (customer_id);

-- ============================================================================
-- 28. TABLA: recomendaciones_ia
-- ============================================================================
CREATE TABLE recomendaciones_ia (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	customer_id INTEGER, 
	product_id INTEGER NOT NULL, 
	source VARCHAR(50) NOT NULL, 
	reason TEXT, 
	score NUMERIC(5, 4), 
	context JSON, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(customer_id) REFERENCES usuarios (id) ON DELETE SET NULL, 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE RESTRICT
);

CREATE INDEX ix_recomendaciones_ia_customer_id ON recomendaciones_ia (customer_id);
CREATE INDEX ix_recomendaciones_ia_tenant_id ON recomendaciones_ia (tenant_id);
CREATE INDEX ix_recomendaciones_ia_product_id ON recomendaciones_ia (product_id);

-- ============================================================================
-- 29. TABLA: variantes_producto
-- ============================================================================
CREATE TABLE variantes_producto (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	product_id INTEGER NOT NULL, 
	size_id INTEGER NOT NULL, 
	color_id INTEGER NOT NULL, 
	sku VARCHAR(80) NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_product_variant_attributes UNIQUE (product_id, size_id, color_id), 
	CONSTRAINT uq_product_variants_tenant_sku UNIQUE (tenant_id, sku), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_id) REFERENCES productos (id) ON DELETE CASCADE, 
	FOREIGN KEY(size_id) REFERENCES tallas (id) ON DELETE RESTRICT, 
	FOREIGN KEY(color_id) REFERENCES colores (id) ON DELETE RESTRICT
);

CREATE INDEX ix_variantes_producto_product_id ON variantes_producto (product_id);
CREATE INDEX ix_variantes_producto_sku ON variantes_producto (sku);
CREATE INDEX ix_variantes_producto_tenant_id ON variantes_producto (tenant_id);

-- ============================================================================
-- 30. TABLA: sync_operations
-- ============================================================================
CREATE TABLE sync_operations (
	id SERIAL NOT NULL, 
	tenant_id INTEGER NOT NULL, 
	client_operation_id VARCHAR(64) NOT NULL, 
	branch_id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	operation_type VARCHAR(30) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	payload JSON NOT NULL, 
	conflict_detail JSON, 
	sale_id INTEGER, 
	reservation_id INTEGER, 
	processed_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_sync_operations_tenant_client_op_id UNIQUE (tenant_id, client_operation_id), 
	CONSTRAINT ck_sync_operations_type CHECK (operation_type IN ('SALE', 'RESERVATION')), 
	CONSTRAINT ck_sync_operations_status CHECK (status IN ('CONFIRMED', 'CONFLICT', 'REJECTED')), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES sucursales (id) ON DELETE RESTRICT, 
	FOREIGN KEY(user_id) REFERENCES usuarios (id) ON DELETE RESTRICT, 
	FOREIGN KEY(sale_id) REFERENCES ventas (id) ON DELETE SET NULL, 
	FOREIGN KEY(reservation_id) REFERENCES reservas (id) ON DELETE SET NULL
);

CREATE INDEX ix_sync_operations_tenant_id ON sync_operations (tenant_id);
CREATE INDEX ix_sync_operations_reservation_id ON sync_operations (reservation_id);
CREATE INDEX ix_sync_operations_sale_id ON sync_operations (sale_id);
CREATE INDEX ix_sync_operations_user_id ON sync_operations (user_id);
CREATE INDEX ix_sync_operations_tenant_created ON sync_operations (tenant_id, created_at);
CREATE INDEX ix_sync_operations_branch_id ON sync_operations (branch_id);
CREATE INDEX ix_sync_operations_client_operation_id ON sync_operations (client_operation_id);

-- ============================================================================
-- 31. TABLA: envios_venta
-- ============================================================================
CREATE TABLE envios_venta (
	id SERIAL NOT NULL, 
	sale_id INTEGER NOT NULL, 
	recipient_name VARCHAR(120) NOT NULL, 
	recipient_ci VARCHAR(30) NOT NULL, 
	recipient_phone VARCHAR(30) NOT NULL, 
	department_or_city VARCHAR(100) NOT NULL, 
	zone VARCHAR(120) NOT NULL, 
	street VARCHAR(150) NOT NULL, 
	house_number VARCHAR(50) NOT NULL, 
	reference VARCHAR(255) NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(sale_id) REFERENCES ventas (id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX ix_envios_venta_sale_id ON envios_venta (sale_id);

-- ============================================================================
-- 32. TABLA: pagos
-- ============================================================================
CREATE TABLE pagos (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	idempotency_key VARCHAR(100), 
	sale_id INTEGER NOT NULL, 
	method VARCHAR(30) NOT NULL, 
	provider VARCHAR(50), 
	transaction_reference VARCHAR(150), 
	status VARCHAR(20) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	received_amount NUMERIC(12, 2), 
	change_amount NUMERIC(12, 2), 
	metadata_json JSON, 
	paid_at TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_payments_tenant_provider_reference UNIQUE (tenant_id, provider, transaction_reference), 
	CONSTRAINT uq_payments_tenant_idempotency_key UNIQUE (tenant_id, idempotency_key), 
	CONSTRAINT ck_payment_amount_nonnegative CHECK (amount >= 0), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(sale_id) REFERENCES ventas (id) ON DELETE RESTRICT
);

CREATE INDEX ix_pagos_sale_id ON pagos (sale_id);
CREATE INDEX ix_pagos_idempotency_key ON pagos (idempotency_key);
CREATE INDEX ix_pagos_tenant_id ON pagos (tenant_id);

-- ============================================================================
-- 33. TABLA: inventario
-- ============================================================================
CREATE TABLE inventario (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	branch_id INTEGER NOT NULL, 
	product_variant_id INTEGER NOT NULL, 
	stock_quantity INTEGER NOT NULL, 
	reserved_quantity INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_inventory_branch_variant UNIQUE (branch_id, product_variant_id), 
	CONSTRAINT ck_inventory_stock_nonnegative CHECK (stock_quantity >= 0), 
	CONSTRAINT ck_inventory_reserved_valid CHECK (reserved_quantity >= 0 AND reserved_quantity <= stock_quantity), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(branch_id) REFERENCES sucursales (id) ON DELETE RESTRICT, 
	FOREIGN KEY(product_variant_id) REFERENCES variantes_producto (id) ON DELETE RESTRICT
);

CREATE INDEX ix_inventory_tenant_branch ON inventario (tenant_id, branch_id);
CREATE INDEX ix_inventario_tenant_id ON inventario (tenant_id);
CREATE INDEX ix_inventario_product_variant_id ON inventario (product_variant_id);
CREATE INDEX ix_inventario_branch_id ON inventario (branch_id);

-- ============================================================================
-- 34. TABLA: detalles_reserva
-- ============================================================================
CREATE TABLE detalles_reserva (
	id SERIAL NOT NULL, 
	reservation_id INTEGER NOT NULL, 
	product_variant_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reservation_variant UNIQUE (reservation_id, product_variant_id), 
	CONSTRAINT ck_reservation_item_quantity_positive CHECK (quantity > 0), 
	FOREIGN KEY(reservation_id) REFERENCES reservas (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_variant_id) REFERENCES variantes_producto (id) ON DELETE RESTRICT
);

CREATE INDEX ix_detalles_reserva_reservation_id ON detalles_reserva (reservation_id);

-- ============================================================================
-- 35. TABLA: detalles_carrito
-- ============================================================================
CREATE TABLE detalles_carrito (
	id SERIAL NOT NULL, 
	cart_id INTEGER NOT NULL, 
	product_variant_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_cart_variant UNIQUE (cart_id, product_variant_id), 
	CONSTRAINT ck_cart_item_quantity_positive CHECK (quantity > 0), 
	FOREIGN KEY(cart_id) REFERENCES carritos (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_variant_id) REFERENCES variantes_producto (id) ON DELETE RESTRICT
);

CREATE INDEX ix_detalles_carrito_cart_id ON detalles_carrito (cart_id);

-- ============================================================================
-- 36. TABLA: detalles_venta
-- ============================================================================
CREATE TABLE detalles_venta (
	id SERIAL NOT NULL, 
	sale_id INTEGER NOT NULL, 
	product_variant_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	unit_price NUMERIC(12, 2) NOT NULL, 
	discount NUMERIC(12, 2) NOT NULL, 
	line_total NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_sale_item_quantity_positive CHECK (quantity > 0), 
	CONSTRAINT ck_sale_item_total_nonnegative CHECK (line_total >= 0), 
	FOREIGN KEY(sale_id) REFERENCES ventas (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_variant_id) REFERENCES variantes_producto (id) ON DELETE RESTRICT
);

CREATE INDEX ix_detalles_venta_sale_id ON detalles_venta (sale_id);

-- ============================================================================
-- 37. TABLA: ofertas_abastecimiento
-- ============================================================================
CREATE TABLE ofertas_abastecimiento (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	supplier_id INTEGER NOT NULL, 
	product_variant_id INTEGER NOT NULL, 
	season_id INTEGER NOT NULL, 
	collection_id INTEGER, 
	status VARCHAR(20) DEFAULT 'AVAILABLE' NOT NULL, 
	available_quantity INTEGER DEFAULT '0' NOT NULL, 
	expected_date DATE, 
	notes TEXT, 
	is_active BOOLEAN NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_supply_offer_quantity_nonnegative CHECK (available_quantity >= 0), 
	CONSTRAINT ck_supply_offer_status CHECK (status IN ('AVAILABLE', 'LIMITED', 'OUT_OF_STOCK', 'UPCOMING')), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(supplier_id) REFERENCES proveedores (id) ON DELETE CASCADE, 
	FOREIGN KEY(product_variant_id) REFERENCES variantes_producto (id) ON DELETE RESTRICT, 
	FOREIGN KEY(season_id) REFERENCES temporadas (id) ON DELETE RESTRICT, 
	FOREIGN KEY(collection_id) REFERENCES colecciones (id) ON DELETE RESTRICT
);

CREATE INDEX ix_supply_offer_supplier ON ofertas_abastecimiento (supplier_id);
CREATE INDEX ix_supply_offer_variant ON ofertas_abastecimiento (product_variant_id);
CREATE INDEX ix_ofertas_abastecimiento_tenant_id ON ofertas_abastecimiento (tenant_id);

-- ============================================================================
-- 38. TABLA: movimientos_inventario
-- ============================================================================
CREATE TABLE movimientos_inventario (
	id SERIAL NOT NULL, 
	tenant_id INTEGER, 
	inventory_id INTEGER NOT NULL, 
	movement_type VARCHAR(30) NOT NULL, 
	quantity INTEGER NOT NULL, 
	stock_before INTEGER NOT NULL, 
	stock_after INTEGER NOT NULL, 
	reason VARCHAR(255), 
	reference_type VARCHAR(50), 
	reference_id INTEGER, 
	created_by INTEGER, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_inventory_movement_quantity_positive CHECK (quantity > 0), 
	CONSTRAINT ck_inventory_movement_stock_nonnegative CHECK (stock_before >= 0 AND stock_after >= 0), 
	CONSTRAINT ck_inventory_movement_type_valid CHECK (movement_type IN ('IN', 'OUT', 'RETURN', 'RESERVE', 'RELEASE', 'SALE')), 
	FOREIGN KEY(tenant_id) REFERENCES tenants (id) ON DELETE CASCADE, 
	FOREIGN KEY(inventory_id) REFERENCES inventario (id) ON DELETE RESTRICT, 
	FOREIGN KEY(created_by) REFERENCES usuarios (id) ON DELETE SET NULL
);

CREATE INDEX ix_movimientos_inventario_inventory_id ON movimientos_inventario (inventory_id);
CREATE INDEX ix_movimientos_inventario_created_by ON movimientos_inventario (created_by);
CREATE INDEX ix_movimientos_inventario_tenant_id ON movimientos_inventario (tenant_id);
