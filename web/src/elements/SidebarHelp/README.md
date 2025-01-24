The SidebarHelp feature uses some fairly fiddly CSS to rotate the "Documentation" button in a way
that doesn't take up too much screen real-estate, because the rotation is purely visual; the layout
flow is still driven by the size of the button as if it were horizontal. Using the SidebarHelp means
enabling a special controller to adjust the width of the container to the _height_ of the button
when the button is rotated into place.
