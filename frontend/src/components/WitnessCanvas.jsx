import React, { useEffect, useRef, useState, useCallback } from 'react';

const R = 4.0;
const CANVAS_PAD = 48;
const STEP_MS = 90;
const TRAIL_MAX = 55;
const LOG_MAX = 7;

function toHexFloat(v) {
  const n = Math.floor(Math.abs(v) * 0xffffffff) >>> 0;
  return '0x' + n.toString(16).padStart(8, '0').toUpperCase();
}

function synthHmac(seq, x) {
  let h = ((seq * 2654435761) ^ Math.floor(x * 1e9)) >>> 0;
  h = ((h ^ (h >>> 16)) * 0x45d9f3b) >>> 0;
  h = ((h ^ (h >>> 16)) * 0x45d9f3b) >>> 0;
  return (h >>> 0).toString(16).padStart(8, '0').toUpperCase().slice(0, 8) + '…';
}

function kappa(x) {
  return Math.abs(R * (1 - 2 * x));
}

export default function WitnessCanvas() {
  const canvasRef = useRef(null);
  const engineRef = useRef({ x: 0.23, seq: 0, trail: [] });
  const rafRef = useRef(null);
  const timerRef = useRef(null);
  const [receipts, setReceipts] = useState([]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = canvas.width;
    const H = canvas.height;
    const pad = CANVAS_PAD;
    const pw = W - pad * 2;
    const ph = H - pad * 2;
    const { trail } = engineRef.current;

    const sc = (cx, cy) => ({ sx: pad + cx * pw, sy: pad + (1 - cy) * ph });

    ctx.clearRect(0, 0, W, H);

    ctx.lineWidth = 0.5;
    ctx.strokeStyle = 'rgba(255,255,255,0.04)';
    for (let i = 0; i <= 4; i++) {
      const t = i / 4;
      ctx.beginPath();
      ctx.moveTo(pad + t * pw, pad);
      ctx.lineTo(pad + t * pw, pad + ph);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(pad, pad + (1 - t) * ph);
      ctx.lineTo(pad + pw, pad + (1 - t) * ph);
      ctx.stroke();
    }

    ctx.beginPath();
    ctx.strokeStyle = 'rgba(255,255,255,0.07)';
    ctx.lineWidth = 0.8;
    const { sx: d0x, sy: d0y } = sc(0, 0);
    const { sx: d1x, sy: d1y } = sc(1, 1);
    ctx.moveTo(d0x, d0y);
    ctx.lineTo(d1x, d1y);
    ctx.stroke();

    ctx.beginPath();
    ctx.strokeStyle = 'rgba(0,240,255,0.22)';
    ctx.lineWidth = 1.5;
    for (let i = 0; i <= 240; i++) {
      const t = i / 240;
      const y = R * t * (1 - t);
      const { sx, sy } = sc(t, y);
      i === 0 ? ctx.moveTo(sx, sy) : ctx.lineTo(sx, sy);
    }
    ctx.stroke();

    for (let i = 1; i < trail.length; i++) {
      const age = i / trail.length;
      const alpha = Math.pow(age, 1.6) * 0.75;
      ctx.beginPath();
      ctx.strokeStyle = `rgba(0,240,255,${alpha.toFixed(3)})`;
      ctx.lineWidth = 0.8 + age * 1.2;
      const a = sc(trail[i - 1].x, trail[i - 1].y);
      const b = sc(trail[i].x, trail[i].y);
      ctx.moveTo(a.sx, a.sy);
      ctx.lineTo(b.sx, b.sy);
      ctx.stroke();
    }

    if (trail.length > 0) {
      const pt = trail[trail.length - 1];
      const { sx, sy } = sc(pt.x, pt.y);

      const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, 18);
      glow.addColorStop(0, 'rgba(0,240,255,0.25)');
      glow.addColorStop(1, 'rgba(0,240,255,0)');
      ctx.beginPath();
      ctx.arc(sx, sy, 18, 0, Math.PI * 2);
      ctx.fillStyle = glow;
      ctx.fill();

      ctx.beginPath();
      ctx.arc(sx, sy, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = '#00f0ff';
      ctx.fill();

      ctx.beginPath();
      ctx.arc(sx, sy, 1.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();
    }
  }, []);

  const tick = useCallback(() => {
    const e = engineRef.current;
    const xn = e.x;
    const xn1 = R * xn * (1 - xn);
    const k = kappa(xn);

    e.trail.push({ x: xn1, y: xn1 });
    if (e.trail.length > TRAIL_MAX) e.trail.shift();

    const receipt = {
      seq: e.seq,
      xn: toHexFloat(xn),
      hmac: synthHmac(e.seq, xn),
      kappa: k.toFixed(4),
      pass: k < 2,
    };

    setReceipts(prev => [receipt, ...prev].slice(0, LOG_MAX));

    e.x = xn1;
    e.seq += 1;

    if (e.seq % 75 === 0) {
      e.x = 0.08 + Math.random() * 0.84;
      e.trail = [];
    }

    rafRef.current = requestAnimationFrame(draw);
    timerRef.current = setTimeout(tick, STEP_MS);
  }, [draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const resize = () => {
      const p = canvas.parentElement;
      if (!p) return;
      canvas.width = p.offsetWidth;
      canvas.height = p.offsetHeight;
      draw();
    };

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas.parentElement);

    timerRef.current = setTimeout(tick, 300);

    return () => {
      clearTimeout(timerRef.current);
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
    };
  }, [tick, draw]);

  return (
    <div className="witness-surface">
      <div className="witness-canvas-wrap">
        <canvas ref={canvasRef} className="witness-canvas" />
        <span className="mono witness-label-axis witness-label-y">f(x)</span>
        <span className="mono witness-label-axis witness-label-x">x</span>
        <span className="mono witness-label-eq">
          x<sub>n+1</sub> = 4x<sub>n</sub>(1−x<sub>n</sub>)
        </span>
      </div>

      <div className="witness-log">
        <div className="witness-log-header mono">
          <span className="text-accent" style={{ letterSpacing: '2px', fontSize: '0.68rem', textTransform: 'uppercase' }}>
            Witness Receipt Log
          </span>
          <span className="text-dim" style={{ fontSize: '0.68rem' }}>Live · r = 4.0</span>
        </div>
        <div className="wr-cols mono text-dim">
          <span>SEQ</span>
          <span>x_n</span>
          <span>HMAC</span>
          <span>κ</span>
          <span>STATUS</span>
        </div>
        <div className="wr-body">
          {receipts.map((r, i) => (
            <div
              className="wr-row"
              key={r.seq}
              style={{ opacity: Math.max(0.15, 1 - i * 0.13) }}
            >
              <span className="text-dim">{String(r.seq).padStart(4, '0')}</span>
              <span className="text-accent">{r.xn}</span>
              <span className="text-dim">{r.hmac}</span>
              <span style={{ color: r.pass ? 'var(--accent-led)' : '#ff4455' }}>{r.kappa}</span>
              <span style={{ color: r.pass ? 'var(--accent-led)' : '#ff4455', fontWeight: 600 }}>
                {r.pass ? 'PASS' : 'HALT'}
              </span>
            </div>
          ))}
          {receipts.length === 0 && (
            <div className="mono text-dim" style={{ fontSize: '0.78rem', padding: '20px 0' }}>
              Initializing…
            </div>
          )}
        </div>
        <div className="witness-log-footer mono">
          Sovereign Parabola · Banach κ &lt; 1 · Wake Chain Active
        </div>
      </div>
    </div>
  );
}
