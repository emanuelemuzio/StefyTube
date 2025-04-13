
const clearProgressData = () => fetch('/api/clear')
setInterval(clearProgressData, 1000);
clearProgressData();