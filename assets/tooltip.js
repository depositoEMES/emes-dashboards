// Funciones personalizadas para tooltips de Dash
window.dccFunctions = window.dccFunctions || {};

// Función para formatear moneda
window.dccFunctions.formatCurrency = function(value) {
    if (value >= 1000000000) {
        // Miles de millones
        return '$' + (value / 1000000000).toFixed(1) + 'B';
    } else if (value >= 1000000) {
        // Millones
        if (value % 1000000 === 0) {
            return '$' + (value / 1000000).toFixed(0) + 'M';
        } else {
            return '$' + (value / 1000000).toFixed(1) + 'M';
        }
    } else if (value >= 1000) {
        // Miles
        if (value % 1000 === 0) {
            return '$' + (value / 1000).toFixed(0) + 'K';
        } else {
            return '$' + (value / 1000).toFixed(0) + 'K';
        }
    } else if (value === 0) {
        return '$0';
    } else {
        // Valores menores con separadores de miles (formato colombiano)
        return '$' + value.toLocaleString('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
};

// Función adicional para formato más detallado
window.dccFunctions.formatCurrencyDetailed = function(value) {
    if (value >= 1000000) {
        return '$' + value.toLocaleString('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    } else {
        return '$' + value.toLocaleString('es-CO', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
};

// Función para porcentajes
window.dccFunctions.formatPercentage = function(value) {
    return value.toFixed(1) + '%';
};