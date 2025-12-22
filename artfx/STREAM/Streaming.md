Can we support streaming for bot responses, for a more responsive and interactive experience for users, where the tokens are injected as they are generated?

> WARNING: The implementation should not be merely a visual effect, it must be implemented as feature where the messages is sent in chunk from the backend

You should explor how to transition from the existing fetch-all-at-once method to a streaming approach. 
The key is in breaking down the response delivery into chunks. The goal is to find the optimum way to achieve the desired typing effect and update the message content dynamically.

### Analyzing Streaming Strategies
- You should evaluat different streaming strategies in light of the need for real-time updates within a single message bubble. Considering the constraints of standard HTMX's append behavior, SSE appears promising for this purpose. 

Consider using the sse extension or a custom StreamingResponse, along with fragments, to inject tokens directly into the message's content dynamically. 

---

## Exploring Streaming Options

Explore the StreamingResponse with partial HTML or JSON and the SSE extension's data: ... events. 
However, a StreamingResponse could yield complete message states repeatedly, but it seems wasteful. 
If you lean toward the SSE extension, you need to integrate it. It is not currently loaded in the base HTML.

## Considering Simplest Approach - Simplifying the stream integration.
Explore an application/x-ndjson or text stream with custom JavaScript for a typing effect. 
While initial plans involves SSE or complex HTMX modifications, 
If you leaning toward a streamlined approach using a StreamingResponse that yields script tags or fragments for DOM updates. Though, the yielded fragments were also a bit messy. 
It seems like using the HTMX SSE extension, if added, might be the most simple method.

## SSE Integration

If you decided to integrate SSE into the framework, focus on optimizing the data flow. The base HTML should be updated to include the HTMX SSE extension. And modify the /chat/{conv_id}/bot-response endpoint to handle SSE connections. Also, a generator to yield tokens and updating the bot_trigger_html with hx-ext="sse" sse-connect="..." for message event listening. 
The goal is to update the inner HTML of the chat bubble, rather than re-rendering the whole. Probably by sending many small updates as tokens.

## Prioritizing Token Accumulation

Consider token accumulation for SSE implementation. If you are leaning towards accumulating tokens on the server-side before sending updates, which seems straightforward for correct rendering. 
Propbably you should modify the /chat/{conv_id}/bot-stream endpoint to yield SSE messages in the specified format, considering both sse-swap and the necessity of managing token accumulation for accurate output in the chat. 
Challenge is balancing streaming with complete and valid HTML rendering at each update.

## Evaluating HTML Rendering

HTML rendering, particularly considering the balance between efficient updates and live rendering of Markdown/KaTeX. Approach to render the message bubble only once, either empty or with a "Thinking..." indicator. 
Probably we swap the whole message bubble with each token arrival. This should trigger the renderMessage function every time, enabling live Markdown and KaTeX rendering as the text is streamed. I'm not sure about this approach though.

## Rendering Strategy
Triggered by the renderMessage function, 
Enable live Markdown and KaTeX output. Since the SSE stream updates only the text, aim for the renderer to be called per token update. 
A final event is planned to signify completion. To achieve this, each token will contain the updated message content. I'm exploring how to trigger renderMessage more often.

### Hyperscript-Rules
- Use hyperscript for simple UI behavior (toggle, show/hide, class switching, basic form interactions) to reduce JS.
- If behavior is complex (multi-step logic, heavy DOM manipulation, async flows, non-trivial state), use JS.
- Do not write JS inside hyperscript tags/attributes.
- Keep hyperscript commands short and readable; if it grows beyond a few lines or becomes hard to scan, move to JS.