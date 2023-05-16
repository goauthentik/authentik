var exec = require('child_process').exec;
var pyyamlCommand = 'python ' + __dirname + '/pyyaml.py';

exports.eval = function(yamlString, callback) {
  exec(pyyamlCommand + ' "' + yamlString + '"', function(err, stdout) {
    if (err) {
      callback(err, null);
    } else {
      var jsonObj = null;
      try {
        jsonObj = JSON.parse(stdout);
      } catch (err) {
        callback(err, null);
        return;
      }
      callback(null, jsonObj);
    }
  });
}

exports.load = function(yamlFile, callback) {
  exec(pyyamlCommand + ' -f ' + yamlFile, function(err, stdout) {
    if (err) {
      callback(err, null);
    } else {
      var jsonObj = null;
      try {
        jsonObj = JSON.parse(stdout);
      } catch (err) {
        callback(err, null);
        return;
      }
      callback(null, jsonObj);
    }
  });
}

exports.dump = function(object, file, callback) {
  exec(pyyamlCommand + ' -d ' + file + ' ' + JSON.stringify(JSON.stringify(object)), callback);
}