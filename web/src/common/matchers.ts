/**
 * Invoked when cleanup is required.
 */
export type MediaMatcherDispose = () => void;

/**
 * Callback invoked when a media query match changes.
 */
export type MediaChangeEffect = (event: MediaQueryListEvent) => void;

export interface MediaQueryEffectListenerOptions extends AddEventListenerOptions {
    /**
     * Whether to invoke the effect immediately upon creation.
     */
    immediate?: boolean;
}

/**
 * Create an effect that runs on a media query match.
 *
 * @param query The media query to match.
 * @param effect The callback to run when the media query matches.
 * @param listenerOptions Options for the event listener.
 *
 * @returns A cleanup function that removes the effect.
 */
export function createMediaQueryEffect(
    query: string | MediaQueryList,
    effect: MediaChangeEffect,
    listenerOptions?: MediaQueryEffectListenerOptions,
): MediaMatcherDispose {
    const mediaQueryList = typeof query === "string" ? window.matchMedia(query) : query;

    // First, wrap the effect to ensure we can abort it.
    const mediaChangeListener = (event: MediaQueryListEvent) => {
        if (listenerOptions?.signal?.aborted) {
            return;
        }

        effect(event);
    };

    mediaQueryList.addEventListener("change", mediaChangeListener, listenerOptions);

    const dispose: MediaMatcherDispose = () => {
        mediaQueryList.removeEventListener("change", mediaChangeListener);
    };

    if (listenerOptions?.immediate) {
        effect(
            new MediaQueryListEvent("change", {
                matches: mediaQueryList.matches,
                media: mediaQueryList.media,
            }),
        );
    }

    return dispose;
}
