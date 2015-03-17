/* jshint jquery:true, browser:true */

$(document).ready(function () {
  'use strict';

  $('img.maybe-unavailable').error(function() {
    var $img = $(this),
        url = $img.attr('src');

    $img.off('error');
    $img.attr('src', url.replace('_thumbnail', ''));
  });
});
