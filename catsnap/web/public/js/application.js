$(document).ready(function () {
    'use strict';

    $('a.form-submitter').click(function(e) {
        e.preventDefault();
        $(this).children('form').submit();
    });

});
