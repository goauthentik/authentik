package web

import _ "embed"

//go:embed robots.txt
var RobotsTxt []byte

//go:embed security.txt
var SecurityTxt []byte
