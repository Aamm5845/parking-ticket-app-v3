document.addEventListener('DOMContentLoaded', () => {

    // Helper function for clipboard copying and user feedback
    function copyToClipboard(button, textToCopy) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalHTML = button.innerHTML;
            const stepElement = button.closest('.step');

            // Provide visual feedback on the button
            button.innerHTML = '<span class="material-icons">done</span>';
            
            // Mark the step as completed
            if (stepElement) {
                stepElement.classList.add('step-completed');
            }
            
            // Reset button after 2 seconds
            setTimeout(() => {
                button.innerHTML = originalHTML;
            }, 2000);

        }).catch(err => {
            console.error('Failed to copy text: ', err);
            alert('Failed to copy text.');
        });
    }

    // Add event listeners to all copy buttons
    document.querySelectorAll('.copy-btn').forEach(button => {
        button.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = e.currentTarget.dataset.target;
            const inputElement = document.getElementById(targetId);
            
            if (inputElement) {
                copyToClipboard(e.currentTarget, inputElement.value);
            }
        });
    });
});
