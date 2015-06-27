/* jshint jquery:true, browser:true */
'use strict';
require('./keycodes.js');
require('./jquery-2.0.0.min.js');
require('./underscore-min.js');
require('./bootstrap.min.js');


/*

TODO: uncomment this.
It's currently commented out while I figure out what's happening
with webpack...
$(document).ready(function () {
  'use strict';

  /* Firefox ignores percentage widths on file inputs, but absolute
  sizes work, so follow the underlay label as it's sized and resized.
  */
/* TODO: also remove this comment (because JS can't nest block comments)
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
*/
