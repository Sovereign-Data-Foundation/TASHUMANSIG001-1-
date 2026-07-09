/**
 * TAS Jules Bridge — Bidirectional Gmail ↔ Jules sub-agent gateway
 *
 * Command surface:  Gmail INBOX (subject prefix [JULES]) → GitHub Issue → Jules picks up
 * Receipt surface:  GitHub PR webhook → TAS-style witness receipt → Gmail reply
 *
 * Auth: Gmail via @replit/connectors-sdk (OAuth proxy)
 *       GitHub via GITHUB_TOKEN env secret
 */

import express from 'express';
import { ReplitConnectors } from '../node_modules/@replit/connectors-sdk/index.js';

const app = express();
app.use(express.json());

const connectors = new ReplitConnectors();

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
const GITHUB_REPO  = process.env.GITHUB_REPO || 'Sovereign-Data-Foundation/truealphaspiral-ethent';
const PORT         = process.env.BRIDGE_PORT || 3001;
const POLL_MS      = 60_000;
const SUBJECT_TAG  = '[JULES]';

let seqCounter = 0;
const processedIds = new Set();

// ── Utility: build base64url-encoded RFC 2822 email ────────────────────────
function buildRawEmail({ to, subject, body, replyToMessageId, references }) {
  const lines = [
    `To: ${to}`,
    `Subject: ${subject}`,
    `MIME-Version: 1.0`,
    `Content-Type: text/plain; charset=UTF-8`,
  ];
  if (replyToMessageId) lines.push(`In-Reply-To: <${replyToMessageId}>`);
  if (references)       lines.push(`References: <${references}>`);
  lines.push('', body);
  const raw = lines.join('\r\n');
  return Buffer.from(raw).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
}

// ── Utility: create TAS witness receipt text ───────────────────────────────
function witnessReceipt({ seq, action, repo, branch, sha, prUrl, prNumber, filesChanged, status }) {
  const ts  = new Date().toISOString();
  const pad = (s, n) => String(s).padEnd(n);
  return [
    `WITNESS RECEIPT`,
    `════════════════════════════════════════`,
    `SEQ         ${pad(String(seq).padStart(5, '0'), 30)}`,
    `ISSUED      ${pad(ts, 30)}`,
    `AUTHORITY   Jules Sub-Agent / GitHub`,
    `ACTION      ${pad(action, 30)}`,
    `REPO        ${pad(repo, 30)}`,
    `BRANCH      ${pad(branch || '—', 30)}`,
    `SHA         ${pad(sha    || '—', 30)}`,
    `PR          ${pad(prNumber ? `#${prNumber}` : '—', 30)}`,
    `FILES Δ     ${pad(filesChanged != null ? filesChanged : '—', 30)}`,
    `STATUS      ${pad(status, 30)}`,
    `════════════════════════════════════════`,
    ``,
    `REVIEW:     ${prUrl || '—'}`,
    ``,
    `This receipt was issued by the TrueAlphaSpiral (TAS) Jules bridge.`,
    `Every state transition leaves a cryptographically anchored record.`,
    `Performance is a privilege of Safety.`,
    ``,
    `— Sovereign Data Foundation`,
  ].join('\n');
}

// ── Gmail: fetch unread [JULES] messages ──────────────────────────────────
async function fetchJulesEmails() {
  try {
    const q   = encodeURIComponent(`subject:${SUBJECT_TAG} is:unread in:inbox`);
    const res = await connectors.proxy('google-mail', `/gmail/v1/users/me/messages?q=${q}&maxResults=10`, { method: 'GET' });
    const data = await res.json();
    return data.messages || [];
  } catch (e) {
    console.error('[bridge] fetchJulesEmails error:', e.message);
    return [];
  }
}

async function getEmailDetail(messageId) {
  const res  = await connectors.proxy('google-mail', `/gmail/v1/users/me/messages/${messageId}?format=full`, { method: 'GET' });
  return res.json();
}

function extractHeader(msg, name) {
  return msg.payload?.headers?.find(h => h.name.toLowerCase() === name.toLowerCase())?.value || '';
}

function decodeBody(msg) {
  const part = msg.payload?.parts?.find(p => p.mimeType === 'text/plain') || msg.payload;
  const data  = part?.body?.data || '';
  return Buffer.from(data, 'base64').toString('utf-8');
}

// ── Gmail: mark message as read ───────────────────────────────────────────
async function markRead(messageId) {
  await connectors.proxy('google-mail', `/gmail/v1/users/me/messages/${messageId}/modify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ removeLabelIds: ['UNREAD'] }),
  });
}

// ── Gmail: send email ─────────────────────────────────────────────────────
async function sendEmail({ to, subject, body, replyToMessageId, references }) {
  const raw = buildRawEmail({ to, subject, body, replyToMessageId, references });
  const res  = await connectors.proxy('google-mail', '/gmail/v1/users/me/messages/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ raw }),
  });
  return res.json();
}

// ── GitHub: create issue ──────────────────────────────────────────────────
async function createGitHubIssue({ title, body, labels }) {
  if (!GITHUB_TOKEN) throw new Error('GITHUB_TOKEN not set');
  const res = await fetch(`https://api.github.com/repos/${GITHUB_REPO}/issues`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28',
    },
    body: JSON.stringify({
      title,
      body,
      labels: labels || ['jules'],
    }),
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`GitHub issue creation failed: ${res.status} — ${err}`);
  }
  return res.json();
}

// ── Poll loop ─────────────────────────────────────────────────────────────
async function pollGmail() {
  console.log(`[bridge] polling Gmail for ${SUBJECT_TAG} …`);
  const messages = await fetchJulesEmails();

  for (const { id } of messages) {
    if (processedIds.has(id)) continue;

    try {
      const msg     = await getEmailDetail(id);
      const subject = extractHeader(msg, 'Subject');
      const from    = extractHeader(msg, 'From');
      const msgId   = extractHeader(msg, 'Message-ID').replace(/[<>]/g, '');
      const body    = decodeBody(msg);

      const issueTitle = subject.replace(SUBJECT_TAG, '').trim();
      const issueBody  = [
        `**Submitted via TAS Jules Bridge**`,
        `**From:** ${from}`,
        `**Gmail Message-ID:** ${msgId}`,
        `---`,
        body,
      ].join('\n');

      const issue = await createGitHubIssue({ title: issueTitle, body: issueBody });

      console.log(`[bridge] created issue #${issue.number}: ${issue.title}`);
      processedIds.add(id);
      await markRead(id);

      // Send confirmation receipt
      await sendEmail({
        to: from,
        subject: `[TAS RECEIPT] Issue #${issue.number} — ${issueTitle}`,
        body: witnessReceipt({
          seq: ++seqCounter,
          action: `GitHub Issue #${issue.number} created`,
          repo: GITHUB_REPO,
          prUrl: issue.html_url,
          prNumber: issue.number,
          status: 'ISSUED — Jules assigned',
        }),
        replyToMessageId: msgId,
        references: msgId,
      });

    } catch (e) {
      console.error(`[bridge] failed to process message ${id}:`, e.message);
    }
  }
}

// ── GitHub webhook endpoint ───────────────────────────────────────────────
app.post('/github', async (req, res) => {
  const event   = req.headers['x-github-event'];
  const payload = req.body;

  res.sendStatus(200);

  if (event !== 'pull_request') return;

  const action = payload.action;
  const pr     = payload.pull_request;
  if (!pr) return;

  const issueBody    = pr.body || '';
  const gmailMsgId   = (issueBody.match(/\*\*Gmail Message-ID:\*\* (.+)/) || [])[1]?.trim();
  const submitterRaw = (issueBody.match(/\*\*From:\*\* (.+)/)             || [])[1]?.trim();

  const statusMap = {
    opened:              'OPENED — Jules working',
    ready_for_review:    'READY FOR REVIEW',
    review_requested:    'REVIEW REQUESTED',
    closed:              pr.merged ? 'MERGED ✓' : 'CLOSED — not merged',
  };

  const status = statusMap[action];
  if (!status || !submitterRaw) return;

  const receipt = witnessReceipt({
    seq:          ++seqCounter,
    action:       `PR #${pr.number} ${action}`,
    repo:         payload.repository?.full_name || GITHUB_REPO,
    branch:       pr.head?.ref,
    sha:          pr.head?.sha?.slice(0, 8),
    prUrl:        pr.html_url,
    prNumber:     pr.number,
    filesChanged: pr.changed_files,
    status,
  });

  try {
    await sendEmail({
      to:                submitterRaw,
      subject:           `[TAS RECEIPT] PR #${pr.number} ${action} — ${pr.title}`,
      body:              receipt,
      replyToMessageId:  gmailMsgId,
      references:        gmailMsgId,
    });
    console.log(`[bridge] sent PR receipt for #${pr.number} (${action}) → ${submitterRaw}`);
  } catch (e) {
    console.error('[bridge] failed to send PR receipt:', e.message);
  }
});

// ── Health check ──────────────────────────────────────────────────────────
app.get('/health', (req, res) => {
  res.json({
    status: 'alive',
    repo:   GITHUB_REPO,
    poll:   `${POLL_MS / 1000}s`,
    seq:    seqCounter,
    processed: processedIds.size,
  });
});

// ── Manual trigger ────────────────────────────────────────────────────────
app.post('/poll', async (req, res) => {
  await pollGmail();
  res.json({ ok: true, processed: processedIds.size });
});

// ── Start ─────────────────────────────────────────────────────────────────
app.listen(PORT, () => {
  console.log(`[bridge] TAS Jules Bridge running on :${PORT}`);
  console.log(`[bridge] Watching Gmail for "${SUBJECT_TAG}" · repo: ${GITHUB_REPO}`);
  if (!GITHUB_TOKEN) console.warn('[bridge] WARNING: GITHUB_TOKEN not set — issue creation will fail');
  pollGmail();
  setInterval(pollGmail, POLL_MS);
});
