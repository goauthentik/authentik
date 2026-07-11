import { DOMEventHandlerNames } from "@goauthentik/lit-jsx";

import { describe, expectTypeOf, it } from "vitest";

describe("DOMEventHandlerNames completeness", () => {
    it("covers every GlobalEventHandlersEventMap event", () => {
        type Covered = (typeof DOMEventHandlerNames)[keyof typeof DOMEventHandlerNames];
        type Missing = Exclude<keyof GlobalEventHandlersEventMap, Covered>;

        expectTypeOf<Missing>().toEqualTypeOf<never>();
    });
});

describe("intrinsic elements", () => {
    it("accepts global attributes, class values, and typed event handlers", () => {
        <div
            id="a"
            class={["x", { y: true }]}
            slot="body"
            title="t"
            data-anything="1"
            aria-label="label"
            onClick={(event) => {
                // This TS lib types the `click` event as `PointerEvent` (a
                // `MouseEvent` subtype), not `MouseEvent` itself.
                expectTypeOf(event).toEqualTypeOf<PointerEvent>();
            }}
        />;
    });

    it("accepts element-specific properties", () => {
        <input type="text" value="v" placeholder="p" disabled />;
        <label htmlFor="field">name</label>;
        <img src="/x.png" alt="x" width={10} />;
    });

    it("types keyboard handlers with the right event", () => {
        <input
            onKeyDown={(event) => {
                expectTypeOf(event).toEqualTypeOf<KeyboardEvent>();
            }}
        />;
    });

    it("rejects unknown tags and misspelled handlers", () => {
        // @ts-expect-error - not a real element
        <notarealtag />;
        // @ts-expect-error - misspelled handler
        <div onClik={() => {}} />;
    });

    it("rejects wrong prop value types", () => {
        // @ts-expect-error - width is numeric
        <img width="not-a-number-type" src="/x.png" alt="" />;
    });
});
