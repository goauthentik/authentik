/**
 * @param {Schema} schema
 *   Schema to use.
 * @param {string} defaultTagName
 *   Default tag name.
 * @param {Array<string> | undefined} [caseSensitive]
 *   Case-sensitive tag names (default: `undefined`).
 * @returns
 *   `h`.
 */
export function createH(schema: Schema, defaultTagName: string, caseSensitive?: Array<string> | undefined): {
    /**
     * Hyperscript compatible DSL for creating virtual hast trees.
     *
     * @overload
     * @param {null | undefined} [selector]
     * @param {...Child} children
     * @returns {Root}
     *
     * @overload
     * @param {string} selector
     * @param {Properties} properties
     * @param {...Child} children
     * @returns {Element}
     *
     * @overload
     * @param {string} selector
     * @param {...Child} children
     * @returns {Element}
     *
     * @param {string | null | undefined} [selector]
     *   Selector.
     * @param {Child | Properties | null | undefined} [properties]
     *   Properties (or first child) (default: `undefined`).
     * @param {...Child} children
     *   Children.
     * @returns {Result}
     *   Result.
     */
    (selector?: null | undefined, ...children: Child[]): Root;
    /**
     * Hyperscript compatible DSL for creating virtual hast trees.
     *
     * @overload
     * @param {null | undefined} [selector]
     * @param {...Child} children
     * @returns {Root}
     *
     * @overload
     * @param {string} selector
     * @param {Properties} properties
     * @param {...Child} children
     * @returns {Element}
     *
     * @overload
     * @param {string} selector
     * @param {...Child} children
     * @returns {Element}
     *
     * @param {string | null | undefined} [selector]
     *   Selector.
     * @param {Child | Properties | null | undefined} [properties]
     *   Properties (or first child) (default: `undefined`).
     * @param {...Child} children
     *   Children.
     * @returns {Result}
     *   Result.
     */
    (selector: string, properties: Properties, ...children: Child[]): Element;
    /**
     * Hyperscript compatible DSL for creating virtual hast trees.
     *
     * @overload
     * @param {null | undefined} [selector]
     * @param {...Child} children
     * @returns {Root}
     *
     * @overload
     * @param {string} selector
     * @param {Properties} properties
     * @param {...Child} children
     * @returns {Element}
     *
     * @overload
     * @param {string} selector
     * @param {...Child} children
     * @returns {Element}
     *
     * @param {string | null | undefined} [selector]
     *   Selector.
     * @param {Child | Properties | null | undefined} [properties]
     *   Properties (or first child) (default: `undefined`).
     * @param {...Child} children
     *   Children.
     * @returns {Result}
     *   Result.
     */
    (selector: string, ...children: Child[]): Element;
};
export type Element = import('hast').Element;
export type Nodes = import('hast').Nodes;
export type Root = import('hast').Root;
export type RootContent = import('hast').RootContent;
export type Info = import('property-information').Info;
export type Schema = import('property-information').Schema;
/**
 * Result from a `h` (or `s`) call.
 */
export type Result = Element | Root;
/**
 * Value for a CSS style field.
 */
export type StyleValue = number | string;
/**
 * Supported value of a `style` prop.
 */
export type Style = Record<string, StyleValue>;
/**
 * Primitive property value.
 */
export type PrimitiveValue = boolean | number | string | null | undefined;
/**
 * List of property values for space- or comma separated values (such as `className`).
 */
export type ArrayValue = Array<number | string>;
/**
 * Primitive value or list value.
 */
export type PropertyValue = (string | number)[] | PrimitiveValue;
/**
 * Acceptable value for element properties.
 */
export type Properties = {
    [property: string]: Style | PropertyValue;
};
/**
 * Primitive children, either ignored (nullish), or turned into text nodes.
 */
export type PrimitiveChild = number | string | null | undefined;
/**
 * List of children.
 */
export type ArrayChild = Array<(import("hast").Nodes | PrimitiveChild)[] | Nodes | PrimitiveChild>;
/**
 * List of children (deep).
 */
export type ArrayChildNested = Array<Nodes | PrimitiveChild>;
/**
 * Acceptable child value.
 */
export type Child = (import("hast").Nodes | PrimitiveChild | ArrayChildNested)[] | Nodes | PrimitiveChild;
//# sourceMappingURL=create-h.d.ts.map