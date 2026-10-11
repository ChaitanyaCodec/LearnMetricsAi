(() => {
    "use strict";
    const form = document.getElementById("teacher-document-form");
    if (!form) return;

    const subjectSelect = document.getElementById("document-subject");
    const sourceSelect = document.getElementById("document-sources");
    const instructionsInput = document.getElementById("document-instructions");
    const titleInput = document.getElementById("generated-document-title");
    const contentInput = document.getElementById("generated-document-content");
    const generateButton = document.getElementById("generate-document-button");
    const generationStatus = document.getElementById("generation-status");
    const exportStatus = document.getElementById("export-status");
    const csrfInput = form.querySelector("[name=csrfmiddlewaretoken]");

    const setStatus = (element, message, isError = false) => {
        element.textContent = message;
        element.classList.toggle("text-danger", isError);
        element.classList.toggle("text-success", !isError && Boolean(message));
    };

    const postJSON = async (url, payload) => {
        const response = await fetch(url, {
            method: "POST",
            credentials: "same-origin",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": csrfInput ? csrfInput.value : "",
            },
            body: JSON.stringify(payload),
        });
        if (!response.ok) {
            let message = "Request failed. Please try again.";
            try {
                const data = await response.json();
                if (data.error) message = data.error;
            } catch (_) { /* Use the safe fallback. */ }
            throw new Error(message);
        }
        return response;
    };

    const filterSources = () => {
        const selectedSubject = subjectSelect.value;
        Array.from(sourceSelect.options).forEach((option) => {
            const allowed = !selectedSubject || option.dataset.subjectId === selectedSubject;
            option.hidden = !allowed;
            if (!allowed) option.selected = false;
        });
    };
    subjectSelect.addEventListener("change", filterSources);
    filterSources();

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        const selectedSources = Array.from(sourceSelect.selectedOptions).map((option) => Number(option.value));
        if (selectedSources.length > 5) {
            setStatus(generationStatus, "Select no more than five source documents.", true);
            return;
        }
        if (!subjectSelect.value) {
            setStatus(generationStatus, "Choose an assigned subject first.", true);
            return;
        }
        generateButton.disabled = true;
        setStatus(generationStatus, "Generating draft… this may take a moment.");
        try {
            const response = await postJSON("/rag/teacher/documents/generate/", {
                subject_id: Number(subjectSelect.value),
                instructions: instructionsInput.value,
                source_document_ids: selectedSources,
            });
            const result = await response.json();
            titleInput.value = result.title || "Teacher document draft";
            contentInput.value = result.content || "";
            setStatus(generationStatus, `Draft generated for ${result.subject_name}. Review it before exporting.`);
            setStatus(exportStatus, "");
        } catch (error) {
            setStatus(generationStatus, error.message || "Could not generate the draft.", true);
        } finally {
            generateButton.disabled = false;
        }
    });

    document.querySelectorAll("[data-export-format]").forEach((button) => {
        button.addEventListener("click", async () => {
            const format = button.dataset.exportFormat;
            const content = contentInput.value;
            if (!content.trim()) {
                setStatus(exportStatus, "Generate or enter document content before exporting.", true);
                return;
            }
            button.disabled = true;
            setStatus(exportStatus, `Preparing ${format.toUpperCase()} download…`);
            try {
                const response = await postJSON(`/rag/teacher/documents/export/${format}/`, {
                    title: titleInput.value,
                    filename: titleInput.value || "teacher-document",
                    content,
                });
                const blob = await response.blob();
                const disposition = response.headers.get("Content-Disposition") || "";
                const match = disposition.match(/filename="?([^";]+)"?/i);
                const filename = match ? match[1] : `teacher-document.${format}`;
                const objectUrl = URL.createObjectURL(blob);
                const link = document.createElement("a");
                link.href = objectUrl;
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                link.remove();
                URL.revokeObjectURL(objectUrl);
                setStatus(exportStatus, `${format.toUpperCase()} download started.`);
            } catch (error) {
                setStatus(exportStatus, error.message || "Could not export this document.", true);
            } finally {
                button.disabled = false;
            }
        });
    });
})();
