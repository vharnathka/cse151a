document.addEventListener('DOMContentLoaded', function () {
    if (window.location.pathname.endsWith('congressman.html')) {
        const urlParams = new URLSearchParams(window.location.search);
        const congress = urlParams.get('congress');
        const billType = urlParams.get('billType');
        const billNumber = urlParams.get('billNumber');

        if (congress && billType && billNumber) {
            console.log(`Congress: ${congress}, Bill Type: ${billType}, Bill Number: ${billNumber}`);
            // Use the parameters as needed, e.g., update the page content or make an API call
        }
    }
});
