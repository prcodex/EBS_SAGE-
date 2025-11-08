// Find all summary divs and update them
document.addEventListener('DOMContentLoaded', function() {
    // Override the createEmailElement function if needed
    const originalCreate = window.createEmailElement;
    if (originalCreate) {
        window.createEmailElement = function(item) {
            const element = originalCreate.call(this, item);
            
            // Find summary div and set innerHTML
            const summaryDiv = element.querySelector('.summary');
            if (summaryDiv && item.enriched_content) {
                summaryDiv.innerHTML = item.enriched_content;
            }
            
            return element;
        };
    }
});
