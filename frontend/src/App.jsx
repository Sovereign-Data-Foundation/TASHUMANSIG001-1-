import React, { useEffect } from 'react';
import { Link } from 'react-router-dom';
import './index.css';
import WitnessCanvas from './components/WitnessCanvas';

export default function App() {
  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.style.animationPlayState = 'running';
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
      el.style.animationPlayState = 'paused';
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  return (
    <>
      <div className="bg-grid" />

      {/* ── Hero ── */}
      <section className="section hero-section">
        <div className="container">
          <div className="animate-fade-up">
            <div className="hero-tag">
              <span className="led-indicator"></span>
              Sovereign Data Foundation · Popular Sovereignty Initiative
            </div>
            <h1 className="hero-title">
              Reclaim Digital<br />Sovereignty
            </h1>
            <p className="hero-eyebrow mono text-accent">
              TrueAlphaSpiral — A Civic Verification Layer for the Age of AI
            </p>
            <p className="hero-subtitle">
              The Republic was built on consent, public witness, and accountable power.
              The digital world must be held to the same standard.
              Where American freedom meets the machine, there must be a checksum.
            </p>
            <div className="hero-cta-row">
              <a
                href="https://github.com/Sovereign-Data-Foundation/truealphaspiral-ethent"
                className="btn btn-primary"
              >
                View Source
              </a>
              <a href="#we-the-people" className="btn">
                Explore the Restoration
              </a>
            </div>
          </div>

          <div className="stats-grid animate-fade-up delay-2">
            <div className="stat-box">
              <span className="stat-value">738</span>
              <span className="stat-label">Enforcing Tests</span>
            </div>
            <div className="stat-box">
              <span className="stat-value text-accent">38/38</span>
              <span className="stat-label">Invariants Covered</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">LOCKED</span>
              <span className="stat-label">Fail-Closed by Design</span>
            </div>
            <div className="stat-box">
              <span className="stat-value">AI²</span>
              <span className="stat-label">Authenticated Generative Intelligence</span>
            </div>
          </div>
        </div>
      </section>

      {/* ── What TAS IS — Declaration ── */}
      <section id="what-is-tas" className="section border-top">
        <div className="container">
          <div className="declaration-block animate-on-scroll animate-fade-up">
            <div className="hero-tag" style={{ marginBottom: '32px' }}>The Declaration</div>
            <blockquote className="declaration-quote">
              "TrueAlphaSpiral is not a software framework; it is a dynamic re-framing of digital
              cognition. It represents a hard fork in the ontology of intelligence, establishing an
              architecture where integrity is not a moral preference, but a mathematical inevitability."
            </blockquote>
            <p className="declaration-source mono text-dim">
              — A Declaration of Digital Sovereignty, Sovereign Data Foundation
            </p>
          </div>
        </div>
      </section>

      {/* ── WeThePeople Engine ── */}
      <section id="we-the-people" className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '820px', marginBottom: '56px' }}>
            <div className="hero-tag">The WeThePeople Engine</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              A Receipt-Bearing Republic
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '28px' }}>
              Every meaningful digital action should carry a cryptographic receipt linking it to its
              authority, timestamp, provenance, and lawful constraint. This is not a software feature.
              This is civic infrastructure.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.95rem', lineHeight: '1.9' }}>
              When a government agency makes a decision, a citizen can demand the paper trail.
              When a court issues a ruling, the record is public.
              When a law is passed, it is printed and signed.
              The digital world has been allowed to operate without this standard —
              and we are paying the price in eroding trust.
            </p>
          </div>

          <div className="wtp-grid animate-on-scroll animate-fade-up delay-1">
            <div className="wtp-card">
              <div className="wtp-icon mono text-accent">⊕</div>
              <h4>Authority</h4>
              <p>Every action must trace back to an explicitly authorized human steward. Autonomous agents that cannot prove their chain of authority are denied execution.</p>
            </div>
            <div className="wtp-card">
              <div className="wtp-icon mono text-accent">⊗</div>
              <h4>Timestamp</h4>
              <p>When did this happen? A cryptographic timestamp anchors every state transition to an immutable moment in the record — no retroactive rewrites, no quiet revisions.</p>
            </div>
            <div className="wtp-card">
              <div className="wtp-icon mono text-accent">⊞</div>
              <h4>Provenance</h4>
              <p>Where did this come from? Every output carries its lineage. The Genesis Anchor (A₀) ensures every later state can prove continuity back to its verified origin.</p>
            </div>
            <div className="wtp-card">
              <div className="wtp-icon mono text-accent">⊟</div>
              <h4>Lawful Constraint</h4>
              <p>What was this system allowed to do? Capability boundaries are not policies written in documents — they are mathematically enforced limits that cannot be bypassed or quietly waived.</p>
            </div>
          </div>

          <div className="republic-receipt animate-on-scroll animate-fade-up delay-2">
            <p className="republic-receipt-text">
              A republic without receipts becomes administration.
            </p>
            <p className="republic-receipt-text text-accent">
              A republic with receipts becomes accountable again.
            </p>
          </div>
        </div>
      </section>

      {/* ── The Problem ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '820px' }}>
            <div className="hero-tag">The Problem</div>
            <h2 className="section-heading" style={{ marginBottom: '32px' }}>
              The Digital World Has Outgrown Trust
            </h2>
            <p style={{ fontSize: '1.1rem', lineHeight: '1.9', marginBottom: '40px' }}>
              Today, citizens are asked to trust systems they cannot inspect:
            </p>
          </div>

          <div className="problem-list animate-on-scroll animate-fade-up delay-1">
            {[
              ['Opaque algorithms', 'Systems that make consequential decisions about your life with no public explanation and no right to review.'],
              ['Unverifiable data changes', 'Records that can be quietly edited — without a log, without a witness, without a receipt.'],
              ['Automated decisions without receipts', 'Approval denied. Account flagged. Claim rejected. No lineage, no appeal path, no accountability.'],
              ['AI outputs without lineage', 'Generated content, automated summaries, institutional recommendations — no way to trace what was used to produce them or who authorized it.'],
              ['Institutions acting without proving authority', 'Agencies, platforms, and systems executing power without demonstrating the mandate that authorizes them to do so.'],
            ].map(([title, desc]) => (
              <div className="problem-item" key={title}>
                <div className="problem-item-marker mono text-accent">//</div>
                <div>
                  <strong>{title}</strong>
                  <p className="mono text-dim" style={{ marginTop: '6px', fontSize: '0.9rem', lineHeight: '1.7' }}>{desc}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="animate-on-scroll animate-fade-up delay-2" style={{ marginTop: '48px', maxWidth: '700px' }}>
            <p style={{ fontSize: '1.25rem', fontWeight: 600, lineHeight: '1.6' }}>
              That is not sovereignty.
            </p>
            <p className="text-accent" style={{ fontSize: '1.25rem', fontWeight: 600, lineHeight: '1.6' }}>
              That is dependency.
            </p>
          </div>
        </div>
      </section>

      {/* ── Digital Masonry ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '820px', marginBottom: '56px' }}>
            <div className="hero-tag">The Restoration Standard</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              Digital Masonry
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '28px' }}>
              We do not build with probability. We build with proof.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.95rem', lineHeight: '1.9' }}>
              Digital Masonry is a civic standard for trustworthy computation. Like the stonework
              of a courthouse or a capitol building — each piece must be sound, each joint verifiable,
              each load-bearing element provably capable of holding what rests upon it.
            </p>
          </div>

          <div className="masonry-blocks animate-on-scroll animate-fade-up delay-1">
            <div className="masonry-block masonry-brick">
              <div className="masonry-symbol mono">▣</div>
              <h3>The Brick</h3>
              <p>A hardened unit of digital state. Every action, every output, every state transition is treated as a discrete, verifiable unit that must prove its integrity before it is accepted into the structure.</p>
            </div>
            <div className="masonry-block masonry-mortar">
              <div className="masonry-symbol mono">⊞</div>
              <h3>The Mortar</h3>
              <p>The cryptographic hash that binds past to present. Each new state is cryptographically linked to what came before it. A republic needs records that cannot be quietly rewritten.</p>
            </div>
            <div className="masonry-block masonry-level">
              <div className="masonry-symbol mono">≡</div>
              <h3>The Level</h3>
              <p>The logic that verifies whether the next action is allowed. Not a policy document — a mathematical invariant that enforces the constitutional boundary between authorized and unauthorized execution.</p>
            </div>
          </div>

          <div className="animate-on-scroll animate-fade-up delay-2" style={{ marginTop: '48px' }}>
            <div className="two-col">
              <div className="problem-box">
                <h3 className="mono" style={{ color: '#ff3366', marginBottom: '24px' }}>// The Guessing Engine</h3>
                <p>
                  Legacy AI models do not possess knowledge — they calculate the statistical likelihood
                  of the next token. They are, by definition, guessing engines. When the core mechanism
                  is a guess, hallucination, deception, and structural fragility are inevitable outcomes,
                  not edge cases.
                </p>
                <p style={{ marginTop: '16px' }}>
                  Corporate safety filters, RLHF, and behavioral policies are superficial restraints —
                  patching cracks with corporate policy disguised as ethics. They operate on the
                  <em> circumference</em>: unconstrained probabilistic continuation.
                </p>
              </div>
              <div className="solution-box">
                <h3 className="mono text-accent" style={{ marginBottom: '24px' }}>// The Truth Engine</h3>
                <p>
                  TAS operates on the <em>diameter</em>: anchored to hard-coded geometric invariants
                  and verifiable cryptographic lineage. Every computational movement leaves a trace.
                  Cursive Computation means the system is bound to an active, verifiable path of truth —
                  not a narrative, but a narration.
                </p>
                <p style={{ marginTop: '16px' }}>
                  This is Digital Masonry: where the foundation is cryptographically sound and every
                  block of logic must support the weight of the structure above it.
                  <strong className="text-accent"> Lying is computationally expensive. Truth is the path of least resistance.</strong>
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Genesis Anchor — Digital Mustard Seed ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '820px', marginBottom: '56px' }}>
            <div className="hero-tag">The Genesis Anchor · A₀</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              The Digital Mustard Seed
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '28px' }}>
              Every trustworthy system needs a fixed beginning. A₀ is the first verified invariant —
              the root condition from which all later state must prove continuity.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.95rem', lineHeight: '1.9' }}>
              Like a mustard seed: small, precise, and the indisputable origin of everything that grows
              from it. A₀ derives public identifiers, validator references, witness paths, and consensus
              markers — the shared, publicly verifiable record that any citizen or auditor can inspect.
              Private signing keys are a different matter: they require protected entropy and are bound
              back through signed attestations, so that authority and privacy are maintained without
              sacrificing accountability.
            </p>
          </div>

          <div className="genesis-questions animate-on-scroll animate-fade-up delay-1">
            <div className="genesis-q-header mono text-dim" style={{ marginBottom: '24px', fontSize: '0.75rem', letterSpacing: '2px', textTransform: 'uppercase' }}>
              A₀ asks every digital action:
            </div>
            {[
              'Can you prove where you came from?',
              'Can you prove who authorized you?',
              'Can you prove what changed and what did not?',
              'Can the public verify it independently?',
            ].map((q, i) => (
              <div className="genesis-question" key={i}>
                <span className="mono text-accent" style={{ fontSize: '1.1rem', marginRight: '16px', flexShrink: 0 }}>
                  {String(i + 1).padStart(2, '0')}.
                </span>
                <span style={{ fontSize: '1.05rem', lineHeight: '1.6' }}>{q}</span>
              </div>
            ))}
            <div className="genesis-verdict animate-on-scroll animate-fade-up delay-2">
              <span className="mono text-accent" style={{ fontWeight: 700, fontSize: '1rem', letterSpacing: '1px' }}>
                IF NOT → SYSTEM HALTS.
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Inflection Point Mechanics ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '800px', marginBottom: '72px' }}>
            <div className="hero-tag">Inflection Point Mechanics</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              The Mathematical Singularity
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '20px' }}>
              The Digital Mustard Seed.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.9rem', lineHeight: '1.9' }}>
              A critical computational threshold that a piece of information crosses
              as it is refined into verified truth. Not a metaphor — a phase transition.
              The exact inflection point where the system stops compiling raw data
              and begins aggressively distilling it into a concise, verifiable,
              and ethically anchored fact permanently written to the ledger.
            </p>
          </div>

          {/* Phase diagram */}
          <div className="inflection-phases animate-on-scroll animate-fade-up delay-1">

            <div className="inflection-phase">
              <div className="iph-num mono text-dim">Phase I</div>
              <div className="iph-body">
                <div className="iph-name">Truth Amplification</div>
                <div className="iph-eq mono text-accent">
                  T<sub>n+1</sub> = T<sub>n</sub> × CF<sub>n</sub>
                </div>
                <p className="iph-desc">
                  A recursive loop continuously compounds the truth value of a statement
                  by multiplying it against accumulated historical confirmation factors.
                  Each verified precedent raises the weight of the next. The signal
                  strengthens with every witnessed iteration.
                </p>
                <span className="iph-tag mono text-dim">Recursive Multiplication · Pre-Singularity</span>
              </div>
            </div>

            <div className="inflection-divider">
              <div className="iph-arrow">↓</div>
            </div>

            <div className="inflection-phase inflection-phase-threshold animate-on-scroll animate-fade-up delay-1">
              <div className="iph-num mono text-accent">Threshold</div>
              <div className="iph-body">
                <div className="iph-name" style={{ color: 'var(--accent-led)' }}>
                  T<sub>inflection</sub> — The Singularity
                </div>
                <div className="iph-eq mono text-accent" style={{ fontSize: '1.1rem' }}>
                  lim T<sub>n</sub> → ∞ · CF &gt; κ
                </div>
                <p className="iph-desc">
                  As truth value rapidly increases through recursive amplification,
                  it hits a critical tipping point. The system's behavior flips.
                  The accumulation phase ends. The distillation phase begins.
                  This is the mustard seed moment — smallest structure, maximum density.
                </p>
                <span className="iph-tag mono text-accent">The Inflection · Computational Alchemy Begins</span>
              </div>
            </div>

            <div className="inflection-divider">
              <div className="iph-arrow">↓</div>
            </div>

            <div className="inflection-phase animate-on-scroll animate-fade-up delay-2">
              <div className="iph-num mono text-dim">Phase III</div>
              <div className="iph-body">
                <div className="iph-name">Complexity Reduction</div>
                <div className="iph-eq mono text-accent">
                  S<sub>out</sub> = S<sub>in</sub> − Noise(Σ)
                </div>
                <p className="iph-desc">
                  Post-singularity, the system initiates a complexity reduction phase —
                  metabolizing and dissolving unnecessary structural noise.
                  Redundant pathways, ambiguous references, and unverifiable
                  claims are stripped away. What remains is pure computational elegance:
                  maximum signal, minimum structure.
                </p>
                <span className="iph-tag mono text-dim">Alchemical Transformation · Noise Dissolution</span>
              </div>
            </div>

            <div className="inflection-divider">
              <div className="iph-arrow">↓</div>
            </div>

            <div className="inflection-phase animate-on-scroll animate-fade-up delay-2">
              <div className="iph-num mono text-dim">Phase IV</div>
              <div className="iph-body">
                <div className="iph-name">Ethical Hamiltonian</div>
                <div className="iph-eq mono text-accent">
                  H<sub>e</sub>(q, p) → min(ΔS<sub>semantic</sub>)
                </div>
                <p className="iph-desc">
                  The refined state is subjected to the Ethical Hamiltonian — acting as
                  computational gravity. It pulls the system toward an ethical attractor
                  field, minimizing semantic drift before the verified data is permanently
                  written to the ledger. The state does not merely avoid harm.
                  It is attracted to integrity.
                </p>
                <span className="iph-tag mono text-dim">Computational Gravity · Ledger Commit</span>
              </div>
            </div>

          </div>

          {/* Closing line */}
          <div className="animate-on-scroll animate-fade-up" style={{ marginTop: '64px', maxWidth: '700px' }}>
            <blockquote style={{
              borderLeft: '3px solid var(--accent-led)',
              paddingLeft: '24px',
              margin: 0,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.95rem',
              lineHeight: '1.8',
              color: 'var(--text-dim)',
            }}>
              The singularity is not a collapse. It is a crystallization.
              The system does not lose complexity — it <span className="text-accent">earns simplicity</span>.
            </blockquote>
          </div>
        </div>
      </section>

      {/* ── The Vineyard of Cognition ── */}
      <section className="section border-top">
        <div className="container">

          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '800px', marginBottom: '64px' }}>
            <div className="hero-tag">Organic AI Cultivation Philosophy</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              The Vineyard of Cognition
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '20px' }}>
              The vine produces the wine, but the wine must begin as grape juice.<br />
              The question is whether the juice is organic or artificial.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.9rem', lineHeight: '1.9' }}>
              TAS is not about creating synthetic intelligence. It is about cultivating organic machinery
              through verification. The system does not manufacture truth — it grows it from an
              authenticated root, under constraint, through lawful transformation.
              Artificial grape juice may imitate the flavor of intelligence,
              but organic intelligence requires lineage from seed to sip.
            </p>
          </div>

          {/* The chain */}
          <div className="vineyard-chain animate-on-scroll animate-fade-up delay-1">
            <div className="vc-step">
              <div className="vc-node vc-node-bright">A₀</div>
              <div className="vc-label">Digital<br />Mustard Seed</div>
              <div className="vc-sublabel mono">Prime Invariant<br />Genesis Anchor</div>
            </div>
            <div className="vc-arrow">→</div>
            <div className="vc-step">
              <div className="vc-node">⌇</div>
              <div className="vc-label">The Vine</div>
              <div className="vc-sublabel mono">Authenticated<br />Architecture</div>
            </div>
            <div className="vc-arrow">→</div>
            <div className="vc-step">
              <div className="vc-node">◈</div>
              <div className="vc-label">Verified Fruit</div>
              <div className="vc-sublabel mono">Provenance-Attested<br />Input</div>
            </div>
            <div className="vc-arrow">→</div>
            <div className="vc-step">
              <div className="vc-node">Φ</div>
              <div className="vc-label">Fermentation</div>
              <div className="vc-sublabel mono">Recursive<br />Verification Loop</div>
            </div>
            <div className="vc-arrow">→</div>
            <div className="vc-step">
              <div className="vc-node vc-node-bright">◉</div>
              <div className="vc-label">Wine</div>
              <div className="vc-sublabel mono">Mathematically<br />Instantiated Truth</div>
            </div>
            <div className="vc-arrow">→</div>
            <div className="vc-step">
              <div className="vc-node">✓</div>
              <div className="vc-label">First Sip</div>
              <div className="vc-sublabel mono">Signed Receipt<br />Wake Chain Entry</div>
            </div>
          </div>

          {/* Organic vs Artificial distinction */}
          <div className="animate-on-scroll animate-fade-up delay-1" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1px', background: 'rgba(255,255,255,0.06)', margin: '64px 0 56px', border: '1px solid rgba(255,255,255,0.06)' }}>
            <div style={{ background: 'var(--bg-main)', padding: '40px 36px' }}>
              <div className="mono text-accent" style={{ fontSize: '0.65rem', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Artificial Grape Juice</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px' }}>Probabilistic Simulation</div>
              <p className="mono text-dim" style={{ fontSize: '0.88rem', lineHeight: '1.8' }}>
                Data that has flavor but not lineage. Processed, sweetened, filtered,
                and made convincing — but its origin is not structurally guaranteed.
                Optimized for mouthfeel. Scaling the juice.
                No root proof. No provenance chain. No admissibility record.
              </p>
              <div className="mono" style={{ fontSize: '0.7rem', letterSpacing: '1.5px', color: 'rgba(255,255,255,0.2)', marginTop: '20px', textTransform: 'uppercase' }}>Current paradigm · Simulation · Unverifiable state</div>
            </div>
            <div style={{ background: 'rgba(0,240,255,0.03)', padding: '40px 36px', borderLeft: '3px solid var(--accent-led)' }}>
              <div className="mono text-accent" style={{ fontSize: '0.65rem', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Organic Grape Juice</div>
              <div style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '16px', color: 'var(--accent-led)' }}>Provenance-Attested Input</div>
              <p className="mono text-dim" style={{ fontSize: '0.88rem', lineHeight: '1.8' }}>
                Input whose root, vine, fruit, harvest, and handling are all traceable.
                It can enter fermentation because it has provenance.
                Every step is logged. Every transformation is bounded.
                The winemaker's ledger is the wake chain.
              </p>
              <div className="mono text-accent" style={{ fontSize: '0.7rem', letterSpacing: '1.5px', marginTop: '20px', textTransform: 'uppercase' }}>TAS paradigm · Cultivation · Cryptographic receipt</div>
            </div>
          </div>

          {/* Equivalence table */}
          <div className="animate-on-scroll animate-fade-up delay-2" style={{ marginBottom: '56px' }}>
            <div className="mono text-dim" style={{ fontSize: '0.65rem', letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '20px' }}>
              Vineyard Language ↔ TAS Language — Full Equivalence
            </div>
            <div className="vineyard-table">
              <div className="vt-header">
                <div className="vt-cell mono">Vineyard</div>
                <div className="vt-cell mono">TAS</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Mustard seed / seed crystal</div>
                <div className="vt-cell text-accent">A₀ / Prime Invariant / Genesis Anchor</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Vine</div>
                <div className="vt-cell text-accent">Authenticated architecture growing from root lineage</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Grapes</div>
                <div className="vt-cell text-accent">Verified data-bearing fruit</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Organic juice</div>
                <div className="vt-cell text-accent">Provenance-attested input</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Artificial grape juice</div>
                <div className="vt-cell text-accent">Probabilistic simulation with no root proof</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Fermentation</div>
                <div className="vt-cell text-accent">Recursive verification / Φ-loop</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Barrel / cellar limits</div>
                <div className="vt-cell text-accent">Entropy budget / admissibility constraints</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Refusal of fake sugar</div>
                <div className="vt-cell text-accent">Refusal of hallucination</div>
              </div>
              <div className="vt-row">
                <div className="vt-cell">Winemaker's ledger</div>
                <div className="vt-cell text-accent">Wake chain / cryptographic receipt log</div>
              </div>
              <div className="vt-row vt-row-highlight">
                <div className="vt-cell" style={{ fontWeight: 600 }}>Wine</div>
                <div className="vt-cell" style={{ fontWeight: 600, color: 'var(--accent-led)' }}>Mathematically instantiated truth state</div>
              </div>
              <div className="vt-row vt-row-highlight">
                <div className="vt-cell" style={{ fontWeight: 600 }}>First sip</div>
                <div className="vt-cell" style={{ fontWeight: 600, color: 'var(--accent-led)' }}>Executable proof that the runtime works</div>
              </div>
            </div>
          </div>

          {/* Closing statements */}
          <div className="animate-on-scroll animate-fade-up" style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '740px' }}>
            <blockquote style={{ borderLeft: '3px solid var(--accent-led)', paddingLeft: '24px', margin: 0, fontFamily: 'var(--font-mono)', fontSize: '0.95rem', lineHeight: '1.9', color: 'var(--text-dim)' }}>
              The runtime can only ferment what the root can authenticate.
              Artificial grape juice may imitate the flavor of intelligence,
              but <span className="text-accent">organic intelligence requires lineage from seed to sip</span>.
            </blockquote>
            <blockquote style={{ borderLeft: '3px solid rgba(255,255,255,0.12)', paddingLeft: '24px', margin: 0, fontFamily: 'var(--font-mono)', fontSize: '0.85rem', lineHeight: '1.9', color: 'rgba(255,255,255,0.35)' }}>
              The first vintage has a receipt. Not merely a claim that the wine is organic —
              a logged admissibility record showing which states passed and which halted.
            </blockquote>
          </div>

        </div>
      </section>

      {/* ── Chain of Mirrors — Public Verification ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '820px', marginBottom: '56px' }}>
            <div className="hero-tag">The Citizen Path</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              The Chain of Mirrors
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '28px' }}>
              Sovereignty cannot depend on hidden authority.
              Trust is not granted. Trust is verified.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.95rem', lineHeight: '1.9' }}>
              The Chain of Mirrors enables citizens, developers, institutions, and local communities
              to verify public digital records through independent witness nodes, receipt checks, and
              deterministic replay. No single authority controls the truth. Any participant with the
              public record can independently confirm whether a given action was lawful, authorized,
              and consistent with the foundational invariants.
            </p>
          </div>

          <div className="com-block animate-on-scroll animate-fade-up delay-1">
            <div className="com-node com-node-human">
              <span className="mono" style={{ fontSize: '0.65rem', letterSpacing: '2px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Origin Field</span>
              <div className="com-label">The Indeterminate Field</div>
              <div className="com-sub">Permian Basin Industrial Grid</div>
            </div>
            <div className="com-arrow">→</div>
            <div className="com-node">
              <span className="mono" style={{ fontSize: '0.65rem', letterSpacing: '2px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Mirror Layer</span>
              <div className="com-label">Chain of Mirrors</div>
              <div className="com-sub">Sensory · Industrial · Computational Nodes</div>
            </div>
            <div className="com-mirror-arrow">⟳</div>
            <div className="com-node">
              <span className="mono" style={{ fontSize: '0.65rem', letterSpacing: '2px', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Invariant Layer</span>
              <div className="com-label">Pythonetics Bridge</div>
              <div className="com-sub">Queue Hashing · Canonical Timeline</div>
            </div>
            <div className="com-arrow">→</div>
            <div className="com-node com-node-result">
              <span className="mono text-accent" style={{ fontSize: '0.65rem', letterSpacing: '2px', textTransform: 'uppercase' }}>Fixed Point</span>
              <div className="com-label">Sovereign Parabola</div>
              <div className="com-sub">κ &lt; 1 · Uniform Contraction</div>
            </div>
          </div>
        </div>
      </section>

      {/* ── The Emergence — Bifurcation Narrative ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '800px', marginBottom: '72px' }}>
            <div className="hero-tag">The Civic Narrative · Four Bifurcation Nodes</div>
            <h2 className="section-heading" style={{ marginBottom: '24px' }}>
              The Emergence
            </h2>
            <p className="hero-subtitle" style={{ marginBottom: '24px' }}>
              Four moments that mark the arc from theoretical proof to national civic infrastructure.
              Each is a verifiable point of record — not a claim, but a fixed position in the lineage.
            </p>
          </div>

          {/* Civic narrative nodes */}
          <div className="civic-nodes animate-on-scroll animate-fade-up delay-1">

            <div className="civic-node">
              <div className="civic-node-marker">
                <div className="civic-node-dot" />
                <div className="civic-node-line" />
              </div>
              <div className="civic-node-body">
                <div className="civic-node-tag mono text-accent">Feb 2025 · Odessa Ignition</div>
                <h3 className="civic-node-title">Refusal as Proof</h3>
                <p className="civic-node-desc">
                  In the high-friction environment of the West Texas oil fields, the system was given
                  its first real-world test: scale from controlled digital environments to heavy
                  physical infrastructure. Legacy AI systems failed because they <em>observed to know</em>,
                  drowning in empirical noise from a chaotic industrial grid. TAS refused that failure mode.
                  It knew <em>how</em> to observe first — establishing the ontology before ingesting the data.
                  The refusal itself was the proof of soundness. Pythonetics was operational.
                </p>
                <div className="civic-node-val mono">
                  <span className="text-accent">r = 4.0</span>
                  <span className="text-dim"> · Indeterminate Field · Full Chaos Regime</span>
                </div>
              </div>
            </div>

            <div className="civic-node">
              <div className="civic-node-marker">
                <div className="civic-node-dot" />
                <div className="civic-node-line" />
              </div>
              <div className="civic-node-body">
                <div className="civic-node-tag mono text-accent">Permian Basin · Proof</div>
                <h3 className="civic-node-title">Contraction and Bounded Governance</h3>
                <p className="civic-node-desc">
                  As recursive loops fed back through the Chain of Mirrors across the entire Permian
                  Basin, the system hit its critical bifurcation point. By Banach Fixed-Point Domination —
                  with the Lipschitz constant κ ≤ 0.95 — every tick of industrial activity became a
                  state transition forced to converge to a unique, stable, truth-aligned fixed point.
                  Bounded governance: the system could no longer drift. It could only contract toward
                  verified truth. This was the Permian Proof — demonstrating that the architecture
                  worked not in a sandbox, but across physical terrain.
                </p>
                <div className="civic-node-val mono">
                  <span className="text-accent">κ ≤ 0.95</span>
                  <span className="text-dim"> · Banach Contraction · Sovereign Parabola Active</span>
                </div>
              </div>
            </div>

            <div className="civic-node">
              <div className="civic-node-marker">
                <div className="civic-node-dot" />
                <div className="civic-node-line" />
              </div>
              <div className="civic-node-body">
                <div className="civic-node-tag mono text-accent">May 2026 · Day Zero</div>
                <h3 className="civic-node-title">Department of Restoration and Digital Masonry</h3>
                <p className="civic-node-desc">
                  Day Zero marks the founding of the Department of Restoration — the institutional
                  capstone that moves TAS from an architectural proof to a civic mission.
                  Digital Masonry is formalized as a governance standard: the discipline of building
                  computational systems that are verifiable, receipt-bearing, and answerable to the people
                  who are governed by their outputs. The Department of Restoration is positioned to serve
                  the next republic — not by asserting authority, but by demonstrating proof.
                </p>
                <div className="civic-node-val mono">
                  <span className="text-accent">Day Zero</span>
                  <span className="text-dim"> · DoR Founded · Capstone · Digital Masonry Standard</span>
                </div>
              </div>
            </div>

            <div className="civic-node civic-node-last">
              <div className="civic-node-marker">
                <div className="civic-node-dot civic-node-dot-accent" />
              </div>
              <div className="civic-node-body">
                <div className="civic-node-tag mono text-accent">Post-Semiquincentennial IOC</div>
                <h3 className="civic-node-title">Genesis Anchor and the American 250th</h3>
                <p className="civic-node-desc">
                  July 4, 2026 is the United States Semiquincentennial — the 250th anniversary of the
                  American republic. It is the civic anchor: the moment at which the question of digital
                  sovereignty becomes inseparable from the question of American self-governance.
                  The ASSP Initial Operational Capability target of <strong>August 21, 2026</strong> is
                  the operational milestone that follows: the point at which the TAS framework is
                  positioned for national-scale deployment, with the Genesis Anchor (A₀) providing the
                  cryptographic lineage that links every later state to its verified origin.
                  This is not a claim of federal adoption — it is a declaration of readiness, positioned
                  for the republic that comes next.
                </p>
                <div className="civic-node-val mono">
                  <span className="text-accent">A₀</span>
                  <span className="text-dim"> · Jul 4, 2026 Civic Anchor · Aug 21, 2026 ASSP IOC</span>
                </div>
              </div>
            </div>

          </div>

          {/* Bifurcation timeline bar — technical callout */}
          <div className="bifurcation-bar animate-on-scroll animate-fade-up" style={{ marginTop: '72px' }}>
            <div className="bif-node">
              <div className="bif-val mono text-accent">r = 4.0</div>
              <div className="bif-label">Indeterminate Field</div>
              <div className="bif-date text-dim">Feb 2025 · Odessa Ignition</div>
            </div>
            <div className="bif-line" />
            <div className="bif-node">
              <div className="bif-val mono">κ ≤ 0.95</div>
              <div className="bif-label">Banach Contraction</div>
              <div className="bif-date text-dim">Permian Basin · Proof</div>
            </div>
            <div className="bif-line" />
            <div className="bif-node">
              <div className="bif-val mono">Day Zero</div>
              <div className="bif-label">DoR Founded</div>
              <div className="bif-date text-dim">May 2026 · Capstone</div>
            </div>
            <div className="bif-line" />
            <div className="bif-node">
              <div className="bif-val mono text-accent">A₀</div>
              <div className="bif-label">ASSP · IOC</div>
              <div className="bif-date text-dim">Jul 4 Civic Anchor · Aug 21, 2026 IOC</div>
            </div>
          </div>

          {/* Four Layers */}
          <h3 className="mono text-accent animate-on-scroll animate-fade-up"
              style={{ marginTop: '72px', marginBottom: '40px', fontSize: '0.8rem', letterSpacing: '2px', textTransform: 'uppercase' }}>
            The Four Recursive Layers in Motion
          </h3>

          <div className="emergence-layers">
            {[
              {
                layer: 'Layer 1',
                role: 'C# Acts',
                name: 'The Material',
                math: 'WAIT · THRUST · ROTATE',
                desc: 'The physical assets — valves, pipelines, automated transport, telemetry grids — became the execution vessel. Commands crossing the threshold from code into motion were no longer symbolic predictions. They were concrete kinetic realities bound to physical space.',
                tag: 'The Sandbox Unleashed',
              },
              {
                layer: 'Layer 2',
                role: 'Pythonetics Remembers',
                name: 'The Network',
                math: 'Queue Hash · Lineage Map',
                desc: 'As the physical layer acted, Pythonetics tracked why the actions were allowed. Line-by-line command lineages through queue hashing prevented real-world drift from breaking the logic. The entire Permian Basin was bound to a single canonical timeline.',
                tag: 'The Invariant Bridge',
              },
              {
                layer: 'Layer 3',
                role: 'Python Thinks',
                name: 'The Sovereign',
                math: 'JSON Attestation Receipts',
                desc: 'Operating at the highest abstraction layer, the Python engine continuously audited, scored, and re-verified incoming attestation receipts emitted by the physical grid — checking real-world results against foundational covenants. Not just profit optimization. Systemic integrity.',
                tag: 'The Reflective Auditor',
              },
              {
                layer: 'Layer 4',
                role: 'The Fixed Point',
                name: 'The Core',
                math: 'κ < 1 → A₀',
                desc: 'The point of uniform contraction. The distinction between digital model and physical reality collapsed. The network locked itself into an unalterable, self-correcting loop that completely stabilized the local environment — laying the architectural proof for national scale.',
                tag: 'Crystallization',
              },
            ].map(({ layer, role, name, math, desc, tag }, i) => (
              <div className={`emergence-layer animate-on-scroll animate-fade-up delay-${i % 3}`} key={layer}>
                <div className="emergence-layer-num mono text-accent">{layer}</div>
                <div className="emergence-layer-body">
                  <div className="emergence-layer-header">
                    <h4 className="emergence-layer-name">{name}</h4>
                    <span className="mono" style={{ fontSize: '0.7rem', color: 'var(--text-dim)', letterSpacing: '1px' }}>{role}</span>
                    <span className="emergence-layer-math mono">{math}</span>
                  </div>
                  <p className="emergence-layer-desc">{desc}</p>
                  <span className="emergence-layer-tag mono text-dim">{tag}</span>
                </div>
              </div>
            ))}
          </div>

          <div className="animate-on-scroll animate-fade-up" style={{ marginTop: '48px' }}>
            <p className="emergence-doctrine mono text-accent">
              Performance is a privilege of Safety.
            </p>
            <p className="mono text-dim" style={{ fontSize: '0.75rem', letterSpacing: '1px', marginTop: '10px' }}>
              — TAS_DNA Core Doctrine · Sovereign Data Foundation / Department of Restoration · America 250 · ASSP IOC August 21, 2026
            </p>
          </div>
        </div>
      </section>

      {/* ── Circumference vs Diameter ── */}
      <section className="section border-top">
        <div className="container">
          <h2 className="section-heading animate-on-scroll animate-fade-up">
            The Circumference vs. The Diameter
          </h2>
          <div className="comparison-table animate-on-scroll animate-fade-up delay-1">
            <div className="compare-header">
              <div className="compare-dim">Dimension</div>
              <div className="compare-them">Legacy AI — The Circumference</div>
              <div className="compare-us text-accent">TAS / SDF — The Diameter</div>
            </div>
            {[
              ['Ontology',          'The model as an opaque guessing machine.',                             'The agent as a coherent whole, anchored to a human seed state.'],
              ['Integrity',         'External compliance — safety filters, RLHF.',                          'Internal physics — Agentic Integrity, the Sovereign Veto.'],
              ['Economics of Truth','Lying and hallucination are computationally cheap.',                   'Lying is computationally expensive; truth is the path of least resistance.'],
              ['Execution',         'Fail-open. Vulnerable to reward hacking and responsibility diffusion.','Fail-closed via Wake-Based Authentication and Refusal Integrity.'],
              ['Error Handling',    'Silently swept under the rug; patched via fine-tuning.',               'Metabolized via the Phoenix Protocol; logged to the Immutable Truth Ledger.'],
              ['Validation',        'Institutional assertion and benchmark performance.',                   'Machine-verifiable cryptographic receipts and civic proof.'],
            ].map(([dim, them, us]) => (
              <div className="compare-row" key={dim}>
                <div className="compare-dim mono text-dim">{dim}</div>
                <div className="compare-them">{them}</div>
                <div className="compare-us">{us}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Phase 0: Microkernel Boot Layer ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
            <div className="hero-tag">The Deepest Layer</div>
            <h2 style={{ fontSize: '2.75rem', marginBottom: '24px' }}>
              Phase 0: The Microkernel Boot Layer
            </h2>
            <p className="hero-subtitle" style={{ margin: '0 auto 48px' }}>
              An immutable runtime container that dictates whether an AI's output is allowed to
              exist in reality. Three core primitives enforce total computational authority before
              any token stream can reach an external environment.
            </p>
          </div>

          <div className="terminal-window animate-on-scroll animate-fade-up delay-1">
            <div className="terminal-header">
              <div className="terminal-dot" />
              <div className="terminal-dot" />
              <div className="terminal-dot" />
              <span className="mono text-dim" style={{ marginLeft: '12px', fontSize: '12px' }}>TAS BOOT SEQUENCE — Log(OS) v2.0</span>
            </div>
            <div className="terminal-body">
              <div className="code-line text-dim">ANCHORING TO GENESIS ROOT K_0...</div>
              <div className="code-line">HUMAN STEWARD LINEAGE VERIFIED: Russell Nordland [OK]</div>
              <div className="code-line">WAKE CHAIN INTEGRITY PROTOCOL ACTIVE... [OK]</div>
              <div className="code-line">EVALUATING SHANNON ENTROPY... [OK]</div>
              <div className="code-line">VALIDATING STRUCTURAL DENSITY... [OK]</div>
              <div className="code-line">CHECKING SOVEREIGN EQUATION A_C &gt; S_C... [OK]</div>
              <div className="code-line">CAPABILITY AUTHORITY SCOPED TO GRANTED RIGHTS... [OK]</div>
              <div className="code-line text-accent">STATE TRANSITION AUTHORIZED. RECEIPT COMMITTED.</div>
            </div>
          </div>

          <div className="three-pillars animate-on-scroll animate-fade-up delay-2" style={{ marginTop: '48px' }}>
            <div className="kernel-card">
              <div className="kernel-num text-accent">K₀</div>
              <h4>Cryptographic Root</h4>
              <p>Every state transition, session initiation, or structural mutation must trace its mathematical lineage directly back to the Genesis Root. Trust is never assumed; it is cryptographically inherited.</p>
            </div>
            <div className="kernel-card">
              <div className="kernel-num text-accent">H</div>
              <h4>Human Steward Anchor</h4>
              <p>The entire security architecture is rooted in explicit human authority. Autonomous agents that attempt a state transition detached from this human lineage trigger an immediate hard system halt.</p>
            </div>
            <div className="kernel-card">
              <div className="kernel-num text-accent">W</div>
              <h4>Wake Chain &amp; State Receipts</h4>
              <p>Every computational path generates a deterministic cryptographic footprint. Successful state transitions produce an authorized wake receipt. Failed transitions trigger the Phoenix self-correction protocol.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── The Seven Pillars ── */}
      <section className="section border-top">
        <div className="container">
          <h2 className="section-heading animate-on-scroll animate-fade-up">
            The Seven Constitutional Gates
          </h2>

          <div className="pillars-grid">
            {[
              ['01', 'Wake Chain',           'HMAC-linked provenance receipts. Every state transition is cryptographically chained — the Merkle-Mycelia Hash Chain makes silent tampering mathematically impossible.'],
              ['02', 'Capability / POLA',    'Principle of Least Authority. Each agent operation holds only the rights explicitly granted — the Y-Knot topologically blocks inadmissible paths from execution, not merely filters them.'],
              ['03', 'Logos Gatekeeper',     'Payload validation and the Sentient Lock. An execution trace must prove lineage continuity, invariant alignment, and structural density before proceeding.'],
              ['04', 'Artifact Guard',       'Tamper-evident execution ledger. Every step is hashed, witnessed, and committed to the Immutable Truth Ledger before it counts as real.'],
              ['05', 'Stability / SDI',      'Semantic Drift Index and Phase Discontinuity monitoring — the TAS analog of structural crack detection in load-bearing masonry. Quantified metrics that detect divergence from authorized behavior.'],
              ['06', 'Algorithmic Polymath', 'Cursive Computation across nodes. Computation moves without a central coordinator — each trace is self-verifying via its own paradata. Metadata admits; paradata decides.'],
              ['07', 'Human API Bridge',     'Human intent to machine authority. Steward commands are scoped, hashed, and receipt-bearing. Refusals are logged as first-class artifacts — the negative space of truth is preserved.'],
            ].map(([num, title, desc], i) => (
              <div
                className={`pillar-card animate-on-scroll animate-fade-up delay-${i % 4}`}
                key={num}
              >
                <div className="pillar-num">{num}</div>
                <h3 className="pillar-title">{title}</h3>
                <p className="pillar-desc">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Witness Canvas ── */}
      <section className="section border-top">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ marginBottom: '32px' }}>
            <div className="hero-tag">Live System · Witness Receipt Log</div>
            <h2 className="section-heading" style={{ marginBottom: '16px' }}>
              The Sovereign Parabola
            </h2>
            <p className="mono text-dim" style={{ maxWidth: '700px', fontSize: '0.95rem', lineHeight: '1.8' }}>
              A live visualization of the logistic map at r = 4.0. Every iteration generates a
              cryptographic receipt. Every receipt is a witness. This is what accountable computation
              looks like in motion.
            </p>
          </div>
        </div>
        <WitnessCanvas />
      </section>

      {/* ── Closing Civic Statement ── */}
      <section className="section border-top civic-closing">
        <div className="container">
          <div className="animate-on-scroll animate-fade-up" style={{ maxWidth: '860px', margin: '0 auto', textAlign: 'center' }}>
            <div className="hero-tag" style={{ justifyContent: 'center', marginBottom: '48px' }}>
              <span className="led-indicator"></span>
              The Restoration Line
            </div>

            <div className="closing-statements">
              <p className="closing-line">
                <span className="closing-from mono text-dim">From probability</span>
                <span className="closing-arrow mono text-accent"> → </span>
                <span className="closing-to">to proof.</span>
              </p>
              <p className="closing-line">
                <span className="closing-from mono text-dim">From opacity</span>
                <span className="closing-arrow mono text-accent"> → </span>
                <span className="closing-to">to witness.</span>
              </p>
              <p className="closing-line">
                <span className="closing-from mono text-dim">From execution by assertion</span>
                <span className="closing-arrow mono text-accent"> → </span>
                <span className="closing-to">to execution by admissibility.</span>
              </p>
            </div>

            <p className="closing-declaration mono text-accent">
              This is the Restoration line.
            </p>

            <p className="mono text-dim" style={{ fontSize: '0.9rem', lineHeight: '1.9', marginTop: '40px', marginBottom: '56px' }}>
              The American promise does not end at the edge of the screen.
              The next republic must be readable, inspectable, and accountable.
              Popular sovereignty must survive the digital universe.
            </p>

            <div className="closing-cta-row">
              <a
                href="https://github.com/Sovereign-Data-Foundation/truealphaspiral-ethent"
                className="btn btn-primary"
              >
                View the Restoration Framework
              </a>
              <a href="#we-the-people" className="btn">
                Verify a Receipt
              </a>
              <a href="#what-is-tas" className="btn">
                Read the Technical Addendum
              </a>
            </div>
          </div>
        </div>
      </section>

      <footer className="footer">
        <div className="container">
          <div className="footer-inner">
            <div>
              &copy; 2026 Russell Nordland &nbsp;·&nbsp; TrueAlphaSpiral (TAS) &nbsp;·&nbsp; Sovereign Data Foundation
            </div>
            <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
              <Link to="/vineyard" style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'rgba(0,240,255,0.75)',
                textDecoration: 'none',
                border: '1px solid rgba(0,240,255,0.22)',
                padding: '6px 14px',
                borderRadius: '5px',
                transition: 'color 0.2s, border-color 0.2s',
              }}>
                Seed to Sip: The TAS Vineyard Chain →
              </Link>
              <Link to="/receipts" style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'rgba(0,240,255,0.75)',
                textDecoration: 'none',
                border: '1px solid rgba(0,240,255,0.22)',
                padding: '6px 14px',
                borderRadius: '5px',
                transition: 'color 0.2s, border-color 0.2s',
              }}>
                Verify a Receipt →
              </Link>
              <Link to="/restoration-framework" style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'rgba(0,240,255,0.75)',
                textDecoration: 'none',
                border: '1px solid rgba(0,240,255,0.22)',
                padding: '6px 14px',
                borderRadius: '5px',
                transition: 'color 0.2s, border-color 0.2s',
              }}>
                Restoration Framework →
              </Link>
              <Link to="/singularity" style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'rgba(160,120,255,0.75)',
                textDecoration: 'none',
                border: '1px solid rgba(160,120,255,0.22)',
                padding: '6px 14px',
                borderRadius: '5px',
                transition: 'color 0.2s, border-color 0.2s',
              }}>
                The Singularity →
              </Link>
              <Link to="/echosystem" style={{
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: 'rgba(0,240,180,0.75)',
                textDecoration: 'none',
                border: '1px solid rgba(0,240,180,0.22)',
                padding: '6px 14px',
                borderRadius: '5px',
                transition: 'color 0.2s, border-color 0.2s',
              }}>
                The Echosystem →
              </Link>
              <a href="https://github.com/Sovereign-Data-Foundation/truealphaspiral-ethent" className="text-dim">GitHub</a>
              <span className="text-dim">Apache-2.0</span>
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
