"use strict";
/**
 * Copyright (c) Facebook, Inc. and its affiliates.
 *
 * This source code is licensed under the MIT license found in the
 * LICENSE file in the root directory of this source tree.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.Schema = exports.DEFAULT_CONFIG = void 0;
exports.validateThemeConfig = validateThemeConfig;
const utils_1 = require("@docusaurus/utils");
const utils_validation_1 = require("@docusaurus/utils-validation");
exports.DEFAULT_CONFIG = {
    // Enabled by default, as it makes sense in most cases
    // see also https://github.com/facebook/docusaurus/issues/5880
    contextualSearch: true,
    searchParameters: {},
    searchPagePath: 'search',
};
exports.Schema = utils_validation_1.Joi.object({
    algolia: utils_validation_1.Joi.object({
        // Docusaurus attributes
        contextualSearch: utils_validation_1.Joi.boolean().default(exports.DEFAULT_CONFIG.contextualSearch),
        externalUrlRegex: utils_validation_1.Joi.string().optional(),
        // Algolia attributes
        appId: utils_validation_1.Joi.string().required().messages({
            'any.required': '"algolia.appId" is required. If you haven\'t migrated to the new DocSearch infra, please refer to the blog post for instructions: https://docusaurus.io/blog/2021/11/21/algolia-docsearch-migration',
        }),
        apiKey: utils_validation_1.Joi.string().required(),
        indexName: utils_validation_1.Joi.string().required(),
        searchParameters: utils_validation_1.Joi.object()
            .default(exports.DEFAULT_CONFIG.searchParameters)
            .unknown(),
        searchPagePath: utils_validation_1.Joi.alternatives()
            .try(utils_validation_1.Joi.boolean().invalid(true), utils_validation_1.Joi.string())
            .allow(null)
            .default(exports.DEFAULT_CONFIG.searchPagePath),
        replaceSearchResultPathname: utils_validation_1.Joi.object({
            from: utils_validation_1.Joi.custom((from) => {
                if (typeof from === 'string') {
                    return (0, utils_1.escapeRegexp)(from);
                }
                else if (from instanceof RegExp) {
                    return from.source;
                }
                throw new Error(`it should be a RegExp or a string, but received ${from}`);
            }).required(),
            to: utils_validation_1.Joi.string().required(),
        }).optional(),
    })
        .label('themeConfig.algolia')
        .required()
        .unknown(), // DocSearch 3 is still alpha: don't validate the rest for now
});
function validateThemeConfig({ validate, themeConfig, }) {
    return validate(exports.Schema, themeConfig);
}
