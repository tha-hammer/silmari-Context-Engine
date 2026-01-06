package fs

import "time"

// currentTime returns the current time.
// This is a variable to allow mocking in tests.
var currentTime = func() time.Time {
	return time.Now()
}
