
const clearProgressData = () => fetch('/api/clear')
setInterval(clearProgressData, 2000);
clearProgressData();