const http = require('http');
const req = http.get('http://127.0.0.1:5555/api/health', (res) => {
  let data = '';
  res.on('data', (chunk) => data += chunk);
  res.on('end', () => {
    process.exit(res.statusCode === 200 ? 0 : 1);
  });
});
req.on('error', () => process.exit(1));
req.setTimeout(5000, () => { req.destroy(); process.exit(1); });
