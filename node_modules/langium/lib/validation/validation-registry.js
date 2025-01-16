/******************************************************************************
 * Copyright 2021 TypeFox GmbH
 * This program and the accompanying materials are made available under the
 * terms of the MIT License, which is available in the project root.
 ******************************************************************************/
import { MultiMap } from '../utils/collections.js';
import { isOperationCancelled } from '../utils/promise-utils.js';
import { stream } from '../utils/stream.js';
/**
 * Create DiagnosticData for a given diagnostic code. The result can be put into the `data` field of a DiagnosticInfo.
 */
export function diagnosticData(code) {
    return { code };
}
export var ValidationCategory;
(function (ValidationCategory) {
    ValidationCategory.all = ['fast', 'slow', 'built-in'];
})(ValidationCategory || (ValidationCategory = {}));
/**
 * Manages a set of `ValidationCheck`s to be applied when documents are validated.
 */
export class ValidationRegistry {
    constructor(services) {
        this.entries = new MultiMap();
        this.reflection = services.shared.AstReflection;
    }
    /**
     * Register a set of validation checks. Each value in the record can be either a single validation check (i.e. a function)
     * or an array of validation checks.
     *
     * @param checksRecord Set of validation checks to register.
     * @param category Optional category for the validation checks (defaults to `'fast'`).
     * @param thisObj Optional object to be used as `this` when calling the validation check functions.
     */
    register(checksRecord, thisObj = this, category = 'fast') {
        if (category === 'built-in') {
            throw new Error("The 'built-in' category is reserved for lexer, parser, and linker errors.");
        }
        for (const [type, ch] of Object.entries(checksRecord)) {
            const callbacks = ch;
            if (Array.isArray(callbacks)) {
                for (const check of callbacks) {
                    const entry = {
                        check: this.wrapValidationException(check, thisObj),
                        category
                    };
                    this.addEntry(type, entry);
                }
            }
            else if (typeof callbacks === 'function') {
                const entry = {
                    check: this.wrapValidationException(callbacks, thisObj),
                    category
                };
                this.addEntry(type, entry);
            }
        }
    }
    wrapValidationException(check, thisObj) {
        return async (node, accept, cancelToken) => {
            try {
                await check.call(thisObj, node, accept, cancelToken);
            }
            catch (err) {
                if (isOperationCancelled(err)) {
                    throw err;
                }
                console.error('An error occurred during validation:', err);
                const message = err instanceof Error ? err.message : String(err);
                if (err instanceof Error && err.stack) {
                    console.error(err.stack);
                }
                accept('error', 'An error occurred during validation: ' + message, { node });
            }
        };
    }
    addEntry(type, entry) {
        if (type === 'AstNode') {
            this.entries.add('AstNode', entry);
            return;
        }
        for (const subtype of this.reflection.getAllSubTypes(type)) {
            this.entries.add(subtype, entry);
        }
    }
    getChecks(type, categories) {
        let checks = stream(this.entries.get(type))
            .concat(this.entries.get('AstNode'));
        if (categories) {
            checks = checks.filter(entry => categories.includes(entry.category));
        }
        return checks.map(entry => entry.check);
    }
}
//# sourceMappingURL=validation-registry.js.map