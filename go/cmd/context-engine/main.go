// Package main provides the context-engine CLI binary.
package main

import (
	"os"

	"github.com/silmari/context-engine/internal/cli"
)

func main() {
	if err := cli.Execute(); err != nil {
		os.Exit(1)
	}
}
