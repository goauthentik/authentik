# fresh
[![Build Status](https://travis-ci.org/go-http-utils/fresh.svg?branch=master)](https://travis-ci.org/go-http-utils/fresh)
[![Coverage Status](https://coveralls.io/repos/github/go-http-utils/fresh/badge.svg?branch=master)](https://coveralls.io/github/go-http-utils/fresh?branch=master)

HTTP response freshness testing for Go

## Installation

```sh
go get -u github.com/go-http-utils/fresh
```

## Documentation

API documentation can be found here: https://godoc.org/github.com/go-http-utils/fresh

## Usage

```go
import (
  "net/http"

  "github.com/go-http-utils/fresh"
  "github.com/go-http-utils/headers"
)
```

```go
reqHeader, resHeader := make(http.Header), make(http.Header)

reqHeader.Set(headers.IfNoneMatch, "foo")
resHeader.Set(headers.ETag, "bar")

fresh.IsFresh(reqHeader, resHeader)
// -> false
```

```go
reqHeader, resHeader := make(http.Header), make(http.Header)

reqHeader.Set(headers.IfMatch, "foo")
resHeader.Set(headers.ETag, "bar")

fresh.IsFresh(reqHeader, resHeader)
// -> true
```

```go
reqHeader, resHeader := make(http.Header), make(http.Header)

reqHeader.Set(headers.IfModifiedSince, "Mon, 14 Nov 2016 22:05:49 GMT")
resHeader.Set(headers.LastModified, "Mon, 14 Nov 2016 22:05:47 GMT")

fresh.IsFresh(reqHeader, resHeader)
// -> true
```

```go
reqHeader, resHeader := make(http.Header), make(http.Header)

resHeader.Set(headers.IfUnmodifiedSince, "Mon, 14 Nov 2016 22:05:47 GMT")
reqHeader.Set(headers.LastModified, "Mon, 14 Nov 2016 22:05:49 GMT")

fresh.IsFresh(reqHeader, resHeader)
// -> true
```
