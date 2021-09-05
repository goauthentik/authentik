"""Enable ESM Modules for generated Web API"""
from json import loads, dumps

TSCONFIG_ESM = {
  "compilerOptions": {
    "declaration": True,
    "target": "es6",
    "module": "esnext",
    "moduleResolution": "node",
    "outDir": "./dist/esm",
    "typeRoots": [
      "node_modules/@types"
    ]
  },
  "exclude": [
    "dist",
    "node_modules"
  ]
}


with open("web-api/package.json", encoding="utf-8") as _package:
    package = loads(_package.read())
    package["license"] = "GPL-3.0-only"
    package["module"] = "./dist/esm/index.js"
    package["sideEffects"] = False
    package["scripts"]["build"] =  "tsc && tsc --project tsconfig.esm.json"

open("web-api/package.json", "w+", encoding="utf-8").write(dumps(package))
open("web-api/tsconfig.esm.json", "w+", encoding="utf-8").write(dumps(TSCONFIG_ESM))
