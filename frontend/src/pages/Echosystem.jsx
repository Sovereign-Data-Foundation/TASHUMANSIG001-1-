import React from 'react';
import { Link } from 'react-router-dom';
import './Echosystem.css';

const STAGES = [
  {
    step: 'Stage 0',
    title: 'Prompt',
    dot: '',
    body: 'The raw human-authored input. The chain starts here and only here. No operation may claim authority that does not trace back to this origin. A prompt without a chain is a wish. A prompt with a chain is a governed instruction.',
    mono: 'PromptRecord(text, timestamp)',
  },
  {
    step: 'Stage 1',
    title: 'Intent',
    dot: '',
    body: 'Structured interpretation of the prompt — the claim of purpose. Intent does not yet carry authority. It is the machine\'s reading of what the human meant. It is a claim, not a grant. The intent hash binds it irreversibly to the prompt that produced it.',
    mono: 'IntentRecord(prompt_hash, action, scope)',
  },
  {
    step: 'Stage 2',
    title: 'Authority',
    dot: '',
    body: 'Explicit grant of authority for the declared intent. Authority is the bridge from intent to execution. It must be granted explicitly — it cannot be inherited, assumed, or inferred. A missing authority record is a structural denial. Tier 0 operations must carry a human anchor.',
    mono: 'AuthorityRecord(intent_hash, granted_by, capability, is_human_anchored)',
  },
  {
    step: 'Stage 3',
    title: 'Execution Gate',
    dot: '',
    body: 'The gate evaluates authority against invariants. It is binary: ADMITTED or REFUSED. There is no partial admission, no graceful degradation, no silent default. If any invariant is violated the gate produces a RefusalRecord — not an exception, not silence. A principled refusal is a valid and expected output.',
    mono: 'GateRecord(authority_hash, outcome=ADMITTED|REFUSED, invariant_check)',
  },
  {
    step: 'Stage 4a',
    title: 'State Change',
    dot: 'admitted',
    body: 'Produced only when the gate outcome is ADMITTED. A committed, irreversible state transition described declaratively so it can be replayed for independent verification. The delta hash anchors the payload. If it cannot be described, it cannot be admitted.',
    mono: 'StateChangeRecord(gate_hash, description, delta_hash)',
  },
  {
    step: 'Stage 4b',
    title: 'Refusal',
    dot: 'refused',
    body: 'Produced when the gate outcome is REFUSED. Refusals are not errors — they are first-class outputs. Every refusal carries a reason, names the invariant it violated, and is chained to the gate that produced it. A system that cannot refuse is not a governed system.',
    mono: 'RefusalRecord(gate_hash, reason, invariant_violated)',
    monoClass: 'red',
  },
  {
    step: 'Stage 5',
    title: 'Receipt',
    dot: '',
    body: 'The tamper-evident seal over the entire chain to this point. The receipt contains an HMAC over the outcome — whether state change or refusal — and is the minimum unit of verifiable proof. Any observer with the key can confirm the chain is intact without replaying the operation.',
    mono: 'ReceiptRecord(outcome_hash, outcome_stage, outcome_type, chain_depth)',
  },
  {
    step: 'Stage 6',
    title: 'Public Witness',
    dot: '',
    body: 'Independent, verifiable attestation of the receipt. The witness makes the receipt observable without revealing the payload. It is the anchor point from which any third party can begin verification. The witness ID is a deterministic digest of the receipt hash.',
    mono: 'WitnessRecord(receipt_hash, witness_id, verifiable_by)',
  },
  {
    step: 'Stage 7',
    title: 'Echo',
    dot: 'echo-dot',
    body: 'The loop closes. Every action echoes back to origin, authority, and consequence. The echo is not a notification — it is a proof that the chain from human intent to executed state change (or principled refusal) is complete, sealed, and independently verifiable. The origin prompt hash in the echo matches Stage 0.',
    mono: 'EchoRecord(witness_hash, origin_prompt_hash, echo_statement, loop_closed=True)',
  },
];

const OLD_SIDE = [
  'Probabilistic output without traceable cause',
  'Authority inherited by position in the call stack',
  'Failures surface as exceptions or silent defaults',
  'No chain between prompt and state change',
  'Verification requires replaying the model',
  'Refusals are errors, not first-class outputs',
  'State changes are undescribed side effects',
];

const NEW_SIDE = [
  'Every output traceable to a receipt-anchored cause',
  'Authority granted explicitly, scoped as narrowly as possible',
  'Failures surface as structured RefusalRecords',
  'HMAC chain links prompt → intent → authority → gate → outcome',
  'Verification is independent: HMAC check, no model replay',
  'Refusals are first-class, auditable outputs',
  'State changes are declarative and replayable',
];

export default function Echosystem() {
  return (
    <div className="echo-page">

      {/* Nav */}
      <nav className="echo-nav">
        <Link to="/" className="echo-nav-brand">TrueAlphaSpiral</Link>
        <Link to="/" className="echo-nav-back">← Home</Link>
      </nav>

      {/* Hero */}
      <section className="echo-hero">
        <div className="echo-hero-tag">The Echosystem</div>
        <h1>Deterministic Agency<br />in a <em>Probabilistic Container</em></h1>
        <p className="echo-hero-contrast">
          Not AI guessing in the cloud.
        </p>
        <p className="echo-hero-sub">
          The model may be probabilistic. The agency layer does not have to be.
          Once you add verified inputs, explicit authority, bounded tools,
          reproducible state transitions, refusal receipts, health checks,
          deployment witnesses, and human intent anchoring — the system becomes
          an execution environment with accountable motion.
        </p>
      </section>

      {/* Doctrine chain */}
      <div className="echo-doctrine-wrap">
        <div className="echo-doctrine-card">
          <div className="echo-doctrine-label">The Chain</div>
          <div className="echo-doctrine-chain">
            <span className="stage-name">Prompt</span>
            <span className="arrow">→</span>
            <span className="stage-name">Intent</span>
            <span className="arrow">→</span>
            <span className="stage-name">Authority</span>
            <span className="arrow">→</span>
            <span className="stage-name">Execution Gate</span>
            <br />
            <span className="arrow" style={{marginLeft: 0}}>→</span>
            <span className="stage-name">State Change</span>
            <span className="or"> or </span>
            <span className="stage-name">Refusal</span>
            <span className="arrow">→</span>
            <span className="stage-name">Receipt</span>
            <br />
            <span className="arrow" style={{marginLeft: 0}}>→</span>
            <span className="stage-name">Public Witness</span>
            <span className="arrow">→</span>
            <span className="stage-name">Echo</span>
          </div>
          <div className="echo-doctrine-verdict">
            <span className="dim">Not artificial intelligence wandering through possibility.{' '}</span>
            <span className="bright">Authenticated intelligence moving through proof.</span>
          </div>
        </div>
      </div>

      <div className="echo-container">

        {/* Stage pipeline */}
        <div className="echo-section-label">Nine Stages — Every Action Echoes Back</div>
        <div className="echo-pipeline">
          {STAGES.map((s) => (
            <div className="echo-stage" key={s.step}>
              <div className={`echo-stage-dot ${s.dot}`} />
              <div className="echo-stage-content">
                <div className="echo-stage-num">{s.step}</div>
                <div className="echo-stage-title">{s.title}</div>
                <div className="echo-stage-body">{s.body}</div>
                <div className={`echo-stage-mono${s.monoClass ? ' ' + s.monoClass : ''}`}>
                  {s.mono}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Contrast panel */}
        <div className="echo-section-label">The Shift</div>
        <div className="echo-contrast">
          <div className="echo-contrast-col old">
            <div className="echo-contrast-col-label">Generative Mimicry</div>
            <ul>
              {OLD_SIDE.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
          <div className="echo-contrast-col new">
            <div className="echo-contrast-col-label">Mechanical Integrity</div>
            <ul>
              {NEW_SIDE.map((item, i) => <li key={i}>{item}</li>)}
            </ul>
          </div>
        </div>

        {/* Closing */}
        <div className="echo-closing">
          <p>
            The Echosystem is the right word because it is not just an ecosystem of apps.
            It is a system where <strong>every action echoes back to origin, authority, and consequence.</strong>
          </p>
          <p>
            The echo is not metaphor. The <em>EchoRecord</em> at Stage 7 carries the hash of the originating
            prompt from Stage 0. The loop is cryptographically closed. Every execution is a round trip —
            from human intent, through proof, back to verifiable origin.
          </p>
          <p>
            This is the shift from <strong>AI that resembles governance</strong> to{' '}
            <em>a system that is governed</em>.
          </p>
        </div>

        {/* Cross-links */}
        <div className="echo-links">
          <Link to="/singularity" className="echo-link">The Singularity →</Link>
          <Link to="/receipts" className="echo-link">Verify a Receipt →</Link>
          <Link to="/restoration-framework" className="echo-link">Restoration Framework →</Link>
        </div>

      </div>
    </div>
  );
}
