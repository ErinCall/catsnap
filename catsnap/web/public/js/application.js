$(document).ready(function () {
    'use strict';

    /* Firefox ignores percentage widths on file inputs, but absolute
    sizes work, so follow the underlay label as it's sized and resized.
    */
    var input_size_fix = function () {
        $('input[type="file"]').width($('label.btn').width());
        $('input[type="file"]').height($('label.btn').height() * 1.4);
    };
    input_size_fix();
    $(window).resize(input_size_fix);

    $('a.form-submitter').click(function(e) {
        e.preventDefault();
        $(this).children('form').submit();
    });

});
