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
                <span class="material-symbols-rounded" style="font-size: 14px">content_copy</span>
                <span>Copy</span>
            `;

            // Click Handler
            btn.onclick = () => {
                const textToCopy = code.innerText;
                navigator.clipboard.writeText(textToCopy).then(() => {
                    const span = btn.querySelector('span:last-child');
                    const icon = btn.querySelector('.material-symbols-rounded');
                    
                    span.innerText = 'Copied!';
                    icon.innerText = 'check';

                    setTimeout(() => {
                        span.innerText = 'Copy';
                        icon.innerText = 'content_copy';
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
    const icon = btn.querySelector('.material-symbols-rounded');
    const originalIcon = icon.innerText;
    
    navigator.clipboard.writeText(text).then(() => {
        icon.innerText = 'check';
        btn.classList.add('text-green-600');
        setTimeout(() => {
            icon.innerText = originalIcon;
            btn.classList.remove('text-green-600');
        }, 1500);
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
