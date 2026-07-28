// chat.js - Handles Chat interactions, message delivery, loading indicators, markdown formatting, copy hooks, and search

document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-message-form');
    const userInput = document.getElementById('chat-user-input');
    const messagesBox = document.getElementById('chat-messages-box');
    const activeConvInput = document.getElementById('active-conversation-id');
    const sendBtn = document.getElementById('chat-send-btn');
    const loadingIndicator = document.getElementById('chat-loading-indicator');
    const searchInput = document.getElementById('search-input');
    const historyListContainer = document.getElementById('history-list-container');
    
    // Mobile sidebar toggle selectors
    const sidebarToggleBtn = document.getElementById('sidebar-toggle-btn');
    const chatSidebarElement = document.getElementById('chat-sidebar-element');

    // 1. Initial Page Load Actions
    autoScrollToBottom();
    formatAllExistingMessages();

    // Auto-resize textarea on input
    if (userInput) {
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });

        // Submit form on Enter key (without shift)
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                chatForm.dispatchEvent(new Event('submit'));
            }
        });
    }

    // 2. Mobile Sidebar Drawer Logic
    if (sidebarToggleBtn && chatSidebarElement) {
        sidebarToggleBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            chatSidebarElement.classList.toggle('active');
        });

        // Close sidebar if user clicks main area on mobile
        document.querySelector('.chat-main').addEventListener('click', () => {
            if (chatSidebarElement.classList.contains('active')) {
                chatSidebarElement.classList.remove('active');
            }
        });
    }

    // 3. Search Conversations functionality
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            // Call the Flask search route
            fetch(`/search?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(conversations => {
                    historyListContainer.innerHTML = '';
                    
                    if (conversations.length === 0) {
                        historyListContainer.innerHTML = '<div class="sidebar-empty">No chats found.</div>';
                        return;
                    }
                    
                    const activeId = activeConvInput.value;
                    
                    conversations.forEach(conv => {
                        const isActive = activeId == conv.id ? 'active' : '';
                        const itemHtml = `
                            <div class="sidebar-history-item ${isActive}" data-id="${conv.id}">
                                <a href="/chat/${conv.id}" class="history-item-link">
                                    <i class="fa-regular fa-comments"></i>
                                    <span class="history-item-title">${escapeHTML(conv.title)}</span>
                                </a>
                                <form action="/delete-chat/${conv.id}" method="POST" onsubmit="return confirm('Delete this conversation?');" class="delete-history-form">
                                    <button type="submit" class="delete-history-btn" title="Delete conversation">
                                        <i class="fa-solid fa-trash-can"></i>
                                    </button>
                                </form>
                            </div>
                        `;
                        historyListContainer.insertAdjacentHTML('beforeend', itemHtml);
                    });
                })
                .catch(err => {
                    console.error('Error searching conversations:', err);
                });
        });
    }

    // 4. Send Message Form Submit
    if (chatForm) {
        chatForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const message = userInput.value.trim();
            const conversationId = activeConvInput.value;
            
            if (!message) return;

            // Clear suggestion welcome screen if present
            const welcomeView = document.getElementById('chat-welcome-view');
            if (welcomeView) {
                welcomeView.remove();
            }

            // Append User message bubble
            appendMessageBubble('user', message);
            
            // Reset input field and auto-resize height
            userInput.value = '';
            userInput.style.height = 'auto';
            
            // Show Thinking Indicator & Disable Input Controls
            toggleLoadingState(true);
            autoScrollToBottom();

            // Make POST API request to Flask
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    conversation_id: conversationId ? parseInt(conversationId) : null
                })
            })
            .then(response => response.json())
            .then(data => {
                toggleLoadingState(false);
                
                if (data.success) {
                    // Update active conversation ID if it's a new chat
                    if (!conversationId) {
                        activeConvInput.value = data.conversation_id;
                        // Redirect to the newly created conversation's page to load full layout history
                        window.location.href = `/chat/${data.conversation_id}`;
                    } else {
                        // Append AI response bubble dynamically
                        appendMessageBubble('assistant', data.response);
                        autoScrollToBottom();
                    }
                } else {
                    // Display friendly error bubble in chat
                    appendMessageBubble('assistant', `⚠️ Error: ${data.error}`);
                    autoScrollToBottom();
                }
            })
            .catch(err => {
                toggleLoadingState(false);
                appendMessageBubble('assistant', '⚠️ Error: Could not connect to server. Please try again.');
                autoScrollToBottom();
                console.error('Fetch error:', err);
            });
        });
    }
});

// --- HELPER FUNCTIONS ---

// Auto-Scroll to the bottom of the chat container
function autoScrollToBottom() {
    const box = document.getElementById('chat-messages-box');
    if (box) {
        box.scrollTop = box.scrollHeight;
    }
}

// Toggle loading dots indicator and input state
function toggleLoadingState(isLoading) {
    const loader = document.getElementById('chat-loading-indicator');
    const userInput = document.getElementById('chat-user-input');
    const sendBtn = document.getElementById('chat-send-btn');
    
    if (loader) {
        loader.style.display = isLoading ? 'flex' : 'none';
        // Move the loader to the very bottom of the message container
        if (isLoading) {
            const container = document.getElementById('chat-messages-box');
            container.appendChild(loader);
        }
    }
    
    if (userInput && sendBtn) {
        userInput.disabled = isLoading;
        sendBtn.disabled = isLoading;
        if (!isLoading) {
            userInput.focus();
        }
    }
}

// Click suggestion card function
function sendSuggestion(questionText) {
    const input = document.getElementById('chat-user-input');
    const form = document.getElementById('chat-message-form');
    if (input && form) {
        input.value = questionText;
        input.style.height = (input.scrollHeight) + 'px';
        form.dispatchEvent(new Event('submit'));
    }
}

// Append a message bubble dynamically
function appendMessageBubble(role, content) {
    const container = document.getElementById('chat-messages-box');
    const row = document.createElement('div');
    row.className = `message-row ${role}-row`;

    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${role}-bubble`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (role === 'assistant') {
        contentDiv.innerHTML = formatMarkdown(content);
    } else {
        contentDiv.textContent = content; // Keep user inputs plain/escaped
    }

    bubble.appendChild(contentDiv);

    if (role === 'assistant') {
        const actionsDiv = document.createElement('div');
        actionsDiv.className = 'message-actions';
        
        const copyBtn = document.createElement('button');
        copyBtn.className = 'copy-response-btn';
        copyBtn.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
        copyBtn.onclick = function() { copyResponse(this); };
        
        actionsDiv.appendChild(copyBtn);
        bubble.appendChild(actionsDiv);
    }

    row.appendChild(bubble);
    container.appendChild(row);
}

// Helper to escape HTML characters
function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// Format all existing messages on initial render
function formatAllExistingMessages() {
    const assistantContents = document.querySelectorAll('.assistant-bubble .message-content');
    assistantContents.forEach(div => {
        // Format markdown text on existing database messages
        const rawText = div.textContent;
        div.innerHTML = formatMarkdown(rawText);
    });
}

// Custom Markdown formatting engine (Intermediate Regex)
function formatMarkdown(text) {
    if (!text) return "";
    
    let formattedText = text;

    // 1. Process code blocks with triple backticks: ```lang \n code \n ```
    // Match language and content
    const codeBlockRegex = /```(\w*)\n([\s\S]*?)```/g;
    formattedText = formattedText.replace(codeBlockRegex, (match, lang, code) => {
        const cleanCode = escapeHTML(code.trim());
        const displayLang = lang ? lang.toUpperCase() : 'CODE';
        
        return `
            <div class="code-header">
                <span><i class="fa-solid fa-code"></i> ${displayLang}</span>
                <button class="copy-code-btn" onclick="copyCodeBlock(this)"><i class="fa-regular fa-copy"></i> Copy Code</button>
            </div>
            <pre><code class="language-${lang}">${cleanCode}</code></pre>
        `;
    });

    // 2. Process inline code with single backticks: `code`
    formattedText = formattedText.replace(/`([^`]+)`/g, (match, code) => {
        return `<code>${escapeHTML(code)}</code>`;
    });

    // 3. Process strong formatting: **bold**
    formattedText = formattedText.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 4. Process italic formatting: *italic*
    formattedText = formattedText.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 5. Convert lists items
    // Bullet list items
    formattedText = formattedText.replace(/^\s*-\s+(.+)$/gm, '<li>$1</li>');
    // Wrap consecutive list items in <ul>
    formattedText = formattedText.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // 6. Handle standard line breaks (only if not inside <pre> structures)
    // Splitting the text by pre blocks to avoid adding <br> tags inside code containers
    const parts = formattedText.split(/(<pre>[\s\S]*?<\/pre>)/);
    for (let i = 0; i < parts.length; i++) {
        if (!parts[i].startsWith('<pre>')) {
            // Replace newlines with breaks in text sections
            parts[i] = parts[i].replace(/\n/g, '<br>');
        }
    }
    formattedText = parts.join('');

    return formattedText;
}

// Copy full response message bubble
function copyResponse(buttonElement) {
    // Find the message bubble content div
    const bubble = buttonElement.closest('.message-bubble');
    const contentDiv = bubble.querySelector('.message-content');
    
    // We want the text content, removing tags or copying raw HTML text
    // Using innerText retrieves formatted text (similar to how it displays)
    const textToCopy = contentDiv.innerText;

    navigator.clipboard.writeText(textToCopy)
        .then(() => {
            // Success Feedback
            const originalHTML = buttonElement.innerHTML;
            buttonElement.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            buttonElement.disabled = true;
            
            setTimeout(() => {
                buttonElement.innerHTML = originalHTML;
                buttonElement.disabled = false;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy text: ', err);
        });
}

// Copy specific code block content
function copyCodeBlock(buttonElement) {
    const header = buttonElement.closest('.code-header');
    // The pre element sits right after the header
    const pre = header.nextElementSibling;
    const code = pre.querySelector('code');
    
    const codeText = code.textContent;

    navigator.clipboard.writeText(codeText)
        .then(() => {
            const originalText = buttonElement.innerHTML;
            buttonElement.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
            buttonElement.disabled = true;
            
            setTimeout(() => {
                buttonElement.innerHTML = originalText;
                buttonElement.disabled = false;
            }, 2000);
        })
        .catch(err => {
            console.error('Failed to copy code: ', err);
        });
}
