// Package main provides the loop-runner CLI binary.
package main

import (
	"os"

	"github.com/silmari/context-engine/go/internal/cli"
)

func main() {
	if err := cli.ExecuteLoopRunner(); err != nil {
		os.Exit(1)
	}
}
