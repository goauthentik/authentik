type RemoveFromTuple<
  Tuple extends unknown[],
  RemoveCount extends number,
  Index extends 1[] = []
> = Index["length"] extends RemoveCount
  ? Tuple
  : Tuple extends [first: unknown, ...infer Rest]
  ? RemoveFromTuple<Rest, RemoveCount, [...Index, 1]>
  : Tuple;

type ConcatTuples<
  Prefix extends unknown[],
  Suffix extends unknown[]
> = [...Prefix, ...Suffix];

type ReplaceThis<T, NewThis> = T extends (this: infer OldThis, ...args: infer A) => infer R
  ? (this: NewThis, ...args: A) => R
  : never;

type BindFunction<
  TThis,
  T extends (this: TThis, ...args: any[]) => any, // Allow specific types to propagate
  TBoundArgs extends unknown[],
  ReceiverBound extends boolean
> = ReceiverBound extends true
  ? (...args: RemoveFromTuple<Parameters<T>, TBoundArgs["length"] & number>) => ReturnType<ReplaceThis<T, TThis>>
  : (...args: ConcatTuples<[TThis], RemoveFromTuple<Parameters<T>, TBoundArgs["length"] & number>>) => ReturnType<T>;

declare function callBind<
  TThis,
  T extends (this: TThis, ...args: any[]) => any,
  TBoundArgs extends Partial<Parameters<T>>
>(
  args: [fn: T, thisArg: TThis, ...boundArgs: TBoundArgs]
): BindFunction<TThis, T, TBoundArgs, true>;

declare function callBind<
  TThis,
  T extends (this: TThis, ...args: any[]) => any,
  TBoundArgs extends Partial<Parameters<T>>
>(
  args: [fn: T, ...boundArgs: TBoundArgs]
): BindFunction<TThis, T, TBoundArgs, false>;

export as namespace callBind;
export = callBind;
