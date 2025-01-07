"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.getQualifierMessage = exports.getSchemaName = void 0;
function prettyName(schema, circular) {
    var _a, _b, _c;
    if (schema.$ref) {
        return schema.$ref.replace("#/components/schemas/", "") + circular
            ? " (circular)"
            : "";
    }
    if (schema.format) {
        return schema.format;
    }
    if (schema.allOf) {
        return "object";
    }
    if (schema.type === "object") {
        return (_b = (_a = schema.xml) === null || _a === void 0 ? void 0 : _a.name) !== null && _b !== void 0 ? _b : schema.type;
    }
    return (_c = schema.title) !== null && _c !== void 0 ? _c : schema.type;
}
function getSchemaName(schema, circular) {
    var _a;
    if (schema.items) {
        return prettyName(schema.items, circular) + "[]";
    }
    return (_a = prettyName(schema, circular)) !== null && _a !== void 0 ? _a : "";
}
exports.getSchemaName = getSchemaName;
function getQualifierMessage(schema) {
    // TODO:
    // - maxItems
    // - minItems
    // - uniqueItems
    // - maxProperties
    // - minProperties
    // - multipleOf
    if (!schema) {
        return undefined;
    }
    if (schema.items) {
        return getQualifierMessage(schema.items);
    }
    let message = "**Possible values:** ";
    let qualifierGroups = [];
    if (schema.minLength || schema.maxLength) {
        let lengthQualifier = "";
        if (schema.minLength) {
            lengthQualifier += `${schema.minLength} ≤ `;
        }
        lengthQualifier += "length";
        if (schema.maxLength) {
            lengthQualifier += ` ≤ ${schema.maxLength}`;
        }
        qualifierGroups.push(lengthQualifier);
    }
    if (schema.minimum ||
        schema.maximum ||
        typeof schema.exclusiveMinimum === "number" ||
        typeof schema.exclusiveMaximum === "number") {
        let minmaxQualifier = "";
        if (typeof schema.exclusiveMinimum === "number") {
            minmaxQualifier += `${schema.exclusiveMinimum} < `;
        }
        else if (schema.minimum && !schema.exclusiveMinimum) {
            minmaxQualifier += `${schema.minimum} ≤ `;
        }
        else if (schema.minimum && schema.exclusiveMinimum === true) {
            minmaxQualifier += `${schema.minimum} < `;
        }
        minmaxQualifier += "value";
        if (typeof schema.exclusiveMaximum === "number") {
            minmaxQualifier += ` < ${schema.exclusiveMaximum}`;
        }
        else if (schema.maximum && !schema.exclusiveMaximum) {
            minmaxQualifier += ` ≤ ${schema.maximum}`;
        }
        else if (schema.maximum && schema.exclusiveMaximum === true) {
            minmaxQualifier += ` < ${schema.maximum}`;
        }
        qualifierGroups.push(minmaxQualifier);
    }
    if (schema.pattern) {
        qualifierGroups.push(`Value must match regular expression \`${schema.pattern}\``);
    }
    if (schema.enum) {
        qualifierGroups.push(`[${schema.enum.map((e) => `\`${e}\``).join(", ")}]`);
    }
    if (qualifierGroups.length === 0) {
        return undefined;
    }
    return message + qualifierGroups.join(", ");
}
exports.getQualifierMessage = getQualifierMessage;
