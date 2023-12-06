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
                        $('#model-list').append('<p>' + model + ' <span class="delete-model" data-model="' + model + '">x</span></p>');
                    });
                }
            },
            error: function(xhr, status, error) {
                $('#model-list').html('An error occurred: ' + error);
            }
        });
    }

    function deleteModel(modelName) {
        $.ajax({
            url: '/model/delete-model/' + modelName,
            type: 'DELETE',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            success: function(response) {
                fetchModels(); // Refresh the list after deletion
            },
            error: function(xhr, status, error) {
                alert('Error deleting model: ' + error);
            }
        });
    }

    function uploadModel(formData) {
        $.ajax({
            url: '/model/upload-model',
            type: 'POST',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            data: formData,
            processData: false,
            contentType: false,
            success: function(response) {
                fetchModels(); // Refresh the list after uploading
                alert('Model uploaded successfully');
            },
            error: function(xhr, status, error) {
                alert('Error uploading model: ' + error);
            }
        });
    }


    // Fetch models on page load
    fetchModels();

    // Refresh models on button click
    $('#ml-refresh-button').click(function() {
        fetchModels();
    });

    $('#model-list').on('click', '.delete-model', function() {
        const modelName = $(this).data('model');
        if (confirm('Are you sure you want to delete ' + modelName + '?')) {
            deleteModel(modelName);
        }
    });

    $('#upload-form').submit(function(e) {
        e.preventDefault();
        var formData = new FormData(this);
        if (!$('#model-file')[0].files[0]) {
            console.log("prazdne")
            alert("No file selected.")
            return
        }
        formData.append('file', $('#model-file')[0].files[0]); // Make sure 'file' matches the FastAPI parameter
        uploadModel(formData);
    });

});
