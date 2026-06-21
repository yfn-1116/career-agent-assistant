const API = 'http://127.0.0.1:8765';

document.getElementById('analyzeBtn').addEventListener('click', async () => {
  const status = document.getElementById('status');
  const result = document.getElementById('result');
  status.textContent = 'Reading page...';

  // Get page data from content script
  chrome.tabs.query({active: true, currentWindow: true}, async (tabs) => {
    try {
      const response = await chrome.tabs.sendMessage(tabs[0].id, {type: 'get_page_data'});
      status.textContent = 'Analyzing...';
      const res = await fetch(`${API}/api/browser/analyze-current-page`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(response || {text: '', url: tabs[0].url, title: tabs[0].title})
      });
      const data = await res.json();
      renderResult(data);
      status.textContent = 'Done';
    } catch (e) {
      status.textContent = 'Error: Is the local API running? (uvicorn career_agent.api.app:app --port 8765)';
      result.innerHTML = `<p class="warn">Cannot reach local API at ${API}</p>`;
    }
  });
});

function renderResult(data) {
  const r = document.getElementById('result');
  let html = '';
  if (data.job_posting) {
    html += `<div class="score">${data.job_posting.job_title || 'Job'} @ ${data.job_posting.company || '?'}</div>`;
    html += `<div><span class="label">Match:</span> ${(data.match_score*100).toFixed(0)}% | <span class="label">Intent:</span> ${(data.hiring_intent_score*100).toFixed(0)}% | <span class="label">Opportunity:</span> ${(data.opportunity_score*100).toFixed(0)}%</div>`;
    html += `<div><span class="label">Action:</span> <b>${data.recommended_action}</b></div>`;
  }
  if (data.message_draft) {
    html += `<div class="msg-box">${data.message_draft.text || ''}</div>`;
    html += `<button class="copy-btn" onclick="navigator.clipboard.writeText('${(data.message_draft.text||'').replace(/'/g,"\\'")}')">📋 Copy Message</button>`;
  }
  if (data.verification_questions && data.verification_questions.length) {
    html += '<div style="margin-top:8px"><span class="label">Verification:</span><ul style="margin:4px 0;padding-left:16px">';
    data.verification_questions.forEach(q => html += `<li>${q}</li>`);
    html += '</ul></div>';
  }
  if (data.ranked_jobs && data.ranked_jobs.length) {
    html += '<div style="margin-top:8px"><span class="label">Top Jobs:</span>';
    data.ranked_jobs.forEach((j,i) => html += `<div>${i+1}. ${j.job_title} @ ${j.company} (${(j.match_score*100).toFixed(0)}%)</div>`);
    html += '</div>';
  }
  if (data.reply_suggestion) {
    html += `<div class="msg-box">${data.reply_suggestion.suggested_reply || ''}</div>`;
    html += `<button class="copy-btn" onclick="navigator.clipboard.writeText('${(data.reply_suggestion.suggested_reply||'').replace(/'/g,"\\'")}')">📋 Copy Reply</button>`;
  }
  if (data.warnings && data.warnings.length) {
    data.warnings.forEach(w => html += `<p class="warn">⚠️ ${w}</p>`);
  }
  html += `<div style="margin-top:8px"><span class="label">Next:</span> ${data.next_action || 'N/A'}</div>`;
  r.innerHTML = html || '<p>No results. Try a job detail or chat page.</p>';
}

// Listen for page data from content script
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === 'page_data') {
    document.getElementById('status').textContent = 'Page loaded: ' + (msg.data.title || '').substring(0, 30);
  }
});
