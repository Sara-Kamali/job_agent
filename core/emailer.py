"""
emailer.py — Builds the job digest and opens it as an HTML file in the browser
"""
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import List, Dict


OUTPUT_DIR = Path(__file__).parent.parent / "output" / "digests"


def score_bar(score: float) -> str:
    filled = round(score * 10)
    return "█" * filled + "░" * (10 - filled)


def score_color(score: float) -> str:
    if score >= 0.80:
        return "#16a34a"  # green
    elif score >= 0.65:
        return "#d97706"  # amber
    else:
        return "#6b7280"  # gray


from core.filters import MATCH_THRESHOLD


def _render_job_card(job: Dict) -> str:
    import json as _json
    score = job.get("match_score", 0.0)
    pct = int(score * 100)
    color = score_color(score)
    bar = score_bar(score)
    job_id_js = _json.dumps(job.get("id", ""))
    _raw_id = str(job.get("id", ""))
    job_id_onclick = "'" + _raw_id.replace("\\", "\\\\").replace("'", "\\'") + "'"

    desc = job.get("description", "")
    snippet = (desc[:220] + "…") if len(desc) > 220 else desc
    snippet_html = (
        f'<p style="margin:8px 0 4px;font-size:13px;color:#374151;'
        f'line-height:1.5;background:#f9fafb;padding:8px 10px;border-radius:6px;">'
        f'{snippet}</p>'
    ) if snippet else ""

    missing = job.get("missing_skills", [])
    missing_html = ""
    if missing:
        tags = "".join(
            f'<span style="display:inline-block;background:#fef3c7;color:#92400e;'
            f'font-size:11px;padding:2px 8px;border-radius:10px;margin:2px;">{s}</span>'
            for s in missing[:5]
        )
        missing_html = f'<p style="margin:6px 0 0;font-size:12px;color:#6b7280;">Gaps: {tags}</p>'

    matching = job.get("matching_skills", [])
    matching_html = ""
    if matching:
        tags = "".join(
            f'<span style="display:inline-block;background:#d1fae5;color:#065f46;'
            f'font-size:11px;padding:2px 8px;border-radius:10px;margin:2px;">{s}</span>'
            for s in matching[:6]
        )
        matching_html = f'<p style="margin:6px 0 0;font-size:12px;color:#6b7280;">Matches: {tags}</p>'

    reason = job.get("reason", "")
    source_badge = (
        f'<span style="background:#e0e7ff;color:#3730a3;font-size:11px;'
        f'padding:2px 8px;border-radius:10px;">{job.get("source","").upper()}</span>'
    )
    threshold_badge = (
        f'<span style="background:#dcfce7;color:#166534;font-size:11px;'
        f'padding:2px 8px;border-radius:10px;">Good match</span>'
        if score >= MATCH_THRESHOLD else
        f'<span style="background:#f3f4f6;color:#6b7280;font-size:11px;'
        f'padding:2px 8px;border-radius:10px;">Below threshold</span>'
    )
    return f"""
    <div class="job-card" data-job-id={job_id_js} style="border:1px solid #e5e7eb;border-radius:12px;padding:18px;margin:0 0 14px;
                background:#ffffff;border-left:4px solid {color};opacity:1;
                transition:opacity 0.2s;">
      <div style="display:flex;align-items:flex-start;gap:12px;">
        <label style="display:flex;align-items:center;margin-top:3px;cursor:pointer;flex-shrink:0;"
               title="Select this job">
          <input type="checkbox" class="job-select"
                 data-job-id={job_id_js}
                 onchange="updateSelection()"
                 style="width:18px;height:18px;cursor:pointer;accent-color:#dc2626;">
        </label>
        <div style="flex:1;min-width:0;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <div style="min-width:0;">
              <h3 style="margin:0 0 4px;font-size:16px;color:#111827;">{job.get('title','')}</h3>
              <p style="margin:0;color:#4b5563;font-size:13px;">
                {job.get('company','')} &nbsp;·&nbsp; {job.get('location','')}
              </p>
            </div>
            <div style="text-align:right;flex-shrink:0;margin-left:12px;">
              <span style="font-size:22px;font-weight:700;color:{color};">{pct}%</span>
              <p style="margin:2px 0 0;font-family:monospace;font-size:10px;color:{color};">{bar}</p>
            </div>
          </div>
          <p style="margin:10px 0 4px;font-size:13px;color:#6b7280;font-style:italic;">{reason}</p>
          {snippet_html}
          {matching_html}
          {missing_html}
          <div style="margin-top:12px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
            {source_badge}
            {threshold_badge}
            <a href="{job.get('url','#')}" target="_blank" rel="noopener noreferrer"
               onclick="markViewed({job_id_onclick}, this)"
               style="background:#2563eb;color:#fff;padding:6px 16px;border-radius:8px;
                      text-decoration:none;font-size:13px;font-weight:500;">
              View Job →
            </a>
          </div>
        </div>
      </div>
    </div>
    """


def build_html(jobs: List[Dict]) -> str:
    """
    Renders the digest as two columns: New (jobs not yet viewed in a previous
    digest load) and Seen (jobs already shown to you before). Each job dict is
    expected to carry a "viewed" flag (0/1) from the database; jobs without one
    are treated as New.
    """
    now = datetime.now().strftime("%A, %d %B %Y – %H:%M")
    count = len(jobs)
    matched_count = sum(1 for j in jobs if j.get("match_score", 0) >= MATCH_THRESHOLD)

    new_jobs = [j for j in jobs if not j.get("viewed", 0)]
    seen_jobs = [j for j in jobs if j.get("viewed", 0)]

    new_cards = "".join(_render_job_card(j) for j in new_jobs)
    seen_cards = "".join(_render_job_card(j) for j in seen_jobs)

    new_empty = '<p style="text-align:center;color:#6b7280;padding:30px 10px;font-size:13px;">No new jobs since your last visit.</p>'
    seen_empty = '<p style="text-align:center;color:#6b7280;padding:30px 10px;font-size:13px;">Nothing seen yet.</p>'

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="UTF-8">
      <style>
        .digest-columns {{
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 20px;
          align-items: start;
        }}
        @media (max-width: 820px) {{
          .digest-columns {{ grid-template-columns: 1fr; }}
        }}
        .column-scroll {{ max-height: 80vh; overflow-y: auto; padding-right: 4px; }}
      </style>
      <script>
        // Live status poll. NOTE: this deliberately never calls location.reload().
        // Auto-reloading during a scrape was resetting scroll position every few
        // seconds. Instead we show a banner and let YOU choose when to refresh.
        let _baselineCount = null;
        async function _poll() {{
          try {{
            const r = await fetch('/status');
            const s = await r.json();
            if (_baselineCount === null) _baselineCount = s.count;
            const bar = document.getElementById('live-bar');
            const refreshBar = document.getElementById('refresh-bar');
            if (s.processing) {{
              bar.style.display = 'block';
              bar.textContent = 'Scraping in progress\u2026 ' + s.count + ' jobs found so far';
            }} else {{
              bar.style.display = 'none';
            }}
            const _diff = s.count - _baselineCount;
            refreshBar.style.display = 'block';
            refreshBar.textContent = _diff > 0
              ? (_diff + ' new job(s) found \u2014 click here to refresh')
              : '0 new jobs found';
            setTimeout(_poll, 4000);
          }} catch(e) {{ /* server not reachable, stop polling */ }}
        }}
        _poll();

        function updateSelection() {{
          const n = document.querySelectorAll('.job-select:checked').length;
          const toolbar = document.getElementById('select-toolbar');
          const label = document.getElementById('select-count');
          label.textContent = n + ' selected';
          toolbar.style.display = n > 0 ? 'flex' : 'none';
        }}

        function clearSelection() {{
          document.querySelectorAll('.job-select:checked').forEach(cb => cb.checked = false);
          updateSelection();
        }}

        async function deleteSelected() {{
          const boxes = Array.from(document.querySelectorAll('.job-select:checked'));
          if (!boxes.length) return;
          const ids = boxes.map(cb => cb.dataset.jobId);
          if (!confirm('Delete ' + ids.length + ' job(s) from the digest? This cannot be undone.')) return;
          try {{
            const resp = await fetch('/delete', {{
              method: 'POST',
              headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify({{ids: ids}})
            }});
            if (!resp.ok) throw new Error('Server error');
          }} catch(e) {{
            alert('Could not delete. Is the job agent server running?');
            return;
          }}
          boxes.forEach(cb => {{
            const card = cb.closest('.job-card');
            if (!card) return;
            const inNew = !!card.closest('#new-list');
            card.style.transition = 'opacity 0.2s';
            card.style.opacity = '0';
            setTimeout(() => card.remove(), 200);
            const el = document.getElementById(inNew ? 'new-count' : 'seen-count');
            if (el) el.textContent = Math.max(0, parseInt(el.textContent || '0', 10) - 1);
          }});
          setTimeout(() => {{
            const ne = document.getElementById('new-empty');
            const se = document.getElementById('seen-empty');
            if (ne) ne.style.display =
              document.querySelectorAll('#new-list .job-card').length ? 'none' : 'block';
            if (se) se.style.display =
              document.querySelectorAll('#seen-list .job-card').length ? 'none' : 'block';
          }}, 250);
          clearSelection();
        }}

        function clearCache() {{
          if (confirm('Clear all saved preferences and browser cache?')) {{
            localStorage.removeItem('jobAgentConfig');
            alert('Cache cleared. Your preferences have been reset.');
          }}
        }}

        async function markViewed(jobId, linkEl) {{
          // Fire-and-forget: don't block the "View Job" click/new-tab opening.
          try {{
            fetch('/view', {{
              method: 'POST',
              headers: {{'Content-Type': 'application/json'}},
              body: JSON.stringify({{id: jobId}})
            }});
          }} catch (e) {{ /* ignore — worst case it re-appears under New next load */ }}

          const card = linkEl.closest('.job-card');
          if (!card || card.dataset.moved === '1') return;
          card.dataset.moved = '1';

          const newList = document.getElementById('new-list');
          const seenList = document.getElementById('seen-list');
          const newCountEl = document.getElementById('new-count');
          const seenCountEl = document.getElementById('seen-count');
          const newEmpty = document.getElementById('new-empty');
          const seenEmpty = document.getElementById('seen-empty');

          // Slide the card from New into the top of Seen.
          card.style.transition = 'opacity 0.25s';
          card.style.opacity = '0.3';
          setTimeout(() => {{
            seenList.insertBefore(card, seenList.firstChild);
            card.style.opacity = '1';
          }}, 150);

          const newCount = Math.max(0, parseInt(newCountEl.textContent || '0', 10) - 1);
          const seenCount = parseInt(seenCountEl.textContent || '0', 10) + 1;
          newCountEl.textContent = newCount;
          seenCountEl.textContent = seenCount;
          if (newEmpty) newEmpty.style.display = newCount === 0 ? 'block' : 'none';
          if (seenEmpty) seenEmpty.style.display = 'none';
        }}
      </script>
    </head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 background:#f9fafb;margin:0;padding:20px;">
      <div style="max-width:1180px;margin:0 auto;">

        <!-- Live scraping banner -->
        <div id="live-bar" style="display:none;background:#1e3a5f;color:#ffffff;
             border-radius:10px;padding:14px 18px;margin-bottom:12px;
             font-size:16px;font-weight:600;text-align:center;"></div>

        <!-- Manual refresh prompt (replaces the old auto-reload) -->
        <div id="refresh-bar" onclick="location.reload()"
             style="background:#fbbf24;color:#4a2c00;border-radius:10px;
                    padding:16px 20px;margin-bottom:12px;font-size:18px;font-weight:700;
                    text-align:center;cursor:pointer;
                    box-shadow:0 2px 10px rgba(251,191,36,0.45);">0 new jobs found</div>

        <!-- Selection toolbar: appears when jobs are checked -->
        <div id="select-toolbar"
             style="display:none;position:sticky;top:10px;z-index:20;
                    background:#111827;color:#fff;border-radius:10px;
                    padding:10px 16px;margin-bottom:12px;
                    align-items:center;gap:12px;justify-content:space-between;
                    box-shadow:0 4px 12px rgba(0,0,0,0.15);">
          <span id="select-count" style="font-size:13px;font-weight:600;">0 selected</span>
          <span style="display:flex;gap:8px;">
            <button onclick="clearSelection()"
                    style="background:#374151;color:#fff;border:none;padding:6px 14px;
                           border-radius:8px;cursor:pointer;font-size:13px;">Clear</button>
            <button onclick="deleteSelected()"
                    style="background:#dc2626;color:#fff;border:none;padding:6px 16px;
                           border-radius:8px;cursor:pointer;font-size:13px;font-weight:600;">
              🗑 Delete selected</button>
          </span>
        </div>

        <!-- Navigation -->
        <div style="margin-bottom:20px;display:flex;gap:16px;justify-content:space-between;">
          <div style="display:flex;gap:16px;">
            <a href="/digest" style="color:#2563eb;text-decoration:none;font-weight:500;">📊 Job Digest</a>
            <a href="/settings" style="color:#2563eb;text-decoration:none;font-weight:500;">⚙ Settings</a>
          </div>
          <button onclick="clearCache()" style="background:#e74c3c;color:white;border:none;padding:6px 12px;border-radius:6px;cursor:pointer;font-weight:500;font-size:13px;">🗑️ Clear Cache</button>
        </div>

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e3a5f,#2563eb);
                    border-radius:16px;padding:28px;margin-bottom:24px;color:#fff;">
          <h1 style="margin:0 0 6px;font-size:22px;">Job Digest</h1>
          <p style="margin:0;opacity:0.85;font-size:14px;">{now}</p>
          <p style="margin:8px 0 0;font-size:28px;font-weight:700;">{count} job{"s" if count != 1 else ""}</p>
          <p style="margin:4px 0 0;opacity:0.75;font-size:13px;">
            {matched_count} above {int(MATCH_THRESHOLD*100)}% match
          </p>
        </div>

        <!-- Two columns: New / Seen -->
        <div class="digest-columns">
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
              <h2 style="margin:0;font-size:15px;color:#111827;">🆕 New</h2>
              <span id="new-count" style="background:#dbeafe;color:#1e40af;font-size:12px;font-weight:600;
                           padding:2px 9px;border-radius:10px;">{len(new_jobs)}</span>
            </div>
            <div class="column-scroll" id="new-list">
              {new_cards}
              <p id="new-empty" style="text-align:center;color:#6b7280;padding:30px 10px;font-size:13px;
                 display:{'none' if new_cards else 'block'};">No new jobs since your last visit.</p>
            </div>
          </div>
          <div>
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
              <h2 style="margin:0;font-size:15px;color:#6b7280;">👀 Seen</h2>
              <span id="seen-count" style="background:#f3f4f6;color:#6b7280;font-size:12px;font-weight:600;
                           padding:2px 9px;border-radius:10px;">{len(seen_jobs)}</span>
            </div>
            <div class="column-scroll" id="seen-list">
              {seen_cards}
              <p id="seen-empty" style="text-align:center;color:#6b7280;padding:30px 10px;font-size:13px;
                 display:{'none' if seen_cards else 'block'};">Nothing seen yet.</p>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div style="text-align:center;padding:24px;color:#9ca3af;font-size:12px;">
          <p>Job Agent · sorted by match score · select jobs to delete them</p>
        </div>
      </div>
    </body>
    </html>
    """
    return html


def send_digest(jobs: List[Dict]) -> bool:
    """Save job digest as HTML and open it in the browser. Returns True on success."""
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        out_path = OUTPUT_DIR / f"digest_{timestamp}.html"
        out_path.write_text(build_html(jobs), encoding="utf-8")
        webbrowser.open(out_path.as_uri())
        print(f"[Digest] Opened in browser: {out_path}")
        return True
    except Exception as e:
        print(f"[Digest] Failed to open HTML: {e}")
        return False
