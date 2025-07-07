

document.addEventListener('DOMContentLoaded', function() {
    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;
    const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const chapterRow = this.closest('.chapter-row');
            const chapterId = chapterRow.dataset.chapterId;
            const field = this.dataset.field;
            const isChecked = this.checked;

            updateProgress(chapterId, field, isChecked, chapterRow);
        });
    });

    function updateProgress(chapterId, field, isChecked, chapterRow) {
        fetch(`{% url 'update_progress' %}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                chapter_id: chapterId,
                field: field,
                status: isChecked
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const progressBar = chapterRow.querySelector('.progress-bar');
                progressBar.style.width = data.new_progress + '%';
                progressBar.textContent = data.new_progress + '%';
            } else {
                console.error('Failed to update progress');
                // Revert checkbox state on failure
                const checkbox = chapterRow.querySelector(`input[data-field="${field}"]`);
                if (checkbox) {
                    checkbox.checked = !isChecked;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const checkbox = chapterRow.querySelector(`input[data-field="${field}"]`);
            if (checkbox) {
                checkbox.checked = !isChecked;
            }
        });
    }
});