"use strict";

function _typeof(o) { "@babel/helpers - typeof"; return _typeof = "function" == typeof Symbol && "symbol" == typeof Symbol.iterator ? function (o) { return typeof o; } : function (o) { return o && "function" == typeof Symbol && o.constructor === Symbol && o !== Symbol.prototype ? "symbol" : typeof o; }, _typeof(o); }
Object.defineProperty(exports, "__esModule", {
  value: true
});
Object.defineProperty(exports, "patchFs", {
  enumerable: true,
  get: function get() {
    return _patchFs["default"];
  }
});
Object.defineProperty(exports, "patchRequire", {
  enumerable: true,
  get: function get() {
    return _patchRequire["default"];
  }
});
Object.defineProperty(exports, "unixify", {
  enumerable: true,
  get: function get() {
    return _correctPath.unixify;
  }
});
exports.util = void 0;
var _patchFs = _interopRequireDefault(require("./patchFs"));
var _patchRequire = _interopRequireDefault(require("./patchRequire"));
var _correctPath = require("./correctPath");
var util = _interopRequireWildcard(require("./util/lists"));
exports.util = util;
function _getRequireWildcardCache(e) { if ("function" != typeof WeakMap) return null; var r = new WeakMap(), t = new WeakMap(); return (_getRequireWildcardCache = function _getRequireWildcardCache(e) { return e ? t : r; })(e); }
function _interopRequireWildcard(e, r) { if (!r && e && e.__esModule) return e; if (null === e || "object" != _typeof(e) && "function" != typeof e) return { "default": e }; var t = _getRequireWildcardCache(r); if (t && t.has(e)) return t.get(e); var n = { __proto__: null }, a = Object.defineProperty && Object.getOwnPropertyDescriptor; for (var u in e) if ("default" !== u && {}.hasOwnProperty.call(e, u)) { var i = a ? Object.getOwnPropertyDescriptor(e, u) : null; i && (i.get || i.set) ? Object.defineProperty(n, u, i) : n[u] = e[u]; } return n["default"] = e, t && t.set(e, n), n; }
function _interopRequireDefault(obj) { return obj && obj.__esModule ? obj : { "default": obj }; }