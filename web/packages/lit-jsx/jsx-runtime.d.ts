import { JSX } from "react";

import { nothing, TemplateResult } from "lit";

export = LitJSX;
export as namespace LitJSX;

declare namespace LitJSX {
    export type CustomElementConstructor<T extends HTMLElement = HTMLElement> = new (
        ...args: any[]
    ) => T;

    export type CustomElementComponent<P = any> = (props: P) => ElementType;

    export type ElementType<
        P = any,
        Tag extends keyof React.JSX.IntrinsicElements = keyof React.JSX.IntrinsicElements,
    > =
        | { [K in Tag]: P extends React.JSX.IntrinsicElements[K] ? K : never }[Tag]
        | CustomElementConstructor<P>;

    export interface Fragment {
        children: LitJSX.ElementType | LitJSX.ElementType[];
    }

    export type LitNode = JSX.Element | ElementType | string | TemplateResult | typeof nothing;

    export type FC<P = any> = (props: P) => LitNode | LitNode[];

    export { JSX };
}
