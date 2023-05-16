# Node-pyyaml

Robust YAML parser and dumper for Node.js using [PyYAML] (http://pyyaml.org/) bindings:
convert a YAML string into a JS object, load a YAML file in a JS object, dump a JS object in a YAML file.

To see how YAML will be parsed into JSON, check out the great [Online YAML Parser] (http://yaml-online-parser.appspot.com/).  

# Installation

    npm install pyyaml


# Usage

    pyyaml.eval(yamlString, callback): parse a YAML string into a JS object
    pyyaml.load(yamlFile, callback): load a YAML file in a JS object
    pyyaml.dump(jsObject, yamlFile, callback): dump a JS object in a YAML file


# Example

    var pyyaml = require('pyyaml');

    //Eval a YAML string
    pyyaml.eval('I like: {using: YAML, for: config files}', function(err, jsObject) {
      if (err) throw err;
      console.log('eval successful: ' + JSON.stringify(jsObject));  
    });

    //Load a YAML file
    pyyaml.load('file.yml', function(err, jsObject) {
      if (err) throw err;
      console.log('load successful: ' + JSON.stringify(jsObject));  
    });

    //Dump a JS object in a YAML file
    pyyaml.dump({use: 'pyyaml', when: 'you want to parse', your: 'YAML files'}, 'file.yml', function(err) {      
      console.log(err ? 'dump failed' : 'dump successful: go check file.yml');      
    });
    

# MIT License 

Copyright (c) 2011 Jie Meng-Gerard <contact@jie.fr>

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
'Software'), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.