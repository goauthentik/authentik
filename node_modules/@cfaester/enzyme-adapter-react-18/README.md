[![npm](https://img.shields.io/npm/v/@cfaester/enzyme-adapter-react-18.svg)](https://www.npmjs.com/package/@cfaester/enzyme-adapter-react-18)

# @cfaester/enzyme-adapter-react-18

A **very** unofficial adapter for React 18 for [Enzyme](https://enzymejs.github.io/enzyme/).

Should you count on it? Probably not. Can you use it as a reference for your own work? Perhaps.

## Installation

```
npm install --save-dev @cfaester/enzyme-adapter-react-18
```

## Configuration

You need to add it to Enzyme configuration. This is actually pretty easy. Just import it.

```js
import Enzyme from 'enzyme';
import Adapter from '@cfaester/enzyme-adapter-react-18';

Enzyme.configure({ adapter: new Adapter() });
```

I have personally had a few issues with tests using `simulate` on a mounted component. Specifically when using form libraries. To alleviate this, wrap your `simulate` calls in `act()`, like so:

```js
await act(() => {
	mountWrapper.find('form').simulate('submit');
});
```

## Motivation and thanks
This is not the best code I've ever written, but sometimes ripping out 900 tests, or going through hoops by running some tests under React 17 (can you really trust that anyway?), is just not feasible if you want the cool suspense features in, or dependencies depending on React 18.

This package can serve as a halfway stop towards migrating your tests to a newer framework like [@testing-library/react](https://www.npmjs.com/package/@testing-library/react), or to keep some of your shallow tests working.

I don't have much plan of spending a lot of time maintaining this package. But after some deliberation, I'd rather open source it, than sit on it. If nothing else, it can serve as a reference point for your own implementation.

This couldn't be possible without the work of [wojtekmaj](https://github.com/wojtekmaj), and his React 17 adapter. I think you should consider sponsoring him for his other projects as well.
