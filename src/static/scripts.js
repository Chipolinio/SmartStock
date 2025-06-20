document.addEventListener('DOMContentLoaded', function () {
    console.log("Script loaded");

    const salesCtx = document.getElementById('salesChart');
    if (!salesCtx) {
        console.error("salesChart canvas not found");
        return;
    }
    const salesLabels = salesCtx.dataset.labels || '[]';
    const salesData = salesCtx.dataset.data || '[]';
    console.log("Sales labels raw:", salesLabels);
    console.log("Sales data raw:", salesData);
    let parsedSalesLabels, parsedSalesData;
    try {
        parsedSalesLabels = JSON.parse(salesLabels);
        parsedSalesData = JSON.parse(salesData);
    } catch (e) {
        console.error("Error parsing sales data:", e, "Raw data:", { labels: salesLabels, data: salesData });
        return;
    }
    console.log("Sales labels parsed:", parsedSalesLabels);
    console.log("Sales data parsed:", parsedSalesData);

    const forecastCtx = document.getElementById('forecastChart');
    if (!forecastCtx) {
        console.error("forecastChart canvas not found");
        return;
    }
    const forecastLabels = forecastCtx.dataset.labels || '[]';
    const forecastData = forecastCtx.dataset.data || '[]';
    console.log("Forecast labels raw:", forecastLabels);
    console.log("Forecast data raw:", forecastData);
    let parsedForecastLabels, parsedForecastData;
    try {
        parsedForecastLabels = JSON.parse(forecastLabels);
        parsedForecastData = JSON.parse(forecastData);
    } catch (e) {
        console.error("Error parsing forecast data:", e, "Raw data:", { labels: forecastLabels, data: forecastData });
        return;
    }
    console.log("Forecast labels parsed:", parsedForecastLabels);
    console.log("Forecast data parsed:", parsedForecastData);

    new Chart(salesCtx.getContext('2d'), {
        type: 'line',
        data: {
            labels: parsedSalesLabels,
            datasets: [{
                label: 'Выручка',
                data: parsedSalesData,
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.2