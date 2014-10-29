$(document).ready(function () {
    'use strict';

    var send_image,
        receive_image_data,
        handle_upload_error,
        tag_link,
        another_add,
        check_for_image;

    send_image = function(event) {
        var $this = $(this),
            form_data = new FormData(this),
            $article = $this.parent('article');

        event.preventDefault();

        $article.find('div.alert').remove();

        $.ajax($this.attr('action') + '.json', {
            type: $this.attr('method'),
            data: form_data,
            contentType: false,
            processData: false,
            success: _.bind(receive_image_data, $article),
            error: _.bind(handle_upload_error, $article),
        });
    };

    receive_image_data = function(data) {
        var delay = 2000, //milliseconds
            $ul;

        another_add(this.clone(true));
        this.find('form').hide();
        this.append($('<img src="/public/img/large-throbber.gif">'));
        this.data('image_id', data.image_id);
        this.data('url', data.url);
        window.setTimeout(_.bind(check_for_image, this, delay), delay);

        this.children('form').remove();
        this.append($('<input type="text" name="title" placeholder="Title" class="form-control">'));

        $ul = $('<ul><li class="tag"></li></ul>');
        $ul.children('li').append(_.bind(tag_link, this)());
        this.append($ul);

        this.append($('<textarea placeholder="Description" class="form-control" name="description">'));
        this.append($('<input type="submit" value="Save" class="btn btn-default edit">'));
    };

    another_add = function($article) {
        var $last_row = $('.row').last(),
            $target_row;
        if ($last_row.find('article').length >= 3) {
            $target_row = $('<section class="row">');
            $last_row.parent().append($target_row);
        } else {
            $target_row = $last_row;
        }

        $target_row.append($article);
        $article.find('input').val(null);
        $article.find('input[type="submit"]').val('Go');
        $article.find('label').text('Select');
        $article.show();
    };

    tag_link = function() {
        var $container = this,
            $a = $('<a href=#>Add tag</a>');

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

                $.ajax('/image/' + $container.data('image_id') + '.json', {
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

                        new_tag_link = _.bind(tag_link, $container)();
                        $next_li.append(new_tag_link);
                        $container.find('ul').append($next_li);
                    }].concat(success_events),
                    error: function(jqXHR, status, errorThrown) {
                        alert(errorThrown);
                    }
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

    handle_upload_error = function(data) {
        var message = data.responseJSON.error;
        this.prepend($('<div class="alert alert-warning">' + message + '</div>'));
        this.find('form').show();
        this.find('img').remove();
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

    $('.add form').submit(send_image);
    $('input[type="file"]').on('change', function(event) {
        $(this).siblings('label').text($(this).val());
    });
});
