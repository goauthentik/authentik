/**
 * @file Vitest browser utilities for Lit.
 *
 * @import { LocatorSelectors } from '@vitest/browser/context'
 * @import { PrettyDOMOptions } from '@vitest/browser/utils'
 * @import { RenderOptions as LitRenderOptions } from 'lit'
 */

import { debug, getElementLocatorSelectors } from "@vitest/browser/utils";

import { render as renderLit } from "lit";

/**
 * @implements {Disposable}
 */
export class LitViteContext {
    /**
     * @type {Set<Disposable>}
     */
    static #resources = new Set();

    /**
     * @param {unknown} template
     * @param {HTMLElement} [container]
     * @param {LitRenderOptions} [options]
     *
     * @returns {LitViteContext}
     */
    static render = (template, container = document.createElement("div"), options) => {
        const context = new LitViteContext(container);
        context.render(template, options);

        return context;
    };

    static [Symbol.dispose] = () => {
        this.#resources.forEach((resource) => resource[Symbol.dispose]());
        this.#resources.clear();
    };

    static cleanup = () => {
        return this[Symbol.dispose]();
    };

    /**
     * @param {unknown} template
     * @param {LitRenderOptions} [options]
     */
    render(template, options) {
        return renderLit(template, this.container, options);
    }

    /**
     * @type {HTMLElement} container
     */
    container;

    /**
     * @type {LocatorSelectors}
     */
    $;

    /**
     * @param {HTMLElement} container
     */
    constructor(container) {
        this.container = container;
        this.$ = getElementLocatorSelectors(container);
    }

    toFragment() {
        return document.createRange().createContextualFragment(this.container.innerHTML);
    }

    /**
     * @param {number} [maxLength]
     * @param {PrettyDOMOptions} [options]
     */
    debug(maxLength, options) {
        return debug(this.container, maxLength, options);
    }

    [Symbol.dispose] = () => {
        this.container.remove();
        LitViteContext.#resources.delete(this);
    };
}
