'use strict';

var filter = require('../');
var test = require('tape');
var runTests = require('./tests');

test('as a function', function (t) {
	t.test('bad array/this value', function (st) {
		st['throws'](function () { filter(undefined, 'a'); }, TypeError, 'undefined is not an object');
		st['throws'](function () { filter(null, 'a'); }, TypeError, 'null is not an object');
		st.end();
	});

	runTests(filter, t);

	t.end();
});
