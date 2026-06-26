const $ = (id) => document.getElementById(id);
const apiKey = () => $("apiKey").value.trim();

async function api(path, method = "GET", body = null) {
  const opts = { method, headers: { "X-API-Key": apiKey() } };
  if (body) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const resp = await fetch(path, opts);
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

// Multipart variant: sends form fields + a file. Lets the browser set the
// Content-Type (with boundary), so we only pass the API key header.
async function apiForm(path, formData) {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "X-API-Key": apiKey() },
    body: formData,
  });
  const data = await resp.json();
  if (!resp.ok) throw data;
  return data;
}

function showError(el, err) {
  el.innerHTML = `<div class="error">Error: ${err.error || JSON.stringify(err)}</div>`;
}

function pct(v) {
  return Math.round(v * 100);
}

// ---- Submit ----
$("submitBtn").addEventListener("click", async () => {
  const el = $("submitResult");
  el.textContent = "Analysing...";
  try {
    const fileInput = $("file");
    const creator = $("creatorId").value || "anonymous";
    let data;
    if (fileInput.files.length) {
      const fd = new FormData();
      fd.append("file", fileInput.files[0]);
      fd.append("creator_id", creator);
      if ($("text").value.trim()) fd.append("text", $("text").value);
      data = await apiForm("/submit", fd);
    } else {
      data = await api("/submit", "POST", {
        text: $("text").value,
        creator_id: creator,
      });
    }
    const s = data.signals;
    const cert = data.certificate?.verified_human
      ? `<div class="badge likely_human">✔ Verified Human creator</div>`
      : "";
    el.innerHTML = `
      ${cert}
      <div class="badge ${data.attribution}">${data.attribution.replace("_", " ")}</div>
      <div><strong>${data.label}</strong></div>
      <div class="bar"><span style="width:${pct(data.confidence)}%"></span></div>
      <div>Confidence: ${pct(data.confidence)}% &middot; source: ${data.source}</div>
      <div style="margin-top:10px">
        ${signalBar("LLM", s.llm)}
        ${signalBar("Stylometric", s.stylometric)}
        ${signalBar("Metadata", s.metadata)}
      </div>
      <div style="margin-top:8px;color:var(--muted)">content_id: ${data.content_id}</div>
    `;
    $("appealId").value = data.content_id;
  } catch (err) {
    showError(el, err);
  }
});

function signalBar(name, v) {
  return `<div class="signal-row"><span>${name}</span>
    <div class="bar" style="flex:1"><span style="width:${pct(v)}%"></span></div>
    <span style="width:36px;text-align:right">${pct(v)}%</span></div>`;
}

// ---- Appeal ----
$("appealBtn").addEventListener("click", async () => {
  const el = $("appealResult");
  el.textContent = "Submitting...";
  try {
    const data = await api("/appeal", "POST", {
      content_id: $("appealId").value.trim(),
      reasoning: $("appealReason").value,
    });
    el.innerHTML = `<div class="badge uncertain">${data.status}</div>
      <div>Appeal recorded for ${data.content_id}</div>`;
  } catch (err) {
    showError(el, err);
  }
});

// ---- Certify ----
$("certBtn").addEventListener("click", async () => {
  const el = $("certResult");
  el.textContent = "Issuing...";
  try {
    const data = await api("/certify", "POST", { creator_id: $("certId").value.trim() });
    el.innerHTML = `<div class="badge likely_human">✔ Verified Human</div>
      <div>Certificate issued to ${data.creator_id}</div>`;
  } catch (err) {
    showError(el, err);
  }
});

// ---- Dashboard ----
$("dashBtn").addEventListener("click", async () => {
  const el = $("dashResult");
  el.textContent = "Loading...";
  try {
    const d = await api("/dashboard");
    el.innerHTML = `
      <div>Total submissions: <strong>${d.total_submissions}</strong></div>
      <div>Appeal rate: <strong>${pct(d.appeal_rate)}%</strong></div>
      <div>Average confidence: <strong>${pct(d.average_confidence)}%</strong></div>
      <pre>${JSON.stringify({ attribution: d.attribution_breakdown, status: d.status_breakdown }, null, 2)}</pre>
    `;
  } catch (err) {
    showError(el, err);
  }
});

// ---- Log ----
$("logBtn").addEventListener("click", async () => {
  const el = $("logResult");
  el.textContent = "Loading...";
  try {
    const d = await api("/log?limit=20");
    if (!d.entries.length) {
      el.textContent = "No events yet.";
      return;
    }
    el.innerHTML = d.entries
      .map(
        (e) =>
          `<div style="border-bottom:1px solid #262a37;padding:6px 0">
            <strong>${e.event_type}</strong>
            <span style="color:var(--muted)"> &middot; ${e.created_at}</span>
            <pre>${JSON.stringify(e.payload, null, 2)}</pre>
          </div>`
      )
      .join("");
  } catch (err) {
    showError(el, err);
  }
});
