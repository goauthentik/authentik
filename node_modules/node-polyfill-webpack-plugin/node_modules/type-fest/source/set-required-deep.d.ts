import type {NonRecursiveType, StringToNumber} from './internal';
import type {Paths} from './paths';
import type {SimplifyDeep} from './simplify-deep';
import type {UnknownArray} from './unknown-array';

/**
Create a type that makes the given keys required. You can specify deeply nested key paths. The remaining keys are kept as is.

Use-case: Selectively make nested properties required in complex types like models.

@example
```
import type {SetRequiredDeep} from 'type-fest';

type Foo = {
	a?: number;
	b?: string;
	c?: {
		d?: number
	}[]
}

type SomeRequiredDeep = SetRequiredDeep<Foo, 'a' | `c.${number}.d`>;
// type SomeRequiredDeep = {
// 	a: number; // Is now required
// 	b?: string;
// 	c: {
// 		d: number // Is now required
// 	}[]
// }
```

@category Object
*/
export type SetRequiredDeep<BaseType, KeyPaths extends Paths<BaseType>> =
BaseType extends NonRecursiveType
	? BaseType
	: SimplifyDeep<(
		BaseType extends UnknownArray
			? {}
			: {[K in keyof BaseType as K extends (KeyPaths | StringToNumber<KeyPaths & string>) ? K : never]-?: BaseType[K]}
	) & {
		[K in keyof BaseType]: Extract<KeyPaths, `${K & (string | number)}.${string}`> extends never
			? BaseType[K]
			: SetRequiredDeep<BaseType[K], KeyPaths extends `${K & (string | number)}.${infer Rest extends Paths<BaseType[K]>}` ? Rest : never>
	}>;
