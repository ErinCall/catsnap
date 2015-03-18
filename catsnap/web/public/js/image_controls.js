/* jshint jquery:true, browser:true */
/* global KeyCodes, _ */

$(document).ready(function () {
  'use strict';

  if (typeof window.catsnap === 'undefined') {
    window.catsnap = {};
  }
  var catsnap = window.catsnap;

  function generateSubmitTag($form, $imageIdElement, abortEditing, onError, onSuccess) {
    return function submitTag(event, successHandlers) {
      var tagName,
          $tagInput = $form.find('input[type=text]');

      event.preventDefault();

      if (typeof successHandlers === 'undefined') {
        successHandlers = [];
      }

      tagName = $tagInput.val().trim();
      if (tagName === '') {
        abortEditing();
        return;
      }

      $form.find('input').attr('disabled', true);

      $.ajax(editingUrl($imageIdElement), {
        type: 'PATCH',
        data: {add_tag: tagName},
        success: [onSuccess].concat(successHandlers),
        error: onError
      });
    };
  }

  function generateAbortEditing($tagInput, $showMe, $removeMe) {
    return function abortEditing () {
/* In Firefox (at least), if there's an autocompletion box up when the input
is removed, the input goes away correctly but the autocompletion box hangs
around. Blurring the element first seems to be a sufficient workaround.
Bug reported: https://bugzilla.mozilla.org/show_bug.cgi?id=1091954
*/
      $tagInput.off('blur');
      $tagInput.blur();
      $removeMe.remove();
      $showMe.show();
    };
  }

  function editingUrl ($element) {
    return "/image/" + $element.data('image-id') + '.json';
  }

  function tagKeyListeners($form, abortEditing, onTab) {
    $form.on('keydown', 'input[type=text]', function(event) {
      if (event.which === KeyCodes.TAB) {
        event.preventDefault();
        $form.triggerHandler('submit', onTab);
      } else if (event.which == KeyCodes.ESCAPE) {
        abortEditing();
      }
    });
  }

  catsnap.generateSubmitTag = generateSubmitTag;
  catsnap.generateAbortEditing = generateAbortEditing;
  catsnap.editingUrl = editingUrl;
  catsnap.tagKeyListeners = tagKeyListeners;
});
