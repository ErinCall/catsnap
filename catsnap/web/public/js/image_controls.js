/* jshint jquery:true, browser:true */
/* global KeyCodes, _ */

$(document).ready(function () {
  'use strict';

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

  function editingUrl ($element) {
    return "/image/" + $element.data('image-id') + '.json';
  }

  if (typeof window.catsnap === 'undefined') {
    window.catsnap = {};
  }

  window.catsnap.generateSubmitTag = generateSubmitTag;
  window.catsnap.editingUrl = editingUrl;
});
