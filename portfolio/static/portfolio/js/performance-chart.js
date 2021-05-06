$(document).ready(() => {
    const config = {
        type: 'line',
        data: {
            datasets: [{
                data: performanceData,
                    fill: false,
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1,
                    borderWidth: 4,
                    pointRadius: 0,
            }],
            labels: performanceLabels
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltips: {
                    enabled: false
                }
            },
        }
    };

    const ctx = document.getElementById('performance-chart').getContext('2d');
    window.performanceChart = new Chart(ctx, config);
});