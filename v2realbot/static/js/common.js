$(document).ready(function() {
    // Function to handle the state of each collapsible section
    function handleCollapsibleState() {
        $('.collapsible-section').each(function() {
            var sectionId = $(this).attr('id');
            var isExpanded = localStorage.getItem(sectionId + 'State') === 'true';

            if (isExpanded) {
                $(this).addClass('show');
                $(this).attr('aria-expanded', 'true');
            } else {
                $(this).removeClass('show');
                $(this).attr('aria-expanded', 'false');
            }

            // Set up event listener for the toggle
            $('[data-bs-target="#' + sectionId + '"]').click(function() {
                setTimeout(function() { // Set timeout to wait for the toggle action to complete
                    var currentState = $('#' + sectionId).hasClass('show');
                    localStorage.setItem(sectionId + 'State', currentState);
                }, 350); // Adjust timeout as needed based on the collapse animation duration
            });
        });
    }

    // Apply the function to all elements with the 'collapsible-section' class
    handleCollapsibleState();

    // Additional functionality such as fetching models (as previously defined)
});
