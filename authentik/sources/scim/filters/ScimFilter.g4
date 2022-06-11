grammar ScimFilter;

parse
    : filter
    ;

filter
	: attrPath SP PR                             #presentExp
	| attrPath SP COMPAREOPERATOR SP VALUE       #operatorExp
	| NOT? SP* '(' filter ')'                    #braceExp
	| attrPath '[' valPathFilter ']'             #valPathExp
	| filter SP AND SP filter                    #andExp
	| filter SP OR SP filter                     #orExp
	;										     
											     
valPathFilter								     
	: attrPath SP PR                             #valPathPresentExp
	| attrPath SP COMPAREOPERATOR SP VALUE       #valPathOperatorExp
	| NOT? SP* '(' valPathFilter ')'             #valPathBraceExp
	| valPathFilter SP AND SP valPathFilter      #valPathAndExp
	| valPathFilter SP OR SP valPathFilter       #valPathOrExp
	;
	
attrPath 
	: (SCHEMA)? ATTRNAME ('.' ATTRNAME)?
	;

COMPAREOPERATOR : EQ | NE | CO | SW | EW | GT | GE | LT | LE;

EQ : [eE][qQ];
NE : [nN][eE];
CO : [cC][oO];
SW : [sS][wW];
EW : [eE][wW];
PR : [pP][rR];
GT : [gG][tT];
GE : [gG][eE];
LT : [lL][tT];
LE : [lL][eE];

NOT : [nN][oO][tT];
AND : [aA][nN][dD];
OR  : [oO][rR];

SP : ' ';

SCHEMA : 'urn:' (SEGMENT ':')+;

ATTRNAME : ALPHA (ALPHA | DIGIT | '_' | '-')+;

fragment SEGMENT : (ALPHA | DIGIT | '_' | '-' | '.')+;

fragment DIGIT : [0-9];

fragment ALPHA : [a-z] | [A-Z];

ESCAPED_QUOTE : '\\"';

VALUE : '"'(ESCAPED_QUOTE | ~'"')*'"' | 'true' | 'false' | 'null' | DIGIT+('.'DIGIT+)?;

EXCLUDE : [\b | \t | \r | \n]+ -> skip;
