/* 生活系统 LifeOS — Service Worker
   改版本号即可让所有设备拉取新版本
   v3：修 v2 的缓存污染 —— 原来任何页面导航都会把响应写进 ./index.html，
       导致访问 /kb/ 之后，离线打开生活系统看到的是知识库页面。 */
const CACHE = 'lifeos-v3';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

// 应用外壳的缓存键：只有访问应用根路径时，才允许覆盖它
const SHELL_KEY = './index.html';

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS))
      .then(() => self.skipWaiting())
      .catch(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

function isShellRequest(req) {
  try {
    const u = new URL(req.url);
    const root = new URL('./', self.registration.scope).pathname;
    return u.pathname === root || u.pathname === root + 'index.html';
  } catch (_) {
    return false;
  }
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  // 页面导航：网络优先，失败回退缓存
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then(res => {
          // 只有应用外壳自己才回写缓存；/kb/ 等子页面只走网络
          if (res.ok && isShellRequest(req)) {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(SHELL_KEY, copy));
          }
          return res;
        })
        .catch(() => caches.match(SHELL_KEY))
    );
    return;
  }

  // 静态资源：缓存优先
  e.respondWith(
    caches.match(req).then(hit => hit || fetch(req).then(res => {
      if (res.ok && new URL(req.url).origin === location.origin) {
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
      }
      return res;
    }).catch(() => caches.match(SHELL_KEY)))
  );
});
