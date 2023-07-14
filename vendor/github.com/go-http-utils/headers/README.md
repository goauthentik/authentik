# headers
[![Build Status](https://travis-ci.org/go-http-utils/headers.svg?branch=master)](https://travis-ci.org/go-http-utils/headers)
[![Coverage Status](https://coveralls.io/repos/github/go-http-utils/headers/badge.svg?branch=master)](https://coveralls.io/github/go-http-utils/headers?branch=master)

HTTP header constants for Gophers.

## Installation

```sh
go get -u github.com/go-http-utils/headers
```

## Documentation

https://godoc.org/github.com/go-http-utils/headers

## Usage

```go
import (
  "fmt"

  "github.com/go-http-utils/headers"
)

fmt.Println(headers.AcceptCharset)
// -> "Accept-Charset"

fmt.Println(headers.IfNoneMatch)
// -> "If-None-Match"

fmt.Println(headers.Normalize("content-type"))
// -> "Content-Type"
```
