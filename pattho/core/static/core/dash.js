document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard script initialized.");

    const csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;
    let pendingChanges = {};
    let debounceTimer;

    // To change the auto-save delay, modify the value below (in milliseconds).
    const DEBOUNCE_DELAY = 5000; // 10 seconds

    const checkboxes = document.querySelectorAll('.checkbox-group input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const chapterRow = this.closest('.chapter-row');
            const chapterId = chapterRow.dataset.chapterId;
            const field = this.dataset.field;
            const isChecked = this.checked;

            console.log(`Change detected: Chapter ${chapterId}, Field ${field}, Status ${isChecked}`);

            // Instantly update the UI for a responsive feel.
            updateChapterProgressUI(chapterRow);

            // Add the change to our pending queue for saving.
            if (!pendingChanges[chapterId]) {
                pendingChanges[chapterId] = {};
            }
            pendingChanges[chapterId][field] = isChecked;

            // Reset the debounce timer to save changes after a period of inactivity.
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(saveProgress, DEBOUNCE_DELAY);

            console.log(`Debounce timer reset. Will save in ${DEBOUNCE_DELAY / 1000} seconds.`);
        });
    });

    function updateChapterProgressUI(chapterRow) {
        // Define weights for each field (must match Python backend)
        const WEIGHTS = {
            'p_theory': 0.10,
            'p_note': 0.20,
            'p_mcq': 0.20,
            'p_cq': 0.35,
            'p_book': 0.15 // Corresponds to Class/Concept
        };

        const chapterCheckboxes = chapterRow.querySelectorAll('.checkbox-group input[type="checkbox"]');
        let weightedSum = 0;

        chapterCheckboxes.forEach(checkbox => {
            if (checkbox.checked) {
                const field = checkbox.dataset.field;
                if (WEIGHTS[field]) {
                    weightedSum += WEIGHTS[field];
                }
            }
        });

        const newProgress = Math.round(weightedSum * 100);

        console.log(`Updating UI instantly for Chapter ${chapterRow.dataset.chapterId}. New calculated progress: ${newProgress}%`);

        const progressBar = chapterRow.querySelector('.progress-bar');
        const progressText = chapterRow.querySelector('.progress-text');

        if (progressBar) progressBar.style.width = newProgress + '%';
        if (progressText) progressText.textContent = newProgress + '%';
    }

    function saveProgress() {
        if (Object.keys(pendingChanges).length === 0) {
            console.log("No pending changes to save.");
            return Promise.resolve(); // Return a resolved Promise if nothing to save
        }

        console.log("Saving progress to server...", pendingChanges);

        // Make a copy of the changes and clear the queue immediately.
        const changesToSave = pendingChanges;
        pendingChanges = {};

        return fetch(window.updateProgressUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ changes: changesToSave })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok (${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                console.log("Progress saved successfully. Syncing UI with server state:", data);
                // Sync the UI with the authoritative progress from the server.
                for (const chapterId in data.new_progress) {
                    const chapterRow = document.querySelector(`.chapter-row[data-chapter-id="${chapterId}"]`);
                    if (chapterRow) {
                        const serverProgress = data.new_progress[chapterId];
                        console.log(`Syncing Chapter ${chapterId} to server progress: ${serverProgress}%`);
                        const progressBar = chapterRow.querySelector('.progress-bar');
                        const progressText = chapterRow.querySelector('.progress-text');
                        if (progressBar) progressBar.style.width = serverProgress + '%';
                        if (progressText) progressText.textContent = serverProgress + '%';
                    }
                }
            } else {
                console.error('Failed to save progress:', data.error);
                // Note: In a real-world app, you might want to add logic here to restore the pending changes
                // and alert the user that saving failed.
            }
            return data; // Return data for further chaining if needed
        })
        .catch(error => {
            console.error('Error saving progress:', error);
            throw error; // Re-throw to propagate the error to the caller
        });
    }

    // Save any remaining changes when the user tries to leave the page.
    window.addEventListener('beforeunload', function(event) {
        if (Object.keys(pendingChanges).length > 0) {
            console.log("User is leaving. Saving pending changes immediately.");
            saveProgress();
            // This message is usually not shown in modern browsers, but is required for the event to trigger.
            event.preventDefault();
            event.returnValue = 'Your changes are being saved.';
        }
    });

    // Expose pendingChanges and saveProgress to a global object for use in other scripts (e.g., layout.html)
    window.app = window.app || {};
    window.app.pendingChanges = pendingChanges;
    window.app.saveProgress = saveProgress;

    // Initialize Lucide icons
    lucide.createIcons();
    console.log("Lucide icons initialized.");
});