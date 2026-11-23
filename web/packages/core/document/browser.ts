/**
 * Read a server-injected `<meta>` value, if the document carries one.
 */
export function readMeta(name: string): string | null {
    const element = document.querySelector<HTMLMetaElement>(`meta[name="${name}"]`);

    return element?.content || null;
}

/**
 * Parse a server-injected `json_script` block, if the document carries one.
 *
 * A malformed block is treated as absent, so callers can fall back to defaults
 * rather than failing to render at all.
 */
export function readJSONScript<T>(id: string): T | null {
    const element = document.getElementById(id);

    if (!element?.textContent) return null;

    try {
        return JSON.parse(element.textContent);
    } catch (_error) {
        return null;
    }
}

/**
 * Create a `<script type="application/json">` element with the given data and optional ID.
 */
export function createJSONScriptElement(
    data?: unknown,
    id?: string,
    ownerDocument: Document = document,
): HTMLScriptElement {
    const script = ownerDocument.createElement("script");
    script.type = "application/json";

    script.textContent = JSON.stringify(data ?? {});

    if (id) {
        script.id = id;
    }

    return script;
}

/**
 * Inject the given element into the destination, replacing any existing element with the same ID.
 */
export function injectOrSwap(element: HTMLElement, destination: HTMLElement = document.head): void {
    const existing = destination.ownerDocument.getElementById(element.id);

    if (existing) {
        existing.replaceWith(element);
    } else {
        destination.append(element);
    }
}
