Can we move some the functionality fom JS to hyperscript to minimize JS.
Note however, if the functionality is complex and requires JS you should not change it to hyperscript. We are only looking to minimize code, and make it readable, simpler and easier to maintain, Do not write complex JS within the hyperscript tag.

use hyperscript when possible to reduce the amount of JS required, 



Can you update the application logic to minimize JavaScript usage by moving simple, declarative behaviors to Hyperscript where appropriate. Keep complex logic in JavaScript—only transfer functionality that is straightforward, readable, and maintainable in Hyperscript. Avoid writing intricate or imperative code within Hyperscript tags. Prioritize clarity, simplicity, and ease of maintenance.

```
hyperscript errors were found on the following element: <input type="file" id="fileInput" name="files" accept="image/*,.pdf" class="hidden" multiple _="on change
```

===

During the streaming stage, if the page gets reloaded, the message of the bot response completely disappears and never gets appended to the UI. Investigate this behavior and come up with plan on how to fix it

During the streaming phase, bot response messages are lost upon page reload and do not persist or reappear in the UI. Investigate the root cause of this issue and provide a clear, actionable plan to ensure message continuity across reloads, leveraging appropriate state preservation mechanisms such as client-side storage or session restoration.


It's working but we have one kind of behavior that we need to fix. When the page reload it should not start from scratch currently it's restart from scratch as if the message is regenerating from scratch. It should instead continue where it left off before the page gets reloaded.


It works now, but with minor inconvenience, When the page reloads, the application should resume from the last state, instead of restarting from scratch, currently it restart the generation from scratch. Specifically, it should continue the ongoing message generation process, ensuring continuity without reprocessing, the backend should not be affected by the UI state. The UI should reflect the backend state. 

Implement state persistence to maintain context across page reloads.



===

Now, all hyperscript errors are resolved. And the rendering works correctly now. However, there is an issue we have to fix, which is when the page reloaded mid generation, currently it breaks the generation, the generation stops, and the generated snippet so far doesn't render as markdown.
Note, the application should resume from the last state, instead of restarting from scratch, currently it restart the generation from scratch. Specifically, it should continue the ongoing message generation process, ensuring continuity without reprocessing, the backend should not be affected by the UI state. The UI should reflect the backend state


But with a minor inconvenience. Specifically, when the page reloads, 
