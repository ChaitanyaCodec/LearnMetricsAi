document.addEventListener("DOMContentLoaded", () => {
    const wrapper = document.querySelector(".universal-search");
    const input = document.getElementById("universalSearchInput");
    const resultsBox = document.getElementById("universalSearchResults");
    if (!wrapper || !input || !resultsBox) return;

    let debounceTimer;
    let activeController;

    const closeResults = () => {
        resultsBox.hidden = true;
        resultsBox.replaceChildren();
        input.setAttribute("aria-expanded", "false");
    };

    const showMessage = (message) => {
        resultsBox.replaceChildren();
        const item = document.createElement("div");
        item.className = "universal-search-message";
        item.textContent = message;
        resultsBox.appendChild(item);
        resultsBox.hidden = false;
        input.setAttribute("aria-expanded", "true");
    };

    const renderResults = (items) => {
        resultsBox.replaceChildren();
        if (!items.length) {
            showMessage("No matching resources found.");
            return;
        }
        items.forEach((result) => {
            const link = document.createElement("a");
            link.className = "universal-search-result";
            link.href = result.url;
            link.setAttribute("role", "option");
            const title = document.createElement("strong");
            title.textContent = result.title;
            const detail = document.createElement("small");
            detail.textContent = [result.category, result.subtitle].filter(Boolean).join(" · ");
            link.append(title, detail);
            resultsBox.appendChild(link);
        });
        resultsBox.hidden = false;
        input.setAttribute("aria-expanded", "true");
    };

    input.addEventListener("input", () => {
        window.clearTimeout(debounceTimer);
        if (activeController) activeController.abort();
        const query = input.value.trim();
        if (query.length < 2) {
            closeResults();
            return;
        }
        showMessage("Searching…");
        debounceTimer = window.setTimeout(async () => {
            activeController = new AbortController();
            try {
                const url = new URL(wrapper.dataset.searchUrl, window.location.origin);
                url.searchParams.set("q", query);
                const response = await fetch(url, {
                    headers: { "X-Requested-With": "XMLHttpRequest" },
                    credentials: "same-origin",
                    signal: activeController.signal
                });
                if (!response.ok) throw new Error("Search request failed");
                const data = await response.json();
                renderResults(data.results || []);
            } catch (error) {
                if (error.name !== "AbortError") showMessage("Search is temporarily unavailable. Please try again.");
            }
        }, 250);
    });

    document.addEventListener("click", (event) => {
        if (!wrapper.contains(event.target)) closeResults();
    });
    input.addEventListener("keydown", (event) => {
        if (event.key === "Escape") closeResults();
    });
});
