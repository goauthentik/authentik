// The converter works entirely by positional keys, and in most cases that works just fine. In the
// rare case where named tokens are used, supply the actual source string as the alternative. These
// strings can be identified in your original `.po` source files by:
//
// grep '{[a-z]' <PO file>
//

export const specialCases = new Map([
    ["{0} day(s) ago", "{ago} day(s) ago"],
    ["{0} days ago", "{ago} days ago"],
    ["{0} hour(s) ago", "{ago} hour(s) ago"],
    ["Welcome, {0}.", "Welcome, {name}."],
]);

export default specialCases;
