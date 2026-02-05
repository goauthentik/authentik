/**
 * @file Common utility types.
 */

/**
 * Type utility to make all properties in T recursively optional.
 */
export type DeepPartial<T> = T extends object
    ? {
          [P in keyof T]?: DeepPartial<T[P]>;
      }
    : T;

/**
 * Type utility to make readonly properties mutable.
 */
export type Writeable<T> = { -readonly [P in keyof T]: T[P] };

/**
 * Utility type to get the writable keys of an object.
 */
export type WritableKeys<T> = {
    [K in keyof T]-?: IfEquals<{ [Q in K]: T[K] }, { -readonly [Q in K]: T[K] }, K, never>;
}[keyof T];

/**
 * Utility type to compare if two types are equal.
 */
export type IfEquals<X, Y, A = X, B = never> =
    (<T>() => T extends X ? 1 : 2) extends <T>() => T extends Y ? 1 : 2 ? A : B;

/**
 * Utility type to get the keys of an object that are not in the base type.
 */
export type OwnKeys<Target, Base> = Exclude<keyof Target, keyof Base>;

/**
 * Utility type to represent the properties of an object that are not in the base type.
 */
export type OwnPropertyRecord<Target, Base> = {
    [K in OwnKeys<Target, Base> as K extends WritableKeys<Target> ? K : never]: Target[K];
};
