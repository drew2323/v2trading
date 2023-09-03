//TODO pridat podporu pro intervaly
//pridat skrz proklik intervalu na 1m chart s timto intervalem - pripadne odkaz na tradingview

$(document).ready(function() {
    var apiUrl = '/testlists';
  
    var datesArray = [];
  
    //$('#datepicker').datepicker();
  
    function populateForm(record) {
      $('#recordId').val(record.id);
      $('#recordName').val(record.name);
      datesArray = record.dates;
      $('#tagContainer').empty();
      datesArray.forEach(function(dates) {
        var tag = $('<div class="tag">' + dates.start + " --- " + dates.end + '<span class="close">X</span></div>');
        tag.find('.close').click(function() {
          var dateText = tag.text();
          console.log("clicked")
          datesArray = datesArray.filter(function(date) {
            tagcontent = date.start + " --- " + date.end + "X"
            console.log(tagcontent,dateText)
            return tagcontent !== dateText;
          });
          $(this).parent().remove();
          console.log("ccclickd")
        });
        $('#tagContainer').append(tag);
      });
    }
  
    function renderRecords(records) {
      var recordsList = $('#recordsList');
      recordsList.empty();
  
      records.forEach(function(record) {
        var recordItem = $('<div class="recordItem"></div>');
        var recordDetails = $('<div class="recordDetails"></div>').html('<strong>ID:</strong> ' + record.id + '<br><strong>Name:</strong> ' + record.name + '<br><strong>Dates:</strong> ');
  
        record.dates.forEach(function(interval) {
          var note = ""
          if (interval.note !== null) {
            var note = '<br><strong>Note:</strong> ' + interval.note 
          }
          var intervalItem = $('<div class="intervalContainer"></div>').html('<strong>Start:</strong> ' + interval.start + '<br><strong>End:</strong> ' + interval.end + note);
          recordDetails.append(intervalItem);
        });        
        
        
        var editButton = $('<button class="btn btn-outline-success btn-sm">Edit</button>');
        var deleteButton = $('<button class="btn btn-outline-success btn-sm">X</button>');
  
        editButton.click(function() {
          editRecord(record);
        });

        deleteButton.click(function() {
            var confirmed = window.confirm("Confirm?");
            if (confirmed) {
                deleteRecord(record);
            }
          });
  
        recordItem.append(recordDetails);
        recordItem.append(editButton);
        recordItem.append(deleteButton);
        recordsList.append(recordItem);
      });
    }
  
    function editRecord(record) {
      populateForm(record);
  
      // Hide Edit button, show Save and Cancel buttons
      $('.editButton').hide();
      $('.deleteButton').hide();
      $('#saveBtn').show();
      $('#cancelBtn').show();
  
      // Disable input fields
      $('#recordName').prop('disabled', false);
      $('#addTagBtn').prop('disabled', false);
      $('#datepickerstart').prop('disabled', false);
      $('#datepickerend').prop('disabled', false);
    }
  
    function cancelEdit() {
      // Clear form
      $('#recordId').val('');
      $('#recordName').val('');
      $('#datepickerstart').val('');
      $('#datepickerend').val('');
      $('#tagContainer').empty();
      datesArray = [];
  
      // Hide Save and Cancel buttons, show Edit button
      $('.editButton').show();
      $('.deleteButton').show();
      // $('#saveBtn').hide();
      // $('#cancelBtn').hide();
  
      // Disable input fields
      $('#recordName').prop('disabled', false);
      $('#addTagBtn').prop('disabled', false);
      $('#datepickerstart').prop('disabled', false);
      $('#datepickerend').prop('disabled', false);
    }
  
    $('#addTagBtn').click(function() {
      var dateTextStart = $('#datepickerstart').val().trim();
      var dateTextEnd = $('#datepickerend').val().trim();
      var datenote = $('#datenote').val();
      if ((dateTextStart !== '') && (dateTextEnd !== '')) {
        var tag = $('<div class="tag">' + dateTextStart + " --- " + dateTextEnd + '<span class="close">X</span></div>');
        tag.find('.close').click(function() {
          var dateText = tag.text();
          console.log("clicked")
          datesArray = datesArray.filter(function(date) {
            tagcontent = date.start + " --- " + date.end + "X"
            console.log(tagcontent,dateText)
            return tagcontent !== dateText;
          });
          $(this).parent().remove();
        });
        $('#tagContainer').append(tag);
        var interval = {}
        interval["start"] = dateTextStart
        interval["end"] = dateTextEnd
        interval["note"] = datenote
        datesArray.push(interval);
        $('#datepicker').val('');
      }
    });
  
    $('#recordFormTestList').submit(function(e) {
      e.preventDefault();
      var recordId = $('#recordId').val();
      var recordName = $('#recordName').val().trim();
      if (recordName === '') {
        alert('Please enter a name.');
        return;
      }
  
      var recordDates = datesArray;
  
      var recordData = {
        id: recordId,
        name: recordName,
        dates: recordDates
      };
  
      if (recordId) {
        // Update existing record
        console.log("update")
        updateRecord(recordData);
      } else {
        // Create new record¨
        console.log("create")
        createRecord(recordData);
      }
    });
  
    $('#cancelBtn').click(function() {
      // Clear form
      cancelEdit();
    });
  
    // $('#tagContainer').on('click', '.tag .close', function() {
    //   var tag = $(this).parent();
    //   var dateText = tag.text();
    //   console.log("clicked")
    //   datesArray = datesArray.filter(function(date) {
    //     tagcontent = date.start + " --- " + date.end
    //     console.log(tagcontent,dateText)
    //     return tagcontent !== dateText;
    //   });
    //   tag.remove();
    // });
  
    function getRecords() {
      $.ajax({
        url: apiUrl,
        method: 'GET',
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        success: function(data) {
          renderRecords(data);
        },
        error: function(xhr, status, error) {
          console.log(error);
        }
      });
    }
  
    function createRecord(recordData) {
    jsonString = JSON.stringify(recordData);
      $.ajax({
        url: apiUrl,
        method: 'POST',
        contentType: "application/json",
        dataType: "json",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        data: jsonString,
        success: function(data) {
          getRecords();
          cancelEdit();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
      });
    }
  
    function updateRecord(recordData) {
      var recordId = recordData.id;
      jsonString = JSON.stringify(recordData);
      $.ajax({
        url: apiUrl + '/' + recordId,
        method: 'PUT',
        contentType: "application/json",
        dataType: "json",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        data: jsonString,
        success: function(data) {
          getRecords();
          cancelEdit();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
      });
    }
  
    function deleteRecord(recordData) {
      $.ajax({
        url: apiUrl + '/' + recordData.id,
        method: 'DELETE',
        contentType: "application/json",
        dataType: "json",
        beforeSend: function (xhr) {
            xhr.setRequestHeader('X-API-Key',
                API_KEY); },
        success: function(data) {
          getRecords();
        },
        error: function(xhr, status, error) {
            var err = eval("(" + xhr.responseText + ")");
            window.alert(JSON.stringify(xhr));
            console.log(JSON.stringify(xhr));
        }
      });
    }
  
    // Load initial records
    getRecords();
  });
  