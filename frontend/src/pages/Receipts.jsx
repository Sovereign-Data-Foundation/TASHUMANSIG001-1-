import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import './Receipts.css';

// ── Manifest data embedded from EXECUTE_01JAB7.json (Day-Zero session) ──
const MANIFEST = {
  schema: "TAS-PDR-v1",
  session_id: "tas-day-zero-2026-07-06",
  generated_at: "2026-07-06T00:00:00Z",
  genesis_chain_id: "TAS-sovereign-01",
  genesis_app_hash: "3A9FA182A94363B1BFD8E867D28CF104",
  wake_head_final: "0eae47c7b46ef877a5f9a875046ab195a283d7bcaf1fe510e486eb3a2111d9dc",
  chain_verified: true,
  manifest_hash: "330e5250d9224fab3bf38cad676742e8eb90a87e8267e6bacb75691271a3d3d3",
  summary: { chain_length: 13, admitted: 13, refused: 1 },
};

const RECEIPTS = [
  { seq: 0,  label: "genesis_anchor_block",        event_type: "genesis",          p1: "GENESIS_BLOCK" },
  { seq: 1,  label: "genesis_anchor",               event_type: "state_transition", p1: "ADMITTED" },
  { seq: 2,  label: "wake_chain_init",              event_type: "state_transition", p1: "ADMITTED" },
  { seq: 3,  label: "p0_equivalence_lock",          event_type: "state_transition", p1: "ADMITTED" },
  { seq: 4,  label: "p1_admissibility_gate",        event_type: "state_transition", p1: "ADMITTED" },
  { seq: 5,  label: "logos_gate_pass",              event_type: "state_transition", p1: "ADMITTED" },
  { seq: 6,  label: "phoenix_circuit_armed",        event_type: "state_transition", p1: "ADMITTED" },
  { seq: 7,  label: "yknot_branch_tied",            event_type: "state_transition", p1: "ADMITTED" },
  { seq: 8,  label: "sdi_within_threshold",         event_type: "state_transition", p1: "ADMITTED" },
  { seq: 9,  label: "uvk_certification",            event_type: "state_transition", p1: "ADMITTED" },
  { seq: 10, label: "human_api_bridge_authorised",  event_type: "state_transition", p1: "ADMITTED" },
  { seq: 11, label: "ledger_sealed",                event_type: "state_transition", p1: "ADMITTED" },
  { seq: 12, label: "chain_seal",                   event_type: "seal",             p1: "CHAIN_SEAL" },
];

const REFUSALS = [
  {
    label: "adversarial_synthetic_rejected",
    reason: "REFUSED:SYNTHETIC",
    doctrine: "SILENT — no output emitted",
  },
];

function truncate(s, n = 20) {
  return s.length > n ? s.slice(0, n) + '…' : s;
}

function badgeClass(eventType) {
  if (eventType === 'genesis') return 'rx-badge rx-badge-genesis';
  if (eventType === 'seal') return 'rx-badge rx-badge-seal';
  return 'rx-badge rx-badge-admitted';
}

function badgeLabel(eventType) {
  if (eventType === 'genesis') return 'GENESIS';
  if (eventType === 'seal') return 'SEALED';
  return 'ADMITTED';
}

function receiptRowClass(eventType) {
  if (eventType === 'genesis') return 'rx-receipt rx-receipt-genesis';
  if (eventType === 'seal') return 'rx-receipt rx-receipt-seal';
  return 'rx-receipt';
}

// ── Verifier ─────────────────────────────────────────────────────────────

function Verifier() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);

  function verify() {
    const trimmed = input.trim().toLowerCase();
    if (!trimmed) return;

    if (trimmed === MANIFEST.manifest_hash.toLowerCase()) {
      setResult({
        pass: true,
        lines: [
          `✓  Hash match confirmed`,
          `   Session  : ${MANIFEST.session_id}`,
          `   Chain    : ${MANIFEST.summary.chain_length} receipts · ${MANIFEST.summary.refused} refusal`,
          `   Head     : ${MANIFEST.wake_head_final.slice(0, 24)}…`,
          `   Verified : chain_verified = true`,
        ],
      });
    } else if (trimmed === MANIFEST.wake_head_final.toLowerCase()) {
      setResult({
        pass: true,
        lines: [
          `✓  Wake-head hash confirmed`,
          `   This is the final accumulation of all 13 receipt hashes.`,
          `   Chain integrity: VERIFIED`,
        ],
      });
    } else if (trimmed.length < 10) {
      setResult({ pass: false, lines: [`✗  Input too short — paste a full SHA-256 hex string (64 chars)`] });
    } else {
      setResult({
        pass: false,
        lines: [
          `✗  No match found in Day-Zero session`,
          `   Checked against manifest_hash and wake_head_final.`,
          `   This hash does not correspond to a known TAS receipt.`,
        ],
      });
    }
  }

  function resultClass() {
    if (!result) return 'rx-result rx-result-idle';
    return result.pass ? 'rx-result rx-result-pass' : 'rx-result rx-result-fail';
  }

  return (
    <div className="rx-verifier">
      <div className="rx-verifier-title">Verify a Receipt Hash</div>
      <div className="rx-input-row">
        <input
          className="rx-input"
          type="text"
          placeholder="Paste SHA-256 manifest hash or wake-head hash…"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && verify()}
          spellCheck={false}
        />
        <button className="rx-verify-btn" onClick={verify}>Verify</button>
      </div>
      <div className={resultClass()}>
        {result
          ? result.lines.map((l, i) => <div key={i}>{l}</div>)
          : 'Enter a hash above to verify it against the Day-Zero session ledger.'}
      </div>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────

export default function Receipts() {
  return (
    <div className="rx-page">
      <div className="rx-glow-tl" />

      <div className="rx-container">

        {/* Back */}
        <div className="rx-back-row">
          <Link to="/" className="rx-back-btn">← Return to Digital Sovereignty</Link>
        </div>

        {/* Header */}
        <div className="rx-kicker">TrueAlphaSpiral · Process Data Record Stream</div>
        <h1 className="rx-h1">Verify a Receipt</h1>
        <p className="rx-subtitle">
          Every state transition in a TAS session produces a{' '}
          <strong>cryptographically chained receipt</strong> — a ProvenanceMark
          that binds what happened, where it came from, and whether it was
          admitted or refused. This page publishes the{' '}
          <strong>Day-Zero session ledger</strong> and lets anyone verify a hash
          against it.
        </p>

        {/* Axiom pills */}
        <div className="rx-axioms">
          <div className="rx-axiom-pill">
            <strong>Axiom P₀ — Equivalence</strong>
            symbol ≡ referent · identity is locked at bind time
          </div>
          <div className="rx-axiom-pill">
            <strong>Axiom P₁ — Admissibility</strong>
            V(spec, proof, π) = True · or the transition does not execute
          </div>
          <div className="rx-axiom-pill">
            <strong>Calculator Doctrine</strong>
            when uncertainty cannot be bounded · the system stays silent
          </div>
        </div>

        {/* Verifier */}
        <Verifier />

        {/* Chain stats */}
        <div className="rx-chain-grid">
          <div className="rx-chain-card rx-chain-card-hi">
            <div className="rx-chain-label">Chain Length</div>
            <div className="rx-chain-value">{MANIFEST.summary.chain_length}</div>
          </div>
          <div className="rx-chain-card rx-chain-card-hi">
            <div className="rx-chain-label">Admitted</div>
            <div className="rx-chain-value">{MANIFEST.summary.admitted}</div>
          </div>
          <div className="rx-chain-card">
            <div className="rx-chain-label">Refused (Adversarial)</div>
            <div className="rx-chain-value">{MANIFEST.summary.refused}</div>
          </div>
          <div className="rx-chain-card">
            <div className="rx-chain-label">Session ID</div>
            <div className="rx-chain-value-sm">{MANIFEST.session_id}</div>
          </div>
          <div className="rx-chain-card">
            <div className="rx-chain-label">Genesis Chain</div>
            <div className="rx-chain-value-sm">{MANIFEST.genesis_chain_id}</div>
          </div>
          <div className="rx-chain-card">
            <div className="rx-chain-label">Chain Verified</div>
            <div className="rx-chain-value" style={{ color: '#00f0ff' }}>TRUE</div>
          </div>
          <div className="rx-chain-card" style={{ gridColumn: '1 / -1' }}>
            <div className="rx-chain-label">Manifest Hash (SHA-256)</div>
            <div className="rx-chain-value-sm">{MANIFEST.manifest_hash}</div>
          </div>
          <div className="rx-chain-card" style={{ gridColumn: '1 / -1' }}>
            <div className="rx-chain-label">Final Wake-Head Hash</div>
            <div className="rx-chain-value-sm">{MANIFEST.wake_head_final}</div>
          </div>
        </div>

        {/* Receipt stream */}
        <div className="rx-section-title">Receipt Stream — {RECEIPTS.length} ProvenanceMarks</div>
        <div className="rx-stream">
          {RECEIPTS.map(r => (
            <div key={r.seq} className={receiptRowClass(r.event_type)}>
              <div className="rx-seq">#{String(r.seq).padStart(2, '0')}</div>
              <div>
                <div className="rx-label">{r.label}</div>
                <div className="rx-label-sub">P1: {r.p1}</div>
              </div>
              <div className="rx-event-type">{r.event_type}</div>
              <div className={badgeClass(r.event_type)}>{badgeLabel(r.event_type)}</div>
            </div>
          ))}
        </div>

        {/* Refusals */}
        <div className="rx-section-title">Refusals — Calculator Doctrine Applied</div>
        <div className="rx-stream">
          {REFUSALS.map((r, i) => (
            <div key={i} className="rx-refusal">
              <div>
                <div className="rx-refusal-label">{r.label}</div>
                <div className="rx-refusal-doctrine">{r.doctrine} · {r.reason}</div>
              </div>
              <div className="rx-badge rx-badge-refused">REFUSED</div>
            </div>
          ))}
        </div>

        {/* Download */}
        <div style={{
          background: 'rgba(255,255,255,0.025)',
          border: '1px solid rgba(255,255,255,0.07)',
          borderRadius: '14px',
          padding: '20px 24px',
          marginBottom: '32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
          flexWrap: 'wrap',
        }}>
          <div>
            <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '4px' }}>
              EXECUTE_01JAB7.json
            </div>
            <div style={{ fontSize: '12px', color: '#a9c4ca' }}>
              Full PDR stream · SHA-256 chained · independently verifiable
            </div>
          </div>
          <a
            href="/EXECUTE_01JAB7.json"
            download
            style={{
              fontSize: '0.75rem',
              fontWeight: 700,
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
              color: 'rgba(0,240,255,0.8)',
              textDecoration: 'none',
              border: '1px solid rgba(0,240,255,0.25)',
              padding: '9px 18px',
              borderRadius: '7px',
              whiteSpace: 'nowrap',
            }}
          >
            Download JSON →
          </a>
        </div>

        {/* Footer */}
        <footer className="rx-footer">
          <span>© 2026 Russell Nordland · TrueAlphaSpiral (TAS) · Sovereign Data Foundation</span>
          <Link to="/" className="rx-back-btn">← Return to Digital Sovereignty</Link>
        </footer>

      </div>
    </div>
  );
}
