const els = {
  totalJobs: document.querySelector('#totalJobs'),
  reviewCount: document.querySelector('#reviewCount'),
  skipCount: document.querySelector('#skipCount'),
  humanCount: document.querySelector('#humanCount'),
  decisionCard: document.querySelector('#decisionCard'),
  evidenceBody: document.querySelector('#evidenceBody'),
  reviewJobs: document.querySelector('#reviewJobs'),
  skipJobs: document.querySelector('#skipJobs'),
  reviewBadge: document.querySelector('#reviewBadge'),
  skipBadge: document.querySelector('#skipBadge'),
  rerun: document.querySelector('#rerun'),
  tracePanel: document.querySelector('#tracePanel'),
  traceTitle: document.querySelector('#traceTitle'),
  traceDecision: document.querySelector('#traceDecision'),
  traceAuthorized: document.querySelector('#traceAuthorized'),
  traceId: document.querySelector('#traceId'),
};

let surfacedJob = null;

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function renderQueue(target, items) {
  target.innerHTML = items.map((item) => {
    const a = item.assessment;
    return `
      <div class="queue-job">
        <div>
          <div class="queue-job-title">${escapeHtml(a.title)}</div>
          <div class="queue-job-company">${escapeHtml(a.company)}</div>
        </div>
        <div class="queue-score">fit ${escapeHtml(a.fit_score)}</div>
      </div>`;
  }).join('');
}

function renderEvidence(assessment) {
  const matched = assessment.matched_skills.length
    ? assessment.matched_skills.map((skill) => `<span class="skill good">${escapeHtml(skill)}</span>`).join('')
    : '<span class="skill">No matched skills</span>';

  const missing = assessment.missing_skills.length
    ? assessment.missing_skills.join(', ')
    : 'None';

  els.evidenceBody.innerHTML = `
    <div class="evidence-list">
      <div class="evidence-item"><span>MATCHED SKILLS</span><div class="skill-row">${matched}</div></div>
      <div class="evidence-item"><span>MISSING MUST-HAVES</span>${escapeHtml(missing)}</div>
      <div class="evidence-item"><span>TOOL RECOMMENDATION</span>${escapeHtml(assessment.recommendation)}</div>
    </div>`;
}

function renderDecision(item) {
  surfacedJob = item;
  const a = item.assessment;
  const skills = a.matched_skills.map((skill) => `<span class="skill good">${escapeHtml(skill)}</span>`).join('');
  els.decisionCard.innerHTML = `
    <div class="decision-kicker">
      <span class="decision-badge">HUMAN DECISION REQUIRED</span>
      <div class="fit-ring">${escapeHtml(a.fit_score)}</div>
    </div>
    <div class="job-company">${escapeHtml(a.company)}</div>
    <h3 class="job-title">${escapeHtml(a.title)}</h3>
    <p class="job-reason">${escapeHtml(a.reason)}</p>
    <div class="skill-row">${skills}</div>
    <div class="actions">
      <button class="action primary" data-decision="APPLY">APPLY</button>
      <button class="action" data-decision="SKIP">SKIP</button>
      <button class="action" data-decision="WHY">WHY?</button>
    </div>`;

  renderEvidence(a);
  els.decisionCard.querySelectorAll('[data-decision]').forEach((button) => {
    button.addEventListener('click', () => submitDecision(button.dataset.decision));
  });
}

function renderEmptyDecision() {
  surfacedJob = null;
  els.decisionCard.innerHTML = `
    <div class="loading">No opportunity currently requires a human decision.</div>`;
}

function renderTrace(result) {
  els.tracePanel.classList.remove('hidden');
  els.traceTitle.textContent = result.decision === 'WHY' ? 'Explanation request recorded' : 'Human decision recorded';
  els.traceDecision.textContent = result.decision;
  els.traceAuthorized.textContent = result.application_authorized ? 'YES' : 'NO';
  els.traceId.textContent = result.trace_id;

  if (result.decision === 'WHY') {
    const explanation = result.explanation;
    els.evidenceBody.innerHTML = `
      <p>${escapeHtml(explanation.reason)}</p>
      <div class="evidence-list">
        <div class="evidence-item"><span>MATCHED SKILLS</span>${escapeHtml(explanation.matched_skills.join(', ') || 'None')}</div>
        <div class="evidence-item"><span>MISSING MUST-HAVES</span>${escapeHtml(explanation.missing_skills.join(', ') || 'None')}</div>
        <div class="evidence-item"><span>TRACE ARTIFACT</span>${escapeHtml(result.artifact_path)}</div>
      </div>`;
  }
}

async function submitDecision(decision) {
  if (!surfacedJob) return;
  const buttons = els.decisionCard.querySelectorAll('button');
  buttons.forEach((button) => button.disabled = true);

  try {
    const response = await fetch('/api/decision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        job_id: surfacedJob.job_id,
        decision,
        rationale: decision === 'APPLY'
          ? 'Strong evidence-backed fit; human chose to authorize the next application step.'
          : decision === 'SKIP'
            ? 'Human chose not to pursue this opportunity.'
            : 'Human requested the evidence behind this recommendation.',
      }),
    });

    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || 'Decision request failed');
    renderTrace(result);
  } catch (error) {
    els.tracePanel.classList.remove('hidden');
    els.traceTitle.textContent = 'Decision failed';
    els.traceDecision.textContent = 'ERROR';
    els.traceAuthorized.textContent = 'NO';
    els.traceId.textContent = error.message;
  } finally {
    buttons.forEach((button) => button.disabled = false);
  }
}

async function loadTriage() {
  els.rerun.disabled = true;
  els.rerun.textContent = 'Running…';
  els.tracePanel.classList.add('hidden');

  try {
    const response = await fetch('/api/triage');
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || 'Triage failed');

    els.totalJobs.textContent = data.total_jobs;
    els.reviewCount.textContent = data.counts.review;
    els.skipCount.textContent = data.counts.skipped;
    els.humanCount.textContent = data.counts.surfaced;
    els.reviewBadge.textContent = data.counts.review;
    els.skipBadge.textContent = data.counts.skipped;

    renderQueue(els.reviewJobs, data.review);
    renderQueue(els.skipJobs, data.skipped);
    data.surfaced.length ? renderDecision(data.surfaced[0]) : renderEmptyDecision();
  } catch (error) {
    els.decisionCard.innerHTML = `<div class="loading">${escapeHtml(error.message)}</div>`;
  } finally {
    els.rerun.disabled = false;
    els.rerun.textContent = 'Run triage';
  }
}

els.rerun.addEventListener('click', loadTriage);
loadTriage();
