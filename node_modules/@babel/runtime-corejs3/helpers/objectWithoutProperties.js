var _Object$getOwnPropertySymbols = require("core-js-pure/features/object/get-own-property-symbols.js");
var _includesInstanceProperty = require("core-js-pure/features/instance/includes.js");
var objectWithoutPropertiesLoose = require("./objectWithoutPropertiesLoose.js");
function _objectWithoutProperties(e, t) {
  if (null == e) return {};
  var o,
    r,
    i = objectWithoutPropertiesLoose(e, t);
  if (_Object$getOwnPropertySymbols) {
    var s = _Object$getOwnPropertySymbols(e);
    for (r = 0; r < s.length; r++) o = s[r], _includesInstanceProperty(t).call(t, o) || {}.propertyIsEnumerable.call(e, o) && (i[o] = e[o]);
  }
  return i;
}
module.exports = _objectWithoutProperties, module.exports.__esModule = true, module.exports["default"] = module.exports;