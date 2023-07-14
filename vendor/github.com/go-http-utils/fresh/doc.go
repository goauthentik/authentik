// Package fresh is used to check whether cache can be used in this HTTP request.
//
// ----------------------------------------------------------------
//
// reqHeader, resHeader := make(http.Header), make(http.Header)
//
// reqHeader.Set("if-none-match", "foo")
// resHeader.Set("etag", "bar")

// fresh.IsFresh(reqHeader, resHeader)
// // -> false
//
// ----------------------------------------------------------------
//
// reqHeader, resHeader := make(http.Header), make(http.Header)

// reqHeader.Set("if-modified-since", "Mon, 14 Nov 2016 22:05:49 GMT")
// resHeader.Set("last-modified", "Mon, 14 Nov 2016 22:05:47 GMT")

// fresh.IsFresh(reqHeader, resHeader)
// // -> true
//
// ----------------------------------------------------------------

package fresh
