package concurrent

import (
	"context"
	"errors"
	"sync"
	"sync/atomic"
	"testing"
	"time"
)

func TestNewGroup(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	if g == nil {
		t.Fatal("NewGroup returned nil")
	}

	if g.ctx == nil {
		t.Error("Group context is nil")
	}

	if g.cancel == nil {
		t.Error("Group cancel function is nil")
	}

	if g.eg == nil {
		t.Error("Group errgroup is nil")
	}

	if g.limit != 0 {
		t.Errorf("Expected default limit 0, got %d", g.limit)
	}
}

func TestGroup_Context(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	groupCtx := g.Context()
	if groupCtx == nil {
		t.Fatal("Context() returned nil")
	}

	// Context should not be cancelled initially
	select {
	case <-groupCtx.Done():
		t.Error("Context should not be cancelled initially")
	default:
		// Expected
	}
}

func TestGroup_Go_SingleTask(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	executed := false
	g.Go(func() error {
		executed = true
		return nil
	})

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if !executed {
		t.Error("Task was not executed")
	}
}

func TestGroup_Go_MultipleTasks(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	var count atomic.Int32
	numTasks := 10

	for i := 0; i < numTasks; i++ {
		g.Go(func() error {
			count.Add(1)
			return nil
		})
	}

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if got := count.Load(); got != int32(numTasks) {
		t.Errorf("Expected %d tasks executed, got %d", numTasks, got)
	}
}

func TestGroup_Go_Error(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	expectedErr := errors.New("test error")

	g.Go(func() error {
		return expectedErr
	})

	err := g.Wait()
	if err != expectedErr {
		t.Errorf("Expected error %v, got %v", expectedErr, err)
	}
}

func TestGroup_Go_FirstErrorReturned(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	err1 := errors.New("error 1")
	err2 := errors.New("error 2")

	var started sync.WaitGroup
	started.Add(2)

	g.Go(func() error {
		started.Done()
		started.Wait() // Wait for both to start
		time.Sleep(10 * time.Millisecond)
		return err1
	})

	g.Go(func() error {
		started.Done()
		started.Wait() // Wait for both to start
		return err2
	})

	err := g.Wait()
	// One of the errors should be returned
	if err != err1 && err != err2 {
		t.Errorf("Expected error1 or error2, got %v", err)
	}
}

func TestGroup_SetLimit(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	g.SetLimit(2)

	if g.limit != 2 {
		t.Errorf("Expected limit 2, got %d", g.limit)
	}

	if g.sem == nil {
		t.Error("Semaphore should be initialized")
	}
}

func TestGroup_SetLimit_Zero(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	// First set a limit
	g.SetLimit(5)
	if g.sem == nil {
		t.Error("Semaphore should be initialized after SetLimit(5)")
	}

	// Set to zero - should not create new semaphore
	g.SetLimit(0)
	if g.limit != 0 {
		t.Errorf("Expected limit 0, got %d", g.limit)
	}
}

func TestGroup_Go_WithLimit(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)
	g.SetLimit(2)

	var maxConcurrent atomic.Int32
	var current atomic.Int32

	numTasks := 10

	for i := 0; i < numTasks; i++ {
		g.Go(func() error {
			cur := current.Add(1)
			for {
				old := maxConcurrent.Load()
				if cur <= old || maxConcurrent.CompareAndSwap(old, cur) {
					break
				}
			}
			time.Sleep(10 * time.Millisecond)
			current.Add(-1)
			return nil
		})
	}

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if maxConcurrent.Load() > 2 {
		t.Errorf("Expected max concurrent <= 2, got %d", maxConcurrent.Load())
	}
}

func TestGroup_GoWithContext(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	var receivedCtx context.Context

	g.GoWithContext(func(ctx context.Context) error {
		receivedCtx = ctx
		return nil
	})

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if receivedCtx == nil {
		t.Error("GoWithContext did not pass context")
	}
}

func TestGroup_GoWithContext_Cancellation(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	var cancelled atomic.Bool

	g.GoWithContext(func(ctx context.Context) error {
		select {
		case <-ctx.Done():
			cancelled.Store(true)
		case <-time.After(1 * time.Second):
		}
		return nil
	})

	// Cancel after a short delay
	time.AfterFunc(10*time.Millisecond, func() {
		g.Cancel()
	})

	_ = g.Wait()

	if !cancelled.Load() {
		t.Error("Task was not notified of cancellation")
	}
}

func TestGroup_Cancel(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	g.Cancel()

	select {
	case <-g.Context().Done():
		// Expected
	default:
		t.Error("Context should be cancelled after Cancel()")
	}
}

func TestGroup_Cancel_BeforeGo(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)
	g.SetLimit(1)

	g.Cancel()

	// Tasks should fail due to cancelled context when acquiring semaphore
	g.Go(func() error {
		return nil
	})

	err := g.Wait()
	if err == nil {
		t.Error("Expected error due to cancelled context")
	}
}

func TestGroup_TryGo_NoLimit(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	executed := false
	ok := g.TryGo(func() error {
		executed = true
		return nil
	})

	if !ok {
		t.Error("TryGo should return true when no limit is set")
	}

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if !executed {
		t.Error("Task was not executed")
	}
}

func TestGroup_TryGo_WithLimit(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)
	g.SetLimit(1)

	started := make(chan struct{})
	proceed := make(chan struct{})

	// First task - should succeed
	ok1 := g.TryGo(func() error {
		close(started)
		<-proceed
		return nil
	})

	if !ok1 {
		t.Error("First TryGo should succeed")
	}

	// Wait for first task to start
	<-started

	// Second task - should fail because limit is reached
	ok2 := g.TryGo(func() error {
		return nil
	})

	if ok2 {
		t.Error("Second TryGo should fail when limit is reached")
	}

	// Let first task complete
	close(proceed)

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}
}

func TestGroup_TryGo_Error(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	expectedErr := errors.New("try go error")

	ok := g.TryGo(func() error {
		return expectedErr
	})

	if !ok {
		t.Error("TryGo should return true when task is spawned")
	}

	err := g.Wait()
	if err != expectedErr {
		t.Errorf("Expected error %v, got %v", expectedErr, err)
	}
}

func TestGroup_Wait_CancelsContext(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	groupCtx := g.Context()

	g.Go(func() error {
		return nil
	})

	_ = g.Wait()

	select {
	case <-groupCtx.Done():
		// Expected - context should be cancelled after Wait
	case <-time.After(100 * time.Millisecond):
		t.Error("Context should be cancelled after Wait")
	}
}

func TestGroup_ContextCancellation_BlocksGo(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	g := NewGroup(ctx)
	g.SetLimit(1)

	started := make(chan struct{})

	// First task holds the semaphore
	g.Go(func() error {
		close(started)
		time.Sleep(100 * time.Millisecond)
		return nil
	})

	<-started

	// Cancel before second task can acquire
	cancel()

	// Second task should fail to acquire semaphore
	g.Go(func() error {
		t.Log("Second task executed")
		return nil
	})

	err := g.Wait()
	if err == nil {
		t.Error("Expected error due to cancelled context")
	}
}

func TestGroup_ConcurrentGo(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	var count atomic.Int32
	var wg sync.WaitGroup

	numGoroutines := 100
	wg.Add(numGoroutines)

	for i := 0; i < numGoroutines; i++ {
		go func() {
			defer wg.Done()
			g.Go(func() error {
				count.Add(1)
				return nil
			})
		}()
	}

	wg.Wait()
	err := g.Wait()

	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if count.Load() != int32(numGoroutines) {
		t.Errorf("Expected %d executions, got %d", numGoroutines, count.Load())
	}
}

func TestGroup_ConcurrentSetLimit(t *testing.T) {
	// This test ensures SetLimit is safe to call concurrently
	// (though in practice it should be called before Go)
	ctx := context.Background()
	g := NewGroup(ctx)

	var wg sync.WaitGroup
	wg.Add(10)

	for i := 0; i < 10; i++ {
		go func(n int) {
			defer wg.Done()
			g.SetLimit(n + 1)
		}(i)
	}

	wg.Wait()
	// No panic means success
}

func TestGroup_ErrorPropagationToOtherTasks(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)

	taskError := errors.New("task error")
	var task2CancelledEarly atomic.Bool

	g.Go(func() error {
		return taskError
	})

	g.GoWithContext(func(ctx context.Context) error {
		// This task should see the context get cancelled due to error in first task
		<-ctx.Done()
		task2CancelledEarly.Store(true)
		return nil
	})

	err := g.Wait()
	if err != taskError {
		t.Errorf("Expected error %v, got %v", taskError, err)
	}

	// Give a moment for the cancellation to propagate
	time.Sleep(10 * time.Millisecond)

	if !task2CancelledEarly.Load() {
		t.Error("Second task should have been cancelled due to error in first task")
	}
}

func TestGroup_ParentContextCancellation(t *testing.T) {
	parentCtx, parentCancel := context.WithCancel(context.Background())
	g := NewGroup(parentCtx)

	var taskCancelled atomic.Bool

	g.GoWithContext(func(ctx context.Context) error {
		<-ctx.Done()
		taskCancelled.Store(true)
		return ctx.Err()
	})

	// Cancel parent context
	parentCancel()

	err := g.Wait()
	if err == nil {
		t.Error("Expected context.Canceled error")
	}

	if !taskCancelled.Load() {
		t.Error("Task should have been cancelled when parent context was cancelled")
	}
}

func TestGroup_LimitEnforcement_Stress(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping stress test in short mode")
	}

	ctx := context.Background()
	g := NewGroup(ctx)
	limit := 5
	g.SetLimit(limit)

	var maxConcurrent atomic.Int32
	var current atomic.Int32
	numTasks := 100

	for i := 0; i < numTasks; i++ {
		g.Go(func() error {
			cur := current.Add(1)
			for {
				old := maxConcurrent.Load()
				if cur <= old || maxConcurrent.CompareAndSwap(old, cur) {
					break
				}
			}
			time.Sleep(time.Duration(1+i%5) * time.Millisecond)
			current.Add(-1)
			return nil
		})
	}

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}

	if maxConcurrent.Load() > int32(limit) {
		t.Errorf("Expected max concurrent <= %d, got %d", limit, maxConcurrent.Load())
	}
}

func TestGroup_TryGo_WithLimit_AfterCompletion(t *testing.T) {
	ctx := context.Background()
	g := NewGroup(ctx)
	g.SetLimit(1)

	// First task completes immediately
	ok1 := g.TryGo(func() error {
		return nil
	})
	if !ok1 {
		t.Error("First TryGo should succeed")
	}

	// Wait a bit for the first task to complete and release the semaphore
	time.Sleep(50 * time.Millisecond)

	// Second task should now succeed
	ok2 := g.TryGo(func() error {
		return nil
	})
	if !ok2 {
		t.Error("Second TryGo should succeed after first task completes")
	}

	err := g.Wait()
	if err != nil {
		t.Errorf("Wait returned unexpected error: %v", err)
	}
}
