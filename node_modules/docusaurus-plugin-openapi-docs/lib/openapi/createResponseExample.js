"use strict";
/* ============================================================================
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.sampleResponseFromSchema = void 0;
const chalk_1 = __importDefault(require("chalk"));
const merge_1 = __importDefault(require("lodash/merge"));
const createSchema_1 = require("../markdown/createSchema");
const primitives = {
    string: {
        default: () => "string",
        email: () => "user@example.com",
        date: () => "2024-07-29",
        "date-time": () => "2024-07-29T15:51:28.071Z",
        uuid: () => "3fa85f64-5717-4562-b3fc-2c963f66afa6",
        hostname: () => "example.com",
        ipv4: () => "198.51.100.42",
        ipv6: () => "2001:0db8:5b96:0000:0000:426f:8e17:642a",
    },
    number: {
        default: () => 0,
        float: () => 0.0,
    },
    integer: {
        default: () => 0,
    },
    boolean: {
        default: (schema) => typeof schema.default === "boolean" ? schema.default : true,
    },
    object: {},
    array: {},
};
function sampleResponseFromProp(name, prop, obj) {
    // Handle resolved circular props
    if (typeof prop === "object" && Object.keys(prop).length === 0) {
        obj[name] = prop;
        return obj;
    }
    // TODO: handle discriminators
    if (prop.oneOf) {
        obj[name] = (0, exports.sampleResponseFromSchema)(prop.oneOf[0]);
    }
    else if (prop.anyOf) {
        obj[name] = (0, exports.sampleResponseFromSchema)(prop.anyOf[0]);
    }
    else if (prop.allOf) {
        const mergedSchemas = (0, createSchema_1.mergeAllOf)(prop);
        sampleResponseFromProp(name, mergedSchemas, obj);
    }
    else {
        obj[name] = (0, exports.sampleResponseFromSchema)(prop);
    }
    return obj;
}
const sampleResponseFromSchema = (schema = {}) => {
    try {
        // deep copy schema before processing
        let schemaCopy = JSON.parse(JSON.stringify(schema));
        let { type, example, allOf, properties, items, oneOf, anyOf } = schemaCopy;
        if (example !== undefined) {
            return example;
        }
        if (allOf) {
            const mergedSchemas = (0, createSchema_1.mergeAllOf)(schemaCopy);
            if (mergedSchemas.properties) {
                for (const [key, value] of Object.entries(mergedSchemas.properties)) {
                    if ((value.writeOnly && value.writeOnly === true) ||
                        value.deprecated) {
                        delete mergedSchemas.properties[key];
                    }
                }
            }
            if (properties) {
                const combinedSchemas = (0, merge_1.default)(schemaCopy, mergedSchemas);
                delete combinedSchemas.allOf;
                return (0, exports.sampleResponseFromSchema)(combinedSchemas);
            }
            return (0, exports.sampleResponseFromSchema)(mergedSchemas);
        }
        if (oneOf) {
            if (properties) {
                const combinedSchemas = (0, merge_1.default)(schemaCopy, oneOf[0]);
                delete combinedSchemas.oneOf;
                return (0, exports.sampleResponseFromSchema)(combinedSchemas);
            }
            // Just go with first schema
            return (0, exports.sampleResponseFromSchema)(oneOf[0]);
        }
        if (anyOf) {
            if (properties) {
                const combinedSchemas = (0, merge_1.default)(schemaCopy, anyOf[0]);
                delete combinedSchemas.anyOf;
                return (0, exports.sampleResponseFromSchema)(combinedSchemas);
            }
            // Just go with first schema
            return (0, exports.sampleResponseFromSchema)(anyOf[0]);
        }
        if (!type) {
            if (properties) {
                type = "object";
            }
            else if (items) {
                type = "array";
            }
            else {
                return;
            }
        }
        if (type === "object") {
            let obj = {};
            for (let [name, prop] of Object.entries(properties !== null && properties !== void 0 ? properties : {})) {
                if (prop.properties) {
                    for (const [key, value] of Object.entries(prop.properties)) {
                        if ((value.writeOnly && value.writeOnly === true) ||
                            value.deprecated) {
                            delete prop.properties[key];
                        }
                    }
                }
                if (prop.items && prop.items.properties) {
                    for (const [key, value] of Object.entries(prop.items.properties)) {
                        if ((value.writeOnly && value.writeOnly === true) ||
                            value.deprecated) {
                            delete prop.items.properties[key];
                        }
                    }
                }
                if (prop.writeOnly && prop.writeOnly === true) {
                    continue;
                }
                if (prop.deprecated) {
                    continue;
                }
                // Resolve schema from prop recursively
                obj = sampleResponseFromProp(name, prop, obj);
            }
            return obj;
        }
        if (type === "array") {
            if (Array.isArray(items === null || items === void 0 ? void 0 : items.anyOf)) {
                return items === null || items === void 0 ? void 0 : items.anyOf.map((item) => (0, exports.sampleResponseFromSchema)(item));
            }
            if (Array.isArray(items === null || items === void 0 ? void 0 : items.oneOf)) {
                return items === null || items === void 0 ? void 0 : items.oneOf.map((item) => (0, exports.sampleResponseFromSchema)(item));
            }
            return [(0, exports.sampleResponseFromSchema)(items)];
        }
        if (schemaCopy.enum) {
            if (schemaCopy.default) {
                return schemaCopy.default;
            }
            return normalizeArray(schemaCopy.enum)[0];
        }
        if ((schemaCopy.writeOnly && schemaCopy.writeOnly === true) ||
            schemaCopy.deprecated) {
            return undefined;
        }
        return primitive(schemaCopy);
    }
    catch (err) {
        console.error(chalk_1.default.yellow("WARNING: failed to create example from schema object:", err));
        return;
    }
};
exports.sampleResponseFromSchema = sampleResponseFromSchema;
function primitive(schema = {}) {
    let { type, format } = schema;
    if (type === undefined) {
        return;
    }
    let fn = schema.default ? () => schema.default : primitives[type].default;
    if (format !== undefined) {
        fn = primitives[type][format] || fn;
    }
    if (fn) {
        return fn(schema);
    }
    return "Unknown Type: " + schema.type;
}
function normalizeArray(arr) {
    if (Array.isArray(arr)) {
        return arr;
    }
    return [arr];
}
