
let networkInstance = null;
let rawGraphData = null;

function renderNetworkGraph(graphData, onNodeSelect) {
    rawGraphData = graphData;
    const container = document.getElementById('network');

    // Map cluster memberships
    const nodeClusterMap = {};
    graphData.nodes.forEach(n => {
        if (n.group && n.group !== 'CLEAN') {
            nodeClusterMap[n.id] = n.group;
        }
    });

    // 1. Spaced, clean nodes
    const nodes = new vis.DataSet(
        graphData.nodes.map(n => {
            const isHigh = n.risk_band === 'HIGH';
            return {
                id: n.id,
                label: isHigh ? n.label : (n.label.length > 11 ? n.label.substring(0, 11) + '..' : n.label),
                title: `🏢 ${n.label}\nID: ${n.id}\nRisk: ${n.risk_band}`,
                color: {
                    background: isHigh ? '#ef4444' : '#10b981',
                    border: isHigh ? '#b91c1c' : '#047857',
                    highlight: { background: '#38bdf8', border: '#0284c7' }
                },
                font: {
                    color: isHigh ? '#ffffff' : '#94a3b8',
                    size: isHigh ? 10 : 7.5,
                    face: 'Segoe UI',
                    strokeWidth: 2,
                    strokeColor: '#090d16'
                },
                shape: 'dot',
                size: isHigh ? 15 : 7,
                group: n.group
            };
        })
    );

    // 2. Clean organic curved edges
    const edges = new vis.DataSet(
        graphData.edges.map(e => {
            const isTxn = e.edge_type === 'transaction';
            const isClusterEdge = nodeClusterMap[e.from] && nodeClusterMap[e.from] === nodeClusterMap[e.to];

            let edgeColor = 'rgba(56, 189, 248, 0.18)';
            let edgeWidth = 0.7;

            if (isClusterEdge) {
                edgeColor = 'rgba(239, 68, 68, 0.85)';
                edgeWidth = 2.0;
            }

            return {
                from: e.from,
                to: e.to,
                title: `${isTxn ? '💸 Commercial Trade' : '🔗 Corporate Link'}: ${e.label}`,
                color: {
                    color: edgeColor,
                    highlight: '#38bdf8'
                },
                width: edgeWidth,
                smooth: {
                    type: isClusterEdge ? 'curvedCW' : 'continuous',
                    roundness: isClusterEdge ? 0.22 : 0.12
                }
            };
        })
    );

    // 3. Fast, Lively, Centered Floating Physics
    const options = {
        physics: {
            enabled: true,
            solver: 'barnesHut',
            timestep: 0.80,               // ◄ Kept your exact speed
            barnesHut: {
                gravitationalConstant: -1400, // ◄ Change from -2000 to -1400 (Less outward push)
                centralGravity: 0.55,         // ◄ Change from 0.25 to 0.55 (Pulls far nodes close in!)
                springLength: 130,
                springConstant: 0.05,         // ◄ Kept your exact springiness
                damping: 0.04                 // ◄ Kept your exact fluid motion
            },
            minVelocity: 0.05,
            maxVelocity: 35,
            stabilization: false
        },
        interaction: {
            hover: true,
            tooltipDelay: 80,
            zoomView: true,
            dragView: true
        }
    };

    networkInstance = new vis.Network(container, { nodes, edges }, options);

    networkInstance.on('click', params => {
        if (params.nodes.length > 0) {
            const selectedEntityId = params.nodes[0];
            onNodeSelect(selectedEntityId);
            applyFocusMode(selectedEntityId);
        } else {
            resetFocusMode();
        }
    });
}

function applyFocusMode(selectedNodeId) {
    if (!networkInstance || !rawGraphData) return;

    const selectedNode = rawGraphData.nodes.find(n => n.id === selectedNodeId);
    const clusterId = selectedNode ? selectedNode.group : null;
    const chip = document.getElementById('focusChip');

    if (clusterId && clusterId !== 'CLEAN') {
        const clusterMembers = rawGraphData.nodes.filter(n => n.group === clusterId).map(n => n.id);
        const dimmedCount = rawGraphData.nodes.length - clusterMembers.length;

        // Dim non-cluster nodes
        networkInstance.body.data.nodes.update(
            rawGraphData.nodes.map(n => {
                const inCluster = clusterMembers.includes(n.id);
                return {
                    id: n.id,
                    color: {
                        background: inCluster ? '#ef4444' : 'rgba(16, 185, 129, 0.04)',
                        border: inCluster ? '#b91c1c' : 'rgba(4, 120, 87, 0.04)'
                    },
                    font: {
                        color: inCluster ? '#ffffff' : 'rgba(148, 163, 184, 0.04)',
                        size: inCluster ? 11 : 4
                    },
                    size: inCluster ? 18 : 4
                };
            })
        );

        // Highlight only cluster edges
        networkInstance.body.data.edges.update(
            rawGraphData.edges.map(e => {
                const isClusterEdge = clusterMembers.includes(e.from) && clusterMembers.includes(e.to);
                return {
                    id: e.id,
                    color: {
                        color: isClusterEdge ? '#ef4444' : 'rgba(51, 65, 85, 0.02)'
                    },
                    width: isClusterEdge ? 2.6 : 0.2
                };
            })
        );

        chip.style.display = 'flex';
        document.getElementById('focusChipText').innerText = `🎯 FOCUS: ${clusterId} | ${clusterMembers.length} entities (${dimmedCount} dimmed)`;
    } else {
        resetFocusMode();
    }
}

function resetFocusMode() {
    if (!networkInstance || !rawGraphData) return;

    const nodeClusterMap = {};
    rawGraphData.nodes.forEach(n => {
        if (n.group && n.group !== 'CLEAN') {
            nodeClusterMap[n.id] = n.group;
        }
    });

    networkInstance.body.data.nodes.update(
        rawGraphData.nodes.map(n => ({
            id: n.id,
            color: {
                background: n.risk_band === 'HIGH' ? '#ef4444' : '#10b981',
                border: n.risk_band === 'HIGH' ? '#b91c1c' : '#047857'
            },
            font: {
                color: n.risk_band === 'HIGH' ? '#ffffff' : '#94a3b8',
                size: n.risk_band === 'HIGH' ? 10 : 7.5
            },
            size: n.risk_band === 'HIGH' ? 15 : 7
        }))
    );

    networkInstance.body.data.edges.update(
        rawGraphData.edges.map(e => {
            const isClusterEdge = nodeClusterMap[e.from] && nodeClusterMap[e.from] === nodeClusterMap[e.to];
            return {
                id: e.id,
                color: {
                    color: isClusterEdge ? 'rgba(239, 68, 68, 0.85)' : 'rgba(56, 189, 248, 0.18)'
                },
                width: isClusterEdge ? 2.0 : 0.7
            };
        })
    );

    document.getElementById('focusChip').style.display = 'none';
}

function focusOnNode(nodeId) {
    if (networkInstance) {
        networkInstance.selectNodes([nodeId]);
        networkInstance.focus(nodeId, {
            scale: 1.15,
            animation: { duration: 500, easingFunction: 'easeInOutQuad' }
        });
    }
}