/* jshint jquery:true, browser:true */

$(document).ready(function () {
  'use strict';

  /* Firefox ignores percentage widths on file inputs, but absolute
  sizes work, so follow the underlay label as it's sized and resized.
  */
  var inputSizeFix = function () {
    $('input[type="file"]').width($('label.btn').width());
    $('input[type="file"]').height($('label.btn').height() * 1.4);
  };
  inputSizeFix();
  $(window).resize(inputSizeFix);

  $('a.form-submitter').click(function(e) {
    e.preventDefault();
    $(this).children('form').submit();
  });

});
