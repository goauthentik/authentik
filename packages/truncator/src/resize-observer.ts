/**
 * @file A shared ResizeObserver that routes content-box width changes to
 * registered elements, so a table of many truncation targets costs a single
 * observer rather than one apiece.
 *
 * DOM-only (like `createCanvasMeasurer`) and left untested. The shared instance
 * allocates no ResizeObserver until the first `observe`, so importing this
 * module in a non-DOM environment is safe.
 */

export type TruncationResizeCallback = (width: number) => void;

export class TruncationResizeObserver {
    /**
     * The process-wide shared instance. Elements register against this rather
     * than constructing an observer of their own.
     */
    public static readonly shared: TruncationResizeObserver = new TruncationResizeObserver();

    /**
     * Created lazily on first {@link observe} so importing this module never
     * touches the DOM.
     */
    protected observer: ResizeObserver | null = null;

    protected callbacks: WeakMap<Element, TruncationResizeCallback> = new WeakMap();

    protected dispatchResizeEvents = (entries: ResizeObserverEntry[]) => {
        for (const entry of entries) {
            const callback = this.callbacks.get(entry.target);

            if (!callback) continue;

            const width = entry.contentBoxSize?.[0]?.inlineSize ?? entry.contentRect.width;

            callback(width);
        }
    };

    #delegateAnimationFrameID = -1;

    protected delegateEntries = (entries: ResizeObserverEntry[]) => {
        cancelAnimationFrame(this.#delegateAnimationFrameID);

        this.#delegateAnimationFrameID = requestAnimationFrame(() => {
            this.dispatchResizeEvents(entries);
        });
    };

    /**
     * Begin observing `target`, invoking `callback` with its content-box width
     * on every size change, including the initial post-layout pass.
     */
    public observe(target: Element, callback: TruncationResizeCallback) {
        this.observer ??= new ResizeObserver(this.delegateEntries);

        this.callbacks.set(target, callback);

        this.observer.observe(target);
    }

    /**
     * Stop observing `target`. Must be called on disconnect, or the observer
     * keeps the element alive.
     */
    public unobserve(target: Element) {
        this.callbacks.delete(target);
        this.observer?.unobserve(target);
    }
}
