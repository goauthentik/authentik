'use strict';

var define = require('define-properties');
var getPolyfill = require('./polyfill');

module.exports = function shimArrayPrototypeMap() {
	var polyfill = getPolyfill();
	define(
		Array.prototype,
		{ filter: polyfill },
		{ filter: function () { return Array.prototype.filter !== polyfill; } }
	);
	return polyfill;
};
