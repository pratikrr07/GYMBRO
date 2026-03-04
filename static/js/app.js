/* ═══════════════════════════════════════════════════════════════
   🏋️ GYMBRO — Frontend Application
   ═══════════════════════════════════════════════════════════════ */

const API = `${window.location.origin}/api`;

// ── State ────────────────────────────────────────────────────────
const state = {
  token: localStorage.getItem('gymbro_token') || null,
  user: null,
  calendarYear: new Date().getFullYear(),
  calendarMonth: new Date().getMonth() + 1,
  exercises: [],
  selectedExercises: [],   // [{exercise, sets: [{reps, weight, notes}]}]
  chatOpen: false,
  chatMessages: [],
};

// ═══════════════════════════════════════════════════════════════
//  API SERVICE
// ═══════════════════════════════════════════════════════════════
async function api(path, opts = {}) {
  const headers = { 'Content-Type': 'application/json' };
  if (state.token) headers['Authorization'] = `Bearer ${state.token}`;

  try {
    const res = await fetch(`${API}${path}`, { ...opts, headers });
    const data = await res.json();
    if (!res.ok) {
      const msg = data.detail || JSON.stringify(data);
      throw new Error(msg);
    }
    return data;
  } catch (err) {
    if (err.message === 'Failed to fetch') {
      throw new Error('Server is not reachable');
    }
    throw err;
  }
}

const get  = (p) => api(p);
const post = (p, b) => api(p, { method: 'POST', body: JSON.stringify(b) });
const put  = (p, b) => api(p, { method: 'PUT', body: JSON.stringify(b) });
const del  = (p) => api(p, { method: 'DELETE' });

// ═══════════════════════════════════════════════════════════════
//  TOAST NOTIFICATIONS
// ═══════════════════════════════════════════════════════════════
function toast(msg, type = 'info') {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  el.innerHTML = `<span>${icons[type] || 'ℹ'}</span> ${msg}`;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 300); }, 3500);
}

// ═══════════════════════════════════════════════════════════════
//  AUTH
// ═══════════════════════════════════════════════════════════════
function initAuth() {
  // Tab switching
  document.querySelectorAll('.auth-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const isLogin = tab.dataset.tab === 'login';
      document.getElementById('login-form').style.display = isLogin ? 'block' : 'none';
      document.getElementById('signup-form').style.display = isLogin ? 'none' : 'block';
    });
  });

  // Login
  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('login-btn');
    btn.disabled = true;
    btn.textContent = 'Signing in...';
    try {
      const data = await post('/auth/login', {
        email: document.getElementById('login-email').value,
        password: document.getElementById('login-password').value,
      });
      state.token = data.access_token;
      localStorage.setItem('gymbro_token', data.access_token);
      toast('Welcome back! 💪', 'success');
      await enterApp();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Sign In';
    }
  });

  // Signup
  document.getElementById('signup-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('signup-btn');
    btn.disabled = true;
    btn.textContent = 'Creating account...';
    try {
      const body = {
        username: document.getElementById('signup-username').value,
        email: document.getElementById('signup-email').value,
        password: document.getElementById('signup-password').value,
      };
      const age = document.getElementById('signup-age').value;
      const height = document.getElementById('signup-height').value;
      const weight = document.getElementById('signup-weight').value;
      if (age) body.age = parseInt(age);
      if (height) body.height_cm = parseFloat(height);
      if (weight) body.weight_kg = parseFloat(weight);
      body.gender = document.getElementById('signup-gender').value;
      body.activity_level = document.getElementById('signup-activity').value;
      body.goal = document.getElementById('signup-goal').value;

      const data = await post('/auth/signup', body);
      state.token = data.access_token;
      localStorage.setItem('gymbro_token', data.access_token);
      toast('Account created! Let\'s get started 🚀', 'success');
      await enterApp();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Create Account';
    }
  });
}

// ═══════════════════════════════════════════════════════════════
//  APP ENTRY / EXIT
// ═══════════════════════════════════════════════════════════════
async function enterApp() {
  try {
    state.user = await get('/auth/me');
  } catch {
    logout();
    return;
  }

  document.getElementById('auth-page').style.display = 'none';
  document.getElementById('app-page').style.display = 'flex';

  updateSidebar();
  navigateTo('dashboard');
  showChatFab();
}

function logout() {
  state.token = null;
  state.user = null;
  localStorage.removeItem('gymbro_token');
  document.getElementById('app-page').style.display = 'none';
  document.getElementById('auth-page').style.display = 'flex';
  hideChatFab();
  state.chatMessages = [];
  toast('Logged out', 'info');
}

function updateSidebar() {
  if (!state.user) return;
  const u = state.user;
  const initial = (u.username || u.email || '?')[0].toUpperCase();
  document.getElementById('sidebar-avatar').textContent = initial;
  document.getElementById('sidebar-name').textContent = u.username || 'User';
  document.getElementById('sidebar-email').textContent = u.email || '';
}

// ═══════════════════════════════════════════════════════════════
//  NAVIGATION
// ═══════════════════════════════════════════════════════════════
function initNav() {
  document.querySelectorAll('.nav-item[data-section]').forEach(btn => {
    btn.addEventListener('click', () => navigateTo(btn.dataset.section));
  });

  document.getElementById('logout-btn').addEventListener('click', logout);

  // Mobile menu
  document.getElementById('menu-toggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
    document.getElementById('sidebar-backdrop').classList.toggle('open');
  });
  document.getElementById('sidebar-backdrop').addEventListener('click', () => {
    document.getElementById('sidebar').classList.remove('open');
    document.getElementById('sidebar-backdrop').classList.remove('open');
  });
}

function navigateTo(section) {
  // Update nav
  document.querySelectorAll('.nav-item[data-section]').forEach(n => n.classList.remove('active'));
  const activeNav = document.querySelector(`.nav-item[data-section="${section}"]`);
  if (activeNav) activeNav.classList.add('active');

  // Show section
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  const sec = document.getElementById(`section-${section}`);
  if (sec) sec.classList.add('active');

  // Close mobile sidebar
  document.getElementById('sidebar').classList.remove('open');
  document.getElementById('sidebar-backdrop').classList.remove('open');

  // Load data
  switch (section) {
    case 'dashboard': loadDashboard(); break;
    case 'workouts':  loadWorkouts(); break;
    case 'meals':     loadMeals(); break;
    case 'goals':     loadGoals(); break;
    case 'progress':  loadProgress(); break;
    case 'profile':   loadProfile(); break;
  }
}

// ═══════════════════════════════════════════════════════════════
//  DASHBOARD
// ═══════════════════════════════════════════════════════════════

// Fun fact comparisons — picked at random based on total volume
const FUN_FACTS = [
  { threshold: 0,      emoji: '🐱', text: (kg) => `You've lifted <strong>${formatNum(kg)} kg</strong> total — that's <strong>${(kg / 4).toFixed(0)} house cats</strong>! 🐱` },
  { threshold: 100,    emoji: '🧑', text: (kg) => `You've moved <strong>${formatNum(kg)} kg</strong> — equal to <strong>${(kg / 70).toFixed(1)} adult humans</strong>! 🧑` },
  { threshold: 500,    emoji: '🐴', text: (kg) => `Total volume: <strong>${formatNum(kg)} kg</strong> — like lifting <strong>${(kg / 450).toFixed(1)} horses</strong>! 🐴` },
  { threshold: 1000,   emoji: '🚗', text: (kg) => `You've pushed <strong>${formatNum(kg)} kg</strong> — that's <strong>${(kg / 1400).toFixed(1)} cars</strong>! 🚗` },
  { threshold: 5000,   emoji: '🐘', text: (kg) => `Insane! <strong>${formatNum(kg)} kg</strong> total — equal to <strong>${(kg / 5000).toFixed(1)} elephants</strong>! 🐘` },
  { threshold: 10000,  emoji: '🚌', text: (kg) => `Legend status: <strong>${formatNum(kg)} kg</strong> — that's <strong>${(kg / 12000).toFixed(1)} school buses</strong>! 🚌` },
  { threshold: 50000,  emoji: '✈️', text: (kg) => `Unreal: <strong>${formatNum(kg)} kg</strong> lifted — <strong>${(kg / 41000).toFixed(1)} fighter jets</strong>! ✈️` },
  { threshold: 100000, emoji: '🚀', text: (kg) => `Absolute beast: <strong>${formatNum(kg)} kg</strong> — that's <strong>${(kg / 130000).toFixed(2)} space shuttles</strong>! 🚀` },
  { threshold: 500000, emoji: '🐋', text: (kg) => `God mode: <strong>${formatNum(kg)} kg</strong> — you've lifted <strong>${(kg / 140000).toFixed(1)} blue whales</strong>! 🐋` },
];

// Alternate fun facts so it's different every time
const ALT_FACTS = [
  (kg) => `That's <strong>${(kg / 0.45).toFixed(0)} sticks of butter</strong> you've moved! 🧈`,
  (kg) => `Equivalent to <strong>${(kg / 7).toFixed(0)} bowling balls</strong>! 🎳`,
  (kg) => `Like carrying <strong>${(kg / 11).toFixed(0)} watermelons</strong> at once! 🍉`,
  (kg) => `About <strong>${(kg / 0.058).toFixed(0)} golf balls</strong> worth of weight! ⛳`,
  (kg) => `Same as <strong>${(kg / 420).toFixed(1)} grand pianos</strong>! 🎹`,
  (kg) => `That's <strong>${(kg / 900).toFixed(1)} polar bears</strong>! 🐻‍❄️`,
  (kg) => `You've moved <strong>${(kg / 150).toFixed(1)} refrigerators</strong>! 🧊`,
  (kg) => `Equal to <strong>${(kg / 2.3).toFixed(0)} laptops</strong>! 💻`,
];

function pickFunFact(totalVolumeKg) {
  const kg = Math.round(totalVolumeKg);
  if (kg === 0) return { emoji: '🏁', text: 'Log your first workout to see a fun fact here!' };

  // Pick from main facts (tier-based) or alternate facts randomly
  const useAlt = Math.random() > 0.5;
  if (useAlt) {
    const fn = ALT_FACTS[Math.floor(Math.random() * ALT_FACTS.length)];
    return { emoji: '💪', text: fn(kg) };
  }

  // Find the highest applicable tier
  let fact = FUN_FACTS[0];
  for (const f of FUN_FACTS) {
    if (kg >= f.threshold) fact = f;
  }
  return { emoji: fact.emoji, text: fact.text(kg) };
}

async function loadDashboard() {
  // ── Greeting based on time of day ──
  const hour = new Date().getHours();
  const name = state.user?.username || 'champ';
  const firstName = name.split(' ')[0];
  let greet, sub;
  if (hour < 5)       { greet = `Burning midnight oil, ${firstName}? 🌙`; sub = "Rest is part of the grind"; }
  else if (hour < 12) { greet = `Good morning, ${firstName} ☀️`; sub = "Rise and grind — let's get after it"; }
  else if (hour < 17) { greet = `Good afternoon, ${firstName} 💪`; sub = "Keep the momentum going"; }
  else if (hour < 21) { greet = `Good evening, ${firstName} 🔥`; sub = "Time to finish strong"; }
  else                { greet = `Still at it, ${firstName}? 🌟`; sub = "Late night gains hit different"; }

  document.getElementById('dash-greeting').textContent = greet;
  document.getElementById('dash-greeting-sub').textContent = sub;

  // Date display
  const today = new Date();
  document.getElementById('dash-hero-date').textContent = today.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  // Load stats + daily calories + tips in parallel
  const [stats, daily, tips] = await Promise.allSettled([
    get('/workouts/stats'),
    get('/meals/daily'),
    get('/goals/coaching-tips'),
  ]);

  // Water (non-blocking)
  loadWaterTracker();

  // Check achievements in background
  post('/progress/achievements/check').catch(() => {});

  // ── Stats row ──
  if (stats.status === 'fulfilled') {
    try {
      const s = stats.value;
      document.getElementById('dash-total-workouts').textContent = s.total_workouts || 0;
      document.getElementById('dash-this-month').textContent = s.total_this_month || 0;
      document.getElementById('dash-this-week').textContent = s.total_this_week || 0;
      document.getElementById('dash-streak').textContent = s.current_streak || 0;

      // ── Last Workout Card ──
      const lwCard = document.getElementById('dash-lw-card');
      if (s.last_workout_date) {
        lwCard.style.display = '';
        document.getElementById('dash-lw-name').textContent = s.last_workout_name || 'Workout';
        const lwDate = new Date(s.last_workout_date + 'T00:00:00');
        document.getElementById('dash-lw-date').textContent = lwDate.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        document.getElementById('dash-lw-exercises').textContent = s.last_workout_exercises || 0;
        document.getElementById('dash-lw-sets').textContent = s.last_workout_sets || 0;
        const lwVol = displayWeight(s.last_workout_volume_kg || 0);
        document.getElementById('dash-lw-volume').textContent = formatNum(lwVol);
        document.getElementById('dash-lw-unit').textContent = weightLabel();
        if (s.last_workout_duration_min > 0) {
          document.getElementById('dash-lw-duration').textContent = s.last_workout_duration_min;
        } else {
          document.getElementById('dash-lw-dur-wrap').style.display = 'none';
        }
      }

      // ── Fun Fact ──
      const ffCard = document.getElementById('dash-ff-card');
      const totalVol = s.total_volume_kg || 0;
      if (totalVol > 0 || s.total_workouts > 0) {
        ffCard.style.display = '';
        const fact = pickFunFact(totalVol);
        document.getElementById('dash-fun-fact').innerHTML = `<span class="ff-emoji">${fact.emoji}</span><span class="ff-text">${fact.text}</span>`;
      }
    } catch (err) {
      console.error('Dashboard stats update failed:', err);
    }
  }

  // ── Calories ──
  if (daily.status === 'fulfilled') {
    const d = daily.value;
    const eaten = Math.round(d.total_calories || 0);
    const target = state.user?.custom_calories || Math.round(d.target_calories || 2500);
    const pct = Math.min((eaten / target) * 100, 100);

    document.getElementById('dash-cal-eaten').textContent = eaten;
    document.getElementById('dash-cal-badge').textContent = `${eaten} / ${target} kcal`;

    const circumference = 490;
    const offset = circumference - (pct / 100) * circumference;
    document.getElementById('cal-ring').style.strokeDashoffset = offset;

    document.getElementById('dash-protein').textContent = `${Math.round(d.total_protein_g || 0)}g`;
    document.getElementById('dash-carbs').textContent = `${Math.round(d.total_carbs_g || 0)}g`;
    document.getElementById('dash-fat').textContent = `${Math.round(d.total_fat_g || 0)}g`;
  }

  // ── Tips ──
  if (tips.status === 'fulfilled') {
    const tipsList = tips.value.tips || tips.value || [];
    renderTips('dash-tips', Array.isArray(tipsList) ? tipsList : []);
  }
}

function renderTips(containerId, tips) {
  const el = document.getElementById(containerId);
  if (!tips.length) {
    el.innerHTML = '<p class="text-muted" style="padding:1rem;font-size:0.85rem">Complete your profile to get personalized tips!</p>';
    return;
  }
  const maxTips = containerId === 'dash-tips' ? 3 : 6; // Dashboard: 3, Goals page: 6
  el.innerHTML = tips.slice(0, maxTips).map(tip => {
    // Try to split emoji from text
    const emojiMatch = tip.match(/^(\p{Emoji_Presentation}|\p{Extended_Pictographic})/u);
    const emoji = emojiMatch ? emojiMatch[0] : '💡';
    const text = emojiMatch ? tip.slice(emojiMatch[0].length).trim() : tip;
    return `<div class="tip-card"><span class="tip-emoji">${emoji}</span><span class="tip-text">${text}</span></div>`;
  }).join('');
}

// ═══════════════════════════════════════════════════════════════
//  WORKOUTS
// ═══════════════════════════════════════════════════════════════
async function loadWorkouts() {
  loadCalendar();
  loadWorkoutList();
  loadWorkoutStats();
  loadRank();
}

async function loadWorkoutStats() {
  try {
    const s = await get('/workouts/stats');
    const wsWeek = document.getElementById('ws-week');
    const wsMonth = document.getElementById('ws-month');
    const wsStreak = document.getElementById('ws-streak');
    const wsVol = document.getElementById('ws-volume');
    if (wsWeek) wsWeek.textContent = s.total_this_week ?? 0;
    if (wsMonth) wsMonth.textContent = s.total_this_month ?? 0;
    if (wsStreak) wsStreak.textContent = s.current_streak ?? 0;
    if (wsVol) {
      const vol = displayWeight(s.total_volume_kg || 0);
      wsVol.textContent = vol >= 1000 ? (vol / 1000).toFixed(1) + 'k' : formatNum(vol);
    }
  } catch (err) {
    console.error('loadWorkoutStats failed:', err);
  }
}

async function loadCalendar() {
  const title = new Date(state.calendarYear, state.calendarMonth - 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  document.getElementById('cal-title').textContent = title;

  let workoutDays = [];
  try {
    const cal = await get(`/workouts/calendar?year=${state.calendarYear}&month=${state.calendarMonth}`);
    workoutDays = (cal || []).filter(d => d.has_workout || d.workout_count > 0).map(d => {
      if (d.day) return d.day;
      // Extract day from date string "YYYY-MM-DD"
      if (d.date) return parseInt(d.date.split('-')[2]);
      return 0;
    });
  } catch { /* ignore */ }

  const grid = document.getElementById('calendar-grid');
  // Keep header cells
  const headers = grid.querySelectorAll('.calendar-header-cell');
  grid.innerHTML = '';
  headers.forEach(h => grid.appendChild(h));

  const firstDay = new Date(state.calendarYear, state.calendarMonth - 1, 1);
  const daysInMonth = new Date(state.calendarYear, state.calendarMonth, 0).getDate();
  // Monday = 0
  let startDay = firstDay.getDay() - 1;
  if (startDay < 0) startDay = 6;

  const today = new Date();
  const isCurrentMonth = today.getFullYear() === state.calendarYear && today.getMonth() + 1 === state.calendarMonth;

  // Empty cells
  for (let i = 0; i < startDay; i++) {
    grid.innerHTML += '<div class="calendar-cell"></div>';
  }

  for (let d = 1; d <= daysInMonth; d++) {
    const classes = ['calendar-cell', 'current-month'];
    if (isCurrentMonth && d === today.getDate()) classes.push('today');
    if (workoutDays.includes(d)) classes.push('has-workout');
    grid.innerHTML += `<div class="${classes.join(' ')}">${d}</div>`;
  }
}

async function loadWorkoutList() {
  const list = document.getElementById('workout-list');
  try {
    const workouts = await get('/workouts/?limit=10');
    if (!workouts.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🏋️</div>
          <h3>No workouts yet</h3>
          <p>Start your first session and track your progress!</p>
        </div>`;
      return;
    }
    list.innerHTML = workouts.map(w => {
      const date = new Date(w.date || w.created_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
      const exCount = (w.exercises || []).length;
      const totalSets = (w.exercises || []).reduce((s, ex) => s + (ex.sets || []).length, 0);
      const totalVol = (w.exercises || []).reduce((v, ex) =>
        v + (ex.sets || []).reduce((sv, set) => sv + (set.weight || 0) * (set.reps || 0), 0), 0);
      return `
        <div class="item-card" onclick="viewWorkout('${w._id || w.id}')">
          <div class="item-card-header">
            <h4>${w.name || 'Workout'}</h4>
            <span class="item-date">${date}</span>
          </div>
          <div class="item-card-body">
            <span class="item-tag accent">${exCount} exercises</span>
            <span class="item-tag">${totalSets} sets</span>
            <span class="item-tag">${formatNum(displayWeight(totalVol))} ${weightLabel()} volume</span>
            ${w.notes ? `<span class="item-tag">${truncate(w.notes, 30)}</span>` : ''}
          </div>
        </div>`;
    }).join('');
  } catch (err) {
    list.innerHTML = `<p class="text-muted" style="padding:1rem">Error loading workouts</p>`;
  }
}

// ═══════════════════════════════════════════════════════════════
//  RANK SYSTEM
// ═══════════════════════════════════════════════════════════════
async function loadRank() {
  try {
    const r = await get('/rank/');
    const card = document.getElementById('rank-card');
    if (!card) return;

    // Current rank badge
    const emoji = document.getElementById('rank-emoji');
    const nameEl = document.getElementById('rank-name');
    const subtitleEl = document.getElementById('rank-subtitle');

    if (r.current_rank) {
      emoji.textContent = r.current_rank.emoji;
      nameEl.textContent = r.current_rank.name;
      nameEl.style.color = r.current_rank.color;
      subtitleEl.textContent = r.next_rank
        ? `Working toward ${r.next_rank.name}`
        : '🏆 Maximum rank achieved!';
    } else {
      emoji.textContent = '🏁';
      nameEl.textContent = 'Unranked';
      subtitleEl.textContent = 'Complete challenges to earn your first rank!';
    }

    // Tier dots
    const tierBar = document.getElementById('rank-tier-bar');
    tierBar.innerHTML = r.all_ranks.map(rk => {
      const isCurrent = r.current_rank && rk.order === r.current_rank.order;
      const cls = [
        'rank-tier-dot',
        rk.unlocked ? 'unlocked' : '',
        isCurrent ? 'current' : '',
      ].filter(Boolean).join(' ');
      return `<div class="${cls}" style="background:${rk.unlocked ? rk.color : 'transparent'}" title="${rk.name}">${rk.emoji}</div>`;
    }).join('');

    // Progress section
    const progSection = document.getElementById('rank-progress-section');
    if (r.next_rank) {
      progSection.style.display = '';
      document.getElementById('rank-next-name').textContent = r.next_rank.name;
      document.getElementById('rank-next-emoji').textContent = r.next_rank.emoji;
      document.getElementById('rank-pct').textContent = `${Math.round(r.overall_pct)}%`;
      document.getElementById('rank-progress-fill').style.width = `${r.overall_pct}%`;
    } else {
      progSection.style.display = 'none';
    }

    // Challenges
    const chList = document.getElementById('rank-challenges');
    if (r.next_challenges && r.next_challenges.length) {
      chList.innerHTML = r.next_challenges.map(ch => {
        const done = ch.completed;
        const pctW = Math.min(ch.pct, 100);
        const currentDisplay = typeof ch.current === 'number' && ch.current % 1 !== 0
          ? ch.current.toFixed(1) : ch.current;
        const targetDisplay = typeof ch.target === 'number' && ch.target >= 1000
          ? (ch.target / 1000).toFixed(ch.target % 1000 === 0 ? 0 : 1) + 'k'
          : ch.target;
        return `
          <div class="rank-challenge ${done ? 'done' : ''}">
            <div class="rank-ch-check">${done ? '✓' : ''}</div>
            <div class="rank-ch-info">
              <div class="rank-ch-label">${ch.label}</div>
              <div class="rank-ch-progress">${currentDisplay} / ${targetDisplay}</div>
            </div>
            <div class="rank-ch-bar">
              <div class="rank-ch-bar-fill" style="width:${pctW}%"></div>
            </div>
          </div>`;
      }).join('');
    } else {
      chList.innerHTML = `<div class="rank-maxed">👑 You've reached the highest rank — Legend! Absolute beast.</div>`;
    }

  } catch (err) {
    console.error('loadRank failed:', err);
  }
}

async function viewWorkout(id) {
  // For now just a simple toast – could open a detail modal
  toast('Workout details coming soon!', 'info');
}

// ── Calendar Navigation ──
document.getElementById('cal-prev').addEventListener('click', () => {
  state.calendarMonth--;
  if (state.calendarMonth < 1) { state.calendarMonth = 12; state.calendarYear--; }
  loadCalendar();
});

document.getElementById('cal-next').addEventListener('click', () => {
  state.calendarMonth++;
  if (state.calendarMonth > 12) { state.calendarMonth = 1; state.calendarYear++; }
  loadCalendar();
});

// ── Log Workout Modal ──
function initWorkoutModal() {
  const modal = document.getElementById('workout-modal');
  const open = () => { modal.classList.add('open'); loadExercisePicker(); };
  const close = () => {
    modal.classList.remove('open');
    state.selectedExercises = [];
    renderSelectedExercises();
  };

  document.getElementById('new-workout-btn').addEventListener('click', open);
  document.getElementById('workout-modal-close').addEventListener('click', close);
  document.getElementById('workout-modal-cancel').addEventListener('click', close);
  modal.addEventListener('click', (e) => { if (e.target === modal) close(); });

  document.getElementById('save-workout-btn').addEventListener('click', saveWorkout);

  // Template buttons
  document.getElementById('load-template-btn').addEventListener('click', openTemplatePicker);
  document.getElementById('save-template-btn').addEventListener('click', saveAsTemplate);

  // Template picker modal
  const tpModal = document.getElementById('template-picker-modal');
  document.getElementById('template-picker-close').addEventListener('click', () => tpModal.classList.remove('open'));
  tpModal.addEventListener('click', (e) => { if (e.target === tpModal) tpModal.classList.remove('open'); });

  // Custom exercise toggle
  document.getElementById('toggle-custom-exercise').addEventListener('click', () => {
    const form = document.getElementById('custom-exercise-form');
    const btn = document.getElementById('toggle-custom-exercise');
    if (form.style.display === 'none') {
      form.style.display = 'block';
      btn.textContent = '✕ Cancel';
      document.getElementById('custom-ex-name').focus();
    } else {
      form.style.display = 'none';
      btn.textContent = '+ Create Custom Exercise';
    }
  });

  // Save custom exercise
  document.getElementById('save-custom-exercise').addEventListener('click', async () => {
    const name = document.getElementById('custom-ex-name').value.trim();
    const category = document.getElementById('custom-ex-category').value;
    if (!name) { toast('Enter an exercise name', 'error'); return; }

    const btn = document.getElementById('save-custom-exercise');
    btn.disabled = true;
    btn.textContent = 'Saving...';
    try {
      const newEx = await post('/exercises/', { name, category });
      state.exercises.push(newEx);
      toast(`"${name}" added to your exercises! 💪`, 'success');

      // Reset form
      document.getElementById('custom-ex-name').value = '';
      document.getElementById('custom-exercise-form').style.display = 'none';
      document.getElementById('toggle-custom-exercise').textContent = '+ Create Custom Exercise';

      // Refresh the picker to show the new exercise
      refreshExercisePicker();
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save';
    }
  });
}

function refreshExercisePicker() {
  // Rebuild categories and grid from current state.exercises
  const cats = [...new Set(state.exercises.map(e => e.category))].sort();
  const catContainer = document.getElementById('exercise-categories');
  const activeCat = catContainer.querySelector('.category-chip.active')?.dataset.cat || 'all';

  catContainer.innerHTML = `<button class="category-chip ${activeCat === 'all' ? 'active' : ''}" data-cat="all">All</button>` +
    cats.map(c => `<button class="category-chip ${activeCat === c ? 'active' : ''}" data-cat="${c}">${formatCategoryName(c)}</button>`).join('');

  catContainer.querySelectorAll('.category-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      catContainer.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      renderExerciseGrid(chip.dataset.cat);
    });
  });

  renderExerciseGrid(activeCat);
}

function formatCategoryName(cat) {
  return cat.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

async function loadExercisePicker() {
  // Always reload exercises to include custom ones
  try {
    state.exercises = await get('/exercises/');
  } catch { state.exercises = []; }

  // Categories
  const cats = [...new Set(state.exercises.map(e => e.category))].sort();
  const catContainer = document.getElementById('exercise-categories');
  catContainer.innerHTML = `<button class="category-chip active" data-cat="all">All</button>` +
    cats.map(c => `<button class="category-chip" data-cat="${c}">${formatCategoryName(c)}</button>`).join('');

  catContainer.querySelectorAll('.category-chip').forEach(chip => {
    chip.addEventListener('click', () => {
      catContainer.querySelectorAll('.category-chip').forEach(c => c.classList.remove('active'));
      chip.classList.add('active');
      renderExerciseGrid(chip.dataset.cat);
    });
  });

  renderExerciseGrid('all');
}

function renderExerciseGrid(category) {
  const filtered = category === 'all'
    ? state.exercises
    : state.exercises.filter(e => e.category === category);

  const grid = document.getElementById('exercise-grid');
  grid.innerHTML = filtered.map(ex => {
    const isSelected = state.selectedExercises.some(s => s.exercise.name === ex.name);
    return `<button class="exercise-chip ${isSelected ? 'selected' : ''}"
      data-name="${ex.name}" data-cat="${ex.category}">${ex.name}</button>`;
  }).join('');

  grid.querySelectorAll('.exercise-chip').forEach(chip => {
    chip.addEventListener('click', () => toggleExercise(chip.dataset.name, chip.dataset.cat));
  });
}

function toggleExercise(name, category) {
  const idx = state.selectedExercises.findIndex(s => s.exercise.name === name);
  if (idx >= 0) {
    state.selectedExercises.splice(idx, 1);
  } else {
    state.selectedExercises.push({
      exercise: { name, category },
      sets: [{ reps: '', weight: '', notes: '', side: '' }],
      isUnilateral: false,
      supersetGroup: null,
    });
  }
  // Refresh chip highlight
  const activeChip = document.querySelector('.category-chip.active');
  renderExerciseGrid(activeChip ? activeChip.dataset.cat : 'all');
  renderSelectedExercises();
}

function renderSelectedExercises() {
  const container = document.getElementById('selected-exercises');
  if (!state.selectedExercises.length) {
    container.innerHTML = '<p class="text-muted" style="font-size:0.85rem">Pick exercises above to add sets</p>';
    return;
  }

  const unit = weightLabel();
  let nextSupersetGroup = 1;
  // Find max existing superset group
  state.selectedExercises.forEach(item => {
    if (item.supersetGroup && item.supersetGroup >= nextSupersetGroup)
      nextSupersetGroup = item.supersetGroup + 1;
  });

  container.innerHTML = state.selectedExercises.map((item, exIdx) => {
    const isUni = item.isUnilateral;
    const ssGroup = item.supersetGroup;
    // Check if next exercise is same superset group (for connector)
    const nextItem = state.selectedExercises[exIdx + 1];
    const showConnector = ssGroup && nextItem && nextItem.supersetGroup === ssGroup;

    return `
    ${ssGroup && (exIdx === 0 || state.selectedExercises[exIdx - 1]?.supersetGroup !== ssGroup) ? `<div class="superset-group">` : ''}
    <div class="card mb-2" style="padding:1rem" data-ex-idx="${exIdx}">
      <div class="flex-between mb-2">
        <h4 style="font-size:0.9rem">${item.exercise.name} <span class="badge badge-gold">${item.exercise.category}</span></h4>
        <button class="btn btn-sm btn-danger" onclick="removeExercise(${exIdx})">Remove</button>
      </div>
      <div class="exercise-toolbar">
        <button class="toolbar-btn ${isUni ? 'active' : ''}" onclick="toggleUnilateral(${exIdx})">
          ↔ Unilateral
        </button>
        <button class="toolbar-btn ${ssGroup ? 'active' : ''}" onclick="toggleSuperset(${exIdx})">
          ⚡ Superset
        </button>
      </div>
      <div class="set-inputs">
        <div class="set-row set-header ${isUni ? 'has-side' : ''}">
          <span>Set</span>${isUni ? '<span>Side</span>' : ''}<span>Reps</span><span>Weight (${unit})</span><span>Notes</span><span></span>
        </div>
        ${item.sets.map((set, sIdx) => `
          <div class="set-row ${isUni ? 'has-side' : ''}">
            <span class="set-num">${sIdx + 1}</span>
            ${isUni ? `
              <div class="side-btn-group">
                <button type="button" class="side-btn ${set.side === 'L' ? 'active-L' : ''}" onclick="setSide(${exIdx},${sIdx},'L')">L</button>
                <button type="button" class="side-btn ${set.side === 'R' ? 'active-R' : ''}" onclick="setSide(${exIdx},${sIdx},'R')">R</button>
              </div>
            ` : ''}
            <input type="number" placeholder="10" value="${set.reps}" onchange="updateSet(${exIdx},${sIdx},'reps',this.value)" />
            <input type="number" placeholder="60" value="${set.weight}" onchange="updateSet(${exIdx},${sIdx},'weight',this.value)" />
            <input type="text" placeholder="optional" value="${set.notes || ''}" onchange="updateSet(${exIdx},${sIdx},'notes',this.value)" />
            <button class="btn btn-icon btn-secondary" onclick="removeSet(${exIdx},${sIdx})" style="font-size:0.8rem">✕</button>
          </div>
        `).join('')}
      </div>
      <button class="btn btn-sm btn-outline mt-1" onclick="addSet(${exIdx})">+ Add Set</button>
    </div>
    ${showConnector ? '<div class="superset-connector"></div>' : ''}
    ${ssGroup && (!nextItem || nextItem.supersetGroup !== ssGroup) ? '</div>' : ''}
    `;
  }).join('');
}

window.removeExercise = (idx) => { state.selectedExercises.splice(idx, 1); renderSelectedExercises(); };
window.addSet = (idx) => {
  const isUni = state.selectedExercises[idx].isUnilateral;
  state.selectedExercises[idx].sets.push({ reps: '', weight: '', notes: '', side: isUni ? 'L' : '' });
  renderSelectedExercises();
};
window.removeSet = (exIdx, sIdx) => {
  state.selectedExercises[exIdx].sets.splice(sIdx, 1);
  if (!state.selectedExercises[exIdx].sets.length) state.selectedExercises.splice(exIdx, 1);
  renderSelectedExercises();
};
window.updateSet = (exIdx, sIdx, field, val) => {
  if (field === 'reps' || field === 'weight') val = parseFloat(val) || 0;
  state.selectedExercises[exIdx].sets[sIdx][field] = val;
};

// ── Unilateral toggle ──
window.toggleUnilateral = (exIdx) => {
  const item = state.selectedExercises[exIdx];
  item.isUnilateral = !item.isUnilateral;
  // Set default side for existing sets
  item.sets.forEach(s => { s.side = item.isUnilateral ? (s.side || 'L') : ''; });
  renderSelectedExercises();
};

// ── Side selector ──
window.setSide = (exIdx, sIdx, side) => {
  const set = state.selectedExercises[exIdx].sets[sIdx];
  set.side = (set.side === side) ? '' : side;
  renderSelectedExercises();
};

// ── Superset toggle ──
window.toggleSuperset = (exIdx) => {
  const item = state.selectedExercises[exIdx];
  if (item.supersetGroup) {
    // Remove from superset
    const group = item.supersetGroup;
    item.supersetGroup = null;
    // If only one left in group, remove that too
    const remaining = state.selectedExercises.filter(e => e.supersetGroup === group);
    if (remaining.length === 1) remaining[0].supersetGroup = null;
  } else {
    // Link with next exercise
    const nextIdx = exIdx + 1;
    if (nextIdx < state.selectedExercises.length) {
      // Find max group number
      let maxGroup = 0;
      state.selectedExercises.forEach(e => {
        if (e.supersetGroup && e.supersetGroup > maxGroup) maxGroup = e.supersetGroup;
      });
      const newGroup = maxGroup + 1;
      item.supersetGroup = newGroup;
      state.selectedExercises[nextIdx].supersetGroup = newGroup;
      toast(`⚡ Superset: ${item.exercise.name} + ${state.selectedExercises[nextIdx].exercise.name}`, 'info');
    } else {
      toast('Add another exercise below to create a superset', 'info');
    }
  }
  renderSelectedExercises();
};

window.viewWorkout = viewWorkout;

async function saveWorkout() {
  const name = document.getElementById('wk-name').value.trim();
  const notes = document.getElementById('wk-notes').value.trim();

  if (!state.selectedExercises.length) {
    toast('Add at least one exercise', 'error');
    return;
  }

  const exercises = state.selectedExercises.map(item => ({
    exercise_name: item.exercise.name,
    category: item.exercise.category,
    is_unilateral: item.isUnilateral || false,
    superset_group: item.supersetGroup || null,
    sets: item.sets.filter(s => s.reps).map(s => ({
      reps: parseInt(s.reps) || 0,
      weight: inputToKg(parseFloat(s.weight) || 0),
      side: item.isUnilateral ? (s.side || null) : null,
      notes: s.notes || '',
    })),
  }));

  if (exercises.some(e => !e.sets.length)) {
    toast('Each exercise needs at least one set with reps', 'error');
    return;
  }

  const btn = document.getElementById('save-workout-btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  try {
    const body = { exercises };
    if (name) body.name = name;
    if (notes) body.notes = notes;

    const saved = await post('/workouts/', body);
    toast('Workout logged! 💪', 'success');

    // Check for PRs in the response
    if (saved.new_prs && saved.new_prs.length) {
      saved.new_prs.forEach((pr, i) => {
        setTimeout(() => {
          prToast(`🏅 New PR! ${pr.exercise}: ${displayWeight(pr.value)} ${weightLabel()} (was ${displayWeight(pr.previous)} ${weightLabel()})`);
        }, 600 * (i + 1));
      });
    }

    // Check achievements in background
    post('/progress/achievements/check').catch(() => {});

    document.getElementById('workout-modal').classList.remove('open');
    state.selectedExercises = [];
    document.getElementById('wk-name').value = '';
    document.getElementById('wk-notes').value = '';
    loadWorkouts();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Save Workout';
  }
}

// ═══════════════════════════════════════════════════════════════
//  WORKOUT TEMPLATES
// ═══════════════════════════════════════════════════════════════

async function openTemplatePicker() {
  const modal = document.getElementById('template-picker-modal');
  modal.classList.add('open');
  const listEl = document.getElementById('template-list');
  const emptyEl = document.getElementById('template-empty');
  listEl.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading templates...</p></div>';
  emptyEl.style.display = 'none';

  try {
    const templates = await get('/templates');
    if (!templates.length) {
      listEl.innerHTML = '';
      emptyEl.style.display = 'block';
      return;
    }
    emptyEl.style.display = 'none';
    listEl.innerHTML = templates.map(t => {
      const exercises = t.exercises.map(e => e.exercise_name).join(', ');
      const usedLabel = t.use_count > 0
        ? `Used ${t.use_count}×`
        : 'Never used';
      return `
      <div class="template-card" data-id="${t.id}">
        <div class="template-card-top">
          <div class="template-card-info">
            <div class="template-card-name">${escapeHtml(t.name)}</div>
            <div class="template-card-meta">
              ${t.exercise_count} exercise${t.exercise_count > 1 ? 's' : ''} · ${t.total_sets} sets · ${usedLabel}
            </div>
            <div class="template-card-exercises">${escapeHtml(exercises)}</div>
          </div>
          <div class="template-card-actions">
            <button class="btn btn-sm btn-primary" onclick="useTemplate('${t.id}')" title="Load into workout">▶ Use</button>
            <button class="btn btn-sm btn-danger" onclick="deleteTemplate('${t.id}')" title="Delete template">✕</button>
          </div>
        </div>
      </div>`;
    }).join('');
  } catch (err) {
    listEl.innerHTML = `<p class="text-muted">Failed to load templates: ${err.message}</p>`;
  }
}

window.useTemplate = async function(templateId) {
  try {
    const t = await post(`/templates/${templateId}/use`);
    // Close template picker
    document.getElementById('template-picker-modal').classList.remove('open');

    // Set workout name
    document.getElementById('wk-name').value = t.name;

    // Load exercises into the workout modal
    state.selectedExercises = t.exercises.map(ex => ({
      exercise: { name: ex.exercise_name, category: ex.category || '' },
      sets: ex.sets.map(s => ({
        reps: s.reps || '',
        weight: s.weight ? displayWeight(s.weight) : '',
        notes: s.notes || '',
        side: s.side || '',
      })),
      isUnilateral: ex.is_unilateral || false,
      supersetGroup: ex.superset_group || null,
    }));

    renderSelectedExercises();
    // Also refresh chips to show them as selected
    const activeChip = document.querySelector('.category-chip.active');
    renderExerciseGrid(activeChip ? activeChip.dataset.cat : 'all');

    toast(`📋 Template "${t.name}" loaded!`, 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
};

async function saveAsTemplate() {
  if (!state.selectedExercises.length) {
    toast('Add exercises first, then save as template', 'error');
    return;
  }

  // Use workout name or prompt
  let name = document.getElementById('wk-name').value.trim();
  if (!name) {
    name = prompt('Give this template a name:');
    if (!name || !name.trim()) return;
    name = name.trim();
  }

  const exercises = state.selectedExercises.map(item => ({
    exercise_name: item.exercise.name,
    category: item.exercise.category,
    is_unilateral: item.isUnilateral || false,
    superset_group: item.supersetGroup || null,
    sets: item.sets.filter(s => s.reps).map(s => ({
      reps: parseInt(s.reps) || 0,
      weight: inputToKg(parseFloat(s.weight) || 0),
      side: item.isUnilateral ? (s.side || null) : null,
      notes: s.notes || '',
    })),
  }));

  // Include exercises even with empty sets (just the structure)
  const exercisesForTemplate = state.selectedExercises.map(item => ({
    exercise_name: item.exercise.name,
    category: item.exercise.category,
    is_unilateral: item.isUnilateral || false,
    superset_group: item.supersetGroup || null,
    sets: item.sets.map(s => ({
      reps: parseInt(s.reps) || 0,
      weight: inputToKg(parseFloat(s.weight) || 0),
      side: item.isUnilateral ? (s.side || null) : null,
      notes: s.notes || '',
    })),
  }));

  const btn = document.getElementById('save-template-btn');
  btn.disabled = true;
  btn.textContent = 'Saving...';

  try {
    await post('/templates', { name, exercises: exercisesForTemplate });
    toast(`💾 Template "${name}" saved!`, 'success');
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Save as Template';
  }
}

window.deleteTemplate = async function(templateId) {
  if (!confirm('Delete this template? This cannot be undone.')) return;
  try {
    await del(`/templates/${templateId}`);
    toast('Template deleted', 'info');
    // Refresh the list
    openTemplatePicker();
  } catch (err) {
    toast(err.message, 'error');
  }
};

// ═══════════════════════════════════════════════════════════════
//  MEALS
// ═══════════════════════════════════════════════════════════════
async function loadMeals() {
  loadDailySummary();   // also populates quick stats bar
  loadMealHistory();
  loadMealCalendar();
  loadRandomRecipe();
}

async function loadDailySummary() {
  const el = document.getElementById('daily-summary');
  try {
    const d = await get('/meals/daily');
    const eaten = Math.round(d.total_calories || 0);
    const target = state.user?.custom_calories || Math.round(d.target_calories || 2500);
    const diff = eaten - target;
    const diffClass = diff >= 0 ? 'text-red' : 'text-green';
    const diffLabel = diff >= 0 ? 'over' : 'remaining';

    document.getElementById('meal-daily-badge').textContent = `${eaten} / ${target} kcal`;

    // ── Quick Stats Bar (pills at top) ──
    const mspCal = document.getElementById('msp-calories');
    const mspP   = document.getElementById('msp-protein');
    const mspC   = document.getElementById('msp-carbs');
    const mspF   = document.getElementById('msp-fat');
    const mspR   = document.getElementById('msp-remaining');
    if (mspCal) mspCal.textContent = eaten;
    if (mspP)   mspP.textContent = `${Math.round(d.total_protein_g || 0)}g`;
    if (mspC)   mspC.textContent = `${Math.round(d.total_carbs_g || 0)}g`;
    if (mspF)   mspF.textContent = `${Math.round(d.total_fat_g || 0)}g`;
    if (mspR) {
      const remaining = Math.max(0, target - eaten);
      mspR.textContent = remaining > 0 ? remaining : (diff >= 0 ? `+${diff}` : '0');
    }

    document.getElementById('meal-daily-badge').textContent = `${eaten} / ${target} kcal`;

    // Macro targets (rough % split)
    const proteinTarget = Math.round(target * 0.30 / 4);  // 30% from protein
    const carbsTarget   = Math.round(target * 0.40 / 4);  // 40% from carbs
    const fatTarget     = Math.round(target * 0.30 / 9);  // 30% from fat
    const protein = Math.round(d.total_protein_g || 0);
    const carbs   = Math.round(d.total_carbs_g || 0);
    const fat     = Math.round(d.total_fat_g || 0);
    const calPct = Math.min((eaten / target) * 100, 100);

    el.innerHTML = `
      <div class="meal-summary-grid">
        <!-- Calorie Ring -->
        <div class="meal-summary-ring">
          <svg viewBox="0 0 100 100" class="summary-ring-svg">
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--bg-input)" stroke-width="7" />
            <circle cx="50" cy="50" r="42" fill="none" stroke="var(--accent)" stroke-width="7"
              stroke-dasharray="${2 * Math.PI * 42}"
              stroke-dashoffset="${2 * Math.PI * 42 - (calPct / 100) * 2 * Math.PI * 42}"
              stroke-linecap="round" transform="rotate(-90 50 50)"
              style="transition: stroke-dashoffset 0.6s ease" />
          </svg>
          <div class="summary-ring-center">
            <span class="summary-ring-val">${eaten}</span>
            <span class="summary-ring-lbl">of ${target}</span>
          </div>
        </div>
        <!-- Macro Bars -->
        <div class="meal-summary-macros">
          <div class="macro-bar-row">
            <div class="macro-bar-label">
              <span>🥩 Protein</span>
              <span class="macro-bar-nums">${protein}g / ${proteinTarget}g</span>
            </div>
            <div class="macro-bar-track">
              <div class="macro-bar-fill protein-fill" style="width:${Math.min((protein / proteinTarget) * 100, 100)}%"></div>
            </div>
          </div>
          <div class="macro-bar-row">
            <div class="macro-bar-label">
              <span>🍞 Carbs</span>
              <span class="macro-bar-nums">${carbs}g / ${carbsTarget}g</span>
            </div>
            <div class="macro-bar-track">
              <div class="macro-bar-fill carbs-fill" style="width:${Math.min((carbs / carbsTarget) * 100, 100)}%"></div>
            </div>
          </div>
          <div class="macro-bar-row">
            <div class="macro-bar-label">
              <span>🥑 Fat</span>
              <span class="macro-bar-nums">${fat}g / ${fatTarget}g</span>
            </div>
            <div class="macro-bar-track">
              <div class="macro-bar-fill fat-fill" style="width:${Math.min((fat / fatTarget) * 100, 100)}%"></div>
            </div>
          </div>
          <div style="text-align:center;margin-top:0.6rem">
            <span class="${diffClass}" style="font-weight:700;font-size:0.95rem">${Math.abs(diff)} kcal ${diffLabel}</span>
          </div>
        </div>
      </div>
    `;
  } catch {
    el.innerHTML = '<p class="text-muted" style="padding:1rem">Log your first meal to see the summary</p>';
  }
}

async function loadMealHistory() {
  const list = document.getElementById('meal-list');
  try {
    const meals = await get('/meals/history?limit=15');
    if (!meals.length) {
      list.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">🍽️</div>
          <h3>No meals logged</h3>
          <p>Describe what you ate and let AI analyze the nutrition!</p>
        </div>`;
      return;
    }
    list.innerHTML = meals.map(m => {
      const date = new Date(m.logged_at || m.created_at).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
      const typeEmoji = { breakfast: '🌅', lunch: '☀️', dinner: '🌙', snack: '🍎' };
      return `
        <div class="item-card">
          <div class="item-card-header">
            <h4>${typeEmoji[m.meal_type] || '🍽️'} ${capitalize(m.meal_type || 'meal')}</h4>
            <span class="item-date">${date}</span>
          </div>
          <p style="font-size:0.85rem;color:var(--text-secondary);margin:0.3rem 0 0.5rem">${m.description || ''}</p>
          <div class="item-card-body">
            <span class="item-tag accent">${Math.round(m.total_calories || 0)} kcal</span>
            <span class="item-tag">P: ${Math.round(m.total_protein_g || 0)}g</span>
            <span class="item-tag">C: ${Math.round(m.total_carbs_g || 0)}g</span>
            <span class="item-tag">F: ${Math.round(m.total_fat_g || 0)}g</span>
            <span class="item-tag" style="font-size:0.7rem;color:var(--text-muted)">via ${m.source || '?'}</span>
          </div>
          <div style="margin-top:0.5rem">
            <button class="btn btn-sm btn-danger" onclick="deleteMeal('${m._id || m.id}')">Delete</button>
          </div>
        </div>`;
    }).join('');
  } catch {
    list.innerHTML = '<p class="text-muted" style="padding:1rem">Error loading meals</p>';
  }
}

window.deleteMeal = async (id) => {
  try {
    await del(`/meals/${id}`);
    toast('Meal deleted', 'success');
    loadMeals();
  } catch (err) {
    toast(err.message, 'error');
  }
};

// ── Log Meal ──
document.getElementById('log-meal-btn').addEventListener('click', async () => {
  const desc = document.getElementById('meal-description').value.trim();
  if (!desc) { toast('Describe what you ate', 'error'); return; }

  const btn = document.getElementById('log-meal-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:16px;height:16px;border-width:2px"></div> Analyzing...';

  const resultDiv = document.getElementById('meal-ai-result');

  try {
    const meal = await post('/meals/', {
      description: desc,
      meal_type: document.getElementById('meal-type').value,
    });

    // Show AI result
    const items = meal.items || [];
    resultDiv.style.display = 'block';
    resultDiv.innerHTML = `
      <div class="ai-result">
        <ul class="ai-food-list">
          ${items.map(it => `
            <li class="ai-food-item">
              <div>
                <span class="ai-food-name">${it.name || it.food || '?'}</span>
                <span class="ai-food-portion">${it.portion || ''}</span>
              </div>
              <span class="ai-food-cal">${Math.round(it.calories || 0)} kcal</span>
            </li>
          `).join('')}
        </ul>
        <hr class="divider" />
        <div class="flex-between">
          <div>
            <span class="badge badge-gold">${Math.round(meal.total_calories || 0)} kcal</span>
            <span class="badge badge-green" style="margin-left:0.3rem">P: ${Math.round(meal.total_protein_g || 0)}g</span>
            <span class="badge badge-blue" style="margin-left:0.3rem">C: ${Math.round(meal.total_carbs_g || 0)}g</span>
          </div>
          <span class="text-muted" style="font-size:0.75rem">Source: ${meal.source || '?'}</span>
        </div>
      </div>
    `;

    toast('Meal logged! ✨', 'success');
    document.getElementById('meal-description').value = '';
    loadDailySummary();
    loadMealHistory();
    loadMealCalendar();
    // Check achievements in background
    post('/progress/achievements/check').catch(() => {});

    // Auto-hide result after 8 seconds
    setTimeout(() => { resultDiv.style.display = 'none'; }, 8000);
  } catch (err) {
    toast(err.message, 'error');
    resultDiv.style.display = 'none';
  } finally {
    btn.disabled = false;
    btn.innerHTML = '✨ Analyze';
  }
});

// ── Manual Meal Entry ──
document.getElementById('toggle-manual-entry').addEventListener('click', () => {
  const panel = document.getElementById('manual-entry-panel');
  const btn = document.getElementById('toggle-manual-entry');
  if (panel.style.display === 'none') {
    panel.style.display = 'block';
    btn.textContent = 'Hide';
  } else {
    panel.style.display = 'none';
    btn.textContent = 'Show';
  }
});

let manualItemIdx = 1;
document.getElementById('add-manual-item-btn').addEventListener('click', () => {
  const list = document.getElementById('manual-items-list');
  const row = document.createElement('div');
  row.className = 'manual-item-row';
  row.dataset.idx = manualItemIdx++;
  row.innerHTML = `
    <button type="button" class="remove-manual-item" onclick="this.parentElement.remove()">✕</button>
    <div class="manual-item-grid">
      <div>
        <label class="input-label">Food Name</label>
        <input type="text" class="input mi-name" placeholder="e.g. Brown Rice" />
      </div>
      <div>
        <label class="input-label">Quantity</label>
        <input type="text" class="input mi-quantity" placeholder="e.g. 150g" />
      </div>
      <div>
        <label class="input-label">Calories</label>
        <input type="number" class="input mi-calories" placeholder="kcal" min="0" />
      </div>
      <div>
        <label class="input-label">Protein (g)</label>
        <input type="number" class="input mi-protein" placeholder="g" min="0" step="0.1" />
      </div>
      <div>
        <label class="input-label">Carbs (g)</label>
        <input type="number" class="input mi-carbs" placeholder="g" min="0" step="0.1" />
      </div>
      <div>
        <label class="input-label">Fat (g)</label>
        <input type="number" class="input mi-fat" placeholder="g" min="0" step="0.1" />
      </div>
    </div>
  `;
  list.appendChild(row);
});

document.getElementById('save-manual-meal-btn').addEventListener('click', async () => {
  const rows = document.querySelectorAll('.manual-item-row');
  const items = [];
  for (const row of rows) {
    const name = row.querySelector('.mi-name').value.trim();
    const calories = parseFloat(row.querySelector('.mi-calories').value) || 0;
    if (!name && !calories) continue;
    items.push({
      name: name || 'Unknown food',
      quantity: row.querySelector('.mi-quantity').value.trim() || null,
      calories,
      protein_g: parseFloat(row.querySelector('.mi-protein').value) || 0,
      carbs_g: parseFloat(row.querySelector('.mi-carbs').value) || 0,
      fat_g: parseFloat(row.querySelector('.mi-fat').value) || 0,
    });
  }
  if (!items.length) { toast('Add at least one food item', 'error'); return; }

  const btn = document.getElementById('save-manual-meal-btn');
  btn.disabled = true;
  btn.innerHTML = '<div class="spinner" style="width:14px;height:14px;border-width:2px"></div> Saving...';

  try {
    await post('/meals/manual', {
      meal_type: document.getElementById('manual-meal-type').value,
      items,
    });
    toast('Meal saved! ✓', 'success');
    // Reset form
    document.getElementById('manual-items-list').innerHTML = `
      <div class="manual-item-row" data-idx="0">
        <div class="manual-item-grid">
          <div><label class="input-label">Food Name</label><input type="text" class="input mi-name" placeholder="e.g. Chicken Breast" /></div>
          <div><label class="input-label">Quantity</label><input type="text" class="input mi-quantity" placeholder="e.g. 200g, 1 cup" /></div>
          <div><label class="input-label">Calories</label><input type="number" class="input mi-calories" placeholder="kcal" min="0" /></div>
          <div><label class="input-label">Protein (g)</label><input type="number" class="input mi-protein" placeholder="g" min="0" step="0.1" /></div>
          <div><label class="input-label">Carbs (g)</label><input type="number" class="input mi-carbs" placeholder="g" min="0" step="0.1" /></div>
          <div><label class="input-label">Fat (g)</label><input type="number" class="input mi-fat" placeholder="g" min="0" step="0.1" /></div>
        </div>
      </div>`;
    manualItemIdx = 1;
    loadDailySummary();
    loadMealHistory();
    loadMealCalendar();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '💾 Save Meal';
  }
});

// ── Meal Calendar ──
let mealCalYear, mealCalMonth;
{
  const now = new Date();
  mealCalYear = now.getFullYear();
  mealCalMonth = now.getMonth() + 1;
}

document.getElementById('meal-cal-prev').addEventListener('click', () => {
  mealCalMonth--;
  if (mealCalMonth < 1) { mealCalMonth = 12; mealCalYear--; }
  loadMealCalendar();
});
document.getElementById('meal-cal-next').addEventListener('click', () => {
  mealCalMonth++;
  if (mealCalMonth > 12) { mealCalMonth = 1; mealCalYear++; }
  loadMealCalendar();
});

async function loadMealCalendar() {
  const grid = document.getElementById('meal-calendar-grid');
  const label = document.getElementById('meal-cal-month-label');
  const monthNames = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  label.textContent = `${monthNames[mealCalMonth - 1]} ${mealCalYear}`;

  try {
    const days = await get(`/meals/calendar?year=${mealCalYear}&month=${mealCalMonth}`);
    const dayMap = {};
    days.forEach(d => { dayMap[d.day] = d; });

    const firstDay = new Date(mealCalYear, mealCalMonth - 1, 1).getDay();
    const daysInMonth = new Date(mealCalYear, mealCalMonth, 0).getDate();
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === mealCalYear && today.getMonth() + 1 === mealCalMonth;

    const dayLabels = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];
    let html = '<div class="meal-cal-grid">';
    dayLabels.forEach(l => { html += `<div class="meal-cal-header">${l}</div>`; });

    // Empty cells before first day
    for (let i = 0; i < firstDay; i++) {
      html += '<div class="meal-cal-day empty"></div>';
    }

    for (let d = 1; d <= daysInMonth; d++) {
      const info = dayMap[d];
      const hasMeals = info && info.has_meals;
      const isToday = isCurrentMonth && d === today.getDate();
      let cls = 'meal-cal-day';
      if (hasMeals) cls += ' has-meals';
      if (isToday) cls += ' today';

      html += `<div class="${cls}" onclick="showMealCalDay(${d}, ${JSON.stringify(info || {}).replace(/"/g, '&quot;')})">`;
      html += `<span class="day-num">${d}</span>`;
      if (hasMeals) {
        html += `<span class="day-cal">${Math.round(info.total_calories || 0)}</span>`;
        html += `<span class="day-meals-count">${info.meal_count} meal${info.meal_count > 1 ? 's' : ''}</span>`;
      }
      html += '</div>';
    }

    html += '</div>';
    grid.innerHTML = html;
  } catch {
    grid.innerHTML = '<p class="text-muted" style="padding:1rem">Could not load calendar</p>';
  }
}

window.showMealCalDay = (day, info) => {
  const detail = document.getElementById('meal-cal-day-detail');
  if (!info || !info.has_meals) {
    detail.style.display = 'block';
    detail.innerHTML = `
      <div class="meal-cal-day-detail">
        <h4>${day} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][mealCalMonth-1]} ${mealCalYear}</h4>
        <p class="text-muted">No meals logged this day</p>
      </div>`;
    return;
  }

  // Highlight selected
  document.querySelectorAll('.meal-cal-day.selected').forEach(el => el.classList.remove('selected'));
  event.currentTarget?.classList.add('selected');

  const t = info;
  detail.style.display = 'block';
  detail.innerHTML = `
    <div class="meal-cal-day-detail">
      <h4>${day} ${['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][mealCalMonth-1]} ${mealCalYear}</h4>
      <div class="macro-row">
        <span class="badge badge-gold">🔥 ${Math.round(t.total_calories || 0)} kcal</span>
        <span class="badge badge-green">🥩 P: ${Math.round(t.total_protein_g || 0)}g</span>
        <span class="badge badge-blue">🍞 C: ${Math.round(t.total_carbs_g || 0)}g</span>
        <span class="badge badge-orange" style="background:rgba(255,152,0,0.15);color:#ff9800">🥑 F: ${Math.round(t.total_fat_g || 0)}g</span>
      </div>
      <p style="margin-top:0.5rem;font-size:0.8rem;color:var(--text-secondary)">${info.meal_count} meal${info.meal_count > 1 ? 's' : ''} logged</p>
    </div>`;
};

// ═══════════════════════════════════════════════════════════════
//  HIGH-PROTEIN RECIPES
// ═══════════════════════════════════════════════════════════════

async function loadRandomRecipe() {
  const container = document.getElementById('recipe-content');
  if (!container) return;

  container.innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading recipe...</p></div>';

  try {
    const r = await get('/recipes/random');
    renderRecipe(r);
  } catch (err) {
    container.innerHTML = '<p class="text-muted" style="padding:1rem">Could not load recipe.</p>';
  }
}

function renderRecipe(r) {
  const container = document.getElementById('recipe-content');
  if (!container) return;

  const mealTypeEmojis = {
    breakfast: '🌅 Breakfast',
    lunch: '☀️ Lunch',
    dinner: '🌙 Dinner',
    snack: '🍎 Snack',
  };

  container.innerHTML = `
    <div class="recipe-detail">
      <div class="recipe-header-row">
        <div class="recipe-title-area">
          <span class="recipe-emoji">${r.emoji}</span>
          <div>
            <h3 class="recipe-name">${escapeHtml(r.name)}</h3>
            <div class="recipe-meta">
              <span class="recipe-meta-item">⏱ ${r.prep_time}</span>
              <span class="recipe-meta-item">🍽 ${r.servings} serving${r.servings > 1 ? 's' : ''}</span>
              <span class="recipe-meta-item">${mealTypeEmojis[r.meal_type] || r.meal_type}</span>
              <span class="recipe-meta-item recipe-counter">${r.recipe_number}/${r.total_recipes}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="recipe-macros">
        <div class="recipe-macro recipe-macro-cal">
          <div class="recipe-macro-value">${r.calories}</div>
          <div class="recipe-macro-label">kcal</div>
        </div>
        <div class="recipe-macro recipe-macro-protein">
          <div class="recipe-macro-value">${r.protein_g}g</div>
          <div class="recipe-macro-label">Protein</div>
        </div>
        <div class="recipe-macro recipe-macro-carbs">
          <div class="recipe-macro-value">${r.carbs_g}g</div>
          <div class="recipe-macro-label">Carbs</div>
        </div>
        <div class="recipe-macro recipe-macro-fat">
          <div class="recipe-macro-value">${r.fat_g}g</div>
          <div class="recipe-macro-label">Fat</div>
        </div>
      </div>

      <div class="recipe-sections">
        <div class="recipe-ingredients">
          <h4 class="recipe-section-title">🛒 Ingredients</h4>
          <ul class="recipe-ingredient-list">
            ${r.ingredients.map(ing => `<li>${escapeHtml(ing)}</li>`).join('')}
          </ul>
        </div>
        <div class="recipe-steps">
          <h4 class="recipe-section-title">👨‍🍳 Prep Steps</h4>
          <ol class="recipe-step-list">
            ${r.instructions.map(step => `<li>${escapeHtml(step)}</li>`).join('')}
          </ol>
        </div>
      </div>
    </div>
  `;
}

// Wire up recipe refresh button after DOM loads
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('refresh-recipe-btn');
  if (btn) btn.addEventListener('click', loadRandomRecipe);
});

// ═══════════════════════════════════════════════════════════════
//  GOALS
// ═══════════════════════════════════════════════════════════════
let journeyChartInstance = null;

async function loadGoals() {
  loadNutritionPlan();
  loadGoalTips();
  loadCustomTargets();
}

function getEffectiveTargets(plan) {
  const u = state.user || {};
  return {
    calories: u.custom_calories || Math.round(plan.target_calories || 0),
    protein_g: u.custom_protein_g || Math.round(plan.protein_g || 0),
    carbs_g: u.custom_carbs_g || Math.round(plan.carbs_g || 0),
    fat_g: u.custom_fat_g || Math.round(plan.fat_g || 0),
    isCustom: !!(u.custom_calories || u.custom_protein_g || u.custom_carbs_g || u.custom_fat_g),
  };
}

async function loadNutritionPlan() {
  const content = document.getElementById('nutrition-plan-content');
  const journeyCard = document.getElementById('journey-card');
  const heroTitle = document.getElementById('goal-hero-title');
  const heroSub = document.getElementById('goal-hero-sub');
  const heroIcon = document.getElementById('goal-hero-icon');

  try {
    const [plan, daily] = await Promise.all([
      get('/goals/nutrition-plan'),
      get('/meals/daily').catch(() => null),
    ]);

    // ── Hero ──
    const goalLabels = { lose_weight: 'Fat Loss', gain_muscle: 'Muscle Gain', maintain: 'Maintenance' };
    const goalIcons  = { lose_weight: '📉', gain_muscle: '💪', maintain: '⚖️' };
    const goalMottos = {
      lose_weight: 'Every deficit is a deposit in your dream body account.',
      gain_muscle: 'Building muscle, one rep and one meal at a time.',
      maintain: 'Consistency is the real superpower.',
    };
    const g = plan.goal || 'maintain';
    document.getElementById('goal-type-badge').textContent = goalLabels[g] || g;
    heroIcon.textContent = goalIcons[g] || '🎯';
    heroTitle.textContent = goalLabels[g] || 'Your Plan';
    heroSub.textContent = goalMottos[g] || 'Your personalized plan';

    // ── Pill bar ──
    const dir = plan.direction || 'none';
    const defLabel = dir === 'loss' ? 'Deficit' : dir === 'gain' ? 'Surplus' : 'Balance';
    document.getElementById('gp-bmr').textContent = Math.round(plan.bmr || 0);
    document.getElementById('gp-tdee').textContent = Math.round(plan.tdee || 0);

    const eff = getEffectiveTargets(plan);
    document.getElementById('gp-target').textContent = eff.calories;
    document.getElementById('gp-dir-icon').textContent = dir === 'loss' ? '📉' : dir === 'gain' ? '📈' : '⚖️';
    document.getElementById('gp-deficit').textContent = plan.daily_deficit || 0;
    document.getElementById('gp-deficit-lbl').textContent = defLabel;
    document.getElementById('gp-deficit-pct').textContent = (plan.deficit_pct || 0) + '%';

    // ── Journey card ──
    if (plan.timeline && plan.timeline.estimated_weeks > 0) {
      journeyCard.style.display = 'block';
      const tl = plan.timeline;
      const curW = displayWeight(tl.current_weight || 0);
      const tgtW = displayWeight(tl.target_weight || 0);
      const wl = weightLabel();
      const diff = Math.abs((tl.current_weight || 0) - (tl.target_weight || 0));
      // progress % (0 = just started, 100 = done) — for now 0 since we don't track historical
      const progressPct = 0;

      document.getElementById('journey-start-wt').textContent = `${curW} ${wl}`;
      document.getElementById('journey-end-wt').textContent = `${tgtW} ${wl}`;
      document.getElementById('journey-fill').style.width = `${progressPct}%`;
      document.getElementById('journey-pct').textContent = `${progressPct}% there`;

      document.getElementById('journey-eta-badge').textContent = `⏱ ${tl.estimated_weeks} wk`;
      document.getElementById('journey-eta-badge').className = 'badge badge-gold';

      // Stats grid
      const wkChange = displayWeight(plan.weekly_weight_change_kg || 0);
      const moChange = displayWeight(plan.monthly_weight_change_kg || 0);
      const butterSticks = ((diff) / 0.113).toFixed(0); // 1 stick butter ≈ 113g
      document.getElementById('journey-stats').innerHTML = `
        <div class="j-stat"><div class="j-stat-val">${plan.daily_deficit || 0}</div><div class="j-stat-lbl">Daily ${defLabel} (kcal)</div></div>
        <div class="j-stat"><div class="j-stat-val">${wkChange} ${wl}</div><div class="j-stat-lbl">Per Week</div></div>
        <div class="j-stat"><div class="j-stat-val">${moChange} ${wl}</div><div class="j-stat-lbl">Per Month</div></div>
        <div class="j-stat"><div class="j-stat-val">${tl.estimated_weeks} wk</div><div class="j-stat-lbl">${tl.estimated_months || '?'} months</div></div>
      `;

      // Motivational nugget
      const funFacts = [
        `That's like melting away ${butterSticks} sticks of butter 🧈`,
        `${displayWeight(diff)} ${wl} is roughly ${(diff * 2.2 / 0.875).toFixed(0)} cups of body fat gone 🫠`,
        `At this pace, you'll be a different person in just ${tl.estimated_months} months 🔥`,
        `Every single day you're ${plan.daily_deficit} kcal closer to your dream body 💪`,
        `${tl.estimated_weeks} weeks is only ${tl.estimated_weeks * 7} days — you got this! 🚀`,
      ];
      const fact = funFacts[Math.floor(Math.random() * funFacts.length)];
      document.getElementById('journey-motivation').innerHTML = `
        <div class="journey-motiv-inner">
          <span class="journey-motiv-icon">✨</span>
          <span>${fact}</span>
        </div>`;

      // Projected weight chart
      renderJourneyChart(tl, plan, wl);
    } else {
      journeyCard.style.display = 'none';
    }

    // ── Nutrition plan content (calorie ring + macros) ──
    const todayCal = Math.round(daily?.total_calories || 0);
    const todayP   = Math.round(daily?.total_protein_g || 0);
    const todayC   = Math.round(daily?.total_carbs_g || 0);
    const todayF   = Math.round(daily?.total_fat_g || 0);
    const tgtP = eff.protein_g, tgtC = eff.carbs_g, tgtF = eff.fat_g, tgtCal = eff.calories;
    const calProg = tgtCal ? Math.min(100, Math.round(todayCal / tgtCal * 100)) : 0;
    const pProg = tgtP ? Math.min(100, Math.round(todayP / tgtP * 100)) : 0;
    const cProg = tgtC ? Math.min(100, Math.round(todayC / tgtC * 100)) : 0;
    const fProg = tgtF ? Math.min(100, Math.round(todayF / tgtF * 100)) : 0;
    const calRingPct = Math.min(calProg, 100);
    const calRingDeg = Math.round(calRingPct * 3.6);

    const overCal = todayCal > tgtCal;
    const ringColor = overCal ? '#e74c3c' : 'var(--accent)';

    content.innerHTML = `
      <div class="np-layout">
        <div class="np-ring-col">
          <div class="calorie-ring" style="--ring-deg:${calRingDeg}deg;--ring-color:${ringColor}">
            <div class="calorie-ring-inner">
              <div class="cr-val">${todayCal}</div>
              <div class="cr-lbl">of ${tgtCal} kcal</div>
              <div class="cr-pct">${calProg}%</div>
            </div>
          </div>
          ${eff.isCustom ? '<span class="badge badge-gold" style="margin-top:0.5rem;font-size:0.65rem">🎛️ Custom</span>' : ''}
        </div>
        <div class="np-macros-col">
          ${eff.isCustom ? '' : `<p style="font-size:0.7rem;color:var(--text-muted);margin-bottom:0.6rem">
            P: ${(plan.protein_g/(parseFloat(state.user?.weight_kg)||1)).toFixed(1)} g/kg · F: ${(plan.fat_g/(parseFloat(state.user?.weight_kg)||1)).toFixed(1)} g/kg · C: remainder
          </p>`}
          <div class="np-macro-bar">
            <div class="np-macro-hdr"><span>🥩 Protein${eff.isCustom?'':` (${plan.protein_pct||0}%)`}</span><span>${todayP}g / ${tgtP}g</span></div>
            <div class="progress-track"><div class="progress-fill green" style="width:${pProg}%"></div></div>
          </div>
          <div class="np-macro-bar">
            <div class="np-macro-hdr"><span>🍞 Carbs${eff.isCustom?'':` (${plan.carbs_pct||0}%)`}</span><span>${todayC}g / ${tgtC}g</span></div>
            <div class="progress-track"><div class="progress-fill blue" style="width:${cProg}%"></div></div>
          </div>
          <div class="np-macro-bar">
            <div class="np-macro-hdr"><span>🥑 Fat${eff.isCustom?'':` (${plan.fat_pct||0}%)`}</span><span>${todayF}g / ${tgtF}g</span></div>
            <div class="progress-track"><div class="progress-fill orange" style="width:${fProg}%"></div></div>
          </div>
          <p style="font-size:0.66rem;color:var(--text-muted);margin-top:0.6rem;text-align:center">
            ${Math.round(plan.tdee||0)} TDEE ${dir==='loss'?'−':dir==='gain'?'+':'='} ${plan.daily_deficit||0} = ${tgtCal} kcal/day
          </p>
        </div>
      </div>
    `;

    // ── Scorecard ──
    renderScorecard(todayCal, todayP, todayC, todayF, tgtCal, tgtP, tgtC, tgtF);

  } catch {
    content.innerHTML = '<p class="text-muted" style="padding:1rem">Complete your profile (age, weight, height) to see your plan.</p>';
    document.getElementById('goal-hero-title').textContent = 'Set Up Your Profile';
    document.getElementById('goal-hero-sub').textContent = 'Add your stats in Settings to unlock your personalised plan';
  }
}

function renderJourneyChart(tl, plan, wl) {
  const ctx = document.getElementById('journey-chart')?.getContext('2d');
  if (!ctx) return;
  if (journeyChartInstance) journeyChartInstance.destroy();

  const weeks = tl.estimated_weeks || 12;
  const startW = tl.current_weight || 0;
  const endW = tl.target_weight || startW;
  const dir = plan.direction || 'none';
  const rate = tl.rate_per_week_kg || 0;

  const labels = [];
  const data = [];
  for (let w = 0; w <= weeks; w++) {
    labels.push(w === 0 ? 'Now' : `Wk ${w}`);
    let projected = dir === 'loss' ? startW - (rate * w) : startW + (rate * w);
    // Clamp to target
    if (dir === 'loss') projected = Math.max(projected, endW);
    else if (dir === 'gain') projected = Math.min(projected, endW);
    data.push(+displayWeight(projected));
  }

  journeyChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: `Projected Weight (${wl})`,
        data,
        borderColor: '#c9a84c',
        backgroundColor: 'rgba(201,168,76,0.08)',
        fill: true,
        tension: 0.35,
        pointRadius: 0,
        pointHoverRadius: 5,
        pointHoverBackgroundColor: '#c9a84c',
        borderWidth: 2.5,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(20,20,20,0.92)',
          titleColor: '#c9a84c',
          bodyColor: '#ddd',
          padding: 10,
          cornerRadius: 8,
          displayColors: false,
        },
      },
      scales: {
        x: {
          ticks: { color: '#888', font: { size: 10 }, maxTicksLimit: 8 },
          grid: { display: false },
        },
        y: {
          ticks: { color: '#888', font: { size: 10 },
            callback: v => `${v} ${wl}`,
          },
          grid: { color: 'rgba(255,255,255,0.04)' },
        },
      },
    },
  });
}

function renderScorecard(cal, p, c, f, tCal, tP, tC, tF) {
  const el = document.getElementById('scorecard-content');
  const gradeEl = document.getElementById('scorecard-grade');

  // Calculate accuracy for each macro (0-100, 100 = perfect)
  const acc = (actual, target) => target > 0 ? Math.max(0, 100 - Math.abs(actual - target) / target * 100) : 100;
  const calAcc = acc(cal, tCal);
  const pAcc   = acc(p, tP);
  const cAcc   = acc(c, tC);
  const fAcc   = acc(f, tF);
  const avg = (calAcc * 2 + pAcc + cAcc + fAcc) / 5; // calories weighted 2x

  // Grade
  let grade, gradeColor, gradeMsg;
  if (avg >= 90)      { grade = 'A+'; gradeColor = '#27ae60'; gradeMsg = 'Perfect day! You nailed it 🏆'; }
  else if (avg >= 80) { grade = 'A';  gradeColor = '#2ecc71'; gradeMsg = 'Excellent! Right on track 💚'; }
  else if (avg >= 70) { grade = 'B';  gradeColor = '#c9a84c'; gradeMsg = 'Good job! Small tweaks needed 👍'; }
  else if (avg >= 55) { grade = 'C';  gradeColor = '#f39c12'; gradeMsg = 'Decent — try to tighten macros 🔧'; }
  else if (avg >= 40) { grade = 'D';  gradeColor = '#e67e22'; gradeMsg = 'Needs work — log more meals 📝'; }
  else                { grade = 'F';  gradeColor = '#e74c3c'; gradeMsg = 'Log your meals to get graded! 🍽️'; }

  if (cal === 0 && p === 0) {
    grade = '—'; gradeColor = '#888'; gradeMsg = 'Log your first meal today to get your grade';
  }

  gradeEl.textContent = grade;
  gradeEl.style.background = gradeColor;

  const bar = (label, emoji, actual, target, unit, color) => {
    const pct = target > 0 ? Math.min(100, Math.round(actual / target * 100)) : 0;
    const accuracy = acc(actual, target);
    let status = '🟢', valColor = '#27ae60';
    if (accuracy < 50) { status = '🔴'; valColor = '#e74c3c'; }
    else if (accuracy < 75) { status = '🟡'; valColor = '#f39c12'; }
    return `
      <div class="sc-row">
        <span class="sc-label">${emoji} ${label}</span>
        <div class="sc-bar-wrap">
          <div class="progress-track" style="height:10px"><div class="progress-fill ${color}" style="width:${pct}%"></div></div>
        </div>
        <span class="sc-val" style="color:${valColor}">${actual}${unit} / ${target}${unit}</span>
        <span class="sc-status">${status}</span>
      </div>`;
  };

  el.innerHTML = `
    <div class="scorecard-msg">${gradeMsg}</div>
    <div class="scorecard-bars">
      ${bar('Calories', '🔥', cal, tCal, '', 'gold')}
      ${bar('Protein', '🥩', p, tP, 'g', 'green')}
      ${bar('Carbs', '🍞', c, tC, 'g', 'blue')}
      ${bar('Fat', '🥑', f, tF, 'g', 'orange')}
    </div>
    <p class="sc-tip">💡 Tip: Log all your meals to improve your daily grade!</p>
  `;
}

async function loadGoalTips() {
  const el = document.getElementById('goal-tips');
  try {
    const data = await get('/goals/coaching-tips');
    const tips = data.tips || data || [];
    renderTips('goal-tips', Array.isArray(tips) ? tips : []);
  } catch {
    el.innerHTML = '<p class="text-muted" style="padding:1rem">Could not load tips</p>';
  }
}

document.getElementById('refresh-tips-btn').addEventListener('click', () => {
  document.getElementById('goal-tips').innerHTML = '<div class="loading-state"><div class="spinner"></div><p>Loading fresh tips…</p></div>';
  loadGoalTips();
});

// ── Custom Target Dropdown Toggle ──
document.getElementById('toggle-custom-targets').addEventListener('click', () => {
  const dropdown = document.getElementById('macro-dropdown');
  dropdown.classList.toggle('open');
});

// ── Custom Macro Targets ──
function loadCustomTargets() {
  const u = state.user || {};
  document.getElementById('custom-cal').value = u.custom_calories || '';
  document.getElementById('custom-protein').value = u.custom_protein_g || '';
  document.getElementById('custom-carbs').value = u.custom_carbs_g || '';
  document.getElementById('custom-fat').value = u.custom_fat_g || '';

  const hasCustom = !!(u.custom_calories || u.custom_protein_g || u.custom_carbs_g || u.custom_fat_g);
  document.getElementById('reset-custom-targets').style.display = hasCustom ? 'inline-flex' : 'none';
  const summary = document.getElementById('custom-targets-summary');
  if (hasCustom) {
    summary.textContent = '✓ Using custom targets';
    summary.classList.add('active');
  } else {
    summary.textContent = 'Tap to set your own targets';
    summary.classList.remove('active');
  }
}

document.getElementById('save-custom-targets').addEventListener('click', async () => {
  const btn = document.getElementById('save-custom-targets');
  btn.disabled = true;
  btn.textContent = 'Saving…';
  try {
    const cal = parseInt(document.getElementById('custom-cal').value) || null;
    const protein = parseInt(document.getElementById('custom-protein').value) || null;
    const carbs = parseInt(document.getElementById('custom-carbs').value) || null;
    const fat = parseInt(document.getElementById('custom-fat').value) || null;
    const body = {};
    body.custom_calories = cal;
    body.custom_protein_g = protein;
    body.custom_carbs_g = carbs;
    body.custom_fat_g = fat;
    Object.keys(body).forEach(k => { if (body[k] === null) body[k] = 0; });
    state.user = await put('/auth/me', body);
    toast('Custom targets saved! 🎯', 'success');
    loadNutritionPlan();
    loadCustomTargets();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = '💾 Save Targets';
  }
});

document.getElementById('reset-custom-targets').addEventListener('click', async () => {
  const btn = document.getElementById('reset-custom-targets');
  btn.disabled = true;
  try {
    state.user = await put('/auth/me', {
      custom_calories: 0, custom_protein_g: 0, custom_carbs_g: 0, custom_fat_g: 0,
    });
    document.getElementById('custom-cal').value = '';
    document.getElementById('custom-protein').value = '';
    document.getElementById('custom-carbs').value = '';
    document.getElementById('custom-fat').value = '';
    toast('Reset to auto-calculated targets', 'success');
    loadNutritionPlan();
    loadCustomTargets();
  } catch (err) {
    toast(err.message, 'error');
  } finally {
    btn.disabled = false;
  }
});

// ═══════════════════════════════════════════════════════════════
//  WATER TRACKER
// ═══════════════════════════════════════════════════════════════
async function loadWaterTracker() {
  try {
    const data = await get('/progress/water');
    updateWaterUI(data.glasses, data.goal);
  } catch {
    updateWaterUI(0, 8);
  }
}

function updateWaterUI(glasses, goal) {
  document.getElementById('water-badge').textContent = `${glasses} / ${goal}`;
  document.getElementById('water-fill').style.width = `${Math.min(glasses / goal, 1) * 100}%`;

  document.querySelectorAll('.water-glass').forEach(el => {
    const num = parseInt(el.dataset.glass);
    if (num <= glasses) {
      el.classList.add('filled');
    } else {
      el.classList.remove('filled');
    }
  });
}

document.getElementById('add-water-btn').addEventListener('click', async () => {
  try {
    const data = await post('/progress/water', {});
    updateWaterUI(data.glasses, data.goal);
    toast('💧 +1 glass!', 'success');
    // Check hydration achievement
    if (data.glasses >= 8) {
      post('/progress/achievements/check').catch(() => {});
    }
  } catch (err) {
    toast(err.message, 'error');
  }
});

document.getElementById('undo-water-btn').addEventListener('click', async () => {
  try {
    const data = await del('/progress/water');
    updateWaterUI(data.glasses, data.goal);
    toast('Removed last glass', 'info');
  } catch (err) {
    toast(err.message, 'error');
  }
});


// ═══════════════════════════════════════════════════════════════
//  PROGRESS PAGE
// ═══════════════════════════════════════════════════════════════
let calorieTrendChart = null;
let workoutFreqChart = null;
let strengthChart = null;
let weightChart = null;
let allAchievements = [];

async function loadProgress() {
  // Load everything in parallel
  const [overview, calTrend, wkFreq, strengthData, prs, achievements, weightLog] = await Promise.allSettled([
    get('/progress/overview'),
    get('/progress/calorie-trend?days=30'),
    get('/progress/workout-frequency?weeks=12'),
    get('/progress/strength-trend'),
    get('/progress/prs'),
    get('/progress/achievements'),
    get('/progress/weight-log?days=90'),
  ]);

  if (overview.status === 'fulfilled') renderProgressOverview(overview.value);
  if (calTrend.status === 'fulfilled') renderCalorieTrendChart(calTrend.value);
  if (wkFreq.status === 'fulfilled') renderWorkoutFreqChart(wkFreq.value);
  if (strengthData.status === 'fulfilled') renderStrengthChart(strengthData.value);
  if (prs.status === 'fulfilled') renderPRs(prs.value);
  if (achievements.status === 'fulfilled') renderAchievements(achievements.value);
  if (weightLog.status === 'fulfilled') renderWeightTracker(weightLog.value);

  // Heatmap
  loadHeatmap();
}


// ── Progress Overview ──
function renderProgressOverview(data) {
  const streak = data.current_streak || 0;
  const heroTitle = document.getElementById('prog-hero-title');
  const heroSub = document.getElementById('prog-hero-sub');
  const memberBadge = document.getElementById('prog-member-badge');

  // Dynamic motivational title
  if (streak >= 30) { heroTitle.textContent = 'Unstoppable Machine! 🔥'; heroSub.textContent = `${streak} day streak — you're legendary`; }
  else if (streak >= 7) { heroTitle.textContent = 'On Fire! Keep Going! 💪'; heroSub.textContent = `${streak} day streak — consistency is key`; }
  else if (streak >= 3) { heroTitle.textContent = 'Building Momentum! 🚀'; heroSub.textContent = `${streak} day streak — keep pushing`; }
  else if (data.total_workouts > 0) { heroTitle.textContent = 'Your Fitness Journey 📈'; heroSub.textContent = `${data.total_workouts} workouts logged — every rep counts`; }
  else { heroTitle.textContent = 'Start Your Journey! 🌟'; heroSub.textContent = 'Log your first workout to begin tracking'; }

  const days = data.member_since_days || 0;
  memberBadge.textContent = days > 365 ? `${Math.floor(days/365)}y ${days%365}d` : days > 0 ? `Day ${days}` : 'New';

  // Populate stat pills
  document.getElementById('ps-workouts').textContent = data.total_workouts || 0;
  document.getElementById('ps-streak').textContent = (data.current_streak || 0) + '🔥';
  document.getElementById('ps-active').textContent = data.active_days || 0;
  document.getElementById('ps-best-streak').textContent = (data.longest_streak || 0) + '⚡';
  document.getElementById('ps-prs').textContent = data.total_prs || 0;
  document.getElementById('ps-volume').textContent = formatVolume(data.total_volume_kg || 0);
  document.getElementById('ps-avg-dur').textContent = data.avg_workout_duration_min > 0 ? Math.round(data.avg_workout_duration_min) + 'm' : '—';
  document.getElementById('ps-achievements').textContent = `${data.achievements_unlocked || 0}/14`;
}

function formatVolume(kg) {
  if (kg >= 1000000) return (kg / 1000000).toFixed(1) + 'M';
  if (kg >= 1000) return (kg / 1000).toFixed(1) + 'k';
  return Math.round(kg).toString();
}


// ── Chart.js defaults ──
function chartDefaults() {
  return {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: { color: '#8a8a8a', font: { family: 'Inter', size: 11 } },
      },
      tooltip: {
        backgroundColor: '#1e1e1e',
        titleColor: '#e8e8e8',
        bodyColor: '#8a8a8a',
        borderColor: '#2a2a2a',
        borderWidth: 1,
        cornerRadius: 8,
        padding: 10,
      },
    },
    scales: {
      x: {
        ticks: { color: '#555', font: { family: 'Inter', size: 10 } },
        grid: { color: 'rgba(42,42,42,0.5)' },
      },
      y: {
        ticks: { color: '#555', font: { family: 'Inter', size: 10 } },
        grid: { color: 'rgba(42,42,42,0.5)' },
      },
    },
  };
}

// ── Weight Tracker ──
function renderWeightTracker(data) {
  const unit = weightLabel();
  const cur = data.current_weight ? displayWeight(data.current_weight) : null;
  const start = data.start_weight ? displayWeight(data.start_weight) : null;
  const target = data.target_weight ? displayWeight(data.target_weight) : null;
  const change = data.total_change != null ? displayWeight(Math.abs(data.total_change)) : null;
  const changeDir = data.total_change > 0 ? '+' : data.total_change < 0 ? '-' : '';
  const changeColor = data.total_change > 0 ? (state.user?.goal === 'gain_muscle' ? 'var(--green)' : 'var(--red)') :
                       data.total_change < 0 ? (state.user?.goal === 'lose_weight' ? 'var(--green)' : 'var(--red)') : 'var(--text-muted)';

  document.getElementById('ws-current').textContent = cur != null ? `${cur} ${unit}` : '—';
  document.getElementById('ws-start').textContent = start != null ? `${start} ${unit}` : '—';
  document.getElementById('ws-target').textContent = target != null ? `${target} ${unit}` : 'Not set';
  const wsChange = document.getElementById('ws-change');
  wsChange.textContent = change != null ? `${changeDir}${change} ${unit}` : '—';
  wsChange.style.color = changeColor;
  document.getElementById('weight-log-unit').textContent = unit;

  // Chart
  if (data.entries.length > 0) {
    renderWeightChart(data.entries, data.target_weight);
  }
}

function renderWeightChart(entries, targetWeight) {
  const ctx = document.getElementById('weight-chart');
  if (weightChart) weightChart.destroy();

  const labels = entries.map(e => {
    const d = new Date(e.date);
    return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });
  const weights = entries.map(e => displayWeight(e.weight_kg));

  const datasets = [{
    label: 'Weight',
    data: weights,
    borderColor: '#c9a84c',
    backgroundColor: 'rgba(201,168,76,0.1)',
    fill: true,
    tension: 0.4,
    pointRadius: 3,
    pointHoverRadius: 6,
    pointBackgroundColor: '#c9a84c',
    borderWidth: 2.5,
  }];

  if (targetWeight) {
    datasets.push({
      label: 'Target',
      data: Array(entries.length).fill(displayWeight(targetWeight)),
      borderColor: 'rgba(74,158,110,0.6)',
      borderDash: [6, 4],
      pointRadius: 0,
      borderWidth: 1.5,
      fill: false,
    });
  }

  weightChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...chartDefaults(),
      plugins: {
        ...chartDefaults().plugins,
        tooltip: {
          ...chartDefaults().plugins.tooltip,
          callbacks: {
            label: (c) => `${c.dataset.label}: ${c.parsed.y} ${weightLabel()}`,
          },
        },
      },
    },
  });
}


// ── Calorie Trend Chart ──
function renderCalorieTrendChart(data) {
  const ctx = document.getElementById('calorie-trend-chart');
  if (calorieTrendChart) calorieTrendChart.destroy();

  const labels = data.map(d => {
    const date = new Date(d.date);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  calorieTrendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [
        {
          label: 'Calories',
          data: data.map(d => Math.round(d.calories)),
          borderColor: '#c9a84c',
          backgroundColor: 'rgba(201,168,76,0.1)',
          fill: true,
          tension: 0.3,
          pointRadius: 2,
          pointHoverRadius: 5,
          borderWidth: 2,
        },
        {
          label: 'Target',
          data: data.map(d => Math.round(d.target)),
          borderColor: 'rgba(196,92,92,0.6)',
          borderDash: [5, 5],
          pointRadius: 0,
          borderWidth: 1.5,
          fill: false,
        },
      ],
    },
    options: chartDefaults(),
  });
}

// ── Workout Frequency Chart ──
function renderWorkoutFreqChart(data) {
  const ctx = document.getElementById('workout-freq-chart');
  if (workoutFreqChart) workoutFreqChart.destroy();

  workoutFreqChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.map(d => d.week_label),
      datasets: [{
        label: 'Workouts',
        data: data.map(d => d.count),
        backgroundColor: data.map(d => d.count >= 4 ? 'rgba(74,158,110,0.7)' : d.count >= 2 ? 'rgba(201,168,76,0.7)' : 'rgba(91,142,201,0.4)'),
        borderRadius: 6,
        borderSkipped: false,
      }],
    },
    options: {
      ...chartDefaults(),
      plugins: {
        ...chartDefaults().plugins,
        legend: { display: false },
      },
      scales: {
        ...chartDefaults().scales,
        y: { ...chartDefaults().scales.y, beginAtZero: true, ticks: { ...chartDefaults().scales.y.ticks, stepSize: 1 } },
      },
    },
  });
}

// ── Strength Trend Chart ──
function renderStrengthChart(data) {
  const ctx = document.getElementById('strength-trend-chart');
  const noData = document.getElementById('strength-no-data');

  if (strengthChart) strengthChart.destroy();

  if (!data.length) {
    ctx.style.display = 'none';
    noData.style.display = 'block';
    return;
  }
  ctx.style.display = 'block';
  noData.style.display = 'none';

  const colors = ['#c9a84c', '#4a9e6e', '#5b8ec9', '#c45c5c', '#8b6ec9'];

  const allDates = [...new Set(data.flatMap(d => d.data_points.map(p => p.date)))].sort();
  const labels = allDates.map(d => {
    const date = new Date(d);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  });

  const datasets = data.map((exercise, i) => {
    const dateMap = {};
    exercise.data_points.forEach(p => { dateMap[p.date] = p.estimated_1rm; });
    return {
      label: exercise.exercise_name,
      data: allDates.map(d => dateMap[d] || null),
      borderColor: colors[i % colors.length],
      backgroundColor: colors[i % colors.length] + '20',
      tension: 0.3,
      pointRadius: 3,
      pointHoverRadius: 6,
      borderWidth: 2,
      spanGaps: true,
    };
  });

  strengthChart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      ...chartDefaults(),
      plugins: {
        ...chartDefaults().plugins,
        tooltip: {
          ...chartDefaults().plugins.tooltip,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${displayWeight(ctx.parsed.y)} ${weightLabel()} (Est. 1RM)`,
          },
        },
      },
    },
  });
}

// ── Personal Records ──
function renderPRs(prs) {
  const container = document.getElementById('pr-list');
  const badge = document.getElementById('pr-count-badge');

  if (!prs.length) {
    badge.textContent = '0';
    container.innerHTML = `
      <div class="empty-state" style="grid-column:1/-1">
        <div class="empty-icon">🏅</div>
        <h3>No PRs yet</h3>
        <p>Start lifting and your personal records will appear here!</p>
      </div>`;
    return;
  }

  const weightPRs = prs.filter(p => p.record_type === 'max_weight');
  const e1rmPRs = prs.filter(p => p.record_type === 'estimated_1rm');
  const allPRs = [...weightPRs.map(p => ({...p, display_type: 'Max Weight'})), ...e1rmPRs.map(p => ({...p, display_type: 'Est. 1RM'}))];

  badge.textContent = allPRs.length;

  container.innerHTML = allPRs.map(pr => {
    const prVal = pr.unit === 'kg' ? displayWeight(pr.value) : pr.value;
    const prUnit = pr.unit === 'kg' ? weightLabel() : pr.unit;
    const improvement = pr.previous_value ? ((prVal - (pr.unit === 'kg' ? displayWeight(pr.previous_value) : pr.previous_value)).toFixed(1)) : null;
    const improvStr = improvement && parseFloat(improvement) > 0 ? `<div class="pr-improvement">↑ ${improvement} ${prUnit}</div>` : '';
    return `
      <div class="pr-card">
        <div class="pr-type">${pr.display_type}</div>
        <div class="pr-exercise">${pr.exercise_name}</div>
        <div class="pr-value">${prVal}<span class="pr-unit">${prUnit}</span></div>
        ${improvStr}
        <div class="pr-date">${new Date(pr.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</div>
      </div>`;
  }).join('');
}

// ── Achievements ──
function renderAchievements(achievements) {
  allAchievements = achievements;
  const grid = document.getElementById('achievement-grid');
  const unlocked = achievements.filter(a => a.unlocked).length;
  document.getElementById('achievement-count-badge').textContent = `${unlocked} / ${achievements.length}`;

  renderAchievementGrid(achievements);

  // Wire filter buttons
  document.querySelectorAll('.ach-filter').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.ach-filter').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      const filtered = cat === 'all' ? allAchievements : allAchievements.filter(a => a.category === cat);
      renderAchievementGrid(filtered);
    });
  });
}

function renderAchievementGrid(achievements) {
  const grid = document.getElementById('achievement-grid');
  grid.innerHTML = achievements.map(a => {
    const cls = a.unlocked ? 'unlocked' : 'locked';
    const pct = a.progress != null ? Math.round(a.progress * 100) : 0;
    const progressBar = a.progress !== null && !a.unlocked
      ? `<div class="achievement-progress"><div class="achievement-progress-fill" style="width:${pct}%"></div></div>
         <div class="achievement-progress-text">${a.progress_text || ''}</div>`
      : '';
    const unlockedAt = a.unlocked && a.unlocked_at
      ? `<div class="achievement-unlocked-at">✓ Unlocked</div>`
      : '';
    return `
      <div class="achievement-card ${cls}">
        <span class="achievement-icon">${a.icon}</span>
        <div class="achievement-name">${a.name}</div>
        <div class="achievement-desc">${a.description}</div>
        ${progressBar}
        ${unlockedAt}
      </div>`;
  }).join('');
}

// ── PR Toast ──
function prToast(msg) {
  const c = document.getElementById('toast-container');
  const el = document.createElement('div');
  el.className = 'toast pr-toast';
  el.innerHTML = msg;
  c.appendChild(el);
  setTimeout(() => { el.style.opacity = '0'; setTimeout(() => el.remove(), 400); }, 5000);
}


// ═══════════════════════════════════════════════════════════════
//  WORKOUT STREAK HEATMAP
// ═══════════════════════════════════════════════════════════════
let heatmapYear = new Date().getFullYear();

async function loadHeatmap(year) {
  if (year !== undefined) heatmapYear = year;
  document.getElementById('heatmap-year-label').textContent = heatmapYear;

  const nextBtn = document.getElementById('heatmap-next-year');
  nextBtn.disabled = heatmapYear >= new Date().getFullYear();
  nextBtn.style.opacity = nextBtn.disabled ? '0.3' : '1';

  try {
    const data = await get(`/progress/heatmap?year=${heatmapYear}`);
    renderHeatmap(data);
  } catch (e) {
    console.error('Heatmap error:', e);
  }
}

function renderHeatmap(data) {
  const grid = document.getElementById('heatmap-grid');
  const monthsEl = document.getElementById('heatmap-months');
  const statsEl = document.getElementById('heatmap-stats');
  const { days, stats } = data;

  statsEl.innerHTML = `
    <div class="heatmap-stat">
      <span class="heatmap-stat-value">${stats.total_workouts}</span>
      <span class="heatmap-stat-label">Workouts</span>
    </div>
    <div class="heatmap-stat">
      <span class="heatmap-stat-value">${stats.active_days}</span>
      <span class="heatmap-stat-label">Active Days</span>
    </div>
    <div class="heatmap-stat">
      <span class="heatmap-stat-value">${stats.current_streak}🔥</span>
      <span class="heatmap-stat-label">Current Streak</span>
    </div>
    <div class="heatmap-stat">
      <span class="heatmap-stat-value">${stats.longest_streak}⚡</span>
      <span class="heatmap-stat-label">Best Streak</span>
    </div>`;

  const dayMap = {};
  let maxCount = 1;
  days.forEach(d => {
    dayMap[d.date] = d.count;
    if (d.count > maxCount) maxCount = d.count;
  });

  const jan1 = new Date(data.year, 0, 1);
  const startDow = jan1.getDay();
  let cells = [];
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const monthPositions = [];
  let lastMonth = -1;

  for (let week = 0; week < 53; week++) {
    for (let dow = 0; dow < 7; dow++) {
      const dayIndex = week * 7 + dow - startDow;
      const date = new Date(data.year, 0, 1 + dayIndex);

      if (date.getFullYear() !== data.year || date > today) {
        cells.push({ empty: true });
        continue;
      }

      const key = date.toISOString().slice(0, 10);
      const count = dayMap[key] || 0;
      let level = 0;
      if (count > 0) {
        if (maxCount <= 1) level = 2;
        else if (count === 1) level = 1;
        else if (count === 2) level = 2;
        else if (count === 3) level = 3;
        else level = 4;
      }

      const month = date.getMonth();
      if (month !== lastMonth) {
        monthPositions.push({ month, week });
        lastMonth = month;
      }

      const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      const tooltip = `${dayNames[dow]}, ${monthNames[month]} ${date.getDate()}: ${count} workout${count !== 1 ? 's' : ''}`;
      cells.push({ level, tooltip, empty: false });
    }
  }

  grid.style.gridTemplateRows = 'repeat(7, 1fr)';
  grid.style.gridTemplateColumns = 'repeat(53, 1fr)';
  grid.innerHTML = cells.map(c => {
    if (c.empty) return '<span class="heatmap-cell heatmap-cell-empty"></span>';
    return `<span class="heatmap-cell" data-level="${c.level}" title="${c.tooltip}"></span>`;
  }).join('');

  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  monthsEl.innerHTML = monthPositions.map(mp => {
    const leftPct = (mp.week / 53) * 100;
    return `<span style="position:absolute;left:${leftPct}%">${monthNames[mp.month]}</span>`;
  }).join('');
}

// ── Weight Log Form Handlers ──
document.addEventListener('DOMContentLoaded', () => {
  // Heatmap year nav
  const prevBtn = document.getElementById('heatmap-prev-year');
  const nextBtn = document.getElementById('heatmap-next-year');
  if (prevBtn) prevBtn.addEventListener('click', () => loadHeatmap(heatmapYear - 1));
  if (nextBtn) nextBtn.addEventListener('click', () => loadHeatmap(heatmapYear + 1));

  // Weight log toggle
  const logWeightBtn = document.getElementById('log-weight-btn');
  const weightForm = document.getElementById('weight-log-form');
  if (logWeightBtn) {
    logWeightBtn.addEventListener('click', () => {
      weightForm.style.display = weightForm.style.display === 'none' ? 'block' : 'none';
      if (weightForm.style.display === 'block') document.getElementById('weight-log-input').focus();
    });
  }

  // Cancel weight log
  const cancelBtn = document.getElementById('weight-log-cancel');
  if (cancelBtn) cancelBtn.addEventListener('click', () => { weightForm.style.display = 'none'; });

  // Save weight log
  const saveBtn = document.getElementById('weight-log-save');
  if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
      const rawVal = parseFloat(document.getElementById('weight-log-input').value);
      if (!rawVal || rawVal < 20) { toast('Enter a valid weight', 'error'); return; }
      const kgVal = inputToKg(rawVal);
      const note = document.getElementById('weight-log-note').value.trim();
      try {
        await post(`/progress/weight-log?weight_kg=${kgVal}&note=${encodeURIComponent(note)}`, {});
        toast('Weight logged! ⚖️', 'success');
        weightForm.style.display = 'none';
        document.getElementById('weight-log-input').value = '';
        document.getElementById('weight-log-note').value = '';
        // Refresh weight data
        const freshData = await get('/progress/weight-log?days=90');
        renderWeightTracker(freshData);
        // Also refresh overview
        const freshOverview = await get('/progress/overview');
        renderProgressOverview(freshOverview);
      } catch (err) {
        toast(err.message, 'error');
      }
    });
  }
});


// ═══════════════════════════════════════════════════════════════
//  PWA — Service Worker Registration
// ═══════════════════════════════════════════════════════════════
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js')
      .then(reg => {
        console.log('✅ GYMBRO SW registered:', reg.scope);
        reg.update();
      })
      .catch(err => console.log('SW registration failed:', err));
  });
}

// PWA Install prompt
let deferredInstallPrompt = null;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredInstallPrompt = e;
  // Show custom install banner
  if (!localStorage.getItem('pwa-install-dismissed')) {
    showPWAInstallBanner();
  }
});

function showPWAInstallBanner() {
  // Don't show if already installed
  if (window.matchMedia('(display-mode: standalone)').matches) return;
  if (document.getElementById('pwa-install-banner')) return;

  const banner = document.createElement('div');
  banner.id = 'pwa-install-banner';
  banner.className = 'pwa-install-banner';
  banner.innerHTML = `
    <span class="pwa-icon">🏋️</span>
    <div class="pwa-text">
      <h4>Install GYMBRO</h4>
      <p>Add to home screen for a native app experience</p>
    </div>
    <button class="pwa-btn" id="pwa-install-btn">Install</button>
    <button class="pwa-dismiss" id="pwa-dismiss-btn">&times;</button>`;
  document.body.appendChild(banner);

  document.getElementById('pwa-install-btn').addEventListener('click', async () => {
    if (deferredInstallPrompt) {
      deferredInstallPrompt.prompt();
      const result = await deferredInstallPrompt.userChoice;
      if (result.outcome === 'accepted') {
        showToast('✅ GYMBRO installed! Find it on your home screen.', 'success');
      }
      deferredInstallPrompt = null;
    }
    banner.remove();
  });

  document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
    banner.remove();
    localStorage.setItem('pwa-install-dismissed', 'true');
  });
}


// ═══════════════════════════════════════════════════════════════
//  PROFILE
// ═══════════════════════════════════════════════════════════════
function loadProfile() {
  const u = state.user;
  if (!u) return;
  const initial = (u.username || u.email || '?')[0].toUpperCase();
  document.getElementById('profile-avatar').textContent = initial;
  document.getElementById('profile-name').textContent = u.username || 'User';
  document.getElementById('profile-email').textContent = u.email || '';

  document.getElementById('profile-username').value = u.username || '';
  document.getElementById('profile-email-input').value = u.email || '';
  document.getElementById('profile-age').value = u.age || '';
  document.getElementById('profile-gender').value = u.gender || 'male';
  document.getElementById('profile-height').value = u.height_cm || '';
  document.getElementById('profile-weight').value = u.weight_kg || '';
  document.getElementById('profile-activity').value = u.activity_level || 'moderately_active';
  document.getElementById('profile-goal').value = u.goal || 'maintain';
  document.getElementById('profile-target-weight').value = u.target_weight_kg || '';

  // Unit toggle
  const unit = u.weight_unit || 'kg';
  document.querySelectorAll('#unit-toggle .unit-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.unit === unit);
  });
  document.getElementById('target-weight-label').textContent = `Target Weight (${unit})`;

  // Init unit toggle buttons
  document.querySelectorAll('#unit-toggle .unit-btn').forEach(btn => {
    btn.onclick = () => {
      document.querySelectorAll('#unit-toggle .unit-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('target-weight-label').textContent = `Target Weight (${btn.dataset.unit})`;
    };
  });
}

document.getElementById('profile-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  try {
    const selectedUnit = document.querySelector('#unit-toggle .unit-btn.active')?.dataset.unit || 'kg';

    const body = {
      username: document.getElementById('profile-username').value,
      age: parseInt(document.getElementById('profile-age').value) || undefined,
      gender: document.getElementById('profile-gender').value,
      height_cm: parseFloat(document.getElementById('profile-height').value) || undefined,
      weight_kg: parseFloat(document.getElementById('profile-weight').value) || undefined,
      activity_level: document.getElementById('profile-activity').value,
      goal: document.getElementById('profile-goal').value,
      target_weight_kg: parseFloat(document.getElementById('profile-target-weight').value) || undefined,
      weight_unit: selectedUnit,
    };

    // Remove undefined keys
    Object.keys(body).forEach(k => body[k] === undefined && delete body[k]);

    state.user = await put('/auth/me', body);
    updateSidebar();
    toast('Profile updated! ✓', 'success');
  } catch (err) {
    toast(err.message, 'error');
  }
});

// ═══════════════════════════════════════════════════════════════
//  HELPERS
// ═══════════════════════════════════════════════════════════════

// ── Unit Preference Helpers ──
function getWeightUnit() {
  return state.user?.weight_unit || 'kg';
}

function displayWeight(kgValue) {
  const unit = getWeightUnit();
  if (unit === 'lbs') return +(kgValue * 2.20462).toFixed(1);
  return +parseFloat(kgValue).toFixed(1);
}

function inputToKg(displayValue) {
  const unit = getWeightUnit();
  if (unit === 'lbs') return +(displayValue / 2.20462).toFixed(2);
  return +parseFloat(displayValue).toFixed(2);
}

function weightLabel() {
  return getWeightUnit() === 'lbs' ? 'lbs' : 'kg';
}

function formatNum(n) {
  if (n >= 1000) return (n / 1000).toFixed(1) + 'k';
  return Math.round(n).toString();
}

function truncate(s, max) {
  return s.length > max ? s.slice(0, max) + '…' : s;
}

function capitalize(s) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// ═══════════════════════════════════════════════════════════════
//  INIT
// ═══════════════════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', async () => {
  initAuth();
  initNav();
  initWorkoutModal();
  initChat();

  // Auto-login if token exists
  if (state.token) {
    document.getElementById('auth-page').innerHTML = `
      <div style="display:flex;flex-direction:column;align-items:center;gap:1rem">
        <div class="spinner spinner-lg"></div>
        <p>Loading GYMBRO...</p>
      </div>`;
    await enterApp();
  }
});

// ═══════════════════════════════════════════════════════════════
//  AI SMART COACH
// ═══════════════════════════════════════════════════════════════

async function requestSmartAnalysis() {
  const resultEl = document.getElementById('ai-analysis-result');
  const workoutEl = document.getElementById('ai-workout-result');
  const loadingEl = document.getElementById('ai-loading');
  const btn = document.getElementById('btn-smart-analysis');

  // Hide previous results
  if (resultEl) resultEl.style.display = 'none';
  if (workoutEl) workoutEl.style.display = 'none';
  if (loadingEl) {
    loadingEl.style.display = 'flex';
    loadingEl.querySelector('.ai-loading-text').textContent = 'Analyzing your fitness data...';
  }
  if (btn) btn.disabled = true;

  try {
    const data = await api('/coaching/smart-analysis', {
      method: 'POST',
    });
    if (loadingEl) loadingEl.style.display = 'none';
    renderSmartAnalysis(data);
  } catch (e) {
    console.error('Smart analysis failed:', e);
    if (loadingEl) loadingEl.style.display = 'none';
    if (resultEl) {
      resultEl.style.display = 'block';
      resultEl.innerHTML = '<div class="ai-error">❌ Analysis failed. Please try again.</div>';
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderSmartAnalysis(data) {
  const resultEl = document.getElementById('ai-analysis-result');
  if (!resultEl) return;
  resultEl.style.display = 'block';

  // ── Score Ring Animation ──
  const score = data.performance_score || 0;
  const grade = data.grade || '—';
  const circumference = 2 * Math.PI * 52; // r=52
  const offset = circumference - (score / 100) * circumference;

  const ring = document.getElementById('ai-ring-fill');
  if (ring) {
    // Color based on score
    let color = '#ef4444'; // red
    if (score >= 80) color = '#22c55e';
    else if (score >= 60) color = '#c9a84c';
    else if (score >= 40) color = '#f59e0b';

    ring.style.stroke = color;
    ring.style.transition = 'stroke-dashoffset 1.5s ease-out';
    setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);
  }

  // Animate score number
  const scoreEl = document.getElementById('ai-score-num');
  if (scoreEl) animateNumber(scoreEl, 0, score, 1500);

  const gradeEl = document.getElementById('ai-score-grade');
  if (gradeEl) {
    gradeEl.textContent = grade;
    gradeEl.className = 'ai-score-grade grade-' + grade.toLowerCase();
  }

  // Headline
  const headlineEl = document.getElementById('ai-headline');
  const headlineSubEl = document.getElementById('ai-headline-sub');
  if (headlineEl) headlineEl.textContent = data.headline || '';
  if (headlineSubEl) headlineSubEl.textContent = data.headline_sub || '';

  // AI Summary
  const summaryBox = document.getElementById('ai-summary-box');
  const summaryText = document.getElementById('ai-summary-text');
  if (data.ai_enhanced && data.ai_summary) {
    if (summaryBox) summaryBox.style.display = 'block';
    if (summaryText) summaryText.textContent = data.ai_summary;
  } else {
    if (summaryBox) summaryBox.style.display = 'none';
  }

  // Score Breakdown bars
  const breakdownEl = document.getElementById('ai-breakdown');
  if (breakdownEl && data.score_breakdown) {
    const labels = {
      consistency: '🏃 Consistency',
      nutrition: '🍽️ Nutrition',
      balance: '⚖️ Balance',
      progression: '📈 Progression',
      weight_progress: '⚖️ Weight',
      hydration: '💧 Hydration',
    };
    let html = '';
    for (const [key, val] of Object.entries(data.score_breakdown)) {
      const label = labels[key] || key;
      let barColor = '#ef4444';
      if (val >= 80) barColor = '#22c55e';
      else if (val >= 60) barColor = '#c9a84c';
      else if (val >= 40) barColor = '#f59e0b';

      html += `<div class="ai-bar-row">
        <span class="ai-bar-label">${label}</span>
        <div class="ai-bar-track">
          <div class="ai-bar-fill" style="width:0%;background:${barColor}" data-width="${val}%"></div>
        </div>
        <span class="ai-bar-val">${val}</span>
      </div>`;
    }
    breakdownEl.innerHTML = html;
    // Animate bars
    setTimeout(() => {
      breakdownEl.querySelectorAll('.ai-bar-fill').forEach(bar => {
        bar.style.width = bar.dataset.width;
      });
    }, 200);
  }

  // Wins
  renderAiList('ai-wins-section', 'ai-wins-list', data.wins, 'ai-win-item');
  // Insights
  renderAiList('ai-insights-section', 'ai-insights-list', data.insights, 'ai-insight-item');
  // Warnings
  renderAiList('ai-warnings-section', 'ai-warnings-list', data.warnings, 'ai-warning-item');

  // Muscle Distribution
  const muscleSection = document.getElementById('ai-muscle-section');
  const muscleBars = document.getElementById('ai-muscle-bars');
  if (muscleSection && muscleBars && data.muscle_distribution) {
    const muscles = data.muscle_distribution;
    const entries = Object.entries(muscles).filter(([k]) => k !== 'other');
    if (entries.length > 0) {
      muscleSection.style.display = 'block';
      const maxVal = Math.max(...entries.map(([, v]) => v));
      muscleBars.innerHTML = entries
        .sort((a, b) => b[1] - a[1])
        .map(([muscle, sets]) => {
          const pct = maxVal > 0 ? (sets / maxVal) * 100 : 0;
          return `<div class="ai-muscle-row">
            <span class="ai-muscle-name">${muscle}</span>
            <div class="ai-muscle-track">
              <div class="ai-muscle-fill" style="width:0%" data-width="${pct}%"></div>
            </div>
            <span class="ai-muscle-val">${sets} sets</span>
          </div>`;
        }).join('');
      setTimeout(() => {
        muscleBars.querySelectorAll('.ai-muscle-fill').forEach(bar => {
          bar.style.width = bar.dataset.width;
        });
      }, 400);
    } else {
      muscleSection.style.display = 'none';
    }
  }
}

function renderAiList(sectionId, listId, items, itemClass) {
  const section = document.getElementById(sectionId);
  const list = document.getElementById(listId);
  if (!section || !list) return;
  if (items && items.length > 0) {
    section.style.display = 'block';
    list.innerHTML = items.map(item =>
      `<div class="${itemClass}">${item}</div>`
    ).join('');
  } else {
    section.style.display = 'none';
  }
}

function animateNumber(el, from, to, duration) {
  const start = performance.now();
  function step(timestamp) {
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3); // ease-out cubic
    el.textContent = Math.round(from + (to - from) * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ── AI Workout Generator ──
async function requestGenerateWorkout() {
  const resultEl = document.getElementById('ai-workout-result');
  const analysisEl = document.getElementById('ai-analysis-result');
  const loadingEl = document.getElementById('ai-loading');
  const btn = document.getElementById('btn-gen-workout');

  if (analysisEl) analysisEl.style.display = 'none';
  if (resultEl) resultEl.style.display = 'none';
  if (loadingEl) {
    loadingEl.style.display = 'flex';
    loadingEl.querySelector('.ai-loading-text').textContent = 'Generating your personalized workout...';
  }
  if (btn) btn.disabled = true;

  try {
    const data = await api('/coaching/generate-workout');
    if (loadingEl) loadingEl.style.display = 'none';
    renderGeneratedWorkout(data);
  } catch (e) {
    console.error('Workout generation failed:', e);
    if (loadingEl) loadingEl.style.display = 'none';
    if (resultEl) {
      resultEl.style.display = 'block';
      resultEl.innerHTML = '<div class="ai-error">❌ Workout generation failed. Please try again.</div>';
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

function renderGeneratedWorkout(data) {
  const el = document.getElementById('ai-workout-result');
  if (!el) return;
  el.style.display = 'block';

  let html = `
    <div class="ai-workout-header">
      <div class="ai-workout-badge">${data.source === 'ai' ? '🤖 AI Generated' : '⚡ Algorithm Generated'}</div>
      <h3 class="ai-workout-name">${data.split_name || data.workout_name || 'Your Workout Plan'}</h3>
      <p class="ai-workout-desc">${data.split_description || ''}</p>
      <div class="ai-workout-meta">
        ${data.frequency ? `<span class="ai-meta-pill">📅 ${data.frequency}</span>` : ''}
        ${data.experience_level ? `<span class="ai-meta-pill">🎯 ${data.experience_level}</span>` : ''}
        ${data.goal_optimization ? `<span class="ai-meta-pill">🏆 ${data.goal_optimization}</span>` : ''}
      </div>
    </div>
  `;

  // Schedule (weekly plan)
  if (data.schedule) {
    html += '<div class="ai-schedule">';
    for (const day of data.schedule) {
      if (day.type === 'rest') {
        html += `<div class="ai-day-card ai-rest-day">
          <div class="ai-day-name">${day.day}</div>
          <div class="ai-day-type">😴 ${day.name}</div>
          <p class="ai-day-notes">${day.notes || ''}</p>
        </div>`;
      } else {
        html += `<div class="ai-day-card">
          <div class="ai-day-name">${day.day}</div>
          <div class="ai-day-type">🏋️ ${day.name}</div>
          <div class="ai-exercises-list">
            ${day.exercises.map((ex, i) => `
              <div class="ai-exercise-row">
                <span class="ai-ex-num">${i + 1}</span>
                <div class="ai-ex-info">
                  <span class="ai-ex-name">${ex.name}</span>
                  <span class="ai-ex-detail">${ex.sets} × ${ex.reps} · ${ex.rest} rest</span>
                  ${ex.tip ? `<span class="ai-ex-tip">💡 ${ex.tip}</span>` : ''}
                </div>
                <span class="ai-ex-muscle">${ex.muscle}</span>
              </div>
            `).join('')}
          </div>
          ${day.notes ? `<p class="ai-day-notes">${day.notes}</p>` : ''}
        </div>`;
      }
    }
    html += '</div>';
  }

  // Single workout (AI generated)
  if (data.exercises && !data.schedule) {
    html += `<div class="ai-schedule"><div class="ai-day-card">
      <div class="ai-day-type">🏋️ Today's Workout</div>
      ${data.warmup ? `<p class="ai-day-notes">🔥 Warmup: ${data.warmup}</p>` : ''}
      <div class="ai-exercises-list">
        ${data.exercises.map((ex, i) => `
          <div class="ai-exercise-row">
            <span class="ai-ex-num">${i + 1}</span>
            <div class="ai-ex-info">
              <span class="ai-ex-name">${ex.name}</span>
              <span class="ai-ex-detail">${ex.sets} × ${ex.reps} · ${ex.rest} rest</span>
              ${ex.tip ? `<span class="ai-ex-tip">💡 ${ex.tip}</span>` : ''}
            </div>
            <span class="ai-ex-muscle">${ex.muscle}</span>
          </div>
        `).join('')}
      </div>
      ${data.cooldown ? `<p class="ai-day-notes">🧊 Cooldown: ${data.cooldown}</p>` : ''}
    </div></div>`;
  }

  // Coaching Notes
  if (data.coaching_notes && data.coaching_notes.length) {
    html += `<div class="ai-coaching-notes">
      <h4>📋 Coaching Notes</h4>
      ${data.coaching_notes.map(n => `<div class="ai-note-item">${n}</div>`).join('')}
    </div>`;
  }

  // Weak muscles warning
  if (data.weak_muscles && data.weak_muscles.length) {
    html += `<div class="ai-weak-alert">
      <span>🎯 Priority muscles to strengthen: <strong>${data.weak_muscles.join(', ')}</strong></span>
    </div>`;
  }

  el.innerHTML = html;
}

// ═══════════════════════════════════════════════════════════════
//  CHATBOT
// ═══════════════════════════════════════════════════════════════

function initChat() {
  // Hide chat FAB until logged in
  const fab = document.getElementById('chat-fab');
  if (fab) fab.style.display = 'none';
}

function showChatFab() {
  const fab = document.getElementById('chat-fab');
  if (fab) fab.style.display = 'flex';
}

function hideChatFab() {
  const fab = document.getElementById('chat-fab');
  if (fab) fab.style.display = 'none';
  closeChatDrawer();
}

function toggleChat() {
  state.chatOpen = !state.chatOpen;
  const drawer = document.getElementById('chat-drawer');
  const fab = document.getElementById('chat-fab');
  if (state.chatOpen) {
    drawer.classList.add('open');
    fab.classList.add('hidden');
    document.getElementById('chat-input').focus();
    // Load suggestions on first open
    if (state.chatMessages.length === 0) {
      loadChatSuggestions();
    }
  } else {
    closeChatDrawer();
  }
}

function closeChatDrawer() {
  state.chatOpen = false;
  const drawer = document.getElementById('chat-drawer');
  const fab = document.getElementById('chat-fab');
  if (drawer) drawer.classList.remove('open');
  if (fab) fab.classList.remove('hidden');
}

async function loadChatSuggestions() {
  try {
    const data = await api('/chat/suggestions');
    const container = document.getElementById('chat-suggestions');
    if (!container) return;
    container.innerHTML = data.suggestions
      .map(q => `<button class="chat-suggestion-btn" onclick="askSuggestion(this)">${q}</button>`)
      .join('');
  } catch (e) {
    console.error('Failed to load suggestions:', e);
  }
}

function askSuggestion(btn) {
  const question = btn.textContent;
  document.getElementById('chat-input').value = question;
  sendChatMessage();
}

async function sendChatMessage() {
  const input = document.getElementById('chat-input');
  const message = input.value.trim();
  if (!message) return;

  input.value = '';

  // Hide welcome on first message
  const welcome = document.querySelector('.chat-welcome');
  if (welcome) welcome.style.display = 'none';

  // Add user message
  state.chatMessages.push({ role: 'user', content: message });
  renderChatMessages();

  // Show typing indicator
  showTypingIndicator();

  try {
    const data = await api('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });

    hideTypingIndicator();

    // Add bot reply
    state.chatMessages.push({
      role: 'bot',
      content: data.response,
      source: data.source,
      matched_topic: data.matched_topic,
    });
    renderChatMessages();
  } catch (e) {
    hideTypingIndicator();
    state.chatMessages.push({
      role: 'bot',
      content: "Sorry, I couldn't process that. Please try again!",
      source: 'error',
    });
    renderChatMessages();
  }
}

function renderChatMessages() {
  const container = document.getElementById('chat-messages');
  if (!container) return;

  // Keep welcome if no messages
  let html = '';
  if (state.chatMessages.length === 0) return;

  html = state.chatMessages.map(msg => {
    if (msg.role === 'user') {
      return `<div class="chat-msg chat-msg-user">
        <div class="chat-bubble chat-bubble-user">${escapeHtml(msg.content)}</div>
      </div>`;
    } else {
      const topicBadge = msg.matched_topic
        ? `<div class="chat-topic-badge">📌 ${escapeHtml(msg.matched_topic)}</div>`
        : '';
      return `<div class="chat-msg chat-msg-bot">
        <div class="chat-avatar">🤖</div>
        <div class="chat-bubble chat-bubble-bot">
          ${topicBadge}
          <div class="chat-bot-text">${formatBotMessage(msg.content)}</div>
        </div>
      </div>`;
    }
  }).join('');

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

function formatBotMessage(text) {
  // Convert markdown-like formatting to HTML
  let html = escapeHtml(text);
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Line breaks
  html = html.replace(/\n/g, '<br>');
  // Bullet points
  html = html.replace(/• /g, '<span class="chat-bullet">•</span> ');
  return html;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function showTypingIndicator() {
  const container = document.getElementById('chat-messages');
  const indicator = document.createElement('div');
  indicator.className = 'chat-msg chat-msg-bot chat-typing-wrapper';
  indicator.id = 'chat-typing';
  indicator.innerHTML = `
    <div class="chat-avatar">🤖</div>
    <div class="chat-bubble chat-bubble-bot chat-typing">
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    </div>`;
  container.appendChild(indicator);
  container.scrollTop = container.scrollHeight;
}

function hideTypingIndicator() {
  const el = document.getElementById('chat-typing');
  if (el) el.remove();
}

