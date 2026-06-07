/* ═══════════════════════════════════════════════════════════════
   DREAM VISUALIZER AI — Main JavaScript
   FIXED: /api/analytics → /api/stats
   FIXED: /api/analyze  → /api/analyze-dream  (correct endpoint)
   FIXED: request body fields match Flask API
═══════════════════════════════════════════════════════════════ */

// ─── Session ──────────────────────────────────────────────────────
let SESSION_ID = localStorage.getItem('dv_session') || null;
if (!SESSION_ID) {
  SESSION_ID = 'dv_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  localStorage.setItem('dv_session', SESSION_ID);
}

// ─── State ────────────────────────────────────────────────────────
let currentDream = null;
let selectedMood = 'calm';
let selectedCategory = 'general';
let isRecording = false;
let recognition = null;
let artworkVariant = 0;

// ─── Examples ─────────────────────────────────────────────────────
const EXAMPLE_DREAMS = [
  "I was soaring above a vast city of golden light, the buildings glowing like embers at sunset. I had magnificent wings made of silver feathers and I could feel the wind currents lifting me higher and higher. Below me, thousands of tiny people went about their lives, unaware I was watching. I felt completely free for the first time in years, invincible even. Then I noticed dark storm clouds gathering at the horizon, approaching rapidly.",
  "I found myself standing at the entrance to an ancient forest where the trees were impossibly tall and the light barely penetrated the canopy. Strange luminescent mushrooms marked a winding path deeper in. A figure in a grey cloak beckoned me forward. I followed, sensing both danger and extraordinary knowledge lay ahead. The trees whispered secrets in a language I almost understood. Suddenly I realized I had been here before, in another life.",
  "The ocean stretched infinitely in all directions, but the water was made of liquid starlight. I was floating on its surface, and below me I could see entire galaxies swirling in the depths. Each time a wave passed through me, I felt memories of my childhood flood back with crystalline clarity. A great whale made entirely of aurora borealis light rose from the deep and looked at me with ancient, knowing eyes."
];

// ─── Init ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  updateNavCount();
  animateHeroConstellation();
  initSpeechRecognition();
});

// ─── Nav Count ────────────────────────────────────────────────────
// FIX: was /api/analytics — correct endpoint is /api/stats
async function updateNavCount() {
  try {
    const res = await fetch('/api/stats');
    const json = await res.json();
    // Flask wraps response in { success: true, data: {...} }
    const data = json.data || json;
    const total = data.overview?.total_dreams ?? data.total_dreams ?? 0;

    const el = document.getElementById('dream-count-nav');
    const stat = document.getElementById('stat-total');
    if (el) el.textContent = `${total} dream${total !== 1 ? 's' : ''}`;
    if (stat) animateNumber(stat, 0, total, 800);
  } catch (e) {
    console.warn('Nav count update failed:', e);
  }
}

function animateNumber(el, from, to, duration) {
  if (!el) return;
  const start = performance.now();
  const range = to - from;
  function step(now) {
    const elapsed = now - start;
    const progress = Math.min(elapsed / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + range * eased);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

// ─── Hero Constellation ───────────────────────────────────────────
function animateHeroConstellation() {
  const svg = document.getElementById('constellation-svg');
  if (!svg) return;

  const stars = [];
  for (let i = 0; i < 40; i++) {
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    stars.push({ x, y, r: Math.random() * 2 + 0.5, opacity: Math.random() * 0.6 + 0.2 });
  }

  stars.forEach(s => {
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', `${s.x}%`);
    circle.setAttribute('cy', `${s.y}%`);
    circle.setAttribute('r', s.r);
    circle.setAttribute('fill', `rgba(168,85,247,${s.opacity})`);
    circle.style.animation = `pulse ${2 + Math.random() * 3}s infinite ${Math.random() * 2}s`;
    svg.appendChild(circle);
  });
}

// ─── Mood & Category ──────────────────────────────────────────────
function selectMood(btn) {
  document.querySelectorAll('.mood-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedMood = btn.dataset.mood;
}

function selectCategory(btn) {
  document.querySelectorAll('.cat-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  selectedCategory = btn.dataset.cat;
}

// ─── Word Count ───────────────────────────────────────────────────
function updateWordCount() {
  const text = document.getElementById('dream-text').value;
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  document.getElementById('word-count').textContent = words;
}

// ─── Voice Input ──────────────────────────────────────────────────
function initSpeechRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    const voiceBtn = document.getElementById('voice-btn');
    if (voiceBtn) voiceBtn.style.opacity = '0.4';
    return;
  }
  recognition = new SpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  recognition.lang = 'en-US';

  let finalTranscript = '';

  recognition.onresult = (event) => {
    let interim = '';
    for (let i = event.resultIndex; i < event.results.length; i++) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      } else {
        interim += event.results[i][0].transcript;
      }
    }
    const textarea = document.getElementById('dream-text');
    textarea.value = finalTranscript + interim;
    updateWordCount();
  };

  recognition.onend = () => {
    if (isRecording) recognition.start();
  };
}

function toggleVoice() {
  if (!recognition) {
    alert('Voice input is not supported in your browser.');
    return;
  }

  const voiceBtn = document.getElementById('voice-btn');
  const voiceStatus = document.getElementById('voice-status');

  if (!isRecording) {
    isRecording = true;
    recognition.start();
    voiceBtn.classList.add('recording');
    if (voiceStatus) voiceStatus.style.display = 'flex';
  } else {
    isRecording = false;
    recognition.stop();
    voiceBtn.classList.remove('recording');
    if (voiceStatus) voiceStatus.style.display = 'none';
  }
}

// ─── Examples ─────────────────────────────────────────────────────
function loadExample(idx) {
  const textarea = document.getElementById('dream-text');
  textarea.value = EXAMPLE_DREAMS[idx];
  updateWordCount();
  textarea.focus();
  textarea.style.transition = 'border-color 0.3s';
  textarea.style.borderColor = 'rgba(168,85,247,0.8)';
  setTimeout(() => (textarea.style.borderColor = ''), 1000);
}

// ─── Scroll ───────────────────────────────────────────────────────
function scrollToDreamInput() {
  document.getElementById('dream-input').scrollIntoView({ behavior: 'smooth' });
}

// ─── Analyze Dream ────────────────────────────────────────────────
// FIX 1: was /api/analyze → correct endpoint is /api/analyze-dream
// FIX 2: body field was "content" → correct field is "dream_text"
// FIX 3: response is wrapped in { success, data } by Flask
async function analyzeDream() {
  const text = document.getElementById('dream-text').value.trim();
  if (!text || text.length < 10) {
    shakeElement(document.getElementById('dream-text'));
    return;
  }

  const titleEl = document.getElementById('dream-title');
  const title = titleEl ? titleEl.value.trim() || 'Untitled Dream' : 'Untitled Dream';

  const btn = document.getElementById('analyze-btn');
  const analyzeText = btn.querySelector('.analyze-text');
  const analyzeLoader = btn.querySelector('.analyze-loader');

  btn.disabled = true;
  if (analyzeText) analyzeText.style.display = 'none';
  if (analyzeLoader) analyzeLoader.style.display = 'flex';

  try {
    const res = await fetch('/api/analyze-dream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        dream_text: text,   // FIX: was "content"
        title: title
      })
    });

    const json = await res.json();

    if (!res.ok || !json.success) {
      throw new Error(json.error || 'Analysis failed');
    }

    // Flask wraps in { success: true, data: {...} }
    const data = json.data;
    currentDream = data;
    artworkVariant = 0;

    showResults(data);
    updateNavCount();

  } catch (err) {
    console.error('Analysis error:', err);
    alert('Analysis failed: ' + err.message);
  } finally {
    btn.disabled = false;
    if (analyzeText) analyzeText.style.display = '';
    if (analyzeLoader) analyzeLoader.style.display = 'none';
  }
}

function shakeElement(el) {
  el.style.animation = 'none';
  el.offsetHeight;
  el.style.animation = 'shake 0.4s ease';
  el.style.borderColor = 'rgba(239,68,68,0.6)';
  setTimeout(() => {
    el.style.animation = '';
    el.style.borderColor = '';
  }, 600);
}

// ─── Save Dream ───────────────────────────────────────────────────
async function saveDream() {
  if (!currentDream) return;

  try {
    const res = await fetch('/api/save-dream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title:          currentDream.title        || 'Untitled Dream',
        dream_text:     currentDream.dream_text   || '',
        mood:           currentDream.mood         || currentDream.emotion || 'Mystery',
        emotion_score:  currentDream.emotion_score ?? currentDream.confidence ?? 0,
        summary:        currentDream.summary      || '',
        interpretation: currentDream.interpretation || '',
        symbols:        currentDream.symbols      || [],
        dream_score:    currentDream.dream_score  || 0,
        image_url:      currentDream.image_url    || ''
      })
    });

    const json = await res.json();
    if (!res.ok || !json.success) throw new Error(json.error || 'Save failed');

    const btn = document.getElementById('save-btn');
    if (btn) {
      btn.textContent = '✓ Saved!';
      btn.style.background = 'rgba(16,185,129,0.2)';
      setTimeout(() => {
        btn.textContent = 'Save Dream';
        btn.style.background = '';
      }, 2000);
    }
    updateNavCount();

  } catch (err) {
    console.error('Save error:', err);
    alert('Could not save dream: ' + err.message);
  }
}

// ─── Show Results ─────────────────────────────────────────────────
function showResults(data) {
  const hero         = document.getElementById('hero');
  const inputSection = document.getElementById('dream-input');
  const resultsSection = document.getElementById('results');
  const features     = document.getElementById('features');

  if (hero)         hero.style.display = 'none';
  if (inputSection) inputSection.style.display = 'none';
  if (features)     features.style.display = 'none';
  if (resultsSection) {
    resultsSection.style.display = 'block';
    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  populateScore(data);
  populateEmotions(data);
  populateAnalysis(data);
  populateSymbols(data);
  populateThemes(data);
  populateInsights(data);
  generateDreamArtwork(data);

  const desc = document.getElementById('artwork-desc');
  if (desc) desc.textContent = data.artwork_prompt || data.summary || '';
}

function populateScore(data) {
  const scoreNumber = document.getElementById('score-number');
  const scoreFill   = document.querySelector('.score-fill');
  const scoreLabel  = document.getElementById('score-label');

  if (!scoreNumber) return;

  animateNumber(scoreNumber, 0, data.dream_score || 0, 1200);

  if (scoreFill) {
    setTimeout(() => {
      const circumference = 327;
      const offset = circumference - ((data.dream_score || 0) / 100) * circumference;
      scoreFill.style.transition = 'stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1)';
      scoreFill.style.strokeDashoffset = offset;
    }, 300);
  }

  if (scoreLabel) {
    const labels = {
      high: ['Vivid & Complex', 'Deeply Symbolic', 'Richly Layered'],
      mid:  ['Emotionally Rich', 'Meaningful', 'Insightful'],
      low:  ['Fragmented', 'Impressionistic', 'Fleeting']
    };
    const score  = data.dream_score || 0;
    const bucket = score >= 70 ? 'high' : score >= 45 ? 'mid' : 'low';
    const opts   = labels[bucket];
    scoreLabel.textContent = opts[Math.floor(Math.random() * opts.length)];
  }
}

function populateEmotions(data) {
  const EMOTION_ICONS = {
    Joy: '☀️', Fear: '👁️', Anxiety: '🌀', Sadness: '🌧️',
    Excitement: '⚡', Mystery: '🔮', Love: '💫', Adventure: '🧭',
    Happy: '😊'
  };

  const icon = document.getElementById('emotion-icon');
  const name = document.getElementById('emotion-name');
  // API returns "emotion" field
  const emotion = data.emotion || data.mood || 'Mystery';
  if (icon) icon.textContent = EMOTION_ICONS[emotion] || '🌙';
  if (name) name.textContent = emotion;

  // Confidence bar (API returns confidence, not emotion_scores array)
  const barsContainer = document.getElementById('emotion-bars');
  if (!barsContainer) return;

  if (data.emotion_scores) {
    // If full scores object exists
    const sorted = Object.entries(data.emotion_scores)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 4);

    barsContainer.innerHTML = sorted.map(([em, score]) => `
      <div class="emotion-bar-item">
        <div class="emotion-bar-label">${em}</div>
        <div class="emotion-bar-track">
          <div class="emotion-bar-fill" style="width:0%" data-target="${score}%"></div>
        </div>
        <div class="emotion-bar-pct">${score}%</div>
      </div>
    `).join('');
  } else {
    // Fallback: show single dominant emotion with confidence
    const pct = Math.round((data.confidence || data.emotion_score || 0.5) * 100);
    barsContainer.innerHTML = `
      <div class="emotion-bar-item">
        <div class="emotion-bar-label">${emotion}</div>
        <div class="emotion-bar-track">
          <div class="emotion-bar-fill" style="width:0%" data-target="${pct}%"></div>
        </div>
        <div class="emotion-bar-pct">${pct}%</div>
      </div>
    `;
  }

  setTimeout(() => {
    barsContainer.querySelectorAll('.emotion-bar-fill').forEach(bar => {
      bar.style.transition = 'width 1s cubic-bezier(0.4, 0, 0.2, 1)';
      bar.style.width = bar.dataset.target;
    });
  }, 400);
}

function populateAnalysis(data) {
  const title = document.getElementById('result-title');
  const text  = document.getElementById('analysis-text');
  if (title) title.textContent = data.title || 'Dream Analysis';
  // API returns "summary" not "analysis"
  if (text)  text.textContent  = data.summary || data.analysis || '';
}

function populateSymbols(data) {
  const grid = document.getElementById('symbols-grid');
  if (!grid) return;

  // API returns symbol_details: [{symbol, meaning}]
  const symbols = data.symbol_details || data.symbols || [];
  if (!symbols.length) {
    grid.innerHTML = '<p style="color:rgba(255,255,255,0.4);font-size:.85rem;">No symbols detected.</p>';
    return;
  }

  grid.innerHTML = symbols.map(sym => {
    const name    = typeof sym === 'string' ? sym : sym.symbol || sym;
    const meaning = typeof sym === 'object' ? sym.meaning || '' : '';
    return `
      <div class="symbol-item" style="animation: fadeInUp 0.4s ease both">
        <div class="symbol-name">${name}</div>
        <div class="symbol-meaning">${meaning}</div>
      </div>
    `;
  }).join('');
}

function populateThemes(data) {
  const pills  = document.getElementById('themes-pills');
  const interp = document.getElementById('interpretation-text');

  // API returns recurring_patterns as themes
  const themes = data.themes || data.recurring_patterns || [];
  if (pills) {
    pills.innerHTML = themes.length
      ? themes.map(t => `<span class="theme-pill">${t}</span>`).join('')
      : '<span class="theme-pill">General</span>';
  }

  if (interp) interp.textContent = data.interpretation || '';
}

function populateInsights(data) {
  const list = document.getElementById('insights-list');
  if (!list) return;

  // API doesn't return psychological_insights directly — use interpretation
  const insights = data.psychological_insights
    || (data.interpretation ? [data.interpretation] : []);

  if (!insights.length) {
    list.innerHTML = '<div style="color:rgba(255,255,255,0.4);font-size:.85rem;">No insights available.</div>';
    return;
  }

  list.innerHTML = insights.map((insight, i) => `
    <div class="insight-item" style="animation: fadeInUp 0.4s ease ${i * 0.1}s both">
      <div class="insight-dot"></div>
      <div class="insight-text">${insight}</div>
    </div>
  `).join('');
}

// ─── Dream Artwork Generator ──────────────────────────────────────
function generateDreamArtwork(data) {
  const canvas = document.getElementById('dream-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;

  // Derive theme from emotion if artwork_theme not present
  const emotion = data.emotion || data.mood || 'Mystery';
  const EMOTION_THEMES = {
    Happy:     { from: '#1a1200', via: '#2d2000', to: '#0d0d00', accent: '#f59e0b' },
    Fear:      { from: '#0d0014', via: '#1a0028', to: '#000014', accent: '#7c3aed' },
    Adventure: { from: '#001a0d', via: '#002814', to: '#000d07', accent: '#10b981' },
    Mystery:   { from: '#0a0a1e', via: '#0f0f2e', to: '#050514', accent: '#6366f1' },
    Love:      { from: '#1a0010', via: '#280018', to: '#0d0008', accent: '#f43f5e' },
    Anxiety:   { from: '#1a0a00', via: '#281400', to: '#0d0500', accent: '#f97316' },
    Excitement:{ from: '#1a1400', via: '#281e00', to: '#0d0a00', accent: '#eab308' },
    Sadness:   { from: '#000a1a', via: '#000f28', to: '#00050d', accent: '#64748b' },
  };
  const theme = data.artwork_theme || EMOTION_THEMES[emotion] || EMOTION_THEMES['Mystery'];

  ctx.clearRect(0, 0, W, H);

  const seed = hashString((data.title || 'dream') + artworkVariant);
  const rng  = seededRandom(seed);

  // Background gradient
  const bgGrad = ctx.createLinearGradient(0, 0, W, H);
  bgGrad.addColorStop(0,   theme.from);
  bgGrad.addColorStop(0.5, theme.via || theme.from);
  bgGrad.addColorStop(1,   theme.to);
  ctx.fillStyle = bgGrad;
  ctx.fillRect(0, 0, W, H);

  // Nebula layers
  for (let i = 0; i < 5; i++) {
    const x = rng() * W, y = rng() * H, r = 80 + rng() * 200;
    const alpha = rng() * 0.15 + 0.05;
    const nebula = ctx.createRadialGradient(x, y, 0, x, y, r);
    nebula.addColorStop(0, hexToRgba(theme.accent, alpha));
    nebula.addColorStop(1, 'transparent');
    ctx.fillStyle = nebula;
    ctx.fillRect(0, 0, W, H);
  }

  // Light rays
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  for (let i = 0; i < 4; i++) {
    const sx = rng() * W, sy = rng() * H * 0.5;
    const angle = rng() * Math.PI * 2, len = 150 + rng() * 250;
    const ray = ctx.createLinearGradient(sx, sy, sx + Math.cos(angle) * len, sy + Math.sin(angle) * len);
    ray.addColorStop(0, hexToRgba(theme.accent, 0.06));
    ray.addColorStop(1, 'transparent');
    ctx.strokeStyle = ray;
    ctx.lineWidth = 40 + rng() * 60;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(sx + Math.cos(angle) * len, sy + Math.sin(angle) * len);
    ctx.stroke();
  }
  ctx.restore();

  // Stars
  ctx.save();
  for (let i = 0; i < 200; i++) {
    const x = rng() * W, y = rng() * H, r = rng() * 1.5;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fillStyle = `rgba(255,255,255,${rng() * 0.8 + 0.2})`;
    ctx.fill();
  }
  ctx.restore();

  // Glowing orbs
  for (let i = 0; i < 3; i++) {
    const x = (0.2 + rng() * 0.6) * W, y = (0.2 + rng() * 0.6) * H, r = 20 + rng() * 60;
    const orb = ctx.createRadialGradient(x, y, 0, x, y, r);
    orb.addColorStop(0,   hexToRgba(theme.accent, 0.5));
    orb.addColorStop(0.4, hexToRgba(theme.accent, 0.2));
    orb.addColorStop(1,   'transparent');
    ctx.fillStyle = orb;
    ctx.fillRect(0, 0, W, H);
  }

  drawDreamShapes(ctx, W, H, theme, rng, emotion);
  addFilmGrain(ctx, W, H);

  // Vignette
  const vignette = ctx.createRadialGradient(W/2, H/2, H*0.3, W/2, H/2, H*0.8);
  vignette.addColorStop(0, 'transparent');
  vignette.addColorStop(1, 'rgba(0,0,0,0.5)');
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, W, H);

  const vizTitle     = document.getElementById('viz-title');
  const vizEmotionTag = document.getElementById('viz-emotion-tag');
  if (vizTitle)      vizTitle.textContent     = data.title || 'Dream';
  if (vizEmotionTag) vizEmotionTag.textContent = `✦ ${emotion} Dream`;
}

function drawDreamShapes(ctx, W, H, theme, rng, emotion) {
  ctx.save();
  ctx.globalCompositeOperation = 'screen';
  ctx.globalAlpha = 0.15;

  const count = emotion === 'Mystery' ? 8 : emotion === 'Adventure' ? 12 : 6;
  for (let i = 0; i < count; i++) {
    const x = rng() * W, y = rng() * H, size = 30 + rng() * 100;
    const type = Math.floor(rng() * 4);
    ctx.strokeStyle = theme.accent;
    ctx.lineWidth = 0.5 + rng() * 1;

    if (type === 0) {
      ctx.beginPath(); ctx.arc(x, y, size, 0, Math.PI * 2); ctx.stroke();
    } else if (type === 1) {
      ctx.beginPath();
      for (let j = 0; j < 3; j++) {
        const angle = (j / 3) * Math.PI * 2 - Math.PI / 2;
        j === 0 ? ctx.moveTo(x + Math.cos(angle)*size, y + Math.sin(angle)*size)
                : ctx.lineTo(x + Math.cos(angle)*size, y + Math.sin(angle)*size);
      }
      ctx.closePath(); ctx.stroke();
    } else if (type === 2) {
      ctx.beginPath();
      ctx.moveTo(x, y - size); ctx.lineTo(x + size*0.6, y);
      ctx.lineTo(x, y + size); ctx.lineTo(x - size*0.6, y);
      ctx.closePath(); ctx.stroke();
    } else {
      const spikes = 5;
      ctx.beginPath();
      for (let j = 0; j < spikes * 2; j++) {
        const angle = (j / (spikes * 2)) * Math.PI * 2 - Math.PI / 2;
        const r = j % 2 === 0 ? size : size * 0.4;
        j === 0 ? ctx.moveTo(x + Math.cos(angle)*r, y + Math.sin(angle)*r)
                : ctx.lineTo(x + Math.cos(angle)*r, y + Math.sin(angle)*r);
      }
      ctx.closePath(); ctx.stroke();
    }
  }
  ctx.restore();
}

function addFilmGrain(ctx, W, H) {
  ctx.save();
  ctx.globalAlpha = 0.03;
  const imageData = ctx.createImageData(W, H);
  for (let i = 0; i < imageData.data.length; i += 4) {
    const val = Math.floor(Math.random() * 255);
    imageData.data[i] = imageData.data[i+1] = imageData.data[i+2] = val;
    imageData.data[i+3] = 255;
  }
  ctx.putImageData(imageData, 0, 0);
  ctx.restore();
}

function hexToRgba(hex, alpha) {
  if (!hex || hex.startsWith('rgba')) return hex || `rgba(168,85,247,${alpha})`;
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgba(${r},${g},${b},${alpha})`;
}

function hashString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = ((hash << 5) - hash) + str.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function seededRandom(seed) {
  let s = seed;
  return function() {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Artwork Actions ──────────────────────────────────────────────
function downloadArtwork() {
  const canvas = document.getElementById('dream-canvas');
  if (!canvas) return;
  const link = document.createElement('a');
  link.download = `dream-${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

function regenerateArtwork() {
  if (!currentDream) return;
  artworkVariant++;
  generateDreamArtwork(currentDream);

  const btn = document.querySelector('.viz-btn:nth-child(2)');
  if (btn) {
    btn.style.transform = 'rotate(360deg)';
    btn.style.transition = 'transform 0.5s ease';
    setTimeout(() => { btn.style.transform = ''; btn.style.transition = ''; }, 500);
  }
}

// ─── Share Card ───────────────────────────────────────────────────
function openShareCard() {
  if (!currentDream) return;

  const modal    = document.getElementById('share-modal');
  const cardBg   = document.getElementById('share-card-bg');
  const titleEl  = document.getElementById('share-card-title');
  const emotionEl= document.getElementById('share-card-emotion');
  const excerpt  = document.getElementById('share-card-excerpt');
  const scoreEl  = document.getElementById('share-score');
  const dateEl   = document.getElementById('share-date');

  if (modal) modal.style.display = 'flex';

  const theme = currentDream.artwork_theme || {};
  if (cardBg) {
    cardBg.style.background = `linear-gradient(135deg, ${theme.from || '#1a0533'}, ${theme.via || '#051a2e'}, ${theme.to || '#0a1a1a'})`;
  }

  const emotion = currentDream.emotion || currentDream.mood || 'Mystery';
  if (titleEl)   titleEl.textContent   = currentDream.title || 'My Dream';
  if (emotionEl) emotionEl.innerHTML   = `<span>${getEmotionIcon(emotion)}</span> ${emotion}`;
  if (excerpt)   excerpt.textContent   = (currentDream.summary || currentDream.analysis || '').substring(0, 160) + '...';
  if (scoreEl)   scoreEl.textContent   = currentDream.dream_score || 0;
  if (dateEl)    dateEl.textContent    = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

  document.body.style.overflow = 'hidden';
}

function closeShareModal(e) {
  if (!e || e.target.classList.contains('modal-overlay') || e.type === 'click') {
    const modal = document.getElementById('share-modal');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
  }
}

function downloadShareCard() {
  const canvas = document.createElement('canvas');
  canvas.width = 500; canvas.height = 300;
  const ctx = canvas.getContext('2d');

  const theme   = currentDream?.artwork_theme || {};
  const emotion = currentDream?.emotion || currentDream?.mood || 'Mystery';

  const grad = ctx.createLinearGradient(0, 0, 500, 300);
  grad.addColorStop(0,   theme.from || '#1a0533');
  grad.addColorStop(0.5, theme.via  || '#051a2e');
  grad.addColorStop(1,   theme.to   || '#0a1a1a');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, 500, 300);

  ctx.fillStyle = theme.accent || '#a855f7';
  ctx.font = 'bold 14px monospace';
  ctx.fillText('✦ DreamVis AI', 28, 40);

  ctx.fillStyle = 'rgba(255,255,255,0.4)';
  ctx.font = '11px monospace';
  ctx.fillText(new Date().toLocaleDateString(), 380, 40);

  ctx.fillStyle = 'rgba(255,255,255,0.9)';
  ctx.font = 'italic 20px Georgia';
  ctx.fillText((currentDream?.title || 'My Dream').substring(0, 45), 28, 100);

  ctx.fillStyle = theme.accent || '#a855f7';
  ctx.font = '13px monospace';
  ctx.fillText(`${getEmotionIcon(emotion)} ${emotion}`, 28, 140);

  ctx.fillStyle = '#f59e0b';
  ctx.font = '13px monospace';
  ctx.fillText(`Dream Score: ${currentDream?.dream_score || 0}`, 28, 230);

  ctx.fillStyle = 'rgba(255,255,255,0.3)';
  ctx.font = '11px monospace';
  ctx.fillText('dreamvisualizer.ai', 28, 272);

  const link = document.createElement('a');
  link.download = `dream-card-${Date.now()}.png`;
  link.href = canvas.toDataURL('image/png');
  link.click();
}

function getEmotionIcon(emotion) {
  const icons = {
    Joy: '☀️', Fear: '👁️', Anxiety: '🌀', Sadness: '🌧️',
    Excitement: '⚡', Mystery: '🔮', Love: '💫', Adventure: '🧭', Happy: '😊'
  };
  return icons[emotion] || '🌙';
}

// ─── Reset ────────────────────────────────────────────────────────
function resetToInput() {
  currentDream  = null;
  artworkVariant = 0;

  const dreamText = document.getElementById('dream-text');
  const wordCount = document.getElementById('word-count');
  if (dreamText) dreamText.value = '';
  if (wordCount)  wordCount.textContent = '0';

  const results    = document.getElementById('results');
  const hero       = document.getElementById('hero');
  const dreamInput = document.getElementById('dream-input');
  const features   = document.getElementById('features');
  if (results)    results.style.display    = 'none';
  if (hero)       hero.style.display       = '';
  if (dreamInput) dreamInput.style.display = '';
  if (features)   features.style.display   = '';

  if (dreamInput) dreamInput.scrollIntoView({ behavior: 'smooth' });

  const scoreFill = document.querySelector('.score-fill');
  if (scoreFill)  scoreFill.style.strokeDashoffset = '327';
}