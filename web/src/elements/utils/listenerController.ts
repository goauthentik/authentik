// This is a more modern way to handle disconnecting listeners on demand.

// example usage:

/*
export class MyElement extends LitElement {

   this.listenerController = new ListenerController();

   connectedCallback() {
      super.connectedCallback();
      window.addEventListener("event-1", handler1, { signal: this.listenerController.signal });
      window.addEventListener("event-2", handler2, { signal: this.listenerController.signal });
      window.addEventListener("event-3", handler3, { signal: this.listenerController.signal });
   }

   disconnectedCallback() {
      // This will disconnect *all* the event listeners at once, and resets the listenerController,
      // releasing the memory used for the signal as well. No more trying to map all the
      // `addEventListener` to `removeEventListener` tediousness!
      this.listenerController.abort();
      super.disconnectedCallback();
   }
}
*/

export class ListenerController {
    listenerController?: AbortController;

    get signal() {
        if (!this.listenerController) {
            this.listenerController = new AbortController();
        }
        return this.listenerController.signal;
    }

    abort() {
        this.listenerController?.abort();
        this.listenerController = undefined;
    }
}
