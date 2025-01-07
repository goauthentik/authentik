require('chai').should();

var refParser = require('json-schema-ref-parser');
var requireYaml = (file) => require('js-yaml').safeLoad(require('fs').readFileSync(require('path').resolve(__dirname, file), 'utf8'));

var resolveAllOf = require('../index');

describe('JSON schema resolve allof', function() {

  
  describe('Primitives', function(){  
    it('should work on primitives', function(){
        resolveAllOf("foo").should.equal("foo");
        resolveAllOf(4).should.equal(4);
        resolveAllOf(3.14159).should.equal(3.14159);
        
        resolveAllOf(undefined);
        resolveAllOf(null);
    });
  });
  
  describe('Arrays', function(){
      it('should work on arrays', function(){
          resolveAllOf([1]).should.deep.equal([1]);
          resolveAllOf(["foo"]).should.deep.equal(["foo"]);
      });
      it('should work on empty arrays', function(){
          resolveAllOf([]).should.deep.equal([]);
      });
  });

  describe('Objects', function(){
      it('should work on empty objects', function(){
          resolveAllOf({}).should.deep.equal({});
      });
      it('should work on simple objects', function(){
          resolveAllOf({foo:"bar"}).should.deep.equal({foo:"bar"});
      });
      it('should work on null field objects', function(){
          resolveAllOf({foo:undefined}).should.deep.equal({foo:undefined});
          
          var case2 = {foo:[]};
          delete case2.foo;
          resolveAllOf(case2).should.deep.equal({});

          var case3 = {foo:{}};
          delete case3.foo;
          resolveAllOf(case3).should.deep.equal({});
          
          var case4 = {foo:{}};
          case4.foo = undefined;
          resolveAllOf(case4).should.deep.equal({foo:undefined});
          
          var case5 = {foo:{}};
          case5.foo = null;
          resolveAllOf(case5).should.deep.equal({foo:null});

      });
  });
 
  describe('Composition', function(){
      it('should work on simple composition', function(){
          importedTestCase('./simpleComposition','./simpleComposition-expected');
      });
      
      it('should work on simple composition and complex parsing', function(done){
          importedComplexTestCase('./simpleComposition','./simpleComposition-expected', done);
      });
      
      it('should work with crazy nested composition', function(done){
          importedComplexTestCase('./nestedRefs','./nestedRefs-expected', done);
      });

      it('should work with a full Swagger spec', function(done){
          importedComplexYamlTestCase('./swagger.yaml','./swagger-expected.yaml', done);
      });
      
      
  });

  
});

function importedTestCase(input, expected){
  var inputobj = require(input);
  var expectedobj = require(expected);
  resolveAllOf(inputobj).should.deep.equal(expectedobj);    
}

function importedComplexTestCase(input, expected, done){
  var inputobj = require(input);
  var expectedobj = require(expected);
  
  refParser.dereference(inputobj)
  .then(function(schema) {
    resolveAllOf(schema).should.deep.equal(expectedobj);
    done();
  })
  .catch(done);
}

function importedComplexYamlTestCase(input, expected, done){
  var inputobj = requireYaml(input);
  var expectedobj = requireYaml(expected);
  
  refParser.dereference(inputobj)
  .then(function(schema) {
    resolveAllOf(schema).should.deep.equal(expectedobj);
    done();
  })
  .catch(done);
}