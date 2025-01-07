"use strict";
/* ============================================================================
 * Copyright (c) Cloud Annotations
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.isURL = void 0;
const isURL = (url) => {
    return /^(?:[a-z]+:)?\/\//i.test(url);
};
exports.isURL = isURL;
