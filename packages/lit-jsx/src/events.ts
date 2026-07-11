/**
 * Canonical camelCase handler prop names for standard DOM events.
 *
 * Single source of truth: the runtime resolves `on*` props through this map,
 * and the JSX types derive handler prop names from its keys.
 *
 * The `satisfies` clause rejects any value that is not a real
 * {@linkcode GlobalEventHandlersEventMap} event name; a type-level test
 * asserts the reverse direction (every event name is covered).
 */
export const DOMEventHandlerNames = {
    onAbort: "abort",
    onAnimationCancel: "animationcancel",
    onAnimationEnd: "animationend",
    onAnimationIteration: "animationiteration",
    onAnimationStart: "animationstart",
    onAuxClick: "auxclick",
    onBeforeInput: "beforeinput",
    onBeforeMatch: "beforematch",
    onBeforeToggle: "beforetoggle",
    onBlur: "blur",
    onCancel: "cancel",
    onCanPlay: "canplay",
    onCanPlayThrough: "canplaythrough",
    onChange: "change",
    onClick: "click",
    onClose: "close",
    onCommand: "command",
    onCompositionEnd: "compositionend",
    onCompositionStart: "compositionstart",
    onCompositionUpdate: "compositionupdate",
    onContextLost: "contextlost",
    onContextMenu: "contextmenu",
    onContextRestored: "contextrestored",
    onCopy: "copy",
    onCueChange: "cuechange",
    onCut: "cut",
    onDblClick: "dblclick",
    onDrag: "drag",
    onDragEnd: "dragend",
    onDragEnter: "dragenter",
    onDragLeave: "dragleave",
    onDragOver: "dragover",
    onDragStart: "dragstart",
    onDrop: "drop",
    onDurationChange: "durationchange",
    onEmptied: "emptied",
    onEnded: "ended",
    onError: "error",
    onFocus: "focus",
    onFocusIn: "focusin",
    onFocusOut: "focusout",
    onFormData: "formdata",
    onGotPointerCapture: "gotpointercapture",
    onInput: "input",
    onInvalid: "invalid",
    onKeyDown: "keydown",
    onKeyPress: "keypress",
    onKeyUp: "keyup",
    onLoad: "load",
    onLoadedData: "loadeddata",
    onLoadedMetadata: "loadedmetadata",
    onLoadStart: "loadstart",
    onLostPointerCapture: "lostpointercapture",
    onMouseDown: "mousedown",
    onMouseEnter: "mouseenter",
    onMouseLeave: "mouseleave",
    onMouseMove: "mousemove",
    onMouseOut: "mouseout",
    onMouseOver: "mouseover",
    onMouseUp: "mouseup",
    onPaste: "paste",
    onPause: "pause",
    onPlay: "play",
    onPlaying: "playing",
    onPointerCancel: "pointercancel",
    onPointerDown: "pointerdown",
    onPointerEnter: "pointerenter",
    onPointerLeave: "pointerleave",
    onPointerMove: "pointermove",
    onPointerOut: "pointerout",
    onPointerOver: "pointerover",
    onPointerRawUpdate: "pointerrawupdate",
    onPointerUp: "pointerup",
    onProgress: "progress",
    onRateChange: "ratechange",
    onReset: "reset",
    onResize: "resize",
    onScroll: "scroll",
    onScrollEnd: "scrollend",
    onSecurityPolicyViolation: "securitypolicyviolation",
    onSeeked: "seeked",
    onSeeking: "seeking",
    onSelect: "select",
    onSelectionChange: "selectionchange",
    onSelectStart: "selectstart",
    onSlotChange: "slotchange",
    onStalled: "stalled",
    onSubmit: "submit",
    onSuspend: "suspend",
    onTimeUpdate: "timeupdate",
    onToggle: "toggle",
    onTouchCancel: "touchcancel",
    onTouchEnd: "touchend",
    onTouchMove: "touchmove",
    onTouchStart: "touchstart",
    onTransitionCancel: "transitioncancel",
    onTransitionEnd: "transitionend",
    onTransitionRun: "transitionrun",
    onTransitionStart: "transitionstart",
    onVolumeChange: "volumechange",
    onWaiting: "waiting",
    onWebkitAnimationEnd: "webkitanimationend",
    onWebkitAnimationIteration: "webkitanimationiteration",
    onWebkitAnimationStart: "webkitanimationstart",
    onWebkitTransitionEnd: "webkittransitionend",
    onWheel: "wheel",
} as const satisfies Record<`on${string}`, keyof GlobalEventHandlersEventMap>;

export type DOMEventHandlerName = keyof typeof DOMEventHandlerNames;

const eventNameByHandler = new Map<string, string>(Object.entries(DOMEventHandlerNames));
const knownDOMEventNames = new Set<string>(Object.values(DOMEventHandlerNames));

const EventHandlerPattern = /^on[A-Z]/;

/**
 * Acronym-aware kebab-case: `"AKChange"` and `"AkChange"` both become `"ak-change"`.
 */
export function kebabCase(input: string): string {
    return input
        .replace(/([a-z0-9])([A-Z])/g, "$1-$2")
        .replace(/([A-Z]+)([A-Z][a-z])/g, "$1-$2")
        .toLowerCase();
}

/**
 * Resolve a JSX prop name to the DOM event name it binds, or `null` when the
 * prop is not an event handler.
 *
 * Resolution order: canonical map, lowercased match against known DOM events,
 * then kebab-case for custom events.
 */
export function resolveEventName(propName: string): string | null {
    if (!EventHandlerPattern.test(propName)) {
        return null;
    }

    const canonical = eventNameByHandler.get(propName);

    if (canonical) {
        return canonical;
    }

    const remainder = propName.slice(2);
    const lowercased = remainder.toLowerCase();

    if (knownDOMEventNames.has(lowercased)) {
        return lowercased;
    }

    return kebabCase(remainder);
}
