    function get_system_status() {
        console.log('Button get system status clicked')
        $.ajax({
            url: '/system-info',
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            success: function(response) {
                $('#disk-gauge-bar').css('width', response.used_percentage + '%');
                $('#free-space').text('Free: ' + response.free + ' GB');
                $('#total-space').text('Total: ' + response.total + ' GB');
                $('#used-percent').text('Used: ' + response.used_percentage + '%');
            
            },
            error: function(xhr, status, error) {
                $('#disk-gauge-bar').html('An error occurred: ' + error + xhr.responseText + status);
            }
        });
    }


$(document).ready(function(){
  get_system_status()
});
