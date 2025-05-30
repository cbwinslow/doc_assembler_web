"""Performance tests for the research pipeline."""
import pytest
import asyncio
import time
import psutil
import os
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

from airesearch.core.researcher import ResearchEngine
from airesearch.core.pipeline import ResearchPipeline
from airesearch.models.topic import Topic
from airesearch.interfaces.crawler_interface import CrawledContent
from airesearch.interfaces.document_interface import DocumentTemplate

class PerformanceMetrics:
    """Class for collecting performance metrics."""
    
    def __init__(self):
        self.execution_time: float = 0
        self.memory_usage: Dict[str, int] = {}
        self.cpu_usage: List[float] = []
        self.content_size: int = 0
        self.operation_counts: Dict[str, int] = {}
        self.stage_timings: Dict[str, List[float]] = defaultdict(list)
        self.latencies: List[float] = []
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.throughput_stats: Dict[str, float] = {}

    def record_memory(self, stage: str):
        """Record memory usage for a stage."""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        self.memory_usage[stage] = {
            'rss': memory_info.rss,
            'vms': memory_info.vms,
            'shared': memory_info.shared,
            'data': memory_info.data
        }

    def record_cpu(self):
        """Record CPU usage."""
        self.cpu_usage.append(psutil.cpu_percent(interval=0.1))

    def record_stage_timing(self, stage: str, duration: float):
        """Record timing for a specific pipeline stage."""
        self.stage_timings[stage].append(duration)

    def record_latency(self, latency: float):
        """Record request latency."""
        self.latencies.append(latency)

    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.error_counts[error_type] += 1

    def calculate_throughput_stats(self, total_operations: int):
        """Calculate throughput statistics."""
        self.throughput_stats = {
            'operations_per_second': total_operations / self.execution_time if self.execution_time > 0 else 0,
            'avg_latency': statistics.mean(self.latencies) if self.latencies else 0,
            'p95_latency': statistics.quantiles(self.latencies, n=20)[18] if len(self.latencies) >= 20 else None,
            'p99_latency': statistics.quantiles(self.latencies, n=100)[98] if len(self.latencies) >= 100 else None
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        metrics = {
            "execution_time": self.execution_time,
            "memory_usage": self.memory_usage,
            "avg_cpu_usage": statistics.mean(self.cpu_usage) if self.cpu_usage else 0,
            "peak_cpu_usage": max(self.cpu_usage) if self.cpu_usage else 0,
            "content_size": self.content_size,
            "operation_counts": self.operation_counts,
            "stage_timings": {
                stage: {
                    'avg': statistics.mean(timings),
                    'min': min(timings),
                    'max': max(timings),
                    'std_dev': statistics.stdev(timings) if len(timings) > 1 else 0
                } for stage, timings in self.stage_timings.items()
            },
            "error_rates": {
                error_type: count / sum(self.operation_counts.values()) if sum(self.operation_counts.values()) > 0 else 0
                for error_type, count in self.error_counts.items()
            },
            "throughput_stats": self.throughput_stats
        }
        return metrics

class BenchmarkContext:
    """Context manager for benchmarking code blocks."""
    
    def __init__(self, metrics: PerformanceMetrics, stage: str):
        self.metrics = metrics
        self.stage = stage
        self.start_time: Optional[float] = None

    async def __aenter__(self):
        """Enter the benchmark context."""
        self.start_time = time.time()
        self.metrics.record_memory(f"{self.stage}_start")
        self.metrics.record_cpu()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the benchmark context."""
        if exc_type:
            self.metrics.record_error(f"{self.stage}_{exc_type.__name__}")
        duration = time.time() - self.start_time if self.start_time else 0
        self.metrics.record_stage_timing(self.stage, duration)
        self.metrics.record_memory(f"{self.stage}_end")
        self.metrics.record_cpu()
        self.metrics.record_latency(duration)

@pytest.fixture
def performance_metrics() -> PerformanceMetrics:
    """Create performance metrics collector."""
    return PerformanceMetrics()

@pytest.fixture
def benchmark_context(performance_metrics: PerformanceMetrics):
    """Create benchmark context."""
    return lambda stage: BenchmarkContext(performance_metrics, stage)

@pytest.mark.performance
@pytest.mark.asyncio
async def test_concurrent_research_performance(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test performance of concurrent research tasks."""
    async with benchmark_context("total"):
        # Create multiple topics
        topics = [
            Topic(
                title=f"Performance Topic {i}",
                description=f"Performance test description {i}",
                keywords=[f"keyword{i}"]
            ) for i in range(5)
        ]

        # Execute concurrent research
        async def monitored_execution(topic: Topic):
            async with benchmark_context("research"):
                return await research_pipeline.execute_research(topic, sample_document_template)

        results = await asyncio.gather(*[monitored_execution(topic) for topic in topics])
        
        # Calculate throughput statistics
        performance_metrics.calculate_throughput_stats(len(topics))
        metrics = performance_metrics.to_dict()
        
        # Verify performance requirements
        assert metrics["execution_time"] < 30
        assert metrics["throughput_stats"]["operations_per_second"] >= 0.2
        assert metrics["throughput_stats"]["avg_latency"] < 10
        
        # Verify memory usage
        for stage in ["research_start", "research_end"]:
            assert metrics["memory_usage"][stage]["rss"] < 500 * 1024 * 1024  # Less than 500MB

@pytest.mark.performance
@pytest.mark.asyncio
async def test_large_content_performance(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test performance with large content volumes."""
    async with benchmark_context("total"):
        # Create large content
        large_content = "\n".join([
            f"Content line {i}" for i in range(10000)
        ])
        performance_metrics.content_size = len(large_content.encode())
        
        # Process content
        async with benchmark_context("content_processing"):
            content = CrawledContent(
                url="https://example.com/large",
                content=large_content,
                metadata={"size": "large"},
                crawled_at=datetime.utcnow()
            )
            await research_pipeline.add_content(content)
        
        # Execute research
        async with benchmark_context("research"):
            result = await research_pipeline.execute_research(
                sample_topic,
                sample_document_template
            )
        
        metrics = performance_metrics.to_dict()
        
        # Verify performance requirements
        assert metrics["stage_timings"]["content_processing"]["avg"] < 5
        assert metrics["stage_timings"]["research"]["avg"] < 30
        assert len(result) > performance_metrics.content_size * 0.1

@pytest.mark.performance
@pytest.mark.stress
@pytest.mark.asyncio
async def test_pipeline_stress(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test pipeline behavior under stress conditions."""
    async with benchmark_context("stress_test"):
        # Create large number of concurrent requests
        num_requests = 50
        topics = [
            Topic(
                title=f"Stress Topic {i}",
                description=f"Testing pipeline under stress {i}",
                keywords=[f"keyword{i}", "stress", "testing"]
            ) for i in range(num_requests)
        ]
        
        # Add varying content sizes
        content_sizes = [1000, 5000, 10000, 50000]
        for size in content_sizes:
            content = CrawledContent(
                url=f"https://example.com/size_{size}",
                content="\n".join([f"Content line {i}" for i in range(size)]),
                metadata={"size": size},
                crawled_at=datetime.utcnow()
            )
            await research_pipeline.add_content(content)
        
        # Execute stress test
        async def stress_execution(topic: Topic):
            try:
                async with benchmark_context("stress_request"):
                    return await research_pipeline.execute_research(
                        topic,
                        sample_document_template
                    )
            except Exception as e:
                performance_metrics.record_error(type(e).__name__)
                raise
        
        results = await asyncio.gather(
            *[stress_execution(topic) for topic in topics],
            return_exceptions=True
        )
        
        performance_metrics.calculate_throughput_stats(num_requests)
        metrics = performance_metrics.to_dict()
        
        # Verify stress handling
        success_rate = len([r for r in results if not isinstance(r, Exception)]) / len(results)
        assert success_rate >= 0.95  # At least 95% success rate
        assert metrics["throughput_stats"]["p99_latency"] < 30  # 99th percentile latency under 30s
        assert metrics["error_rates"].get("TimeoutError", 0) < 0.05  # Less than 5% timeout rate

@pytest.mark.performance
@pytest.mark.load
@pytest.mark.asyncio
async def test_sustained_load(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test pipeline under sustained load."""
    test_duration = 60  # 1 minute test
    request_rate = 2  # requests per second
    
    async with benchmark_context("load_test"):
        start_time = time.time()
        request_count = 0
        load_stats = {
            'success_count': 0,
            'error_count': 0,
            'latencies': []
        }
        
        async def load_generator():
            nonlocal request_count
            while time.time() - start_time < test_duration:
                topic = Topic(
                    title=f"Load Topic {request_count}",
                    description=f"Testing sustained load {request_count}",
                    keywords=[f"keyword{request_count}"]
                )
                
                async with benchmark_context("load_request"):
                    try:
                        request_start = time.time()
                        await research_pipeline.execute_research(
                            topic,
                            sample_document_template
                        )
                        latency = time.time() - request_start
                        load_stats['latencies'].append(latency)
                        load_stats['success_count'] += 1
                        request_count += 1
                    except Exception as e:
                        performance_metrics.record_error(type(e).__name__)
                        load_stats['error_count'] += 1
                
                # Adaptive sleep to maintain request rate
                elapsed = time.time() - request_start
                sleep_time = max(0, (1 / request_rate) - elapsed)
                await asyncio.sleep(sleep_time)
        
        # Run multiple load generators
        generators = [load_generator() for _ in range(3)]
        await asyncio.gather(*generators)
        
        performance_metrics.calculate_throughput_stats(request_count)
        metrics = performance_metrics.to_dict()
        
        # Verify load handling
        assert metrics["throughput_stats"]["operations_per_second"] >= request_rate
        assert metrics["error_rates"].get("TimeoutError", 0) < 0.01  # Less than 1% timeout rate
        assert all(
            stats["avg"] < 5 for stats in metrics["stage_timings"].values()
        )
        
        # Verify load stability
        avg_latency = statistics.mean(load_stats['latencies'])
        latency_stdev = statistics.stdev(load_stats['latencies'])
        assert latency_stdev / avg_latency < 0.5  # Coefficient of variation < 0.5

@pytest.mark.performance
@pytest.mark.recovery
@pytest.mark.asyncio
async def test_recovery_performance(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test pipeline recovery performance after errors."""
    async with benchmark_context("recovery_test"):
        # Simulate system under pressure
        pressure_tasks = []
        for _ in range(10):
            content = CrawledContent(
                url="https://example.com/pressure",
                content="Pressure test content" * 1000,
                metadata={"type": "pressure"},
                crawled_at=datetime.utcnow()
            )
            pressure_tasks.append(research_pipeline.add_content(content))
        
        await asyncio.gather(*pressure_tasks)
        
        # Test recovery after simulated failures
        async def recovery_execution():
            for attempt in range(3):
                try:
                    async with benchmark_context(f"recovery_attempt_{attempt}"):
                        return await research_pipeline.execute_research(
                            sample_topic,
                            sample_document_template
                        )
                except Exception as e:
                    performance_metrics.record_error(type(e).__name__)
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
            return None
        
        results = await asyncio.gather(*[recovery_execution() for _ in range(5)])
        
        metrics = performance_metrics.to_dict()
        
        # Verify recovery performance
        success_count = len([r for r in results if r is not None])
        assert success_count >= 4  # At least 4 out of 5 should succeed
        
        # Verify recovery improvements
        for i in range(2):
            current_attempt = f"recovery_attempt_{i}"
            next_attempt = f"recovery_attempt_{i+1}"
            if current_attempt in metrics["stage_timings"] and next_attempt in metrics["stage_timings"]:
                assert metrics["stage_timings"][current_attempt]["avg"] > \
                       metrics["stage_timings"][next_attempt]["avg"]  # Recovery should improve

@pytest.mark.performance
@pytest.mark.stability
@pytest.mark.asyncio
async def test_long_running_stability(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test pipeline stability during long-running operations."""
    test_duration = 180  # 3 minutes
    check_interval = 15  # Check every 15 seconds
    
    async with benchmark_context("stability_test"):
        start_time = time.time()
        stability_metrics = {
            'memory_snapshots': [],
            'cpu_snapshots': [],
            'request_latencies': [],
            'success_rate': [],
            'gc_stats': [],
            'thread_counts': []
        }
        
        while time.time() - start_time < test_duration:
            async with benchmark_context("stability_iteration"):
                # Record pre-iteration metrics
                process = psutil.Process()
                stability_metrics['thread_counts'].append(process.num_threads())
                
                # Execute batch of requests
                batch_size = 5
                tasks = []
                batch_start = time.time()
                
                for i in range(batch_size):
                    topic = Topic(
                        title=f"Stability Topic {i}",
                        description=f"Testing long-running stability {i}",
                        keywords=[f"keyword{i}", "stability", "test"]
                    )
                    tasks.append(research_pipeline.execute_research(
                        topic,
                        sample_document_template
                    ))
                
                # Collect results and metrics
                results = await asyncio.gather(*tasks, return_exceptions=True)
                batch_duration = time.time() - batch_start
                
                successes = len([r for r in results if not isinstance(r, Exception)])
                stability_metrics['success_rate'].append(successes / batch_size)
                stability_metrics['request_latencies'].append(batch_duration / batch_size)
                
                # Record system metrics
                memory_info = process.memory_info()
                stability_metrics['memory_snapshots'].append({
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'shared': memory_info.shared,
                    'data': memory_info.data
                })
                
                stability_metrics['cpu_snapshots'].append(
                    psutil.cpu_percent(interval=0.1)
                )
                
                import gc
                gc.collect()
                stability_metrics['gc_stats'].append(gc.get_stats())
                
                await asyncio.sleep(check_interval)
        
        # Calculate stability indicators
        memory_trend = [
            y['rss'] - x['rss'] for x, y in zip(
                stability_metrics['memory_snapshots'][:-1],
                stability_metrics['memory_snapshots'][1:]
            )
        ]
        avg_memory_growth = statistics.mean(memory_trend) if memory_trend else 0
        
        success_rate_stability = statistics.stdev(
            stability_metrics['success_rate']
        ) if len(stability_metrics['success_rate']) > 1 else 0
        
        latency_stability = statistics.stdev(
            stability_metrics['request_latencies']
        ) if len(stability_metrics['request_latencies']) > 1 else 0
        
        # Verify stability requirements
        assert avg_memory_growth < 1024 * 1024  # Less than 1MB growth per interval
        assert min(stability_metrics['success_rate']) >= 0.95  # Minimum 95% success
        assert success_rate_stability < 0.05  # Low variation in success rate
        assert max(stability_metrics['cpu_snapshots']) < 90  # CPU usage under 90%
        assert latency_stability < 1.0  # Low latency variation
        assert max(stability_metrics['thread_counts']) < 100  # Thread count in check

@pytest.mark.performance
@pytest.mark.resources
@pytest.mark.asyncio
async def test_resource_utilization(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test resource utilization patterns."""
    async with benchmark_context("resource_test"):
        # Set up resource monitoring
        baseline_process = psutil.Process()
        initial_metrics = {
            'cpu': baseline_process.cpu_percent(),
            'memory': baseline_process.memory_info(),
            'threads': baseline_process.num_threads(),
            'files': len(baseline_process.open_files()),
            'connections': len(baseline_process.connections()),
            'ctx_switches': baseline_process.num_ctx_switches(),
            'handles': baseline_process.num_handles() if os.name == 'nt' else 0,
            'fds': baseline_process.num_fds() if os.name != 'nt' else 0
        }
        
        # Execute workload
        tasks = []
        workload_metrics = []
        
        for i in range(10):
            topic = Topic(
                title=f"Resource Topic {i}",
                description=f"Testing resource utilization {i}",
                keywords=[f"keyword{i}", "resource", "test"]
            )
            tasks.append(research_pipeline.execute_research(
                topic,
                sample_document_template
            ))
        
        # Monitor during execution
        async def monitor_resources():
            while not all(t.done() for t in tasks):
                process = psutil.Process()
                metrics = {
                    'timestamp': time.time(),
                    'cpu': process.cpu_percent(),
                    'memory': process.memory_info(),
                    'threads': process.num_threads(),
                    'files': len(process.open_files()),
                    'connections': len(process.connections()),
                    'ctx_switches': process.num_ctx_switches(),
                    'handles': process.num_handles() if os.name == 'nt' else 0,
                    'fds': process.num_fds() if os.name != 'nt' else 0,
                    'io_counters': process.io_counters()
                }
                workload_metrics.append(metrics)
                await asyncio.sleep(0.1)
        
        # Run workload and monitoring
        monitor_task = asyncio.create_task(monitor_resources())
        results = await asyncio.gather(*tasks)
        await monitor_task
        
        # Calculate peak metrics
        peak_metrics = {
            'cpu': max(m['cpu'] for m in workload_metrics),
            'memory': max(m['memory'].rss for m in workload_metrics),
            'threads': max(m['threads'] for m in workload_metrics),
            'files': max(m['files'] for m in workload_metrics),
            'connections': max(m['connections'] for m in workload_metrics)
        }
        
        # Allow for cleanup
        await asyncio.sleep(1)
        final_process = psutil.Process()
        final_metrics = {
            'memory': final_process.memory_info(),
            'threads': final_process.num_threads(),
            'files': len(final_process.open_files()),
            'connections': len(final_process.connections())
        }
        
        # Verify resource utilization
        assert peak_metrics['cpu'] < 80  # CPU usage under 80%
        assert peak_metrics['memory'] < initial_metrics['memory'].rss * 3  # Less than 3x memory growth
        assert peak_metrics['threads'] < 100  # Thread count under control
        assert peak_metrics['files'] < 1000  # File handle usage reasonable
        assert peak_metrics['connections'] < 100  # Connection count reasonable
        
        # Verify cleanup
        assert final_metrics['memory'].rss < peak_metrics['memory']  # Memory cleaned up
        assert final_metrics['threads'] <= initial_metrics['threads'] + 5  # Threads cleaned up
        assert final_metrics['files'] <= initial_metrics['files'] + 10  # File handles cleaned up
        assert final_metrics['connections'] <= initial_metrics['connections'] + 5  # Connections cleaned up

@pytest.mark.performance
@pytest.mark.asyncio
async def test_pipeline_throughput(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test pipeline throughput with continuous processing."""
    num_iterations = 10
    batch_size = 2
    memory_samples = []
    batch_timings = []
    
    async with benchmark_context("total"):
        # Record initial memory state
        initial_process = psutil.Process()
        initial_memory = initial_process.memory_info()
        memory_samples.append({
            'rss': initial_memory.rss,
            'vms': initial_memory.vms,
            'shared': initial_memory.shared,
            'data': initial_memory.data,
            'timestamp': time.time()
        })
        
        for batch in range(0, num_iterations, batch_size):
            async with benchmark_context(f"batch_{batch//batch_size}"):
                batch_start = time.time()
                tasks = []
                
                for i in range(batch, min(batch + batch_size, num_iterations)):
                    topic = Topic(
                        title=f"Throughput Topic {i}",
                        description=f"Testing pipeline throughput iteration {i}",
                        keywords=[f"keyword{i}", "throughput", "test"]
                    )
                    tasks.append(research_pipeline.execute_research(
                        topic,
                        sample_document_template
                    ))
                
                # Execute batch and measure performance
                batch_results = await asyncio.gather(*tasks)
                batch_duration = time.time() - batch_start
                batch_timings.append(batch_duration)
                
                # Record memory state
                memory_info = psutil.Process().memory_info()
                memory_samples.append({
                    'rss': memory_info.rss,
                    'vms': memory_info.vms,
                    'shared': memory_info.shared,
                    'data': memory_info.data,
                    'timestamp': time.time()
                })
                
                # Verify batch results
                assert all(isinstance(r, bytes) for r in batch_results)
                assert all(len(r) > 0 for r in batch_results)
                
                # Allow for memory stabilization
                if batch < num_iterations - batch_size:
                    await asyncio.sleep(0.1)
        
        # Calculate final metrics
        performance_metrics.calculate_throughput_stats(num_iterations)
        metrics = performance_metrics.to_dict()
        
        # Memory growth analysis
        memory_growth = [
            samples[1]['rss'] - samples[0]['rss']
            for samples in zip(memory_samples[:-1], memory_samples[1:])
        ]
        time_intervals = [
            samples[1]['timestamp'] - samples[0]['timestamp']
            for samples in zip(memory_samples[:-1], memory_samples[1:])
        ]
        memory_growth_rates = [
            growth / interval for growth, interval in zip(memory_growth, time_intervals)
        ]
        
        avg_growth_rate = statistics.mean(memory_growth_rates) if memory_growth_rates else 0
        growth_trend = [
            y - x for x, y in zip(memory_growth_rates[:-1], memory_growth_rates[1:])
        ] if len(memory_growth_rates) > 1 else []
        
        # Performance metrics analysis
        batch_throughput = [batch_size / timing for timing in batch_timings]
        avg_throughput = statistics.mean(batch_throughput)
        throughput_stability = statistics.stdev(batch_throughput) / avg_throughput
        
        # Verify performance requirements
        assert metrics["throughput_stats"]["operations_per_second"] >= 0.5
        assert metrics["throughput_stats"]["p95_latency"] < 15
        assert all(
            stats["avg"] < 10
            for stats in metrics["stage_timings"].values()
        )
        assert throughput_stability < 0.3  # Throughput variation under 30%
        
        # Verify memory stability
        assert avg_growth_rate < 1024 * 1024  # Less than 1MB/s average growth
        assert all(growth < 5 * 1024 * 1024 for growth in memory_growth)  # No sudden spikes
        assert not growth_trend or statistics.mean(growth_trend) <= 0  # No accelerating growth

@pytest.mark.performance
@pytest.mark.performance
@pytest.mark.memory
@pytest.mark.profiling
@pytest.mark.asyncio
async def test_memory_profiling(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test detailed memory profiling of the pipeline."""
    import tracemalloc
    import linecache
    import gc
    from collections import defaultdict
    
    def get_trace_key(trace):
        """Create a key for the trace."""
        return tuple((frame.filename, frame.lineno) for frame in trace)
    
    def format_trace(trace):
        """Format trace for readability."""
        result = []
        for frame in trace:
            filename = frame.filename
            lineno = frame.lineno
            line = linecache.getline(filename, lineno).strip()
            result.append(f"{filename}:{lineno}: {line}")
        return result
    
    def analyze_snapshot_diff(diff, threshold_mb: float = 0.1):
        """Analyze memory snapshot differences."""
        significant_allocs = []
        for stat in diff:
            # Convert to MB for readability
            size_mb = stat.size_diff / (1024 * 1024)
            if abs(size_mb) >= threshold_mb:
                significant_allocs.append({
                    'size_mb': size_mb,
                    'count': stat.count_diff,
                    'trace': format_trace(stat.traceback)
                })
        return significant_allocs
    
    async with benchmark_context("memory_profiling"):
        # Enable garbage collection monitoring
        gc.set_debug(gc.DEBUG_STATS)
        
        # Start tracking memory allocations
        tracemalloc.start(25)  # Track 25 frames
        
        # Track memory by operation type
        operation_memory = defaultdict(list)
        snapshots = {}
        gc_stats = defaultdict(list)
        
        # Test different operations
        operations = [
            ("content_processing", lambda: research_pipeline.add_content(
                CrawledContent(
                    url="https://example.com/profiling",
                    content="Test content" * 1000,
                    metadata={"type": "profiling"},
                    crawled_at=datetime.utcnow()
                )
            )),
            ("research", lambda: research_pipeline.execute_research(
                sample_topic,
                sample_document_template
            )),
            ("batch_processing", lambda: asyncio.gather(*[
                research_pipeline.execute_research(
                    Topic(
                        title=f"Profile Topic {i}",
                        description=f"Memory profiling test {i}",
                        keywords=[f"keyword{i}"]
                    ),
                    sample_document_template
                ) for i in range(3)
            ]))
        ]
        
        for op_name, op_func in operations:
            # Record initial state
            gc.collect()
            gc_stats[op_name].append(gc.get_stats())
            snapshots[f"{op_name}_before"] = tracemalloc.take_snapshot()
            
            # Execute operation
            async with benchmark_context(f"profile_{op_name}"):
                await op_func()
            
            # Record post-operation state
            gc_stats[op_name].append(gc.get_stats())
            snapshots[f"{op_name}_after"] = tracemalloc.take_snapshot()
            
            # Analyze memory changes
            memory_diff = snapshots[f"{op_name}_after"].compare_to(
                snapshots[f"{op_name}_before"],
                'traceback'
            )
            
            # Analyze significant allocations
            significant_changes = analyze_snapshot_diff(memory_diff)
            
            # Record memory statistics
            operation_memory[op_name].extend([
                {
                    'size': stat.size_diff,
                    'count': stat.count_diff,
                    'trace': format_trace(stat.traceback)
                }
                for stat in memory_diff
            ])
            
            # Record significant changes in metrics
            if significant_changes:
                performance_metrics.memory_usage[f"{op_name}_significant"] = significant_changes
            
            # Allow for cleanup
            await asyncio.sleep(0.1)
        
        # Disable tracing before analysis
        tracemalloc.stop()
        gc.set_debug(0)
        
        # Analyze memory patterns
        for op_name, stats in operation_memory.items():
            total_size = sum(stat['size'] for stat in stats)
            total_count = sum(stat['count'] for stat in stats)
            
            # Calculate memory statistics
            sizes = [stat['size'] for stat in stats]
            if sizes:
                avg_size = statistics.mean(sizes)
                max_size = max(sizes)
                min_size = min(sizes)
            
            # Record in performance metrics
            performance_metrics.operation_counts[f"{op_name}_allocations"] = total_count
            performance_metrics.memory_usage[f"{op_name}_memory"] = {
                'total': total_size,
                'average': avg_size if sizes else 0,
                'max': max_size if sizes else 0,
                'min': min_size if sizes else 0
            }
            
            # Analyze GC impact
            before_stats = gc_stats[op_name][0]
            after_stats = gc_stats[op_name][1]
            collections = [
                after_stats[i][0] - before_stats[i][0]
                for i in range(3)  # Three GC generations
            ]
            
            performance_metrics.operation_counts[f"{op_name}_gc_collections"] = collections
            
            # Verify memory usage patterns
            assert total_size < 50 * 1024 * 1024  # Less than 50MB per operation
            assert total_count < 10000  # Reasonable number of allocations
            
            # Check for memory leaks
            leaked_memory = [
                stat for stat in stats
                if stat['size'] > 1024 * 1024  # Larger than 1MB
                and stat['count'] > 0  # Still allocated
            ]
            assert not leaked_memory, f"Memory leaks detected in {op_name}"

@pytest.mark.memory
@pytest.mark.asyncio
async def test_memory_leak_detection
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test for memory leaks during extended operation."""
    num_iterations = 20
    memory_tracking = {
        'rss': [],
        'vms': [],
        'shared': [],
        'data': [],
        'gc_counts': [],
        'timestamps': [],
        'allocated_objects': []
    }
    
    async with benchmark_context("memory_test"):
        import gc
        import sys
        import tracemalloc
        
        # Enable memory tracking
        tracemalloc.start()
        gc.collect()  # Initial cleanup
        
        initial_snapshot = tracemalloc.take_snapshot()
        
        for i in range(num_iterations):
            async with benchmark_context(f"iteration_{i}"):
                # Execute research
                result = await research_pipeline.execute_research(
                    Topic(
                        title=f"Memory Test {i}",
                        description=f"Testing memory usage iteration {i}",
                        keywords=[f"keyword{i}", "memory", "test"]
                    ),
                    sample_document_template
                )
                
                # Record memory metrics
                memory_info = psutil.Process().memory_info()
                current_time = time.time()
                
                memory_tracking['timestamps'].append(current_time)
                memory_tracking['rss'].append(memory_info.rss)
                memory_tracking['vms'].append(memory_info.vms)
                memory_tracking['shared'].append(memory_info.shared)
                memory_tracking['data'].append(memory_info.data)
                
                # Track garbage collection and object counts
                gc.collect()
                memory_tracking['gc_counts'].append(sum(gc.get_count()))
                memory_tracking['allocated_objects'].append(len(gc.get_objects()))
                
                # Force cleanup
                del result
                await asyncio.sleep(0.1)
        
        # Take final snapshot and compare
        final_snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Analyze memory patterns
        for metric, values in memory_tracking.items():
            if metric not in ['gc_counts', 'timestamps', 'allocated_objects']:
                # Calculate growth rate over time
                growth_rates = [
                    (y - x) / (t2 - t1)
                    for (x, t1), (y, t2) in zip(
                        zip(values[:-1], memory_tracking['timestamps'][:-1]),
                        zip(values[1:], memory_tracking['timestamps'][1:])
                    )
                ]
                avg_growth_rate = statistics.mean(growth_rates) if growth_rates else 0
                
                # Verify no consistent growth
                assert avg_growth_rate < 1024 * 1024  # Less than 1MB/s growth
                
                # Check for memory spikes
                max_spike = max(abs(r) for r in growth_rates) if growth_rates else 0
                assert max_spike < 5 * 1024 * 1024  # No more than 5MB/s spike
        
        # Analyze object allocation patterns
        object_growth = [
            y - x for x, y in zip(
                memory_tracking['allocated_objects'][:-1],
                memory_tracking['allocated_objects'][1:]
            )
        ]
        avg_object_growth = statistics.mean(object_growth) if object_growth else 0
        assert avg_object_growth <= 0  # No persistent object growth
        
        # Compare memory snapshots
        stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
        total_growth = sum(stat.size_diff for stat in stats)
        assert total_growth < 1024 * 1024  # Less than 1MB total growth

