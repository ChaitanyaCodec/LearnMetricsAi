(function () {
    "use strict";

    const API = {
        conversations: "/rag/conversations/",
        conversation: (id) => `/rag/conversations/${id}/`,
        messages: (id) => `/rag/conversations/${id}/messages/`,
    };

    const state = {
        conversations: [],
        activeConversationId: null,
        activeSubjectId: null,
        isSending: false,
    };

    const elements = {
        conversationList: document.getElementById("conversation-list"),
        conversationEmptyState: document.getElementById(
            "conversation-empty-state"
        ),
        newChatButton: document.getElementById("new-chat-button"),
        newChatSidebarButton: document.getElementById(
            "new-chat-sidebar-button"
        ),
        subjectSelect: document.getElementById("subject-select"),
        chatMessages: document.getElementById("chat-messages"),
        chatEmptyState: document.getElementById("chat-empty-state"),
        chatInput: document.getElementById("chat-input"),
        sendButton: document.getElementById("send-message-button"),
        characterCount: document.getElementById("character-count"),
        activeTitle: document.getElementById(
            "active-conversation-title"
        ),
        loading: document.getElementById("chat-loading"),
        error: document.getElementById("chat-error"),
        errorMessage: document.getElementById("chat-error-message"),
        sidebar: document.getElementById("rag-sidebar"),
        sidebarToggle: document.getElementById("sidebar-toggle"),
    };

    /* ---------------------------------------------------------
       CSRF & Networking
       --------------------------------------------------------- */

    function getCookie(name) {
        let cookieValue = null;

        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");

            for (let i = 0; i < cookies.length; i += 1) {
                const cookie = cookies[i].trim();

                if (
                    cookie.substring(0, name.length + 1) ===
                    `${name}=`
                ) {
                    cookieValue = decodeURIComponent(
                        cookie.substring(name.length + 1)
                    );
                    break;
                }
            }
        }

        return cookieValue;
    }

    async function apiRequest(url, options = {}) {
        const headers = {
            Accept: "application/json",
            ...(options.headers || {}),
        };

        if (
            options.body &&
            !(options.body instanceof FormData)
        ) {
            headers["Content-Type"] = "application/json";
        }

        const csrfToken = getCookie("csrftoken");

        if (csrfToken) {
            headers["X-CSRFToken"] = csrfToken;
        }

        const response = await fetch(url, {
            ...options,
            headers,
            credentials: "same-origin",
        });

        if (response.status === 204) {
            return {
                success: true,
            };
        }

        let data = null;

        const contentType =
            response.headers.get("Content-Type") || "";

        if (contentType.includes("application/json")) {
            data = await response.json();
        }

        if (!response.ok) {
            throw new Error(
                data?.detail ||
                data?.error ||
                `Request failed with status ${response.status}`
            );
        }

        return data;
    }

    /* ---------------------------------------------------------
       UI Helpers
       --------------------------------------------------------- */

    function showLoading(show) {
        if (!elements.loading) {
            return;
        }

        elements.loading.classList.toggle("d-none", !show);
    }

    function showError(message) {
        if (!elements.error || !elements.errorMessage) {
            return;
        }

        elements.errorMessage.textContent = message;
        elements.error.classList.remove("d-none");
    }

    function clearError() {
        if (elements.error) {
            elements.error.classList.add("d-none");
        }
    }

    function scrollChatToBottom() {
        if (!elements.chatMessages) {
            return;
        }

        requestAnimationFrame(() => {
            elements.chatMessages.scrollTop =
                elements.chatMessages.scrollHeight;
        });
    }

    function updateCharacterCount() {
        if (
            !elements.chatInput ||
            !elements.characterCount
        ) {
            return;
        }

        const count = elements.chatInput.value.length;

        elements.characterCount.textContent =
            `${count} / 5000`;

        if (elements.sendButton) {
            elements.sendButton.disabled =
                count === 0 || state.isSending;
        }
    }

    /* ---------------------------------------------------------
       Conversation Empty State
       --------------------------------------------------------- */

    function createConversationEmptyState() {
        const emptyState = document.createElement("div");

        emptyState.id = "conversation-empty-state";
        emptyState.className = "rag-empty-sidebar";

        const icon = document.createElement("i");
        icon.className = "fa-regular fa-message";

        const paragraph = document.createElement("p");
        paragraph.textContent = "No previous sessions";

        const small = document.createElement("small");
        small.textContent = "Start a chat to review topics";

        emptyState.appendChild(icon);
        emptyState.appendChild(paragraph);
        emptyState.appendChild(small);

        return emptyState;
    }

    /* ---------------------------------------------------------
       Render Conversation List
       --------------------------------------------------------- */

    function renderConversationList() {
        if (!elements.conversationList) {
            return;
        }

        elements.conversationList.innerHTML = "";

        if (!state.conversations.length) {
            const emptyState =
                createConversationEmptyState();

            elements.conversationList.appendChild(
                emptyState
            );

            elements.conversationEmptyState = emptyState;

            return;
        }

        state.conversations.forEach((conversation) => {
            const id =
                conversation.id ||
                conversation.conversation_id;

            const item =
                document.createElement("div");

            item.className =
                "rag-conversation-item";

            if (
                String(id) ===
                String(state.activeConversationId)
            ) {
                item.classList.add("active");
            }

            const details =
                document.createElement("div");

            details.className =
                "rag-conv-details";

            const title =
                document.createElement("div");

            title.className =
                "rag-conv-title";

            title.textContent =
                conversation.title ||
                "Study Session";

            const subject =
                document.createElement("div");

            subject.className =
                "rag-conv-sub";

            subject.textContent =
                conversation.subject_name ||
                "Academic Materials";

            details.appendChild(title);
            details.appendChild(subject);

            details.addEventListener("click", () => {
                if (elements.sidebar) {
                    elements.sidebar.classList.remove(
                        "open"
                    );
                }

                loadConversation(id);
            });

            item.appendChild(details);

            elements.conversationList.appendChild(
                item
            );
        });
    }

    /* ---------------------------------------------------------
       Sources / Citations
       --------------------------------------------------------- */

    function createSourcesElement(sources) {
        if (
            !Array.isArray(sources) ||
            !sources.length
        ) {
            return null;
        }

        const box =
            document.createElement("div");

        box.className =
            "rag-citations-box";

        sources.forEach((source) => {
            const pill =
                document.createElement("span");

            pill.className =
                "rag-citation-pill";

            const icon =
                document.createElement("i");

            icon.className =
                "fa-solid fa-file-lines";

            const title =
                source.document_title ||
                source.title ||
                "Material";

            const pageValue =
                source.page ??
                source.page_number;

            const pageText =
                pageValue !== null &&
                pageValue !== undefined &&
                pageValue !== ""
                    ? ` (p. ${pageValue})`
                    : "";

            const text =
                document.createTextNode(
                    ` ${title}${pageText}`
                );

            pill.appendChild(icon);
            pill.appendChild(text);

            box.appendChild(pill);
        });

        return box;
    }

    /* ---------------------------------------------------------
       Message Rendering
       --------------------------------------------------------- */

    function createMessageElement(
        role,
        text,
        sources = []
    ) {
        const row =
            document.createElement("div");

        row.className =
            `rag-msg-row ${role}`;

        const avatar =
            document.createElement("div");

        avatar.className =
            "rag-avatar";

        const avatarIcon =
            document.createElement("i");

        avatarIcon.className =
            role === "user"
                ? "fa-solid fa-user"
                : "fa-solid fa-robot";

        avatar.appendChild(avatarIcon);

        const bubbleWrapper =
            document.createElement("div");

        const bubble =
            document.createElement("div");

        bubble.className =
            "rag-bubble";

        const safeText =
            typeof text === "string"
                ? text
                : String(text ?? "");

        if (
            role === "assistant" &&
            window.marked &&
            window.DOMPurify
        ) {
            const rawHtml =
                window.marked.parse(safeText);

            bubble.innerHTML =
                window.DOMPurify.sanitize(
                    rawHtml
                );
        } else {
            bubble.textContent =
                safeText;
        }

        bubbleWrapper.appendChild(bubble);

        if (
            role === "assistant" &&
            Array.isArray(sources) &&
            sources.length
        ) {
            const citations =
                createSourcesElement(
                    sources
                );

            if (citations) {
                bubbleWrapper.appendChild(
                    citations
                );
            }
        }

        row.appendChild(avatar);
        row.appendChild(bubbleWrapper);

        return row;
    }

    function renderMessages(messages) {
        if (!elements.chatMessages) {
            return;
        }

        elements.chatMessages.innerHTML = "";

        if (
            !Array.isArray(messages) ||
            !messages.length
        ) {
            if (elements.chatEmptyState) {
                elements.chatMessages.appendChild(
                    elements.chatEmptyState
                );
                elements.chatEmptyState.classList.remove(
                    "d-none"
                );
            }

            return;
        }

        if (elements.chatEmptyState) {
            elements.chatEmptyState.classList.add(
                "d-none"
            );
        }

        messages.forEach((message) => {
            const roleValue =
                (
                    message.role ||
                    message.message_type ||
                    ""
                ).toLowerCase();

            const role =
                roleValue.includes("user")
                    ? "user"
                    : "assistant";

            const text =
                message.content ||
                message.message ||
                message.text ||
                "";

            const sources =
                message.metadata?.sources ||
                message.sources ||
                [];

            elements.chatMessages.appendChild(
                createMessageElement(
                    role,
                    text,
                    sources
                )
            );
        });

        scrollChatToBottom();
    }

    /* ---------------------------------------------------------
       Conversation API Operations
       --------------------------------------------------------- */

    async function loadConversations() {
        try {
            const data =
                await apiRequest(
                    API.conversations
                );

            state.conversations =
                Array.isArray(data)
                    ? data
                    : (
                        data?.results ||
                        data?.conversations ||
                        []
                    );

            renderConversationList();

            if (
                state.conversations.length &&
                !state.activeConversationId
            ) {
                const first =
                    state.conversations[0];

                const firstId =
                    first.id ||
                    first.conversation_id;

                await loadConversation(
                    firstId
                );
            }
        } catch (error) {
            showError(
                "Unable to load history. Please refresh."
            );
        }
    }

    async function loadConversation(id) {
        if (!id) {
            return;
        }

        clearError();
        showLoading(true);

        try {
            const response =
                await apiRequest(
                    API.conversation(id)
                );

            /*
             * Current backend returns the serialized
             * conversation directly.
             *
             * This also tolerates a wrapped
             * {"conversation": {...}} response.
             */
            const data =
                response?.conversation ||
                response;

            state.activeConversationId =
                data.id ||
                data.conversation_id ||
                id;

            state.activeSubjectId =
                data.subject_id ||
                data.subject?.id ||
                null;

            if (elements.activeTitle) {
                elements.activeTitle.textContent =
                    data.title ||
                    "Academic Session";
            }

            if (
                elements.subjectSelect &&
                state.activeSubjectId
            ) {
                elements.subjectSelect.value =
                    String(
                        state.activeSubjectId
                    );
            }

            renderMessages(
                data.messages || []
            );

            renderConversationList();
        } catch (error) {
            showError(
                `Error opening conversation: ${error.message}`
            );
        } finally {
            showLoading(false);
        }
    }

    async function createConversation(
        subjectId
    ) {
        const numericSubjectId =
            Number(subjectId);

        if (
            !Number.isInteger(
                numericSubjectId
            ) ||
            numericSubjectId <= 0
        ) {
            throw new Error(
                "Please select a valid subject."
            );
        }

        const payload = {
            subject_id:
                numericSubjectId,
        };

        const response =
            await apiRequest(
                API.conversations,
                {
                    method: "POST",
                    body: JSON.stringify(
                        payload
                    ),
                }
            );

        /*
         * Current backend returns the
         * serialized conversation directly.
         *
         * Also tolerate a wrapped response.
         */
        const data =
            response?.conversation ||
            response;

        const newId =
            data.id ||
            data.conversation_id;

        if (!newId) {
            throw new Error(
                "Conversation was created but no conversation ID was returned."
            );
        }

        state.activeConversationId =
            newId;

        state.activeSubjectId =
            numericSubjectId;

        if (elements.activeTitle) {
            elements.activeTitle.textContent =
                data.title ||
                "Academic Session";
        }

        return newId;
    }

    /* ---------------------------------------------------------
       New Conversation
       --------------------------------------------------------- */

    function startNewChat() {
        state.activeConversationId = null;
        state.activeSubjectId = null;

        if (elements.activeTitle) {
            elements.activeTitle.textContent =
                "New Conversation";
        }

        if (elements.subjectSelect) {
            elements.subjectSelect.value = "";
        }

        if (elements.chatMessages) {
            elements.chatMessages.innerHTML = "";
        }

        if (
            elements.chatMessages &&
            elements.chatEmptyState
        ) {
            elements.chatMessages.appendChild(
                elements.chatEmptyState
            );

            elements.chatEmptyState.classList.remove(
                "d-none"
            );
        }

        if (elements.chatInput) {
            elements.chatInput.value = "";
            elements.chatInput.style.height =
                "auto";
        }

        updateCharacterCount();
        clearError();

        if (elements.sidebar) {
            elements.sidebar.classList.remove(
                "open"
            );
        }

        renderConversationList();
    }

    /* ---------------------------------------------------------
       Message Submission
       --------------------------------------------------------- */

    async function sendQuestion() {
        if (state.isSending) {
            return;
        }

        if (!elements.chatInput) {
            return;
        }

        const text =
            elements.chatInput.value.trim();

        if (!text) {
            return;
        }

        const selectedSubject =
            elements.subjectSelect
                ? elements.subjectSelect.value
                : state.activeSubjectId;

        const subjectId =
            Number(selectedSubject);

        if (
            !Number.isInteger(subjectId) ||
            subjectId <= 0
        ) {
            showError(
                "Please pick a subject before asking questions."
            );
            return;
        }

        clearError();

        state.isSending = true;

        if (elements.sendButton) {
            elements.sendButton.disabled =
                true;
        }

        elements.chatInput.disabled = true;

        if (elements.chatEmptyState) {
            elements.chatEmptyState.classList.add(
                "d-none"
            );
        }

        /*
         * Optimistically display the user's
         * question immediately.
         */
        if (elements.chatMessages) {
            elements.chatMessages.appendChild(
                createMessageElement(
                    "user",
                    text
                )
            );

            scrollChatToBottom();
        }

        elements.chatInput.value = "";
        elements.chatInput.style.height =
            "auto";

        updateCharacterCount();
        showLoading(true);

        try {
            if (!state.activeConversationId) {
                await createConversation(
                    subjectId
                );
            }

            const data =
                await apiRequest(
                    API.messages(
                        state.activeConversationId
                    ),
                    {
                        method: "POST",
                        body: JSON.stringify({
                            question: text,
                        }),
                    }
                );

            const answer =
                data.answer ||
                data.assistant_message?.content ||
                "No explanation provided.";

            const sources =
                data.sources ||
                data.assistant_message
                    ?.metadata?.sources ||
                [];

            if (elements.chatMessages) {
                elements.chatMessages.appendChild(
                    createMessageElement(
                        "assistant",
                        answer,
                        sources
                    )
                );

                scrollChatToBottom();
            }

            /*
             * Refresh history so the current
             * conversation's metadata/order is
             * reflected in the sidebar.
             */
            await loadConversations();

            /*
             * Keep the current conversation selected
             * after refreshing the list.
             */
            renderConversationList();
        } catch (error) {
            showError(
                `Failed to receive response: ${error.message}`
            );
        } finally {
            state.isSending = false;

            elements.chatInput.disabled =
                false;

            updateCharacterCount();

            elements.chatInput.focus();

            showLoading(false);
        }
    }

    /* ---------------------------------------------------------
       Subject Selection
       --------------------------------------------------------- */

    function handleSubjectChange() {
        if (!elements.subjectSelect) {
            return;
        }

        const value =
            elements.subjectSelect.value;

        state.activeSubjectId =
            value
                ? Number(value)
                : null;

        /*
         * A subject change should apply to a
         * new conversation. Do not silently
         * change the subject of an existing
         * persisted conversation.
         */
        if (
            state.activeConversationId &&
            state.activeSubjectId
        ) {
            return;
        }
    }

    /* ---------------------------------------------------------
       Event Listeners
       --------------------------------------------------------- */

    function initializeEvents() {
        if (elements.newChatButton) {
            elements.newChatButton.addEventListener(
                "click",
                startNewChat
            );
        }

        if (
            elements.newChatSidebarButton
        ) {
            elements.newChatSidebarButton.addEventListener(
                "click",
                startNewChat
            );
        }

        if (elements.sendButton) {
            elements.sendButton.addEventListener(
                "click",
                sendQuestion
            );
        }

        if (elements.subjectSelect) {
            elements.subjectSelect.addEventListener(
                "change",
                handleSubjectChange
            );
        }

        if (elements.chatInput) {
            elements.chatInput.addEventListener(
                "input",
                function () {
                    this.style.height =
                        "auto";

                    this.style.height =
                        `${Math.min(
                            this.scrollHeight,
                            160
                        )}px`;

                    updateCharacterCount();
                }
            );

            elements.chatInput.addEventListener(
                "keydown",
                (event) => {
                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {
                        event.preventDefault();
                        sendQuestion();
                    }
                }
            );
        }

        /*
         * Quick prompt buttons.
         */
        document
            .querySelectorAll(".rag-prompt-pill")
            .forEach((pill) => {
                pill.addEventListener(
                    "click",
                    () => {
                        const prompt =
                            pill.getAttribute(
                                "data-prompt"
                            );

                        if (
                            prompt &&
                            elements.chatInput
                        ) {
                            elements.chatInput.value =
                                prompt;

                            updateCharacterCount();

                            elements.chatInput.focus();
                        }
                    }
                );
            });

        /*
         * Mobile conversation drawer.
         */
        if (
            elements.sidebarToggle &&
            elements.sidebar
        ) {
            elements.sidebarToggle.addEventListener(
                "click",
                () => {
                    elements.sidebar.classList.toggle(
                        "open"
                    );
                }
            );
        }
    }

    /* ---------------------------------------------------------
       Initialization
       --------------------------------------------------------- */

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            initializeEvents();
            updateCharacterCount();
            loadConversations();
        }
    );
})();