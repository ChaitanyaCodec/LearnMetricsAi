(function () {
    "use strict";

    const API = {
        conversations: "/rag/conversations/",
        conversation: (id) => `/rag/conversations/${id}/`,
        messages: (id) => `/rag/conversations/${id}/messages/`,
    };

    const STATUS = {
        ANSWER: "ANSWER",
        NO_RELEVANT_CONTEXT: "NO_RELEVANT_CONTEXT",
        CLARIFICATION: "CLARIFICATION",
        ERROR: "ERROR",
    };

    const state = {
        conversations: [],
        activeConversationId: null,
        activeSubjectId: null,
        isSending: false,

        openActionMenuId: null,

        pendingDeleteConversationId: null,
        pendingRenameConversationId: null,

        isRenaming: false,
        isDeleting: false,
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
        errorMessage: document.getElementById(
            "chat-error-message"
        ),

        sidebar: document.getElementById("rag-sidebar"),
        sidebarToggle: document.getElementById(
            "sidebar-toggle"
        ),

        renameModal: document.getElementById(
            "renameChatModal"
        ),

        renameForm: document.getElementById(
            "rename-conversation-form"
        ),

        renameInput: document.getElementById(
            "rename-conversation-input"
        ),

        renameError: document.getElementById(
            "rename-conversation-error"
        ),

        renameCharacterCount: document.getElementById(
            "rename-character-count"
        ),

        saveRenameBtn: document.getElementById(
            "save-rename-btn"
        ),

        deleteModal: document.getElementById(
            "deleteChatModal"
        ),

        deleteConversationTitle: document.getElementById(
            "delete-conversation-title"
        ),

        confirmDeleteBtn: document.getElementById(
            "confirm-delete-btn"
        ),
    };


    /* ==========================================================
       CSRF & NETWORKING
       ========================================================== */

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


    /* ==========================================================
       GENERAL UI HELPERS
       ========================================================== */

    function showLoading(show) {
        if (!elements.loading) return;

        elements.loading.classList.toggle(
            "d-none",
            !show
        );
    }


    function showError(message) {
        if (
            !elements.error ||
            !elements.errorMessage
        ) {
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
        if (!elements.chatMessages) return;

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

        const count =
            elements.chatInput.value.length;

        elements.characterCount.textContent =
            `${count} / 5000`;

        if (elements.sendButton) {
            elements.sendButton.disabled =
                count === 0 ||
                state.isSending;
        }
    }


    function getConversationId(conversation) {
        return (
            conversation?.id ||
            conversation?.conversation_id
        );
    }


    /* ==========================================================
       CONVERSATION MODALS
       ========================================================== */

    function openModal(modal) {
        if (!modal) return;

        closeActionMenus();

        modal.classList.add("is-open");
        modal.setAttribute("aria-hidden", "false");

        document.body.classList.add(
            "rag-modal-open"
        );
    }


    function closeModal(modal) {
        if (!modal) return;

        modal.classList.remove("is-open");
        modal.setAttribute("aria-hidden", "true");

        if (
            !document.querySelector(
                ".rag-modal.is-open"
            )
        ) {
            document.body.classList.remove(
                "rag-modal-open"
            );
        }
    }


    function closeAllModals() {
        closeModal(elements.renameModal);
        closeModal(elements.deleteModal);

        state.pendingRenameConversationId = null;
        state.pendingDeleteConversationId = null;
    }


    function handleModalClose(modalType) {
        if (modalType === "rename") {
            closeModal(elements.renameModal);
            state.pendingRenameConversationId = null;
        }

        if (modalType === "delete") {
            closeModal(elements.deleteModal);
            state.pendingDeleteConversationId = null;
        }
    }


    /* ==========================================================
       CONVERSATION EMPTY STATE
       ========================================================== */

    function createConversationEmptyState() {
        const emptyState =
            document.createElement("div");

        emptyState.id =
            "conversation-empty-state";

        emptyState.className =
            "rag-empty-sidebar";

        const icon =
            document.createElement("i");

        icon.className =
            "fa-regular fa-message";

        const paragraph =
            document.createElement("p");

        paragraph.textContent =
            "No previous sessions";

        const small =
            document.createElement("small");

        small.textContent =
            "Start a chat to review topics";

        emptyState.appendChild(icon);
        emptyState.appendChild(paragraph);
        emptyState.appendChild(small);

        return emptyState;
    }


    /* ==========================================================
       CONVERSATION ACTION MENUS
       ========================================================== */

    function closeActionMenus() {
        document
            .querySelectorAll(
                ".rag-conversation-actions-menu"
            )
            .forEach((menu) => {
                menu.classList.add("d-none");
            });

        document
            .querySelectorAll(
                ".rag-conversation-actions-button"
            )
            .forEach((button) => {
                button.classList.remove("is-active");
                button.setAttribute(
                    "aria-expanded",
                    "false"
                );
            });

        state.openActionMenuId = null;
    }


    function createConversationActions(
        conversationId
    ) {
        const wrapper =
            document.createElement("div");

        wrapper.className =
            "rag-conversation-actions";


        const button =
            document.createElement("button");

        button.type = "button";

        button.className =
            "rag-conversation-actions-button";

        button.setAttribute(
            "aria-label",
            "Conversation actions"
        );

        button.setAttribute(
            "aria-expanded",
            "false"
        );

        button.innerHTML =
            '<i class="fa-solid fa-ellipsis"></i>';


        const menu =
            document.createElement("div");

        menu.className =
            "rag-conversation-actions-menu d-none";


        /* Rename */

        const renameButton =
            document.createElement("button");

        renameButton.type = "button";

        renameButton.className =
            "rag-conversation-action";

        renameButton.innerHTML =
            '<i class="fa-regular fa-pen-to-square"></i>' +
            "<span>Rename</span>";

        renameButton.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                closeActionMenus();

                openRenameModal(
                    conversationId
                );
            }
        );


        /* Delete */

        const deleteButton =
            document.createElement("button");

        deleteButton.type = "button";

        deleteButton.className =
            "rag-conversation-action " +
            "rag-conversation-action-danger";

        deleteButton.innerHTML =
            '<i class="fa-regular fa-trash-can"></i>' +
            "<span>Delete</span>";

        deleteButton.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                closeActionMenus();

                openDeleteModal(
                    conversationId
                );
            }
        );


        menu.appendChild(renameButton);
        menu.appendChild(deleteButton);


        button.addEventListener(
            "click",
            (event) => {
                event.stopPropagation();

                const isOpen =
                    !menu.classList.contains(
                        "d-none"
                    );

                closeActionMenus();

                if (!isOpen) {
                    menu.classList.remove(
                        "d-none"
                    );

                    button.classList.add(
                        "is-active"
                    );

                    button.setAttribute(
                        "aria-expanded",
                        "true"
                    );

                    state.openActionMenuId =
                        String(conversationId);
                }
            }
        );


        wrapper.appendChild(button);
        wrapper.appendChild(menu);

        return wrapper;
    }


    /* ==========================================================
       RENDER CONVERSATION LIST
       ========================================================== */

    function renderConversationList() {
        if (!elements.conversationList) {
            return;
        }

        closeActionMenus();

        elements.conversationList.innerHTML =
            "";

        if (!state.conversations.length) {
            const emptyState =
                createConversationEmptyState();

            elements.conversationList.appendChild(
                emptyState
            );

            elements.conversationEmptyState =
                emptyState;

            return;
        }


        state.conversations.forEach(
            (conversation) => {
                const id =
                    getConversationId(
                        conversation
                    );

                const item =
                    document.createElement("div");

                item.className =
                    "rag-conversation-item";


                if (
                    String(id) ===
                    String(
                        state.activeConversationId
                    )
                ) {
                    item.classList.add(
                        "active"
                    );
                }


                const conversationIcon =
                    document.createElement("div");

                conversationIcon.className =
                    "rag-conversation-icon";

                conversationIcon.innerHTML =
                    '<i class="fa-regular fa-comments"></i>';


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


                details.addEventListener(
                    "click",
                    () => {
                        if (
                            elements.sidebar
                        ) {
                            elements.sidebar.classList.remove(
                                "open"
                            );
                        }

                        loadConversation(id);
                    }
                );


                const actions =
                    createConversationActions(
                        id
                    );


                item.appendChild(
                    conversationIcon
                );

                item.appendChild(details);

                item.appendChild(actions);

                elements.conversationList.appendChild(
                    item
                );
            }
        );
    }


    /* ==========================================================
       RENAME CONVERSATION
       ========================================================== */

    function clearRenameValidation() {
        if (elements.renameError) {
            elements.renameError.textContent =
                "";
        }

        if (elements.renameInput) {
            elements.renameInput.classList.remove(
                "is-invalid"
            );
        }
    }


    function updateRenameCharacterCount() {
        if (
            !elements.renameInput ||
            !elements.renameCharacterCount
        ) {
            return;
        }

        const count =
            elements.renameInput.value.length;

        elements.renameCharacterCount.textContent =
            `${count} / 120`;
    }


    function setRenameLoading(isLoading) {
        state.isRenaming = isLoading;

        if (
            !elements.saveRenameBtn ||
            !elements.renameInput
        ) {
            return;
        }

        elements.saveRenameBtn.disabled =
            isLoading;

        elements.renameInput.disabled =
            isLoading;

        if (isLoading) {
            elements.saveRenameBtn.innerHTML =
                '<i class="fa-solid fa-circle-notch fa-spin"></i>' +
                "<span>Saving...</span>";
        } else {
            elements.saveRenameBtn.innerHTML =
                '<i class="fa-solid fa-check"></i>' +
                "<span>Save changes</span>";
        }
    }


    function validateRenameTitle(title) {
        const normalizedTitle =
            title.trim();

        if (!normalizedTitle) {
            return {
                valid: false,
                message:
                    "Conversation name cannot be empty.",
            };
        }

        if (normalizedTitle.length > 120) {
            return {
                valid: false,
                message:
                    "Conversation name cannot exceed 120 characters.",
            };
        }

        return {
            valid: true,
            value: normalizedTitle,
        };
    }


    function openRenameModal(conversationId) {
        const conversation =
            state.conversations.find(
                (item) =>
                    String(
                        getConversationId(item)
                    ) ===
                    String(conversationId)
            );

        if (!conversation) {
            showError(
                "Conversation could not be found."
            );
            return;
        }

        state.pendingRenameConversationId =
            conversationId;

        const currentTitle =
            conversation.title ||
            "Study Session";

        clearRenameValidation();

        if (elements.renameInput) {
            elements.renameInput.value =
                currentTitle;

            updateRenameCharacterCount();
        }

        openModal(
            elements.renameModal
        );

        requestAnimationFrame(() => {
            if (elements.renameInput) {
                elements.renameInput.focus();

                elements.renameInput.select();
            }
        });
    }


    async function renameConversation(
        conversationId,
        newTitle
    ) {
        const validation =
            validateRenameTitle(
                newTitle
            );

        if (!validation.valid) {
            if (elements.renameError) {
                elements.renameError.textContent =
                    validation.message;
            }

            if (elements.renameInput) {
                elements.renameInput.classList.add(
                    "is-invalid"
                );
            }

            return false;
        }

        const conversation =
            state.conversations.find(
                (item) =>
                    String(
                        getConversationId(item)
                    ) ===
                    String(conversationId)
            );

        if (!conversation) {
            showError(
                "Conversation could not be found."
            );

            return false;
        }

        const currentTitle =
            conversation.title ||
            "Study Session";

        if (
            validation.value ===
            currentTitle
        ) {
            closeModal(
                elements.renameModal
            );

            state.pendingRenameConversationId =
                null;

            return true;
        }

        clearError();

        setRenameLoading(true);

        try {
            const response =
                await apiRequest(
                    API.conversation(
                        conversationId
                    ),
                    {
                        method: "PATCH",
                        body: JSON.stringify({
                            title:
                                validation.value,
                        }),
                    }
                );

            const updatedConversation =
                response?.conversation ||
                response ||
                {};

            const index =
                state.conversations.findIndex(
                    (item) =>
                        String(
                            getConversationId(
                                item
                            )
                        ) ===
                        String(
                            conversationId
                        )
                );

            if (index !== -1) {
                state.conversations[index] =
                    {
                        ...state
                            .conversations[
                            index
                        ],

                        ...updatedConversation,

                        title:
                            updatedConversation.title ||
                            validation.value,
                    };
            }


            if (
                String(
                    state.activeConversationId
                ) ===
                String(conversationId)
            ) {
                if (elements.activeTitle) {
                    elements.activeTitle.textContent =
                        updatedConversation.title ||
                        validation.value;
                }
            }


            closeModal(
                elements.renameModal
            );

            state.pendingRenameConversationId =
                null;

            renderConversationList();

            return true;

        } catch (error) {
            if (elements.renameError) {
                elements.renameError.textContent =
                    error.message ||
                    "Could not rename conversation.";
            }

            if (elements.renameInput) {
                elements.renameInput.classList.add(
                    "is-invalid"
                );
            }

            return false;

        } finally {
            setRenameLoading(false);
        }
    }


    /* ==========================================================
       DELETE CONVERSATION
       ========================================================== */

    function setDeleteLoading(isLoading) {
        state.isDeleting = isLoading;

        if (!elements.confirmDeleteBtn) {
            return;
        }

        elements.confirmDeleteBtn.disabled =
            isLoading;

        if (isLoading) {
            elements.confirmDeleteBtn.innerHTML =
                '<i class="fa-solid fa-circle-notch fa-spin"></i>' +
                "<span>Deleting...</span>";
        } else {
            elements.confirmDeleteBtn.innerHTML =
                '<i class="fa-regular fa-trash-can"></i>' +
                "<span>Delete conversation</span>";
        }
    }


    function openDeleteModal(conversationId) {
        const conversation =
            state.conversations.find(
                (item) =>
                    String(
                        getConversationId(item)
                    ) ===
                    String(conversationId)
            );

        if (!conversation) {
            showError(
                "Conversation could not be found."
            );
            return;
        }

        state.pendingDeleteConversationId =
            conversationId;

        const title =
            conversation.title ||
            "Study Session";

        if (
            elements.deleteConversationTitle
        ) {
            elements.deleteConversationTitle.textContent =
                title;
        }

        openModal(
            elements.deleteModal
        );

        requestAnimationFrame(() => {
            if (
                elements.confirmDeleteBtn
            ) {
                elements.confirmDeleteBtn.focus();
            }
        });
    }


    async function deleteConversation(
        conversationId
    ) {
        clearError();

        setDeleteLoading(true);

        try {
            await apiRequest(
                API.conversation(
                    conversationId
                ),
                {
                    method: "DELETE",
                }
            );


            state.conversations =
                state.conversations.filter(
                    (conversation) =>
                        String(
                            getConversationId(
                                conversation
                            )
                        ) !==
                        String(conversationId)
                );


            const wasActive =
                String(
                    state.activeConversationId
                ) ===
                String(conversationId);


            if (wasActive) {
                state.activeConversationId =
                    null;

                state.activeSubjectId =
                    null;

                const nextConversation =
                    state.conversations[0];

                if (nextConversation) {
                    const nextId =
                        getConversationId(
                            nextConversation
                        );

                    renderConversationList();

                    await loadConversation(
                        nextId
                    );

                } else {
                    startNewChat();
                }

            } else {
                renderConversationList();
            }


            closeModal(
                elements.deleteModal
            );

            state.pendingDeleteConversationId =
                null;

        } catch (error) {
            showError(
                `Could not delete conversation: ${error.message}`
            );

        } finally {
            setDeleteLoading(false);
        }
    }


    /* ==========================================================
       SOURCES / CITATIONS
       ========================================================== */

    function createSourcesElement(
        sources
    ) {
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


    /* ==========================================================
       MESSAGE RENDERING
       ========================================================== */

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


        avatar.appendChild(
            avatarIcon
        );


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
                window.marked.parse(
                    safeText
                );

            bubble.innerHTML =
                window.DOMPurify.sanitize(
                    rawHtml
                );

        } else {
            bubble.textContent =
                safeText;
        }


        bubbleWrapper.appendChild(
            bubble
        );


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


    /* ==========================================================
       SMART QUERY GUIDANCE
       ========================================================== */

    const RESPONSE_STATUS = {
        ANSWER: "ANSWER",
        NO_RELEVANT_CONTEXT:
            "NO_RELEVANT_CONTEXT",
        CLARIFICATION:
            "CLARIFICATION",
        ERROR: "ERROR",
    };


    function createGuidanceElement(
        message,
        suggestions = [],
        status =
            RESPONSE_STATUS.NO_RELEVANT_CONTEXT
    ) {
        const wrapper =
            document.createElement("div");

        wrapper.className =
            "rag-guidance-wrapper";


        const card =
            document.createElement("div");

        card.className =
            "rag-guidance-card";

        card.dataset.status =
            status;


        const header =
            document.createElement("div");

        header.className =
            "rag-guidance-header";


        const icon =
            document.createElement("div");

        icon.className =
            "rag-guidance-icon";

        icon.innerHTML =
            '<i class="fa-solid fa-lightbulb"></i>';


        const heading =
            document.createElement("div");

        heading.className =
            "rag-guidance-heading";

        heading.textContent =
            status ===
            RESPONSE_STATUS.CLARIFICATION
                ? "Let's narrow that down"
                : "Let's find the right topic";


        header.appendChild(icon);
        header.appendChild(heading);


        const messageElement =
            document.createElement("p");

        messageElement.className =
            "rag-guidance-message";

        messageElement.textContent =
            typeof message === "string" &&
            message.trim()
                ? message
                : "I couldn't identify a specific topic from the uploaded study material.";


        card.appendChild(header);
        card.appendChild(messageElement);


        const normalizedSuggestions =
            Array.isArray(suggestions)
                ? suggestions.filter(
                      (suggestion) =>
                          typeof suggestion ===
                              "string" &&
                          suggestion.trim()
                  )
                : [];


        if (normalizedSuggestions.length) {
            const label =
                document.createElement("div");

            label.className =
                "rag-guidance-suggestions-label";

            label.textContent =
                "Try one of these:";


            card.appendChild(label);


            const suggestionList =
                document.createElement("div");

            suggestionList.className =
                "rag-guidance-suggestions";


            normalizedSuggestions.forEach(
                (suggestion) => {
                    const button =
                        document.createElement(
                            "button"
                        );

                    button.type = "button";

                    button.className =
                        "rag-guidance-suggestion";

                    button.textContent =
                        suggestion;


                    button.addEventListener(
                        "click",
                        () => {
                            if (
                                !elements.chatInput ||
                                state.isSending
                            ) {
                                return;
                            }

                            elements.chatInput.value =
                                suggestion;

                            elements.chatInput.style.height =
                                "auto";

                            elements.chatInput.style.height =
                                `${Math.min(
                                    elements
                                        .chatInput
                                        .scrollHeight,
                                    160
                                )}px`;

                            updateCharacterCount();

                            elements.chatInput.focus();
                        }
                    );


                    suggestionList.appendChild(
                        button
                    );
                }
            );


            card.appendChild(
                suggestionList
            );
        }


        wrapper.appendChild(card);

        return wrapper;
    }


    function renderGuidance(
        message,
        suggestions = [],
        status =
            RESPONSE_STATUS.NO_RELEVANT_CONTEXT
    ) {
        if (!elements.chatMessages) {
            return;
        }

        const guidance =
            createGuidanceElement(
                message,
                suggestions,
                status
            );

        elements.chatMessages.appendChild(
            guidance
        );

        scrollChatToBottom();
    }


    /* ==========================================================
       CONVERSATION MESSAGE RENDERING
       ========================================================== */

    function renderMessages(messages) {
        if (!elements.chatMessages) {
            return;
        }

        elements.chatMessages.innerHTML =
            "";


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
            const roleValue = (
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


    /* ==========================================================
       CONVERSATION API
       ========================================================== */

    async function loadConversations() {
        try {
            const data =
                await apiRequest(
                    API.conversations
                );


            state.conversations =
                Array.isArray(data)
                    ? data
                    : data?.results ||
                      data?.conversations ||
                      [];


            renderConversationList();


            if (
                state.conversations.length &&
                !state.activeConversationId
            ) {
                const first =
                    state.conversations[0];

                const firstId =
                    getConversationId(first);

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
        if (!id) return;

        clearError();

        showLoading(true);


        try {
            const response =
                await apiRequest(
                    API.conversation(id)
                );


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


    /* ==========================================================
       NEW CONVERSATION
       ========================================================== */

    function startNewChat() {
        state.activeConversationId =
            null;

        state.activeSubjectId =
            null;


        if (elements.activeTitle) {
            elements.activeTitle.textContent =
                "New Conversation";
        }


        if (elements.subjectSelect) {
            elements.subjectSelect.value =
                "";
        }


        if (elements.chatMessages) {
            elements.chatMessages.innerHTML =
                "";

            if (elements.chatEmptyState) {
                elements.chatMessages.appendChild(
                    elements.chatEmptyState
                );

                elements.chatEmptyState.classList.remove(
                    "d-none"
                );
            }
        }


        if (elements.chatInput) {
            elements.chatInput.value =
                "";

            elements.chatInput.style.height =
                "auto";
        }


        updateCharacterCount();

        clearError();

        closeActionMenus();

        if (elements.sidebar) {
            elements.sidebar.classList.remove(
                "open"
            );
        }


        renderConversationList();
    }


    /* ==========================================================
       MESSAGE SUBMISSION
       ========================================================== */

    async function sendQuestion() {
        if (
            state.isSending ||
            !elements.chatInput
        ) {
            return;
        }


        const text =
            elements.chatInput.value.trim();


        if (!text) return;


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


        elements.chatInput.disabled =
            true;


        if (elements.chatEmptyState) {
            elements.chatEmptyState.classList.add(
                "d-none"
            );
        }


        if (elements.chatMessages) {
            elements.chatMessages.appendChild(
                createMessageElement(
                    "user",
                    text
                )
            );

            scrollChatToBottom();
        }


        elements.chatInput.value =
            "";

        elements.chatInput.style.height =
            "auto";


        updateCharacterCount();

        showLoading(true);


        try {
            if (
                !state.activeConversationId
            ) {
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


            const status =
                String(
                    data?.status ||
                    "ANSWER"
                ).toUpperCase();


            if (
                status ===
                    RESPONSE_STATUS.NO_RELEVANT_CONTEXT ||
                status ===
                    RESPONSE_STATUS.CLARIFICATION
            ) {
                const guidance =
                    data?.guidance ||
                    {};


                renderGuidance(
                    guidance.message ||
                        "I couldn't identify a specific topic from the uploaded study material.",

                    Array.isArray(
                        guidance.suggestions
                    )
                        ? guidance.suggestions
                        : [],

                    status
                );


                await loadConversations();

                renderConversationList();

                return;
            }


            if (
                status ===
                RESPONSE_STATUS.ERROR
            ) {
                showError(
                    data?.error ||
                        "Something went wrong while processing your question."
                );

                return;
            }


            const answer =
                data.answer ||
                data.assistant_message
                    ?.content ||
                "No explanation provided.";


            const sources =
                data.sources ||
                data.assistant_message
                    ?.metadata
                    ?.sources ||
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


            await loadConversations();

            renderConversationList();

        } catch (error) {
            showError(
                `Failed to receive response: ${error.message}`
            );

        } finally {
            state.isSending =
                false;

            elements.chatInput.disabled =
                false;

            updateCharacterCount();

            elements.chatInput.focus();

            showLoading(false);
        }
    }


    /* ==========================================================
       SUBJECT SELECTION
       ========================================================== */

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

        if (
            state.activeConversationId &&
            state.activeSubjectId
        ) {
            return;
        }
    }


    /* ==========================================================
       EVENT LISTENERS
       ========================================================== */

    function initializeEvents() {

        /* New chat */

        if (elements.newChatButton) {
            elements.newChatButton.addEventListener(
                "click",
                startNewChat
            );
        }


        if (elements.newChatSidebarButton) {
            elements.newChatSidebarButton.addEventListener(
                "click",
                startNewChat
            );
        }


        /* Send */

        if (elements.sendButton) {
            elements.sendButton.addEventListener(
                "click",
                sendQuestion
            );
        }


        /* Subject */

        if (elements.subjectSelect) {
            elements.subjectSelect.addEventListener(
                "change",
                handleSubjectChange
            );
        }


        /* Rename form */

        if (elements.renameForm) {
            elements.renameForm.addEventListener(
                "submit",
                async (event) => {
                    event.preventDefault();

                    if (
                        state.isRenaming ||
                        !state.pendingRenameConversationId
                    ) {
                        return;
                    }

                    const title =
                        elements.renameInput
                            ? elements.renameInput.value
                            : "";

                    await renameConversation(
                        state.pendingRenameConversationId,
                        title
                    );
                }
            );
        }


        /* Rename input */

        if (elements.renameInput) {
            elements.renameInput.addEventListener(
                "input",
                () => {
                    updateRenameCharacterCount();

                    if (
                        elements.renameInput.classList.contains(
                            "is-invalid"
                        )
                    ) {
                        clearRenameValidation();
                    }
                }
            );
        }


        /* Delete */

        if (elements.confirmDeleteBtn) {
            elements.confirmDeleteBtn.addEventListener(
                "click",
                async () => {
                    if (
                        state.isDeleting ||
                        !state.pendingDeleteConversationId
                    ) {
                        return;
                    }

                    const targetId =
                        state.pendingDeleteConversationId;

                    await deleteConversation(
                        targetId
                    );
                }
            );
        }


        /* Modal close buttons */

        document
            .querySelectorAll(
                "[data-modal-close]"
            )
            .forEach((button) => {
                button.addEventListener(
                    "click",
                    (event) => {
                        const modalType =
                            event.currentTarget
                                .dataset
                                .modalClose;

                        handleModalClose(
                            modalType
                        );
                    }
                );
            });


        /* Composer */

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


        /* Quick prompts */

        document
            .querySelectorAll(
                ".rag-prompt-pill"
            )
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


        /* Mobile sidebar */

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


        /* Close action menu */

        document.addEventListener(
            "click",
            () => {
                closeActionMenus();
            }
        );


        /* Keyboard modal handling */

        document.addEventListener(
            "keydown",
            (event) => {

                if (
                    event.key === "Escape"
                ) {
                    closeActionMenus();

                    if (
                        elements.renameModal?.classList.contains(
                            "is-open"
                        )
                    ) {
                        handleModalClose(
                            "rename"
                        );

                        return;
                    }

                    if (
                        elements.deleteModal?.classList.contains(
                            "is-open"
                        )
                    ) {
                        handleModalClose(
                            "delete"
                        );
                    }
                }
            }
        );
    }


    /* ==========================================================
       INITIALIZATION
       ========================================================== */

    document.addEventListener(
        "DOMContentLoaded",
        () => {
            initializeEvents();

            updateCharacterCount();

            updateRenameCharacterCount();

            loadConversations();
        }
    );

})();