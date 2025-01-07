"use strict";
var _ = require("lodash");
function resolveAllOf(inputSpec) {
    if (inputSpec && typeof inputSpec === 'object') {
        if (Object.keys(inputSpec).length > 0) {
            if (inputSpec.allOf) {
                var allOf = inputSpec.allOf;
                delete inputSpec.allOf;
                var nested = _.mergeWith.apply(_, [{}].concat(allOf, [customizer]));
                inputSpec = _.defaultsDeep(inputSpec, nested, customizer);
            }
            Object.keys(inputSpec).forEach(function (key) {
                inputSpec[key] = resolveAllOf(inputSpec[key]);
            });
        }
    }
    return inputSpec;
}
var customizer = function (objValue, srcValue) {
    if (_.isArray(objValue)) {
        return _.union(objValue, srcValue);
    }
    return;
};
module.exports = resolveAllOf;
//# sourceMappingURL=index.js.map