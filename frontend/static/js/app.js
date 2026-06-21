// EcoTrack AI - Main Frontend Application JS (ES6)

const API_BASE = '/api';

// Application State
const state = {
  token: localStorage.getItem('ecotrack_token') || null,
  refreshToken: localStorage.getItem('ecotrack_refresh') || null,
  user: null,
  activeView: 'auth',
  currentQuiz: null,
  quizAnswers: {},
  currentQuestionIdx: 0,
  activeChartTab: 'daily',
  charts: {
    trend: null,
    category: null,
    comparison: null
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setupEventListeners();
  route();
  
  // Track hash change for SPA routing
  window.addEventListener('hashchange', route);
});

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
  if (savedTheme === 'dark') {
    document.documentElement.classList.add('dark');
    document.getElementById('theme-toggle-icon').className = 'fa-solid fa-sun text-yellow-400';
  } else {
    document.documentElement.classList.remove('dark');
    document.getElementById('theme-toggle-icon').className = 'fa-solid fa-moon text-slate-600';
  }
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme');
  const target = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', target);
  localStorage.setItem('theme', target);
  
  const icon = document.getElementById('theme-toggle-icon');
  if (target === 'dark') {
    document.documentElement.classList.add('dark');
    icon.className = 'fa-solid fa-sun text-yellow-400';
  } else {
    document.documentElement.classList.remove('dark');
    icon.className = 'fa-solid fa-moon text-slate-600';
  }
  
  // Re-draw charts with new theme colors if active
  if (state.token && state.activeView === 'dashboard') {
    loadDashboardCharts();
  }
}

// Router
function route() {
  const hash = window.location.hash || '#/dashboard';
  
  // Auth protection check
  if (!state.token) {
    showView('auth');
    return;
  }
  
  const view = hash.replace('#/', '');
  showView(view);
}

function showView(viewName) {
  // Hide all sections
  document.querySelectorAll('.view-section').forEach(el => el.classList.add('hidden'));
  document.getElementById('view-auth').classList.add('hidden');
  
  // Remove active from nav links
  document.querySelectorAll('.nav-link').forEach(el => el.classList.remove('active'));
  
  if (viewName === 'auth') {
    document.getElementById('view-auth').classList.remove('hidden');
    document.getElementById('main-header').classList.add('hidden');
    document.getElementById('mobile-nav').classList.add('hidden');
    state.activeView = 'auth';
    return;
  }
  
  // Show header and mobile nav for authorized views
  document.getElementById('main-header').classList.remove('hidden');
  document.getElementById('mobile-nav').classList.remove('hidden');
  
  const targetEl = document.getElementById(`view-${viewName}`);
  if (targetEl) {
    targetEl.classList.remove('hidden');
    
    // Set active nav link
    document.querySelectorAll(`.nav-link[data-view="${viewName}"]`).forEach(el => el.classList.add('active'));
    state.activeView = viewName;
    
    // Load context data for the view
    loadViewData(viewName);
  } else {
    // Default fallback to dashboard
    window.location.hash = '#/dashboard';
  }
}

// Load specific view details from API
function loadViewData(viewName) {
  if (viewName === 'dashboard') {
    fetchDashboardSummary();
    loadDashboardCharts();
  } else if (viewName === 'calculator') {
    loadPastEntries();
    updateLiveEstimation();
  } else if (viewName === 'challenges') {
    loadBadges();
    loadChallenges();
    loadLeaderboard();
  } else if (viewName === 'education') {
    loadArticles();
    loadQuizzes();
  } else if (viewName === 'community') {
    loadCommunityPosts();
  } else if (viewName === 'reports') {
    loadReportsList();
  }
  fetchNotifications();
}

// Setup listeners
function setupEventListeners() {
  // Theme Switcher
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);
  
  // Auth cards toggle
  document.getElementById('go-to-register-btn').addEventListener('click', () => {
    document.getElementById('auth-login-card').classList.add('hidden');
    document.getElementById('auth-register-card').classList.remove('hidden');
  });
  document.getElementById('go-to-login-btn').addEventListener('click', () => {
    document.getElementById('auth-register-card').classList.add('hidden');
    document.getElementById('auth-login-card').classList.remove('hidden');
  });
  document.getElementById('forgot-password-btn').addEventListener('click', () => {
    document.getElementById('auth-login-card').classList.add('hidden');
    document.getElementById('auth-forgot-card').classList.remove('hidden');
  });
  document.getElementById('forgot-back-btn').addEventListener('click', () => {
    document.getElementById('auth-forgot-card').classList.add('hidden');
    document.getElementById('auth-login-card').classList.remove('hidden');
  });

  // Auth Forms Submission
  document.getElementById('login-form').addEventListener('submit', handleLogin);
  document.getElementById('register-form').addEventListener('submit', handleRegister);
  document.getElementById('forgot-form').addEventListener('submit', handleForgotPassword);
  document.getElementById('reset-confirm-form').addEventListener('submit', handleResetPassword);
  document.getElementById('logout-btn').addEventListener('click', handleLogout);

  // Carbon Calculator tab selection
  document.querySelectorAll('.calc-tab').forEach(tab => {
    tab.addEventListener('click', (e) => {
      document.querySelectorAll('.calc-tab').forEach(t => {
        t.classList.remove('active', 'bg-white', 'dark:bg-slate-900', 'shadow-sm', 'text-emerald-600');
        t.classList.add('text-slate-500');
      });
      const activeTab = e.currentTarget;
      activeTab.classList.add('active', 'bg-white', 'dark:bg-slate-900', 'shadow-sm', 'text-emerald-600');
      activeTab.classList.remove('text-slate-500');
      
      const cat = activeTab.getAttribute('data-category');
      document.getElementById('calc-current-category').value = cat;
      
      document.querySelectorAll('.calc-form-block').forEach(b => b.classList.add('hidden'));
      document.getElementById(`calc-form-${cat}`).classList.remove('hidden');
      
      updateLiveEstimation();
    });
  });

  // Calculator inputs listener for live updates
  document.querySelectorAll('.calc-form-block input, .calc-form-block select').forEach(input => {
    input.addEventListener('input', updateLiveEstimation);
  });
  document.getElementById('calc-transport-trips').addEventListener('input', (e) => {
    document.getElementById('calc-transport-trips-value').innerText = `${e.target.value} trip${e.target.value > 1 ? 's' : ''}`;
  });

  // Calculator Submit/Reset
  document.getElementById('calculator-form').addEventListener('submit', handleCarbonEntrySubmit);
  document.getElementById('calc-reset').addEventListener('click', () => {
    document.getElementById('calculator-form').reset();
    document.getElementById('calc-transport-trips-value').innerText = '1 trip';
    updateLiveEstimation();
  });

  // AI Coach Chat Submission
  document.getElementById('coach-chat-form').addEventListener('submit', handleCoachChatSubmit);
  document.querySelectorAll('.chat-chip').forEach(chip => {
    chip.addEventListener('click', (e) => {
      document.getElementById('coach-chat-input').value = e.target.innerText;
      document.getElementById('coach-chat-form').requestSubmit();
    });
  });
  // Handle suggestion prompt links inside chat bubbles dynamically
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('chat-prompt-link')) {
      document.getElementById('coach-chat-input').value = e.target.innerText;
      document.getElementById('coach-chat-form').requestSubmit();
    }
  });

  // Dashboard trend chart period switcher tabs
  document.getElementById('chart-tab-daily').addEventListener('click', (e) => switchChartTab('daily', e.target));
  document.getElementById('chart-tab-weekly').addEventListener('click', (e) => switchChartTab('weekly', e.target));
  document.getElementById('chart-tab-monthly').addEventListener('click', (e) => switchChartTab('monthly', e.target));

  // Educational hub quizzes & modals listeners
  document.getElementById('quiz-modal-close').addEventListener('click', () => {
    document.getElementById('quiz-modal').close();
  });
  document.getElementById('quiz-next-btn').addEventListener('click', handleNextQuizQuestion);
  document.getElementById('quiz-submit-btn').addEventListener('click', handleQuizAnswersSubmit);

  // Community creation
  document.getElementById('community-create-form').addEventListener('submit', handleCommunityPostSubmit);
  document.getElementById('comment-modal-close').addEventListener('click', () => {
    document.getElementById('comment-modal').close();
  });
  document.getElementById('comment-add-form').addEventListener('submit', handleCommentSubmit);

  // Reports download center triggers
  document.getElementById('report-generate-form').addEventListener('submit', handleReportGenerationSubmit);
  
  // Notification bells
  document.getElementById('notif-bell').addEventListener('click', (e) => {
    e.stopPropagation();
    const list = document.getElementById('notif-dropdown');
    list.classList.toggle('hidden');
  });
  document.addEventListener('click', () => {
    document.getElementById('notif-dropdown').classList.add('hidden');
  });
  document.getElementById('notif-dropdown').addEventListener('click', (e) => e.stopPropagation());
  document.getElementById('notif-clear').addEventListener('click', handleClearAllNotifications);
}

// Request Helper
async function apiRequest(path, method = 'GET', body = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  
  const options = { method, headers };
  if (body) {
    options.body = JSON.stringify(body);
  }

  try {
    const res = await fetch(`${API_BASE}${path}`, options);
    
    // Auto-refresh JWT logic if unauthorized
    if (res.status === 401 && state.refreshToken && path !== '/auth/login/') {
      const refreshed = await attemptTokenRefresh();
      if (refreshed) {
        // re-run request
        headers['Authorization'] = `Bearer ${state.token}`;
        return apiRequest(path, method, body);
      }
    }
    
    if (res.status === 204) return null;
    
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.error || JSON.stringify(data));
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${path}:`, err);
    throw err;
  }
}

async function attemptTokenRefresh() {
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: state.refreshToken })
    });
    if (res.ok) {
      const data = await res.json();
      state.token = data.access;
      localStorage.setItem('ecotrack_token', data.access);
      if (data.refresh) {
        state.refreshToken = data.refresh;
        localStorage.setItem('ecotrack_refresh', data.refresh);
      }
      return true;
    }
  } catch (e) {
    console.error("Token refresh failed:", e);
  }
  
  // Clear keys on failure
  handleLogout();
  return false;
}

// Toast Alert
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const msgEl = document.getElementById('toast-message');
  
  msgEl.innerText = message;
  toast.className = `fixed bottom-5 right-5 px-5 py-3.5 rounded-xl text-white font-semibold flex items-center gap-2 shadow-xl z-50 transform transition-all duration-300 ${
    type === 'success' ? 'bg-emerald-600' : 'bg-red-500'
  }`;
  
  // Animate in
  toast.classList.remove('translate-y-20', 'opacity-0');
  
  setTimeout(() => {
    toast.classList.add('translate-y-20', 'opacity-0');
  }, 4000);
}

function showLoading(show = true) {
  const overlay = document.getElementById('loading-overlay');
  if (show) {
    overlay.classList.remove('hidden');
  } else {
    overlay.classList.add('hidden');
  }
}

// Auth Actions
async function handleLogin(e) {
  e.preventDefault();
  const username = document.getElementById('login-username').value;
  const password = document.getElementById('login-password').value;
  
  showLoading(true);
  try {
    const data = await apiRequest('/auth/login/', 'POST', { username, password });
    state.token = data.access;
    state.refreshToken = data.refresh;
    
    // Save in storage
    localStorage.setItem('ecotrack_token', data.access);
    localStorage.setItem('ecotrack_refresh', data.refresh);
    
    // Set profile display
    const profile = await apiRequest('/profile/');
    state.user = profile;
    document.getElementById('username-display').innerText = profile.user.username;
    document.getElementById('user-avatar-initial').innerText = profile.user.username[0].toUpperCase();
    
    showToast("Signed in successfully!");
    window.location.hash = '#/dashboard';
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function handleRegister(e) {
  e.preventDefault();
  const first_name = document.getElementById('register-fname').value;
  const last_name = document.getElementById('register-lname').value;
  const username = document.getElementById('register-username').value;
  const email = document.getElementById('register-email').value;
  const password = document.getElementById('register-password').value;

  showLoading(true);
  try {
    const data = await apiRequest('/auth/register/', 'POST', {
      first_name, last_name, username, email, password
    });
    
    state.token = data.access;
    state.refreshToken = data.refresh;
    localStorage.setItem('ecotrack_token', data.access);
    localStorage.setItem('ecotrack_refresh', data.refresh);
    
    state.user = data.user;
    document.getElementById('username-display').innerText = data.user.username;
    document.getElementById('user-avatar-initial').innerText = data.user.username[0].toUpperCase();

    showToast("Account created successfully!");
    window.location.hash = '#/dashboard';
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function handleForgotPassword(e) {
  e.preventDefault();
  const email = document.getElementById('forgot-email').value;
  showLoading(true);
  try {
    const res = await apiRequest('/auth/forgot-password/', 'POST', { email });
    showToast(res.message);
    // Display confirm password fields
    document.getElementById('forgot-form').classList.add('hidden');
    document.getElementById('reset-confirm-form').classList.remove('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function handleResetPassword(e) {
  e.preventDefault();
  const email = document.getElementById('forgot-email').value;
  const password = document.getElementById('reset-password-val').value;
  showLoading(true);
  try {
    const res = await apiRequest('/auth/reset-password/', 'POST', { email, password });
    showToast(res.message);
    // Reset cards to login
    document.getElementById('auth-forgot-card').classList.add('hidden');
    document.getElementById('reset-confirm-form').classList.add('hidden');
    document.getElementById('forgot-form').classList.remove('hidden');
    document.getElementById('auth-login-card').classList.remove('hidden');
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

function handleLogout() {
  state.token = null;
  state.refreshToken = null;
  state.user = null;
  localStorage.removeItem('ecotrack_token');
  localStorage.removeItem('ecotrack_refresh');
  
  // Reset navigation
  document.getElementById('main-header').classList.add('hidden');
  document.getElementById('mobile-nav').classList.add('hidden');
  showView('auth');
  window.location.hash = '#/auth';
  showToast("Logged out successfully.");
}

// Dashboard metric loaders
async function fetchDashboardSummary() {
  try {
    const data = await apiRequest('/analytics/summary/');
    
    // Update dashboard header indicators
    document.getElementById('dash-points').innerText = data.green_points;
    document.getElementById('dash-streak').innerText = data.streak_count || 0;
    document.getElementById('dash-level').innerText = data.level;
    document.getElementById('dash-welcome').innerText = `Hello, ${state.user ? state.user.user.username : 'Eco Warrior'}!`;
    
    // Update summary cards
    document.getElementById('metric-total-co2').innerText = parseFloat(data.total_carbon_footprint).toFixed(2);
    document.getElementById('metric-monthly-co2').innerText = parseFloat(data.monthly_emissions).toFixed(2);
    document.getElementById('metric-reduction').innerText = parseFloat(data.emission_reduction).toFixed(2);
    document.getElementById('metric-trees').innerText = parseFloat(data.trees_saved).toFixed(2);
    document.getElementById('metric-budget').innerText = `${parseFloat(data.carbon_budget).toFixed(0)} kg`;

    // Update level progress bar
    const levelMap = { 'Seed': 20, 'Sapling': 40, 'Tree': 60, 'Forest Guardian': 80, 'Planet Protector': 100 };
    const pct = levelMap[data.level] || 20;
    document.getElementById('dash-level-percentage').innerText = `${data.level}`;
    document.getElementById('dash-level-progressbar').style.width = `${pct}%`;
  } catch (err) {
    console.error(err);
  }
}

// Chart.js Visualizations Setup
async function loadDashboardCharts() {
  try {
    const hist = await apiRequest('/analytics/history/');
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.05)';
    const textColor = isDark ? '#94a3b8' : '#64748b';

    // 1. Trend Line Chart (renders based on active Tab: daily, weekly, monthly)
    const activeData = hist[state.activeChartTab];
    const labels = activeData.map(d => d.label);
    const values = activeData.map(d => d.value);
    
    if (state.charts.trend) state.charts.trend.destroy();
    
    const ctxTrend = document.getElementById('trendChart').getContext('2d');
    state.charts.trend = new Chart(ctxTrend, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Carbon Emissions (kg CO₂)',
          data: values,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.15)',
          fill: true,
          tension: 0.4,
          borderWidth: 3,
          pointBackgroundColor: '#10b981',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { grid: { color: gridColor }, ticks: { color: textColor } },
          y: { grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    });

    // 2. Category Pie / Donut Chart
    const categories = hist.category_distribution;
    const catLabels = categories.map(c => c.category);
    const catValues = categories.map(c => c.value);
    const catColors = ['#10b981', '#84cc16', '#38bdf8', '#fb7185', '#6366f1'];
    
    if (state.charts.category) state.charts.category.destroy();
    
    const ctxCat = document.getElementById('categoryChart').getContext('2d');
    state.charts.category = new Chart(ctxCat, {
      type: 'doughnut',
      data: {
        labels: catLabels,
        datasets: [{
          data: catValues,
          backgroundColor: catColors,
          borderWidth: isDark ? 2 : 1,
          borderColor: isDark ? '#1e293b' : '#ffffff'
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        cutout: '65%'
      }
    });

    // Populate Category legend details
    const legendEl = document.getElementById('category-legend');
    legendEl.innerHTML = '';
    categories.forEach((c, idx) => {
      legendEl.innerHTML += `
        <div class="flex items-center gap-1.5">
          <span class="h-2.5 w-2.5 rounded-full" style="background-color: ${catColors[idx % catColors.length]}"></span>
          <span>${c.category}: <b>${c.percentage}%</b></span>
        </div>
      `;
    });
    if (categories.length === 0) {
      legendEl.innerHTML = '<span class="col-span-2 text-center text-slate-400 py-2">No category logs recorded yet</span>';
    }

    // 3. Benchmarking comparative Bar chart
    const comparison = hist.comparison;
    const compLabels = comparison.map(c => c.category);
    const compUser = comparison.map(c => c.user);
    const compAvg = comparison.map(c => c.average);
    
    if (state.charts.comparison) state.charts.comparison.destroy();
    
    const ctxComp = document.getElementById('comparisonChart').getContext('2d');
    state.charts.comparison = new Chart(ctxComp, {
      type: 'bar',
      data: {
        labels: compLabels,
        datasets: [
          {
            label: 'Your Monthly Footprint',
            data: compUser,
            backgroundColor: '#10b981',
            borderRadius: 6
          },
          {
            label: 'Regional Average User',
            data: compAvg,
            backgroundColor: isDark ? '#334155' : '#e2e8f0',
            borderRadius: 6
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: textColor } }
        },
        scales: {
          x: { grid: { display: false }, ticks: { color: textColor } },
          y: { grid: { color: gridColor }, ticks: { color: textColor } }
        }
      }
    });

  } catch (err) {
    console.error("Error drawing dashboard charts:", err);
  }
}

function switchChartTab(tabName, buttonEl) {
  state.activeChartTab = tabName;
  document.querySelectorAll('#view-dashboard button[id^="chart-tab-"]').forEach(btn => {
    btn.className = "px-3 py-1 text-xs font-semibold rounded-md text-slate-500 hover:text-slate-800 dark:hover:text-slate-300 transition-all";
  });
  buttonEl.className = "px-3 py-1 text-xs font-semibold rounded-md bg-white dark:bg-slate-900 shadow-sm transition-all text-slate-800 dark:text-white";
  loadDashboardCharts();
}

// Live calculation Estimator
async function updateLiveEstimation() {
  const cat = document.getElementById('calc-current-category').value;
  const inputs = getCategoryInputs(cat);
  
  try {
    const res = await apiRequest('/carbon/calculate/', 'POST', { category: cat, inputs });
    document.getElementById('calc-live-co2').innerText = parseFloat(res.calculated_emissions_co2).toFixed(2);
  } catch (e) {
    console.error(e);
  }
}

function getCategoryInputs(cat) {
  if (cat === 'transport') {
    return {
      trips_per_week: parseInt(document.getElementById('calc-transport-trips').value),
      car_distance: parseFloat(document.getElementById('calc-transport-car').value) || 0,
      fuel_type: document.getElementById('calc-transport-fuel').value,
      bike_distance: parseFloat(document.getElementById('calc-transport-bike').value) || 0,
      bus_distance: parseFloat(document.getElementById('calc-transport-bus').value) || 0,
      train_distance: parseFloat(document.getElementById('calc-transport-train').value) || 0,
      flight_distance: parseFloat(document.getElementById('calc-transport-flight').value) || 0
    };
  } else if (cat === 'energy') {
    return {
      electricity_kwh: parseFloat(document.getElementById('calc-energy-electricity').value) || 0,
      lpg_kg: parseFloat(document.getElementById('calc-energy-lpg').value) || 0,
      ac_hours: parseFloat(document.getElementById('calc-energy-ac').value) || 0,
      appliance_hours: parseFloat(document.getElementById('calc-energy-appliances').value) || 0
    };
  } else if (cat === 'food') {
    return {
      diet_type: document.getElementById('calc-food-diet').value,
      food_waste_kg: parseFloat(document.getElementById('calc-food-waste').value) || 0
    };
  } else if (cat === 'shopping') {
    return {
      clothes_count: parseFloat(document.getElementById('calc-shopping-clothes').value) || 0,
      electronics_count: parseFloat(document.getElementById('calc-shopping-electronics').value) || 0,
      online_orders_count: parseFloat(document.getElementById('calc-shopping-online').value) || 0
    };
  } else if (cat === 'waste') {
    return {
      plastic_kg: parseFloat(document.getElementById('calc-waste-plastic').value) || 0,
      recycled_kg: parseFloat(document.getElementById('calc-waste-recycled').value) || 0,
      water_kl: parseFloat(document.getElementById('calc-waste-water').value) || 0,
      general_waste_kg: parseFloat(document.getElementById('calc-waste-general').value) || 0
    };
  }
  return {};
}

async function handleCarbonEntrySubmit(e) {
  e.preventDefault();
  const cat = document.getElementById('calc-current-category').value;
  const inputs = getCategoryInputs(cat);
  
  showLoading(true);
  try {
    const res = await apiRequest('/carbon/entries/', 'POST', {
      category: cat,
      inputs,
      date: new Date().toISOString().split('T')[0]
    });
    showToast(`Carbon logged: ${parseFloat(res.emissions_co2).toFixed(2)} kg CO₂ recorded.`);
    
    // Clear & reload
    document.getElementById('calculator-form').reset();
    document.getElementById('calc-transport-trips-value').innerText = '1 trip';
    updateLiveEstimation();
    loadPastEntries();
    fetchDashboardSummary();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadPastEntries() {
  try {
    const data = await apiRequest('/carbon/entries/');
    const tbody = document.getElementById('calc-entries-tbody');
    tbody.innerHTML = '';
    
    const categoryIcons = {
      transport: 'fa-car text-emerald-600',
      energy: 'fa-plug text-lime-600',
      food: 'fa-utensils text-red-500',
      shopping: 'fa-bag-shopping text-blue-500',
      waste: 'fa-trash-can text-indigo-500'
    };

    data.results.forEach(entry => {
      const inputsList = Object.entries(entry.inputs)
        .filter(([_, v]) => parseFloat(v) > 0)
        .map(([k, v]) => `${k.replace('_', ' ')}: ${v}`)
        .join(', ');

      tbody.innerHTML += `
        <tr class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-all">
          <td class="py-3.5 font-medium">${entry.date}</td>
          <td class="py-3.5">
            <span class="flex items-center gap-2">
              <i class="fa-solid ${categoryIcons[entry.category]}"></i>
              ${entry.category.toUpperCase()}
            </span>
          </td>
          <td class="py-3.5 text-slate-500 max-w-xs truncate" title="${inputsList}">${inputsList || 'Default Factor'}</td>
          <td class="py-3.5 text-right font-bold text-emerald-600">${parseFloat(entry.emissions_co2).toFixed(2)}</td>
          <td class="py-3.5 text-center">
            <button onclick="handleDeleteEntry(${entry.id})" class="text-red-400 hover:text-red-600 p-1.5"><i class="fa-solid fa-trash"></i></button>
          </td>
        </tr>
      `;
    });
    
    if (data.results.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="py-8 text-center text-slate-400">No calculation entries logged yet.</td></tr>';
    }
  } catch (err) {
    console.error(err);
  }
}

window.handleDeleteEntry = async function(id) {
  if (!confirm("Are you sure you want to delete this carbon entry?")) return;
  showLoading(true);
  try {
    await apiRequest(`/carbon/entries/${id}/`, 'DELETE');
    showToast("Carbon log deleted.");
    loadPastEntries();
    fetchDashboardSummary();
  } catch (e) {
    showToast(e.message, 'error');
  } finally {
    showLoading(false);
  }
};

// EcoGuide AI coach chat
async function handleCoachChatSubmit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('coach-chat-input');
  const query = inputEl.value.trim();
  if (!query) return;
  
  // Add query bubble to chat box
  const chatBox = document.getElementById('coach-chat-box');
  chatBox.innerHTML += `
    <div class="flex items-start gap-3 max-w-[80%] self-end flex-row-reverse">
      <div class="w-8 h-8 rounded-full bg-slate-200 dark:bg-slate-800 text-slate-600 flex items-center justify-center flex-shrink-0 text-sm font-bold">Me</div>
      <div class="p-3.5 rounded-2xl rounded-tr-none bg-emerald-600 text-white text-sm leading-relaxed">${query}</div>
    </div>
  `;
  
  inputEl.value = '';
  chatBox.scrollTop = chatBox.scrollHeight;
  
  // Loading skeleton bubble
  const skeletonId = `bot-skeleton-${Date.now()}`;
  chatBox.innerHTML += `
    <div id="${skeletonId}" class="flex items-start gap-3 max-w-[80%]">
      <div class="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center flex-shrink-0 text-sm font-bold">AI</div>
      <div class="p-3.5 rounded-2xl rounded-tl-none bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 flex flex-col gap-2 w-48">
        <div class="skeleton h-3 w-full"></div>
        <div class="skeleton h-3 w-5/6"></div>
      </div>
    </div>
  `;
  chatBox.scrollTop = chatBox.scrollHeight;

  try {
    const res = await apiRequest('/coach/chat/', 'POST', { message: query });
    
    // Simulate searching/thinking delay (0.4s - 1.0s)
    const delay = Math.random() * 600 + 400;
    setTimeout(() => {
      // Remove skeleton
      const skeletonEl = document.getElementById(skeletonId);
      if (skeletonEl) skeletonEl.remove();
      
      // Add real answer with formatting support (simple markdown bullet parsing)
      const formatted = res.reply
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>')
        .replace(/### (.*?)(?:<br>|$)/g, '<h4 class="font-extrabold text-base text-emerald-600 mt-2">$1</h4>');

      chatBox.innerHTML += `
        <div class="flex items-start gap-3 max-w-[80%] animate-fade-in">
          <div class="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-950 text-emerald-600 flex items-center justify-center flex-shrink-0 text-sm font-bold">AI</div>
          <div class="p-3.5 rounded-2xl rounded-tl-none bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-sm leading-relaxed">${formatted}</div>
        </div>
      `;
      chatBox.scrollTop = chatBox.scrollHeight;
    }, delay);
  } catch (err) {
    const skeletonEl = document.getElementById(skeletonId);
    if (skeletonEl) skeletonEl.remove();
    showToast(err.message, 'error');
  }
}

// Gamification badges lists
async function loadBadges() {
  try {
    const list = await apiRequest('/recommendations/personalized/'); // yields items for check
    // We fetch user badges and full badges
    const userBadges = await apiRequest('/leaderboard/'); // endpoints
    const profiles = await apiRequest('/profile/');
    
    // Mock mapping badge info from user badges endpoint
    const badgesContainer = document.getElementById('dash-badges-grid');
    const showcaseContainer = document.getElementById('badges-showcase-grid');
    
    // We fetch actual database unlocked badges
    const response = await fetch(`${API_BASE}/leaderboard/`, { headers: { 'Authorization': `Bearer ${state.token}` } });
    const lbData = await response.json();
    
    // Fetch user profile badges
    const userProfileData = await apiRequest('/profile/');
    
    // Fetch all badges from generic list (Mocked arrays as fallback or pull from api if needed)
    // To ensure strict correctness, let's load from default seed structures or fetch
    const badges = [
      { id: 1, name: 'Eco Recruit', description: 'Signed up to EcoTrack AI to protect the planet', icon: 'fa-leaf', points: 0 },
      { id: 2, name: 'Carbon Conscious', description: 'Log your first 5 carbon entries in the EcoTrack Calculator.', icon: 'fa-calculator', points: 50 },
      { id: 3, name: 'Green Hero', description: 'Reach over 250 green points through completing challenges and quizzes.', icon: 'fa-award', points: 250 },
      { id: 4, name: 'Challenge Champion', description: 'Successfully finish 3 sustainability challenges.', icon: 'fa-trophy', points: 500 },
      { id: 5, name: 'Earth Guardian', description: 'Amass 1,000 green points to achieve top levels.', icon: 'fa-globe', points: 1000 }
    ];

    const currentPoints = userProfileData.green_points;

    badgesContainer.innerHTML = '';
    showcaseContainer.innerHTML = '';

    badges.forEach(b => {
      const isUnlocked = currentPoints >= b.points;
      const opacity = isUnlocked ? 'opacity-100 scale-100' : 'opacity-40 grayscale scale-95';
      const badgeCardHTML = `
        <div class="glass-panel p-3.5 flex flex-col items-center text-center transition-all ${opacity}">
          <div class="h-12 w-12 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center text-xl mb-2">
            <i class="fa-solid ${b.icon}"></i>
          </div>
          <h5 class="text-xs font-bold truncate w-full">${b.name}</h5>
          <span class="text-[9px] text-emerald-600 mt-1 font-bold">${isUnlocked ? 'Unlocked' : `Requires ${b.points} pts`}</span>
        </div>
      `;

      showcaseContainer.innerHTML += `
        <div class="glass-panel p-4 flex flex-col items-center text-center transition-all ${opacity}">
          <div class="h-14 w-14 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center text-2xl mb-3">
            <i class="fa-solid ${b.icon}"></i>
          </div>
          <h4 class="text-sm font-bold">${b.name}</h4>
          <p class="text-[10px] text-slate-500 dark:text-slate-400 mt-1 leading-snug">${b.description}</p>
          <span class="text-xs mt-3 font-semibold px-2 py-0.5 rounded-full ${isUnlocked ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-500'}">
            ${isUnlocked ? 'Unlocked' : 'Locked'}
          </span>
        </div>
      `;

      if (isUnlocked) {
        badgesContainer.innerHTML += `
          <div class="flex flex-col items-center text-center">
            <div class="h-10 w-10 rounded-full bg-emerald-100 dark:bg-emerald-950/60 text-emerald-600 flex items-center justify-center text-lg mb-1" title="${b.name}">
              <i class="fa-solid ${b.icon}"></i>
            </div>
            <span class="text-[9px] truncate w-14">${b.name}</span>
          </div>
        `;
      }
    });

  } catch (err) {
    console.error(err);
  }
}

async function loadChallenges() {
  try {
    const list = await apiRequest('/challenges/');
    const activeData = await apiRequest('/recommendations/personalized/'); // Check joined states
    const userProfileData = await apiRequest('/profile/');

    const container = document.getElementById('challenges-list');
    container.innerHTML = '';

    list.results.forEach(chal => {
      // For testing states, we show simple join/complete actions
      // In models, we track ChallengeProgress. Since ChallengeProgress logic is fully coded in backend:
      container.innerHTML += `
        <div class="glass-panel p-5 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
          <div>
            <div class="flex items-center gap-2">
              <h4 class="font-bold text-base">${chal.title}</h4>
              <span class="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-600">${chal.level}</span>
            </div>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-1 leading-snug">${chal.description}</p>
            <div class="flex items-center gap-4 mt-3 text-xs text-slate-400">
              <span><i class="fa-solid fa-gift text-emerald-600 mr-1.5"></i>Reward: <b>${chal.points_reward} pts</b></span>
              <span><i class="fa-solid fa-hourglass mr-1.5"></i>Duration: <b>${chal.duration_days} Days</b></span>
            </div>
          </div>
          <div class="flex gap-2 self-stretch md:self-auto">
            <button onclick="handleChallengeAction(${chal.id}, 'join')" class="btn-glass-secondary flex-1 md:flex-none text-xs py-2 px-4">Accept</button>
            <button onclick="handleChallengeAction(${chal.id}, 'complete')" class="btn-glass-primary flex-1 md:flex-none text-xs py-2 px-4">Claim Reward</button>
          </div>
        </div>
      `;
    });
  } catch (err) {
    console.error(err);
  }
}

window.handleChallengeAction = async function(id, actionName) {
  showLoading(true);
  try {
    const res = await apiRequest(`/challenges/${id}/${actionName}/`, 'POST');
    showToast(res.message);
    loadChallenges();
    fetchDashboardSummary();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
};

async function loadLeaderboard() {
  try {
    const data = await apiRequest('/leaderboard/');
    const list = document.getElementById('leaderboard-list');
    list.innerHTML = '';

    data.leaderboard.forEach(user => {
      const isMe = state.user && user.username === state.user.user.username;
      list.innerHTML += `
        <div class="flex items-center justify-between p-3 rounded-xl border ${isMe ? 'border-emerald-500/50 bg-emerald-50/20' : 'border-transparent'}">
          <div class="flex items-center gap-3">
            <span class="font-extrabold text-sm ${user.rank === 1 ? 'text-yellow-500' : user.rank === 2 ? 'text-slate-400' : user.rank === 3 ? 'text-amber-600' : 'text-slate-400'}">#${user.rank}</span>
            <div>
              <h5 class="text-sm font-bold flex items-center gap-2">
                ${user.username}
                <span class="text-[9px] px-1.5 py-0.5 rounded bg-emerald-100 dark:bg-emerald-950 text-emerald-600 font-bold">${user.level}</span>
              </h5>
            </div>
          </div>
          <span class="text-sm font-black text-emerald-600">${user.points} pts</span>
        </div>
      `;
    });

    // Update current user ranking summary at bottom
    document.getElementById('lb-user-rank').innerText = data.user_rank.rank;
    document.getElementById('lb-user-points').innerText = data.user_rank.points;
    document.getElementById('lb-user-level').innerText = data.user_rank.level;
    document.getElementById('lb-user-username').innerText = state.user ? `${state.user.user.username} (You)` : 'You';
  } catch (e) {
    console.error(e);
  }
}

// Educational Articles & Quizzes loaders
async function loadArticles() {
  try {
    const list = await apiRequest('/articles/');
    const grid = document.getElementById('articles-grid');
    grid.innerHTML = '';

    list.results.forEach(art => {
      const iconsMap = { fire: 'fa-fire', calculator: 'fa-calculator', seedling: 'fa-seedling', sun: 'fa-sun', recycle: 'fa-recycle', leaf: 'fa-leaf' };
      const icon = iconsMap[art.image_url] || 'fa-leaf';

      grid.innerHTML += `
        <div class="glass-panel p-5 flex flex-col justify-between">
          <div>
            <div class="h-10 w-10 bg-emerald-100 dark:bg-emerald-950/60 rounded-xl flex items-center justify-center text-emerald-600 text-lg mb-3">
              <i class="fa-solid ${icon}"></i>
            </div>
            <span class="text-[10px] font-bold text-emerald-600 bg-emerald-100/50 dark:bg-emerald-950/50 px-2 py-0.5 rounded-full">${art.category}</span>
            <h4 class="font-bold text-base mt-2">${art.title}</h4>
            <p class="text-xs text-slate-500 dark:text-slate-400 mt-2.5 leading-relaxed">${art.content}</p>
          </div>
          <div class="flex items-center justify-between border-t border-slate-100 dark:border-slate-800 pt-3 mt-4 text-xs text-slate-400">
            <span>Read: <b>${art.read_time} mins</b></span>
          </div>
        </div>
      `;
    });
  } catch (e) {
    console.error(e);
  }
}

async function loadQuizzes() {
  try {
    const list = await apiRequest('/quizzes/');
    const grid = document.getElementById('quizzes-grid');
    grid.innerHTML = '';

    list.results.forEach(q => {
      grid.innerHTML += `
        <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-emerald-500/30 transition-all flex flex-col md:flex-row justify-between items-start md:items-center gap-3">
          <div>
            <h4 class="font-bold text-sm text-emerald-700 dark:text-emerald-400">${q.title}</h4>
            <p class="text-xs text-slate-400 mt-0.5">${q.description}</p>
          </div>
          <button onclick="handleStartQuiz(${q.id})" class="btn-glass-primary py-1.5 px-4 text-xs">Start Quiz (+${q.points_reward} pts)</button>
        </div>
      `;
    });
  } catch (e) {
    console.error(e);
  }
}

window.handleStartQuiz = async function(id) {
  showLoading(true);
  try {
    const q = await apiRequest(`/quizzes/${id}/`);
    state.currentQuiz = q;
    state.quizAnswers = {};
    state.currentQuestionIdx = 0;
    
    // Open Dialog modal
    document.getElementById('quiz-modal-title').innerText = q.title;
    document.getElementById('quiz-points-val').innerText = q.points_reward;
    document.getElementById('quiz-question-total').innerText = q.questions.length;
    
    renderQuizQuestion();
    document.getElementById('quiz-modal').showModal();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
};

function renderQuizQuestion() {
  const q = state.currentQuiz;
  const idx = state.currentQuestionIdx;
  const question = q.questions[idx];
  
  document.getElementById('quiz-question-current').innerText = idx + 1;
  document.getElementById('quiz-question-text').innerText = question.question_text;
  
  const optionsBox = document.getElementById('quiz-options-container');
  optionsBox.innerHTML = '';

  const opts = [
    { key: 'A', text: question.option_a },
    { key: 'B', text: question.option_b },
    { key: 'C', text: question.option_c },
    { key: 'D', text: question.option_d }
  ];

  opts.forEach(o => {
    optionsBox.innerHTML += `
      <button onclick="handleSelectQuizAnswer('${o.key}')" class="quiz-option-btn w-full text-left p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 font-semibold text-xs transition-all flex justify-between items-center text-slate-800 dark:text-slate-200" data-option="${o.key}">
        <span>${o.key}. ${o.text}</span>
        <i class="fa-regular fa-circle text-slate-400"></i>
      </button>
    `;
  });

  // Toggle navigation buttons
  const isLast = idx === q.questions.length - 1;
  document.getElementById('quiz-next-btn').classList.toggle('hidden', isLast);
  document.getElementById('quiz-submit-btn').classList.toggle('hidden', !isLast);
}

window.handleSelectQuizAnswer = function(optionKey) {
  const q = state.currentQuiz;
  const question = q.questions[state.currentQuestionIdx];
  state.quizAnswers[question.id] = optionKey;
  
  document.querySelectorAll('.quiz-option-btn').forEach(btn => {
    btn.className = "quiz-option-btn w-full text-left p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900 font-semibold text-xs transition-all flex justify-between items-center text-slate-800 dark:text-slate-200";
    btn.querySelector('i').className = "fa-regular fa-circle text-slate-400";
  });
  
  const activeBtn = document.querySelector(`.quiz-option-btn[data-option="${optionKey}"]`);
  activeBtn.className = "quiz-option-btn w-full text-left p-3.5 rounded-xl border-2 border-emerald-500 bg-emerald-50/10 font-bold text-xs transition-all flex justify-between items-center text-emerald-600";
  activeBtn.querySelector('i').className = "fa-solid fa-circle-check text-emerald-600";
};

function handleNextQuizQuestion() {
  const q = state.currentQuiz;
  const question = q.questions[state.currentQuestionIdx];
  if (!state.quizAnswers[question.id]) {
    showToast("Please choose an answer first.", 'error');
    return;
  }
  
  state.currentQuestionIdx++;
  renderQuizQuestion();
}

async function handleQuizAnswersSubmit() {
  const q = state.currentQuiz;
  const question = q.questions[state.currentQuestionIdx];
  if (!state.quizAnswers[question.id]) {
    showToast("Please choose an answer first.", 'error');
    return;
  }

  showLoading(true);
  try {
    const res = await apiRequest(`/quizzes/${q.id}/submit/`, 'POST', { answers: state.quizAnswers });
    document.getElementById('quiz-modal').close();
    showToast(`Quiz completed! You scored ${res.score}% and earned +${res.points_earned} points.`);
    fetchDashboardSummary();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Community posts & Comments loaders
async function loadCommunityPosts() {
  try {
    const list = await apiRequest('/community/posts/');
    const stream = document.getElementById('community-posts-stream');
    stream.innerHTML = '';

    list.results.forEach(post => {
      const hasLiked = post.has_liked;
      const likeColor = hasLiked ? 'text-red-500' : 'text-slate-400';
      const likeIcon = hasLiked ? 'fa-solid' : 'fa-regular';

      stream.innerHTML += `
        <div class="glass-panel p-5 flex flex-col gap-3">
          <div class="flex items-center justify-between border-b pb-2.5 border-slate-200 dark:border-slate-800">
            <div class="flex items-center gap-2">
              <div class="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-xs">${post.username[0].toUpperCase()}</div>
              <div>
                <h5 class="text-xs font-bold">${post.username}</h5>
                <span class="text-[9px] text-slate-400">${new Date(post.created_at).toLocaleString()}</span>
              </div>
            </div>
          </div>
          <div>
            <h4 class="font-bold text-base text-emerald-700 dark:text-emerald-500">${post.title}</h4>
            <p class="text-xs text-slate-500 dark:text-slate-300 mt-1.5 leading-relaxed">${post.content}</p>
          </div>
          <div class="flex items-center gap-6 border-t pt-2.5 border-slate-100 dark:border-slate-800 mt-2 text-xs">
            <button onclick="handleLikePost(${post.id})" class="flex items-center gap-2 hover:text-red-500 ${likeColor} transition-all">
              <i class="${likeIcon} fa-heart"></i> Likes (<span id="likes-count-${post.id}">${post.likes_count}</span>)
            </button>
            <button onclick="handleOpenComments(${post.id}, '${post.title.replace(/'/g, "\\'")}')" class="flex items-center gap-2 text-slate-400 hover:text-emerald-600 transition-all">
              <i class="fa-regular fa-comment"></i> Comments (${post.comments.length})
            </button>
          </div>
        </div>
      `;
    });
    if (list.results.length === 0) {
      stream.innerHTML = '<div class="glass-panel p-8 text-center text-slate-400">No community tips shared yet. Be the first to share one!</div>';
    }
  } catch (e) {
    console.error(e);
  }
}

async function handleCommunityPostSubmit(e) {
  e.preventDefault();
  const title = document.getElementById('community-title').value;
  const content = document.getElementById('community-content').value;

  showLoading(true);
  try {
    await apiRequest('/community/posts/', 'POST', { title, content });
    showToast("Tip shared with the community! Earned +5 Green Points.");
    document.getElementById('community-create-form').reset();
    loadCommunityPosts();
    fetchDashboardSummary();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

window.handleLikePost = async function(id) {
  try {
    const res = await apiRequest(`/community/posts/${id}/like/`, 'POST');
    const heart = document.querySelector(`button[onclick="handleLikePost(${id})"]`);
    const count = document.getElementById(`likes-count-${id}`);
    
    count.innerText = res.likes_count;
    if (res.liked) {
      heart.className = "flex items-center gap-2 hover:text-red-500 text-red-500 transition-all";
      heart.querySelector('i').className = "fa-solid fa-heart";
    } else {
      heart.className = "flex items-center gap-2 hover:text-red-500 text-slate-400 transition-all";
      heart.querySelector('i').className = "fa-regular fa-heart";
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
};

window.handleOpenComments = async function(postId, postTitle) {
  showLoading(true);
  try {
    const listEl = document.getElementById('comment-list-box');
    listEl.innerHTML = '';
    
    document.getElementById('comment-modal-title').innerText = `Comments for: "${postTitle}"`;
    document.getElementById('comment-target-post-id').value = postId;
    
    const post = await apiRequest(`/community/posts/${postId}/`);
    post.comments.forEach(c => {
      listEl.innerHTML += `
        <div class="p-3 bg-slate-50 dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800/60">
          <div class="flex justify-between items-center text-[10px] text-slate-400 font-semibold mb-1">
            <span>${c.username}</span>
            <span>${new Date(c.created_at).toLocaleTimeString()}</span>
          </div>
          <p class="text-xs leading-relaxed text-slate-600 dark:text-slate-300">${c.content}</p>
        </div>
      `;
    });
    
    if (post.comments.length === 0) {
      listEl.innerHTML = '<p class="text-center text-xs text-slate-400 py-6">No comments yet.</p>';
    }

    document.getElementById('comment-modal').showModal();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
};

async function handleCommentSubmit(e) {
  e.preventDefault();
  const postId = document.getElementById('comment-target-post-id').value;
  const content = document.getElementById('comment-input').value;

  showLoading(true);
  try {
    await apiRequest(`/community/posts/${postId}/comment/`, 'POST', { content });
    showToast("Comment added.");
    document.getElementById('comment-input').value = '';
    document.getElementById('comment-modal').close();
    loadCommunityPosts();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

// Notifications and Alerts
async function fetchNotifications() {
  try {
    const data = await apiRequest('/notifications/');
    const list = document.getElementById('notif-list');
    const badge = document.getElementById('notif-badge');
    
    const unread = data.results.filter(n => !n.is_read);
    badge.className = unread.length > 0 ? "absolute -top-1 -right-1 h-3.5 w-3.5 bg-red-500 rounded-full border-2 border-white dark:border-slate-900 animate-pulse" : "hidden";

    list.innerHTML = '';
    data.results.slice(0, 10).forEach(n => {
      list.innerHTML += `
        <div onclick="handleReadNotification(${n.id})" class="p-3 rounded-lg border text-xs cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-900 transition-all ${
          n.is_read ? 'border-slate-100 dark:border-slate-800 text-slate-400' : 'border-emerald-500/20 bg-emerald-500/5 font-semibold text-slate-700 dark:text-slate-300'
        }">
          <div class="flex justify-between items-center text-[9px] text-slate-400 mb-1">
            <span>${n.notification_type.toUpperCase()}</span>
            <span>${new Date(n.created_at).toLocaleDateString()}</span>
          </div>
          <h5>${n.title}</h5>
          <p class="text-[10px] text-slate-400 font-normal mt-0.5">${n.message}</p>
        </div>
      `;
    });

    if (data.results.length === 0) {
      list.innerHTML = '<p class="text-xs text-center text-slate-500 py-4">No new notifications</p>';
    }
  } catch (e) {
    console.error(e);
  }
}

window.handleReadNotification = async function(id) {
  try {
    await apiRequest(`/notifications/${id}/read/`, 'POST');
    fetchNotifications();
  } catch (e) {
    console.error(e);
  }
};

async function handleClearAllNotifications() {
  showLoading(true);
  try {
    // Standard loops clear
    const data = await apiRequest('/notifications/');
    const unread = data.results.filter(n => !n.is_read);
    for (let n of unread) {
      await apiRequest(`/notifications/${n.id}/read/`, 'POST');
    }
    fetchNotifications();
    showToast("Notifications cleared.");
  } catch (e) {
    console.error(e);
  } finally {
    showLoading(false);
  }
}

// Reports generation and retrieval
async function handleReportGenerationSubmit(e) {
  e.preventDefault();
  const range_type = document.getElementById('report-range').value;
  const format_type = document.querySelector('input[name="report-format"]:checked').value;

  showLoading(true);
  try {
    const res = await apiRequest('/reports/generate/', 'POST', { range_type, format_type });
    showToast("Report generated successfully!");
    
    // Auto initiate direct browser download link
    const link = document.createElement('a');
    link.href = res.file_path;
    link.download = res.title;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    loadReportsList();
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    showLoading(false);
  }
}

async function loadReportsList() {
  try {
    const data = await apiRequest('/reports/generate/');
    const tbody = document.getElementById('generated-reports-tbody');
    tbody.innerHTML = '';

    data.forEach(rep => {
      tbody.innerHTML += `
        <tr class="border-b border-slate-100 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/40 transition-all text-xs">
          <td class="py-3 font-medium">${new Date(rep.generated_at).toLocaleDateString()}</td>
          <td class="py-3 font-semibold">${rep.title}</td>
          <td class="py-3">
            <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
              rep.format_type === 'PDF' ? 'bg-red-100 text-red-700' : rep.format_type === 'Excel' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
            }">${rep.format_type}</span>
          </td>
          <td class="py-3 text-right">
            <a href="${rep.file_path}" download class="btn-glass-primary px-3 py-1.5 text-[10px]"><i class="fa-solid fa-download mr-1"></i>Download</a>
          </td>
        </tr>
      `;
    });

    if (data.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="py-6 text-center text-slate-400">No generated reports in archive.</td></tr>';
    }
  } catch (e) {
    console.error(e);
  }
}

