#!/usr/bin/env bash

TARGET="./node_modules/@custom-elements-manifest/analyzer/src/features/analyse-phase/creators/handlers.js"

# If the second question mark is not there in this test, put it there. The flags to grep ensure it
# will behave correctly on both MacOS and Linux by requiring it to use only the POSIX "basic"
# regular expression behavior.
#

if ! grep -GL 'node\.name?\.text?\.startsWith' "$TARGET" > /dev/null 2>&1; then
patch --forward -V none --no-backup-if-mismatch -p0 $TARGET <<EOF
--- a/packages/analyzer/src/features/analyse-phase/creators/handlers.js
+++ b/packages/analyzer/src/features/analyse-phase/creators/handlers.js
@@ -34,7 +34,7 @@ export function handleModifiers(doc, node) {
     }
   });
 
-  if (node.name?.text.startsWith('#')) {
+  if (node.name?.text?.startsWith('#')) {
     doc.privacy = 'private';
   }
EOF
fi
