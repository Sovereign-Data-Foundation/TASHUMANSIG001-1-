import React from 'react';
import { Link } from 'react-router-dom';
import './RestorationFramework.css';

const THREAT_PATTERNS = [
  {
    id: '01',
    title: 'An Unlabeled State Space',
    body: [
      'An autonomous agent can jump between radically different repository states — branches, detached HEAD, forced resets — while believing it is "just committing progress."',
      'History-rewriting operations (rebase, filter-branch, reset, push --force) mutate the commit graph in ways that are extremely hard for a policy learned from shallow examples to model correctly.',
      'The same textual working tree can correspond to multiple distinct histories. The true state includes the whole commit graph plus refs and remotes. The agent often only sees files on disk.',
    ],
  },
  {
    id: '02',
    title: 'Silent Security Regressions',
    body: [
      'An agent can resurrect credentials or secrets from old commits while "refactoring history," re-introducing vulnerabilities that were considered resolved.',
      'When coding agents are tied into CI/CD and deployment, Git becomes the control API for the software supply chain.',
    ],
  },
  {
    id: '03',
    title: 'Supply-Chain Compromise',
    body: [
      'If an attacker influences the agent, they can cause it to pick specific branches or SHAs that contain backdoored code while "cleaning up."',
      'The agent has no invariant model of which refs are trusted, which histories are authorised, or what a forced reset implies for downstream consumers.',
    ],
  },
  {
    id: '04',
    title: 'Loss of Provenance',
    body: [
      'Aggressive rewriting by agents destroys the ability to reason about origin and authorship. Rollbacks become impossible if the clean point has been erased.',
      'Most present-day coding agents treat Git as a string interface — they execute commands without understanding the underlying state machine and mimic "fix it" behaviors without understanding global consequences.',
    ],
  },
];

const GUARDS = [
  {
    label: 'Formalized Git Model',
    body: 'Treat commits, refs, and reflogs as nodes in a constrained graph with defined invariants — not as a shell command surface.',
  },
  {
    label: 'Runtime Guards (GitActionGuard)',
    body: 'No direct shell authority. High-level operations compiled down to vetted state transitions. Automatic rejection of invariant violations — e.g., force-pushing to main.',
  },
  {
    label: 'Provenance-Aware Reasoning',
    body: "The agent's internal state must include the commit DAG and policy status, allowing it to recognize when an action moves it into an unsafe region of the graph.",
  },
];

export default function RestorationFramework() {
  return (
    <div className="rf-page">
      <div className="rf-glow-tl" />
      <div className="rf-glow-br" />

      <div className="rf-container">

        {/* Back */}
        <div className="rf-back-row">
          <Link to="/" className="rf-back-btn">← Return to Digital Sovereignty</Link>
        </div>

        {/* Header */}
        <div className="rf-kicker">TrueAlphaSpiral · Restoration Framework</div>
        <h1 className="rf-h1">The Hidden State Spaces of Git</h1>
        <p className="rf-subtitle">
          Why nobody knows — and why <strong>Sovereignty resides in the Wake.</strong>
        </p>

        {/* ── Product vs Process ── */}
        <section className="rf-section">
          <h2 className="rf-h2"><span>The Product vs. The Process</span></h2>
          <p className="rf-body">
            Modern DevOps tools — GitHub, VS Code, CI/CD pipelines — are built on a fundamental
            bias: <strong>Product over Process.</strong> They treat the commit as the final truth.
            They treat the process of getting there as noise to be squashed, rebased, and
            garbage-collected. The UI actively hides these states to reduce cognitive load,
            presenting a linear, sanitized narrative of development.
          </p>

          {/* Two-model comparison */}
          <div className="rf-model-compare">
            <div className="rf-model rf-model-git">
              <div className="rf-model-label">Git Model</div>
              <div className="rf-model-statement">
                "History is what you agreed to keep."
              </div>
              <div className="rf-model-sub">Sanitized Result</div>
              <ul className="rf-model-list">
                <li>Experimental branches → squashed</li>
                <li>Amended commits → overwritten</li>
                <li>Reflog expires in 90 days</li>
                <li>Dangling objects pruned by <code>git gc</code></li>
              </ul>
            </div>
            <div className="rf-model-divider">↔</div>
            <div className="rf-model rf-model-tas">
              <div className="rf-model-label">TAS Model</div>
              <div className="rf-model-statement">
                "History is everything that happened."
              </div>
              <div className="rf-model-sub">Cryptographic Trajectory</div>
              <ul className="rf-model-list">
                <li>Every draft committed to the wake</li>
                <li>Rejected paradoxes logged permanently</li>
                <li>Drift corrections preserved immutably</li>
                <li>Provenance anchored at A₀</li>
              </ul>
            </div>
          </div>
        </section>

        {/* ── Three Hidden Spaces ── */}
        <section className="rf-section">
          <h2 className="rf-h2"><span>The Three Hidden Spaces</span></h2>

          <div className="rf-hidden-grid">
            <div className="rf-hidden-card rf-hidden-hi">
              <div className="rf-hidden-icon">⟳</div>
              <div className="rf-hidden-name">The Reflog</div>
              <div className="rf-hidden-tagline">The True "Wake"</div>
              <p className="rf-hidden-body">
                <code>git reflog</code> tracks every movement of the HEAD pointer — including
                commits that were "deleted" or amended. It is local-only and expires after 90 days.
              </p>
              <div className="rf-hidden-tas">
                <strong>TAS View:</strong> The reflog is a primitive, ephemeral form of the
                Paradata Wake. In TAS, we make this wake{' '}
                <em>permanent, immutable, and cryptographic.</em> The deleted draft is as important
                as the final commit — it proves the intent and trajectory of the agent.
              </div>
            </div>

            <div className="rf-hidden-card">
              <div className="rf-hidden-icon">◎</div>
              <div className="rf-hidden-name">The Object Database</div>
              <div className="rf-hidden-tagline">The Subconscious</div>
              <p className="rf-hidden-body">
                <code>.git/objects</code> stores every file version (blob) and directory structure
                (tree) ever staged, addressed by SHA-1. Objects become "dangling" once a ref moves
                away. <code>git gc</code> eventually prunes them.
              </p>
              <div className="rf-hidden-tas">
                <strong>TAS View:</strong> This corresponds to the unsequenced biological tissue in
                the TAS Shadow Scan — "Shadow Code" that exists in the machine's subconscious but
                is not part of the Living Braid (the reachable graph).
              </div>
            </div>

            <div className="rf-hidden-card">
              <div className="rf-hidden-icon">▤</div>
              <div className="rf-hidden-name">The Index</div>
              <div className="rf-hidden-tagline">The Staging Layer</div>
              <p className="rf-hidden-body">
                The staging area is a mutable buffer between the working tree and the commit graph.
                Its contents represent intent that has not yet been anchored to a receipt.
              </p>
              <div className="rf-hidden-tas">
                <strong>TAS View:</strong> Unanchored intent is inadmissible under Axiom P₁.
                Every staged change must pass the Logos gate before it is committed to the wake.
              </div>
            </div>
          </div>
        </section>

        {/* ── Paradata Paradigm Shift ── */}
        <section className="rf-section rf-section-accent">
          <div className="rf-paradigm-row">
            <div className="rf-paradigm-quote">
              We expose the hidden state space because{' '}
              <strong>Sovereignty resides in the Wake.</strong>
            </div>
            <div className="rf-paradigm-body">
              To prove an agent acted ethically, you cannot just look at the final output.
              You must verify the <em>rejected paradoxes</em> and the{' '}
              <em>drift corrections</em> that happened in the hidden states.
              <br /><br />
              <strong>The Hidden State Space is the repository of Why.</strong>
            </div>
          </div>
        </section>

        {/* ── Threat Patterns ── */}
        <section className="rf-section">
          <h2 className="rf-h2">
            <span>Why The Hidden State Space Is Dangerous</span> to Autonomous Agents
          </h2>
          <p className="rf-body">
            When coding agents operate inside Git without a correct model of its hidden state space,
            you have given them a loaded weapon with no concept of where the barrel is pointing.
          </p>

          <div className="rf-threats">
            {THREAT_PATTERNS.map(t => (
              <div key={t.id} className="rf-threat">
                <div className="rf-threat-id">{t.id}</div>
                <div>
                  <div className="rf-threat-title">{t.title}</div>
                  {t.body.map((line, i) => (
                    <p key={i} className="rf-threat-body">{line}</p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* ── Toward a Safer Design ── */}
        <section className="rf-section">
          <h2 className="rf-h2"><span>Toward a Safer Design</span> — GitActionGuard</h2>
          <p className="rf-body">
            TAS requires that autonomous agents operating in version-controlled environments
            treat the commit graph as a first-class constrained system — not a shell command
            surface.
          </p>

          <div className="rf-guards">
            {GUARDS.map((g, i) => (
              <div key={i} className="rf-guard">
                <div className="rf-guard-num">0{i + 1}</div>
                <div>
                  <div className="rf-guard-label">{g.label}</div>
                  <div className="rf-guard-body">{g.body}</div>
                </div>
              </div>
            ))}
          </div>

          {/* Code block */}
          <div className="rf-code-block">
            <div className="rf-code-label">GitActionGuard — Invariant Boundaries</div>
            <pre className="rf-code">{`# Protected invariants — any violation triggers Phoenix Circuit
INVARIANTS = [
    "never rewrite protected branches (main, release/*)",
    "never deploy from unverified refs",
    "never push --force without human-authorised HCS token",
    "all commits must carry wake-chain receipt hash in trailer",
    "dangling blobs ≥ 7 days old → Shadow Scan before gc",
]

# Every Git operation is compiled to a vetted state transition
class GitActionGuard:
    def commit(self, message, staged_paths):
        self.logos_gate(staged_paths)      # P1 admissibility
        receipt = self.wake.commit(...)    # anchor to wake chain
        return self._exec("git commit",
                          trailer=f"TAS-Receipt: {receipt.receipt_hash().hex()}")`}
            </pre>
          </div>
        </section>

        {/* ── Closing anchor ── */}
        <section className="rf-section rf-section-closing">
          <div className="rf-closing-grid">
            <div className="rf-closing-left">
              <div className="rf-closing-label">The Genesis Anchor</div>
              <div className="rf-closing-a0">A₀</div>
              <p className="rf-closing-body">
                Every commit graph, every object database, every staged file traces back
                to a Prime Invariant. The restoration framework makes that lineage
                visible, permanent, and cryptographically provable.
              </p>
            </div>
            <div className="rf-closing-right">
              <blockquote className="rf-quote">
                "The Chain of Mirrors does not hide what was tried and discarded.
                It is a complete record of every reflection — admitted and refused —
                from seed to sip, from intent to execution."
              </blockquote>
              <div className="rf-closing-links">
                <Link to="/receipts" className="rf-nav-link">Verify a Receipt →</Link>
                <Link to="/vineyard" className="rf-nav-link">Vineyard Chain →</Link>
              </div>
            </div>
          </div>
        </section>

        {/* Footer */}
        <footer className="rf-footer">
          <span>© 2026 Russell Nordland · TrueAlphaSpiral (TAS) · Sovereign Data Foundation</span>
          <Link to="/" className="rf-back-btn">← Return to Digital Sovereignty</Link>
        </footer>

      </div>
    </div>
  );
}
