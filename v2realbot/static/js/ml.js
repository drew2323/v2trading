$(document).ready(function() {
    function fetchModels() {
        $.ajax({
            url: '/model/list-models',
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            success: function(response) {
                $('#model-list').empty();
                if(response.error) {
                    $('#model-list').html('Error: ' + response.error);
                } else {
                    const models = response.models;
                    models.forEach(function(model) {
                        $('#model-list').append('<p>' + model + '</p>');
                    });
                }
            },
            error: function(xhr, status, error) {
                $('#model-list').html('An error occurred: ' + error);
            }
        });
    }

    // Fetch models on page load
    fetchModels();

    // Refresh models on button click
    $('#ml-refresh-button').click(function() {
        fetchModels();
    });
});
