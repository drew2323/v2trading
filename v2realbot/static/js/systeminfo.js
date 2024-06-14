    function get_system_info() {
        console.log('Button get system status clicked')
        $.ajax({
            url: '/system-info',
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            success: function(response) {
                $.each(response, function(index, item) {
                    if (index=="disk_space") {
                        $('#disk-gauge-bar').css('width', response.disk_space.used_percentage + '%');
                        $('#free-space').text('Free: ' + response.disk_space.free + ' GB');
                        $('#total-space').text('Total: ' + response.disk_space.total + ' GB');
                        $('#used-percent').text('Used: ' + response.disk_space.used_percentage + '%');
                    } else {
                        var formatted_item = JSON.stringify(item, null, 4)
                        $('#system-info-output').append('<p>' + index + ': ' + formatted_item + '</p>');
                    }
                });            
            },
            error: function(xhr, status, error) {
                $('#disk-gauge-bar').html('An error occurred: ' + error + xhr.responseText + status);
            }
        });
    }


$(document).ready(function(){
  get_system_info()
});
