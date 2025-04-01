/**
 * Type guard to ensure that a value is unreachable.
 *
 * Use this to allow TypeScript to infer that a switch statement is exhaustive.
 *
 * ```ts
 * type MyType = "a" | "b";
 *
 * function doSomething(value: MyType) {
 *     switch (value) {
 *         case "a":
 *             return "A";
 *     }
 *
 *     assertUnreachable(value);
 * }
 *```
 */
export function assertUnreachable(_unreachableValue: never): never {
    throw new TypeError("Compile-time check failed: This code should not be reachable");
}
