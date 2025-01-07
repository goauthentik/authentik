/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

export type Children = string | undefined | (string | undefined)[];

export type Props = Record<string, any> & { children?: Children };

export function create(tag: string, props: Props): string {
  const { children, ...rest } = props;

  let propString = "";
  for (const [key, value] of Object.entries(rest)) {
    propString += ` ${key}={${JSON.stringify(value)}}`;
  }

  return `<${tag}${propString}>${render(children)}</${tag}>`;
}

export function guard<T>(
  value: T | undefined,
  cb: (value: T) => Children
): string {
  if (value) {
    const children = cb(value);
    return render(children);
  }
  return "";
}

export function render(children: Children): string {
  const res = Array.isArray(children)
    ? children.filter((c) => c !== undefined).join("\n")
    : children ?? "";

  const isMultiline = res.split("\n").length > 1;

  // It is not possible to wrap “blocks” if text and tags are on the same line,
  // but the corresponding tags are on different lines. This can accidentally
  // happen if the rendered item has multiple lines. To be safe, we pad with
  // newlines.
  //
  // See: https://mdxjs.com/migrating/v2/#jsx
  if (isMultiline) {
    return "\n" + res + "\n";
  }

  return res;
}
