const { chromium } = require('../web/node_modules/@playwright/test');
const fs = require('fs');
const path = require('path');

const outputDir = path.resolve(__dirname, '../docs/ui-screens/etapa-1');
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

// Read actual project styles.css
const projectCss = fs.readFileSync(path.resolve(__dirname, '../web/src/styles.css'), 'utf8');

// Common Web Frame Template using real FashionStore styling
function renderWebPage(cuTitle, cuCode, innerHtml, activeNav = 'saas', tenantLabel = 'Plataforma SaaS Central') {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>${cuTitle}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
  <style>
    ${projectCss}

    /* Presentation Canvas Wrapper */
    body.showcase-body {
      background: #eae5dc;
      padding: 30px;
      margin: 0;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: 'Plus Jakarta Sans', Arial, sans-serif;
    }
    .window-container {
      width: 1240px;
      background: var(--paper, #fbf9f6);
      border-radius: 14px;
      overflow: hidden;
      box-shadow: 0 25px 60px rgba(27, 28, 26, 0.18), 0 0 0 1px rgba(229, 224, 216, 0.9);
      display: flex;
      flex-direction: column;
    }
    .browser-toolbar {
      background: #f0ede6;
      border-bottom: 1px solid var(--line, #e5e0d8);
      padding: 10px 18px;
      display: flex;
      align-items: center;
      gap: 16px;
    }
    .window-dots {
      display: flex;
      gap: 7px;
    }
    .w-dot { width: 11px; height: 11px; border-radius: 50%; display: inline-block; }
    .w-red { background: #e06c75; }
    .w-yellow { background: #e5c07b; }
    .w-green { background: #98c379; }
    .browser-address {
      flex: 1;
      background: #ffffff;
      border: 1px solid var(--line, #e5e0d8);
      border-radius: 6px;
      padding: 5px 12px;
      font-size: 0.72rem;
      color: var(--muted, #756f68);
      display: flex;
      align-items: center;
      gap: 8px;
      font-family: 'JetBrains Mono', monospace;
    }
    .cu-pill-header {
      background: var(--ink, #1b1c1a);
      color: #f7e7ce;
      font-size: 0.68rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 5px 14px;
      border-radius: 20px;
      display: flex;
      align-items: center;
      gap: 6px;
      border: 1px solid rgba(184, 146, 74, 0.4);
    }
    .showcase-content {
      background: var(--paper, #fbf9f6);
      padding: 0 40px 48px;
      min-height: 600px;
    }
  </style>
</head>
<body class="showcase-body">
  <div class="window-container">
    <!-- Browser Top Bar -->
    <div class="browser-toolbar">
      <div class="window-dots">
        <span class="w-dot w-red"></span>
        <span class="w-dot w-yellow"></span>
        <span class="w-dot w-green"></span>
      </div>
      <div class="browser-address">
        <span class="material-symbols-outlined" style="font-size:14px; color:#8f6d2d;">lock</span>
        <span>http://localhost:4200/admin/${activeNav}</span>
      </div>
      <div class="cu-pill-header">
        <span class="material-symbols-outlined" style="font-size:15px; color:#b8924a;">verified</span>
        ${cuCode} · ${cuTitle}
      </div>
    </div>

    <!-- FashionStore Real Site Header -->
    <header class="site-header" style="position:relative; background:rgba(251, 249, 246, 0.98); border-bottom:1px solid var(--line); padding:0 40px;">
      <div class="header-container" style="display:flex; justify-content:space-between; align-items:center; height:72px;">
        <div style="display:flex; align-items:center; gap:20px;">
          <a class="brand" style="display:flex; align-items:center; gap:10px;">
            <span class="brand-monogram">FS</span>
            <div class="brand-text">
              <span class="brand-name">FashionStore</span>
              <span class="brand-tagline">ATELIER · BOUTIQUE</span>
            </div>
          </a>
          <span style="background:var(--panel); border:1px solid var(--line); padding:5px 12px; border-radius:14px; font-size:0.65rem; font-weight:600; color:var(--muted); letter-spacing:0.08em; text-transform:uppercase; display:flex; align-items:center; gap:6px;">
            <span class="material-symbols-outlined" style="font-size:15px; color:var(--accent);">business</span>
            ${tenantLabel}
          </span>
        </div>
        <div style="display:flex; align-items:center; gap:14px;">
          <span class="online-pill" style="font-size:0.7rem; padding:4px 10px;">
            <span class="material-symbols-outlined" style="font-size:14px;">wifi</span>
            En línea
          </span>
          <div style="display:flex; align-items:center; gap:8px; border-left:1px solid var(--line); padding-left:14px;">
            <span class="user-avatar" style="width:32px; height:32px; border-radius:50%; background:var(--panel); border:1px solid var(--line); display:flex; align-items:center; justify-content:center; font-size:0.72rem; font-weight:700;">SA</span>
            <small style="font-size:0.68rem; font-weight:600; color:var(--ink); letter-spacing:0.05em; text-transform:uppercase;">Superadmin SaaS</small>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content Area -->
    <div class="showcase-content">
      ${innerHtml}
    </div>
  </div>
</body>
</html>`;
}

// Common Mobile Frame Template using FashionStore Mobile Palette
function renderMobilePage(cuTitle, cuCode, innerHtml) {
  return `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <title>${cuTitle}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,600&family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: #eae5dc;
      padding: 30px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      font-family: 'Plus Jakarta Sans', Arial, sans-serif;
      color: #25211d;
    }
    .mobile-header-tag {
      background: #25211d;
      color: #fbf7ef;
      font-size: 0.72rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      padding: 6px 18px;
      border-radius: 20px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
      box-shadow: 0 4px 14px rgba(37,33,29,0.15);
      border: 1px solid rgba(184, 146, 74, 0.4);
    }
    .phone-mockup {
      width: 412px;
      height: 840px;
      background: #ffffff;
      border-radius: 46px;
      padding: 12px;
      box-shadow: 0 30px 80px rgba(37,33,29,0.22), 0 0 0 4px #d8d0c5, 0 0 0 6px #ffffff;
      position: relative;
    }
    .phone-inner {
      width: 100%;
      height: 100%;
      background: #fbf7ef; /* AppColors.ivory */
      border-radius: 36px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      position: relative;
    }
    .phone-status-bar {
      padding: 12px 24px 6px;
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      font-weight: 600;
      color: #6f675d;
    }
    .phone-app-bar {
      padding: 10px 18px;
      background: #fbf7ef;
      border-bottom: 1px solid #e5e0d8;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .phone-app-title {
      font-family: 'Playfair Display', serif;
      font-size: 1.15rem;
      font-weight: 700;
      color: #25211d;
      letter-spacing: -0.01em;
    }
    .phone-app-title span { color: #8f6d2d; font-style: italic; }
    .phone-content {
      flex: 1;
      padding: 18px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .phone-bottom-nav {
      height: 64px;
      background: #fffcf6; /* AppColors.parchment */
      border-top: 1px solid #e5e0d8;
      display: flex;
      align-items: center;
      justify-content: space-around;
      padding: 0 10px;
    }
    .p-nav-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
      color: #6f675d;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .p-nav-item.active { color: #8f6d2d; }
  </style>
</head>
<body>
  <div class="mobile-header-tag">
    <span class="material-symbols-outlined" style="font-size:16px; color:#b8924a;">smartphone</span>
    ${cuCode} · ${cuTitle}
  </div>
  <div class="phone-mockup">
    <div class="phone-inner">
      <div class="phone-status-bar">
        <span>09:41</span>
        <div style="display:flex; gap:6px; align-items:center;">
          <span class="material-symbols-outlined" style="font-size:14px;">signal_cellular_alt</span>
          <span class="material-symbols-outlined" style="font-size:14px;">wifi</span>
          <span class="material-symbols-outlined" style="font-size:16px;">battery_full</span>
        </div>
      </div>
      ${innerHtml}
    </div>
  </div>
</body>
</html>`;
}

async function run() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1440, height: 1020 } });

  console.log('✨ Renderizando las 10 interfaces de la Etapa 1 con el estilo real de FashionStore...');

  // -------------------------------------------------------------------------
  // CU-01: Registrar Empresa Contratante (Tenant) - Web Admin Layout
  // -------------------------------------------------------------------------
  const htmlCU01 = renderWebPage(
    'Registrar Empresa Contratante (Tenant)',
    'CU-01',
    `
    <div class="admin-layout" style="padding-top:36px;">
      <aside class="admin-sidebar">
        <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Plataforma SaaS</p>
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; line-height:0.95; margin:14px 0 36px; font-weight:400;">
          Gestión<br><em>empresas.</em>
        </h1>
        <nav class="admin-nav">
          <button class="current">Empresas SaaS</button>
          <button>Planes Suscripción</button>
          <button>Control de Cuotas</button>
          <button>Auditoría Global</button>
        </nav>
      </aside>

      <section class="admin-content">
        <div class="admin-heading">
          <div>
            <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Backoffice SaaS</p>
            <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Alta de Nueva Empresa</h2>
            <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Crea un nuevo tenant con aislamiento lógico, subdominio y administrador inicial.</p>
          </div>
        </div>

        <div class="admin-panel" style="background:var(--panel); border:1px solid var(--line); border-radius:12px; padding:32px;">
          <h3 style="font-family:'Playfair Display', serif; font-size:1.4rem; margin:0 0 20px;">Ficha de Registro Corporativo</h3>
          
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px; margin-bottom:24px;">
            <label>
              Nombre Comercial de la Empresa
              <input type="text" value="Boutique Aurora S.R.L.">
            </label>
            <label>
              Subdominio / Slug de Aislamiento (tenant_id)
              <input type="text" value="boutique-aurora" style="font-family:'JetBrains Mono', monospace; font-weight:600; color:#8f6d2d;">
            </label>
            <label>
              Identificación Fiscal (NIT / RUC)
              <input type="text" value="3049281014">
            </label>
            <label>
              Plan de Suscripción Inicial
              <select style="font-weight:600;">
                <option selected>Plan Básico (Hasta 2 sucursales activas)</option>
                <option>Plan Profesional (Hasta 10 sucursales activas · Sofía IA)</option>
              </select>
            </label>
          </div>

          <div style="border-top:1px solid var(--line); padding-top:22px; margin-bottom:24px;">
            <p class="eyebrow" style="color:var(--accent); font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:14px;">Administrador Inicial de Empresa</p>
            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
              <label>
                Nombre del Responsable
                <input type="text" value="Valeria Aurora">
              </label>
              <label>
                Correo Electrónico Corporativo
                <input type="email" value="admin@boutiqueaurora.com">
              </label>
            </div>
          </div>

          <div style="display:flex; justify-content:flex-end; gap:12px;">
            <button class="button button-light">Cancelar</button>
            <button class="button button-dark"><span class="material-symbols-outlined" style="font-size:18px;">save</span> Guardar y Crear Tenant</button>
          </div>
        </div>
      </section>
    </div>
    `,
    'saas',
    'Superadmin SaaS'
  );
  await page.setContent(htmlCU01);
  await page.screenshot({ path: path.join(outputDir, 'CU-01_Registrar_Empresa_SaaS.png') });
  console.log('✅ CU-01_Registrar_Empresa_SaaS.png');

  // -------------------------------------------------------------------------
  // CU-02: Gestionar Planes de Suscripción - Web
  // -------------------------------------------------------------------------
  const htmlCU02 = renderWebPage(
    'Gestionar Planes de Suscripción',
    'CU-02',
    `
    <div class="admin-layout" style="padding-top:36px;">
      <aside class="admin-sidebar">
        <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Plataforma SaaS</p>
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; line-height:0.95; margin:14px 0 36px; font-weight:400;">
          Planes &<br><em>límites.</em>
        </h1>
        <nav class="admin-nav">
          <button>Empresas SaaS</button>
          <button class="current">Planes Suscripción</button>
          <button>Control de Cuotas</button>
          <button>Auditoría Global</button>
        </nav>
      </aside>

      <section class="admin-content">
        <div class="admin-heading">
          <div>
            <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Configuración del Servicio</p>
            <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Planes de Suscripción Activos</h2>
            <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Define cuotas de sucursales y características habilitadas para los tenants.</p>
          </div>
          <button class="button button-dark"><span class="material-symbols-outlined" style="font-size:18px;">add</span> Nuevo Plan</button>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px;">
          <!-- Plan Básico -->
          <div class="admin-panel" style="background:#ffffff; border:1px solid var(--line); border-radius:12px; padding:28px; position:relative;">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <span class="tag" style="background:var(--panel); color:var(--muted); margin-bottom:8px; display:inline-block;">CÓDIGO: BASIC</span>
                <h3 style="font-family:'Playfair Display', serif; font-size:1.8rem; margin:6px 0 4px; color:var(--ink);">Básico</h3>
                <p style="color:var(--muted); font-size:0.8rem;">Orientado a boutiques individuales y marcas emergentes.</p>
              </div>
            </div>

            <div style="margin:24px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:18px 0; display:flex; flex-direction:column; gap:12px; font-size:0.82rem;">
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Sucursales Activas:</span>
                <strong style="color:var(--ink);">Hasta 2 sucursales</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Operación Offline (PWA & SQLite):</span>
                <strong style="color:var(--green);">✓ Habilitado</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Reportes Convencionales:</span>
                <strong style="color:var(--green);">✓ Habilitado</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Reportes Generativos con IA:</span>
                <strong style="color:var(--accent);">✕ Deshabilitado</strong>
              </div>
            </div>

            <button class="button button-light" style="width:100%;"><span class="material-symbols-outlined" style="font-size:16px;">edit</span> Modificar Condiciones</button>
          </div>

          <!-- Plan Profesional -->
          <div class="admin-panel" style="background:#ffffff; border:2px solid #8f6d2d; border-radius:12px; padding:28px; position:relative; box-shadow:0 10px 30px rgba(143,109,45,0.08);">
            <div style="position:absolute; top:-12px; right:20px; background:#8f6d2d; color:#ffffff; font-size:0.62rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; padding:3px 12px; border-radius:12px;">PLAN RECOMENDADO</div>
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
              <div>
                <span class="tag" style="background:#f4efe6; color:#8f6d2d; margin-bottom:8px; display:inline-block;">CÓDIGO: PROFESSIONAL</span>
                <h3 style="font-family:'Playfair Display', serif; font-size:1.8rem; margin:6px 0 4px; color:var(--ink);">Profesional</h3>
                <p style="color:var(--muted); font-size:0.8rem;">Cadenas multitienda con analítica avanzada de IA.</p>
              </div>
            </div>

            <div style="margin:24px 0; border-top:1px solid var(--line); border-bottom:1px solid var(--line); padding:18px 0; display:flex; flex-direction:column; gap:12px; font-size:0.82rem;">
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Sucursales Activas:</span>
                <strong style="color:var(--ink);">Hasta 10 sucursales</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Operación Offline (PWA & SQLite):</span>
                <strong style="color:var(--green);">✓ Habilitado</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Reportes Convencionales:</span>
                <strong style="color:var(--green);">✓ Habilitado</strong>
              </div>
              <div style="display:flex; justify-content:space-between;">
                <span style="color:var(--muted);">Reportes Generativos con IA:</span>
                <strong style="color:#8f6d2d;">✓ Sofía IA + Machine Learning</strong>
              </div>
            </div>

            <button class="button button-dark" style="width:100%;"><span class="material-symbols-outlined" style="font-size:16px;">edit</span> Modificar Condiciones</button>
          </div>
        </div>
      </section>
    </div>
    `,
    'plans',
    'Superadmin SaaS'
  );
  await page.setContent(htmlCU02);
  await page.screenshot({ path: path.join(outputDir, 'CU-02_Gestionar_Planes_Suscripcion.png') });
  console.log('✅ CU-02_Gestionar_Planes_Suscripcion.png');

  // -------------------------------------------------------------------------
  // CU-03: Asignar y Renovar Suscripción de Empresa - Web
  // -------------------------------------------------------------------------
  const htmlCU03 = renderWebPage(
    'Asignar y Renovar Suscripción de Empresa',
    'CU-03',
    `
    <div class="admin-layout" style="padding-top:36px;">
      <aside class="admin-sidebar">
        <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Empresa</p>
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; line-height:0.95; margin:14px 0 36px; font-weight:400;">
          Plan &<br><em>estado.</em>
        </h1>
        <nav class="admin-nav">
          <button class="current">Suscripción Activa</button>
          <button>Sucursales (2)</button>
          <button>Personal & Roles</button>
          <button>Catálogo</button>
        </nav>
      </aside>

      <section class="admin-content">
        <div class="admin-heading">
          <div>
            <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Gestión Comercial</p>
            <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Suscripción: Boutique Aurora</h2>
            <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Consulta de estado, vigencia y simulación de renovación o cambio de plan.</p>
          </div>
          <button class="button button-dark"><span class="material-symbols-outlined" style="font-size:18px;">upgrade</span> Cambiar de Plan</button>
        </div>

        <div style="display:grid; grid-template-columns: 2fr 1fr; gap:24px;">
          <div class="admin-panel" style="background:#ffffff; border:1px solid var(--line); border-radius:12px; padding:28px;">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--line); padding-bottom:18px;">
              <div>
                <h3 style="font-family:'Playfair Display', serif; font-size:1.5rem; margin:0; color:var(--ink);">Boutique Aurora S.R.L.</h3>
                <small style="color:var(--muted); font-family:'JetBrains Mono', monospace;">tenant_id: 1 · boutique-aurora</small>
              </div>
              <span class="online-pill" style="font-size:0.75rem; padding:6px 14px;">
                ● SUSCRIPCIÓN ACTIVA
              </span>
            </div>

            <div style="display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin:24px 0;">
              <div style="background:var(--panel); padding:16px; border-radius:8px;">
                <small style="color:var(--muted); font-size:0.65rem; letter-spacing:0.08em; text-transform:uppercase; font-weight:700;">PLAN ASIGNADO</small>
                <div style="font-family:'Playfair Display', serif; font-size:1.4rem; color:var(--ink); margin-top:4px;">Plan Básico</div>
                <small style="color:#8f6d2d;">Límite: 2 sucursales activas</small>
              </div>
              <div style="background:var(--panel); padding:16px; border-radius:8px;">
                <small style="color:var(--muted); font-size:0.65rem; letter-spacing:0.08em; text-transform:uppercase; font-weight:700;">PERIODO DE VIGENCIA</small>
                <div style="font-family:'Playfair Display', serif; font-size:1.15rem; color:var(--ink); margin-top:4px;">25/10/2026 — 25/11/2026</div>
                <small style="color:var(--green);">Renovación administrativa simulada</small>
              </div>
            </div>

            <div style="background:var(--panel); padding:16px; border-radius:8px;">
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; margin-bottom:8px;">
                <span style="color:var(--muted);">Consumo de sucursales autorizadas:</span>
                <strong style="color:var(--ink);">2 de 2 sucursales (100% de la cuota)</strong>
              </div>
              <div style="width:100%; height:8px; background:var(--line); border-radius:4px; overflow:hidden;">
                <div style="width:100%; height:100%; background:#8f6d2d;"></div>
              </div>
            </div>
          </div>

          <div class="admin-panel" style="background:#ffffff; border:1px solid var(--line); border-radius:12px; padding:24px; display:flex; flex-direction:column; justify-content:space-between;">
            <div>
              <p class="eyebrow" style="color:var(--accent); font-size:0.65rem; letter-spacing:0.1em; text-transform:uppercase; margin-bottom:10px;">Acciones de Suscripción</p>
              <h4 style="font-family:'Playfair Display', serif; font-size:1.2rem; margin-bottom:10px;">Renovación Académica</h4>
              <p style="color:var(--muted); font-size:0.78rem; line-height:1.5;">Conforme a la sección 9.5 del examen, se simula administrativamente la contratación y renovación de planes.</p>
            </div>
            <div style="display:flex; flex-direction:column; gap:10px; margin-top:20px;">
              <button class="button button-dark" style="width:100%;"><span class="material-symbols-outlined" style="font-size:16px;">autorenew</span> Renovar por 30 Días</button>
              <button class="button button-light" style="width:100%; color:var(--accent);"><span class="material-symbols-outlined" style="font-size:16px;">pause_circle</span> Pausar Suscripción</button>
            </div>
          </div>
        </div>
      </section>
    </div>
    `,
    'subscription',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU03);
  await page.screenshot({ path: path.join(outputDir, 'CU-03_Asignar_Renovar_Suscripcion.png') });
  console.log('✅ CU-03_Asignar_Renovar_Suscripcion.png');

  // -------------------------------------------------------------------------
  // CU-04: Controlar Límites y Restricciones por Plan - Web
  // -------------------------------------------------------------------------
  const htmlCU04 = renderWebPage(
    'Controlar Límites y Restricciones por Plan',
    'CU-04',
    `
    <div class="admin-layout" style="padding-top:36px;">
      <aside class="admin-sidebar">
        <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Estructura</p>
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; line-height:0.95; margin:14px 0 36px; font-weight:400;">
          Sucursales &<br><em>cuotas.</em>
        </h1>
        <nav class="admin-nav">
          <button>Resumen</button>
          <button class="current">Ciudades y sucursales</button>
          <button>Catálogo base</button>
        </nav>
      </aside>

      <section class="admin-content">
        <!-- Banner de Error / Alerta Estilo FashionStore (admin-alert) -->
        <div class="admin-alert" style="background:#f4dfdb; border:1px solid #e8c0b8; border-radius:10px; padding:18px 24px; margin-bottom:28px; display:flex; align-items:center; justify-content:space-between;">
          <div style="display:flex; align-items:center; gap:16px;">
            <span class="material-symbols-outlined" style="font-size:32px; color:var(--accent);">error_outline</span>
            <div>
              <strong style="color:var(--accent); font-size:0.9rem; text-transform:uppercase; letter-spacing:0.05em;">Límite de Sucursales Alcanzado (Cuota de Plan)</strong>
              <p style="color:var(--ink); font-size:0.82rem; margin-top:2px;">
                La empresa <strong>Boutique Aurora</strong> opera bajo el <strong>Plan Básico</strong> con un límite máximo de <strong>2 sucursales activas</strong>. Ya tiene 2 sucursales registradas.
              </p>
            </div>
          </div>
          <button class="button button-dark" style="white-space:nowrap; background:#8f6d2d;"><span class="material-symbols-outlined" style="font-size:16px;">upgrade</span> Actualizar a Profesional</button>
        </div>

        <div class="admin-heading">
          <div>
            <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Boutique Aurora</p>
            <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Ciudades y sucursales</h2>
            <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Puntos de venta físicos autorizados en el tenant.</p>
          </div>
          <!-- Botón deshabilitado por cuota -->
          <button class="button button-dark" disabled style="opacity:0.4; cursor:not-allowed;" title="Límite alcanzado">
            <span class="material-symbols-outlined" style="font-size:18px;">add_business</span> + Nueva Sucursal (Límite 2/2)
          </button>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:20px;">
          <article class="branch-card" style="background:#ffffff; border:1px solid var(--line); border-radius:10px; padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <strong style="font-size:1.1rem; color:var(--ink);">Aurora Equipetrol</strong>
              <span class="status-pill active" style="background:#e3ebd3; color:#2e6f40; font-size:0.62rem; font-weight:700; padding:4px 8px; border-radius:12px;">ACTIVA</span>
            </div>
            <p style="color:var(--muted); font-size:0.8rem; margin:0 0 8px;">Santa Cruz · Av. San Martín 450</p>
            <small style="color:var(--muted);">Tel: 71001001</small>
          </article>

          <article class="branch-card" style="background:#ffffff; border:1px solid var(--line); border-radius:10px; padding:20px;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
              <strong style="font-size:1.1rem; color:var(--ink);">Aurora Prado</strong>
              <span class="status-pill active" style="background:#e3ebd3; color:#2e6f40; font-size:0.62rem; font-weight:700; padding:4px 8px; border-radius:12px;">ACTIVA</span>
            </div>
            <p style="color:var(--muted); font-size:0.8rem; margin:0 0 8px;">Cochabamba · Av. Ballivián 210</p>
            <small style="color:var(--muted);">Tel: 71001002</small>
          </article>
        </div>
      </section>
    </div>
    `,
    'locations',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU04);
  await page.screenshot({ path: path.join(outputDir, 'CU-04_Control_Limites_Restricciones_Plan.png') });
  console.log('✅ CU-04_Control_Limites_Restricciones_Plan.png');

  // -------------------------------------------------------------------------
  // CU-05: Gestionar Sucursales y Empleados por Tenant - Web
  // -------------------------------------------------------------------------
  const htmlCU05 = renderWebPage(
    'Gestionar Sucursales y Empleados por Tenant',
    'CU-05',
    `
    <div class="admin-layout" style="padding-top:36px;">
      <aside class="admin-sidebar">
        <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Estructura</p>
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; line-height:0.95; margin:14px 0 36px; font-weight:400;">
          Equipo &<br><em>sucursales.</em>
        </h1>
        <nav class="admin-nav">
          <button>Resumen</button>
          <button class="current">Usuarios y personal</button>
          <button>Ciudades y sucursales</button>
        </nav>
      </aside>

      <section class="admin-content">
        <div class="admin-heading">
          <div>
            <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Tenant: Boutique Aurora</p>
            <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Personal Operativo por Sucursal</h2>
            <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Asignación estricta de encargados y cajeros a sus tiendas físicas correspondientes.</p>
          </div>
          <button class="button button-dark"><span class="material-symbols-outlined" style="font-size:18px;">person_add</span> + Nuevo Empleado</button>
        </div>

        <div class="table-wrap" style="background:#ffffff; border:1px solid var(--line); border-radius:12px; padding:18px;">
          <table>
            <thead>
              <tr>
                <th>Empleado</th>
                <th>Correo Corporativo</th>
                <th>Rol Asignado</th>
                <th>Sucursal Autorizada</th>
                <th>Estado</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Diego Aurora</strong><small style="color:var(--muted); display:block;">ID #2</small></td>
                <td>encargado@boutiqueaurora.com</td>
                <td><span class="tag" style="background:#f0ede6; color:var(--ink);">Encargado Sucursal</span></td>
                <td><strong>Aurora Equipetrol (Santa Cruz)</strong></td>
                <td><span class="status-pill active" style="background:#e3ebd3; color:#2e6f40; padding:3px 8px; border-radius:10px; font-size:0.65rem; font-weight:700;">ACTIVO</span></td>
                <td><button class="small-button">Reasignar</button></td>
              </tr>
              <tr>
                <td><strong>Carlos Vendedor</strong><small style="color:var(--muted); display:block;">ID #5</small></td>
                <td>cajero@boutiqueaurora.com</td>
                <td><span class="tag" style="background:#f0ede6; color:var(--ink);">Cajero</span></td>
                <td><strong>Aurora Prado (Cochabamba)</strong></td>
                <td><span class="status-pill active" style="background:#e3ebd3; color:#2e6f40; padding:3px 8px; border-radius:10px; font-size:0.65rem; font-weight:700;">ACTIVO</span></td>
                <td><button class="small-button">Reasignar</button></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
    `,
    'users',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU05);
  await page.screenshot({ path: path.join(outputDir, 'CU-05_Gestionar_Sucursales_Empleados_Tenant.png') });
  console.log('✅ CU-05_Gestionar_Sucursales_Empleados_Tenant.png');

  // -------------------------------------------------------------------------
  // CU-06: Descargar y Almacenar Catálogo Offline - Móvil Flutter
  // -------------------------------------------------------------------------
  const htmlCU06 = renderMobilePage(
    'Descargar y Almacenar Catálogo Offline',
    'CU-06',
    `
    <div class="phone-app-bar">
      <div class="phone-app-title">Fashion<span>Store</span></div>
      <span class="material-symbols-outlined" style="font-size:20px; color:#25211d;">cloud_download</span>
    </div>
    <div class="phone-content">
      <div style="background:#fffcf6; border:1px solid #e5e0d8; border-radius:18px; padding:22px; text-align:center; box-shadow:0 6px 16px rgba(37,33,29,0.05);">
        <div style="width:56px; height:56px; background:#f0e8db; border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 12px;">
          <span class="material-symbols-outlined" style="font-size:28px; color:#8f6d2d;">sync</span>
        </div>
        <h3 style="font-family:'Playfair Display', serif; font-size:1.25rem; font-weight:700; color:#25211d; margin-bottom:6px;">Catálogo Local SQLite</h3>
        <p style="font-size:0.75rem; color:#6f675d; line-height:1.5; margin-bottom:18px;">
          Descarga productos, precios y existencias autorizadas de tu sucursal para continuar atendiendo sin internet.
        </p>

        <button style="width:100%; padding:14px; background:#25211d; color:#ffffff; border:0; border-radius:10px; font-size:0.75rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; display:flex; align-items:center; justify-content:center; gap:8px;">
          <span class="material-symbols-outlined" style="font-size:18px;">download</span> Descargar Catálogo
        </button>
      </div>

      <div style="background:#fffcf6; border:1px solid #e5e0d8; border-radius:18px; padding:18px;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:14px;">
          <span style="font-size:0.7rem; font-weight:700; color:#8f6d2d; letter-spacing:0.08em; text-transform:uppercase;">ESTADO DEL ALMACÉN SQLITE</span>
          <span style="background:#e3ebd3; color:#2e6f40; font-size:0.62rem; font-weight:700; padding:3px 8px; border-radius:10px;">SINCRONIZADO</span>
        </div>
        <div style="display:flex; flex-direction:column; gap:10px; font-size:0.78rem; color:#25211d;">
          <div style="display:flex; justify-content:space-between;">
            <span style="color:#6f675d;">Sucursal activa:</span><strong>Aurora Equipetrol</strong>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:#6f675d;">Prendas guardadas:</span><strong>18 artículos</strong>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:#6f675d;">Variantes y stock:</span><strong>42 combinaciones</strong>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span style="color:#6f675d;">Última actualización:</span><span style="font-family:'JetBrains Mono', monospace; font-size:0.72rem;">25/10/2026 21:05</span>
          </div>
        </div>
      </div>
    </div>
    <div class="phone-bottom-nav">
      <div class="p-nav-item"><span class="material-symbols-outlined">storefront</span>Catálogo</div>
      <div class="p-nav-item"><span class="material-symbols-outlined">shopping_bag</span>Bolsa</div>
      <div class="p-nav-item active"><span class="material-symbols-outlined">cloud_sync</span>Sync</div>
      <div class="p-nav-item"><span class="material-symbols-outlined">person</span>Cuenta</div>
    </div>
    `
  );
  await page.setContent(htmlCU06);
  await page.screenshot({ path: path.join(outputDir, 'CU-06_Descargar_Almacenar_Catalogo_Offline.png') });
  console.log('✅ CU-06_Descargar_Almacenar_Catalogo_Offline.png');

  // -------------------------------------------------------------------------
  // CU-07: Consultar Catálogo y Existencias Offline - Web PWA Real
  // -------------------------------------------------------------------------
  const htmlCU07 = renderWebPage(
    'Consultar Catálogo y Existencias Offline',
    'CU-07',
    `
    <!-- FashionStore Real Sync Status Bar (Lines 8100-8183 of styles.css) -->
    <div class="sync-status-bar" style="margin-top:28px;">
      <div class="sync-status-info">
        <span class="offline-pill">
          <span class="material-symbols-outlined" style="font-size:16px;">wifi_off</span>
          Modo offline · Catálogo local
        </span>
        <span class="offline-warning-text">
          Precios y disponibilidad locales pueden estar desactualizados.
        </span>
        <span class="last-sync-badge">
          Sincronizado: Aurora Equipetrol (25/10/2026 18:30)
        </span>
      </div>
      <div class="sync-actions">
        <button type="button" class="button button-light sync-btn" style="padding:6px 14px; font-size:0.75rem;">
          <span class="material-symbols-outlined" style="font-size:16px;">sync</span>
          Actualizar catálogo
        </button>
      </div>
    </div>

    <!-- Collection Browser Real Header -->
    <section class="collection-browser" style="margin-top:20px;">
      <div class="collection-title-wrap">
        <h1 style="font-family:'Playfair Display', serif; font-size:2.8rem; font-weight:400; margin:0 0 6px; color:var(--ink);">Atelier Essentials</h1>
        <p style="color:var(--muted); font-size:0.88rem; margin:0;">Colección descargada en memoria local para consulta inmediata sin conexión.</p>
        <div style="margin-top:12px;">
          <span style="font-size:0.72rem; font-weight:700; color:var(--accent); text-transform:uppercase; letter-spacing:0.08em;">
            ● 6 prendas disponibles localmente · Sucursal Aurora Equipetrol
          </span>
        </div>
      </div>
    </section>

    <!-- Product Grid Real FashionStore Styling -->
    <div style="display:grid; grid-template-columns: repeat(3, 1fr); gap:24px; margin-top:28px;">
      <article style="background:#ffffff; border:1px solid var(--line); border-radius:12px; overflow:hidden;">
        <div style="height:200px; background:#f0ede6; display:flex; align-items:center; justify-content:center; color:var(--muted);">
          <span class="material-symbols-outlined" style="font-size:54px; color:var(--accent);">dry_cleaning</span>
        </div>
        <div style="padding:18px;">
          <span style="font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--accent);">Abrigos</span>
          <h4 style="font-family:'Playfair Display', serif; font-size:1.25rem; font-weight:600; margin:4px 0 10px; color:var(--ink);">Blazer Atelier Slim</h4>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:1.1rem; color:var(--ink);">Bs 349.00</strong>
            <span class="tag" style="background:#e3ebd3; color:#2e6f40; font-weight:700;">Stock local: 5</span>
          </div>
        </div>
      </article>

      <article style="background:#ffffff; border:1px solid var(--line); border-radius:12px; overflow:hidden;">
        <div style="height:200px; background:#f0ede6; display:flex; align-items:center; justify-content:center; color:var(--muted);">
          <span class="material-symbols-outlined" style="font-size:54px; color:var(--accent);">apparel</span>
        </div>
        <div style="padding:18px;">
          <span style="font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--accent);">Vestidos</span>
          <h4 style="font-family:'Playfair Display', serif; font-size:1.25rem; font-weight:600; margin:4px 0 10px; color:var(--ink);">Vestido Seda Aurora</h4>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:1.1rem; color:var(--ink);">Bs 420.00</strong>
            <span class="tag" style="background:#e3ebd3; color:#2e6f40; font-weight:700;">Stock local: 3</span>
          </div>
        </div>
      </article>

      <article style="background:#ffffff; border:1px solid var(--line); border-radius:12px; overflow:hidden;">
        <div style="height:200px; background:#f0ede6; display:flex; align-items:center; justify-content:center; color:var(--muted);">
          <span class="material-symbols-outlined" style="font-size:54px; color:var(--accent);">checkroom</span>
        </div>
        <div style="padding:18px;">
          <span style="font-size:0.65rem; font-weight:700; letter-spacing:0.1em; text-transform:uppercase; color:var(--accent);">Camisas</span>
          <h4 style="font-family:'Playfair Display', serif; font-size:1.25rem; font-weight:600; margin:4px 0 10px; color:var(--ink);">Camisa Lino Classic</h4>
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <strong style="font-size:1.1rem; color:var(--ink);">Bs 180.00</strong>
            <span class="tag" style="background:#e3ebd3; color:#2e6f40; font-weight:700;">Stock local: 8</span>
          </div>
        </div>
      </article>
    </div>
    `,
    'catalog',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU07);
  await page.screenshot({ path: path.join(outputDir, 'CU-07_Consultar_Catalogo_Existencias_Offline.png') });
  console.log('✅ CU-07_Consultar_Catalogo_Existencias_Offline.png');

  // -------------------------------------------------------------------------
  // CU-23: Notificar Estado de Conectividad (Semáforo Online/Offline) - Web
  // -------------------------------------------------------------------------
  const htmlCU23 = renderWebPage(
    'Notificar Estado de Conectividad (Semáforo)',
    'CU-23',
    `
    <div style="padding-top:36px; max-width:980px; margin:0 auto;">
      <div class="admin-heading">
        <div>
          <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Monitor de Conectividad</p>
          <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Semáforo de Red y Sincronización</h2>
          <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Detección automática en cliente ante eventos online/offline con transición de estados en el header.</p>
        </div>
      </div>

      <div style="display:grid; grid-template-columns: 1fr 1fr; gap:24px; margin-top:20px;">
        <!-- Estado En Línea -->
        <div class="admin-panel" style="background:#ffffff; border:1px solid #cce5d4; border-radius:12px; padding:28px;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <span style="width:12px; height:12px; background:#2e6f40; border-radius:50%; box-shadow:0 0 10px rgba(46,111,64,0.4);"></span>
            <strong style="color:#2e6f40; font-size:0.85rem; letter-spacing:0.08em; text-transform:uppercase;">Condición: En Línea (Online)</strong>
          </div>

          <div class="online-pill" style="padding:10px 16px; border-radius:8px; font-size:0.85rem; margin-bottom:14px; width:100%; justify-content:center;">
            <span class="material-symbols-outlined" style="font-size:18px;">wifi</span>
            <strong>En línea · Conexión activa con el servidor</strong>
          </div>

          <p style="color:var(--muted); font-size:0.8rem; line-height:1.6;">
            Las transacciones, reservas y consultas de catálogo se realizan directamente contra la API REST central en PostgreSQL.
          </p>
        </div>

        <!-- Estado Desconectado -->
        <div class="admin-panel" style="background:#ffffff; border:1px solid #f2c7c0; border-radius:12px; padding:28px;">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:16px;">
            <span style="width:12px; height:12px; background:#991b1b; border-radius:50%; box-shadow:0 0 10px rgba(153,27,27,0.4);"></span>
            <strong style="color:#991b1b; font-size:0.85rem; letter-spacing:0.08em; text-transform:uppercase;">Condición: Desconectado (Offline)</strong>
          </div>

          <div class="offline-pill" style="padding:10px 16px; border-radius:8px; font-size:0.85rem; margin-bottom:14px; width:100%; justify-content:center;">
            <span class="material-symbols-outlined" style="font-size:18px;">wifi_off</span>
            <strong>Modo offline · Contingencia local activa</strong>
          </div>

          <p style="color:var(--muted); font-size:0.8rem; line-height:1.6;">
            El semáforo conmuta automáticamente al perder conexión. Las operaciones se enrutan a IndexedDB/SQLite con aviso de datos locales.
          </p>
        </div>
      </div>
    </div>
    `,
    'network',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU23);
  await page.screenshot({ path: path.join(outputDir, 'CU-23_Notificar_Estado_Conectividad.png') });
  console.log('✅ CU-23_Notificar_Estado_Conectividad.png');

  // -------------------------------------------------------------------------
  // CU-24: Instalar y Registrar Service Worker (PWA) - Web
  // -------------------------------------------------------------------------
  const htmlCU24 = renderWebPage(
    'Instalar y Registrar Service Worker (PWA)',
    'CU-24',
    `
    <div style="padding-top:36px; max-width:920px; margin:0 auto;">
      <div class="admin-heading">
        <div>
          <p class="eyebrow" style="color:var(--accent); font-size:0.68rem; letter-spacing:0.12em; text-transform:uppercase;">Progressive Web App</p>
          <h2 style="font-family:'Playfair Display', serif; font-size:2.4rem; font-weight:400; margin-top:8px;">Instalación & Service Worker</h2>
          <p style="color:var(--muted); font-size:0.85rem; margin-top:6px;">Instalabilidad en navegadores compatibles y control de caché autónomo.</p>
        </div>
      </div>

      <!-- Diálogo de Instalación PWA Estilo FashionStore -->
      <div class="auth-card wide" style="margin:20px 0 28px; text-align:left; border:1px solid var(--line); box-shadow:0 15px 40px rgba(27,28,26,0.08);">
        <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--line); padding-bottom:18px; margin-bottom:18px;">
          <div style="display:flex; align-items:center; gap:16px;">
            <span class="brand-monogram" style="width:48px; height:48px; font-size:1.4rem;">FS</span>
            <div>
              <h3 style="font-family:'Playfair Display', serif; font-size:1.4rem; margin:0; color:var(--ink);">¿Instalar FashionStore en tu dispositivo?</h3>
              <p style="color:var(--muted); font-size:0.8rem; margin-top:2px;">Aplicación web progresiva lista para operar con y sin internet.</p>
            </div>
          </div>
          <div style="display:flex; gap:10px;">
            <button class="button button-light">Ahora no</button>
            <button class="button button-dark"><span class="material-symbols-outlined" style="font-size:16px;">download</span> Instalar App</button>
          </div>
        </div>

        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:18px;">
          <div style="background:var(--panel); padding:16px; border-radius:8px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
              <span class="material-symbols-outlined" style="color:#2e6f40; font-size:18px;">check_circle</span>
              <strong style="font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink);">Service Worker Activo</strong>
            </div>
            <p style="color:var(--muted); font-size:0.75rem; margin:0; line-height:1.5;">Controlado por <code>ngsw-worker.js</code> con precaché de assets, fuentes e interfaz de usuario.</p>
          </div>

          <div style="background:var(--panel); padding:16px; border-radius:8px;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
              <span class="material-symbols-outlined" style="color:#2e6f40; font-size:18px;">check_circle</span>
              <strong style="font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em; color:var(--ink);">Web App Manifest</strong>
            </div>
            <p style="color:var(--muted); font-size:0.75rem; margin:0; line-height:1.5;">Configurado en <code>manifest.webmanifest</code> con modo <code>standalone</code> e iconografía editorial.</p>
          </div>
        </div>
      </div>
    </div>
    `,
    'pwa',
    'Boutique Aurora'
  );
  await page.setContent(htmlCU24);
  await page.screenshot({ path: path.join(outputDir, 'CU-24_Instalar_Service_Worker_PWA.png') });
  console.log('✅ CU-24_Instalar_Service_Worker_PWA.png');

  // -------------------------------------------------------------------------
  // CU-25: Configurar y Migrar Persistencia SQLite Móvil - Móvil Flutter
  // -------------------------------------------------------------------------
  const htmlCU25 = renderMobilePage(
    'Configurar y Migrar Persistencia SQLite Móvil',
    'CU-25',
    `
    <div class="phone-app-bar">
      <div class="phone-app-title">Fashion<span>Store</span></div>
      <span class="material-symbols-outlined" style="font-size:20px; color:#25211d;">storage</span>
    </div>
    <div class="phone-content">
      <div style="background:#fffcf6; border:1px solid #e5e0d8; border-radius:18px; padding:20px; box-shadow:0 6px 16px rgba(37,33,29,0.05);">
        <div style="display:flex; align-items:center; gap:12px; margin-bottom:14px;">
          <div style="width:44px; height:44px; background:#f0e8db; border-radius:10px; display:flex; align-items:center; justify-content:center; color:#8f6d2d;">
            <span class="material-symbols-outlined" style="font-size:24px;">database</span>
          </div>
          <div>
            <h4 style="font-family:'Playfair Display', serif; font-size:1.15rem; font-weight:700; color:#25211d;">fashionstore_offline.db</h4>
            <span style="font-size:0.68rem; color:#2e6f40; font-weight:700; text-transform:uppercase;">SQLite nativo · Versión 1</span>
          </div>
        </div>
        <p style="font-size:0.75rem; color:#6f675d; line-height:1.5;">
          Motor relacional SQLite inicializado con sqflite para garantizar persistencia ACID entre reinicios.
        </p>
      </div>

      <div style="background:#fffcf6; border:1px solid #e5e0d8; border-radius:18px; padding:18px;">
        <span style="font-size:0.68rem; font-weight:700; color:#8f6d2d; letter-spacing:0.08em; text-transform:uppercase; display:block; margin-bottom:12px;">TABLAS NORMALIZADAS VERIFICADAS</span>
        <div style="display:flex; flex-direction:column; gap:10px; font-size:0.75rem; font-family:'JetBrains Mono', monospace; color:#25211d;">
          <div style="display:flex; justify-content:space-between; border-bottom:1px solid #f0e8db; padding-bottom:6px;">
            <span>✓ metadata</span><span style="color:#6f675d;">(branch_id, tenant_id)</span>
          </div>
          <div style="display:flex; justify-content:space-between; border-bottom:1px solid #f0e8db; padding-bottom:6px;">
            <span>✓ categories</span><span style="color:#6f675d;">(id, name, is_active)</span>
          </div>
          <div style="display:flex; justify-content:space-between; border-bottom:1px solid #f0e8db; padding-bottom:6px;">
            <span>✓ products</span><span style="color:#6f675d;">(id, code, price, slug)</span>
          </div>
          <div style="display:flex; justify-content:space-between; border-bottom:1px solid #f0e8db; padding-bottom:6px;">
            <span>✓ variants</span><span style="color:#6f675d;">(id, sku, size, color)</span>
          </div>
          <div style="display:flex; justify-content:space-between;">
            <span>✓ inventory</span><span style="color:#6f675d;">(branch_id, stock)</span>
          </div>
        </div>
      </div>

      <div style="background:#f0e8db; border-radius:14px; padding:12px 16px; display:flex; align-items:center; gap:10px;">
        <span class="material-symbols-outlined" style="color:#8f6d2d; font-size:18px;">shield</span>
        <span style="font-size:0.72rem; color:#25211d; font-weight:500;">Aislamiento multi-tenant: purga atómica de SQLite en logout.</span>
      </div>
    </div>
    <div class="phone-bottom-nav">
      <div class="p-nav-item"><span class="material-symbols-outlined">storefront</span>Catálogo</div>
      <div class="p-nav-item"><span class="material-symbols-outlined">shopping_bag</span>Bolsa</div>
      <div class="p-nav-item"><span class="material-symbols-outlined">cloud_sync</span>Sync</div>
      <div class="p-nav-item active"><span class="material-symbols-outlined">tune</span>Diagnóstico</div>
    </div>
    `
  );
  await page.setContent(htmlCU25);
  await page.screenshot({ path: path.join(outputDir, 'CU-25_Persistencia_SQLite_Movil.png') });
  console.log('✅ CU-25_Persistencia_SQLite_Movil.png');

  await browser.close();
  console.log('🎉 Las 10 capturas de la Etapa 1 fueron regeneradas exitosamente con los estilos reales de FashionStore!');
}

run().catch((e) => {
  console.error('Error generando capturas:', e);
  process.exit(1);
});
