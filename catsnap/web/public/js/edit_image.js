(function () {
	var startEditing,
		stopEditing;

	startEditing = function (event) {
		var $input,
			$form,
			$this = $(this);

		$form = $("<form/>");
		$input = $("<input/>").val($this.text().trim());
		$input.blur(function (event) {
			_.bind(stopEditing, $form, event)();
		});
		$form.submit(function (event) {
			event.preventDefault();
			_.bind(stopEditing, $form, event)();
		});
		$form.append($input);
		$this.parent().append($form);
		$this.remove();
		$input.focus();
		$input.select();
	};

	stopEditing = function (event) {
		var $h2,
			$throbber,
			$parent,
			text,
			$this = $(this);

		$parent = $this.parent();
		text = $this.children().val().trim();
		$h2 = $("<h2/>").text(text);
		$h2.click(startEditing);
		$throbber = $("<img/>").attr('src', '/public/img/ajax-loader.gif');
		$parent.append($throbber);
		$this.remove();
		$.ajax('/image/' + window.image_id + '.json', {
			type: "PATCH",
			data: {attributes: JSON.stringify({title: text})},
			success: function(data, status, jqXHR) {
				$throbber.remove();
				$parent.append($h2);
				$('title').text(text + ' - Catsnap');
			},
			error: function(jqXHR, status, errorThrown) {
				$throbber.remove();
				alert(errorThrown);
			}
		});
	};

	$(function() {
		if (window.logged_in) {
			$('header h2').click(startEditing);
		}
	});
})();
