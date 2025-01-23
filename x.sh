#!/bin/bash

# Directory containing the markdown files
DIR="website/integrations/services"

# Loop through all markdown files in the specified directory and subdirectories
find "$DIR" -type f -name "*.md" | while read -r file; do
    # Use sed to update the header line in place
    sed -i -E 's/^(# )(.*)/\1Integrate with \2/' "$file"
done

echo "Headers updated in all markdown files in $DIR"
