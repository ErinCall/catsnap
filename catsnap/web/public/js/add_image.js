/* jshint jquery:true, browser:true */

$(document).ready(function () {
  'use strict';

  var catsnap = window.catsnap,
      sendImage,
      receiveImageData,
      showError,
      tagLink,
      appendAddPane,
      saveAttributes,
      saveAlbum,
      availableRow,
      waitForImage,
      suffixOrder = {
        _thumbnail: 0,
        _small: 1,
        _medium: 2,
        _large: 3,
        '': 4
      };

  sendImage = function(event) {
    var $this = $(this),
        formData = new FormData(this),
        $article = $this.parent('article');

    event.preventDefault();
    $this.find('input').addClass('disabled').attr('disabled', true);
    formData.append('album_id', $('select[name="album"]').val());

    $article.find('div.alert').remove();

    $.ajax($this.attr('action') + '.json', {
      type: $this.attr('method'),
      data: formData,
      contentType: false,
      processData: false,
      success: function(data) {
        var $newAddPane = $article.clone(true);
        $article.remove();

        $.each(data, function(i, datum) {
          var $editPane = $('<article class="image-control">'),
              $targetRow = availableRow();

          $targetRow.append($editPane);
          receiveImageData.call($editPane, datum);
        });

        appendAddPane($newAddPane);
      },
      error: function(data) {
        $article.find('form').show();
        $article.find('img').remove();
        $this.find('input').removeClass('disabled').attr('disabled', false);
        showError.call($article, data);
      }
    });
  };

  receiveImageData = function(data) {
    var $titleInput,
        $titleForm,
        $throbberLink,
        $throbberImage,
        $descriptionArea,
        $descriptionForm,
        $ul;

    $throbberImage = $('<img src="/public/img/large-throbber.gif" class="throbber">');
    $throbberLink = $('<a href="/image/' + data.image_id + '">');
    $throbberLink.append($throbberImage);
    this.append($throbberLink);
    this.data('image-id', data.image_id);
    this.data('url', data.url);

    waitForImage.call(this, data.task_id);

    $titleInput = $('<input type="text" placeholder="Title" ' +
                    'name="title" class="form-control">');
    $descriptionArea = $('<textarea placeholder="Description" ' +
                         'class="form-control" name="description">');

    $($titleInput).add($descriptionArea).blur(function() {
      $(this).parent('form').submit();
    });

    $titleForm = $('<form method="post" action="#">');
    $titleForm.submit(saveAttributes);
    $titleForm.append($titleInput);
    this.append($titleForm);

    $ul = $('<ul class="edit-tags"><li class="tag"></li></ul>');
    $ul.children('li').append(tagLink.call(this));
    this.append($ul);

    $descriptionForm = $('<form method="post" action="#">');
    $descriptionForm.append($descriptionArea);
    $descriptionForm.append($('<input type="submit" value="Save" ' +
             'class="btn btn-default edit" name="save">'));
    $descriptionForm.submit(saveAttributes);

    this.append($descriptionForm);
  };

  saveAttributes = function(event) {
    var $form = $(this),
        $article = $form.parent('article'),
        $saveButton = $article.find('input[type="submit"]'),
        $titleInput = $article.find('input[name="title"]'),
        $descriptionInput = $article.find('textarea[name="description"]');

    event.preventDefault();

    $saveButton.addClass('disabled');
    $.ajax(window.catsnap.editingUrl($article), {
      type: "PATCH",
      data: {
        title: $titleInput.val(),
        description: $descriptionInput.val(),
      },
      success: function() {
        $saveButton.removeClass('disabled');
      },
      error: function(data, status, errorThrown) {
        showError.call($article, errorThrown);
        $saveButton.removeClass('disabled');
      }
    });
  };

  appendAddPane = function($article) {
    var $targetRow = availableRow();

    $targetRow.append($article);
    $article.find('input').val(null);
    $article.find('input').removeClass('disabled').attr('disabled', false);
    $article.find('input[type="submit"]').val('Go');
    $article.find('label').text('Select');
    $article.show();
  };

  availableRow = function() {
    var $lastRow = $('.row').last();
    if ($lastRow.find('article').length >= 3) {
      $lastRow.parent().append($('<section class="row">'));
    }
    return $('.row').last();
  };

  tagLink = function() {
    var $container = this,
        $addButton = $('<button class="btn btn-xs btn-default add-tag"><span class="glyphicon glyphicon-plus-sign"></span></button>'),
        $a = $('<a href="#" class="add-tag">Add tag</a>');

    function startEditing(event) {
      var abortEditing,
          submitTag,
          $thisLi = $(event.target).parent(),
          $tagInput,
          $form;
      event.preventDefault();
      $thisLi.find('*').hide();

      $form = $('<form><input type="submit" class="enter-to-submit"></form>');
      $tagInput = $('<input type="text" class="edit form-control" name="tag" autocapitalize="none">');
      $form.prepend($tagInput);

      abortEditing = catsnap.generateAbortEditing($tagInput, $a.add($addButton), $form);

      submitTag = window.catsnap.generateSubmitTag(
          $form, $container, abortEditing, showError.bind($container), function() {
        var $nextLi = $('<li class="tag">'),
            $removeButton = $('<button class="btn btn-xs btn-default remove-tag">'),
            $xSign = $('<span class="glyphicon glyphicon-remove-sign" aria-label="remove">'),
            $tag = $('<a href="#">'),
            tagName = $tagInput.val().trim(),
            removeTag,
            newTagLink;

        $thisLi.find('*').remove();

        removeTag = catsnap.generateRemoveTag($container, $thisLi.remove);

        $tag.text(tagName);
        $removeButton.append($xSign);
        $thisLi.append([$removeButton, ' ', $tag]);
        $removeButton.click(removeTag);
        $tag.click(removeTag);

        newTagLink = tagLink.call($container);
        $nextLi.append(newTagLink);
        $container.find('ul').append($nextLi);
      });

      $tagInput.blur(submitTag);
      $form.submit(submitTag);
      catsnap.tagKeyListeners($form, abortEditing, function() {
        $thisLi.siblings().find('a.add-tag').click();
      });

      $thisLi.append($form);
      $a.parent().append($thisLi);
      $form.find('input').focus();
    }

    $addButton.click(startEditing);
    $a.click(startEditing);

    return [$addButton, ' ', $a];
  };

  showError = function(data) {
    var message = data.responseJSON.error;
    this.find('div.alert').remove();
    this.prepend($('<div class="alert alert-warning">' + message + '</div>'));
  };

  waitForImage = function(taskId) {
    var $container = this,
        socketUrl,
        socket,
        url = this.data('url'),
        $a = $('<a href="/image/' + this.data('image-id') +'">'),
        $img = $('<img>');

    /*
    The server instance used for Selenium tests can't accept websocket
    connections, and makes a bunch of noise if we try. It also doesn't upload
    images anywhere, so there's no point hanging around.
    */
    if ($('body').data('test-server')) {
      return;
    }
    /*
    If we've failed to load image data even after receiving a websocket event
    saying it's ready, the most likely problem is that the image just hasn't
    propagated out to cloudfront yet, so check again once per second (If the
    timeout function fires before the image is really ready, this error
    handler will fire again).
    */
    $img.error(function() {
      $img.data('failed_src', $img.attr('src'));
      $img.removeAttr('src');
      window.setTimeout(function() {
        /*
        failed_src may have been cleared below, in the rare case where we
        received suffixes out of order and got a better one after the error
        handler already fired.
        */
        if ($img.data('failed_src' !== undefined)) {
          $img.attr('src', $img.data('failed_src'));
          $img.removeData('failed_src');
        }
      }, 1000);
    });

    /*
    We successfully loaded the image! Remove any other images in the edit pane
    and append the new image element.
    */
    $img.load(function() {
      $container.find('img').remove();
      $a.append($img);
      $container.prepend($a);
    });

    /*
    Open a websocket and ask to be notified when the image has been uploaded.
    */
    socketUrl = document.location.origin.replace('http', 'ws') + '/task_info';
    socket = new WebSocket(socketUrl);

    socket.addEventListener('message', function(message) {
      var suffix = message.data;
      // if this is the first suffix we've heard about, or we're hearing about
      // a better one...
      if ($container.data('suffix') === undefined ||
          suffixOrder[suffix] < suffixOrder[$container.data('suffix')]) {
        $img.removeData('failed_src');
        $container.data('suffix', suffix);
        $img.attr('src', url + suffix);
      }
    });

    socket.addEventListener('open', function() {
      socket.send(JSON.stringify({task_id: taskId}));
    });
  };

  saveAlbum = function(event) {
    var $form = $(this),
        $modalHeader = $('#new-album').find('.modal-header'),
        $albumInput = $form.find('input[type="text"]'),
        albumName = $albumInput.val();

    event.preventDefault();

    $.ajax($form.attr('action') + '.json', {
      type: "POST",
      data: {name: albumName},
      success: function(data) {
        var $albumDropdown = $('#album'),
            $modal = $('#new-album'),
            $option;

        $option = $('<option>');
        $option.text(albumName);
        $option.val(data.album_id);
        $albumDropdown.append($option);
        $albumDropdown.val(data.album_id);

        $modalHeader.find('div.alert').remove();
        $albumInput.val('');
        $modal.modal('hide');
      },
      error: showError.bind($modalHeader),
    });
  };

  $('.image-control form').submit(sendImage);
  $('#new-album form').submit(saveAlbum);
  $('input[type="file"]').on('change', function() {
    var numFiles = $(this).prop('files').length,
        displayText = $(this).val();

    if (numFiles > 1) {
      displayText = displayText + ', ' + (numFiles - 1) + ' more';
    }
    $(this).siblings('label').text(displayText);
  });
});
