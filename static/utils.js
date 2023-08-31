// Requête Ajax
function makeAjaxRequest(url, type, data, onSuccess) {
    $.ajax({
        url: url,
        type: type,
        contentType: 'application/json',
        data: JSON.stringify(data),
        success: onSuccess
    });
}