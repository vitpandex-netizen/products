import { createServer } from 'node:http';
import { readFileSync, readdirSync, existsSync, appendFileSync, writeFileSync } from 'node:fs';
import { execSync } from 'node:child_process';
import { join } from 'node:path';
import { URL } from 'node:url';

const DEV = '/Volumes/External/dev';
const PORT = process.env.PORT || 3001;
const METRICS_FILE = '/tmp/dashboard-metrics.jsonl';
const META_FILE = '/Volumes/External/dev/project-dashboard/PROJECT_META.json';

let projectMeta = {};
try { projectMeta = JSON.parse(readFileSync(META_FILE, 'utf-8')); } catch(e) {}

function sh(cmd, cwd) {
  try { return execSync(cmd, { cwd, encoding: 'utf-8', timeout: 5000, stdio: ['pipe','pipe','pipe'] }).trim(); } catch { return ''; }
}

function collectMetrics() {
  try {
    if (!existsSync(DEV)) return;
    const ts = new Date().toISOString().replace(/\.\d+Z/, '+0500');
    let dirty = 0, clean = 0, nogit = 0;
    for (const e of readdirSync(DEV, { withFileTypes: true })) {
      if (!e.isDirectory() || e.name.startsWith('.') || e.name === 'project-dashboard') continue;
      const p = join(DEV, e.name);
      if (existsSync(join(p, '.git'))) {
        sh('git status --short', p) ? dirty++ : clean++;
      } else { nogit++; }
    }
    const cpu = parseFloat(sh("ps -A -o %cpu | awk '{s+=$1} END {printf \"%.1f\", s}'") || '0');
    const diskPct = parseInt(sh("df -h / | tail -1 | awk '{print $5}' | tr -d '%'") || '0');
    const diskUsed = sh("df -h / | tail -1 | awk '{print $3}'") || '?';
    const diskTotal = sh("df -h / | tail -1 | awk '{print $2}'") || '?';
    const pm2 = parseInt(sh('pm2 list 2>/dev/null | grep -c online') || '0');
    const uptime = sh("uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}'") || '?';
    const mem = parseInt(sh('sysctl hw.memsize 2>/dev/null | awk \'{printf "%.0f", $2/1073741824}\'') || '0');
    const obj = { ts, dirty, clean, nogit, cpu, disk_pct: diskPct, disk_used: diskUsed, disk_total: diskTotal, mem_total: mem, pm2_online: pm2, uptime };
    appendFileSync(METRICS_FILE, JSON.stringify(obj) + '\n');
    const lines = readFileSync(METRICS_FILE, 'utf-8').split('\n').filter(Boolean);
    if (lines.length > 1440) writeFileSync(METRICS_FILE, lines.slice(-1440).join('\n') + '\n');
  } catch(e) {}
}

function getMetrics() {
  try {
    if (!existsSync(METRICS_FILE)) return [];
    return readFileSync(METRICS_FILE, 'utf-8').split('\n').filter(Boolean).map(l => { try { return JSON.parse(l); } catch { return null; } }).filter(Boolean);
  } catch { return []; }
}

function getProjects() {
  const projects = [];
  for (const entry of readdirSync(DEV, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith('.')) continue;
    if (entry.name === 'project-dashboard') continue;
    const p = join(DEV, entry.name);
    const isGit = existsSync(join(p, '.git'));
    let branch = '', dirty = 0, lastCommit = '', lastCommitTime = '', rules = false, files = [];
    if (isGit) {
      branch = sh('git branch --show-current', p);
      const raw = sh('git status --short', p);
      dirty = raw ? raw.split('\n').length : 0;
      lastCommit = sh('git log -1 --format=%s', p);
      lastCommitTime = sh('git log -1 --format=%ar', p);
      files = raw ? raw.split('\n').filter(Boolean).map(l => ({ status: l.substring(0,2).trim(), file: l.substring(3).trim() })) : [];
    }
    rules = existsSync(join(p, '.interpreter-rules'));
    let type = 'unknown';
    if (rules) { const r = readFileSync(join(p, '.interpreter-rules'), 'utf-8'); const m = r.match(/## Project type\n([\w,\s-]+)/); if (m) type = m[1].trim(); }
    let size = ''; try { size = execSync(`du -sh "${p}" 2>/dev/null | cut -f1`, { encoding: 'utf-8', timeout: 2000 }).trim(); } catch {}
    const meta = projectMeta[entry.name] || {};
    projects.push({ name: meta.name || entry.name, dir: entry.name, path: p, git: isGit, branch: branch || '-', dirty, files, lastCommit: lastCommit || '-', lastCommitTime: lastCommitTime || '-', rules, type, size, description: meta.description || '' });
  }
  return projects.sort((a, b) => a.name.localeCompare(b.name));
}

function getSystemStats() {
  const cpu = sh("ps -A -o %cpu | awk '{s+=$1} END {printf \"%.1f\", s}'") || 'N/A';
  const disk = sh("df -h / | tail -1 | awk '{print $3 \" / \" $2 \" (\" $5 \")\"}'") || 'N/A';
  const uptime = sh("uptime | awk -F'up ' '{print $2}' | awk -F',' '{print $1}'") || 'N/A';
  return { cpu: cpu + '%', disk, uptime };
}

function getPm2Status() {
  const raw = sh("pm2 list 2>/dev/null | grep -E 'online|errored'");
  return raw.split('\n').filter(Boolean).map(line => {
    const parts = line.trim().split(/\s+/);
    return parts.length < 6 ? null : { name: parts[1] || '?', status: parts[7] || '?', uptime: parts[5] || '?', restarts: parts[6] || '?' };
  }).filter(Boolean);
}

function getLaunchdStatus() {
  const raw = sh("launchctl list | grep com.vitaliyr");
  return raw.split('\n').filter(Boolean).map(line => {
    const parts = line.trim().split(/\s+/);
    return { pid: parts[0] === '-' ? 'stopped' : parts[0], status: parts[1] === '0' ? 'OK' : 'ERR', name: parts[2] || '?' };
  });
}

function getBackupInfo() {
  const backups = sh('ls -1t /Volumes/External/dev/.backups/ 2>/dev/null | head -3');
  if (!backups) return { lastBackup: 'none', status: 'red', age: '-' };
  const dates = backups.split('\n');
  const last = dates[0];
  const age = sh(`echo $(( ($(date +%s) - $(date -r /Volumes/External/dev/.backups/${last}/config.json +%s 2>/dev/null)) / 3600 ))`) || '?';
  return { lastBackup: last, age: age + 'h', status: parseInt(age) < 24 ? 'green' : 'yellow' };
}

function getSessionLog() {
  const f = join(DEV, 'SESSION_LOG.md');
  if (!existsSync(f)) return 'No entries.';
  return readFileSync(f, 'utf-8');
}

// ─── SVG Charts ────────────────────────────────────
function renderDirtyChart(metrics) {
  if (metrics.length < 2) return '<div style="color:#484f58;padding:10px;font-size:11px;">Not enough data yet</div>';
  const width = 600, height = 160;
  const pad = { top: 15, right: 10, bottom: 20, left: 35 };
  const cw = width - pad.left - pad.right;
  const ch = height - pad.top - pad.bottom;
  const pts = metrics.slice(-48);
  const maxVal = Math.max(...pts.map(p => (p.dirty||0) + (p.clean||0)), 5);
  const xStep = cw / (pts.length - 1 || 1);
  const dirtyPath = pts.map((p, i) => `${i===0?'M':'L'}${pad.left+i*xStep},${pad.top+ch-(p.dirty/maxVal)*ch}`).join(' ');
  const cleanPath = pts.map((p, i) => `${i===0?'M':'L'}${pad.left+i*xStep},${pad.top+ch-(p.clean/maxVal)*ch}`).join(' ');
  const dirtyArea = dirtyPath + ` L${pad.left+(pts.length-1)*xStep},${pad.top+ch} L${pad.left},${pad.top+ch} Z`;
  const cleanArea = cleanPath + ` L${pad.left+(pts.length-1)*xStep},${pad.top+ch} L${pad.left},${pad.top+ch} Z`;
  const yLabels = [0,1,2,3,4,5].filter(v => v <= maxVal).map(v => {
    const y = pad.top + ch - (v/maxVal)*ch;
    return `<text x="${pad.left-5}" y="${y+3}" text-anchor="end" fill="#484f58" font-size="9">${v}</text><line x1="${pad.left}" y1="${y}" x2="${width-pad.right}" y2="${y}" stroke="#21262d" stroke-width="0.5"/>`;
  }).join('\n');
  const last = pts[pts.length-1];
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="max-width:100%;height:auto;">
    <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"/>
    ${yLabels}<path d="${dirtyArea}" fill="#d2992222" stroke="none"/><path d="${cleanArea}" fill="#23863622" stroke="none"/>
    <path d="${dirtyPath}" fill="none" stroke="#d29922" stroke-width="1.5"/><path d="${cleanPath}" fill="none" stroke="#3fb950" stroke-width="1.5"/>
    <rect x="${pad.left+10}" y="${pad.top-12}" width="8" height="8" rx="2" fill="#d29922"/>
    <text x="${pad.left+22}" y="${pad.top-5}" fill="#d29922" font-size="9">Dirty (${last.dirty})</text>
    <rect x="${pad.left+100}" y="${pad.top-12}" width="8" height="8" rx="2" fill="#3fb950"/>
    <text x="${pad.left+112}" y="${pad.top-5}" fill="#3fb950" font-size="9">Clean (${last.clean})</text>
  </svg>`;
}

function renderCpuChart(metrics) {
  if (metrics.length < 2) return '';
  const pts = metrics.slice(-48);
  const width=600,height=120,pad={top:10,right:10,bottom:20,left:35};
  const cw=width-pad.left-pad.right,ch=height-pad.top-pad.bottom;
  const maxCpu=Math.max(...pts.map(p=>p.cpu||0),100);
  const xStep=cw/(pts.length-1||1);
  const path=pts.map((p,i)=>`${i===0?'M':'L'}${pad.left+i*xStep},${pad.top+ch-(Math.min(p.cpu,maxCpu)/maxCpu)*ch}`).join(' ');
  const area=path+` L${pad.left+(pts.length-1)*xStep},${pad.top+ch} L${pad.left},${pad.top+ch} Z`;
  const last=pts[pts.length-1];
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="max-width:100%;height:auto;">
    <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"/>
    <path d="${area}" fill="#58a6ff22" stroke="none"/><path d="${path}" fill="none" stroke="#58a6ff" stroke-width="1.5"/>
    <text x="${pad.left+10}" y="${pad.top+10}" fill="#58a6ff" font-size="9">CPU: ${last.cpu}%</text></svg>`;
}

function renderDiskChart(metrics) {
  if (metrics.length < 2) return '';
  const pts=metrics.slice(-48),width=600,height=120,pad={top:10,right:10,bottom:20,left:35};
  const cw=width-pad.left-pad.right,ch=height-pad.top-pad.bottom,xStep=cw/(pts.length-1||1);
  const path=pts.map((p,i)=>`${i===0?'M':'L'}${pad.left+i*xStep},${pad.top+ch-((p.disk_pct||0)/100)*ch}`).join(' ');
  const area=path+` L${pad.left+(pts.length-1)*xStep},${pad.top+ch} L${pad.left},${pad.top+ch} Z`;
  const last=pts[pts.length-1]; const color=last.disk_pct>80?'#f85149':last.disk_pct>60?'#d29922':'#3fb950';
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="max-width:100%;height:auto;">
    <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"/>
    <path d="${area}" fill="${color}22" stroke="none"/><path d="${path}" fill="none" stroke="${color}" stroke-width="1.5"/>
    <text x="${pad.left+10}" y="${pad.top+10}" fill="${color}" font-size="9">Disk: ${last.disk_pct}% (${last.disk_used||'?'})</text></svg>`;
}

function renderPm2Chart(metrics) {
  if (metrics.length < 2) return '';
  const pts=metrics.slice(-48),width=600,height=100,pad={top:10,right:10,bottom:20,left:35};
  const cw=width-pad.left-pad.right,ch=height-pad.top-pad.bottom,xStep=cw/(pts.length-1||1);
  const path=pts.map((p,i)=>`${i===0?'M':'L'}${pad.left+i*xStep},${pad.top+ch-((p.pm2_online||0)/15)*ch}`).join(' ');
  return `<svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}" style="max-width:100%;height:auto;">
    <rect x="0" y="0" width="${width}" height="${height}" fill="transparent"/>
    <path d="${path}" fill="none" stroke="#3fb950" stroke-width="1.5"/>
    <text x="${pad.left+10}" y="${pad.top+10}" fill="#3fb950" font-size="9">pm2: ${pts[pts.length-1].pm2_online}</text></svg>`;
}

// ─── Render HTML ───────────────────────────────────
function renderHTML() {
  const projects = getProjects();
  const stats = getSystemStats();
  const pm2 = getPm2Status();
  const launchd = getLaunchdStatus();
  const backup = getBackupInfo();
  const metrics = getMetrics();
  const total = projects.length;
  const gitClean = projects.filter(p => p.git && p.dirty === 0).length;
  const unclean = projects.filter(p => p.git && p.dirty > 0).length;
  const noGit = projects.filter(p => !p.git).length;

  const projectRows = projects.map(p => {
    const statusClass = !p.git ? 'no-git' : p.dirty > 0 ? 'dirty' : 'clean';
    const gitBadge = !p.git ? 'red' : p.dirty > 0 ? 'yellow' : 'green';
    const filesHtml = p.files.length > 0 ? p.files.map(f => 
      `<span class="dirty-file ${f.status==='??'?'untracked':'modified'}">${f.status==='??'?'+':'~'} ${f.file}</span>`
    ).join('') : '';
    return `<div class="project-card ${statusClass}" data-dir="${p.dir}" onclick="window.location.href='file:///Volumes/External/dev/${p.dir}'">
      <div class="project-header">
        <span class="project-name" title="${p.dir}">${p.name}</span>
        ${p.description ? `<span class="project-desc">${p.description}</span>` : ''}
        <span class="project-badge ${gitBadge}"></span>
      </div>
      <div class="project-meta">
        ${p.type!=='unknown'?`<span class="tag">${p.type}</span>`:''}
        ${p.rules?'<span class="tag rule-tag">rules</span>':''}
        ${p.size?`<span class="tag">${p.size}</span>`:''}
      </div>
      ${p.git?`<div class="project-details"><span class="branch">${p.branch}</span><span class="commit" title="${p.lastCommit}">${p.lastCommit}</span><span class="time">${p.lastCommitTime}</span></div>`:''}
      <div class="dirty-files">${filesHtml}</div>
      <div class="project-actions">
        <button class="btn btn-sm" onclick="showFiles('${p.dir}')">files</button>
        ${p.dirty>0?`<button class="btn btn-sm success" onclick="commitProject('${p.dir}')">commit</button>`:''}
        <button class="btn btn-sm" onclick="verifyProject('${p.dir}')">verify</button>
      </div>
    </div>`;
  }).join('\n');

  const pm2Rows = pm2.map(p => `<div class="sys-item"><span class="dot on"></span><span class="sys-name">${p.name}</span><span class="sys-meta">${p.uptime}</span></div>`).join('\n');
  const launchdRows = launchd.map(l => `<div class="sys-item"><span class="dot ${l.pid==='stopped'?'off':'on'}"></span><span class="sys-name">${l.name.replace('com.vitaliyr.','')}</span><span class="sys-meta">${l.pid==='stopped'?'off':'pid '+l.pid}</span></div>`).join('\n');
  const logLines = getSessionLog().split('\n').filter(l => l.startsWith('|')).slice(-20).join('\n');

  return `<!DOCTYPE html>
<html lang="ru"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Project Dashboard</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:12px}
.header{display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #21262d;margin-bottom:12px}
.header h1{font-size:16px;font-weight:600;color:#f0f6fc}.header h1 span{color:#58a6ff}
.header-stats{display:flex;gap:8px;font-size:11px;color:#8b949e}.stat{display:flex;align-items:center;gap:3px}
.search-bar{width:100%;padding:6px 10px;margin-bottom:8px;background:#161b22;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:13px;outline:none}
.search-bar:focus{border-color:#58a6ff}
.btn{padding:4px 10px;border-radius:6px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;font-size:10px;cursor:pointer;transition:all .15s;display:inline-block;text-decoration:none}
.btn:hover{background:#30363d;border-color:#58a6ff}.btn.primary{background:#1f6feb;border-color:#1f6feb;color:#fff}
.btn.success{border-color:#238636;color:#3fb950}.btn-sm{padding:2px 6px;font-size:9px}
.actions{display:flex;gap:6px;margin-bottom:10px;flex-wrap:wrap}
.dashboard-grid{display:grid;grid-template-columns:1fr 320px;gap:12px}@media(max-width:1000px){.dashboard-grid{grid-template-columns:1fr}}
.project-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:8px}
.project-card{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;cursor:pointer;transition:all .15s}
.project-card{cursor:pointer}.project-card:hover{border-color:#58a6ff;background:#1c2128;transform:translateY(-1px);box-shadow:0 4px 12px rgba(0,0,0,.3)}
.project-card.dirty{border-left:3px solid #d29922}.project-card.clean{border-left:3px solid #238636}.project-card.no-git{border-left:3px solid #8b949e}
.project-header{display:flex;align-items:center;gap:6px;margin-bottom:4px}
.project-name{font-size:14px;font-weight:600;color:#f0f6fc;cursor:help;flex-shrink:0}
.project-desc{font-size:10px;color:#8b949e;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;flex:1;min-width:0}
.project-badge{width:8px;height:8px;border-radius:50%;flex-shrink:0}
.project-badge.green{background:#3fb950}.project-badge.yellow{background:#d29922}.project-badge.red{background:#8b949e}
.project-meta{display:flex;gap:3px;flex-wrap:wrap;margin-bottom:4px}
.tag{font-size:9px;padding:1px 5px;border-radius:8px;background:#1f6feb33;color:#58a6ff;border:1px solid #1f6feb44}
.tag.rule-tag{background:#23863633;color:#3fb950;border-color:#23863644}
.project-details{font-size:10px;color:#8b949e;display:flex;flex-direction:column;gap:1px}
.branch{color:#d2a8ff}.commit{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:250px;display:inline-block}.time{color:#484f58}
.dirty-files{margin:4px 0;display:flex;flex-wrap:wrap;gap:2px}
.dirty-file{font-size:9px;padding:1px 5px;border-radius:4px}
.dirty-file.modified{background:#d2992222;color:#d29922}.dirty-file.untracked{background:#1f6feb22;color:#58a6ff}
.project-actions{display:flex;gap:4px;margin-top:6px;padding-top:6px;border-top:1px solid #21262d;opacity:0.7;transition:opacity .15s}
.project-card:hover .project-actions{opacity:1}
.panel{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;margin-bottom:10px}
.panel h3{font-size:11px;color:#8b949e;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.sys-item{display:flex;align-items:center;gap:6px;padding:3px 0;font-size:11px;border-bottom:1px solid #21262d}
.sys-item:last-child{border-bottom:none}.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dot.on{background:#3fb950}.dot.off{background:#484f58}
.sys-name{color:#c9d1d9;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sys-meta{color:#484f58;font-size:10px;white-space:nowrap}
.stat-row{display:flex;justify-content:space-between;padding:3px 0;font-size:11px;border-bottom:1px solid #21262d}
.stat-row:last-child{border-bottom:none}.stat-label{color:#8b949e}.stat-value{color:#c9d1d9}
.chart-section{background:#161b22;border:1px solid #30363d;border-radius:8px;padding:10px;margin-bottom:12px}
.chart-section h3{font-size:11px;color:#8b949e;margin-bottom:8px;text-transform:uppercase;letter-spacing:.5px}
.chart-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}@media(max-width:800px){.chart-grid{grid-template-columns:1fr}}
.session-log pre{color:#8b949e;font-family:monospace;white-space:pre-wrap;font-size:9px}
.toast{position:fixed;bottom:16px;right:16px;padding:8px 16px;border-radius:8px;font-size:12px;background:#238636;color:#fff;display:none;z-index:999;box-shadow:0 4px 12px rgba(0,0,0,.4)}
.toast.error{background:#da3633}.toast.show{display:block;animation:fadeIn .2s}
@keyframes fadeIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.modal-overlay{display:none;position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.6);z-index:100}
.modal-overlay.show{display:flex;align-items:center;justify-content:center}
.modal{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:20px;max-width:600px;width:90%;max-height:80vh;overflow-y:auto}
.modal h2{font-size:15px;margin-bottom:10px}.modal pre{font-size:11px;color:#8b949e;margin:6px 0;white-space:pre-wrap}
.modal-actions{display:flex;gap:6px;margin-top:12px;justify-content:flex-end}
.hidden{display:none!important}.last-updated{text-align:right;font-size:10px;color:#484f58;margin-top:4px}
.metrics-info{font-size:10px;color:#484f58;margin-top:4px}
</style></head><body>
<div class="container">
  <div class="header">
    <h1>Project Dashboard <span style="font-size:10px;color:#484f58;font-weight:400">v4.0</span></h1>
    <div class="header-stats">
      <span class="stat">${total} projects</span>
      <span class="stat"><span class="dot on" style="display:inline-block;vertical-align:middle"></span> ${gitClean}</span>
      <span class="stat"><span class="dot" style="display:inline-block;vertical-align:middle;background:#d29922"></span> ${unclean}</span>
      <span class="stat"><span class="dot off" style="display:inline-block;vertical-align:middle"></span> ${noGit}</span>
      <span class="stat">${metrics.length} points</span>
    </div>
  </div>

  <div class="chart-section">
    <h3>Metrics (last 24h)</h3>
    <div class="chart-grid">
      <div>${renderDirtyChart(metrics)}</div>
      <div>${renderCpuChart(metrics)}</div>
      <div>${renderDiskChart(metrics)}</div>
      <div>${renderPm2Chart(metrics)}</div>
    </div>
    <div class="metrics-info">Collected every 30 min via pm2 | ${metrics.length} data points</div>
  </div>

  <div class="dashboard-grid">
    <div class="main-col">
      <input type="text" class="search-bar" placeholder="Search projects..." oninput="filterProjects(this.value)">
      <div class="actions">
        <button class="btn primary" onclick="location.reload()">refresh</button>
        <button class="btn" onclick="window.open('/api/raw-status')">json</button>
        <button class="btn" onclick="showHelp()">help</button>
        <span style="flex:1"></span>
        <span class="last-updated" id="lastUpdated">${new Date().toLocaleTimeString('ru-RU')}</span>
      </div>
      <div class="project-grid" id="projectGrid">${projectRows}</div>
    </div>
    <div class="side-col">
      <div class="panel"><h3>System</h3>
        <div class="stat-row"><span class="stat-label">CPU</span><span class="stat-value">${stats.cpu}</span></div>
        <div class="stat-row"><span class="stat-label">Disk</span><span class="stat-value">${stats.disk}</span></div>
        <div class="stat-row"><span class="stat-label">Uptime</span><span class="stat-value">${stats.uptime}</span></div>
      </div>
      <div class="panel"><h3>Backup</h3>
        <div class="stat-row"><span class="stat-label">Last</span><span class="stat-value" style="color:#3fb950">${backup.lastBackup}</span></div>
        <div class="stat-row"><span class="stat-label">Age</span><span class="stat-value" style="color:#8b949e">${backup.age}</span></div>
      </div>
      <div class="panel"><h3>pm2 (${pm2.length})</h3>${pm2Rows||'<div style="font-size:11px;color:#484f58;">No data</div>'}</div>
      <div class="panel"><h3>launchd (${launchd.length})</h3>${launchdRows||'<div style="font-size:11px;color:#484f58;">No data</div>'}</div>
      <div class="panel session-log"><h3>Sessions</h3><pre>${logLines||'No entries.'}</pre></div>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>
<div class="modal-overlay" id="modal"><div class="modal"><h2 id="modalTitle">...</h2><pre id="modalBody"></pre><div class="modal-actions"><button class="btn" onclick="closeModal()">Close</button></div></div></div>
<script>

function showFiles(name) {
  fetch('/api/open/' + name).then(r => r.json()).then(d => {
    document.getElementById('modalTitle').textContent = name;
    document.getElementById('modalBody').textContent = d.files.join('\\n');
    document.getElementById('modal').className = 'modal-overlay show';
  });
}
function commitProject(name) {
  showToast('Committing...');
  fetch('/api/commit/' + name).then(r => r.json()).then(d => {
    showToast(d.message, d.error);
    setTimeout(() => location.reload(), 1500);
  });
}
function verifyProject(name) {
  showToast('Verifying...');
  fetch('/api/verify/' + name).then(r => r.json()).then(d => {
    document.getElementById('modalTitle').textContent = 'Verify: ' + name;
    document.getElementById('modalBody').textContent = d.result;
    document.getElementById('modal').className = 'modal-overlay show';
  });
}
function filterProjects(q) {
  const ql = q.toLowerCase();
  document.querySelectorAll('.project-card').forEach(c => {
    c.style.display = c.dataset.dir.includes(ql) ? '' : 'none';
  });
}
function showToast(m, e) {
  const t = document.getElementById('toast');
  t.textContent = m; t.className = 'toast show' + (e ? ' error' : '');
  setTimeout(() => t.className = 'toast', 3000);
}
function closeModal() { document.getElementById('modal').className = 'modal-overlay'; }
function showHelp() {
  document.getElementById('modalTitle').textContent = 'How to use';
  document.getElementById('modalBody').textContent = 
    'Click on a project card -> opens in Interpreter, I start working\\n' +
    'files -> show project files\\n' +
    'commit -> git add + commit\\n' +
    'verify -> check git status + python syntax\\n' +
    'refresh -> reload\\n' +
    'json -> raw API data\\n' +
    '\\nAuto-refresh: 30s\\nMetrics: every 30 min\\nDaily update: 17:00\\nBackup: 18:00';
  document.getElementById('modal').className = 'modal-overlay show';
}

</script></body></html>`;
}

// ─── Server ─────────────────────────────────────────
const server = createServer((req, res) => {
  const url = new URL(req.url, 'http://localhost:' + PORT);
  const path = url.pathname;
  res.setHeader('Access-Control-Allow-Origin', '*');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  // API: start project — opens project via CLI + writes signal file
  if (path.startsWith('/api/start/')) {
    const name = decodeURIComponent(path.slice(11));
    const projectPath = join(DEV, name);
    const meta = projectMeta[name] || {};
    const friendlyName = meta.name || name;
    try {
      execSync('/Users/vitaliyr/.local/bin/start-project.sh ' + name, { timeout: 10000, stdio: 'pipe' });
    } catch(e) {}
    try {
      execSync('interpreter-app tools builtin-interpreter interpreter_set --json ' + JSON.stringify({path: 'tree.tabs', value: [{path: projectPath}]}), { timeout: 5000, stdio: 'pipe' });
    } catch(e) {}
    res.writeHead(200, {'Content-Type':'application/json'});
    res.end(JSON.stringify({name, friendlyName, message: 'opened ' + friendlyName + '!'}));
    return;
  }

  // API: open project files
  if (path.startsWith('/api/open/')) {
    const name = decodeURIComponent(path.slice(10));
    try { const files = readdirSync(join(DEV, name)).filter(f => !f.startsWith('.')).slice(0, 30); res.writeHead(200,{'Content-Type':'application/json'}); res.end(JSON.stringify({name, files})); }
    catch { res.writeHead(404); res.end(JSON.stringify({error:'Not found'})); }
    return;
  }

  // API: commit
  if (path.startsWith('/api/commit/')) {
    const name = decodeURIComponent(path.slice(11));
    const r = sh('git add -A && git commit -m "auto: dashboard commit" --no-verify', join(DEV, name));
    res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify({message: r.includes('nothing') ? 'Nothing to commit' : 'Committed ' + name}));
    return;
  }

  // API: verify
  if (path.startsWith('/api/verify/')) {
    const name = decodeURIComponent(path.slice(13));
    const p = join(DEV, name);
    let result = '--- Git ---\n' + (sh('git status --short', p) || 'Clean') + '\n\n--- Python ---\n';
    const pyFiles = readdirSync(p).filter(f => f.endsWith('.py')).slice(0, 5);
    for (const f of pyFiles) { const r = sh('python3 -m py_compile "' + join(p, f) + '" 2>&1', p); result += r ? 'FAIL ' + f + ': ' + r : 'OK ' + f; result += '\n'; }
    res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify({result}));
    return;
  }

  // API: raw status
  if (path === '/api/raw-status') {
    res.writeHead(200, {'Content-Type':'application/json'});
    res.end(JSON.stringify({projects: getProjects(), system: getSystemStats(), pm2: getPm2Status(), launchd: getLaunchdStatus(), backup: getBackupInfo(), metrics: getMetrics().slice(-48), time: new Date().toISOString()}, null, 2));
    return;
  }

  // Serve HTML
  res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'});
  res.end(renderHTML());
});

// Collect on startup + every 30 min
collectMetrics();
setInterval(collectMetrics, 1800000);

server.listen(PORT, () => console.log('Dashboard v4.0 on http://localhost:' + PORT));
