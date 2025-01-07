export class MissingValueError extends Error {
	name: 'MissingValueError';
	message: string;
	key: string;
	constructor(key: string);
}

export type Options = {
	/**
	By default, Pupa throws a `MissingValueError` when a placeholder resolves to `undefined`. With this option set to `true`, it simply ignores it and leaves the placeholder as is.

	@default false
	*/
	ignoreMissing?: boolean;
	/**
	Performs arbitrary operation for each interpolation. If the returned value was `undefined`, it behaves differently depending on the `ignoreMissing` option. Otherwise, the returned value will be interpolated into a string (and escaped when double-braced) and embedded into the template.

	@default ({value}) => value
	*/
	transform?: (data: {value: unknown; key: string}) => unknown;
};

/**
Simple micro templating.

@param template - Text with placeholders for `data` properties.
@param data - Data to interpolate into `template`.

@example
```
import pupa from 'pupa';

pupa('The mobile number of {name} is {phone.mobile}', {
	name: 'Sindre',
	phone: {
		mobile: '609 24 363'
	}
});
//=> 'The mobile number of Sindre is 609 24 363'

pupa('I like {0} and {1}', ['🦄', '🐮']);
//=> 'I like 🦄 and 🐮'

// Double braces encodes the HTML entities to avoid code injection.
pupa('I like {{0}} and {{1}}', ['<br>🦄</br>', '<i>🐮</i>']);
//=> 'I like &lt;br&gt;🦄&lt;/br&gt; and &lt;i&gt;🐮&lt;/i&gt;'
```
*/
export default function pupa(
	template: string,
	data: unknown[] | Record<string, any>,
	options?: Options
): string;
