/* 生活系统 LifeOS — Service Worker
   改版本号即可让所有设备拉取新版本

   v5：界面调整（知识库/设置入口移到首屏右上角）后升版本，让已装主屏的设备尽快换新。
   v4：知识库（kb/site/）也进离线缓存；导航的离线回退按路径区分，
       不会再用知识库页面顶替应用外壳。
   v3：修缓存污染 —— 原来任何页面导航都会把响应写进 ./index.html。
*/
const CACHE = 'lifeos-v5';

// 应用外壳
const SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './icons/icon-192.png',
  './icons/icon-512.png',
  './icons/icon-maskable-512.png',
  './icons/apple-touch-icon.png'
];

// 知识库（单文件，离线也能查）
const KB = './kb/site/index.html';

const ASSETS = SHELL.concat([KB]);
const SHELL_KEY = './index.html';

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(ASSETS).catch(() => c.addAll(SHELL)))
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

function pathOf(req) {
  try { return new URL(req.url).pathname; } catch (_) { return ''; }
}

function isShellRequest(req) {
  try {
    const root = new URL('./', self.registration.scope).pathname;
    const p = pathOf(req);
    return p === root || p === root + 'index.html';
  } catch (_) {
    return false;
  }
}

function isKbRequest(req) {
  return /\/kb(\/site)?\/?$/.test(pathOf(req));
}

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;

  // 页面导航：网络优先；离线时按路径回退到对应页面
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req)
        .then(res => {
          // 只有应用外壳自己才回写外壳缓存（v3 的修复）
          if (res.ok && isShellRequest(req)) {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(SHELL_KEY, copy));
          }
          return res;
        })
        .catch(() => caches.match(isKbRequest(req) ? KB : SHELL_KEY))
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
