/**
 * @typedef {import('./create-h.js').Child} Child
 *   Acceptable child value.
 * @typedef {import('./create-h.js').Properties} Properties
 *   Acceptable value for element properties.
 * @typedef {import('./create-h.js').Result} Result
 *   Result from a `h` (or `s`) call.
 */

// Register the JSX namespace on `h`.
/**
 * @typedef {import('./jsx-classic.js').Element} h.JSX.Element
 * @typedef {import('./jsx-classic.js').ElementChildrenAttribute} h.JSX.ElementChildrenAttribute
 * @typedef {import('./jsx-classic.js').IntrinsicAttributes} h.JSX.IntrinsicAttributes
 * @typedef {import('./jsx-classic.js').IntrinsicElements} h.JSX.IntrinsicElements
 */

// Register the JSX namespace on `s`.
/**
 * @typedef {import('./jsx-classic.js').Element} s.JSX.Element
 * @typedef {import('./jsx-classic.js').ElementChildrenAttribute} s.JSX.ElementChildrenAttribute
 * @typedef {import('./jsx-classic.js').IntrinsicAttributes} s.JSX.IntrinsicAttributes
 * @typedef {import('./jsx-classic.js').IntrinsicElements} s.JSX.IntrinsicElements
 */

import {html, svg} from 'property-information'
import {createH} from './create-h.js'
import {svgCaseSensitiveTagNames} from './svg-case-sensitive-tag-names.js'

// Note: this explicit type is needed, otherwise TS creates broken types.
/** @type {ReturnType<createH>} */
export const h = createH(html, 'div')

// Note: this explicit type is needed, otherwise TS creates broken types.
/** @type {ReturnType<createH>} */
export const s = createH(svg, 'g', svgCaseSensitiveTagNames)
