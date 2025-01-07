/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

import { SchemaObject } from "../openapi/types";

function prettyName(schema: SchemaObject, circular?: boolean) {
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
    return schema.xml?.name ?? schema.type;
  }

  return schema.title ?? schema.type;
}

export function getSchemaName(
  schema: SchemaObject,
  circular?: boolean
): string {
  if (schema.items) {
    return prettyName(schema.items, circular) + "[]";
  }

  return prettyName(schema, circular) ?? "";
}

export function getQualifierMessage(schema?: SchemaObject): string | undefined {
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

  if (
    schema.minimum ||
    schema.maximum ||
    typeof schema.exclusiveMinimum === "number" ||
    typeof schema.exclusiveMaximum === "number"
  ) {
    let minmaxQualifier = "";
    if (typeof schema.exclusiveMinimum === "number") {
      minmaxQualifier += `${schema.exclusiveMinimum} < `;
    } else if (schema.minimum && !schema.exclusiveMinimum) {
      minmaxQualifier += `${schema.minimum} ≤ `;
    } else if (schema.minimum && schema.exclusiveMinimum === true) {
      minmaxQualifier += `${schema.minimum} < `;
    }
    minmaxQualifier += "value";
    if (typeof schema.exclusiveMaximum === "number") {
      minmaxQualifier += ` < ${schema.exclusiveMaximum}`;
    } else if (schema.maximum && !schema.exclusiveMaximum) {
      minmaxQualifier += ` ≤ ${schema.maximum}`;
    } else if (schema.maximum && schema.exclusiveMaximum === true) {
      minmaxQualifier += ` < ${schema.maximum}`;
    }
    qualifierGroups.push(minmaxQualifier);
  }

  if (schema.pattern) {
    qualifierGroups.push(
      `Value must match regular expression \`${schema.pattern}\``
    );
  }

  if (schema.enum) {
    qualifierGroups.push(`[${schema.enum.map((e) => `\`${e}\``).join(", ")}]`);
  }

  if (qualifierGroups.length === 0) {
    return undefined;
  }

  return message + qualifierGroups.join(", ");
}
