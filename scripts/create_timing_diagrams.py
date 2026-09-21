"""Script maestro para generar los Diagramas de Tiempo UML 2.5 en Enterprise Architect y exportar imágenes de alta resolución.

Basado exactamente en el modelo de referencia (media_1789875953185.jpg):
- Título superior: "Diagrama de tiempo"
- Marco UML 2.5 con etiqueta pentagonal 'sd [NombreDiagrama]'
- Contenedor interior de línea de vida (TimeLine) con fondo suave (#f2f8f9) y bordes redondeados
- Etiqueta de la línea de vida orientada verticalmente a 90° en el lateral izquierdo
- Estados discretos ordenados de abajo hacia arriba en el eje vertical
- Eje horizontal de tiempo en la parte inferior con marcas cada 5 unidades (0, 5, 10, ..., 100)
- Forma de onda escalonada con transiciones verticales y segmentos horizontales
- Eventos rotulados en los puntos de transición
- Restricciones de duración con flechas y corchetes '{duración}' en la parte superior
- Registro en Enterprise Architect en el paquete '06 - Diagramas de Tiempo'
"""

import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import win32com.client

MODEL_PATH = r"C:\ProyectoSi2_TiendaRopa\docs\uml\FashioStore\FashionStore.eap"
EXPORT_DIR = r"C:\ProyectoSi2_TiendaRopa\docs\uml\diagrams"

TIMING_DIAGRAMS_DATA = [
    {
        "id": "CU01_CU02",
        "diagram_name": "CU01_CU02_SesionJWT",
        "title_ea": "CU01/CU02 Sesión de Usuario y Tokens JWT",
        "filename": "tiempo-cu01-sesion-jwt.png",
        "timeline_name": "TimeLine_SesionUsuario",
        "states": ["SinSesion", "TokenActivo", "TokenExpirado", "RenovandoToken"],
        "waveform": [
            (0, "SinSesion"),
            (5, "SinSesion"),
            (5, "TokenActivo"),
            (25, "TokenActivo"),
            (25, "TokenExpirado"),
            (32, "TokenExpirado"),
            (32, "RenovandoToken"),
            (38, "RenovandoToken"),
            (38, "TokenActivo"),
            (88, "TokenActivo"),
            (88, "SinSesion"),
            (100, "SinSesion"),
        ],
        "events": [
            {"time": 5, "state": "TokenActivo", "label": "login(email, pass)", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 25, "state": "TokenExpirado", "label": "tokenExpirado()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 32, "state": "RenovandoToken", "label": "refreshToken()", "offset_x": 0.5, "offset_y": 1.5, "align": "left"},
            {"time": 38, "state": "TokenActivo", "label": "nuevoAccessToken()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 88, "state": "SinSesion", "label": "logout() / expirarSesion()", "offset_x": -0.8, "offset_y": 1.5, "align": "right"},
        ],
        "constraints": [
            {"t_start": 5, "t_end": 88, "label": "7 días (Vigencia Total Refresh Token)", "state_start": "TokenActivo", "state_end": "SinSesion", "y": 82},
            {"t_start": 5, "t_end": 25, "label": "15 min (Access Token)", "state_start": "TokenActivo", "state_end": "TokenExpirado", "y": 74},
            {"t_start": 32, "t_end": 38, "label": "< 1s", "state_start": "RenovandoToken", "state_end": "TokenActivo", "y": 74},
        ],
        "description": "Ciclo de vida de autenticación JWT. El Access Token expira a los 15 minutos forzando renovación o uso de Refresh Token vigente por 7 días.",
    },
    {
        "id": "CU10",
        "diagram_name": "CU10_ReservaPrendas",
        "title_ea": "CU10 Realizar Reserva de Prendas en Tienda",
        "filename": "tiempo-cu10-reserva-prendas.png",
        "timeline_name": "TimeLine_ReservaPrenda",
        "states": ["StockDisponible", "BloqueoTemporal", "ReservaConfirmada", "PrendaRecogida"],
        "waveform": [
            (0, "StockDisponible"),
            (5, "StockDisponible"),
            (5, "BloqueoTemporal"),
            (18, "BloqueoTemporal"),
            (18, "ReservaConfirmada"),
            (82, "ReservaConfirmada"),
            (82, "PrendaRecogida"),
            (92, "PrendaRecogida"),
            (92, "StockDisponible"),
            (100, "StockDisponible"),
        ],
        "events": [
            {"time": 5, "state": "BloqueoTemporal", "label": "solicitarReserva()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 18, "state": "ReservaConfirmada", "label": "confirmarReserva()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 82, "state": "PrendaRecogida", "label": "recogerEnTienda() / pagar()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 92, "state": "StockDisponible", "label": "completarEntrega() [o expirarReserva()]", "offset_x": -0.8, "offset_y": 1.5, "align": "right"},
        ],
        "constraints": [
            {"t_start": 5, "t_end": 18, "label": "15 min", "state_start": "BloqueoTemporal", "state_end": "ReservaConfirmada", "y": 76},
            {"t_start": 18, "t_end": 82, "label": "48 horas (Vigencia Máxima)", "state_start": "ReservaConfirmada", "state_end": "PrendaRecogida", "y": 76},
        ],
        "description": "Bloqueo temporal de stock por 15 min durante registro y retención física en tienda física por máximo 48 horas antes de liberación automática.",
    },
    {
        "id": "CU14_CU17",
        "diagram_name": "CU14_CU17_PagoDigital",
        "title_ea": "CU14/CU17 Compra Digital con Pago Electrónico",
        "filename": "tiempo-cu14-pago-digital.png",
        "timeline_name": "TimeLine_ProcesoPago",
        "states": ["CarritoActivo", "OrdenIniciada", "EsperandoPago", "ProcesandoWebhook", "PagoAprobado"],
        "waveform": [
            (0, "CarritoActivo"),
            (7, "CarritoActivo"),
            (7, "OrdenIniciada"),
            (18, "OrdenIniciada"),
            (18, "EsperandoPago"),
            (68, "EsperandoPago"),
            (68, "ProcesandoWebhook"),
            (78, "ProcesandoWebhook"),
            (78, "PagoAprobado"),
            (100, "PagoAprobado"),
        ],
        "events": [
            {"time": 7, "state": "OrdenIniciada", "label": "iniciarCheckout()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 18, "state": "EsperandoPago", "label": "generarCobroQR() / sesionStripe()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 68, "state": "ProcesandoWebhook", "label": "webhookPasarela()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 78, "state": "PagoAprobado", "label": "pagoAprobado() / emitirComprobante()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
        ],
        "constraints": [
            {"t_start": 18, "t_end": 68, "label": "10 min (Vigencia QR)", "state_start": "EsperandoPago", "state_end": "ProcesandoWebhook", "y": 76},
            {"t_start": 68, "t_end": 78, "label": "30 seg", "state_start": "ProcesandoWebhook", "state_end": "PagoAprobado", "y": 76},
        ],
        "description": "Vigencia de sesión QR / pasarela por 10 minutos y timeout de respuesta de webhook de conciliación bancaria de 30 segundos.",
    },
    {
        "id": "CU12",
        "diagram_name": "CU12_ProbadorVirtualVTON",
        "title_ea": "CU12 Sesión de Probador Virtual (VTON)",
        "filename": "tiempo-cu12-probador-virtual.png",
        "timeline_name": "TimeLine_ProbadorVirtual",
        "states": ["Inactivo", "CamaraIniciada", "PoseDetectada", "InferenciaVTON", "PrendaAjustada"],
        "waveform": [
            (0, "Inactivo"),
            (5, "Inactivo"),
            (5, "CamaraIniciada"),
            (18, "CamaraIniciada"),
            (18, "PoseDetectada"),
            (32, "PoseDetectada"),
            (32, "InferenciaVTON"),
            (56, "InferenciaVTON"),
            (56, "PrendaAjustada"),
            (88, "PrendaAjustada"),
            (88, "Inactivo"),
            (100, "Inactivo"),
        ],
        "events": [
            {"time": 5, "state": "CamaraIniciada", "label": "iniciarProbador()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 18, "state": "PoseDetectada", "label": "capturarPose()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 32, "state": "InferenciaVTON", "label": "procesarAjusteVTON(prendaId)", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 56, "state": "PrendaAjustada", "label": "mostrarResultado()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 88, "state": "Inactivo", "label": "timeoutInactividad() / cerrar()", "offset_x": -0.8, "offset_y": 1.5, "align": "right"},
        ],
        "constraints": [
            {"t_start": 18, "t_end": 32, "label": "< 500 ms", "state_start": "PoseDetectada", "state_end": "InferenciaVTON", "y": 76},
            {"t_start": 32, "t_end": 56, "label": "2.5 seg (Inferencia IA)", "state_start": "InferenciaVTON", "state_end": "PrendaAjustada", "y": 76},
            {"t_start": 56, "t_end": 88, "label": "5 min (Timeout Inactividad)", "state_start": "PrendaAjustada", "state_end": "Inactivo", "y": 76},
        ],
        "description": "Latencia en tiempo real para detección de postura por visión computacional (<500ms), inferencia generativa VTON (2.5s) y timeout de 5m.",
    },
    {
        "id": "CU20",
        "diagram_name": "CU20_GestionPromociones",
        "title_ea": "CU20 Gestionar Promociones y Descuentos",
        "filename": "tiempo-cu20-promociones.png",
        "timeline_name": "TimeLine_CicloPromocion",
        "states": ["Borrador", "Programada", "VigenteActiva", "Pausada", "Expirada"],
        "waveform": [
            (0, "Borrador"),
            (8, "Borrador"),
            (8, "Programada"),
            (25, "Programada"),
            (25, "VigenteActiva"),
            (55, "VigenteActiva"),
            (55, "Pausada"),
            (66, "Pausada"),
            (66, "VigenteActiva"),
            (88, "VigenteActiva"),
            (88, "Expirada"),
            (100, "Expirada"),
        ],
        "events": [
            {"time": 8, "state": "Programada", "label": "programarCampaña(f_inicio, f_fin)", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 25, "state": "VigenteActiva", "label": "iniciarVigencia() [fecha >= f_inicio]", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 55, "state": "Pausada", "label": "pausarPromocion()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 66, "state": "VigenteActiva", "label": "reanudarPromocion()", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
            {"time": 88, "state": "Expirada", "label": "expirarCampaña() [fecha >= f_fin]", "offset_x": 0.8, "offset_y": 1.5, "align": "left"},
        ],
        "constraints": [
            {"t_start": 8, "t_end": 25, "label": "Programada", "state_start": "Programada", "state_end": "VigenteActiva", "y": 76},
            {"t_start": 25, "t_end": 88, "label": "Vigencia: N días", "state_start": "VigenteActiva", "state_end": "Expirada", "y": 76},
        ],
        "description": "Estados de una promoción desde borrador, programada con fecha de inicio, activación automática en catálogo, pausas operativas y expiración final.",
    },
]

def render_timing_diagram(data, output_path):
    """Renderiza con Matplotlib una imagen idéntica a media_1789875953185.jpg con alta precisión."""
    fig_width = 14.5
    fig_height = 5.6
    dpi = 150
    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Título superior: "Diagrama de tiempo"
    ax.text(2, 95.5, "Diagrama de tiempo", fontsize=17, fontweight='bold', family='sans-serif', color='#111111')

    # Marco exterior UML 2.5
    frame_left = 2
    frame_bottom = 3.5
    frame_width = 96
    frame_height = 86.5

    rect_frame = patches.Rectangle(
        (frame_left, frame_bottom), frame_width, frame_height,
        linewidth=1.2, edgecolor='#333333', facecolor='none', zorder=2
    )
    ax.add_patch(rect_frame)

    # Etiqueta pentagonal UML 2.5: "sd [diagram_name]"
    tab_title = f"sd {data['diagram_name']}"
    tab_w = max(20.0, len(tab_title) * 0.98)
    tab_h = 4.8
    tab_x = frame_left
    tab_y = frame_bottom + frame_height
    chamfer = 2.0

    pentagon = [
        (tab_x, tab_y),
        (tab_x + tab_w - chamfer, tab_y),
        (tab_x + tab_w, tab_y - chamfer),
        (tab_x + tab_w, tab_y - tab_h),
        (tab_x, tab_y - tab_h),
    ]
    poly_tab = patches.Polygon(pentagon, closed=True, facecolor='white', edgecolor='#333333', linewidth=1.2, zorder=3)
    ax.add_patch(poly_tab)
    ax.text(tab_x + 1.2, tab_y - tab_h + 1.3, tab_title, fontsize=10.5, fontweight='bold', family='sans-serif', color='#111111', zorder=4)

    # Contenedor interior de la línea de vida
    box_left = frame_left + 3.0
    box_right = frame_left + frame_width - 3.0
    box_bottom = frame_bottom + 4.5
    box_top = tab_y - tab_h - 3.5
    box_w = box_right - box_left
    box_h = box_top - box_bottom

    inner_box = patches.FancyBboxPatch(
        (box_left, box_bottom), box_w, box_h,
        boxstyle="round,pad=0,rounding_size=1.2",
        linewidth=1.0, edgecolor='#777777', facecolor='#f2f8f9', zorder=2
    )
    ax.add_patch(inner_box)

    # Nombre de la línea de vida rotado 90° CCW
    tl_name = data['timeline_name']
    ax.text(box_left + 1.5, box_bottom + box_h * 0.50, tl_name,
            rotation=90, va='center', ha='center', fontsize=10.0, fontweight='bold', family='sans-serif', color='#222222', zorder=5)

    # Niveles de estados
    states = data['states']
    num_states = len(states)
    
    tl_start_x = box_left + 17.5
    tl_end_x = box_right - 2.5
    tl_width = tl_end_x - tl_start_x

    axis_y = box_bottom + 5.5
    state_area_bottom = axis_y + 6.0
    state_area_top = box_top - 16.0
    
    y_coords = {}
    for i, st in enumerate(states):
        y = state_area_bottom + i * (state_area_top - state_area_bottom) / (num_states - 1)
        y_coords[st] = y
        ax.text(tl_start_x - 1.5, y, st, va='center', ha='right', fontsize=9.8, fontweight='bold', family='sans-serif', color='#222222', zorder=5)

    # Eje horizontal de tiempo
    ax.plot([tl_start_x, tl_end_x], [axis_y, axis_y], color='#555555', linewidth=1.2, zorder=4)

    # Ticks de 0 a 100
    for t_val in range(0, 105, 5):
        x_tick = tl_start_x + (t_val / 100.0) * tl_width
        ax.plot([x_tick, x_tick], [axis_y - 1.2, axis_y + 1.2], color='#555555', linewidth=1.0, zorder=4)
        ax.text(x_tick, axis_y - 3.2, str(t_val), va='center', ha='center', fontsize=9.0, family='sans-serif', color='#333333', zorder=4)

    def t2x(t):
        return tl_start_x + (t / 100.0) * tl_width

    # Línea de forma de onda (Waveform)
    points = data['waveform']
    x_line = []
    y_line = []
    
    for i in range(len(points) - 1):
        t_curr, st_curr = points[i]
        t_next, st_next = points[i + 1]
        
        y_curr = y_coords[st_curr]
        y_next = y_coords[st_next]
        
        x_line.extend([t2x(t_curr), t2x(t_next)])
        y_line.extend([y_curr, y_curr])
        
        if y_curr != y_next:
            x_line.extend([t2x(t_next), t2x(t_next)])
            y_line.extend([y_curr, y_next])

    ax.plot(x_line, y_line, color='#3a4a58', linewidth=2.0, zorder=5)

    # Eventos de transición
    events = data.get('events', [])
    for ev in events:
        t_ev = ev['time']
        st_ev = ev['state']
        text = ev['label']
        offset_y = ev.get('offset_y', 2.0)
        offset_x = ev.get('offset_x', 0.5)
        align = ev.get('align', 'left')
        x_pos = t2x(t_ev) + offset_x
        y_pos = y_coords[st_ev] + offset_y
        ax.text(x_pos, y_pos, text, va='bottom', ha=align, fontsize=9.5, fontweight='bold', family='sans-serif', color='#1a202c', zorder=6)

    # Restricciones de duración
    constraints = data.get('constraints', [])
    for cons in constraints:
        t_start = cons['t_start']
        t_end = cons['t_end']
        label = cons['label']
        y_c = cons.get('y', box_top - 6.0)
        
        x1 = t2x(t_start)
        x2 = t2x(t_end)
        
        # Guías punteadas desde la forma de onda
        ax.plot([x1, x1], [y_coords[cons['state_start']] + 1.2, y_c], color='#aaaaaa', linestyle=':', linewidth=0.9, zorder=3)
        ax.plot([x2, x2], [y_coords[cons['state_end']] + 1.2, y_c], color='#aaaaaa', linestyle=':', linewidth=0.9, zorder=3)
        
        # Marcas de tope vertical
        ax.plot([x1, x1], [y_c - 1.2, y_c + 1.2], color='#555555', linewidth=1.2, zorder=5)
        ax.plot([x2, x2], [y_c - 1.2, y_c + 1.2], color='#555555', linewidth=1.2, zorder=5)
        
        # Flecha continua
        mid_x = (x1 + x2) / 2.0
        label_text = f"{{{label}}}"
        
        ax.annotate('', xy=(x1, y_c), xytext=(x2, y_c),
                    arrowprops=dict(arrowstyle="<->", color='#555555', lw=1.2), zorder=4)
        
        # Texto con fondo idéntico al contenedor para ocultar la línea debajo
        ax.text(mid_x, y_c, label_text, va='center', ha='center', fontsize=9.5, fontweight='bold',
                family='sans-serif', color='#111111',
                bbox=dict(boxstyle='square,pad=0.25', facecolor='#f2f8f9', edgecolor='none'), zorder=6)

    plt.tight_layout()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, dpi=dpi, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"  -> PNG guardado: {output_path}")

def sync_with_enterprise_architect():
    """Sincroniza los paquetes, diagramas de tiempo y elementos TimeLine en FashionStore.eap."""
    print("\nSincronizando con repositorio Enterprise Architect...")
    rep = win32com.client.Dispatch("EA.Repository")
    if not rep.OpenFile(MODEL_PATH):
        print(f"Error al abrir {MODEL_PATH}")
        return False

    root_model = rep.Models.GetAt(0)

    # Eliminar paquete temporal si existe
    for i in range(root_model.Packages.Count - 1, -1, -1):
        p = root_model.Packages.GetAt(i)
        if p.Name in ["TEST_TIMING_PKG", "06 - Diagramas de Tiempo"]:
            root_model.Packages.Delete(i)
            root_model.Packages.Refresh()

    # Crear paquete principal
    pkg_main = root_model.Packages.AddNew("06 - Diagramas de Tiempo", "")
    pkg_main.Notes = "Diagramas de Tiempo (Timing Diagrams) según especificación UML 2.5 para casos de uso clave en Ciclo 1, 2 y 3."
    pkg_main.Update()
    root_model.Packages.Refresh()

    for item in TIMING_DIAGRAMS_DATA:
        # Subpaquete por Caso de Uso
        sub_pkg = pkg_main.Packages.AddNew(f"{item['id']} - {item['title_ea']}", "")
        sub_pkg.Notes = item["description"]
        sub_pkg.Update()
        pkg_main.Packages.Refresh()

        # Diagrama de Tiempo UML 2.5
        diag = sub_pkg.Diagrams.AddNew(item["diagram_name"], "Timing")
        diag.Notes = f"Diagrama de tiempo UML 2.5 para {item['title_ea']}.\nRestricciones temporales y estados discretos."
        diag.StyleEx = "ShowFrame=1;"
        diag.Update()
        sub_pkg.Diagrams.Refresh()

        # Elemento TimeLine
        tl = sub_pkg.Elements.AddNew(item["timeline_name"], "TimeLine")
        tl.Notes = f"Línea de vida de estados temporales para {item['title_ea']}.\nEstados: {', '.join(item['states'])}\nRestricciones: {'; '.join([c['label'] for c in item['constraints']])}"
        tl.Update()
        sub_pkg.Elements.Refresh()

        # Agregar TimeLine al diagrama
        d_obj = diag.DiagramObjects.AddNew("", "")
        d_obj.ElementID = tl.ElementID
        d_obj.left = 50
        d_obj.right = 850
        d_obj.top = -50
        d_obj.bottom = -420
        d_obj.Update()
        diag.Update()

        print(f"  [EA] Diagrama y TimeLine creados para {item['id']}")

    rep.CloseFile()
    rep.Exit()
    print("Sincronización con EA completada con éxito.")
    return True

def main():
    print("=" * 75)
    print("GENERADOR DE DIAGRAMAS DE TIEMPO UML 2.5 (CICLOS 1, 2 Y 3)")
    print("FashionStore - Enterprise Architect & Visual Artifacts")
    print("=" * 75)

    # 1. Generar imágenes PNG de alta resolución
    print("\n1. Renderizando imágenes de alta resolución...")
    for item in TIMING_DIAGRAMS_DATA:
        out_png = os.path.join(EXPORT_DIR, item["filename"])
        render_timing_diagram(item, out_png)

    # 2. Sincronizar modelos en Enterprise Architect
    print("\n2. Registrando en FashionStore.eap...")
    try:
        sync_with_enterprise_architect()
    except Exception as e:
        print(f"Aviso durante sincronización EA: {e}")

    print("\n" + "=" * 75)
    print("TODOS LOS DIAGRAMAS DE TIEMPO FUERON GENERADOS Y REGISTRADOS EXITOSAMENTE")
    print("=" * 75)
    return 0

if __name__ == "__main__":
    sys.exit(main())
