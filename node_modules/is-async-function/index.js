'use strict';

var callBound = require('call-bound');
var safeRegexTest = require('safe-regex-test');

var toStr = callBound('Object.prototype.toString');
var fnToStr = callBound('Function.prototype.toString');
var isFnRegex = safeRegexTest(/^\s*async(?:\s+function(?:\s+|\()|\s*\()/);

var hasToStringTag = require('has-tostringtag/shams')();
var getProto = require('get-proto');

var getAsyncFunc = function () { // eslint-disable-line consistent-return
	if (!hasToStringTag) {
		return false;
	}
	try {
		return Function('return async function () {}')();
	} catch (e) {
	}
};

/** @type {import('.').AsyncFunction | false} */
var AsyncFunction;

/** @type {import('.')} */
module.exports = function isAsyncFunction(fn) {
	if (typeof fn !== 'function') {
		return false;
	}
	if (isFnRegex(fnToStr(fn))) {
		return true;
	}
	if (!hasToStringTag) {
		var str = toStr(fn);
		return str === '[object AsyncFunction]';
	}
	if (!getProto) {
		return false;
	}
	if (typeof AsyncFunction === 'undefined') {
		var asyncFunc = getAsyncFunc();
		// eslint-disable-next-line no-extra-parens
		AsyncFunction = asyncFunc ? /** @type {import('.').AsyncFunction} */ (getProto(asyncFunc)) : false;
	}
	return getProto(fn) === AsyncFunction;
};
