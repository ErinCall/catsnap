$(document).ready(function () {
    'use strict';

    var send_image,
        receive_image_data,
        show_error,
        tag_link,
        append_add_pane,
        save_attributes,
        editing_url,
        save_album,
        available_row,
        check_for_image;

    send_image = function(event) {
        var $this = $(this),
            form_data = new FormData(this),
            $article = $this.parent('article');

        event.preventDefault();
        $this.find('input').addClass('disabled').attr('disabled', true);
        form_data.append('album_id', $('select[name="album"]').val());

        $article.find('div.alert').remove();

        $.ajax($this.attr('action') + '.json', {
            type: $this.attr('method'),
            data: form_data,
            contentType: false,
            processData: false,
            success: function(data) {
                var $new_add_pane = $article.clone(true);
                $article.remove();

                $.each(data, function(i, datum) {
                    var $edit_pane = $('<article class="image-control">'),
                        $target_row = available_row();

                    $target_row.append($edit_pane);
                    receive_image_data.call($edit_pane, datum);
                });

                append_add_pane($new_add_pane);
            },
            error: function(data, status, errorThrown) {
                $article.find('form').show();
                $article.find('img').remove();
                $this.find('input').removeClass('disabled').attr('disabled', false);
                show_error.call($article, data);
            }
        });
    };

    receive_image_data = function(data) {
        var delay = 2000, //milliseconds
            $form,
            $ul;

        this.append($('<img src="/public/img/large-throbber.gif" class="throbber">'));
        this.data('image_id', data.image_id);
        this.data('url', data.url);
        window.setTimeout(_.bind(check_for_image, this, delay), delay);

        $form = $('<form method="post" action="#">');
        $form.append($('<input type="text" name="title" ' +
                       'placeholder="Title" class="form-control">'));

        $ul = $('<ul><li class="tag"></li></ul>');
        $ul.children('li').append(tag_link.call(this));
        $form.append($ul);

        $form.append($('<textarea placeholder="Description" ' +
                       'class="form-control" name="description">'));
        $form.append($('<input type="submit" value="Save" ' +
                       'class="btn btn-default edit" name="save">'));
        $form.submit(save_attributes);
        $form.find('input').blur(function() {
            $(this).parent('form').submit();
        });
        this.append($form);
    };

    save_attributes = function(event) {
        var $form = $(this),
            $save_button = $form.find('input[type="submit"]'),
            $title_input = $form.find('input[name="title"]'),
            $description_input = $form.find('textarea[name="description"]'),
            $article = $form.parent('article');

        event.preventDefault();

        $save_button.addClass('disabled');
        $.ajax(editing_url($article), {
            type: "PATCH",
            data: {
                title: $title_input.val(),
                description: $description_input.val(),
            },
            success: function(data) {
                $save_button.removeClass('disabled');
            },
            error: function(data, status, errorThrown) {
                show_error.call($article, errorThrown);
                $save_button.removeClass('disabled');
            }
        });
    };

    append_add_pane = function($article) {
        var $target_row = available_row();

        $target_row.append($article);
        $article.find('input').val(null);
        $article.find('input').removeClass('disabled').attr('disabled', false);
        $article.find('input[type="submit"]').val('Go');
        $article.find('label').text('Select');
        $article.show();
    };

    available_row = function() {
        var $last_row = $('.row').last();
        if ($last_row.find('article').length >= 3) {
            $last_row.parent().append($('<section class="row">'));
        }
        return $('.row').last();
    };

    tag_link = function() {
        var $container = this,
            $a = $('<a href="#">Add tag</a>');

        $a.click(function(event) {
            var tag_name,
                abort_editing,
                submit_tag,
                $this_li = $(this).parent(),
                $tag_input,
                $form;
            event.preventDefault();
            $a.hide();

            submit_tag = function(event, success_events) {
                event.preventDefault();
                tag_name = $form.find('input[type=text]').val().trim();
                if (tag_name === "") {
                    abort_editing();
                    return;
                }
                $form.find('input').attr('disabled', true);
                if (typeof(success_events) === 'undefined') {
                    success_events = [];
                }

                $.ajax(editing_url($container), {
                    type: "PATCH",
                    data: {add_tag: tag_name},
                    success: [function(data) {
                        var $next_li = $('<li class="tag">'),
                            $name_span = $('<span class="tag">'),
                            new_tag_link;

                        $a.remove();
                        $form.remove();

                        $name_span.append(tag_name);
                        $this_li.append($name_span);

                        new_tag_link = tag_link.call($container);
                        $next_li.append(new_tag_link);
                        $container.find('ul').append($next_li);
                    }].concat(success_events),
                    error: _.bind(show_error, $container),
                });
            };
            $form = $('<form><input type="submit" class="enter-to-submit"/></form>');
            $tag_input = $('<input type="text" class="edit form-control" name="tag"/>');
            $form.prepend($tag_input);
            $form.submit(submit_tag);
            $tag_input.blur(_.bind(submit_tag, $form));
            $tag_input.keydown(function(event) {
                if (event.which === KeyCodes.ENTER) {
                    event.preventDefault();
                    $form.trigger('submit', function() {
                        $this_li.siblings().find('a').click();
                    });
                } else if (event.which == KeyCodes.ESCAPE) {
                    abort_editing();
                }
            });

            abort_editing = function () {
                $a.show();
/* In Firefox (at least), if there's an autocompletion box up when the input
is removed, the input goes away correctly but the autocompletion box hangs
around. Blurring the element first seems to be a sufficient workaround.
Bug reported: https://bugzilla.mozilla.org/show_bug.cgi?id=1091954
*/
                $tag_input.off('blur');
                $tag_input.blur();
                $tag_input.remove();
            };

            $this_li.append($form);
            $a.parent().append($this_li);
            $form.find('input').focus();
        });
        return $a;
    };

    show_error = function(data) {
        var message = data.responseJSON.error;
        this.find('div.alert').remove();
        this.prepend($('<div class="alert alert-warning">' + message + '</div>'));
    };

    check_for_image = function(previous_timeout) {
        var $container = this,
            url = this.data('url'),
            new_timeout = previous_timeout * 1.4,
            $a = $('<a href="/image/' + this.data('image_id') +'">'),
            $img = $('<img>');

        $img.error(function() {
            $img.off('error');
            $img.error(function() {
                window.setTimeout(_.bind(
                    check_for_image, $container, new_timeout), new_timeout);
            });
            $img.attr('src', url);
        });
        $img.load(function() {
            $container.find('img').remove();
            $a.append($img);
            $container.prepend($a);
        });
        $img.attr('src', url + '_thumbnail');
    };

    editing_url = function($element) {
        return "/image/" + $element.data('image_id') + '.json';
    };

    save_album = function(event) {
        var $form = $(this),
            $modal_header = $('#new-album').find('.modal-header'),
            $album_input = $form.find('input[type="text"]'),
            album_name = $album_input.val();

        event.preventDefault();

        $.ajax($form.attr('action') + '.json', {
            type: "POST",
            data: {name: album_name},
            success: function(data) {
                var $album_dropdown = $('#album'),
                    $modal = $('#new-album'),
                    $option;

                $option = $('<option>');
                $option.text(album_name);
                $option.val(data.album_id);
                $album_dropdown.append($option);
                $album_dropdown.val(data.album_id);

                $modal_header.find('div.alert').remove();
                $album_input.val('');
                $modal.modal('hide');
            },
            error: _.bind(show_error, $modal_header),
        });
    };

    $('.image-control form').submit(send_image);
    $('#new-album form').submit(save_album);
    $('input[type="file"]').on('change', function(event) {
        var num_files = $(this).prop('files').length,
            display_text = $(this).val();

        if (num_files > 1) {
            display_text = display_text + ', ' + (num_files - 1) + ' more';
        }
        $(this).siblings('label').text(display_text);
    });
});
