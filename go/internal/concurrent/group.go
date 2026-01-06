// Package concurrent provides concurrency primitives for coordinating goroutines.
// It wraps common patterns for error handling, worker pools, streams, and rate limiting.
package concurrent

import (
	"context"
	"sync"

	"golang.org/x/sync/errgroup"
	"golang.org/x/sync/semaphore"
)

// Group coordinates a collection of goroutines with shared error handling and cancellation.
// It wraps errgroup.Group to provide a simpler API for common use cases.
type Group struct {
	ctx    context.Context
	cancel context.CancelFunc
	eg     *errgroup.Group
	sem    *semaphore.Weighted
	limit  int64
	mu     sync.Mutex
}

// NewGroup creates a new Group with the given context.
// The context is used for cancellation propagation to all spawned goroutines.
func NewGroup(ctx context.Context) *Group {
	ctx, cancel := context.WithCancel(ctx)
	eg, ctx := errgroup.WithContext(ctx)
	return &Group{
		ctx:    ctx,
		cancel: cancel,
		eg:     eg,
		limit:  0,
	}
}

// Context returns the context associated with this group.
// This context is cancelled when any goroutine returns an error or Wait is called.
func (g *Group) Context() context.Context {
	return g.ctx
}

// SetLimit sets the maximum number of goroutines that can run concurrently.
// A limit of 0 (the default) means no limit.
// SetLimit must be called before any calls to Go.
func (g *Group) SetLimit(n int) {
	g.mu.Lock()
	defer g.mu.Unlock()
	g.limit = int64(n)
	if n > 0 {
		g.sem = semaphore.NewWeighted(int64(n))
	}
}

// Go spawns a new goroutine that executes fn.
// If a limit is set, Go blocks until a slot is available.
// The first error returned by any goroutine will be returned by Wait.
func (g *Group) Go(fn func() error) {
	g.mu.Lock()
	sem := g.sem
	limit := g.limit
	g.mu.Unlock()

	if limit > 0 && sem != nil {
		g.eg.Go(func() error {
			if err := sem.Acquire(g.ctx, 1); err != nil {
				return err
			}
			defer sem.Release(1)
			return fn()
		})
	} else {
		g.eg.Go(fn)
	}
}

// GoWithContext spawns a new goroutine with access to the group's context.
// This is useful when the function needs to check for cancellation.
func (g *Group) GoWithContext(fn func(ctx context.Context) error) {
	g.Go(func() error {
		return fn(g.ctx)
	})
}

// Wait blocks until all spawned goroutines complete.
// It returns the first error encountered by any goroutine, or nil if all succeeded.
func (g *Group) Wait() error {
	err := g.eg.Wait()
	g.cancel()
	return err
}

// Cancel cancels the group's context, signaling all goroutines to stop.
func (g *Group) Cancel() {
	g.cancel()
}

// TryGo attempts to spawn a goroutine without blocking.
// It returns false if the concurrency limit is reached and no slot is available.
// If no limit is set, it always spawns the goroutine and returns true.
func (g *Group) TryGo(fn func() error) bool {
	g.mu.Lock()
	sem := g.sem
	limit := g.limit
	g.mu.Unlock()

	if limit > 0 && sem != nil {
		if !sem.TryAcquire(1) {
			return false
		}
		g.eg.Go(func() error {
			defer sem.Release(1)
			return fn()
		})
		return true
	}

	g.eg.Go(fn)
	return true
}
