/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */

export const isURL = (url: string) => {
  return /^(?:[a-z]+:)?\/\//i.test(url);
};
