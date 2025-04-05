const CACHE_NAME = 'pwa-base-v1';
const ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/js/app.js',
    '/static/manifest.json'
];

self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
    );
});

self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request)
            .then(res => res || fetch(e.request))
    );
});