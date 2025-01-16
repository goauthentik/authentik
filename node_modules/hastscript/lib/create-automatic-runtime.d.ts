/**
 * Create an automatic runtime.
 *
 * @param {ReturnType<CreateH>} f
 *   `h` function.
 * @returns
 *   Automatic JSX runtime.
 */
export function createAutomaticRuntime(f: ReturnType<CreateH>): {
    Fragment: null;
    jsx: {
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: null, props: {
            children?: Child;
        }, key?: string | undefined): Root;
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: string, props: JSXProps, key?: string | undefined): Element;
    };
    jsxDEV: {
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: null, props: {
            children?: Child;
        }, key?: string | undefined): Root;
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: string, props: JSXProps, key?: string | undefined): Element;
    };
    jsxs: {
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: null, props: {
            children?: Child;
        }, key?: string | undefined): Root;
        /**
         * @overload
         * @param {null} type
         * @param {{children?: Child}} props
         * @param {string} [key]
         * @returns {Root}
         *
         * @overload
         * @param {string} type
         * @param {JSXProps} props
         * @param {string} [key]
         * @returns {Element}
         *
         * @param {string | null} type
         *   Element name or `null` to get a root.
         * @param {Properties & {children?: Child}} props
         *   Properties.
         * @returns {Result}
         *   Result.
         */
        (type: string, props: JSXProps, key?: string | undefined): Element;
    };
};
export type Element = import('hast').Element;
export type Root = import('hast').Root;
export type Child = import('./create-h.js').Child;
export type Properties = import('./create-h.js').Properties;
export type PropertyValue = import('./create-h.js').PropertyValue;
export type Result = import('./create-h.js').Result;
export type Style = import('./create-h.js').Style;
export type CreateH = typeof import("./create-h.js").createH;
export type JSXProps = Record<string, Child | PropertyValue | Style>;
//# sourceMappingURL=create-automatic-runtime.d.ts.map