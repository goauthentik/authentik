# pupa

> Simple micro templating

Useful when all you need is to fill in some placeholders.

## Install

```
$ npm install pupa
```

## Usage

```js
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

## API

### pupa(template, data, options?)

#### template

Type: `string`

Text with placeholders for `data` properties.

#### data

Type: `object | unknown[]`

Data to interpolate into `template`.

#### options

Type: `object`

##### ignoreMissing

Type: `boolean`\
Default: `false`

By default, Pupa throws a `MissingValueError` when a placeholder resolves to `undefined`. With this option set to `true`, it simply ignores it and leaves the placeholder as is.

##### transform

Type: `((data: {value: unknown; key: string}) => unknown) | undefined` (default: `({value}) => value`)

Performs arbitrary operation for each interpolation. If the returned value was `undefined`, it behaves differently depending on the `ignoreMissing` option. Otherwise, the returned value will be interpolated into a string (and escaped when double-braced) and embedded into the template.

### MissingValueError

Exposed for instance checking.

## FAQ

### What about template literals?

Template literals expand on creation. This module expands the template on execution, which can be useful if either or both template and data are lazily created or user-supplied.

## Related

- [pupa-cli](https://github.com/sindresorhus/pupa-cli) - CLI for this module
