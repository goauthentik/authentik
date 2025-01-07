"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.isNoIndexMetaRoute = isNoIndexMetaRoute;
// Maybe we want to add a routeConfig.metadata.noIndex instead?
// But using Helmet is more reliable for third-party plugins...
function isNoIndexMetaRoute({ head, route, }) {
    const isNoIndexMetaTag = ({ name, content, }) => {
        if (!name || !content) {
            return false;
        }
        return (
        // meta name is not case-sensitive
        name.toLowerCase() === 'robots' &&
            // Robots directives are not case-sensitive
            content.toLowerCase().includes('noindex'));
    };
    // https://github.com/staylor/react-helmet-async/pull/167
    const meta = head[route]?.meta.toComponent();
    return (meta?.some((tag) => isNoIndexMetaTag({ name: tag.props.name, content: tag.props.content })) ?? false);
}
