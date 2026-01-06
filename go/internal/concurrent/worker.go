package concurrent

import (
	"context"
	"sync"
)

// Result holds the outcome of a worker task, containing either a value or an error.
type Result[R any] struct {
	Value R
	Err   error
	Index int // Original submission order
}

// WorkerPool manages a pool of worker goroutines that process items of type T
// and produce results of type R. It provides ordered result collection and
// graceful shutdown.
type WorkerPool[T, R any] struct {
	ctx     context.Context
	cancel  context.CancelFunc
	workers int
	fn      func(context.Context, T) (R, error)
	input   chan workItem[T]
	output  chan Result[R]
	wg      sync.WaitGroup
	once    sync.Once
	closed  bool
	mu      sync.Mutex
	index   int
}

type workItem[T any] struct {
	item  T
	index int
}

// NewWorkerPool creates a new worker pool with the specified number of workers.
// The fn function is called for each submitted item to produce a result.
// The pool starts workers immediately upon creation.
func NewWorkerPool[T, R any](ctx context.Context, workers int, fn func(context.Context, T) (R, error)) *WorkerPool[T, R] {
	if workers < 1 {
		workers = 1
	}

	ctx, cancel := context.WithCancel(ctx)
	p := &WorkerPool[T, R]{
		ctx:     ctx,
		cancel:  cancel,
		workers: workers,
		fn:      fn,
		input:   make(chan workItem[T], workers*2),
		output:  make(chan Result[R], workers*2),
	}

	p.start()
	return p
}

// start spawns the worker goroutines.
func (p *WorkerPool[T, R]) start() {
	for i := 0; i < p.workers; i++ {
		p.wg.Add(1)
		go p.worker()
	}

	// Goroutine to close output channel when all workers are done
	go func() {
		p.wg.Wait()
		close(p.output)
	}()
}

// worker processes items from the input channel.
func (p *WorkerPool[T, R]) worker() {
	defer p.wg.Done()

	for {
		select {
		case <-p.ctx.Done():
			return
		case item, ok := <-p.input:
			if !ok {
				return
			}
			result, err := p.fn(p.ctx, item.item)
			select {
			case p.output <- Result[R]{Value: result, Err: err, Index: item.index}:
			case <-p.ctx.Done():
				return
			}
		}
	}
}

// Submit adds an item to the worker pool for processing.
// It blocks if the input buffer is full.
// Returns false if the pool is closed or the context is cancelled.
func (p *WorkerPool[T, R]) Submit(item T) bool {
	p.mu.Lock()
	if p.closed {
		p.mu.Unlock()
		return false
	}
	idx := p.index
	p.index++
	p.mu.Unlock()

	select {
	case p.input <- workItem[T]{item: item, index: idx}:
		return true
	case <-p.ctx.Done():
		return false
	}
}

// SubmitAll submits multiple items at once.
// Returns the number of items successfully submitted.
func (p *WorkerPool[T, R]) SubmitAll(items []T) int {
	count := 0
	for _, item := range items {
		if p.Submit(item) {
			count++
		} else {
			break
		}
	}
	return count
}

// Results returns a channel that receives results as they complete.
// Results may arrive out of order; use Result.Index to track original order.
func (p *WorkerPool[T, R]) Results() <-chan Result[R] {
	return p.output
}

// Close stops accepting new work and signals workers to finish.
// Call this after all items have been submitted.
func (p *WorkerPool[T, R]) Close() {
	p.once.Do(func() {
		p.mu.Lock()
		p.closed = true
		p.mu.Unlock()
		close(p.input)
	})
}

// Wait closes the input channel and waits for all workers to complete.
// Returns the first error encountered, or nil if all succeeded.
func (p *WorkerPool[T, R]) Wait() error {
	p.Close()

	var firstErr error
	for result := range p.output {
		if result.Err != nil && firstErr == nil {
			firstErr = result.Err
		}
	}
	return firstErr
}

// Collect closes the input channel and collects all results.
// Results are returned in submission order.
func (p *WorkerPool[T, R]) Collect() ([]R, error) {
	p.Close()

	results := make(map[int]Result[R])
	var firstErr error
	maxIndex := -1

	for result := range p.output {
		results[result.Index] = result
		if result.Index > maxIndex {
			maxIndex = result.Index
		}
		if result.Err != nil && firstErr == nil {
			firstErr = result.Err
		}
	}

	ordered := make([]R, maxIndex+1)
	for i := 0; i <= maxIndex; i++ {
		if r, ok := results[i]; ok {
			ordered[i] = r.Value
		}
	}

	return ordered, firstErr
}

// Cancel cancels the worker pool, stopping all workers.
func (p *WorkerPool[T, R]) Cancel() {
	p.cancel()
	p.Close()
}

// Map applies the worker pool's function to all items and returns results in order.
// This is a convenience function that submits all items, waits for completion,
// and returns ordered results.
func Map[T, R any](ctx context.Context, workers int, items []T, fn func(context.Context, T) (R, error)) ([]R, error) {
	pool := NewWorkerPool[T, R](ctx, workers, fn)
	pool.SubmitAll(items)
	return pool.Collect()
}
