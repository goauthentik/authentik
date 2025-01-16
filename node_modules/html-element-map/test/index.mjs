import * as Module from 'html-element-map';
import test from 'tape';

test('named exports', async (t) => {
	t.deepEqual(
		Object.keys(Module).sort(),
		['byTag', 'byConstructor', 'byConstructorName'].sort(),
		'has expected named exports',
	);

	const { byTag, byConstructor, byConstructorName } = Module;
	t.equal(await import('html-element-map/byTag'), byTag, 'byTag named export matches deep export');
	t.equal(await import('html-element-map/byConstructor'), byConstructor, 'byConstructor named export matches deep export');
	t.equal(await import('html-element-map/byConstructorName'), byConstructorName, 'byConstructorName named export matches deep export');

	t.end();
});
