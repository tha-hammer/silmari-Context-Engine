package concurrent

import (
	"context"
	"iter"
	"sync"
	"sync/atomic"
)

// Stream provides a channel-based stream abstraction for producing and consuming
// values of type T. It supports both channel-based and iterator-based consumption.
type Stream[T any] struct {
	ch     chan T
	closed atomic.Bool
	once   sync.Once
}

// NewStream creates a new Stream with the specified buffer size.
// A buffer of 0 creates an unbuffered channel.
func NewStream[T any](buffer int) *Stream[T] {
	if buffer < 0 {
		buffer = 0
	}
	return &Stream[T]{
		ch: make(chan T, buffer),
	}
}

// Send sends an item to the stream.
// Returns false if the stream is closed.
func (s *Stream[T]) Send(item T) bool {
	if s.closed.Load() {
		return false
	}

	defer func() {
		// Recover from panic if channel was closed between check and send
		recover()
	}()

	s.ch <- item
	return true
}

// TrySend attempts to send an item without blocking.
// Returns false if the stream is closed or the buffer is full.
func (s *Stream[T]) TrySend(item T) bool {
	if s.closed.Load() {
		return false
	}

	select {
	case s.ch <- item:
		return true
	default:
		return false
	}
}

// SendContext sends an item with context cancellation support.
// Returns false if the stream is closed or the context is cancelled.
func (s *Stream[T]) SendContext(ctx context.Context, item T) bool {
	if s.closed.Load() {
		return false
	}

	select {
	case s.ch <- item:
		return true
	case <-ctx.Done():
		return false
	}
}

// Receive returns the underlying channel for receiving values.
// Use this in a for-range loop or select statement.
func (s *Stream[T]) Receive() <-chan T {
	return s.ch
}

// Close closes the stream, preventing further sends.
// It is safe to call Close multiple times.
func (s *Stream[T]) Close() {
	s.once.Do(func() {
		s.closed.Store(true)
		close(s.ch)
	})
}

// IsClosed returns true if the stream has been closed.
func (s *Stream[T]) IsClosed() bool {
	return s.closed.Load()
}

// Iter returns an iterator for use with Go 1.23+ range-over-func.
// The iterator yields all values from the stream until it is closed.
func (s *Stream[T]) Iter() iter.Seq[T] {
	return func(yield func(T) bool) {
		for item := range s.ch {
			if !yield(item) {
				return
			}
		}
	}
}

// Iter2 returns an iterator that yields index-value pairs.
func (s *Stream[T]) Iter2() iter.Seq2[int, T] {
	return func(yield func(int, T) bool) {
		i := 0
		for item := range s.ch {
			if !yield(i, item) {
				return
			}
			i++
		}
	}
}

// Collect drains the stream and returns all values as a slice.
// This blocks until the stream is closed.
func (s *Stream[T]) Collect() []T {
	var result []T
	for item := range s.ch {
		result = append(result, item)
	}
	return result
}

// CollectN collects up to n items from the stream.
// Returns early if the stream is closed before n items are received.
func (s *Stream[T]) CollectN(n int) []T {
	result := make([]T, 0, n)
	for i := 0; i < n; i++ {
		item, ok := <-s.ch
		if !ok {
			break
		}
		result = append(result, item)
	}
	return result
}

// Pipe creates a new Stream and spawns a goroutine that applies fn to each
// item from this stream and sends the result to the new stream.
func (s *Stream[T]) Pipe(fn func(T) T) *Stream[T] {
	out := NewStream[T](cap(s.ch))
	go func() {
		defer out.Close()
		for item := range s.ch {
			out.Send(fn(item))
		}
	}()
	return out
}

// Filter creates a new Stream containing only items that satisfy the predicate.
func (s *Stream[T]) Filter(predicate func(T) bool) *Stream[T] {
	out := NewStream[T](cap(s.ch))
	go func() {
		defer out.Close()
		for item := range s.ch {
			if predicate(item) {
				out.Send(item)
			}
		}
	}()
	return out
}

// Merge combines multiple streams into a single stream.
// The returned stream closes when all input streams are closed.
func Merge[T any](streams ...*Stream[T]) *Stream[T] {
	out := NewStream[T](len(streams))
	var wg sync.WaitGroup

	for _, s := range streams {
		wg.Add(1)
		go func(stream *Stream[T]) {
			defer wg.Done()
			for item := range stream.Receive() {
				out.Send(item)
			}
		}(s)
	}

	go func() {
		wg.Wait()
		out.Close()
	}()

	return out
}

// Fan distributes items from one stream to multiple output streams in round-robin fashion.
func Fan[T any](input *Stream[T], n int) []*Stream[T] {
	outputs := make([]*Stream[T], n)
	for i := range outputs {
		outputs[i] = NewStream[T](cap(input.ch))
	}

	go func() {
		defer func() {
			for _, out := range outputs {
				out.Close()
			}
		}()

		i := 0
		for item := range input.Receive() {
			outputs[i].Send(item)
			i = (i + 1) % n
		}
	}()

	return outputs
}

// Generate creates a stream from a generator function.
// The generator runs in a separate goroutine and should call send for each value.
// When the generator returns, the stream is closed.
func Generate[T any](buffer int, generator func(send func(T))) *Stream[T] {
	s := NewStream[T](buffer)
	go func() {
		defer s.Close()
		generator(func(item T) {
			s.Send(item)
		})
	}()
	return s
}

// FromSlice creates a stream from a slice.
// All items are sent to the stream and it is closed.
func FromSlice[T any](items []T) *Stream[T] {
	s := NewStream[T](len(items))
	go func() {
		defer s.Close()
		for _, item := range items {
			s.Send(item)
		}
	}()
	return s
}

// FromChannel creates a Stream from an existing channel.
// The Stream takes ownership of the channel and will not close it.
func FromChannel[T any](ch <-chan T) *Stream[T] {
	s := NewStream[T](0)
	go func() {
		defer s.Close()
		for item := range ch {
			s.Send(item)
		}
	}()
	return s
}
