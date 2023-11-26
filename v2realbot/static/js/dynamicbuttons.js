//ekvivalent to ready
$(function(){

    //dynamicke buttony predelat na trdi se vstupem (nazev cfg klice, id conteineru)
    var buttonConfig = get_from_config("analyze_buttons");

    console.log("here")

    buttonConfig.forEach(function(button) {
        var $btnGroup = $('<div>', {class: 'btn-group'});
        var $btn = $('<button>', {
            type: 'button',
            class: 'btn btn-primary',
            text: button.label
        });

        var $form = $('<form>', {class: 'input-group'});

        // Handling additional parameters
        for (var key in button.additionalParameters) {
            var param = button.additionalParameters[key];
            var $input;

            if (param.type === 'select') {
                $input = $('<select>', {class: 'form-select', name: key});
                param.options.forEach(function(option) {
                    $input.append($('<option>', {value: option, text: option}));
                });
            } else {
                $input = $('<input>', {
                    type: param.type === 'number' ? 'number' : 'text',
                    class: 'form-control',
                    name: key,
                    placeholder: key
                });
            }

            $form.append($input);
        }

        $btnGroup.append($btn).append($form);
        $('#buttons-container').append($btnGroup);

        // Event listener for button
        $btn.on('click', function(event) {
            event.preventDefault();

            var formData = $form.serializeArray().reduce(function(obj, item) {
                obj[item.name] = item.value;
                return obj;
            }, {});

            $.ajax({
                url: button.apiEndpoint,
                method: 'POST',
                data: formData,
                success: function(response) {
                    console.log('API Call Successful:', response);
                },
                error: function(error) {
                    console.error('API Call Failed:', error);
                }
            });
        });
    });
});
