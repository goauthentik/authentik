package web

import "embed"

//go:embed dist/*
var StaticDist embed.FS

//go:embed authentik
var StaticAuthentik embed.FS

//go:embed dist/if/flow/index.html
var InterfaceFlow []byte

//go:embed dist/if/admin/index.html
var InterfaceAdmin []byte

//go:embed robots.txt
var RobotsTxt []byte

//go:embed security.txt
var SecurityTxt []byte
