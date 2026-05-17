// ════════════════════════════════════════════════════
//  DevFlow AI — Frontend Script (STANDALONE — NO BACKEND NEEDED)
//  Auth works 100% via localStorage mock. All pages fully functional.
// ════════════════════════════════════════════════════

// ─── MOCK BACKEND ──────────────────────────────────
// Stores users & sessions in localStorage.
// Mimics the FastAPI /api/v1/auth/* endpoints exactly.
// ───────────────────────────────────────────────────
const MockBackend = {
  _getUsers() {
    try { return JSON.parse(localStorage.getItem('_df_users') || '[]'); } catch(_) { return []; }
  },
  _saveUsers(u) { localStorage.setItem('_df_users', JSON.stringify(u)); },
  _makeToken(user) {
    // Simple base64 "token" — no server needed
    return btoa(JSON.stringify({ sub: user.id, email: user.email, name: user.name, t: Date.now() }));
  },

  signup({ name, username, email, password }) {
    const users = this._getUsers();
    if (users.find(u => u.email === email)) return { ok: false, detail: 'Email already taken' };
    if (users.find(u => u.username === username)) return { ok: false, detail: 'Username already taken' };
    const user = { id: 'u_' + Math.random().toString(36).slice(2), name, username, email, password, role: 'USER', createdAt: Date.now() };
    users.push(user);
    this._saveUsers(users);
    const token = this._makeToken(user);
    return { ok: true, access_token: token, refresh_token: 'rt_' + Math.random().toString(36).slice(2), token_type: 'bearer', user: { id: user.id, email: user.email, name: user.name, username: user.username } };
  },

  login({ email, password }) {
    const users = this._getUsers();
    const user = users.find(u => u.email === email);
    if (!user) return { ok: false, detail: 'Invalid credentials' };
    if (user.password !== password) return { ok: false, detail: 'Invalid credentials' };
    const token = this._makeToken(user);
    return { ok: true, access_token: token, refresh_token: 'rt_' + Math.random().toString(36).slice(2), token_type: 'bearer', user: { id: user.id, email: user.email, name: user.name, role: user.role } };
  },

  health() { return { status: 'ok', service: 'devflow-ai-mock', version: '1.0.0-standalone' }; }
};

// ─── AUTH STATE ───
let currentUser = null;
let accessToken = localStorage.getItem('devflow_token') || null;

// ─── HELPER: escape HTML ───
function escHtml(s) {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ─── HELPER: show toast notifications ───
function showToast(msg, type) {
  type = type || 'info';
  var toast = document.getElementById('toast-container');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = 'toast-container';
    toast.style.cssText = 'position:fixed;top:24px;right:24px;z-index:9999;display:flex;flex-direction:column;gap:10px;';
    document.body.appendChild(toast);
  }
  var colors = { success:'#22c55e', error:'#ef4444', info:'#0fb6ff', warning:'#f59e0b' };
  var el = document.createElement('div');
  el.style.cssText = 'background:#1a1f2e;border:1px solid ' + (colors[type]||colors.info) + ';color:#fff;padding:12px 20px;border-radius:10px;font-size:14px;box-shadow:0 8px 24px rgba(0,0,0,0.4);max-width:340px;line-height:1.4;transition:opacity 0.4s;';
  el.textContent = msg;
  toast.appendChild(el);
  setTimeout(function() { el.style.opacity='0'; setTimeout(function(){ el.remove(); }, 400); }, 3500);
}

// ─── PAGE ROUTING ───
var NAV_PAGE_MAP = {
  landing:'Home', dashboard:'Dashboard', ai:'AI Assistant',
  workspace:'Workspace', deploy:'Deploy', analytics:'Analytics',
  settings:'Settings', login:null, signup:null
};

function showPage(id) {
  var protectedPages = ['dashboard','ai','workspace','deploy','analytics','settings'];
  if (protectedPages.indexOf(id) !== -1 && !accessToken) {
    showToast('Please sign in to access this page', 'warning');
    id = 'login';
  }
  document.querySelectorAll('.page').forEach(function(p){ p.classList.remove('active'); });
  var page = document.getElementById('page-' + id);
  if (!page) { console.warn('No page found: page-' + id); return; }
  page.classList.add('active');
  window.scrollTo(0, 0);

  document.querySelectorAll('.nav-link').forEach(function(l){ l.classList.remove('active'); });
  var targetLabel = NAV_PAGE_MAP[id];
  if (targetLabel) {
    document.querySelectorAll('.nav-link').forEach(function(l){
      if (l.textContent.trim() === targetLabel) l.classList.add('active');
    });
  }
  updateAuthUI();
}

// ─── UPDATE NAV BASED ON AUTH STATE ───
function updateAuthUI() {
  var navCta    = document.querySelector('.nav-cta');
  var navSignIn = document.querySelector('.btn-ghost');
  if (currentUser) {
    if (navCta)    { navCta.textContent = currentUser.name || 'My Account'; navCta.onclick = function(){ showPage('settings'); }; }
    if (navSignIn) { navSignIn.textContent = 'Logout'; navSignIn.onclick = logoutUser; }
    var dashName = document.getElementById('dash-user-name');
    if (dashName) dashName.textContent = currentUser.name || 'Developer';
  } else {
    if (navCta)    { navCta.textContent = 'Get Started →'; navCta.onclick = function(){ showPage('signup'); }; }
    if (navSignIn) { navSignIn.textContent = 'Sign in'; navSignIn.onclick = function(){ showPage('login'); }; }
  }
}

// ════════════════════════════════════════════════════
//  SIGNUP — uses MockBackend (no server needed)
// ════════════════════════════════════════════════════
async function handleSignup() {
  var name     = (document.getElementById('signup-name')?.value || '').trim();
  var username = (document.getElementById('signup-username')?.value || '').trim();
  var email    = (document.getElementById('signup-email')?.value || '').trim();
  var password =  document.getElementById('signup-password')?.value || '';

  if (!name || !username || !email || !password) {
    showToast('Please fill in all fields', 'error'); return;
  }
  if (password.length < 8) {
    showToast('Password must be at least 8 characters', 'error'); return;
  }
  if (!email.includes('@')) {
    showToast('Please enter a valid email address', 'error'); return;
  }

  var btn = document.getElementById('signup-btn');
  if (btn) { btn.textContent = 'Creating account...'; btn.disabled = true; }

  // Small artificial delay for UX realism
  await new Promise(r => setTimeout(r, 600));

  try {
    var data = MockBackend.signup({ name, username, email, password });
    if (!data.ok) throw new Error(data.detail || 'Signup failed');

    accessToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem('devflow_token', accessToken);
    localStorage.setItem('devflow_user', JSON.stringify(currentUser));

    showToast('Welcome to DevFlow AI, ' + currentUser.name + '! 🚀', 'success');
    setTimeout(function(){ showPage('dashboard'); }, 800);

  } catch(err) {
    showToast(err.message || 'Signup failed', 'error');
    console.error('Signup error:', err);
  } finally {
    if (btn) { btn.textContent = 'Create Account →'; btn.disabled = false; }
  }
}

// ════════════════════════════════════════════════════
//  LOGIN — uses MockBackend (no server needed)
// ════════════════════════════════════════════════════
async function handleLogin() {
  var email    = (document.getElementById('login-email')?.value || '').trim();
  var password =  document.getElementById('login-password')?.value || '';

  if (!email || !password) {
    showToast('Please enter your email and password', 'error'); return;
  }

  var btn = document.getElementById('login-btn');
  if (btn) { btn.textContent = 'Signing in...'; btn.disabled = true; }

  await new Promise(r => setTimeout(r, 500));

  try {
    var data = MockBackend.login({ email, password });
    if (!data.ok) throw new Error(data.detail || 'Invalid email or password');

    accessToken = data.access_token;
    currentUser = data.user;
    localStorage.setItem('devflow_token', accessToken);
    localStorage.setItem('devflow_user', JSON.stringify(currentUser));

    showToast('Welcome back, ' + (currentUser.name || currentUser.email) + '!', 'success');
    setTimeout(function(){ showPage('dashboard'); }, 600);

  } catch(err) {
    showToast(err.message || 'Login failed', 'error');
    console.error('Login error:', err);
  } finally {
    if (btn) { btn.textContent = 'Sign In →'; btn.disabled = false; }
  }
}

// ─── LOGOUT ───
function logoutUser() {
  accessToken = null;
  currentUser = null;
  localStorage.removeItem('devflow_token');
  localStorage.removeItem('devflow_user');
  showToast('Logged out successfully', 'info');
  showPage('landing');
}

// ─── RESTORE SESSION ON LOAD ───
function restoreSession() {
  var savedUser  = localStorage.getItem('devflow_user');
  var savedToken = localStorage.getItem('devflow_token');
  if (savedUser && savedToken) {
    try { currentUser = JSON.parse(savedUser); accessToken = savedToken; } catch(_) {}
  }
}

// ─── BACKEND STATUS (always shows online for standalone) ───
function checkBackendStatus() {
  var indicator = document.getElementById('backend-status');
  if (indicator) {
    indicator.textContent = '🟢 Standalone Mode';
    indicator.style.color = '#22c55e';
  }
}

// ════════════════════════════════════════════════════
//  DASHBOARD AI CHAT (demo)
// ════════════════════════════════════════════════════
var DASH_AI_RESPONSES = [
  "I've analyzed the relevant code sections. Based on the repository structure, I can see several opportunities for optimization. Let me provide detailed insights.",
  "Great question! Looking at the codebase, the architecture follows a clean separation of concerns. Here's what I found in the authentication flow...",
  "IBM BOB analysis complete. I've identified the relevant code sections and can provide a comprehensive explanation of the patterns used.",
  "Scanning the repository now... Found 3 relevant files. The primary logic is in <code style='font-family:var(--mono);font-size:12px;background:rgba(0,176,255,0.1);padding:1px 5px;border-radius:3px'>useAuth.tsx</code>. Want me to explain the full flow?"
];

function sendDashMsg() {
  var input = document.getElementById('dash-ai-input');
  var val = input.value.trim();
  if (!val) return;
  var container = document.getElementById('dash-ai-messages');
  var initial = currentUser ? (currentUser.name || 'U').charAt(0).toUpperCase() : 'U';
  var userMsg = document.createElement('div');
  userMsg.className = 'msg user fade-in';
  userMsg.innerHTML = '<div class="msg-avatar user">' + escHtml(initial) + '</div><div class="msg-bubble">' + escHtml(val) + '</div>';
  container.appendChild(userMsg);
  input.value = '';
  container.scrollTop = container.scrollHeight;
  setTimeout(function() {
    var aiMsg = document.createElement('div');
    aiMsg.className = 'msg fade-in';
    var text = DASH_AI_RESPONSES[Math.floor(Math.random() * DASH_AI_RESPONSES.length)];
    aiMsg.innerHTML = '<div class="msg-avatar ai">B</div><div class="msg-bubble">' + text + '</div>';
    container.appendChild(aiMsg);
    container.scrollTop = container.scrollHeight;
  }, 1000);
}

// ════════════════════════════════════════════════════
//  MAIN AI CHAT (demo)
// ════════════════════════════════════════════════════
var AI_RESPONSES = [
  {
    text: "I've analyzed the relevant code sections in your repository. Here's the secure implementation using httpOnly cookies:",
    code: '<span class="kw">const</span> <span class="fn">useAuth</span> = () => {\n  <span class="cm">// ✓ Secure: httpOnly cookie — immune to XSS</span>\n  <span class="kw">const</span> token = <span class="fn">getCookie</span>(<span class="str">\'auth_token\'</span>)\n  <span class="cm">// ✓ Added CSRF protection token</span>\n  <span class="kw">return</span> { token, <span class="fn">csrf</span>: <span class="fn">generateCSRF</span>() }\n}',
    file: "src/hooks/useAuth.tsx (fixed)"
  },
  {
    text: "Based on IBM BOB's deep analysis, here's a comprehensive architecture overview with suggested improvements:",
    code: '<span class="cm">// Authentication Flow</span>\n<span class="kw">const</span> flow = [\n  <span class="str">\'API Request\'</span>,\n  <span class="str">\'Rate Limit Check\'</span>,\n  <span class="str">\'JWT Validation\'</span>,\n  <span class="str">\'CSRF Verification\'</span>,\n  <span class="str">\'Role Check\'</span>,\n  <span class="str">\'Route Handler\'</span>\n]',
    file: "Architecture map"
  }
];

function addUserMsg(text) {
  var input = document.getElementById('main-ai-input');
  if (input) { input.value = text; sendMainMsg(); }
}

function sendMainMsg() {
  var input = document.getElementById('main-ai-input');
  var val = input.value.trim();
  if (!val) return;
  var messages = document.getElementById('chat-messages');
  var typing   = document.getElementById('typing-indicator');
  var userName = currentUser ? currentUser.name : 'Developer';
  var initial  = userName.charAt(0).toUpperCase();

  var userMsg = document.createElement('div');
  userMsg.className = 'chat-msg user-msg fade-in';
  userMsg.innerHTML = '<div class="chat-avatar user">' + escHtml(initial) + '</div><div class="chat-content"><div class="chat-sender">' + escHtml(userName) + '</div><div class="chat-text" style="border-radius:14px 14px 3px 14px;background:rgba(15,98,254,0.1);border-color:rgba(15,98,254,0.2);color:var(--text-1)">' + escHtml(val) + '</div></div>';
  messages.insertBefore(userMsg, typing);
  input.value = '';
  typing.style.display = 'flex';
  messages.scrollTop = messages.scrollHeight;

  setTimeout(function() {
    typing.style.display = 'none';
    var r = AI_RESPONSES[Math.floor(Math.random() * AI_RESPONSES.length)];
    var aiMsg = document.createElement('div');
    aiMsg.className = 'chat-msg fade-in';
    aiMsg.innerHTML = '<div class="chat-avatar ai">B</div><div class="chat-content"><div class="chat-sender">IBM BOB</div><div class="chat-text">' + r.text + '</div><div class="chat-code"><div class="chat-code-header"><span>' + r.file + '</span><span onclick="copyCode(this)" style="cursor:pointer">Copy</span></div><pre>' + r.code + '</pre></div><div class="action-chips"><div class="action-chip" onclick="addUserMsg(\'Explain this further\')">Explain more</div><div class="action-chip" onclick="addUserMsg(\'Generate tests for this\')">Generate tests</div><div class="action-chip" onclick="addUserMsg(\'Show related files\')">Related files</div></div></div>';
    messages.insertBefore(aiMsg, typing);
    messages.scrollTop = messages.scrollHeight;
  }, 1600);
}

function copyCode(btn) {
  var pre = btn.closest('.chat-code').querySelector('pre');
  var text = pre ? pre.innerText : '';
  if (navigator.clipboard) {
    navigator.clipboard.writeText(text).then(function(){
      btn.textContent = 'Copied!';
      setTimeout(function(){ btn.textContent = 'Copy'; }, 2000);
    });
  }
}

// ─── DOM READY ───
document.addEventListener('DOMContentLoaded', function () {
  restoreSession();
  checkBackendStatus();
  updateAuthUI();

  // Enter key on signup password
  var spwd = document.getElementById('signup-password');
  if (spwd) spwd.addEventListener('keydown', function(e){ if(e.key==='Enter') handleSignup(); });

  // Enter key on login password
  var lpwd = document.getElementById('login-password');
  if (lpwd) lpwd.addEventListener('keydown', function(e){ if(e.key==='Enter') handleLogin(); });

  // Dashboard AI input
  var dashInput = document.getElementById('dash-ai-input');
  if (dashInput) dashInput.addEventListener('keydown', function(e){ if(e.key==='Enter'){e.preventDefault();sendDashMsg();} });

  // Main AI textarea
  var mainInput = document.getElementById('main-ai-input');
  if (mainInput) mainInput.addEventListener('keydown', function(e){ if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMainMsg();} });

  // Toggle switches
  document.querySelectorAll('.toggle').forEach(function(t){
    t.addEventListener('click', function(){ t.classList.toggle('off'); });
  });

  // Settings nav tabs
  document.querySelectorAll('.settings-nav-item').forEach(function(item){
    item.addEventListener('click', function(){
      document.querySelectorAll('.settings-nav-item').forEach(function(i){ i.classList.remove('active'); });
      item.classList.add('active');
    });
  });

  // Scroll-triggered animations
  if (typeof IntersectionObserver !== 'undefined') {
    var observer = new IntersectionObserver(function(entries){
      entries.forEach(function(e){
        if(e.isIntersecting){ e.target.style.opacity='1'; e.target.style.transform='translateY(0)'; }
      });
    }, { threshold: 0.1 });
    document.querySelectorAll('.feature-card,.testimonial-card,.pricing-card,.workflow-step').forEach(function(el){
      el.style.opacity='0'; el.style.transform='translateY(18px)'; el.style.transition='opacity 0.5s ease,transform 0.5s ease';
      observer.observe(el);
    });
  }

  // Set Home active
  document.querySelectorAll('.nav-link').forEach(function(l){
    if(l.textContent.trim()==='Home') l.classList.add('active');
  });
});
