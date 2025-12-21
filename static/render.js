window.renderMessage = function (el) {
    if (!window.marked || !window.renderMathInElement || !window.hljs) {
        console.warn('Markdown, LaTeX, or Highlight renderer not found. Retrying in 50ms...');
        setTimeout(() => window.renderMessage(el), 50);
        return;
    }

    // Capture the raw text before any processing
    const rawContent = el.innerText;

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
