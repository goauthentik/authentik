"use strict";
/* ============================================================================
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.toString = exports.render = exports.guard = exports.create = void 0;
function create(tag, props) {
    const { children, ...rest } = props;
    let propString = "";
    for (const [key, value] of Object.entries(rest)) {
        propString += ` ${key}={${JSON.stringify(value)}}`;
    }
    return `<${tag}${propString}>${render(children)}</${tag}>`;
}
exports.create = create;
function guard(value, cb) {
    if (!!value || value === 0) {
        const children = cb(value);
        return render(children);
    }
    return "";
}
exports.guard = guard;
function render(children) {
    if (Array.isArray(children)) {
        return children.filter((c) => c !== undefined).join("");
    }
    return children ?? "";
}
exports.render = render;
function toString(value) {
    // Return as-is if already string
    if (typeof value === "string") {
        return value;
    }
    // Return undefined if null or undefined
    if (value == null) {
        return undefined;
    }
    // Return formatted array if Array
    if (Array.isArray(value)) {
        return `[${value.join(", ")}]`;
    }
    // Coerce to string in all other cases,
    return value + "";
}
exports.toString = toString;
