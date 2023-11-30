//ekvivalent to ready
$(function(){

    //load configu buttons
    loadConfig("dynamic_buttons").then(config => {
        console.log("Config loaded for dynamic_buttons", config);

        // $(targetElement).append(dropdownHtml)
        // // Find the ul element within the dropdown
        // var dropdownMenu = $(targetElement).find('.dropdown-menu');
        configData["dynamic_buttons"] = config
        //toto je obecné nad table buttony
        console.log("conf data z buttonu po loadu", configData)
        populate_dynamic_buttons($("#buttons-container"), config);
    }).catch(error => {
        console.error('Error loading config for', "dynamic_buttons", error);
    });





})

//vstupem je #some dropdown menu (TODO mozna dava smysl, abychom si element vytvorili predtim
//a nikoliv v nasledne funkci jak to zatim je)
function populate_dynamic_buttons(targetElement, config, batch_id = null)  {
    //console.log("buttonConfig",config)

    // Function to create form inputs based on the configuration
    function createFormInputs(additionalParameters, batch_id = null) {
        var formHtml = ''
        // else
        // {
        //     $.each(runner_ids, function(index, id) {
        //         formHtml += '<input type="hidden" name="runner_ids[]" value="' + id + '">';
        //     });
        // }

        $.each(additionalParameters, function(key, param) {
            // Include 'name' attribute in each input element
            var id_prefix = batch_id ? batch_id : ''
            var id = id_prefix + key
            switch(param.type) {
                case 'select':
                    formHtml += '<div class="form-label-group"><select class="form-select form-select-sm" name="' + key + '" id="' + id + '">';
                    $.each(param.options, function(index, option) {
                        var selected = (option == param.defval) ? 'selected' : '';
                        formHtml += '<option ' + selected + '>' + option + '</option>';
                    });
                    formHtml += '</select><label for="' + id + '">' + key + '</label></div>';
                    break;
                case 'string':
                    formHtml += '<div class="form-label-group"><input type="text" name="' + key + '" id="' + id + '" class="form-control form-control-sm" placeholder="' + key + '" value="' + param.default + '"><label for="' + id + '">' + key + '</label></div>';
                    break;
                case 'number':
                    formHtml += '<div class="form-label-group"><input type="number" name="' + key + '" id="' + id + '" class="form-control form-control-sm" placeholder="' + key + '" value="' + param.default + '"><label for="' + id + '">' + key + '</label></div>';
                    break;
                case 'boolean':
                    formHtml += '<div class="form-label-group"><input type="checkbox" name="' + key + '" id="' + id + '" class="form-check" ' + (param.default? 'checked' : '') + '><label for="' + id + '">' + key + '</label></div>';
                    break

            }
        });
        return formHtml;
    }
        
    //naplnime obecny element (mozna delat ve volajici fci)

    //pro batche to je ikonka
    if (batch_id) {
        dropdownHtml = '<div class="dropdown stat_div" id="dd'+batch_id+'"><span class="material-symbols-outlined tool-icon dropdown-toggle" id="actionDropdown'+batch_id+'" data-bs-toggle="dropdown" aria-expanded="false">query_stats</span><ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="actionDropdown'+batch_id+'" id="ul'+batch_id+'"></ul></div>'
    }
    //pro runnery je to button
    else {
        dropdownHtml = '<div class="dropdown stat_div" id="dd'+batch_id+'"><button title="Available analysis to run on selected days" class="btn btn-outline-success btn-sm dropdown-toggle" type="button" id="actionDropdown'+batch_id+'" data-bs-toggle="dropdown" aria-expanded="false">Analytics</button><ul class="dropdown-menu dropdown-menu-dark" aria-labelledby="actionDropdown'+batch_id+'" id="ul'+batch_id+'"></ul></div>'

    }
    targetElement.append(dropdownHtml)
    //console.log("po pridani", targetElement)
    // Find the ul element within the dropdown
    var dropdownMenu = targetElement.find('.dropdown-menu');

    // Dynamically create buttons and forms based on the configuration
    $.each(config, function(index, buttonConfig) {
        var formHtml = createFormInputs(buttonConfig.additionalParameters, batch_id);
        var batchInputHtml = batch_id ? '<input type="hidden" name="batch_id" id="batch'+buttonConfig.function+batch_id+'" value="'+batch_id+'">': ''
        var buttonHtml = '<li><a class="dropdown-item" href="#">' + buttonConfig.label +
                            '<i class="bi bi-play-circle float-end hover-icon"></i><form class="d-none action-form" data-endpoint="' + buttonConfig.apiEndpoint + '"><div class="spinner-border text-primary d-none" role="status" id="formSpinner"><span class="visually-hidden">Loading...</span></div><input type="hidden" name="function" id="func'+buttonConfig.function+batch_id+'" value="'+buttonConfig.function+'"></input>' +
                            batchInputHtml + formHtml + '<button type="submit" class="btn btn-primary btn-sm">Submit</button></form></a></li>';
        dropdownMenu.append(buttonHtml);
        //$(targetElement).append(buttonHtml);
        //$('#actionDropdown').next('.dropdown-menu').append(buttonHtml);
    });

    // Submit form logic
    targetElement.find('.dropdown-menu').on('submit', '.action-form', function(e) {
        e.preventDefault();

        var $form = $(this);
        var $submitButton = $form.find('input[type="submit"], button[type="submit"]'); // Locate the submit button
        var $spinner = $form.find('#formSpinner');

        // Serialize the form data to a JSON object
        var formData = $form.serializeArray().reduce(function(obj, item) {
            // Handle checkbox, translating to boolean
            if ($form.find(`[name="${item.name}"]`).attr('type') === 'checkbox') {
                obj[item.name] = item.value === 'on' ? true : false;
            } else {
                obj[item.name] = item.value;
            }
            //Number should be numbers, not strings
            if ($form.find(`[name="${item.name}"]`).attr('type') === 'number') {
                obj[item.name] = Number(item.value)
            } 
            return obj;
        }, {});

        // puvodni bez boolean translatu
        //var formData = $(this).serializeJSON();

        //pokud nemame batch_id - dotahujeme rows ze selected runnerů
        console.log("toto jsou formdata pred submitem", formData)
        if (formData.batch_id == undefined) {
            console.log("batch undefined")
            rows = archiveRecords.rows('.selected');
            console.log(rows)
            if (rows == undefined || rows.data().length == 0) {
                console.log("no selected rows")
                alert("no selected rows or batch_id")
                return
            }
            // Creating an array to store the IDs
            formData.runner_ids = []

            // Iterating over the selected rows to extract the IDs
            rows.every(function (rowIdx, tableLoop, rowLoop ) {
                var data = this.data()
                formData.runner_ids.push(data.id);
            });

        }

        //population of object that is expected by the endpoint
        obj = {}
        if (formData.runner_ids) {
            obj.runner_ids = formData.runner_ids
            delete formData.runner_ids
        }
        if (formData.batch_id) {
            obj.batch_id = formData.batch_id
            delete formData.batch_id
        }
        obj.function = formData.function
        delete formData.function
        obj.params = {}
        obj.params = formData
        
        $submitButton.attr('disabled', true);
        $spinner.removeClass('d-none');

        console.log("toto jsou transformovana data", obj) 
        var apiEndpoint = $(this).data('endpoint');
        // console.log("formdata", formData)
        // API call (adjust as needed for your backend)
        $.ajax({
            url: apiEndpoint,
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            method: 'POST',
            //menime hlavicku podle toho jestli je uspesne nebo ne, abychom mohli precist chybovou hlasku
            xhr: function() {
                var xhr = new XMLHttpRequest();
                xhr.onreadystatechange = function() {
                    if (xhr.readyState === 2) { // Headers have been received
                        if (xhr.status === 200) {
                            xhr.responseType = "blob"; // Set responseType to 'blob' for successful image responses
                        } else {
                            xhr.responseType = "text"; // Set responseType to 'text' for error messages
                        }
                    }
                };
                return xhr;
            },
            xhrFields: {
                responseType: 'blob'
            },
            contentType: "application/json",
            processData: false,
            data: JSON.stringify(obj),
            success: function(data, textStatus, xhr) {
                if (xhr.getResponseHeader("Content-Type") === "image/png") {
                    // Process as Blob
                    var blob = new Blob([data], { type: 'image/png' });
                    var url = window.URL || window.webkitURL;
                    display_image(url.createObjectURL(blob));
                } else {
                    // Process as JSON
                    console.log('Received JSON', data);
                }
                $submitButton.attr('disabled', false);
                $spinner.addClass('d-none');            
            },
            error: function(xhr, status, error) {
                $spinner.addClass('d-none');
                $submitButton.attr('disabled', false);
                console.log(xhr, status, error)
                console.log(xhr.responseJSON.message)
                if (xhr.responseJSON && xhr.responseJSON.detail) {
                    console.log('Error:', xhr.responseJSON.detail);
                    window.alert(xhr.responseJSON.detail);
                } else {
                    // Fallback error message
                    console.log('Error:', error);
                    window.alert('An unexpected error occurred');
                }
            }
        });
        console.log('Form submitted for', $(this).closest('.dropdown-item').text().trim());
    });


    //HANDLERS

    //CLICKABLE VERSION (odstranit d-none z action-formu)
    // Attach click event to each dropdown item
    // $('.dropdown-menu').on('click', '.dropdown-item', function(event) {
    //     event.stopPropagation(); // Stop the event from bubbling up

    //     var currentForm = $(this).find('.action-form');
    //     // Hide all other forms
    //     $('.action-form').not(currentForm).hide();
    //     // Toggle current form
    //     currentForm.toggle();
    // });

    // // Hide form when clicking outside
    // $(document).on('click', function(event) {
    //     if (!$(event.target).closest('.dropdown-item').length) {
    //         $('.action-form').hide();
    //     }
    // });

    // // Prevent global click event from hiding form when clicking inside a form
    // $('.dropdown-menu').on('click', '.action-form', function(event) {
    //     event.stopPropagation();
    // });


    //VERZE on HOVER (je treba pridat class d-none do action formu)
    // Toggle visibility of form on hover
    targetElement.find('.dropdown-menu').on('mouseenter', '.dropdown-item', function() {
        $(this).find('.action-form').removeClass('d-none').show();
    }).on('mouseleave', '.dropdown-item', function() {
        setTimeout(() => {
            if (!$('.action-form:hover').length) {
                $(this).find('.action-form').addClass('d-none').hide();
            }
        }, 50);
    });

    // // Hide form when mouse leaves the form area
    // targetElement.find('.dropdown-menu').on('mouseleave', '.action-form', function() {
    //     $(this).hide();
    // });

    // stop propagating click up
    targetElement.find('.dropdown').on('click', function(event) {
        // Stop the event from propagating to parent elements
        event.stopPropagation();
    });

    // stop propagating click up
    targetElement.find('.action-form').on('click', function(event) {
        // Stop the event from propagating to parent elements
        event.stopPropagation();
        // Check if the clicked element or any of its parents is a submit button
        if (!$(event.target).closest('input[type="submit"], button[type="submit"], input[type="checkbox"]').length) {
            // Stop the event from propagating to parent elements
            event.preventDefault();
        }
    });

}