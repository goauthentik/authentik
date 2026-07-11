import type { FC } from "@goauthentik/lit-jsx";
import { DOMEventHandlerNames } from "@goauthentik/lit-jsx";

import { describe, expectTypeOf, it } from "vitest";

import { html, LitElement } from "lit";

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
            // eslint-disable-next-line react/no-unknown-property -- lit-jsx uses `class`, not `className` like React
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
        // eslint-disable-next-line react/no-unknown-property -- deliberately misspelled handler for the negative type-test above
        <div onClik={() => undefined} />;
    });

    it("rejects wrong prop value types", () => {
        // @ts-expect-error - width is numeric
        <img width="not-a-number-type" src="/x.png" alt="" />;
    });
});

class AkTypedWidget extends LitElement {
    static properties = {
        label: { type: String },
        count: { type: Number },
        active: { type: Boolean },
    };

    declare label: string;
    declare count: number;
    declare active: boolean;

    render() {
        return html`${this.label}`;
    }
}

describe("custom element classes as tags", () => {
    it("accepts declared properties and custom event handlers", () => {
        <AkTypedWidget
            label="hi"
            count={3}
            active
            onAkChange={(event) => {
                expectTypeOf(event).toEqualTypeOf<Event>();
            }}
        />;
    });

    it("accepts base props and refs", () => {
        <AkTypedWidget
            label="hi"
            class="x"
            slot="s"
            data-x="1"
            ref={(element) => {
                expectTypeOf(element).toEqualTypeOf<AkTypedWidget | undefined>();
            }}
        />;
    });

    it("rejects wrong property types and non-element classes", () => {
        // @ts-expect-error - count is a number
        <AkTypedWidget count="three" />;

        class NotAnElement {}
        // @ts-expect-error - not an HTMLElement subclass
        <NotAnElement />;
    });
});

describe("function components", () => {
    const Panel: FC<{ heading: string }> = ({ heading, children }) => (
        <section>
            <h2>{heading}</h2>
            {children}
        </section>
    );

    it("accepts declared props and children", () => {
        <Panel heading="h">
            <p>body</p>
        </Panel>;
    });

    it("rejects missing and unknown props", () => {
        // @ts-expect-error - heading is required
        <Panel />;
        // @ts-expect-error - unknown prop
        <Panel heading="h" mystery={1} />;
    });
});
