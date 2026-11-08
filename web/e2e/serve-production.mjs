import { createReadStream } from 'node:fs';
import { access, stat } from 'node:fs/promises';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = resolve(fileURLToPath(new URL('.', import.meta.url)), '..', 'dist', 'fashionstore-web', 'browser');
const port = Number(process.env.PWA_PORT || 4300);
const offlineCatalog = {
  metadata: { tenant_id: 1, tenant_name: 'Boutique Aurora', branch_id: 10, branch_name: 'Aurora Central', sync_timestamp: '2026-10-23T20:00:00Z', catalog_version: 'cat-v1-100' },
  categories: [{ id: 1, name: 'Vestidos', is_active: true }],
  products: [{ id: 101, category_id: 1, category_name: 'Vestidos', name: 'Vestido Persistente', code: 'VES-PERSISTENTE', slug: 'vestido-persistente', description: 'Producto guardado en IndexedDB', price: 350, image_url: null, is_active: true }],
  variants: [{ id: 1001, product_id: 101, sku: 'VES-PERSISTENTE-S-RED', size_id: 1, size_name: 'S', color_id: 1, color_name: 'Rojo', price: 350, is_active: true }],
  inventory: [{ product_variant_id: 1001, stock_quantity: 15, reserved_quantity: 3, available_quantity: 12 }],
};
const contentTypes = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webmanifest': 'application/manifest+json; charset=utf-8',
};

function safePath(urlPath) {
  const pathname = decodeURIComponent(new URL(urlPath, 'http://localhost').pathname);
  const candidate = resolve(root, `.${normalize(pathname)}`);
  return candidate.startsWith(root) ? candidate : null;
}

const server = createServer(async (request, response) => {
  const requestUrl = new URL(request.url || '/', 'http://localhost');
  if (requestUrl.pathname.startsWith('/api/v1/')) {
    const body = requestUrl.pathname === '/api/v1/sync/catalog'
      ? offlineCatalog
      : requestUrl.pathname === '/api/v1/catalog/filters'
        ? { categories: offlineCatalog.categories, sizes: [{ id: 1, name: 'S' }], colors: [{ id: 1, name: 'Rojo', hex_code: '#b91c1c' }], branches: [{ id: 10, name: 'Aurora Central' }] }
        : requestUrl.pathname === '/api/v1/catalog/navigation'
          ? { seasons: [], collections: [], audiences: [] }
          : { items: offlineCatalog.products, total: 1, page: 1, page_size: 12, total_pages: 1 };
    response.writeHead(200, { 'content-type': 'application/json; charset=utf-8' });
    response.end(JSON.stringify(body));
    return;
  }
  const requested = safePath(request.url || '/');
  const filePath = requested && (await isFile(requested) ? requested : join(root, 'index.html'));

  if (!filePath) {
    response.writeHead(400, { 'content-type': 'text/plain; charset=utf-8' });
    response.end('Invalid path');
    return;
  }

  response.writeHead(200, {
    'cache-control': filePath.endsWith('ngsw-worker.js') || filePath.endsWith('ngsw.json') ? 'no-cache' : 'public, max-age=0',
    'content-type': contentTypes[extname(filePath)] || 'application/octet-stream',
  });
  createReadStream(filePath).pipe(response);
});

async function isFile(filePath) {
  try {
    return (await stat(filePath)).isFile();
  } catch {
    return false;
  }
}

await access(root);
server.listen(port, '127.0.0.1', () => {
  console.log(`Serving production PWA from ${root} at http://127.0.0.1:${port}`);
});
