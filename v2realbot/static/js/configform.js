let editor_json

//JS code for FRONTEND CONFIG FORM
$(document).ready(function () {
        // API Base URL
        const apiBaseUrl = '';
        let editingItemId = null;
        var localArray = []

        // Function to populate the config list and load JSON data initially
        function populateConfigList(to_select = null) {
            $.ajax({
                url: `${apiBaseUrl}/config-items/`,
                beforeSend: function (xhr) {
                    xhr.setRequestHeader('X-API-Key',
                        API_KEY); },
                type: 'GET',
                success: function (data) {
                    const configList = $('#configList');
                    configList.empty();

                    localArray = data
                    selected = ""
                    data.forEach((item, index, array) => {
                        selected = "";
                        //pokud prijde id ktere mame vybrat vybereme to, jinak vybereme prvni
                        if (((to_select !== null) && (to_select == item.id)) || ((to_select == null) && (index==0))) {
                            selected = "SELECTED"
                            $('#itemName').val(item.item_name);
                            //$('#jsonTextarea').val(item.json_data);
                            if (!editor_json) {

                            require(["vs/editor/editor.main"], () => {
                                editor_json = monaco.editor.create(document.getElementById('json_editor'), {
                                    value: item.json_data,
                                    language: 'json',
                                    theme: 'vs-dark',
                                    automaticLayout: true
                                  });
                                });
                            }
                            else
                            {
                                editor_json.setValue(item.json_data)
                            }

                            editingItemId = item.id;
                        }
                        configList.append(`<option value="${item.id}" ${selected}>${item.item_name}</option>`);
                    });
                    
                }
            });
        }

        // 
        function showJSONdata(itemId) {
            localArray.forEach((item, index, array) => {
                if (item.id == itemId) {
                    $('#itemName').val(item.item_name);
                    //$('#jsonTextarea').val(item.json_data);
                    editingItemId = itemId;
                    editor_json.setValue(item.json_data)
                }
            });
        }

        $('#cancelButton').attr('disabled', true);
        // Populate the config list and load JSON data and item name initially
        populateConfigList();

        // Event listener for config list change
        $('#configList').change(function () {
            const selectedItem = $(this).val();
            console.log(selectedItem)
            if (selectedItem) {
                showJSONdata(selectedItem);
            }
        });

        // Save or add a config item
        $('#saveButton').click(function () {
            const itemName = $('#itemName').val();
            //const jsonData = $('#jsonTextarea').val();
            const jsonData = editor_json.getValue()
            var validformat = false
            $('#addButton').attr('disabled', false);
            $('#deleteButton').attr('disabled', false);

            try {
                var parsedJSON = JSON.parse(jsonData)
                validformat = true
            }
            catch (error) {
                alert("Not valid JSON", error.message)
            }

            if (validformat) {
                var confirmed = window.confirm("Sure?");

                if (editingItemId && confirmed) {
                    // Update the selected item with the modified data using API
                    $.ajax({
                        url: `${apiBaseUrl}/config-items/${editingItemId}`,
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader('X-API-Key',
                                API_KEY); },
                        type: 'PUT',
                        contentType: 'application/json',
                        data: JSON.stringify({ item_name: itemName, json_data: jsonData }),
                        success: function () {
                            alert('Data saved successfully.');
                            populateConfigList(editingItemId); // Refresh the config list
                        }
                    });

                } else if (confirmed) {
                    // Add a new config item using API
                    $.ajax({
                        url: `${apiBaseUrl}/config-items/`,
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader('X-API-Key',
                                API_KEY); },
                        type: "POST",
                        contentType: "application/json",
                        dataType: "json",
                        data: JSON.stringify({ item_name: itemName, json_data: jsonData }),
                        success: function (data) {
                            console.log(data)
                            alert('New item added successfully.');
                            populateConfigList(data.id); // Refresh the config list
                        }
                    });
                }
            }
        });

        // Add a new config item (populates a new record in the form)
        $('#addButton').click(function () {
            $('#configList').val('');
            $('#itemName').val('');
            editor_json.setValue('')
            //$('#jsonTextarea').val('');
            editingItemId = null;
            $('#addButton').attr('disabled', true);
            $('#deleteButton').attr('disabled', true);
            $('#cancelButton').attr('disabled', false);

        });

        // Add a new config item (populates a new record in the form)
        $('#cancelButton').click(function () {
            $('#addButton').attr('disabled', false);
            $('#deleteButton').attr('disabled', false);
            $('#cancelButton').attr('disabled', true);
            populateConfigList(); 
        });

        // Delete a config item
        $('#deleteButton').click(function () {
            if (editingItemId == null) {
                $('#configList').val('');
                $('#itemName').val('');
                editor_json.setValue('')
                //$('#jsonTextarea').val('');
            }
            else {
                var confirmed = window.confirm("Confirm?");
                if (confirmed) {

                    $.ajax({
                        url: `${apiBaseUrl}/config-items/${editingItemId}`,
                        beforeSend: function (xhr) {
                            xhr.setRequestHeader('X-API-Key',
                                API_KEY); },
                        type: 'DELETE',
                        success: function () {
                            alert('Item deleted successfully.');
                            populateConfigList(); // Refresh the config list
                        }
                    });
                }
            }

        });

});