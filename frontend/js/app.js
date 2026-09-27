let allEntities = [];
let currentSelectedEntity = null;
let currentDossierData = null;

async function initDashboard() {
    try {
        const entRes = await fetch('/entities');
        allEntities = await entRes.json();
        renderEntityList(allEntities);

        const graphRes = await fetch('/graph');
        const graphData = await graphRes.json();
        renderNetworkGraph(graphData, selectVendor);

        // Auto-select injected fraud case
        const shellVendor = allEntities.find(e => e.entity_id.includes('SHELL'));
        if (shellVendor) {
            selectVendor(shellVendor.entity_id);
        }
    } catch (err) {
        console.error('Failed to initialize dashboard:', err);
    }
}

function renderEntityList(entities) {
    const container = document.getElementById('vendorList');
    container.innerHTML = '';

    entities.forEach(e => {
        const isFraudPlanted = e.entity_id.includes('SHELL');
        const card = document.createElement('div');
        card.className = 'vendor-card';
        card.id = `card-${e.entity_id}`;
        card.innerHTML = `
      <div class="title">${e.name}</div>
      <div class="meta">
        <span>${e.entity_id}</span>
        <span style="color: ${isFraudPlanted ? '#ef4444' : '#10b981'}; font-weight:600;">
          ${isFraudPlanted ? 'SUSPECT' : 'CLEAN'}
        </span>
      </div>
    `;
        card.onclick = () => selectVendor(e.entity_id);
        container.appendChild(card);
    });
}

async function selectVendor(entityId) {
    currentSelectedEntity = entityId;

    document.querySelectorAll('.vendor-card').forEach(c => c.classList.remove('active'));
    const activeCard = document.getElementById(`card-${entityId}`);
    if (activeCard) {
        activeCard.classList.add('active');
        activeCard.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }

    focusOnNode(entityId);

    const res = await fetch(`/risk-score/${entityId}`);
    currentDossierData = await res.json();
    renderDossier(currentDossierData);
}

function renderDossier(data) {
    document.getElementById('dossierEntityId').innerText = data.entity_id;
    document.getElementById('finalScore').innerText = data.final_risk_score;

    const scoreColor = data.risk_band === 'HIGH' ? '#ef4444' : data.risk_band === 'MEDIUM' ? '#f59e0b' : '#10b981';
    document.getElementById('finalScore').style.color = scoreColor;

    const bandEl = document.getElementById('riskBand');
    bandEl.className = `band-tag band-${data.risk_band}`;
    bandEl.innerText = `${data.risk_band} RISK`;

    document.getElementById('baseScore').innerText = `${data.base_score} / 100`;
    document.getElementById('escalationScore').innerText = `+${data.escalation_applied}`;

    // Toggle Inspect Button if Heatmap exists
    const inspectBtn = document.getElementById('inspectDocBtn');
    if (data.heatmap_image) {
        inspectBtn.style.display = 'block';
    } else {
        inspectBtn.style.display = 'none';
    }

    // Render Reasons
    const reasonsContainer = document.getElementById('reasonsList');
    reasonsContainer.innerHTML = '';

    data.reasons.forEach(r => {
        const pill = document.createElement('div');
        pill.className = 'reason-pill';
        if (r.includes('CRITICAL') || r.includes('ELA')) pill.classList.add('critical');
        if (r.includes('CROSS-LAYER') || r.includes('Escalation')) pill.classList.add('escalation');
        pill.innerText = r;
        reasonsContainer.appendChild(pill);
    });
}

function openForensicsModal() {
    if (currentDossierData && currentDossierData.heatmap_image) {
        document.getElementById('originalDocImg').src = currentDossierData.original_image || '';
        document.getElementById('heatmapDocImg').src = currentDossierData.heatmap_image || '';
        document.getElementById('forensicsModal').classList.add('open');
    }
}

function closeForensicsModal() {
    document.getElementById('forensicsModal').classList.remove('open');
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const activeEntityId = currentSelectedEntity || 'VEND-SHELL-CLUSTER-01-1';
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`/analyze-document?entity_id=${activeEntityId}`, {
            method: 'POST',
            body: formData
        });
        const docResult = await res.json();

        // Refresh full risk assessment
        selectVendor(activeEntityId);
        alert(`Document "${file.name}" analyzed successfully! Tamper Score: ${docResult.authenticity_score}`);
    } catch (err) {
        alert('Failed to upload document');
    }
}

// Search Filter
document.getElementById('searchInput').addEventListener('input', e => {
    const query = e.target.value.toLowerCase();
    const filtered = allEntities.filter(
        ent => ent.name.toLowerCase().includes(query) || ent.entity_id.toLowerCase().includes(query)
    );
    renderEntityList(filtered);
});

window.onload = initDashboard;