(function () {
    'use strict';
    var throbber,
        start_editing,
        stop_editing,
        set_album,
        change_album,
        submit_tag,
        remove_tag,
        add_tag;

    start_editing = function (event, display_element, edit_element, on_success) {
        var $edit,
            $form,
            attribute,
            $this = $(this);

        attribute = $this.data('attribute');
        $form = $('<form class="navbar-form">');
        $edit = $("<" + edit_element + ' class="form-control">');
        $edit.val($this.text().trim());
        $edit.blur(function (event) {
            _.bind(stop_editing, $form,
                    event, attribute, display_element, edit_element, on_success)();
        });
        $form.submit(function (event) {
            event.preventDefault();
            _.bind(stop_editing, $form,
                    event, attribute, display_element, edit_element, on_success)();
        });
        $form.append($edit);
        $this.parent().append($form);
        $this.remove();
        $edit.focus();
        $edit.select();
    };

    stop_editing = function (event,
            attribute,
            display_element,
            edit_element,
            on_success) {
        var $display,
            $parent,
            text,
            $throbber = throbber(),
            post_data = {},
            $this = $(this);

        $parent = $this.parent();
        text = $this.children().val().trim();
        $display = $("<" + display_element + "/>").text(text);
        $display.data('attribute', attribute);
        $display.click(function(event) {
            _.bind(start_editing, $display,
                    event, display_element, edit_element)();
        });
        $parent.append($throbber);
        $this.remove();
        post_data[attribute] = text;
        $.ajax('/image/' + window.image_id + '.json', {
            type: "PATCH",
            data: {attributes: JSON.stringify(post_data)},
            success: function(data, status, jqXHR) {
                $throbber.remove();
                $parent.append($display);
                if (typeof on_success !== 'undefined') {
                    on_success(text);
                }
            },
            error: function(jqXHR, status, errorThrown) {
                $throbber.remove();
                alert(errorThrown);
            }
        });
    };

    set_album = function(event, albums) {
        var $parent,
            $form,
            $select,
            $blank_option,
            $new_album_link,
            $this = $(this);

        $parent = $this.parent();
        if (typeof albums === 'undefined') {
            albums = {};
            _.each($parent.find('.data'), function(element) {
                var $element = $(element);
                albums[$element.data('id')] = $element.data('name');
            })
        }

        $form = $('<form class="navbar-form">');
        $select = $('<select class="form-control name="album">');
        $form.append($select);
        $blank_option = $('<option/>');
        $blank_option.text('(no album)');
        $blank_option.val('');
        $select.append($blank_option);
        _.each(_.keys(albums), function(album_id) {
            var $option;
            $option = $('<option/>');
            $option.text(albums[album_id]);
            $option.val(album_id);
            if (album_id === window.album_id) {
                $option.attr('selected', 'selected');
            }
            $select.append($option);
        });
        $select.change(function(event) {
            _.bind(change_album, $select, event, albums)();
        });

        $parent.text('');
        $parent.append($form);

        $new_album_link = $('<a/>');
        $new_album_link.attr('href', '/new_album');
        $new_album_link.text('create a new album');
        $parent.append(' or ');
        $parent.append($new_album_link);
    };

    change_album = function(event, albums) {
        var $parent,
            post_data = {},
            $throbber = throbber(),
            $this = $(this);

        $parent = $this.parent();
        post_data.album_id = $this.val();
        $this.remove();
        $parent.append($throbber);

        $.ajax('/image/' + window.image_id + '.json', {
            type: "PATCH",
            data: {attributes: JSON.stringify(post_data)},
            success: function(data, status, jqXHR) {
                var $set_album,
                    $selected,
                    $link;
                if ($this.val() !== '') {
                    $selected = $this.find('option:selected');
                    $link = $('<a/>');
                    $link.attr('href', '/album/' + $this.val());
                    $link.text($selected.text());
                    $throbber.remove();
                    $parent.text("This image appears in the album '");
                    $parent.append($link);
                    $parent.append("'. ");
                } else {
                    $parent.text("This image has no album. ");
                }


                $set_album = $('<span/>');
                $set_album.text('(click to set album)');
                $set_album.click(function(event) {
                    _.bind(set_album, $set_album, event, albums)();
                });
                $parent.append($set_album);

                window.album_id = $this.val();
            },
            error: function(jqXHR, status, errorThrown) {
                $throbber.remove();
                alert(errorThrown);
            }
        });
    };

    add_tag = function(event) {
        var $form,
            $edit,
            $this = $(this);
        $form = $('<form class="navbar-form">');
        $edit = $('<input class="form-control">');
        $form.append($edit);
        $this.text('');
        $this.append($form);
        $edit.focus();
        $edit.blur(function(event) {
            _.bind(submit_tag, $this, event)();
        });
        $form.submit(function(event) {
            event.preventDefault();
            _.bind(submit_tag, $this, event)();
        });
    };

    submit_tag = function(event) {
        var tag_name,
            $throbber = throbber(),
            $this = $(this);

        tag_name = $this.find('input').val();
        $this.append($throbber);
        $this.find('form').remove();
        $.ajax('/image/' + window.image_id + '.json', {
            type: "PATCH",
            data: {add_tag: tag_name},
            success: function(data, status, jqXHR) {
                var $add_new,
                    $remove,
                    $span,
                    $link;
                $throbber.remove();
                $link = $('<a/>');
                $link.attr('href', '/find?tags=' + tag_name);
                $link.text(tag_name);
                $span = $('<span/>');
                $span.append($link);

                $this.append($span);

                $remove = $('<a/>');
                $remove.attr('href', '#');
                $remove.text('x');
                $remove.click(remove_tag);

                $this.append(' [');
                $this.append($remove);
                $this.append(']');

                $add_new = $('<li/>');
                $add_new.text('(click to add a tag)');
                $add_new.click(add_tag);
                $this.parent().append($add_new);
            },
            error: function(jqXHR, status, errorThrown) {
                $throbber.remove();
                alert(errorThrown);
            }
        });
    };

    remove_tag = function(event) {
        var tag_name,
            $parent,
            $throbber = throbber(),
            $this = $(this);
        event.preventDefault();

        $parent = $this.parent();
        tag_name = $parent.find('span').text();
        $parent.text('');
        $parent.append($throbber);
        $.ajax('/image/' + window.image_id + '.json', {
            type: "PATCH",
            data: {remove_tag: tag_name},
            success: function(data, status, jqXHR) {
                $parent.remove();
            },
            error: function(jqXHR, status, errorThrown) {
                $throbber.remove();
                alert(errorThrown);
            }
        });
    };

    throbber = function() {
        return $("<img/>").attr('src', '/public/img/ajax-loader.gif');
    };

    $(function() {
        if (window.logged_in) {
            $('div.page-head h2').click(function(event) {
                var on_success;
                on_success = function(text) {
                    $('title').text(text + ' - Catsnap');
                };
                _.bind(start_editing, this, event, 'h2', 'input', on_success)();
            });
            $('#description span').click(function(event) {
                _.bind(start_editing, this, event, 'span', 'textarea')();
            });
            $('#set-album').click(set_album);
            $('#add-tag').click(add_tag);
            $('.remove-tag').click(remove_tag);
        }
    });
})();
