window.renderMessage = function (el) {
    if (!window.marked || !window.renderMathInElement || !window.hljs) {
        console.warn('Markdown, LaTeX, or Highlight renderer not found. Retrying in 50ms...');
        setTimeout(() => window.renderMessage(el), 50);
        return;
    }

    // Configure marked to treat single newlines as <br> tags
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // Capture the raw text before any processing
    // We use textContent to avoid browser CSS whitespace collapsing (innerText would return collapsed text)
    const rawContent = el.textContent;

    // Configure marked to treat single newlines as <br> tags
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // 1. Render Markdown
    el.innerHTML = marked.parse(rawContent);

    // 2. Render LaTeX
    renderMathInElement(el, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false }
        ],
        throwOnError: false
    });

    // 3. Add Copy Buttons and Syntax Highlighting to Code Blocks
    const codeBlocks = el.querySelectorAll('pre');
    codeBlocks.forEach(pre => {
        const code = pre.querySelector('code');
        if (code) {
            // Apply Highlight.js
            hljs.highlightElement(code);

            // Avoid duplicate containers if re-rendered
            if (pre.parentElement.classList.contains('code-block-container')) return;
            const container = document.createElement('div');
            container.className = 'code-block-container';

            // Re-structure DOM
            pre.parentNode.insertBefore(container, pre);
            container.appendChild(pre);

            // Create button
            const btn = document.createElement('button');
            btn.className = 'copy-button';
            btn.innerHTML = `
                <svg fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path>
                </svg>
                <span>Copy</span>
            `;

            // Click Handler
            btn.onclick = () => {
                const textToCopy = code.innerText;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const span = btn.querySelector('span');
                    const originalHTML = btn.innerHTML;

                    span.innerText = 'Copied!';
                    btn.classList.add('text-green-400');

                    setTimeout(() => {
                        span.innerText = 'Copy';
                        btn.classList.remove('text-green-400');
                    }, 2000);
                }).catch(err => {
                    console.error('Failed to copy: ', err);
                });
            };

            container.appendChild(btn);
        }
    });

    // Final Styling Adjustments
    el.classList.remove('whitespace-pre-wrap');
    el.classList.add('markdown-content');
};

window.copyMessage = function (btn, text) {
    navigator.clipboard.writeText(text).then(() => {
        const original = btn.innerText;
        btn.innerText = '✅';
        setTimeout(() => {
            btn.innerText = original;
        }, 1000);
    }).catch(err => {
        console.error('Failed to copy message: ', err);
    });
};

/**
 * Streaming-optimized render function for live token updates.
 * Renders Markdown/LaTeX live as tokens arrive.
 * Uses 'breaks: true' to ensure newlines are respected during the stream.
 */
window.renderMessageStreaming = function (el) {
    if (!window.marked || !window.renderMathInElement || !window.hljs) {
        console.warn('Renderers not ready, retrying...');
        setTimeout(() => window.renderMessageStreaming(el), 50);
        return;
    }

    // Configure marked to treat single newlines as <br> tags
    marked.setOptions({
        breaks: true,
        gfm: true
    });

    // Get the raw accumulated text
    const rawContent = el.textContent || el.innerText;

    // Skip if empty
    if (!rawContent || !rawContent.trim()) return;

    // 1. Render Markdown live
    el.innerHTML = marked.parse(rawContent);

    // 2. Render LaTeX live
    renderMathInElement(el, {
        delimiters: [
            { left: '$$', right: '$$', display: true },
            { left: '$', right: '$', display: false }
        ],
        throwOnError: false
    });

    // 3. Lightweight syntax highlighting
    const codeBlocks = el.querySelectorAll('pre code');
    codeBlocks.forEach(code => {
        if (!code.classList.contains('hljs')) {
            hljs.highlightElement(code);
        }
    });

    // Apply markdown styling
    el.classList.add('markdown-content');
};

/**
 * Final render function called when streaming is complete.
 * This does full markdown/LaTeX/syntax parsing with all features.
 */
window.finalizeStreamedMessage = function (el) {
    // Call the full render function to add copy buttons and final styling
    window.renderMessage(el);
};

/**
 * Client-side component renderer for Bot Action Buttons.
 * Generates the Copy, Edit, and Regenerate buttons dynamically.
 */
window.renderBotActions = function (containerEl, convId, msgIndex, content) {
    if (!containerEl) return;

    // Escape content for safety in attributes
    const safeContent = content
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

    const html = `
        <button class="action-btn" title="Copy" data-message="${safeContent}" 
            _="on click copyMessage(me, my.getAttribute('data-message'))">📋</button>
        
        <button class="action-btn" title="Edit" _="on click
            add .hidden to #message-bubble-${msgIndex}
            add .hidden to my parentElement
            remove .hidden from #edit-container-${msgIndex}
            focus() on #edit-textarea-${msgIndex}">✏️</button>
        
        <button class="action-btn" title="Regenerate">♻️</button>
    `;

    containerEl.innerHTML = html;

    // Activate Hyperscript logic on the new elements
    if (window._hyperscript) {
        window._hyperscript.processNode(containerEl);
    }
};
