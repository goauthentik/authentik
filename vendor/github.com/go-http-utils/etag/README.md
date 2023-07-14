# etag
[![Build Status](https://travis-ci.org/go-http-utils/etag.svg?branch=master)](https://travis-ci.org/go-http-utils/etag)
[![Coverage Status](https://coveralls.io/repos/github/go-http-utils/etag/badge.svg?branch=master)](https://coveralls.io/github/go-http-utils/etag?branch=master)

HTTP etag support middleware for Go.

## Installation

```
go get -u github.com/go-http-utils/etag
```

## Documentation

API documentation can be found here: https://godoc.org/github.com/go-http-utils/etag

## Usage

```go
import (
  "github.com/go-http-utils/etag"
)
```

```go
mux := http.NewServeMux()
mux.HandleFunc("/", func(res http.ResponseWriter, req *http.Request) {
  res.Write([]byte("Hello World"))
})

http.ListenAndServe(":8080", etag.Handler(mux, false))
```
