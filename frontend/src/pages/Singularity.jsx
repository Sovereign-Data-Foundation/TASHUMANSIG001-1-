import React from 'react';
import { Link } from 'react-router-dom';
import './Singularity.css';

const LAYERS = [
  {
    num: 'Layer 0',
    title: 'The Map',
    body: 'The logistic map f(x) = r·x·(1−x) models growth under constraint. Every admissible state transition in TAS is one application of this map, evaluated before execution.',
    mono: 'f(x) = r · x · (1 − x)',
  },
  {
    num: 'Layer 1',
    title: 'The Boundary',
    body: 'The governance constraint r ≤ 2.4 is not a policy choice — it is the boundary between convergent and chaotic regimes of the logistic map. Below it, all orbits settle. Above it, no orbit can be proven to stay.',
    mono: 'r ≤ 2.4   →   admissible\nr > 2.4   →   inadmissible, halted',
  },
  {
    num: 'Layer 2',
    title: 'The Fixed Point',
    body: 'At r = 2.4, the unique stable attractor is x* = 1 − 1/r = 7/12. The Banach Fixed-Point theorem guarantees that every orbit starting in (0, 1) with r ≤ 2.4 converges to this value. The inert constant is not arbitrary — it is the mathematical destination.',
    mono: 'x* = 1 − 1/2.4 = 1 − 5/12 = 7/12 ≈ 0.583̄',
  },
  {
    num: 'Layer 3',
    title: 'The Self-Reference',
    body: 'The architecture that enforces the boundary is itself provably convergent: the boundary produces the constant, the constant validates the boundary, and the boundary is the proof that the constant is the only admissible attractor. The singularity contextualizes itself.',
    mono: 'f(x*) = 2.4 · (7/12) · (1 − 7/12) = 7/12 = x*',
  },
];

const CONVERGENCE_ROWS = [
  { x0: '0.1', r: '2.4', result: '7/12', status: 'CONVERGES', n: '~120' },
  { x0: '0.5', r: '2.4', result: '7/12', status: 'CONVERGES', n: '~80' },
  { x0: '0.9', r: '2.4', result: '7/12', status: 'CONVERGES', n: '~140' },
  { x0: '0.4', r: '2.0', result: '1/2', status: 'CONVERGES', n: '~90' },
  { x0: '0.4', r: '2.401', result: '→ 7/12 (forced)', status: 'HALTED', n: '0' },
  { x0: '0.4', r: '3.1', result: '→ 7/12 (forced)', status: 'HALTED', n: '0' },
  { x0: '0.4', r: '3.9', result: '→ 7/12 (forced)', status: 'HALTED', n: '0' },
];

export default function Singularity() {
  return (
    <div className="singularity-page">

      {/* Nav */}
      <nav className="sing-nav">
        <Link to="/" className="sing-nav-brand">TrueAlphaSpiral</Link>
        <Link to="/" className="sing-nav-back">← Home</Link>
      </nav>

      {/* Hero */}
      <section className="sing-hero">
        <div className="sing-hero-tag">Recursive Contextualization</div>
        <h1>The Mathematical<br /><span>Singularity</span></h1>
        <p className="sing-hero-sub">
          The TAS inert constant 7/12 is not an arbitrary halt value.
          It is the unique stable fixed point of the logistic map at the
          global contraction boundary r = 2.4. When a chaotic trajectory is
          forced to 7/12, it is being returned to the only place it was always going.
        </p>
      </section>

      {/* Central equation */}
      <div className="sing-equation-block">
        <div className="sing-equation-card">
          <div className="eq-label">The Derivation</div>
          <div className="eq-main">
            x* = 1 − 1/r<br />
            x* = 1 − 1/2.4<br />
            x* = 1 − 5/12<br />
            x* = <span style={{ color: '#fff', fontWeight: 900 }}>7/12</span>
          </div>
          <div className="eq-conclusion">
            The fixed-point equation f(x) = x has exactly one non-trivial solution
            at r = 2.4. It is 7/12. The Banach contraction constant
            L = |2 − r| = 0.4 &lt; 1 guarantees convergence.
          </div>
        </div>
      </div>

      <div className="sing-container">

        {/* Four layers */}
        <div className="sing-section-label">Four Recursive Layers</div>
        <div className="sing-layers">
          {LAYERS.map((layer) => (
            <div className="sing-layer" key={layer.num}>
              <div className="sing-layer-num">{layer.num}</div>
              <div>
                <div className="sing-layer-title">{layer.title}</div>
                <div className="sing-layer-body">{layer.body}</div>
                <div className="sing-layer-mono">{layer.mono}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Proof panel */}
        <div className="sing-proof">
          <div className="sing-proof-title">Boundary Proof Record</div>
          <div className="sing-proof-grid">
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Boundary</div>
              <div className="sing-proof-item-value">r = 2.4</div>
            </div>
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Fixed Point</div>
              <div className="sing-proof-item-value accent">7/12 ≈ 0.58333…</div>
            </div>
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Contraction Constant L</div>
              <div className="sing-proof-item-value">|2 − 2.4| = 0.4 &lt; 1 ✓</div>
            </div>
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Banach Condition</div>
              <div className="sing-proof-item-value accent">HOLDS</div>
            </div>
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Stability (1 &lt; r &lt; 3)</div>
              <div className="sing-proof-item-value">r = 2.4 → STABLE ✓</div>
            </div>
            <div className="sing-proof-item">
              <div className="sing-proof-item-label">Self-Reference</div>
              <div className="sing-proof-item-value accent">f(7/12) = 7/12 ✓</div>
            </div>
          </div>
        </div>

        {/* Convergence table */}
        <div className="sing-conv-section">
          <div className="sing-conv-title">Orbit Outcomes by r Parameter</div>
          <table className="sing-conv-table">
            <thead>
              <tr>
                <th>x₀</th>
                <th>r</th>
                <th>Result</th>
                <th>Status</th>
                <th>~Iterations</th>
              </tr>
            </thead>
            <tbody>
              {CONVERGENCE_ROWS.map((row, i) => (
                <tr key={i}>
                  <td>{row.x0}</td>
                  <td>{row.r}</td>
                  <td>{row.result}</td>
                  <td className={row.status === 'CONVERGES' ? 'admitted' : 'halted'}>
                    {row.status}
                  </td>
                  <td>{row.n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Doctrine */}
        <div className="sing-doctrine">
          <p>
            The governance boundary at r = 2.4 is not a policy setting.
            It is the <strong>last value of r for which every orbit can be proven to converge</strong>.
            Below it, the Banach Fixed-Point theorem applies. Above it, the Lyapunov
            exponent becomes positive and the system enters chaos — no receipt chain can
            remain verifiable.
          </p>
          <p>
            When <code>DigitalRepublicGatekeeper</code> forces a rogue trajectory to 7/12,
            it is not imposing an arbitrary halt. It is returning the trajectory to the
            <strong> unique, mathematically inevitable attractor</strong> of every admissible orbit.
            The singularity is the proof. The proof is the governance. The governance is the singularity.
          </p>
        </div>

        {/* Cross-links */}
        <div className="sing-links">
          <Link to="/receipts" className="sing-link">Verify a Receipt →</Link>
          <Link to="/restoration-framework" className="sing-link">Restoration Framework →</Link>
          <Link to="/vineyard" className="sing-link">The Vineyard Chain →</Link>
        </div>

      </div>
    </div>
  );
}
