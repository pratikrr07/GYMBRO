// ═══════════════════════════════════════════════════════════════
//  GYMBRO Service Worker v10 — Passthrough (no caching)
//  Exists only for PWA installability — all requests go to network
// ═══════════════════════════════════════════════════════════════

// ── Install: skip waiting immediately ──
self.addEventListener('install', (event) => {
  console.log('📦 GYMBRO SW v10: Installing (passthrough)');
  self.skipWaiting();
});

// ── Activate: delete ALL caches from every previous version ──
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.map((key) => {
        console.log('🗑️ Deleting cache:', key);
        return caches.delete(key);
      }))
    )
  );
  self.clients.claim();
  console.log('✅ GYMBRO SW v4: Active — passthrough, no caching');
});

// ── NO fetch handler — browser handles all requests directly ──
