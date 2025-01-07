"use strict";
/* ============================================================================
 * Copyright (c) Palo Alto Networks
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 * ========================================================================== */
Object.defineProperty(exports, "__esModule", { value: true });
exports.createDescription = void 0;
function createDescription(description) {
    if (!description) {
        return "";
    }
    return `\n\n${description}\n\n`;
}
exports.createDescription = createDescription;
