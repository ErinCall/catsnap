(function () {
	var startEditing,
		stopEditing;

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
			$throbber,
			$parent,
			text,
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
		$throbber = $("<img/>").attr('src', '/public/img/ajax-loader.gif');
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
		}
	});
})();
