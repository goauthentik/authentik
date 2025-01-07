'use strict';

var callBound = require('call-bound');

var $deref = callBound('WeakRef.prototype.deref', true);

/** @type {import('.')} */
module.exports = typeof WeakRef === 'undefined'
	? function isWeakRef(_value) { // eslint-disable-line no-unused-vars
		return false;
	}
	: function isWeakRef(value) {
		if (!value || typeof value !== 'object') {
			return false;
		}
		try {
			$deref(value);
			return true;
		} catch (e) {
			return false;
		}
	};
