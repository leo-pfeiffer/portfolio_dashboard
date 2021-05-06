console.log('hello from allocation')

$(document).ready(() => {
      const config = {
        type: 'doughnut',
        data: {
            datasets: [{
                data: allocationData,
                backgroundColor: allocationColorPalette,
                label: 'Symbol'
            }],
            labels: allocationLabels
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

    const ctx = document.getElementById('allocation-chart').getContext('2d');
    window.allocationChart = new Chart(ctx, config);
})