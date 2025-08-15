// Efectos de hover para gráficos de pie
document.addEventListener('DOMContentLoaded', function() {
    
    // Función para manejar hover en pie charts
    function setupPieHoverEffects() {
        const pieCharts = document.querySelectorAll('[id*="forma-pago"]');
        
        pieCharts.forEach(chart => {
            if (chart._fullLayout) {
                chart.on('plotly_hover', function(data) {
                    const point = data.points[0];
                    const update = {
                        'pull': Array(point.data.values.length).fill(0.02)
                    };
                    // Expandir el segmento en hover
                    update.pull[point.pointNumber] = 0.15; // Expansión del 15%
                    
                    Plotly.restyle(chart, update, 0);
                });
                
                chart.on('plotly_unhover', function(data) {
                    const point = data.points[0];
                    const update = {
                        'pull': Array(point.data.values.length).fill(0.02)
                    };
                    
                    Plotly.restyle(chart, update, 0);
                });
            }
        });
    }
    
    // Ejecutar cuando se carguen los gráficos
    setTimeout(setupPieHoverEffects, 1000);
    
    // Re-ejecutar cuando cambien los datos
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                setTimeout(setupPieHoverEffects, 500);
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});