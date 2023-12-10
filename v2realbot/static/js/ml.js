//ML Model GUI section

let model_editor_json
let model_editor_python

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
                        $('#model-list').append(`
                        <p>${model}
                            <span class="inspect-model" data-model="${model}">[🔍]</span>
                            <span class="download-model" data-model="${model}">[↓]</span>
                            <span class="delete-model" data-model="${model}">[x]</span>
                        </p>
                    `);
        
                    });
                }
            },
            error: function(xhr, status, error) {
                $('#model-list').html('An error occurred: ' + error + xhr.responseText + status);
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
                alert('Error deleting model: ' + error + xhr.responseText + status);
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
                alert('Error uploading model: ' + error + xhr.responseText + status);
            }
        });
    }

    function downloadModel(modelName) {
        $.ajax({
            url: '/model/download-model/' + modelName,
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key', API_KEY);
            },
            success: function(data, status, xhr) {
                // Get a URL for the blob to download
                var blob = new Blob([data], { type: xhr.getResponseHeader('Content-Type') });
                var downloadUrl = URL.createObjectURL(blob);
                var a = document.createElement('a');
                a.href = downloadUrl;
                a.download = modelName;
                document.body.appendChild(a);
                a.click();
                // Clean up
                window.URL.revokeObjectURL(downloadUrl);
                a.remove();
            },
            error: function(xhr, status, error) {
                alert('Error downloading model: ' + error + xhr.responseText + status);
            }
        });
    }

    // Function to fetch metadata
    function fetchMetadata(modelName) {
        $.ajax({
            url: '/model/metadata/' + modelName,
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key', API_KEY);
            },
            success: function(response) {
                show_metadata(response, modelName)
            },
            error: function(xhr, status, error) {
                $('#metadata-container').html('Error fetching metadata: ' + error + xhr.responseText + status);
                show_metadata(xhr)
            }
        });
    }

    function show_metadata(response, name) {
        // var formattedMetadata = '<pre>cfg:' + JSON.stringify(response.cfg, null, 4) + '</pre>';
        // formattedMetadata += '<pre>arch_function:' + response.arch_function + '</pre>';
        // $('#metadata-container').html(formattedMetadata);
        //console.log(response)
        console.log(JSON.stringify(response,null,4))
        $('#metadata_label').html(name);

        require(["vs/editor/editor.main"], () => {
            model_editor_json = monaco.editor.create(document.getElementById('toml-editor-container'), {
                value: response.cfg_toml ? response.cfg_toml : JSON.stringify(response,null,4),
                language: 'toml',
                theme: 'tomlTheme-dark',
                automaticLayout: true,
                readOnly: true
            });
            model_editor_python = monaco.editor.create(document.getElementById('python-editor-container'), {
                value: response.arch_function ? response.arch_function : '',
                language: 'python',
                theme: 'tomlTheme-dark',
                automaticLayout: true,
                readOnly: true
            });
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

    // Event handler for the inspect icon
    $('#model-list').on('click', '.inspect-model', function() {
        if (model_editor_json) {model_editor_json.dispose()}
        if (model_editor_python) {model_editor_python.dispose()}
        const modelName = $(this).data('model');
        fetchMetadata(modelName);
        window.$('#modelModal').modal('show');
    });

    //Handler to download the model
    $('#model-list').on('click', '.download-model', function() {
        const modelName = $(this).data('model');
        downloadModel(modelName);
    });

});
