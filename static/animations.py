"""
NoteCaster — Animations Module
================================
Tutte le animazioni CSS/JS per la landing page e l'app Streamlit.

Brand: Navy (#1e3a5f → #2563eb) + Sky blue (#0ea5e9 → #0284c7)
Target: Studenti medicina 18-25 anni
Principi: Smooth (60fps), sottili, mobile-first, prefers-reduced-motion
"""

ANIMATION_CSS = """
/* ============================================================
   NoteCaster — Animation Stylesheet
   ============================================================ */

/* ── prefers-reduced-motion: disabilita TUTTE le animazioni ── */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}

/* ═══════════════════════════════════════════════════════════════
   1. HERO — Onde/Flussi animati in background
   ═══════════════════════════════════════════════════════════════ */

.nc-hero {
  position: relative;
  overflow: hidden;
  min-height: 90vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.nc-hero-bg {
  position: absolute;
  inset: 0;
  z-index: 0;
  overflow: hidden;
}

.nc-hero-wave {
  position: absolute;
  width: 200%;
  height: 200%;
  top: -50%;
  left: -50%;
  border-radius: 45%;
  opacity: 0.15;
  will-change: transform;
}

.nc-hero-wave--1 {
  background: linear-gradient(135deg, #1e3a5f, #2563eb);
  animation: ncWaveRotate 20s linear infinite;
}

.nc-hero-wave--2 {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
  animation: ncWaveRotate 30s linear infinite reverse;
  opacity: 0.10;
}

.nc-hero-wave--3 {
  background: linear-gradient(135deg, #1e3a5f, #0ea5e9);
  animation: ncWaveRotate 25s linear infinite;
  opacity: 0.08;
  width: 150%;
  height: 150%;
  top: -25%;
  left: -25%;
}

@keyframes ncWaveRotate {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

/* ── Hero: Microfono fluttuante con glow ── */
.nc-hero-mic {
  display: inline-block;
  font-size: 5rem;
  line-height: 1;
  animation: ncFloat 3s ease-in-out infinite;
  filter: drop-shadow(0 0 20px rgba(30, 58, 95, 0.3));
  will-change: transform;
}

@keyframes ncFloat {
  0%, 100% { transform: translateY(0px); }
  50%      { transform: translateY(-12px); }
}

.nc-hero-glow {
  position: absolute;
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(30,58,95,0.2) 0%, transparent 70%);
  animation: ncGlowPulse 2.5s ease-in-out infinite;
  pointer-events: none;
}

@keyframes ncGlowPulse {
  0%, 100% { transform: scale(0.8); opacity: 0.4; }
  50%      { transform: scale(1.3); opacity: 0.8; }
}

/* ── Hero: Testo fade-in + slide-up ── */
.nc-hero-title {
  opacity: 0;
  transform: translateY(30px);
  animation: ncFadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
}

.nc-hero-subtitle {
  opacity: 0;
  transform: translateY(20px);
  animation: ncFadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.5s forwards;
}

.nc-hero-cta {
  opacity: 0;
  transform: translateY(20px);
  animation: ncFadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.8s forwards;
}

@keyframes ncFadeInUp {
  to { opacity: 1; transform: translateY(0); }
}

/* ── Hero: Floating dots / particelle ── */
.nc-particle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  will-change: transform;
}

.nc-particle--purple {
  background: rgba(30, 58, 95, 0.3);
  box-shadow: 0 0 6px rgba(30, 58, 95, 0.2);
}

.nc-particle--teal {
  background: rgba(14, 165, 233, 0.3);
  box-shadow: 0 0 6px rgba(14, 165, 233, 0.2);
}

/* ═══════════════════════════════════════════════════════════════
   2. SCROLL ANIMATIONS — Fade-in-up all'intersezione
   ═══════════════════════════════════════════════════════════════ */

.nc-scroll-fade {
  opacity: 0;
  transform: translateY(40px);
  transition: opacity 0.7s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: opacity, transform;
}

.nc-scroll-fade.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.nc-scroll-fade[data-delay="1"]  { transition-delay: 0.05s; }
.nc-scroll-fade[data-delay="2"]  { transition-delay: 0.10s; }
.nc-scroll-fade[data-delay="3"]  { transition-delay: 0.15s; }
.nc-scroll-fade[data-delay="4"]  { transition-delay: 0.20s; }
.nc-scroll-fade[data-delay="5"]  { transition-delay: 0.25s; }
.nc-scroll-fade[data-delay="6"]  { transition-delay: 0.30s; }

/* ── Scroll Progress Bar ── */
.nc-scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #1e3a5f, #2563eb, #0ea5e9, #0284c7);
  background-size: 300% 100%;
  animation: ncShimmer 3s linear infinite;
  z-index: 999999;
  width: 0%;
  transition: width 0.1s linear;
  will-change: width;
}

@keyframes ncShimmer {
  0%   { background-position: 0% center; }
  50%  { background-position: 100% center; }
  100% { background-position: 0% center; }
}

/* ── Parallax leggero ── */
.nc-parallax {
  will-change: transform;
  transition: transform 0.1s linear;
}

/* ═══════════════════════════════════════════════════════════════
   3. CARDS / FEATURE BOXES — Hover effects
   ═══════════════════════════════════════════════════════════════ */

.nc-card {
  position: relative;
  background: rgba(255, 255, 255, 0.75);
  border: 1px solid rgba(30, 58, 95, 0.15);
  border-radius: 18px;
  padding: 1.5rem;
  backdrop-filter: blur(10px);
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              border-color 0.35s ease;
  will-change: transform;
  overflow: hidden;
}

.nc-card::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 20px;
  background: linear-gradient(135deg, #1e3a5f, #2563eb, #0ea5e9, #0284c7, #1e3a5f);
  background-size: 400% 400%;
  opacity: 0;
  transition: opacity 0.35s ease;
  z-index: -1;
  animation: ncGradientShift 4s ease infinite;
}

@keyframes ncGradientShift {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.nc-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 20px 40px rgba(30, 58, 95, 0.15),
              0 8px 20px rgba(14, 165, 233, 0.10);
  border-color: transparent;
}

.nc-card:hover::before {
  opacity: 1;
}

.nc-card::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(30,58,95,0.08) 0%, transparent 70%);
  transform: translate(-50%, -50%);
  transition: width 0.5s ease, height 0.5s ease;
  pointer-events: none;
}

.nc-card:hover::after {
  width: 300%;
  height: 300%;
}

.nc-card-icon {
  display: inline-block;
  font-size: 2rem;
  animation: ncIconPulse 3s ease-in-out infinite;
  will-change: transform;
}

@keyframes ncIconPulse {
  0%, 100% { transform: scale(1); }
  50%      { transform: scale(1.08); }
}

/* ═══════════════════════════════════════════════════════════════
   4. CTA BUTTONS — Gradient animato + pulse + ripple
   ═══════════════════════════════════════════════════════════════ */

.nc-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 2rem;
  border: none;
  border-radius: 12px;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  overflow: hidden;
  outline: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  will-change: transform;
  text-decoration: none;
}

.nc-btn--primary {
  background: linear-gradient(135deg, #1e3a5f, #2563eb, #0ea5e9, #1e3a5f);
  background-size: 300% 300%;
  animation: ncBtnGradient 4s ease infinite;
  color: #fff;
  box-shadow: 0 4px 15px rgba(30, 58, 95, 0.35);
}

@keyframes ncBtnGradient {
  0%   { background-position: 0% 50%; }
  50%  { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.nc-btn--primary::after {
  content: '';
  position: absolute;
  inset: -4px;
  border-radius: 16px;
  border: 2px solid rgba(30, 58, 95, 0.3);
  animation: ncBtnPulse 3s ease-in-out infinite;
  pointer-events: none;
}

@keyframes ncBtnPulse {
  0%, 100% { transform: scale(1); opacity: 0.5; }
  50%      { transform: scale(1.06); opacity: 0; }
}

.nc-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(30, 58, 95, 0.45);
}

.nc-btn:active {
  transform: translateY(0);
}

.nc-ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transform: scale(0);
  animation: ncRippleAnim 0.6s ease-out;
  pointer-events: none;
}

@keyframes ncRippleAnim {
  to { transform: scale(4); opacity: 0; }
}

/* ═══════════════════════════════════════════════════════════════
   5. AUDIO PLAYER — Waveform + Disco rotante
   ═══════════════════════════════════════════════════════════════ */

.nc-waveform {
  display: flex;
  align-items: center;
  gap: 3px;
  height: 40px;
}

.nc-waveform-bar {
  width: 4px;
  border-radius: 2px;
  background: linear-gradient(to top, #1e3a5f, #2563eb);
  animation: ncWaveformAnim 0.8s ease-in-out infinite alternate;
  will-change: transform;
}

.nc-waveform-bar:nth-child(1)  { animation-delay: 0.0s; height: 20%; }
.nc-waveform-bar:nth-child(2)  { animation-delay: 0.1s; height: 40%; }
.nc-waveform-bar:nth-child(3)  { animation-delay: 0.2s; height: 60%; }
.nc-waveform-bar:nth-child(4)  { animation-delay: 0.3s; height: 80%; }
.nc-waveform-bar:nth-child(5)  { animation-delay: 0.4s; height: 100%; }
.nc-waveform-bar:nth-child(6)  { animation-delay: 0.3s; height: 80%; }
.nc-waveform-bar:nth-child(7)  { animation-delay: 0.2s; height: 60%; }
.nc-waveform-bar:nth-child(8)  { animation-delay: 0.1s; height: 40%; }
.nc-waveform-bar:nth-child(9)  { animation-delay: 0.0s; height: 20%; }
.nc-waveform-bar:nth-child(10) { animation-delay: 0.15s; height: 50%; }
.nc-waveform-bar:nth-child(11) { animation-delay: 0.25s; height: 70%; }
.nc-waveform-bar:nth-child(12) { animation-delay: 0.35s; height: 90%; }
.nc-waveform-bar:nth-child(13) { animation-delay: 0.25s; height: 70%; }
.nc-waveform-bar:nth-child(14) { animation-delay: 0.15s; height: 50%; }
.nc-waveform-bar:nth-child(15) { animation-delay: 0.05s; height: 30%; }

@keyframes ncWaveformAnim {
  0%   { transform: scaleY(0.3); }
  100% { transform: scaleY(1); }
}

.nc-spinning-disc {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #1e3a5f, #2563eb, #0ea5e9, #0284c7, #1e3a5f);
  animation: ncSpin 3s linear infinite;
  box-shadow: 0 0 20px rgba(30, 58, 95, 0.2);
  will-change: transform;
}

.nc-spinning-disc.is-paused {
  animation-play-state: paused;
}

.nc-vinyl {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: conic-gradient(from 0deg, #0f172a, #1e293b, #0f172a, #1e293b, #0f172a);
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ncSpin 4s linear infinite;
  box-shadow: 0 0 15px rgba(30, 58, 95, 0.15);
  will-change: transform;
}

.nc-vinyl.is-paused {
  animation-play-state: paused;
}

.nc-vinyl-center {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1e3a5f, #2563eb);
  box-shadow: 0 0 8px rgba(30, 58, 95, 0.4);
}

@keyframes ncSpin {
  from { transform: rotate(0deg); }
  to   { transform: rotate(360deg); }
}

/* ═══════════════════════════════════════════════════════════════
   6. PRICING CARDS
   ═══════════════════════════════════════════════════════════════ */

.nc-pricing-card {
  position: relative;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(30, 58, 95, 0.15);
  border-radius: 20px;
  padding: 2rem 1.5rem;
  backdrop-filter: blur(10px);
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  will-change: transform;
  text-align: center;
}

.nc-pricing-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 24px 48px rgba(30, 58, 95, 0.12),
              0 8px 24px rgba(14, 165, 233, 0.08);
}

.nc-pricing-card--featured {
  border: 2px solid transparent;
  background-clip: padding-box;
  box-shadow: 0 8px 32px rgba(30, 58, 95, 0.15);
}

.nc-pricing-card--featured::before {
  content: '';
  position: absolute;
  inset: -2px;
  border-radius: 22px;
  background: linear-gradient(135deg, #1e3a5f, #2563eb, #0ea5e9, #0284c7, #1e3a5f);
  background-size: 400% 400%;
  animation: ncGradientShift 4s ease infinite;
  z-index: -1;
}

.nc-pricing-badge {
  position: absolute;
  top: -14px;
  left: 50%;
  transform: translateX(-50%);
  background: linear-gradient(135deg, #1e3a5f, #2563eb);
  color: #fff;
  font-size: 0.72rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 4px 16px;
  border-radius: 999px;
  white-space: nowrap;
  animation: ncBadgeFloat 2.5s ease-in-out infinite;
  box-shadow: 0 4px 12px rgba(30, 58, 95, 0.3);
  will-change: transform;
}

@keyframes ncBadgeFloat {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50%      { transform: translateX(-50%) translateY(-6px); }
}

/* ═══════════════════════════════════════════════════════════════
   UTILITY — Loading shimmer
   ═══════════════════════════════════════════════════════════════ */

.nc-skeleton {
  background: linear-gradient(90deg, rgba(30,58,95,0.06) 25%, rgba(30,58,95,0.12) 50%, rgba(30,58,95,0.06) 75%);
  background-size: 200% 100%;
  animation: ncSkeletonShimmer 1.5s ease-in-out infinite;
  border-radius: 8px;
}

@keyframes ncSkeletonShimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

/* ═══════════════════════════════════════════════════════════════
   RESPONSIVE
   ═══════════════════════════════════════════════════════════════ */

@media (max-width: 768px) {
  .nc-hero-mic { font-size: 3.5rem; }
  .nc-hero-glow { width: 80px; height: 80px; }
  .nc-card:hover { transform: translateY(-3px) scale(1.01); }
  .nc-pricing-card:hover { transform: translateY(-4px); }
  .nc-btn { padding: 0.6rem 1.5rem; font-size: 0.9rem; }
}
"""


ANIMATION_JS = """
(function() {
  'use strict';

  var prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (prefersReducedMotion) return;

  var doc = window.parent.document || document;
  var win = window;

  /* ── 1. HERO: Particelle fluttuanti ── */
  function initParticles(container) {
    if (!container) return;
    var count = win.innerWidth < 768 ? 15 : 30;
    var colors = ['nc-particle--purple', 'nc-particle--teal'];

    for (var i = 0; i < count; i++) {
      var p = doc.createElement('div');
      p.className = 'nc-particle ' + colors[i % 2];
      var size = 3 + Math.random() * 6;
      p.style.width = size + 'px';
      p.style.height = size + 'px';
      p.style.left = Math.random() * 100 + '%';
      p.style.top = Math.random() * 100 + '%';
      p.style.opacity = 0.2 + Math.random() * 0.4;
      p.style.animation = 'ncParticleFloat' + (i % 3) + ' ' + (6 + Math.random() * 8) + 's ease-in-out infinite';
      p.style.animationDelay = Math.random() * 5 + 's';
      container.appendChild(p);
    }

    var style = doc.createElement('style');
    style.textContent =
      '@keyframes ncParticleFloat0 { 0%,100% { transform: translate(0,0); } 25% { transform: translate(30px,-20px); } 50% { transform: translate(-20px,30px); } 75% { transform: translate(20px,20px); } }' +
      '@keyframes ncParticleFloat1 { 0%,100% { transform: translate(0,0); } 25% { transform: translate(-25px,25px); } 50% { transform: translate(30px,-15px); } 75% { transform: translate(-15px,-25px); } }' +
      '@keyframes ncParticleFloat2 { 0%,100% { transform: translate(0,0); } 33% { transform: translate(20px,-30px); } 66% { transform: translate(-30px,10px); } }';
    doc.head.appendChild(style);
  }

  /* ── 2. SCROLL: Intersection Observer ── */
  function initScrollAnimations() {
    var els = doc.querySelectorAll('.nc-scroll-fade');
    if (!els.length) return;

    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    for (var i = 0; i < els.length; i++) {
      observer.observe(els[i]);
    }
  }

  /* ── 2. SCROLL: Progress bar ── */
  function initScrollProgress() {
    var bar = doc.getElementById('nc-scroll-progress');
    if (!bar) return;

    function update() {
      var scrollTop = win.scrollY || doc.documentElement.scrollTop;
      var docHeight = doc.documentElement.scrollHeight - win.innerHeight;
      var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = progress + '%';
    }

    win.addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ── 2. SCROLL: Parallax ── */
  function initParallax() {
    var els = doc.querySelectorAll('.nc-parallax');
    if (!els.length) return;

    win.addEventListener('scroll', function() {
      var scrollY = win.scrollY;
      for (var i = 0; i < els.length; i++) {
        var el = els[i];
        var speed = parseFloat(el.getAttribute('data-speed')) || 0.05;
        var rect = el.getBoundingClientRect();
        if (rect.top < win.innerHeight && rect.bottom > 0) {
          var offset = (rect.top - win.innerHeight / 2) * speed;
          el.style.transform = 'translateY(' + offset + 'px)';
        }
      }
    }, { passive: true });
  }

  /* ── 4. CTA: Ripple effect ── */
  function initRippleEffect() {
    doc.addEventListener('click', function(e) {
      var btn = e.target.closest('.nc-btn');
      if (!btn) return;

      var rect = btn.getBoundingClientRect();
      var ripple = doc.createElement('span');
      ripple.className = 'nc-ripple';
      var size = Math.max(rect.width, rect.height);
      ripple.style.width = ripple.style.height = size + 'px';
      ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
      ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
      btn.appendChild(ripple);
      setTimeout(function() { ripple.remove(); }, 600);
    });
  }

  /* ── 5. AUDIO: Waveform toggle ── */
  function initWaveformToggle() {
    var waveforms = doc.querySelectorAll('.nc-waveform');
    for (var i = 0; i < waveforms.length; i++) {
      var wf = waveforms[i];
      var bars = wf.querySelectorAll('.nc-waveform-bar');
      var parent = wf.closest('[data-playable]');
      if (parent) {
        (function(wfBars) {
          parent.addEventListener('click', function() {
            var isPlaying = wf.classList.toggle('is-playing');
            for (var j = 0; j < wfBars.length; j++) {
              wfBars[j].style.animationPlayState = isPlaying ? 'running' : 'paused';
            }
          });
        })(bars);
      }
    }
  }

  /* ── 5. AUDIO: Vinyl toggle ── */
  function initVinylToggle() {
    var vinyls = doc.querySelectorAll('.nc-vinyl, .nc-spinning-disc');
    for (var i = 0; i < vinyls.length; i++) {
      (function(vinyl) {
        var parent = vinyl.closest('[data-playable]');
        if (parent) {
          parent.addEventListener('click', function() {
            vinyl.classList.toggle('is-paused');
          });
        }
      })(vinyls[i]);
    }
  }

  /* ── Init ── */
  function init() {
    var heroBg = doc.querySelector('.nc-hero-bg');
    if (heroBg) initParticles(heroBg);
    initScrollAnimations();
    initScrollProgress();
    initParallax();
    initRippleEffect();
    initWaveformToggle();
    initVinylToggle();
  }

  if (doc.readyState === 'loading') {
    doc.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  if (typeof Streamlit !== 'undefined') {
    Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, function() {
      setTimeout(init, 100);
    });
  }
})();
"""


def inject_animation_css() -> str:
    return "<style>" + ANIMATION_CSS + "</style>"


def inject_animation_js() -> str:
    return "<script>" + ANIMATION_JS + "</script>"


def inject_scroll_progress_bar() -> str:
    return '<div id="nc-scroll-progress" class="nc-scroll-progress"></div>'


def inject_all() -> str:
    parts = [
        inject_scroll_progress_bar(),
        inject_animation_css(),
        inject_animation_js(),
    ]
    return "\\n".join(parts)


def hero_section_html(
    title: str = "Trasforma le tue sbobine in podcast",
    subtitle: str = "Con due host AI — come NotebookLM, ma gratis e in italiano.",
    cta_text: str = "🎙️ Inizia gratis",
    cta_url: str = "#",
) -> str:
    return '''
    <div class="nc-hero">
      <div class="nc-hero-bg">
        <div class="nc-hero-wave nc-hero-wave--1"></div>
        <div class="nc-hero-wave nc-hero-wave--2"></div>
        <div class="nc-hero-wave nc-hero-wave--3"></div>
      </div>
      <div style="position:relative; z-index:1; text-align:center; padding: 2rem;">
        <div style="position:relative; display:inline-block; margin-bottom:1rem;">
          <div class="nc-hero-glow" style="top:50%; left:50%; transform:translate(-50%,-50%);"></div>
          <div class="nc-hero-mic">🎙️</div>
        </div>
        <h1 class="nc-hero-title" style="
          font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 900;
          background: linear-gradient(135deg, #1e3a5f, #2563eb, #0ea5e9);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text; margin: 0.5rem 0 0.6rem; letter-spacing: -1.5px;
          line-height: 1.15;
        ">''' + title + '''</h1>
        <p class="nc-hero-subtitle" style="
          font-size: clamp(1rem, 2vw, 1.2rem); color: #6b7280;
          max-width: 520px; margin: 0 auto 2rem; line-height: 1.6;
        ">''' + subtitle + '''</p>
        <div class="nc-hero-cta">
          <a href="''' + cta_url + '''" class="nc-btn nc-btn--primary" style="text-decoration:none;">
            ''' + cta_text + '''
          </a>
        </div>
      </div>
    </div>
    '''


def feature_card_html(icon: str, title: str, description: str, delay: int = 1) -> str:
    return '''
    <div class="nc-card nc-scroll-fade" data-delay="''' + str(delay) + '''">
      <div class="nc-card-icon">''' + icon + '''</div>
      <h3 style="font-size:1.1rem; font-weight:700; color:#1e293b; margin:0.75rem 0 0.4rem;">''' + title + '''</h3>
      <p style="font-size:0.88rem; color:#6b7280; margin:0; line-height:1.5;">''' + description + '''</p>
    </div>
    '''


def pricing_card_html(
    name: str,
    price: str,
    description: str,
    features: list,
    is_featured: bool = False,
    cta_text: str = "Scegli piano",
    cta_url: str = "#",
) -> str:
    featured_class = "nc-pricing-card--featured" if is_featured else ""
    badge = '<div class="nc-pricing-badge">✦ Più popolare</div>' if is_featured else ""
    feats = ""
    for f in features:
        feats += '<li style="font-size:0.85rem; color:#4b5563; padding:0.3rem 0; list-style:none;">✓ ' + f + '</li>'
    return '''
    <div class="nc-pricing-card ''' + featured_class + '''" style="position:relative;">
      ''' + badge + '''
      <h3 style="font-size:1.2rem; font-weight:800; color:#1f2937; margin:0 0 0.25rem;">''' + name + '''</h3>
      <div style="font-size:2.5rem; font-weight:900; color:#1e3a5f; margin:0.5rem 0;">''' + price + '''</div>
      <p style="font-size:0.85rem; color:#6b7280; margin:0 0 1rem;">''' + description + '''</p>
      <ul style="padding:0; margin:0 0 1.5rem;">''' + feats + '''</ul>
      <a href="''' + cta_url + '''" class="nc-btn nc-btn--primary" style="text-decoration:none; font-size:0.9rem; padding:0.6rem 1.5rem;">
        ''' + cta_text + '''
      </a>
    </div>
    '''


def waveform_html(bar_count: int = 15) -> str:
    bars = ""
    for _ in range(bar_count):
        bars += '<div class="nc-waveform-bar"></div>'
    return '<div class="nc-waveform">' + bars + '</div>'


def vinyl_disc_html() -> str:
    return '''
    <div class="nc-vinyl">
      <div class="nc-vinyl-center"></div>
    </div>
    '''
