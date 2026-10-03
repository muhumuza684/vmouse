(function () {
  'use strict';
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  // ── Connection ─────────────────────────────────────────────────────────────
  var params = new URLSearchParams(location.search);
  var TOKEN = params.get('k') || '';
  var HOST = location.hostname;
  var SECURE_PAGE = location.protocol === 'https:';
  var PORT = SECURE_PAGE ? (params.get('wss') || '8765') : (params.get('ws') || '8766');
  var ws = null, ready = false, retryTimer = null, retryDelay = 1000, giveUp = false, hb = null, hbTimeout = null;
  var waiting = null; // callback waiting for the next reply

  function setBadge(text, ok) { var b = $('#badge'); b.textContent = text; b.className = 'badge' + (ok ? '' : ' off'); }
  function showStatus(title, text, retry) {
    $('#st-title').textContent = title; $('#st-text').textContent = text; $('#st-retry').hidden = !retry;
    show('status');
  }

  function connect() {
    clearTimeout(retryTimer);
    if (!TOKEN) { giveUp = true; setBadge('Not paired', false); showStatus('Scan the QR code', 'Open the camera on your iPhone and scan the QR code shown by VMouse on your PC.', false); return; }
    setBadge('Connecting', false);
    if (!ready) showStatus('Connecting to your PC', 'Keep this page open. Your PC and phone must be on the same Wi-Fi.', false);
    try { ws = new WebSocket((SECURE_PAGE ? 'wss://' : 'ws://') + HOST + ':' + PORT); } catch (e) { scheduleRetry(); return; }
    var sock = ws;
    sock.onopen = function () { sock.send(JSON.stringify({ type: 'auth', token: TOKEN })); };
    sock.onmessage = function (ev) {
      var msg; try { msg = JSON.parse(ev.data); } catch (e) { return; }
      if (msg.type === 'auth_ok') { ready = true; retryDelay = 1000; setBadge('Connected', true); startHeartbeat(); if (current === 'status') show('home'); return; }
      if (msg.type === 'auth_failed') {
        giveUp = true; ready = false;
        var why = { bad_token: 'This PC did not accept the code. Scan the QR code on the PC again.', blocked: 'Too many wrong tries. Wait two minutes, then scan the QR code again.', web_disabled: 'The iPhone web app is switched off on the PC. Tick "Allow iPhone web app" in VMouse.', auth_required: 'The PC did not accept the connection. Scan the QR code again.' };
        setBadge('Not paired', false); showStatus('Could not connect', why[msg.reason] || why.auth_required, false); return;
      }
      if (msg.type === 'pong') { clearTimeout(hbTimeout); return; }
      if (waiting) { var cb = waiting; waiting = null; cb(msg); }
    };
    sock.onclose = function () {
      if (sock !== ws) return;
      var was = ready; ready = false; stopHeartbeat();
      if (giveUp) return;
      setBadge('PC offline', false);
      if (was) showStatus('PC offline', 'Trying to reconnect…', true);
      scheduleRetry();
    };
    sock.onerror = function () {};
  }
  function scheduleRetry() { clearTimeout(retryTimer); retryTimer = setTimeout(connect, retryDelay); retryDelay = Math.min(retryDelay * 1.6, 8000); }
  function startHeartbeat() {
    stopHeartbeat();
    hb = setInterval(function () { send({ type: 'ping' }); clearTimeout(hbTimeout); hbTimeout = setTimeout(function () { try { ws.close(); } catch (e) {} }, 10000); }, 5000);
  }
  function stopHeartbeat() { clearInterval(hb); clearTimeout(hbTimeout); }
  function send(obj) { if (ws && ready && ws.readyState === 1) { ws.send(JSON.stringify(obj)); return true; } return false; }
  function ask(obj, cb) { waiting = cb; if (!send(obj)) { waiting = null; cb({ status: 'error', message: 'Not connected' }); } }
  $('#st-retry').onclick = function () { giveUp = false; retryDelay = 1000; connect(); };
  document.addEventListener('visibilitychange', function () { if (!document.hidden && !ready && !giveUp) { retryDelay = 1000; connect(); } });

  // ── Screens ────────────────────────────────────────────────────────────────
  var current = 'status', history = [];
  function show(name, push) {
    if (push && current !== 'status') history.push(current);
    current = name;
    $$('.screen').forEach(function (s) { s.classList.toggle('active', s.id === 's-' + name); });
    $('#back').hidden = (name === 'home' || name === 'status');
    if (name === 'health') loadHealth();
  }
  $('#back').onclick = function () { show(history.pop() || 'home'); };
  $$('.tile').forEach(function (t) {
    t.onclick = function () {
      var go = t.getAttribute('data-go');
      if (go === 'keyboard') { show('mouse', true); tab('keyboard'); } else if (go === 'mouse') { show('mouse', true); tab('trackpad'); } else show(go, true);
    };
  });
  function tab(name) {
    $$('[data-tabs="mouse"] button').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-tab') === name); });
    $$('#s-mouse .pane').forEach(function (p) { p.classList.toggle('on', p.getAttribute('data-pane') === name); });
  }
  $$('[data-tabs="mouse"] button').forEach(function (b) { b.onclick = function () { tab(b.getAttribute('data-tab')); }; });

  // ── Trackpad ───────────────────────────────────────────────────────────────
  var pad = $('#pad'), st = null, accX = 0, accY = 0, accS = 0, raf = 0;
  function flush() {
    raf = 0;
    if (Math.abs(accX) >= 0.5 || Math.abs(accY) >= 0.5) { send({ type: 'move', dx: Math.round(accX * 10) / 10, dy: Math.round(accY * 10) / 10 }); accX = 0; accY = 0; }
    var steps = Math.trunc(accS / 8); if (steps) { send({ type: 'scroll', dy: steps }); accS -= steps * 8; }
  }
  function queue() { if (!raf) raf = requestAnimationFrame(flush); }
  function pt(e, i) { var t = e.touches[i]; return { x: t.clientX, y: t.clientY }; }
  pad.addEventListener('touchstart', function (e) {
    e.preventDefault(); pad.classList.add('live');
    if (!st) st = { t: Date.now(), moved: 0, max: 0, last: pt(e, 0), lastY2: null };
    st.max = Math.max(st.max, e.touches.length);
    if (e.touches.length === 2) { st.lastY2 = (pt(e, 0).y + pt(e, 1).y) / 2; }
  }, { passive: false });
  pad.addEventListener('touchmove', function (e) {
    e.preventDefault(); if (!st) return;
    if (e.touches.length >= 2) {
      var y2 = (pt(e, 0).y + pt(e, 1).y) / 2;
      if (st.lastY2 !== null) { accS += (y2 - st.lastY2); st.moved += Math.abs(y2 - st.lastY2); }
      st.lastY2 = y2; queue(); return;
    }
    var p = pt(e, 0); var dx = p.x - st.last.x, dy = p.y - st.last.y; st.last = p; st.moved += Math.abs(dx) + Math.abs(dy);
    accX += dx * 1.4; accY += dy * 1.4; queue();
  }, { passive: false });
  function endTouch(e) {
    e.preventDefault();
    if (e.touches.length > 0 || !st) return;
    var quick = Date.now() - st.t < 280 && st.moved < 10;
    if (quick) send(st.max >= 2 ? { type: 'click', button: 'right', clicks: 1 } : { type: 'click', button: 'left', clicks: 1 });
    st = null; pad.classList.remove('live');
  }
  pad.addEventListener('touchend', endTouch, { passive: false });
  pad.addEventListener('touchcancel', endTouch, { passive: false });
  $$('[data-click]').forEach(function (b) { b.onclick = function () { send({ type: 'click', button: b.getAttribute('data-click'), clicks: 1 }); if (navigator.vibrate) navigator.vibrate(8); }; });

  // ── Keyboard and shortcuts ─────────────────────────────────────────────────
  var kb = $('#pane-keyboard');
  kb.innerHTML = '<div class="row"><input id="txt" type="text" placeholder="Type here to send text to PC…" autocapitalize="off" autocomplete="off" autocorrect="off" spellcheck="false"><button id="txt-send" class="send" aria-label="Send"><svg class="i"><use href="#i-send"/></svg></button></div><div class="grid5" id="keys"></div>';
  var KEYS = [['Esc', 'esc'], ['Tab', 'tab'], ['Backspace', 'backspace'], ['Enter', 'enter'], ['Delete', 'delete'], ['F1', 'f1'], ['F2', 'f2'], ['F3', 'f3'], ['F4', 'f4'], ['F5', 'f5'], ['Home', 'home'], ['End', 'end'], ['PgUp', 'page_up'], ['PgDn', 'page_down'], ['Ins', 'insert'], ['←', 'left'], ['→', 'right'], ['↑', 'up'], ['↓', 'down'], ['Space', 'space']];
  var keysEl = $('#keys');
  KEYS.forEach(function (k) { var b = document.createElement('button'); b.className = 'key'; b.textContent = k[0]; b.onclick = function () { send({ type: 'key', key: k[1] }); }; keysEl.appendChild(b); });
  function sendText() { var t = $('#txt'); if (t.value) { send({ type: 'type', text: t.value }); t.value = ''; } }
  $('#txt-send').onclick = sendText;
  $('#txt').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); sendText(); } });
  var SHORT = [['Copy', 'ctrl+c'], ['Paste', 'ctrl+v'], ['Cut', 'ctrl+x'], ['Undo', 'ctrl+z'], ['Redo', 'ctrl+y'], ['Select All', 'ctrl+a'], ['Save', 'ctrl+s'], ['New Tab', 'ctrl+t'], ['Close Tab', 'ctrl+w'], ['Find', 'ctrl+f'], ['Alt+F4', 'alt+f4'], ['Print Screen', 'printscreen'], ['Task Mgr', 'ctrl+shift+esc'], ['Show Desktop', 'win+d']];
  var sg = $('#shortcut-grid');
  SHORT.forEach(function (s) { var b = document.createElement('button'); b.className = 'btn2'; b.innerHTML = '<b></b><br><small style="color:#8B8AA3"></small>'; b.firstChild.textContent = s[0]; b.lastChild.textContent = s[1]; b.onclick = function () { send({ type: 'shortcut', keys: s[1] }); }; sg.appendChild(b); });

  // ── System controls ────────────────────────────────────────────────────────
  var POWER = [['Lock', 'lock', false, 'Lock the PC?'], ['Sleep', 'sleep', true, 'Put the PC to sleep?'], ['Restart', 'restart', true, 'Restart the PC in 5 seconds?'], ['Shutdown', 'shutdown', true, 'Shut down the PC in 5 seconds?'], ['Sign out', 'logout', true, 'Sign out of the PC?'], ['Cancel shutdown', 'cancel', false, '']];
  var pg = $('#power-grid'), pending = null;
  POWER.forEach(function (p) { var b = document.createElement('button'); b.className = 'btn2'; b.textContent = p[0]; b.onclick = function () { if (p[2]) confirmBox(p[0], p[3], function () { doPower(p[1]); }); else doPower(p[1]); }; pg.appendChild(b); });
  function doPower(action) { ask({ type: 'system_power', action: action }, function (r) { toast(r.message || r.status); }); }
  function confirmBox(title, text, yes) { $('#confirm-title').textContent = title; $('#confirm-text').textContent = text; $('#confirm').hidden = false; pending = yes; }
  $('#confirm-no').onclick = function () { $('#confirm').hidden = true; pending = null; };
  $('#confirm-yes').onclick = function () { $('#confirm').hidden = true; var f = pending; pending = null; if (f) f(); };
  function runCmd() {
    var c = $('#cmd').value.trim(); if (!c) return; var out = $('#cmd-out'); out.hidden = false; out.textContent = 'Running…';
    ask({ type: 'system_command', command: c }, function (r) { out.textContent = r.output || r.message || r.error || r.status || 'No output'; });
  }
  $('#cmd-run').onclick = runCmd;
  $('#cmd').addEventListener('keydown', function (e) { if (e.key === 'Enter') { e.preventDefault(); runCmd(); } });
  function toast(text) { var out = $('#cmd-out'); out.hidden = false; out.textContent = text; }

  // ── Health monitor ─────────────────────────────────────────────────────────
  function meter(label, pct, extra) {
    var c = document.createElement('div'); c.className = 'card';
    var v = (pct === null || pct === undefined) ? 'n/a' : Math.round(pct) + '%';
    c.innerHTML = '<b></b><div class="val"></div>' + (typeof pct === 'number' ? '<div class="meter"><i></i></div>' : '') + '<div class="small"></div>';
    c.firstChild.textContent = label; c.children[1].textContent = v; c.lastChild.textContent = extra || '';
    var bar = c.querySelector('i'); if (bar) { bar.style.width = Math.min(100, pct) + '%'; if (pct > 85) bar.className = 'hot'; }
    return c;
  }
  function loadHealth() {
    var body = $('#health-body'); body.innerHTML = '<p class="small">Loading…</p>';
    ask({ type: 'get_health' }, function (r) {
      var d = r.data; body.innerHTML = '';
      if (!d || d.error) { body.innerHTML = '<p class="small">Could not read the PC health.</p>'; return; }
      body.appendChild(meter('CPU', d.cpu && d.cpu.usage_percent, d.cpu ? d.cpu.cores + (d.cpu.cores === 1 ? ' core' : ' cores') : ''));
      body.appendChild(meter('Memory', d.ram && d.ram.percent, d.ram ? d.ram.used_gb + ' of ' + d.ram.total_gb + ' GB' : ''));
      body.appendChild(meter('Disk', d.disk && d.disk.percent, d.disk ? d.disk.free_gb + ' GB free' : ''));
      if (d.battery && d.battery.percent !== null) body.appendChild(meter('Battery', d.battery.percent, d.battery.plugged_in ? 'Charging' : 'On battery'));
      var a = r.analysis || {}, box = document.createElement('div'); box.className = 'card'; box.innerHTML = '<b>Advice</b>';
      (a.risks || []).forEach(function (t) { var p = document.createElement('div'); p.className = /^no /i.test(t) ? 'risk fine' : 'risk'; p.textContent = t; box.appendChild(p); });
      (a.recommendations || []).forEach(function (t) { var p = document.createElement('div'); p.className = 'rec'; p.textContent = t; box.appendChild(p); });
      if (box.children.length > 1) body.appendChild(box);
    });
  }
  $('#health-refresh').onclick = loadHealth;

  if ('serviceWorker' in navigator && (SECURE_PAGE || location.hostname === 'localhost')) { navigator.serviceWorker.register('sw.js').catch(function () {}); }
  window.__vmouse = { send: send, tab: tab, show: show };
  connect();
})();
