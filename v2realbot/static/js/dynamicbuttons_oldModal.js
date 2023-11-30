//ekvivalent to ready
$(function(){

    // Toggle input fields based on the selected button
    $('.main-btn, .dropdown-item').on('click', function(e) {
        e.preventDefault();
        var targetId = $(this).data('target');

        // Hide all input groups
        $('.input-group').hide();

        // Show the corresponding input group
        $(targetId).show();
    });

    // //load configu buttons
    // loadConfig("dynamic_buttons").then(configData => {
    //     console.log("Config loaded for dynamic_buttons", configData);
    //     populate_dynamic_buttons(configData);
    // }).catch(error => {
    //     console.error('Error loading config for', area, error);
    // });

    function populate_dynamic_buttons(buttonConfig)  {
        console.log("buttonConfig",buttonConfig)


        buttonConfig.forEach(function(button) {
            var modalId = 'modal-' + button.id;
            var $btn = $('<button>', {
                type: 'button',
                class: 'btn btn-primary',
                'data-bs-toggle': 'modal',
                'data-bs-target': '#' + modalId,
                text: button.label
            });
    
            // Create and append modal structure
            var $modal = createModalStructure(button, modalId);
            $('#buttons-container').append($btn).append($modal);
        });
    
        // Global event listener for modal form submission
        $(document).on('submit', '.modal form', function(event) {
            event.preventDefault();
    
            var $form = $(this);
            var formData = $form.serializeArray().reduce(function(obj, item) {
                obj[item.name] = item.value;
                return obj;
            }, {});
    
            var apiEndpoint = $form.data('api-endpoint');
    
            $.ajax({
                url: apiEndpoint,
                method: 'POST',
                data: formData,
                success: function(response) {
                    console.log('API Call Successful:', response);
                    $form.closest('.modal').modal('hide');
                },
                error: function(error) {
                    console.error('API Call Failed:', error);
                }
            });
        });
    }
});


function createModalStructure(button, modalId) {
    var $modal = $('<div>', {
        class: 'modal fade',
        id: modalId,
        tabindex: '-1',
        'aria-labelledby': modalId + 'Label',
        'aria-hidden': 'true'
    });

    var $modalDialog = $('<div>', {class: 'modal-dialog'});
    var $modalContent = $('<div>', {class: 'modal-content'});

    var $modalHeader = $('<div>', {class: 'modal-header'});
    $modalHeader.append($('<h5>', {
        class: 'modal-title',
        id: modalId + 'Label',
        text: button.label
    }));
    $modalHeader.append($('<button>', {
        type: 'button',
        class: 'btn-close',
        'data-bs-dismiss': 'modal',
        'aria-label': 'Close'
    }));

    var $modalBody = $('<div>', {class: 'modal-body'});
    var $form = $('<form>', {
        'data-api-endpoint': button.apiEndpoint
    });

    // Handling additional parameters
    for (var key in button.additionalParameters) {
        var param = button.additionalParameters[key];
        var $formGroup = $('<div>', {class: 'mb-3'});

        if (param.type === 'select') {
            var $label = $('<label>', {class: 'form-label', text: key});
            var $select = $('<select>', {class: 'form-select', name: key});
            param.options.forEach(function(option) {
                $select.append($('<option>', {value: option, text: option}));
            });
            $formGroup.append($label).append($select);
        } else {
            $formGroup.append($('<label>', {class: 'form-label', text: key}));
            $formGroup.append($('<input>', {
                type: param.type === 'number' ? 'number' : 'text',
                class: 'form-control',
                name: key,
                placeholder: key
            }));
        }

        $form.append($formGroup);
    }

    var $modalFooter = $('<div>', {class: 'modal-footer'});
    $modalFooter.append($('<button>', {
        type: 'submit',
        class: 'btn btn-primary',
        text: 'Submit'
    }));

    $modalBody.append($form);
    $modalContent.append($modalHeader).append($modalBody).append($modalFooter);
    $modalDialog.append($modalContent);
    $modal.append($modalDialog);

    return $modal;
}
