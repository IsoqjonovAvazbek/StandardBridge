/* StandartBridge Service Worker v3 */
const CACHE_NAME = 'sb-cache-v3';
const OFFLINE_URL = '/offline/';

/* Static assets to pre-cache */
const PRECACHE = [
  '/',
  '/offline/',
  '/static/manifest.json',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
];

/* ── Install ── */
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(PRECACHE))
  );
  self.skipWaiting();
});

/* ── Activate: delete old caches ── */
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

/* ── Fetch strategy ── */
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Only handle same-origin GET requests
  if (request.method !== 'GET' || url.origin !== location.origin) return;

  // Skip admin, API, media, auth endpoints — always network
  const skip = ['/admin/', '/api/', '/media/', '/click/', '/health/'];
  if (skip.some(p => url.pathname.startsWith(p))) return;

  // Static assets: Cache-first
  if (url.pathname.startsWith('/static/')) {
    event.respondWith(
      caches.match(request).then(cached => {
        if (cached) return cached;
        return fetch(request).then(resp => {
          if (resp && resp.status === 200) {
            const clone = resp.clone();
            caches.open(CACHE_NAME).then(c => c.put(request, clone));
          }
          return resp;
        });
      })
    );
    return;
  }

  // Navigation (HTML pages): Network-first, fallback to offline page
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match(OFFLINE_URL).then(r => r || new Response('Offline', { status: 503 }))
      )
    );
    return;
  }

  // Everything else: Network-first
  event.respondWith(
    fetch(request).catch(() => caches.match(request))
  );
});

/* ── Push notifications ── */
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'StandartBridge';
  const options = {
    body: data.body || "Yangi bildirishnoma",
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/icon-72.png',
    data: { url: data.url || '/notifications/' },
    vibrate: [100, 50, 100],
    requireInteraction: false,
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
      for (const c of list) {
        if (c.url === target && 'focus' in c) return c.focus();
      }
      if (clients.openWindow) return clients.openWindow(target);
    })
  );
});
