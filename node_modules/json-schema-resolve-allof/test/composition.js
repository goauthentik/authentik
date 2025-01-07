var expect = require('chai').expect;
var should = require('chai').should();
var refParser = require('json-schema-ref-parser');

var resolveAllOf = require('../index.js');


function resolve(obj){
  return refParser.dereference(obj).then(spec => resolveAllOf(spec));
}

describe('swagger.js resolver tests', function () {

  it('resolves a model with composition', function (done) {
    var spec = {
      definitions: {
        Animal : {
          type: 'object',
          required: [ 'name' ],
          properties : {
            name : {
              type : 'string'
            },
            type : {
              type : 'string'
            }
          },
          discriminator : 'type'
        },
        Human : {
          allOf : [ {
            type: 'object',
            properties : {
              firstName : {
                type : 'string'
              },
              lastName : {
                type : 'string'
              }
            }
          },
          {
            $ref : '#/definitions/Animal'
          } ],
          example: 'this is example'
        },
        Pet : {
          allOf : [ {
            $ref : '#/definitions/Animal'
          }, {
            type: 'object',
            required : [ 'isDomestic', 'name', 'type' ],
            properties : {
              isDomestic : {
                type : 'boolean',
                default : false
              }
            }
          } ]
        },
        Monster: {
          description: 'useful information',
          allOf : [
            {
              $ref: '#/definitions/Ghoul'
            }, {
              $ref: '#/definitions/Pet'
            }, {
              properties: {
                hasScales: {
                  type: 'boolean'
                }
              }
            }
          ]
        },
        Ghoul: {
          description: 'a ghoul',
          required: [ 'fangs' ],
          properties: {
            fangs: {
              type: 'integer',
              format: 'int32'
            }
          }
        }
      }
    };

    resolve(spec).then(function (spec) {
      // test.object(spec.definitions.Monster);
      var properties = spec.definitions.Monster.properties;
      expect(properties.name).to.be.an('object');
      expect(properties.type).to.be.an('object');
      expect(properties.isDomestic).to.be.an('object');
      expect(properties.fangs).to.be.an('object');
      expect(properties.hasScales).to.be.an('object');

      expect(properties.firstName).to.be.an('undefined');
      expect(properties.lastName).to.be.an('undefined');
      expect(properties.definitions).to.be.an('undefined');

      expect(spec.definitions.Human.example).to.equal('this is example');
      expect(spec.definitions.Ghoul.description).to.equal('a ghoul');
      expect(spec.definitions.Monster.description).to.equal('useful information');

      done();
    })
    .catch(done);
  });

  it('resolves a model with composition 2', function (done) {
    var spec = {
      definitions: {
        Pet: {
          discriminator: 'petType',
          properties: {
            name: {
              type: 'string'
            },
            petType: {
              type: 'string'
            }
          },
          required: [
            'name',
            'petType'
          ]
        },
        Cat: {
          description: 'A representation of a cat',
          allOf: [
            {
              $ref: '#/definitions/Pet'
            },
            {
              properties: {
                petType: {
                  type: 'string',
                  enum: [ 'cat' ]
                },
                huntingSkill: {
                  type: 'string',
                  description: 'The measured skill for hunting',
                  default: 'lazy',
                  enum: [
                    'clueless',
                    'lazy',
                    'adventurous',
                    'aggressive'
                  ]
                }
              },
              required: [
                'huntingSkill'
              ]
            }
          ]
        },
        Dog: {
          description: 'A representation of a dog',
          allOf: [
            {
              $ref: '#/definitions/Pet'
            },
            {
              properties: {
                petType: {
                  type: 'string',
                  enum: [ 'dog' ]
                },                
                packSize: {
                  type: 'integer',
                  format: 'int32',
                  description: 'the size of the pack the dog is from',
                  default: 0,
                  minimum: 0
                }
              },
              required: [
                'packSize'
              ]
            }
          ]
        },
        Fish: {
          description: 'A representation of a fish',
          allOf: [
            {
              $ref: '#/definitions/Pet'
            },
            {
              properties: {
                petType: {
                  type: 'string',
                  enum: [ 'fish' ]
                },                
                fins: {
                  type: 'integer',
                  format: 'int32',
                  description: 'count of fins',
                  minimum: 0
                }
              },
              required: [
                'fins'
              ]
            }
          ]
        }
      }
    };

    resolve(spec).then(function (spec2) {
      expect(spec2).to.be.an('object');
      done();
    }).catch(done);
  });

  it('resolves a model with a composed response array', function (done) {
    var spec = {
      paths: {
        '/test': {
          get: {
            responses: {
              200: {
                schema: {
                  type: 'array',
                  items: {
                    $ref: '#/definitions/Response'
                  }
                }
              }
            }
          }
        }
      },
      definitions: {
        Request: {
        properties: {
          name: {
            type: 'string'
          }
        }
      },
      Response: {
        allOf: [
          {
            $ref: '#/definitions/Request'
          },
          {
            properties: {
              id: {
                description: 'ID of entry',
                type: 'integer',
                format: 'int32'
              }
            }
          }
        ]
        }
      }
    };

    resolve(spec).then(function (spec2) {
      expect(spec2).to.be.an('object');
      done();
    }).catch(done);
  });

  it('tests issue #567', function (done) {
    var input = {
      definitions: {
        'Pet': {
          discriminator: 'type',
          required: [
            'type'
          ],
          properties: {
            hasFur: {
              type: 'boolean'
            },
            limbCount: {
              type: 'integer',
              format: 'int32'
            },
            eatsMeat: {
              type: 'boolean'
            },
            eatsPeople: {
              type: 'boolean'
            }
          }
        },
        'Cat': {
          properties: {
            commonName: {
              type: 'string',
              example: 'Abyssinian'
            }
          }
        },
        'Dog': {
          properties: {
            barks: {
              type: 'boolean'
            },
            slobberFactor: {
              type: 'integer',
              format: 'int32'
            }
          }
        }
      }
    };
    resolve(input).then(function (spec2) {
      expect(spec2).to.be.an('object');
      var pet = spec2.definitions.Pet;
      expect(pet).to.be.an('object');
      expect(pet.discriminator).to.be.a('string');
      done();
    }).catch(done);
  });

  it('tests issue #459', function (done) {
    var input = {
      definitions: {
        'new_model': {
          properties: {
            subclass: {
              allOf: [
                {
                  $ref: '#/definitions/superclass'
                },
                {
                  properties: {
                    name: {
                      type: 'string'
                    }
                  }
                }
              ]
            }
          }
        },
        superclass: {
          properties: {
            id: {
              format: 'int32',
              type: 'integer'
            }
          }
        }
      }
    };

    resolve(input).then(function (spec) {

      expect(spec).to.be.an('object');
      var schema = spec.definitions.new_model.properties.subclass;

      expect(Object.keys(schema.properties).length).to.equal(2);

      var id = schema.properties.id;
      expect(id.type).to.equal('integer');
      expect(id.format).to.equal('int32');

      var name = schema.properties.name;
      expect(name.type).to.equal('string');

      done();
    }).catch(done);
  });
  
});