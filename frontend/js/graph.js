let networkInstance = null;

function renderNetworkGraph(graphData, onNodeSelect) {
    const container = document.getElementById('network');

    const nodes = new vis.DataSet(
        graphData.nodes.map(n => ({
            id: n.id,
            label: n.label.length > 18 ? n.label.substring(0, 18) + '...' : n.label,
            title: `${n.label} (${n.id})`,
            color: {
                background: n.risk_band === 'HIGH' ? '#ef4444' : '#10b981',
                border: n.risk_band === 'HIGH' ? '#b91c1c' : '#047857',
                highlight: { background: '#38bdf8', border: '#0284c7' }
            },
            font: { color: '#f8fafc', size: 12 },
            shape: 'dot',
            size: n.risk_band === 'HIGH' ? 18 : 12
        }))
    );

    const edges = new vis.DataSet(
        graphData.edges.map(e => ({
            from: e.from,
            to: e.to,
            label: e.label,
            font: { size: 9, color: '#64748b', align: 'middle' },
            color: { color: '#334155', highlight: '#38bdf8' },
            arrows: e.edge_type === 'transaction' ? 'to' : ''
        }))
    );

    const options = {
        physics: {
            stabilization: { iterations: 120 },
            barnesHut: { gravitationalConstant: -3000, springLength: 95 }
        },
        interaction: { hover: true, tooltipDelay: 100 }
    };

    networkInstance = new vis.Network(container, { nodes, edges }, options);

    networkInstance.on('click', params => {
        if (params.nodes.length > 0) {
            const selectedEntityId = params.nodes[0];
            onNodeSelect(selectedEntityId);
        }
    });
}

function focusOnNode(nodeId) {
    if (networkInstance) {
        networkInstance.selectNodes([nodeId]);
        networkInstance.focus(nodeId, {
            scale: 1.2,
            animation: { duration: 600, easingFunction: 'easeInOutQuad' }
        });
    }
}