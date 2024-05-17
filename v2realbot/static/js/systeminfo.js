//function get_system_status() {
//    var free_disk_value = document.getElementById("free_disk_value_display")
//    free_disk_value.textContent = "20GB";
//    console.log("clicked on the free disk button")
//}

//$(document).ready(function() {
    function get_system_status() {
        $.ajax({
            url: '/system-info',
            type: 'GET',
            beforeSend: function (xhr) {
                xhr.setRequestHeader('X-API-Key',
                API_KEY); },
            success: function(response) {
                $('.disk-gauge-bar').css('width', response.used_percentage + '%');
                $('.free-space').text('Free: ' + response.free + ' GB');
                $('.total-space').text('Total: ' + response.total + ' GB');
                $('.used-percent').text('Used: ' + response.used_percentage + '%');
            },
            error: function(xhr, status, error) {
                $('#disk_value_display').html('An error occurred: ' + error + xhr.responseText + status);
            }
        });
    }

