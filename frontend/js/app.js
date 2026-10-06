
let allEntities = [];
let currentSelectedEntity = null;
let currentDossierData = null;
let streamInterval = null;

async function initDashboard() {
    try {
        const entRes = await fetch('/entities');
        allEntities = await entRes.json();
        renderEntityList(allEntities);

        const graphRes = await fetch('/graph');
        const graphData = await graphRes.json();
        renderNetworkGraph(graphData, selectVendor);

        if (allEntities.length > 0) {
            selectVendor(allEntities[0].entity_id);
        }
    } catch (err) {
        console.error('Failed to initialize dashboard:', err);
    }
}

function renderEntityList(entities) {
    const container = document.getElementById('vendorList');
    container.innerHTML = '';

    entities.forEach(e => {
        const card = document.createElement('div');
        card.className = 'vendor-card';
        card.id = `card-${e.entity_id}`;
        card.innerHTML = `
      <div class="title">${e.name}</div>
      <div class="meta">
        <span>${e.entity_id}</span>
        <span style="color: #10b981; font-weight:600;">ACTIVE</span>
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

    const inspectBtn = document.getElementById('inspectDocBtn');
    inspectBtn.style.display = data.heatmap_image ? 'block' : 'none';

    const reasonsContainer = document.getElementById('reasonsList');
    reasonsContainer.innerHTML = '';

    data.reasons.forEach(r => {
        const pill = document.createElement('div');
        pill.className = 'reason-pill';
        if (r.includes('CRITICAL') || r.includes('ELA')) pill.classList.add('critical');
        if (r.includes('CROSS-LAYER') || r.includes('Escalation') || r.includes('NETWORK')) pill.classList.add('escalation');
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

function openPdfModal() {
    if (currentSelectedEntity) {
        const frame = document.getElementById('pdfViewerFrame');
        frame.src = `/export-dossier/${currentSelectedEntity}`;
        document.getElementById('pdfModal').classList.add('open');
    }
}

function closePdfModal() {
    document.getElementById('pdfViewerFrame').src = '';
    document.getElementById('pdfModal').classList.remove('open');
}

function downloadPdfDirect() {
    if (currentSelectedEntity) {
        const link = document.createElement('a');
        link.href = `/export-dossier/${currentSelectedEntity}`;
        link.download = `Audit_Dossier_${currentSelectedEntity}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const activeEntityId = currentSelectedEntity || allEntities[0]?.entity_id || 'VEND-1001';
    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch(`/analyze-document?entity_id=${activeEntityId}`, {
            method: 'POST',
            body: formData
        });
        const docResult = await res.json();

        selectVendor(activeEntityId);
        alert(`Document "${file.name}" analyzed successfully! Forensic Score: ${docResult.authenticity_score}`);
    } catch (err) {
        alert('Failed to upload and analyze document');
    }
}

function toggleTenderStream(event) {
    const isChecked = event.target.checked;
    const streamPanel = document.getElementById('streamPanel');

    if (isChecked) {
        streamPanel.classList.add('open');
        startSimulatedStream();
    } else {
        streamPanel.classList.remove('open');
        clearInterval(streamInterval);
    }
}

function startSimulatedStream() {
    const tbody = document.getElementById('streamTbody');
    tbody.innerHTML = '';
    document.getElementById('alertCard').style.display = 'none';
    let counter = 0;

    const cleanSequence = [allEntities[0], allEntities[1], allEntities[2], allEntities[3]].filter(Boolean);
    const cartelTarget = allEntities.find(e => e.entity_id === 'VEND-4990') || allEntities[allEntities.length - 1];

    streamInterval = setInterval(async () => {
        counter++;
        let targetEntity;
        if (counter === 3 && cartelTarget) {
            targetEntity = cartelTarget;
        } else {
            targetEntity = cleanSequence[(counter - 1) % cleanSequence.length] || allEntities[0];
        }

        if (!targetEntity) return;

        const timeStr = new Date().toLocaleTimeString();
        const bidAmount = (12.5 + counter * 2.1).toFixed(1);
        const tenderId = `GEM/B/${4468 + counter}`;

        const res = await fetch(`/risk-score/${targetEntity.entity_id}`);
        const data = await res.json();
        const isHigh = data.risk_band === 'HIGH';

        const row = document.createElement('tr');
        row.innerHTML = `
      <td>${timeStr}</td>
      <td><b>${targetEntity.name}</b> (${targetEntity.entity_id})</td>
      <td>${tenderId}</td>
      <td>₹${bidAmount}L</td>
      <td><span class="band-tag band-${data.risk_band}">${data.risk_band}</span></td>
    `;
        tbody.prepend(row);

        if (isHigh) {
            document.getElementById('alertCard').style.display = 'flex';
            document.getElementById('alertVendorName').innerText = `${targetEntity.name} (${targetEntity.entity_id})`;
            document.getElementById('alertTenderId').innerText = `Bid ${tenderId} held before award`;
            document.getElementById('btnAlertDossier').onclick = () => {
                document.getElementById('streamToggle').checked = false;
                toggleTenderStream({ target: { checked: false } });
                selectVendor(targetEntity.entity_id);
            };
        }
    }, 2800);
}

document.getElementById('searchInput').addEventListener('input', e => {
    const query = e.target.value.toLowerCase();
    const filtered = allEntities.filter(
        ent => ent.name.toLowerCase().includes(query) || ent.entity_id.toLowerCase().includes(query)
    );
    renderEntityList(filtered);
});

// Auto-run dashboard initialization on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDashboard);
} else {
    initDashboard();
}