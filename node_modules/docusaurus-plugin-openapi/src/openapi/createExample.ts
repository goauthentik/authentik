/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { SchemaObject } from "./types";

interface OASTypeToTypeMap {
  string: string;
  number: number;
  integer: number;
  boolean: boolean;
  object: any;
  array: any[];
}

type Primitives = {
  [OASType in keyof OASTypeToTypeMap]: {
    [format: string]: (schema: SchemaObject) => OASTypeToTypeMap[OASType];
  };
};

const primitives: Primitives = {
  string: {
    default: () => "string",
    email: () => "user@example.com",
    date: () => new Date().toISOString().substring(0, 10),
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
    default: (schema) =>
      typeof schema.default === "boolean" ? schema.default : true,
  },
  object: {},
  array: {},
};

export const sampleFromSchema = (schema: SchemaObject = {}): any => {
  let { type, example, allOf, properties, items } = schema;

  if (example !== undefined) {
    return example;
  }

  if (allOf) {
    // TODO: We are just assuming it will always be an object for now
    let obj: SchemaObject = {
      type: "object",
      properties: {},
      required: [], // NOTE: We shouldn't need to worry about required
    };
    for (let item of allOf) {
      if (item.properties) {
        obj.properties = {
          ...obj.properties,
          ...item.properties,
        };
      }
    }
    return sampleFromSchema(obj);
  }

  if (!type) {
    if (properties) {
      type = "object";
    } else if (items) {
      type = "array";
    } else {
      return;
    }
  }

  if (type === "object") {
    let obj: any = {};
    for (let [name, prop] of Object.entries(properties ?? {})) {
      if (prop.deprecated) {
        continue;
      }
      obj[name] = sampleFromSchema(prop);
    }
    return obj;
  }

  if (type === "array") {
    if (Array.isArray(items?.anyOf)) {
      return items?.anyOf.map((item) => sampleFromSchema(item));
    }

    if (Array.isArray(items?.oneOf)) {
      return items?.oneOf.map((item) => sampleFromSchema(item));
    }

    return [sampleFromSchema(items)];
  }

  if (schema.enum) {
    if (schema.default) {
      return schema.default;
    }
    return normalizeArray(schema.enum)[0];
  }

  return primitive(schema);
};

function primitive(schema: SchemaObject = {}) {
  let { type, format } = schema;

  if (type === undefined) {
    return;
  }

  let fn = primitives[type].default;

  if (format !== undefined) {
    fn = primitives[type][format] || fn;
  }

  if (fn) {
    return fn(schema);
  }

  return "Unknown Type: " + schema.type;
}

function normalizeArray(arr: any) {
  if (Array.isArray(arr)) {
    return arr;
  }
  return [arr];
}
