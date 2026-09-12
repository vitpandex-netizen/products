// UZ IT Jobs — Telegram Mini App Client JS

const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
}

// Автоматическое определение пути API для поддержки Funnel /uzjobs/
const BASE_PATH = window.location.pathname.includes('/uzjobs') ? '/uzjobs/api' : '/api';

// Авторизованный запрос с передачей Telegram initData (Whitelist security)
async function authFetch(url, options = {}) {
  options.headers = options.headers || {};
  if (tg?.initData) {
    options.headers['X-Telegram-Init-Data'] = tg.initData;
  }
  const urlParams = new URLSearchParams(window.location.search);
  const devKey = urlParams.get('dev_key');
  if (devKey) {
    options.headers['X-Dev-Key'] = devKey;
  }
  const res = await fetch(url, options);
  if (res.status === 403) {
    showAccessDeniedModal();
    throw new Error('403 Forbidden: Доступ запрещен Whitelist');
  }
  return res;
}

function showAccessDeniedModal() {
  const container = document.querySelector('.container') || document.body;
  container.innerHTML = `
    <div style="padding: 60px 20px; text-align: center; color: var(--tg-theme-text-color, #fff);">
      <div style="font-size: 64px; margin-bottom: 20px;">⛔</div>
      <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 12px;">Доступ ограничен</h2>
      <p style="font-size: 14px; opacity: 0.7; line-height: 1.5; margin-bottom: 24px;">
        Этот проект находится в закрытом режиме разработки (Enterprise Whitelist).<br>
        Доступ разрешен только авторизованным пользователям через бота <b>@hhjob_ai_bot</b>.
      </p>
      <div style="font-size: 12px; opacity: 0.5; font-family: monospace;">Security Policy: Private-Only</div>
    </div>
  `;
}

// Утилита для тактильного отклика Telegram
function haptic(type = 'light') {
  if (tg?.HapticFeedback) {
    if (type === 'selection') tg.HapticFeedback.selectionChanged();
    else tg.HapticFeedback.impactOccurred(type);
  }
}

// Состояние приложения
const state = {
  activeTab: 'jobs',
  category: 'all',
  searchQuery: '',
  sort: 'score',
  minScore: 0.0,
  offset: 0,
  limit: 20,
  total: 0,
  vacancies: [],
  selectedVacancy: null,
  coverLetterLang: 'ru',
  stats: null,
  analytics: null
};

// DOM Элементы
const elements = {
  searchInput: document.getElementById('search-input'),
  searchClear: document.getElementById('search-clear'),
  categoryChips: document.getElementById('category-chips'),
  resultsCount: document.getElementById('results-count'),
  sortSelect: document.getElementById('sort-select'),
  vacanciesList: document.getElementById('vacancies-list'),
  loadMoreContainer: document.getElementById('load-more-container'),
  btnLoadMore: document.getElementById('btn-load-more'),
  badgeTotalCount: document.getElementById('badge-total-count'),

  // Табы
  navButtons: document.querySelectorAll('.nav-item'),
  tabPanes: document.querySelectorAll('.tab-pane'),

  // Аналитика
  statTotalVacancies: document.getElementById('stat-total-vacancies'),
  statTotalCompanies: document.getElementById('stat-total-companies'),
  statGoodMatches: document.getElementById('stat-good-matches'),
  topEmployersList: document.getElementById('top-employers-list'),
  techClustersList: document.getElementById('tech-clusters-list'),

  // Профиль
  thresholdSlider: document.getElementById('threshold-slider'),
  thresholdVal: document.getElementById('threshold-val'),

  // Модалка
  modal: document.getElementById('vacancy-modal'),
  modalTitle: document.getElementById('modal-title'),
  modalCompany: document.getElementById('modal-company'),
  modalSalary: document.getElementById('modal-salary'),
  modalLocation: document.getElementById('modal-location'),
  modalMatchScore: document.getElementById('modal-match-score'),
  modalDesc: document.getElementById('modal-description'),
  modalLink: document.getElementById('modal-external-link'),
  btnCloseModal: document.getElementById('btn-close-modal'),
  clText: document.getElementById('cl-text'),
  btnCopyCl: document.getElementById('btn-copy-cl'),
  clLangRu: document.getElementById('cl-lang-ru'),
  clLangUz: document.getElementById('cl-lang-uz'),
};

// Форматирование скора
function formatScore(score) {
  const pct = Math.round((score || 0) * 100);
  if (pct >= 50) return { text: `🔥 ${pct}% Match`, cls: 'score-high' };
  if (pct >= 30) return { text: `⭐ ${pct}% Match`, cls: 'score-mid' };
  return { text: `${pct}%`, cls: 'score-low' };
}

// Форматирование дат
function formatDate(dateStr) {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' });
}

// Загрузка вакансий
async function fetchVacancies(append = false) {
  if (!append) {
    state.offset = 0;
    elements.vacanciesList.innerHTML = `
      <div class="loading-state">
        <div class="spinner"></div>
        <p>Поиск вакансий по Узбекистану...</p>
      </div>`;
  }

  let cat = state.category;
  let minScore = state.minScore;

  if (state.category === 'top_match') {
    cat = 'all';
    minScore = 0.30;
  }

  const params = new URLSearchParams({
    offset: state.offset,
    limit: state.limit,
    sort: state.sort,
    category: cat,
    min_score: minScore
  });

  if (state.searchQuery.trim()) {
    params.append('q', state.searchQuery.trim());
  }

  try {
    const res = await authFetch(`${BASE_PATH}/vacancies?${params.toString()}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    state.total = data.total;
    if (append) {
      state.vacancies.push(...data.items);
    } else {
      state.vacancies = data.items;
    }

    renderVacancies(append);
  } catch (err) {
    console.error('Fetch vacancies error:', err);
    elements.vacanciesList.innerHTML = `
      <div class="loading-state text-gold">
        <p>Не удалось связаться с сервером вакансий.</p>
        <button class="btn-load-more" style="margin-top:12px;" onclick="fetchVacancies()">Повторить попытку</button>
      </div>`;
  }
}

// Отрисовка списка вакансий
function renderVacancies(append = false) {
  elements.resultsCount.textContent = `Найдено: ${state.total} вакансий`;

  if (!append) {
    elements.vacanciesList.innerHTML = '';
  }

  if (state.vacancies.length === 0) {
    elements.vacanciesList.innerHTML = `
      <div class="loading-state">
        <div style="font-size:36px; margin-bottom:8px;">🔍</div>
        <p>По вашему запросу вакансий не найдено.</p>
        <p style="font-size:11px; margin-top:4px;">Попробуйте изменить фильтр или категорию.</p>
      </div>`;
    elements.loadMoreContainer.classList.add('hidden');
    return;
  }

  const startIndex = append ? state.offset : 0;
  const newItems = state.vacancies.slice(startIndex);

  newItems.forEach(vac => {
    const card = document.createElement('div');
    card.className = 'vacancy-card';
    card.dataset.id = vac.id;

    const scoreInfo = formatScore(vac.matched_score);
    const dateFormatted = formatDate(vac.created_at);

    let catTagsHtml = '';
    (vac.categories || []).forEach(c => {
      const catMap = {
        'c_level': '👔 C-Level',
        'devops': '🛠 DevOps/SRE',
        'security': '🔒 Инфобез',
        'dev': '💻 Dev',
        'enterprise': '🏢 1C/ERP'
      };
      if (catMap[c]) {
        catTagsHtml += `<span class="tag-badge">${catMap[c]}</span>`;
      }
    });

    card.innerHTML = `
      <div class="card-top">
        <span class="company-name">${vac.company || 'Компания Узбекистана'}</span>
        <span class="score-badge ${scoreInfo.cls}">${scoreInfo.text}</span>
      </div>
      <div class="vac-title">${vac.title}</div>
      <div class="vac-location">📍 ${vac.location || 'Ташкент'} &bull; ${dateFormatted}</div>
      <div class="card-tags">
        ${catTagsHtml}
      </div>
    `;

    card.addEventListener('click', () => openVacancyModal(vac.id));
    elements.vacanciesList.appendChild(card);
  });

  if (state.vacancies.length < state.total) {
    elements.loadMoreContainer.classList.remove('hidden');
  } else {
    elements.loadMoreContainer.classList.add('hidden');
  }
}

// Загрузка сводки и аналитики
async function fetchStatsAndAnalytics() {
  try {
    const [statsRes, analyticsRes] = await Promise.all([
      authFetch(`${BASE_PATH}/stats`),
      authFetch(`${BASE_PATH}/analytics`)
    ]);

    if (statsRes.ok) {
      state.stats = await statsRes.json();
      elements.badgeTotalCount.textContent = `${state.stats.total_vacancies} вак.`;
      elements.statTotalVacancies.textContent = state.stats.total_vacancies;
      elements.statTotalCompanies.textContent = `${state.stats.companies_count}+`;
      elements.statGoodMatches.textContent = state.stats.good_matches;
    }

    if (analyticsRes.ok) {
      state.analytics = await analyticsRes.json();
      renderAnalytics(state.analytics);
    }
  } catch (err) {
    console.error('Stats & Analytics error:', err);
  }
}

// Отрисовка вкладки аналитики
function renderAnalytics(data) {
  elements.topEmployersList.innerHTML = '';
  data.top_employers.forEach(emp => {
    const item = document.createElement('div');
    item.className = 'employer-item';
    item.innerHTML = `
      <span class="emp-name">${emp.name}</span>
      <span class="emp-count">${emp.count} вак.</span>
    `;
    item.addEventListener('click', () => {
      haptic('selection');
      state.searchQuery = emp.name;
      elements.searchInput.value = emp.name;
      elements.searchClear.classList.remove('hidden');
      switchTab('jobs');
      fetchVacancies();
    });
    elements.topEmployersList.appendChild(item);
  });

  elements.techClustersList.innerHTML = '';
  const maxCount = Math.max(...data.tech_clusters.map(t => t.count), 1);
  data.tech_clusters.forEach(cluster => {
    const pct = Math.round((cluster.count / maxCount) * 100);
    const item = document.createElement('div');
    item.className = 'tech-item';
    item.innerHTML = `
      <div class="tech-header">
        <span>${cluster.tech}</span>
        <span style="color:${cluster.color}; font-weight:700;">${cluster.count} упоминаний</span>
      </div>
      <div class="tech-bar-bg">
        <div class="tech-bar-fill" style="width:${pct}%; background-color:${cluster.color};"></div>
      </div>
    `;
    elements.techClustersList.appendChild(item);
  });
}

// Открытие модального окна вакансии
async function openVacancyModal(id) {
  haptic('selection');
  elements.modal.classList.remove('hidden');
  document.body.style.overflow = 'hidden';

  elements.modalTitle.textContent = 'Загрузка...';
  elements.modalCompany.textContent = '—';
  elements.modalSalary.textContent = '';
  elements.modalDesc.textContent = 'Получение полного описания с US Server...';
  elements.clText.value = 'Подготовка персонального отклика...';

  try {
    const res = await authFetch(`${BASE_PATH}/vacancies/${id}`);
    if (!res.ok) throw new Error('Not found');
    const vac = await res.json();
    state.selectedVacancy = vac;

    const scoreInfo = formatScore(vac.matched_score);
    elements.modalTitle.textContent = vac.title;
    elements.modalCompany.textContent = vac.company || 'Компания Узбекистана';
    elements.modalLocation.textContent = vac.location || 'Ташкент';
    elements.modalMatchScore.textContent = scoreInfo.text;
    elements.modalMatchScore.className = `score-badge ${scoreInfo.cls}`;

    let salaryText = '💰 Зарплата не указана (по результатам собеседования)';
    if (vac.salary_from || vac.salary_to) {
      const cur = (vac.salary_currency || 'UZS').toUpperCase();
      salaryText = `💰 ${vac.salary_from ? 'от ' + vac.salary_from.toLocaleString() : ''} ${vac.salary_to ? 'до ' + vac.salary_to.toLocaleString() : ''} ${cur}`;
    }
    elements.modalSalary.textContent = salaryText;

    elements.modalDesc.textContent = vac.clean_description || 'Детальное описание доступно по ссылке на сайте работодателя.';
    elements.modalLink.href = vac.url || `https://hh.ru/vacancy/${vac.id}`;

    generateCoverLetter();
  } catch (err) {
    elements.modalDesc.textContent = 'Ошибка загрузки данных вакансии.';
  }
}

// Генерация отклика
async function generateCoverLetter() {
  if (!state.selectedVacancy) return;
  try {
    const res = await authFetch(`${BASE_PATH}/cover-letter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: state.selectedVacancy.title,
        company: state.selectedVacancy.company || 'Работодатель',
        lang: state.coverLetterLang
      })
    });
    if (res.ok) {
      const d = await res.json();
      elements.clText.value = d.cover_letter;
    }
  } catch (e) {
    console.error('CL error:', e);
  }
}

// Закрытие модального окна
function closeModal() {
  haptic('light');
  elements.modal.classList.add('hidden');
  document.body.style.overflow = '';
  state.selectedVacancy = null;
}

// Переключение табов
function switchTab(tabId) {
  haptic('selection');
  state.activeTab = tabId;

  elements.navButtons.forEach(btn => {
    btn.classList.toggle('active', btn.dataset.tab === tabId);
  });

  elements.tabPanes.forEach(pane => {
    pane.classList.toggle('active', pane.id === `tab-${tabId}`);
    pane.classList.toggle('hidden', pane.id !== `tab-${tabId}`);
  });

  const isJobs = tabId === 'jobs';
  document.getElementById('search-container').style.display = isJobs ? 'flex' : 'none';
  document.getElementById('category-chips').style.display = isJobs ? 'flex' : 'none';
}

// Обработчики событий
function setupEventListeners() {
  elements.navButtons.forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.tab));
  });

  elements.categoryChips.addEventListener('click', e => {
    const chip = e.target.closest('.chip');
    if (!chip) return;
    haptic('selection');

    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    chip.classList.add('active');

    state.category = chip.dataset.category;
    fetchVacancies();
  });

  let searchTimer;
  elements.searchInput.addEventListener('input', e => {
    const val = e.target.value;
    elements.searchClear.classList.toggle('hidden', !val);
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.searchQuery = val;
      fetchVacancies();
    }, 350);
  });

  elements.searchClear.addEventListener('click', () => {
    elements.searchInput.value = '';
    elements.searchClear.classList.add('hidden');
    state.searchQuery = '';
    fetchVacancies();
  });

  elements.sortSelect.addEventListener('change', e => {
    state.sort = e.target.value;
    fetchVacancies();
  });

  elements.btnLoadMore.addEventListener('click', () => {
    haptic('light');
    state.offset += state.limit;
    fetchVacancies(true);
  });

  elements.btnCloseModal.addEventListener('click', closeModal);
  elements.modal.addEventListener('click', e => {
    if (e.target === elements.modal) closeModal();
  });

  elements.clLangRu.addEventListener('click', () => {
    haptic('selection');
    state.coverLetterLang = 'ru';
    elements.clLangRu.classList.add('active');
    elements.clLangUz.classList.remove('active');
    generateCoverLetter();
  });

  elements.clLangUz.addEventListener('click', () => {
    haptic('selection');
    state.coverLetterLang = 'uz';
    elements.clLangUz.classList.add('active');
    elements.clLangRu.classList.remove('active');
    generateCoverLetter();
  });

  elements.btnCopyCl.addEventListener('click', () => {
    haptic('notification');
    elements.clText.select();
    navigator.clipboard.writeText(elements.clText.value);
    const originalText = elements.btnCopyCl.textContent;
    elements.btnCopyCl.textContent = '✓ Скопировано в буфер!';
    elements.btnCopyCl.style.borderColor = 'var(--emerald)';
    elements.btnCopyCl.style.color = 'var(--emerald)';
    setTimeout(() => {
      elements.btnCopyCl.textContent = originalText;
      elements.btnCopyCl.style.borderColor = '';
      elements.btnCopyCl.style.color = '';
    }, 2000);
  });

  elements.thresholdSlider.addEventListener('input', e => {
    const val = parseInt(e.target.value);
    elements.thresholdVal.textContent = `${val}%`;
    state.minScore = val / 100;
  });

  elements.thresholdSlider.addEventListener('change', () => {
    haptic('selection');
    fetchVacancies();
  });
}

// Запуск приложения
document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  fetchVacancies();
  fetchStatsAndAnalytics();
});
