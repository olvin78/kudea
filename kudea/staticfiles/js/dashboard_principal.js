// ===== FECHA ACTUAL =====
const fechaElem = document.getElementById('fecha-actual');
if (fechaElem) {
    fechaElem.textContent = new Date().toLocaleDateString('es-ES', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

// ===== GRÁFICO =====
const diasElem = document.getElementById('dias-data');
const ventasElem = document.getElementById('ventas-data');
const ctx = document.getElementById('salesChart');

if (window.Chart && diasElem && ventasElem && ctx) {

    let dias = [];
    let ventas = [];

    try {
        dias = JSON.parse(diasElem.textContent.trim());
        ventas = JSON.parse(ventasElem.textContent.trim());
    } catch (e) {
        console.warn("Error en datos del gráfico");
    }

    if (Array.isArray(dias) && Array.isArray(ventas)) {
        const gradient = ctx.getContext('2d').createLinearGradient(0, 0, 0, 400);
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.2)');
        gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');

        new Chart(ctx, {
            type: 'line',
            data: {
                labels: dias,
                datasets: [{
                    label: 'Ventas (€)',
                    data: ventas,
                    borderColor: '#3b82f6',
                    borderWidth: 3,
                    fill: true,
                    backgroundColor: gradient,
                    tension: 0.45,
                    pointRadius: 4,
                    pointBackgroundColor: '#fff',
                    pointBorderColor: '#3b82f6',
                    pointBorderWidth: 2,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#3b82f6',
                    pointHoverBorderColor: '#fff',
                    pointHoverBorderWidth: 2,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#0f172a',
                        titleFont: { size: 13, weight: 'bold' },
                        bodyFont: { size: 12 },
                        padding: 12,
                        cornerRadius: 10,
                        displayColors: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(0,0,0,0.03)', drawBorder: false },
                        ticks: { font: { weight: 'bold' }, color: '#94a3b8' }
                    },
                    x: {
                        grid: { display: false },
                        ticks: { font: { weight: 'bold' }, color: '#94a3b8' }
                    }
                }
            }
        });
    }
}

// ===== ICONOS =====
if (window.lucide) {
    window.lucide.createIcons();
}