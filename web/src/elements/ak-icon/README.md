This element exists to regularize our use of icons. It is not normally componentized in the
Patternfly ecosystem.

## Analysis

Aside from regularizing the size and default behavior of icons in our system, almost all of the
functionality is pure CSS: once the font family has been chosen, the size, colors, orientation and
animations of the icon derive from setting CSS properties on the icon itself.

The Fontawesome and Patternfly Icon CSS has therefore been modified to respond to changes in the
`:host` setting, so that simple attributes describe how the icon should look and behave. Placement
of the icon itself is entirely up to the client.

Providing convenience names for our most frequently used icons is just that, a convenience. It's a
nice convenience, but that's what it is.
