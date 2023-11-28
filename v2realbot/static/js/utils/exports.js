// Function to convert a JavaScript object to CSV
function convertToCsv(data) {
    var csv = '';
    // Get the headers
    var headers = Object.keys(data[0]);
    csv += headers.join(',') + '\n';

    // Iterate over the data
    data.forEach(function (item) {
        var row = headers.map(function (header) {
            return item[header];
        });
        csv += row.join(',') + '\n';
    });

    return csv;
}

//type ("text/csv","application/xml"), filetype (csv), filename
function downloadFile(type, filetype, filename, content) {
    var blob = new Blob([content], { type: type });
    var url = window.URL.createObjectURL(blob);
    var link = document.createElement("a");
    link.href = url;
    link.download = filename +"."+filetype;
    link.click();
}

// Function to convert a JavaScript object to XML
function convertToXml(data) {
    var xml = '<?xml version="1.0" encoding="UTF-8"?>\n<trades>\n';
    data.forEach(function (item) {
        xml += '  <trade>\n';
        Object.keys(item).forEach(function (key) {
            xml += '    <' + key + '>' + item[key] + '</' + key + '>\n';
        });
        xml += '  </trade>\n';
    });
    xml += '</trades>';
    return xml;
}