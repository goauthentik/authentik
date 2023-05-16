import yaml, json, sys

if sys.argv[1] == '-f':
  print json.dumps(yaml.safe_load(file(sys.argv[2], 'r')));
elif sys.argv[1] == '-d':  
  print yaml.dump(yaml.safe_load(sys.argv[3]), file(sys.argv[2], 'w'), indent=2, default_flow_style=False)
else:
  print json.dumps(yaml.safe_load(sys.argv[1]));