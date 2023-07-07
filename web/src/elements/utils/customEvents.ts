export const customEvent = (name: string, details = {}) =>
    new CustomEvent(name as string, {
        composed: true,
        bubbles: true,
        detail: details,
    });

// "Unknown" seems to violate some obscure Typescript rule and doesn't work here, although it
// should.
//
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const isCustomEvent = (v: any): v is CustomEvent =>
    v instanceof CustomEvent && "detail" in v;
