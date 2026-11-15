// The Field: the library's letters (Greek, Hebrew, Latin) drifting on a slow wind behind the
// home page, warmed by the pointer, rung in blue where you click empty space. One per page.
// Copied from the Gospel Scholar Archives' home (homelab gsa-dash/static/home/field.js,
// DESIGN.md Appendix A there); only the colours it reads are Lectern's.
//
//   startField({ canvas, calm: () => [cx, cy, rx, ry], ignore: 'a,button' })
//   setGlyphs(archive: boolean), setStill(on: boolean)
//
// Written for GSA after studying the Claude Code "New session" texture
// (DESIGN.md Appendix A). The ring and wake follow the shapes published
// by Claude Code Background Lab (github.com/a459795/-1, MIT); none of
// Anthropic's code is in it.

// One instanced quad per monospace cell. The vertex shader decides each
// cell's glyph and brightness; the fragment shader only samples the atlas.
const ARCHIVE = 'ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩαβγδεζηθικλμνξοπρστυφχψω' + 'אבגדהוזחטיכלמנסעפצקרשת' +
  'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789' + '§¶†‡·:;';
const LATIN = 'abcdefghijklmnopqrstuvxyzABCDEFGHIJKLMNOPQRSTUVXYZ0123456789';
const CELL = { w: 7, h: 14, font: 10 };          // CSS px
const SET = {
  wind: { speed: 34, gust: [460, 170], warp: 90 },  // px/s, px
  threshold: [.50, .68],                            // smoothstep on the cloud field
  ambient: .05,                                     // faint floor, so the grid is felt everywhere
  ink: .30,                                         // alpha ceiling of a fully lit cell
  calmDepth: .12,                                   // brightness left inside the calm zone
  change: .9,                                       // glyph swaps per second, per cell (mean)
  idleStopS: 120,                                   // stop drawing after this long untouched
  fps: 30,
};

const VERT = `#version 300 es
precision highp float; precision highp int;
uniform vec2 uView, uCell, uOrigin; uniform float uDpr;
uniform int uCols, uGlyphs, uAtlasCols, uAtlasRows;
uniform float uTime, uWall, uSeed, uReveal, uAmbient, uChange;
uniform vec4 uWind;        // dir.xy, speed, warp
uniform vec2 uGust, uThresh;
uniform vec4 uCalm;        // center.xy, radii.xy (CSS px)
uniform float uCalmDepth;
uniform int uWakeN, uTapN;
uniform vec4 uWake[16];    // x, y, born, strength
uniform vec4 uTap[6];      // x, y, born, strength
out vec2 vUV; out float vLum, vGlow;

float h21(vec2 p) { return fract(sin(dot(p, vec2(41.3, 289.1)) + uSeed * 0.031) * 45758.5453); }
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p); f = f * f * (3. - 2. * f);
  return mix(mix(h21(i), h21(i + vec2(1, 0)), f.x), mix(h21(i + vec2(0, 1)), h21(i + vec2(1)), f.x), f.y);
}
float fbm(vec2 p, float t) {
  float s = 0., a = .5, n = 0.;
  for (int k = 0; k < 4; k++) {
    s += a * vnoise(p + t * vec2(.017 + float(k) * .006, -.011)); n += a;
    p = mat2(1.6, -1.2, 1.2, 1.6) * p + 5.3; a *= .52;
  }
  return s / n;
}
void main() {
  int row = gl_InstanceID / uCols, col = gl_InstanceID - row * uCols;
  vec2 cell = vec2(col, row);
  vec2 dev = uOrigin + (cell + .5) * uCell;     // device px
  vec2 p = dev / uDpr;                          // CSS px
  float t = uTime;

  // wind: move into the wind's frame, warp it with a slow low-frequency field
  vec2 dir = uWind.xy, across = vec2(-dir.y, dir.x);
  vec2 warp = vec2(vnoise(p / 420. + t * .011), vnoise(p / 420. + vec2(9.1, -t * .008))) - .5;
  vec2 q = vec2(dot(p + warp * uWind.w, dir) - t * uWind.z, dot(p + warp * uWind.w, across));
  float cloud = fbm(q / uGust, t * .6);
  float thread = 1. - smoothstep(0., .22, abs(vnoise(q / vec2(160., 26.) + t * .006) - .5));
  cloud += .07 * (thread - .5);
  float lit = pow(smoothstep(uThresh.x, uThresh.y, cloud), 2.);

  // the pointer's wake: warmth that blooms and cools where it passed
  float warm = 0.;
  for (int j = 0; j < 16; j++) {
    if (j >= uWakeN) break;
    float a = max(0., uWall - uWake[j].z), r = 56. + 44. * a;
    vec2 d = p - uWake[j].xy;
    warm += uWake[j].w * (1. - exp(-a / .06)) * exp(-a / .7) * exp(-dot(d, d) / (r * r));
  }
  warm = 1. - exp(-1.4 * warm);
  lit = mix(lit, max(lit, .75 * fbm(q / vec2(34., 22.), t)), warm);

  // a click: one wave racing out, lighting cells as it passes. Its front is
  // not a circle: it bends with a slow noise around its rim (sampled on the
  // unit direction, so there is no seam), bulges where the wind's own cloud
  // is thick, breathes in width, and drifts downwind as it goes.
  float glow = 0.;
  for (int j = 0; j < 6; j++) {
    if (j >= uTapN) break;
    float a = max(0., uWall - uTap[j].z);
    float grow = smoothstep(0., .5, a);
    vec2 o = uTap[j].xy + dir * uWind.z * a * .6;
    vec2 d = p - o;
    float len = length(d);
    vec2 u = d / max(len, 1.);
    float bend = (vnoise(u * 1.7 + vec2(a * .9, float(j) * 7.13)) - .5) * 2.
               + (vnoise(u * 4.3 + vec2(-a * 1.6, 3.7 + float(j))) - .5);
    float R = 720. * (1. - exp(-a / 1.15));
    R *= 1. + .11 * bend * grow;
    R += 90. * (cloud - .5) * grow;
    float w = (64. + 70. * a) * (.7 + .6 * vnoise(u * 2.9 + vec2(a, 11.3)));
    float ring = exp(-4. * pow(len - R, 2.) / (w * w));
    glow += ring * (1. - exp(-a / .04)) * exp(-a / 1.05) * uTap[j].w;
  }
  // quantize the ring to five steps: it reads as letters switching on, not as a blur
  float stepped = floor(clamp(glow, 0., 1.) * 5. + h21(cell + 3.3) * .9) / 5.;

  // the calm zone behind the headline and the field
  vec2 c = (p - uCalm.xy) / uCalm.zw;
  float calm = mix(uCalmDepth, 1., 1. - exp(-1.1 * dot(c, c)));

  vLum = (max(lit, uAmbient) + stepped * .6) * calm * max(uReveal, warm);
  vGlow = stepped * mix(.55, 1., calm);

  int k = int(floor(t * uChange * (.4 + 1.2 * h21(cell + 7.)) + h21(cell) * 60. + stepped * 8.));
  int g = (int(h21(cell + 77.) * 997.) + k) % uGlyphs;
  vec2 corner = vec2(gl_VertexID == 1 || gl_VertexID == 2 || gl_VertexID == 4 ? 1. : 0., gl_VertexID >= 2 && gl_VertexID != 3 ? 1. : 0.);
  vUV = (vec2(g % uAtlasCols, g / uAtlasCols) + corner) / vec2(uAtlasCols, uAtlasRows);
  vec2 at = uOrigin + (cell + corner) * uCell;
  gl_Position = vec4(at / uView * vec2(2., -2.) + vec2(-1., 1.), 0., 1.);
}`;
const FRAG = `#version 300 es
precision highp float;
uniform sampler2D uAtlas; uniform vec3 uInk, uAccent; uniform float uInkA;
in vec2 vUV; in float vLum, vGlow; out vec4 o;
void main() {
  float cov = texture(uAtlas, vUV).a;
  if (cov < .004) discard;
  float a = cov * clamp(vLum * uInkA + vGlow * .8, 0., 1.);
  vec3 col = mix(uInk, uAccent, smoothstep(.15, .45, vGlow));
  o = vec4(col * a, a);
}`;

let canvas, gl, calm, ignoreSel;
const reduce = matchMedia('(prefers-reduced-motion: reduce)');
let still = reduce.matches, held = false;
const state = { taps: [], wakes: [], last: null, lastInput: performance.now(), running: false, frame: 0, t0: performance.now(), clock: 0, prev: performance.now() };
let prog, U = {}, atlas, grid, glyphs = ARCHIVE;

function compile(type, src) {
  const s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
  return s;
}
async function buildAtlas() {
  await Promise.all(['10px "Geist Mono Variable"', '10px "Field Greek"', '10px "Field Hebrew"'].map(f => document.fonts.load(f, glyphs)));
  const chars = [...glyphs], dpr = Math.min(devicePixelRatio || 1, 2);
  const cw = Math.round(CELL.w * dpr), ch = Math.round(CELL.h * dpr), cols = 16, rows = Math.ceil(chars.length / cols);
  const c = new OffscreenCanvas(cw * cols, ch * rows), x = c.getContext('2d');
  x.font = `300 ${Math.round(CELL.font * dpr)}px "Geist Mono Variable", "Field Greek", "Field Hebrew", monospace`;
  x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillStyle = '#fff';   // the atlas's coverage mask, not a colour anyone sees
  chars.forEach((s, i) => {   // each glyph clipped to its own cell, so no neighbour bleeds in
    const cx = (i % cols) * cw, cy = Math.floor(i / cols) * ch;
    x.save(); x.beginPath(); x.rect(cx + 1, cy + 1, cw - 2, ch - 2); x.clip();
    x.fillText(s, cx + cw / 2, cy + ch * .55, cw - 2); x.restore();
  });
  atlas = atlas || gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, atlas);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, c);
  // cells and atlas share one device-pixel size, so NEAREST samples each glyph exactly
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return { n: chars.length, cols, rows };
}
function layout() {
  const dpr = Math.min(devicePixelRatio || 1, 2);
  canvas.width = Math.round(innerWidth * dpr); canvas.height = Math.round(innerHeight * dpr);
  gl.viewport(0, 0, canvas.width, canvas.height);
  const cw = Math.round(CELL.w * dpr), ch = Math.round(CELL.h * dpr);
  const cols = Math.ceil(canvas.width / cw), rows = Math.ceil(canvas.height / ch);
  grid = { dpr, cw, ch, cols, rows, ox: Math.round((canvas.width - cols * cw) / 2), oy: Math.round((canvas.height - rows * ch) / 2) };
}
function calmZone() { return calm(); }
async function init() {
  if (!gl) return;
  prog = gl.createProgram();
  gl.attachShader(prog, compile(gl.VERTEX_SHADER, VERT)); gl.attachShader(prog, compile(gl.FRAGMENT_SHADER, FRAG));
  gl.linkProgram(prog); gl.useProgram(prog);
  for (let i = 0, n = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS); i < n; i++) {
    const name = gl.getActiveUniform(prog, i).name.replace(/\[0\]$/, '');
    U[name] = gl.getUniformLocation(prog, name);
  }
  gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);
  layout(); atlas_ = await buildAtlas();
  const seed = Math.random() * 1000, ang = (Math.random() < .5 ? 1 : -1) * (.25 + Math.random() * .35);
  state.seed = seed; state.dir = [Math.cos(ang), Math.sin(ang)];
  addEventListener('resize', () => { layout(); draw(); });
  canvas.classList.add('in');
  start();
}
let atlas_;
function theme() {
  const s = getComputedStyle(document.documentElement), hex = v => { const m = s.getPropertyValue(v).trim().match(/\w\w/g); return m.map(x => parseInt(x, 16) / 255); };
  return { ink: hex('--ink'), accent: hex('--field-ring'), inkA: SET.ink };
}
function draw() {
  if (!prog || !grid || !atlas_) return;   // a resize can land before the atlas exists
  const now = performance.now(), wall = (now - state.t0) / 1000;
  state.taps = state.taps.filter(t => wall - t[2] < 5);
  state.wakes = state.wakes.filter(w => wall - w[2] < 3);
  const th = theme(), z = calmZone();
  gl.uniform2f(U.uView, canvas.width, canvas.height); gl.uniform2f(U.uCell, grid.cw, grid.ch);
  gl.uniform2f(U.uOrigin, grid.ox, grid.oy); gl.uniform1f(U.uDpr, grid.dpr);
  gl.uniform1i(U.uCols, grid.cols); gl.uniform1i(U.uGlyphs, atlas_.n); gl.uniform1i(U.uAtlasCols, atlas_.cols); gl.uniform1i(U.uAtlasRows, atlas_.rows);
  gl.uniform1f(U.uTime, state.clock); gl.uniform1f(U.uWall, wall); gl.uniform1f(U.uSeed, state.seed);
  gl.uniform1f(U.uReveal, Math.min(1, state.clock / 4)); gl.uniform1f(U.uAmbient, SET.ambient); gl.uniform1f(U.uChange, SET.change);
  gl.uniform4f(U.uWind, state.dir[0], state.dir[1], SET.wind.speed, SET.wind.warp);
  gl.uniform2f(U.uGust, SET.wind.gust[0], SET.wind.gust[1]); gl.uniform2f(U.uThresh, SET.threshold[0], SET.threshold[1]);
  gl.uniform4f(U.uCalm, ...z); gl.uniform1f(U.uCalmDepth, SET.calmDepth);
  gl.uniform1i(U.uWakeN, state.wakes.length); gl.uniform1i(U.uTapN, state.taps.length);
  if (state.wakes.length) gl.uniform4fv(U.uWake, state.wakes.flat());
  if (state.taps.length) gl.uniform4fv(U.uTap, state.taps.flat());
  gl.uniform3f(U.uInk, ...th.ink); gl.uniform3f(U.uAccent, ...th.accent); gl.uniform1f(U.uInkA, th.inkA);
  gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, atlas); gl.uniform1i(U.uAtlas, 0);
  gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
  gl.drawArraysInstanced(gl.TRIANGLES, 0, 6, grid.cols * grid.rows);
}
function tick(now) {
  if (!state.running) return;
  state.frame = requestAnimationFrame(tick);
  const busy = state.taps.length > 0;
  if (now - state.prev < (busy ? 16 : 1000 / SET.fps) - 2) return;   // 30 fps at rest, 60 while a ring runs
  state.clock += Math.min(.1, (now - state.prev) / 1000); state.prev = now;
  draw();
  if (now - state.lastInput > SET.idleStopS * 1000 && !busy) stop();  // settle: a still frame until touched
}
function start() {
  if (held) return;                     // home isn't showing
  if (still) { state.clock = 6; draw(); return; }
  if (state.running || document.hidden) return;
  state.running = true; state.prev = performance.now(); state.frame = requestAnimationFrame(tick);
}
function stop() { state.running = false; cancelAnimationFrame(state.frame); }
function wake() { state.lastInput = performance.now(); start(); }

function listen() {
// input: a wake follows the pointer; a click on empty space rings
const wallClock = () => (performance.now() - state.t0) / 1000;
addEventListener('pointermove', e => {
  if (still || e.pointerType !== 'mouse') return;
  wake();
  const p = [e.clientX, e.clientY], l = state.last;
  if (l && Math.hypot(p[0] - l[0], p[1] - l[1]) < 22) return;
  const speed = l ? Math.hypot(p[0] - l[0], p[1] - l[1]) / Math.max(.016, wallClock() - l[2]) : 0;
  state.last = [...p, wallClock()];
  state.wakes.push([p[0], p[1], wallClock(), Math.min(1, .25 + speed / 900)]);
  if (state.wakes.length > 16) state.wakes.shift();
}, { passive: true });
addEventListener('pointerdown', e => {
  if (still || e.button) return;
  if (e.target.closest(ignoreSel)) return;   // only empty space rings
  wake();
  state.taps.push([e.clientX, e.clientY, wallClock(), 1]);
  if (state.taps.length > 6) state.taps.shift();
});
document.addEventListener('visibilitychange', () => document.hidden ? stop() : wake());
addEventListener('blur', stop); addEventListener('focus', wake);
reduce.addEventListener('change', () => { still = reduce.matches; still ? stop() : wake(); });
}

export function startField(opts) {
  canvas = opts.canvas;
  gl = canvas.getContext('webgl2', { alpha: true, premultipliedAlpha: true, antialias: false });
  calm = opts.calm;
  ignoreSel = opts.ignore || 'a,button,input,textarea,select,img,[data-no-ring]';
  listen();
  setTimeout(init, opts.delay ?? 600);   // let the page settle; the field arrives after the content
}
export async function setGlyphs(archive) { glyphs = archive ? ARCHIVE : LATIN; atlas_ = await buildAtlas(); draw(); }
/** hold the Field while home is out of sight; let it go when it's back */
export function holdField(on) { held = on; if (on) stop(); else if (canvas) wake(); }
export function setStill(on) { still = on; if (on) { stop(); state.clock = 6; draw(); } else wake(); }
