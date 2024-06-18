#!/usr/bin/env bash

TARGET="./node_modules/@spotlightjs/overlay/dist/index-"[0-9a-f]*.js

if [[ $(grep -L "QX2" "$TARGET" > /dev/null 2&>1) ]]; then
    patch --forward -V none --no-backup-if-mismatch -p0 $TARGET <<EOF
--- a/index-5682ce90.js	2024-06-13 16:19:28
+++ b/index-5682ce90.js	2024-06-13 16:20:23
@@ -4958,11 +4958,10 @@
     }
   );
 }
-const q2 = w.lazy(() => import("./main-3257b7fc.js").then((n) => n.m));
+const q2 = w.lazy(() => import("./main-3257b7fc.js").then((n) => n.m)), QX2 = () => {};
 function Gp({
   data: n,
-  onUpdateData: a = () => {
-  },
+  onUpdateData: a = QX2,
   editingEnabled: s = !1,
   clipboardEnabled: o = !1,
   displayDataTypes: c = !1,
EOF
fi
