$(document).ready(function () {
    'use strict';

    var send_image,
        receive_image_data,
        handle_upload_error,
        tag_link,
        check_for_image;

    send_image = function(event) {
        var $this = $(this),
            form_data = new FormData(this),
            $article = $this.parent('article');

        event.preventDefault();

        $this.hide();
        $article.append($('<img src="/public/img/large-throbber.gif">'));
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

        this.data('image_id', data.image_id);
        this.data('url', data.url);
        window.setTimeout(_.bind(check_for_image, this, delay), delay);

        this.children('form').remove();
        this.append($('<input type="text" placeholder="Title" class="form-control">'));

        $ul = $('<ul><li class="tag"></li></ul>');
        $ul.children('li').append(_.bind(tag_link, this)());
        this.append($ul);

        this.append($('<textarea placeholder="Description" class="form-control">'));
        this.append($('<input type="submit" value="Save" class="btn btn-default edit">'));
    };

    tag_link = function() {
        var $container = this,
            $a = $('<a href=#>Add tag</a>');

        $a.click(function(event) {
            var tag_name,
                $this_li = $(this).parent(),
                $form;
            event.preventDefault();
            $a.hide();

            $form = $('<form><input type="text" class="edit form-control"/><input type="submit" class="enter-to-submit"/></form>');
            $form.submit(function(event) {
                event.preventDefault();
                tag_name = $form.find('input[type=text]').val();
                $form.find('input').attr('disabled', true);

                $.ajax('/image/' + $container.data('image_id') + '.json', {
                    type: "PATCH",
                    data: {add_tag: tag_name},
                    success: function(data) {
                        var $next_li = $('<li class="tag">'),
                            $name_span = $('<span>'),
                            new_tag_link;

                        $a.remove();
                        $form.remove();

                        $name_span.append(tag_name);
                        $this_li.append($name_span);

                        new_tag_link = _.bind(tag_link, $container)();
                        $next_li.append(new_tag_link);
                        $container.find('ul').append($next_li);
                    },
                    error: function(jqXHR, status, errorThrown) {
                        alert(errorThrown);
                    }
                });
            });

            $this_li.append($form);
            $a.parent().append($this_li);
            $form.find('input').focus();
        });
        return $a;
    };

    handle_upload_error = function(data) {
        console.log(data);
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
    $('input[type="file"]').change(function(event) {
        $(this).siblings('label').text($(this).val());
    });
});
