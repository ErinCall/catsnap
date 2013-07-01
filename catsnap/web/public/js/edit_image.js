(function () {
	var throbber,
		startEditing,
		stopEditing,
		submitTag,
		removeTag,
		addTag;

	startEditing = function (event, display_element, edit_element, on_success) {
		var $edit,
			$form,
			attribute,
			$this = $(this);

		attribute = $this.data('attribute');
		$form = $("<form/>");
		$edit = $("<" + edit_element + "/>").val($this.text().trim());
		$edit.blur(function (event) {
			_.bind(stopEditing, $form,
					event, attribute, display_element, edit_element, on_success)();
		});
		$form.submit(function (event) {
			event.preventDefault();
			_.bind(stopEditing, $form,
					event, attribute, display_element, edit_element, on_success)();
		});
		$form.append($edit);
		$this.parent().append($form);
		$this.remove();
		$edit.focus();
		$edit.select();
	};

	stopEditing = function (event,
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
			_.bind(startEditing, $display,
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

	addTag = function(event) {
		var $form,
			$edit,
			$this = $(this);
		$form = $('<form/>');
		$edit = $('<input/>');
		$form.append($edit);
		$this.text('');
		$this.append($form);
		$edit.focus();
		$edit.blur(function(event) {
			_.bind(submitTag, $this, event)();
		});
		$form.submit(function(event) {
			event.preventDefault();
			_.bind(submitTag, $this, event)();
		})
	};

	submitTag = function(event) {
		var tag_name,
			$throbber = throbber(),
			$this = $(this);

		tag_name = $this.find('input').val();
		$this.append($throbber);
		$this.find('form').remove()
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
				$remove.click(removeTag);

				$this.append(' [')
				$this.append($remove);
				$this.append(']');

				$add_new = $('<li/>');
				$add_new.text('(click to add a tag)');
				$add_new.click(addTag);
				$this.parent().append($add_new);
			},
			error: function(jqXHR, status, errorThrown) {
				$throbber.remove();
				alert(errorThrown);
			}
		});
	};

	removeTag = function(event) {
		var tag_name,
			$parent,
			$throbber = throbber();
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
			$('header h2').click(function(event) {
				var on_success;
				on_success = function(text) {
					$('title').text(text + ' - Catsnap');
				};
				_.bind(startEditing, this, event, 'h2', 'input', on_success)();
			});
			$('#description span').click(function(event) {
				_.bind(startEditing, this, event, 'span', 'textarea')();
			});
			$('#add-tag').click(addTag);
			$('.remove-tag').click(removeTag);
		}
	});
})();
