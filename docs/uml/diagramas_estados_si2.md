# Catálogo de Diagramas de Estados UML (State Machine Diagrams) — FashionStore (SI2)

Este documento contiene la especificación formal y los **Diagramas de Estados** para los Casos de Uso (CU) de los **Ciclos 1, 2 y 3** del sistema **FashionStore**.

Los diagramas están modelados siguiendo el estándar exacto de **Sistemas de Información 2 (SI2)**, donde se representa el flujo de vida y control de la transacción del Caso de Uso:
- **Estado Inicial (`Inicio`)**
- **Autenticación del Actor** con ciclo de validación de credenciales `[error]` / `[correcto]`
- **Estado Central de Navegación** (`Seleccionar opción ...`)
- **Bifurcaciones con condiciones de guarda `[...]`** para cada operación del CU
- **Puntos de control transaccional** (`Revisar Datos`, `Verificar Disponibilidad`, `Procesar Pago`, etc.)
- **Estado Final (`Fin`)** alcanzado tras la `Transacción completada`.

---

## 📑 Índice de Diagramas

- [Ciclo 1: Base de Plataforma, Seguridad y Catálogo](#ciclo-1-base-de-plataforma-seguridad-y-catálogo)
  - [CU01: Registrar Cliente](#cu01-registrar-cliente)
  - [CU02: Autenticación (Login, Logout y Refresh Token)](#cu02-autenticación-login-logout-y-refresh-token)
  - [CU03: Gestionar Usuarios y Roles](#cu03-gestionar-usuarios-y-roles)
  - [CU04: Gestionar Sucursales y Ciudades](#cu04-gestionar-sucursales-y-ciudades)
  - [CU05: Gestionar Productos y Variantes](#cu05-gestionar-productos-y-variantes)
  - [CU08 / CU09: Consultar Catálogo y Disponibilidad en Tiendas](#cu08--cu09-consultar-catálogo-y-disponibilidad-en-tiendas)
- [Ciclo 2: Operación Comercial, Logística y Reservas](#ciclo-2-operación-comercial-logística-y-reservas)
  - [CU10: Realizar Reserva de Prendas](#cu10-realizar-reserva-de-prendas)
  - [CU11: Atender Reservas en Sucursal](#cu11-atender-reservas-en-sucursal)
  - [CU13: Administrar Carrito de Compras](#cu13-administrar-carrito-de-compras)
  - [CU14: Realizar Compra Digital (Checkout E-commerce)](#cu14-realizar-compra-digital-checkout-e-commerce)
  - [CU15 / CU16: Venta Presencial y Cobro en Caja (POS)](#cu15--cu16-venta-presencial-y-cobro-en-caja-pos)
  - [CU17: Procesar Pago Electrónico (Sandbox / QR / Stripe)](#cu17-procesar-pago-electrónico-sandbox--qr--stripe)
  - [CU18: Gestionar Inventario y Movimientos (Kárdex)](#cu18-gestionar-inventario-y-movimientos-kárdex)
- [Ciclo 3: Innovación, Analítica e Inteligencia Artificial](#ciclo-3-innovación-analítica-e-inteligencia-artificial)
  - [CU12: Sesión de Probador Virtual (Fitting Room)](#cu12-sesión-de-probador-virtual-fitting-room)
  - [CU20: Gestionar Promociones y Descuentos](#cu20-gestionar-promociones-y-descuentos)
  - [CU21: Dashboards y Reportes Gerenciales con Sofía Copilot IA](#cu21-dashboards-y-reportes-gerenciales-con-sofía-copilot-ia)
  - [CU22: Obtener Recomendaciones con IA](#cu22-obtener-recomendaciones-con-ia)
  - [CU23: Consultar Historial de Compras y Devoluciones](#cu23-consultar-historial-de-compras-y-devoluciones)

---

# Ciclo 1: Base de Plataforma, Seguridad y Catálogo

---

### CU01: Registrar Cliente

Modela el proceso de creación de una nueva cuenta de cliente, asegurando la unicidad del correo electrónico y el cumplimiento de las políticas de seguridad.

```mermaid
stateDiagram-v2
    [*] --> Formulario_Registro: Inicio
    Formulario_Registro --> Validar_Datos: [ingresar datos personales y contraseña]
    
    Validar_Datos --> Formulario_Registro: [formato inválido o contraseña débil]
    Validar_Datos --> Verificar_Email: [datos válidos]

    Verificar_Email --> Formulario_Registro: [email duplicado]
    Verificar_Email --> Crear_Cuenta_Cliente: [email disponible]

    Crear_Cuenta_Cliente --> Generar_Sesion_Inicial: [asignar rol CLIENT]
    Generar_Sesion_Inicial --> Transaccion_Completada: [emitir tokens JWT]
    Transaccion_Completada --> [*]: Fin
```

---

### CU02: Autenticación (Login, Logout y Refresh Token)

Modela el ciclo de vida de la sesión del usuario en el sistema para cualquier actor (`CLIENT`, `ADMIN`, `BRANCH_MANAGER`, `CASHIER`, `SUPPLIER`).

```mermaid
stateDiagram-v2
    [*] --> Ingresar_Credenciales: Inicio
    
    Ingresar_Credenciales --> Ingresar_Credenciales: [error credenciales]
    Ingresar_Credenciales --> Denegar_Acceso: [usuario inactivo]
    Denegar_Acceso --> [*]: Fin
    
    Ingresar_Credenciales --> Sesion_Activa: [credenciales válidas]
    
    Sesion_Activa --> Renovar_Token: [access token expirado]
    Renovar_Token --> Sesion_Activa: [refresh token válido]
    Renovar_Token --> Ingresar_Credenciales: [refresh token expirado / revocado]

    Sesion_Activa --> Revocar_Sesion: [solicitar cerrar sesión]
    Revocar_Sesion --> Transaccion_Completada: [eliminar token de base de datos]
    Transaccion_Completada --> [*]: Fin
```

---

### CU03: Gestionar Usuarios y Roles

Corresponde al modelo administrativo de gestión de cuentas de usuario, asignación de roles y sucursales.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Administrador: Inicio
    Loguear_Administrador --> Loguear_Administrador: [error]
    Loguear_Administrador --> Seleccionar_Opcion_Usuario: [correcto]

    Seleccionar_Opcion_Usuario --> Desplegar_Lista: [listar]
    Desplegar_Lista --> [*]: Fin

    Seleccionar_Opcion_Usuario --> Crear_Usuario: [crear]
    Crear_Usuario --> Revisar_Datos: [llenar datos]

    Seleccionar_Opcion_Usuario --> Modificar_Usuario: [modificar]
    Modificar_Usuario --> Revisar_Datos: [llenar datos]

    Seleccionar_Opcion_Usuario --> ID_Usuario_Eliminar: [eliminar]
    ID_Usuario_Eliminar --> Seleccionar_Opcion_Usuario: [incorrecto]
    ID_Usuario_Eliminar --> Eliminar_Usuario: [correcto]

    Revisar_Datos --> Transaccion_Completada: [datos validados]
    Eliminar_Usuario --> Transaccion_Completada: [desactivación completada]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU04: Gestionar Sucursales y Ciudades

Permite al administrador abrir nuevas tiendas físicas, asignar sucursales a ciudades y activar/desactivar locales.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Administrador: Inicio
    Loguear_Administrador --> Loguear_Administrador: [error credenciales]
    Loguear_Administrador --> Seleccionar_Opcion_Sucursal: [correcto]

    Seleccionar_Opcion_Sucursal --> Desplegar_Lista_Sucursales: [listar]
    Desplegar_Lista_Sucursales --> [*]: Fin

    Seleccionar_Opcion_Sucursal --> Crear_Sucursal: [crear]
    Crear_Sucursal --> Revisar_Datos_Sucursal: [seleccionar ciudad, nombre y dirección]

    Seleccionar_Opcion_Sucursal --> Modificar_Sucursal: [modificar]
    Modificar_Sucursal --> Revisar_Datos_Sucursal: [actualizar teléfono / dirección]

    Seleccionar_Opcion_Sucursal --> ID_Sucursal_Estado: [cambiar estado]
    ID_Sucursal_Estado --> Seleccionar_Opcion_Sucursal: [sucursal inexistente]
    ID_Sucursal_Estado --> Actualizar_Estado_Tienda: [sucursal válida]

    Revisar_Datos_Sucursal --> Transaccion_Completada: [guardar cambios]
    Actualizar_Estado_Tienda --> Transaccion_Completada: [activar / suspender]
    Transaccion_Completada --> [*]: Fin
```

---

### CU05: Gestionar Productos y Variantes

Modela la administración integral de prendas del atelier: ficha base, combinaciones de tallas y colores, galería de imágenes y publicación.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Administrador: Inicio
    Loguear_Administrador --> Loguear_Administrador: [error]
    Loguear_Administrador --> Seleccionar_Opcion_Prenda: [correcto]

    Seleccionar_Opcion_Prenda --> Desplegar_Catalogo_Admin: [listar]
    Desplegar_Catalogo_Admin --> [*]: Fin

    Seleccionar_Opcion_Prenda --> Crear_Ficha_Producto: [crear]
    Crear_Ficha_Producto --> Configurar_Variantes: [ingresar nombre, código y precio base]
    
    Configurar_Variantes --> Cargar_Imagenes: [asignar tallas, colores y SKUs]
    Cargar_Imagenes --> Revisar_Producto_Completo: [subir fotografías y portada]

    Seleccionar_Opcion_Prenda --> Modificar_Prenda: [modificar precio / variantes]
    Modificar_Prenda --> Revisar_Producto_Completo: [actualizar]

    Revisar_Producto_Completo --> Publicar_En_Catalogo: [validar variantes y fotos OK]
    Publicar_En_Catalogo --> Transaccion_Completada: [producto visible al cliente]
    Transaccion_Completada --> [*]: Fin
```

---

### CU08 / CU09: Consultar Catálogo y Disponibilidad en Tiendas

Modela la experiencia del cliente explorando prendas, aplicando filtros multivariables y verificando stock por sucursal física.

```mermaid
stateDiagram-v2
    [*] --> Abrir_Catalogo: Inicio
    Abrir_Catalogo --> Aplicar_Filtros: [filtrar por categoría, talla o color]
    Aplicar_Filtros --> Desplegar_Prendas: [resultados coincidentes]
    
    Desplegar_Prendas --> Ver_Detalle_Prenda: [seleccionar prenda]
    
    Ver_Detalle_Prenda --> Consultar_Disponibilidad: [seleccionar talla y color]
    
    Consultar_Disponibilidad --> Notificar_Agotado: [sin existencias en ninguna tienda]
    Notificar_Agotado --> Ver_Detalle_Prenda: [seleccionar otra variante]

    Consultar_Disponibilidad --> Mostrar_Sucursales_Con_Stock: [stock disponible > 0]
    
    Mostrar_Sucursales_Con_Stock --> Derivar_A_Reserva: [cliente decide reservar para probar]
    Mostrar_Sucursales_Con_Stock --> Derivar_A_Carrito: [cliente decide comprar online]

    Derivar_A_Reserva --> Transaccion_Completada: [continuar en CU10]
    Derivar_A_Carrito --> Transaccion_Completada: [continuar en CU13]
    Transaccion_Completada --> [*]: Fin
```

---

# Ciclo 2: Operación Comercial, Logística y Reservas

---

### CU10: Realizar Reserva de Prendas

Permite al cliente separar prendas para probárselas presencialmente en una sucursal en una fecha programada, con bloqueo temporal de inventario.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Cliente: Inicio
    Loguear_Cliente --> Loguear_Cliente: [error credenciales]
    Loguear_Cliente --> Seleccionar_Prenda: [correcto]

    Seleccionar_Prenda --> Consultar_Disponibilidad: [elegir talla y color]
    
    Consultar_Disponibilidad --> Seleccionar_Prenda: [sin stock en sucursal]
    Consultar_Disponibilidad --> Configurar_Reserva: [stock disponible]

    Configurar_Reserva --> Revisar_Datos_Reserva: [seleccionar sucursal y fecha de visita]
    
    Revisar_Datos_Reserva --> Configurar_Reserva: [modificar selección]
    Revisar_Datos_Reserva --> Bloquear_Stock_Temporal: [confirmar reserva]
    
    Bloquear_Stock_Temporal --> Transaccion_Completada: [generar código FS-XXXX y estado PENDING]
    Transaccion_Completada --> [*]: Fin
```

---

### CU11: Atender Reservas en Sucursal

Modela el flujo de trabajo del Encargado de Sucursal para preparar las prendas en percheros y atender al cliente cuando asiste a la tienda.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Encargado: Inicio
    Loguear_Encargado --> Loguear_Encargado: [error]
    Loguear_Encargado --> Bandeja_Reservas_Sucursal: [correcto]

    Bandeja_Reservas_Sucursal --> Seleccionar_Reserva_Pending: [seleccionar reserva PENDING]
    
    Seleccionar_Reserva_Pending --> Preparando_Prendas: [iniciar búsqueda en almacén]
    Preparando_Prendas --> Prendas_Listas_En_Probador: [prendas ubicadas en perchero (READY)]

    Prendas_Listas_En_Probador --> Cliente_Asiste: [cliente se presenta en fecha]
    Prendas_Listas_En_Probador --> Cliente_Ausente: [plazo expirado / 48 hrs]

    Cliente_Asiste --> Marcar_Reserva_Atendida: [cliente se prueba las prendas (ATTENDED)]
    Cliente_Ausente --> Liberar_Stock_Reservado: [reintegrar prendas a disponibilidad (EXPIRED)]

    Marcar_Reserva_Atendida --> Transaccion_Completada
    Liberar_Stock_Reservado --> Transaccion_Completada
    Transaccion_Completada --> [*]: Fin
```

---

### CU13: Administrar Carrito de Compras

Modela el contenedor de compras en línea del cliente, asegurando la consistencia de existencias en cada adición o cambio de cantidad.

```mermaid
stateDiagram-v2
    [*] --> Carrito_Vacio: Inicio
    
    Carrito_Vacio --> Agregar_Prenda: [añadir prenda desde catálogo]
    
    Agregar_Prenda --> Validar_Stock_Disponible: [verificar existencias]
    Validar_Stock_Disponible --> Carrito_Vacio: [sin stock]
    Validar_Stock_Disponible --> Carrito_Con_Articulos: [stock suficiente]

    Carrito_Con_Articulos --> Modificar_Cantidad: [cambiar unidades]
    Modificar_Cantidad --> Validar_Stock_Disponible: [revalidar stock]

    Carrito_Con_Articulos --> Eliminar_Articulo: [quitar prenda]
    Eliminar_Articulo --> Carrito_Con_Articulos: [quedan prendas]
    Eliminar_Articulo --> Carrito_Vacio: [última prenda eliminada]

    Carrito_Con_Articulos --> Proceder_Checkout: [iniciar compra]
    Proceder_Checkout --> Transaccion_Completada: [continuar a CU14]
    Transaccion_Completada --> [*]: Fin
```

---

### CU14: Realizar Compra Digital (Checkout E-commerce)

Modela el flujo completo de compra por comercio electrónico: selección de tienda para retiro, aplicación de descuentos de temporada y pago electrónico.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Cliente: Inicio
    Loguear_Cliente --> Iniciar_Checkout: [correcto]

    Iniciar_Checkout --> Seleccionar_Sucursal_Retiro: [elegir tienda para retiro Click & Collect]
    Seleccionar_Sucursal_Retiro --> Aplicar_Promociones: [calcular descuentos vigentes]
    
    Aplicar_Promociones --> Generar_Orden_Venta: [crear orden PENDING]
    
    Generar_Orden_Venta --> Pasarela_Pago_Electronico: [derivar a Stripe o QR bancario]

    Pasarela_Pago_Electronico --> Pago_Rechazado: [fondos insuficientes o timeout]
    Pago_Rechazado --> Iniciar_Checkout: [reintentar con otro método]

    Pasarela_Pago_Electronico --> Pago_Aprobado: [webhook / confirmación exitosa]

    Pago_Aprobado --> Descontar_Inventario_Definitivo: [registrar movimiento SALE]
    Descontar_Inventario_Definitivo --> Vaciar_Carrito_Cliente: [orden PAID]
    Vaciar_Carrito_Cliente --> Transaccion_Completada: [emitir número de orden y ticket digital]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU15 / CU16: Venta Presencial y Cobro en Caja (POS)

Modela la venta física en el mostrador de una sucursal realizada por el cajero, con cobro en efectivo (cálculo de cambio), tarjeta o QR.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Cajero: Inicio
    Loguear_Cajero --> Loguear_Cajero: [error]
    Loguear_Cajero --> Apertura_Terminal_POS: [correcto / autoseleccionar sucursal]

    Apertura_Terminal_POS --> Seleccionar_Prenda_Tienda: [seleccionar prenda de inventario]
    Seleccionar_Prenda_Tienda --> Validar_Stock_Local: [verificar unidades disponibles]
    
    Validar_Stock_Local --> Seleccionar_Prenda_Tienda: [stock insuficiente]
    Validar_Stock_Local --> Calcular_Total_Venta: [stock suficiente / aplicar promociones]

    Calcular_Total_Venta --> Seleccionar_Metodo_Cobro: [elegir forma de pago]

    Seleccionar_Metodo_Cobro --> Cobro_Efectivo: [Efectivo]
    Cobro_Efectivo --> Calcular_Cambio: [monto entregado >= total]

    Seleccionar_Metodo_Cobro --> Cobro_Tarjeta_QR: [Tarjeta o QR]
    Cobro_Tarjeta_QR --> Validar_Referencia_POS: [ingresar número de operación]

    Calcular_Cambio --> Confirmar_Venta_Fisica: [cobro completado]
    Validar_Referencia_POS --> Confirmar_Venta_Fisica: [transacción aprobada]

    Confirmar_Venta_Fisica --> Descontar_Stock_Inmediato: [movimiento SALE en Kárdex]
    Descontar_Stock_Inmediato --> Transaccion_Completada: [emitir comprobante de venta]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU17: Procesar Pago Electrónico (Sandbox / QR / Stripe)

Modela la máquina de estados de una transacción de pago electrónico con protección contra cobros duplicados (idempotencia).

```mermaid
stateDiagram-v2
    [*] --> Iniciar_Pago: [recibir orden_id y método]
    Iniciar_Pago --> Validar_Idempotencia: [verificar clave única de pago]

    Validar_Idempotencia --> Rechazar_Duplicado: [pago ya procesado anteriormente]
    Rechazar_Duplicado --> [*]: Fin

    Validar_Idempotencia --> Crear_Registro_Pago: [clave nueva / estado PENDING]
    
    Crear_Registro_Pago --> Contactar_Pasarela: [enviar a Stripe / generar QR]
    
    Contactar_Pasarela --> Esperar_Confirmacion: [estado PROCESSING]
    
    Esperar_Confirmacion --> Pago_Fallido: [error bancario / expiración]
    Esperar_Confirmacion --> Pago_Exitoso: [firma webhook válida / estado APPROVED]

    Pago_Fallido --> Transaccion_Completada: [notificar rechazo]
    Pago_Exitoso --> Transaccion_Completada: [vincular a orden y marcar PAID]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU18: Gestionar Inventario y Movimientos (Kárdex)

Modela el control de existencias físicas en bodega y tienda, garantizando la trazabilidad de entradas, salidas y devoluciones.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Encargado: Inicio
    Loguear_Encargado --> Seleccionar_Sucursal_Inventario: [correcto]

    Seleccionar_Sucursal_Inventario --> Consultar_Stock_Local: [ver existencias actuales]
    
    Consultar_Stock_Local --> Seleccionar_Tipo_Movimiento: [registrar ajuste]

    Seleccionar_Tipo_Movimiento --> Entrada_Mercaderia: [tipo IN - recepción de taller/proveedor]
    Entrada_Mercaderia --> Incrementar_Stock_Fisico: [sumar unidades]

    Seleccionar_Tipo_Movimiento --> Salida_Mercaderia: [tipo OUT - merma o traslado]
    Salida_Mercaderia --> Validar_Stock_Suficiente: [verificar no dejar negativo]
    Validar_Stock_Suficiente --> Seleccionar_Tipo_Movimiento: [stock insuficiente]
    Validar_Stock_Suficiente --> Decrementar_Stock_Fisico: [restar unidades]

    Incrementar_Stock_Fisico --> Asentar_Kardex_Bitacora: [registrar movimiento inmutable]
    Decrementar_Stock_Fisico --> Asentar_Kardex_Bitacora: [registrar movimiento inmutable]

    Asentar_Kardex_Bitacora --> Transaccion_Completada: [inventario actualizado]
    Transaccion_Completada --> [*]: Fin
```

---

# Ciclo 3: Innovación, Analítica e Inteligencia Artificial

---

### CU12: Sesión de Probador Virtual (Fitting Room)

Modela la experiencia de realidad asistida para que el cliente previsualice cómo le queda una prenda en tiempo real con su cámara o en simulador.

```mermaid
stateDiagram-v2
    [*] --> Seleccionar_Prenda_Catalogo: Inicio
    Seleccionar_Prenda_Catalogo --> Iniciar_Sesion_Fitting: [abrir probador virtual]

    Iniciar_Sesion_Fitting --> Verificar_Camara_Dispositivo: [comprobar permisos de video]

    Verificar_Camara_Dispositivo --> Modo_Simulador_Fallback: [sin cámara o permiso denegado]
    Verificar_Camara_Dispositivo --> Activar_Detector_Poses: [cámara disponible]

    Activar_Detector_Poses --> Detectar_Landmarks_Torso: [procesar landmarks de hombros y cadera]
    Detectar_Landmarks_Torso --> Modo_Simulador_Fallback: [cuerpo no detectado en encuadre]
    Detectar_Landmarks_Torso --> Ajustar_Escala_Prenda: [torso detectado con precisión]

    Ajustar_Escala_Prenda --> Superponer_Prenda_En_Vivo: [renderizar prenda sobre el usuario]
    Modo_Simulador_Fallback --> Renderizar_Maniqui_3D: [mostrar prenda sobre silueta estándar]

    Superponer_Prenda_En_Vivo --> Finalizar_Sesion: [guardar captura o cerrar]
    Renderizar_Maniqui_3D --> Finalizar_Sesion: [cerrar simulador]

    Finalizar_Sesion --> Transaccion_Completada: [registrar sesión en base de datos]
    Transaccion_Completada --> [*]: Fin
```

---

### CU20: Gestionar Promociones y Descuentos

Modela la configuración y puesta en marcha de campañas de descuento (porcentaje o monto fijo) asociadas a colecciones y temporadas.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Administrador: Inicio
    Loguear_Administrador --> Seleccionar_Opcion_Promocion: [correcto]

    Seleccionar_Opcion_Promocion --> Desplegar_Lista_Promociones: [listar promociones]
    Desplegar_Lista_Promociones --> [*]: Fin

    Seleccionar_Opcion_Promocion --> Crear_Promocion: [crear nueva campaña]
    Crear_Promocion --> Definir_Tipo_Descuento: [porcentaje o importe fijo en Bs]
    Definir_Tipo_Descuento --> Asignar_Prendas_Elegibles: [vincular productos del catálogo]
    Asignar_Prendas_Elegibles --> Configurar_Vigencia: [establecer fecha inicio y fin]

    Seleccionar_Opcion_Promocion --> Modificar_Promocion: [modificar]
    Modificar_Promocion --> Configurar_Vigencia: [actualizar reglas]

    Seleccionar_Opcion_Promocion --> Conmutar_Estado_Campana: [activar / desactivar]

    Configurar_Vigencia --> Revisar_Datos_Promocion: [validar consistencia]
    Revisar_Datos_Promocion --> Transaccion_Completada: [promoción activa en catálogo]
    Conmutar_Estado_Campana --> Transaccion_Completada: [estado actualizado]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU21: Dashboards y Reportes Gerenciales con Sofía Copilot IA

Modela el análisis de datos de facturación, canales y stock, combinando consultas en lenguaje natural mediante IA y exportación ejecutiva a Excel/PDF.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Administrador: Inicio
    Loguear_Administrador --> Cargar_Dashboard_Consolidado: [correcto]

    Cargar_Dashboard_Consolidado --> Filtrar_Por_Sucursal_Fecha: [aplicar filtros analíticos]
    Filtrar_Por_Sucursal_Fecha --> Desplegar_Metricas_KPI: [ingresos, ticket medio, stock bajo]

    Desplegar_Metricas_KPI --> Formular_Pregunta_Sofia_IA: [ingresar consulta en lenguaje natural]
    
    Formular_Pregunta_Sofia_IA --> Clasificar_Intencion_Scoring: [analizar prompt con motor IA]
    Clasificar_Intencion_Scoring --> Generar_Narrativa_Estrategica: [generar resumen y recomendaciones]

    Generar_Narrativa_Estrategica --> Desplegar_Tarjetas_Ejecutivas: [visualizar hallazgos]

    Desplegar_Metricas_KPI --> Solicitar_Exportacion: [exportar informe formal]
    Desplegar_Tarjetas_Ejecutivas --> Solicitar_Exportacion: [exportar reporte enriquecido]

    Solicitar_Exportacion --> Generar_Archivo_Excel_PDF: [compilar libro Excel con fórmulas y cabeceras Navy]
    Generar_Archivo_Excel_PDF --> Transaccion_Completada: [descarga exitosa de archivo .xlsx / .pdf]
    
    Transaccion_Completada --> [*]: Fin
```

---

### CU22: Obtener Recomendaciones con IA

Modela el motor de recomendación inteligente que analiza el historial de compras del cliente, afinidad por categorías y disponibilidad en tiendas.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Cliente: Inicio
    Loguear_Cliente --> Solicitar_Recomendaciones: [abrir sección Para Ti o Catálogo]

    Solicitar_Recomendaciones --> Evaluar_Historial_Cliente: [analizar compras previas]

    Evaluar_Historial_Cliente --> Cold_Start_Populares: [cliente nuevo / sin compras]
    Evaluar_Historial_Cliente --> Scoring_Afinidad_Categorias: [cliente recurrente]

    Cold_Start_Populares --> Filtrar_Stock_Disponible: [seleccionar prendas top vendidas]
    Scoring_Afinidad_Categorias --> Filtrar_Stock_Disponible: [calcular ponderación según temporada y categoría]

    Filtrar_Stock_Disponible --> Excluir_Prendas_Agotadas: [garantizar que exista inventario > 0]
    Excluir_Prendas_Agotadas --> Generar_Explicacion_IA: [crear motivo: 'Basado en tu última compra...']

    Generar_Explicacion_IA --> Desplegar_Carrusel_Recomendados: [mostrar al cliente]
    Desplegar_Carrusel_Recomendados --> Transaccion_Completada: [cliente interactúa con prenda]
    Transaccion_Completada --> [*]: Fin
```

---

### CU23: Consultar Historial de Compras y Devoluciones

Modela la consulta de compras realizadas por el cliente y el proceso de devolución presencial en caja con reingreso automático al inventario.

```mermaid
stateDiagram-v2
    [*] --> Loguear_Cliente: Inicio
    Loguear_Cliente --> Consultar_Mis_Compras: [correcto]

    Consultar_Mis_Compras --> Desplegar_Lista_Ordenes: [cargar órdenes históricas]
    
    Desplegar_Lista_Ordenes --> Ver_Detalle_Compra: [seleccionar orden]
    Ver_Detalle_Compra --> Consultar_Estado_Envio_Pago: [revisar comprobante y prendas]

    Consultar_Estado_Envio_Pago --> Solicitar_Devolucion: [cliente asiste a tienda para devolución]
    
    Solicitar_Devolucion --> Validar_Venta_Completada: [cajero ingresa ID de orden en POS]
    Validar_Venta_Completada --> Solicitar_Devolucion: [orden no encontrada o ya devuelta]
    
    Validar_Venta_Completada --> Reingresar_Prendas_Kardex: [orden confirmada / registrar motivo]
    
    Reingresar_Prendas_Kardex --> Marcar_Orden_Returned: [sumar unidades a inventario local]
    Marcar_Orden_Returned --> Transaccion_Completada: [comprobante de devolución emitido]
    
    Transaccion_Completada --> [*]: Fin
```
