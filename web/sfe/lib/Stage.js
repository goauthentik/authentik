/**
 * @import { ContextualFlowInfo, ErrorDetail } from "@goauthentik/api";
 */

/**
 * @typedef {object} FlowInfoChallenge
 * @property {ContextualFlowInfo} [flowInfo]
 * @property {Record<string, Array<ErrorDetail>>} [responseErrors]
 */

/**
 * @abstract
 */
export class FlowExecutor {
    constructor() {
        /**
         * The DOM container element.
         *
         * @type {HTMLElement}
         * @abstract
         * @returns {void}
         */
        // eslint-disable-next-line @typescript-eslint/no-unused-expressions
        this.container;
    }

    /**
     * Submits the form data.
     *
     * @param {Record<string, unknown> | FormData} data The data to submit.
     * @abstract
     * @returns {void}
     */
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    submit(data) {
        throw new Error(`Method 'submit' not implemented in ${this.constructor.name}`);
    }
}

/**
 * Represents a stage in a flow
 * @template {FlowInfoChallenge} T
 * @abstract
 */
export class Stage {
    /**
     * @param {FlowExecutor} executor - The executor for this stage
     * @param {T} challenge - The challenge for this stage
     */
    constructor(executor, challenge) {
        /** @type {FlowExecutor} */
        this.executor = executor;

        /** @type {T} */
        this.challenge = challenge;
    }

    /**
     * @protected
     * @param {string} fieldName
     */
    error(fieldName) {
        if (!this.challenge.responseErrors) {
            return [];
        }
        return this.challenge.responseErrors[fieldName] || [];
    }

    /**
     * @protected
     * @param {string} fieldName
     * @returns {string}
     */
    renderInputError(fieldName) {
        return `${this.error(fieldName)
            .map((error) => {
                return /* html */ `<div class="invalid-feedback">
                    ${error.string}
                </div>`;
            })
            .join("")}`;
    }

    /**
     * @protected
     * @returns {string}
     */
    renderNonFieldErrors() {
        return `${this.error("non_field_errors")
            .map((error) => {
                return /* html */ `<div class="alert alert-danger" role="alert">
                    ${error.string}
                </div>`;
            })
            .join("")}`;
    }

    /**
     * @protected
     * @param {string} innerHTML
     * @returns {void}
     */
    html(innerHTML) {
        this.executor.container.innerHTML = innerHTML;
    }

    /**
     * Renders the stage (must be implemented by subclasses)
     *
     * @abstract
     * @returns {void}
     */
    render() {
        throw new Error("Abstract method");
    }
}
