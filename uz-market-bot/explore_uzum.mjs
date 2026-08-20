import { chromium } from 'playwright';

const browser = await chromium.launch({ headless: true });
const page = await browser.newPage();

const apiCalls = [];
page.on('request', req => {
  const url = req.url();
  if (url.includes('uzum.uz/') && (url.includes('/api/') || url.includes('search') || url.includes('product'))) {
    apiCalls.push({ url: url, method: req.method() });
  }
});

// Перехватываем ответы
const apiResponses = [];
page.on('response', async res => {
  const url = res.url();
  if (url.includes('uzum.uz/') && (url.includes('/api/') || url.includes('search') || url.includes('product'))) {
    try {
      const ct = res.headers()['content-type'] || '';
      apiResponses.push({ url: url, status: res.status(), contentType: ct });
    } catch(e) {}
  }
});

console.log("=== Открываем Uzum ===");
await page.goto('https://uzum.uz/', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(3000);

console.log("URL:", page.url());

console.log("\n=== API запросы ===");
for (const call of apiCalls) console.log(call.method, call.url);

console.log("\n=== API ответы ===");
for (const r of apiResponses) console.log(r.status, r.contentType, r.url);

// Пробуем поиск
console.log("\n=== Поиск ===");
apiCalls.length = 0;
apiResponses.length = 0;
await page.goto('https://uzum.uz/ru/search?q=iphone', { waitUntil: 'networkidle', timeout: 30000 });
await page.waitForTimeout(3000);

console.log("URL:", page.url());
console.log("\n=== API запросов после поиска ===");
for (const call of apiCalls) console.log(call.method, call.url);
console.log("\n=== API ответов ===");
for (const r of apiResponses) console.log(r.status, r.contentType, r.url);

// Смотрим что в теле страницы
const text = await page.evaluate(() => document.body?.innerText?.slice(0, 2000) || 'no body');
console.log("\n=== Текст страницы ===");
console.log(text);

await browser.close();
