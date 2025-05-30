"""Memory profiling and leak detection tests."""
import gc
import asyncio
import tracemalloc
import psutil
from datetime import datetime
from typing import Callable

import pytest
from airesearch.pipeline import ResearchPipeline
from airesearch.models import Topic, DocumentTemplate, CrawledContent
from airesearch.metrics import PerformanceMetrics
from airesearch.context import BenchmarkContext
import pytest
import asyncio
import time
import psutil
import os
import statistics
import gc
import sys
import tracemalloc
import warnings
from pathlib import Path
from typing import Dict, List, Any, Callable
from collections import defaultdict, Counter
from datetime import datetime

from airesearch.core.researcher import ResearchEngine
from airesearch.core.pipeline import ResearchPipeline
from airesearch.models.topic import Topic
from airesearch.interfaces.crawler_interface import CrawledContent
from airesearch.interfaces.document_interface import DocumentTemplate
from tests.performance.test_research_performance import PerformanceMetrics, BenchmarkContext

# Fixtures specific to memory testing
def track_allocations(func):
    """Decorator to track allocations during a benchmark."""
    async def wrapper(*args, **kwargs):
        gc.collect()
        before_objects = len(gc.get_objects())
        before_mem = psutil.Process().memory_info().rss
        
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            gc.collect()
            after_objects = len(gc.get_objects())
            after_mem = psutil.Process().memory_info().rss
            
            print(f"Allocation tracking for {func.__name__}:")
            print(f"  Objects: {after_objects - before_objects}")
            print(f"  Memory: {(after_mem - before_mem) / 1024 / 1024:.2f} MB")
    
    return wrapper

@pytest.fixture(autouse=True)
def setup_memory_test(request):
    """Set up memory profiling tests."""
    """Setup for memory testing."""
    # Disable GC during setup
    gc.disable()
    # Clear any existing tracemalloc
    if tracemalloc.is_tracing():
        tracemalloc.stop()

@pytest.mark.memory
@pytest.mark.allocations
@pytest.mark.asyncio
async def test_allocation_tracking(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test memory allocation patterns during operations."""
    async with benchmark_context("allocation_tracking"):
        tracemalloc.start(25)  # Track 25 frames
        gc.collect()  # Initial cleanup
        
        test_scenarios = [
            {
                "name": "small_content",
                "content_size": 1000,
                "description": "Testing small content processing"
            },
            {
                "name": "medium_content",
                "content_size": 10000,
                "description": "Testing medium content processing"
            },
            {
                "name": "large_content",
                "content_size": 100000,
                "description": "Testing large content processing"
            }
        ]
        
        try:
            for scenario in test_scenarios:
                # Pre-operation state
                gc.collect()
                before = tracemalloc.take_snapshot()
                before_process = psutil.Process()
                before_memory = before_process.memory_info()
                before_objects = len(gc.get_objects())
                
                # Execute operation
                async with benchmark_context(f"scenario_{scenario['name']}"):
                    # Add content
                    content = CrawledContent(
                        url=f"https://example.com/{scenario['name']}",
                        content="x" * scenario['content_size'],
                        metadata={"type": scenario['name']},
                        crawled_at=datetime.utcnow()
                    )
                    await research_pipeline.add_content(content)
                    
                    # Process content
                    result = await research_pipeline.execute_research(
                        Topic(
                            title=f"Allocation Test {scenario['name']}",
                            description=scenario['description'],
                            keywords=[scenario['name'], "test"]
                        ),
                        sample_document_template
                    )
                
                # Post-operation state
                gc.collect()
                after = tracemalloc.take_snapshot()
                after_process = psutil.Process()
                after_memory = after_process.memory_info()
                after_objects = len(gc.get_objects())
                
                # Calculate metrics
                memory_diff = after.compare_to(before, 'traceback')
                allocation_stats = {
                    'rss_delta': after_memory.rss - before_memory.rss,
                    'vms_delta': after_memory.vms - before_memory.vms,
                    'shared_delta': after_memory.shared - before_memory.shared,
                    'object_delta': after_objects - before_objects,
                    'total_allocated': sum(s.size for s in memory_diff if s.size > 0),
                    'total_freed': abs(sum(s.size for s in memory_diff if s.size < 0)),
                    'allocation_count': sum(s.count for s in memory_diff if s.count > 0)
                }
                
                # Record metrics
                performance_metrics.memory_usage[f"{scenario['name']}_stats"] = allocation_stats
                
                # Record top allocations
                top_stats = memory_diff.statistics('traceback')[:5]
                if top_stats:
                    performance_metrics.memory_usage[f"{scenario['name']}_top"] = [
                        {
                            'size': stat.size,
                            'count': stat.count,
                            'traceback': str(stat.traceback)
                        }
                        for stat in top_stats
                    ]
                
                # Cleanup
                del result
                del content
                gc.collect()
                await asyncio.sleep(0.1)
                
                # Verify scenario results
                assert allocation_stats['rss_delta'] < scenario['content_size'] * 2, \
                    f"Excessive memory growth in {scenario['name']}"
                
                assert allocation_stats['object_delta'] < 1000, \
                    f"Too many objects retained in {scenario['name']}"
                
                efficiency = allocation_stats['total_freed'] / allocation_stats['total_allocated'] \
                    if allocation_stats['total_allocated'] > 0 else 0
                assert efficiency > 0.5, \
                    f"Poor memory efficiency in {scenario['name']}: {efficiency:.2%} freed"
        
        finally:
            tracemalloc.stop()
            gc.collect()
    # Suppress resource warnings
@pytest.mark.memory
@pytest.mark.patterns
@pytest.mark.asyncio
async def test_memory_pattern_analysis(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext],
    memory_tracker: Dict[str, Any]
):
    """Test for memory usage patterns and anomalies with advanced statistical analysis.
    
    Features:
    - Advanced statistical analysis (KS test, CUSUM, seasonal decomposition)
    - Extended metrics collection
    - Enhanced anomaly detection (MACD, Bollinger Bands)
    - Improved validation with significance testing
    """
        try:
            import numpy as np
            from scipy import stats
            from scipy.signal import find_peaks, seasonal_decompose
            from scipy.stats import ks_2samp
            import pandas as pd
            from sklearn.ensemble import IsolationForest
            from statsmodels.tsa.seasonal import seasonal_decompose
            from statsmodels.tsa.holtwinters import ExponentialSmoothing
        except ImportError as e:
            pytest.skip(f"Required package not found: {e}")
    
    async with benchmark_context("memory_patterns"):
        pattern_metrics = {
            'cyclic_patterns': [],
            'growth_trends': [],
            'anomalies': [],
            'baselines': {},
            'samples': defaultdict(list),
            'time_series': pd.DataFrame(),
            'distribution_tests': {},
            'change_points': [],
            'seasonal_components': {},
            'allocation_stats': defaultdict(list),
            'cache_metrics': defaultdict(list),
            'anomaly_scores': [],
            'validation_metrics': {},
            'allocation_lifetimes': defaultdict(list),
            'fragmentation_metrics': defaultdict(list),
            'memory_churn': {
                'allocation_frequency': defaultdict(list),
                'deallocation_frequency': defaultdict(list),
                'object_lifetimes': defaultdict(list),
                'turnover_rates': defaultdict(float),
                'churn_patterns': defaultdict(list)
            },
            'access_patterns': {
                'frequency_map': defaultdict(int),
                'temporal_locality': defaultdict(list),
                'spatial_locality': defaultdict(list),
                'hotspots': defaultdict(int)
            },
            'heap_analysis': {
                'block_sizes': defaultdict(list),
                'free_space': defaultdict(list),
                'fragmentation_index': defaultdict(float),
                'allocation_patterns': defaultdict(list)
            },
            'allocation_distribution': {
                'size_clusters': defaultdict(list),
                'source_patterns': defaultdict(list),
                'lifetime_distribution': defaultdict(list),
                'correlation_matrix': defaultdict(dict)
            }
        }
        }
        
        # Execute workload with varying patterns
        workload_patterns = [
            ('baseline', 1),    # Establish baseline
            ('intensive', 5),   # Heavy workload
            ('normal', 1),      # Return to normal
            ('intensive', 5),   # Second heavy phase
            ('cooldown', 1)     # Final cooldown
        ]
        
        all_samples = []  # For time series analysis
        
        for pattern, intensity in workload_patterns:
            async with benchmark_context(f"pattern_{pattern}"):
                # Execute operations with specified intensity
                for iteration in range(intensity):
                    # Record pre-operation state
                    pre_memory = psutil.Process().memory_info()
                    start_time = time.time()
                    
                    # Execute operation
                    result = await research_pipeline.execute_research(
                        Topic(
                            title=f"Pattern Test {pattern}",
                            description=f"Testing memory patterns {pattern}",
                            keywords=[pattern, "test", f"iteration_{iteration}"]
                        ),
                        sample_document_template
                    )
                    
                    # Record detailed metrics
                    end_time = time.time()
                    post_memory = psutil.Process().memory_info()
                    duration = end_time - start_time
                    memory_delta = post_memory.rss - pre_memory.rss
                    
                    sample_data = {
                        'timestamp': end_time,
                        'pattern': pattern,
                        'iteration': iteration,
                        'duration': duration,
                        'memory_delta': memory_delta,
                        'rss': post_memory.rss,
                        'vms': post_memory.vms,
                        'shared': post_memory.shared,
                        'data': post_memory.data
                    }
                    
                    all_samples.append(sample_data)
                    pattern_metrics['samples'][pattern].append(sample_data)
                    
                    # Record in tracker
                    memory_tracker['rss'].append(post_memory.rss)
                    memory_tracker['timestamps'].append(end_time)
                    
                    # Force cleanup and stabilization
                    gc.collect()
                    await asyncio.sleep(0.1)
        # Memory Churn Analysis Setup
        object_creation_times = {}
        object_sizes = {}
        
        # Initialize tracemalloc for detailed tracking
        tracemalloc.stop()
        tracemalloc.start(25)
        snapshot1 = tracemalloc.take_snapshot()
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(all_samples)
        pattern_metrics['time_series'] = df
        
        # Track memory churn metrics
        snapshot2 = tracemalloc.take_snapshot()
        memory_diff = snapshot2.compare_to(snapshot1, 'lineno')
        
        # Analyze memory churn
        for stat in memory_diff:
            if stat.size_diff > 0:  # New allocations
                pattern_metrics['memory_churn']['allocation_frequency'][str(stat.traceback)].append({
                    'size': stat.size_diff,
                    'count': stat.count_diff,
                    'timestamp': time.time()
                })
            else:  # Deallocations
                pattern_metrics['memory_churn']['deallocation_frequency'][str(stat.traceback)].append({
                    'size': -stat.size_diff,
                    'count': -stat.count_diff,
                    'timestamp': time.time()
                })

        # Calculate memory turnover rates
        for trace, allocs in pattern_metrics['memory_churn']['allocation_frequency'].items():
            deallocs = pattern_metrics['memory_churn']['deallocation_frequency'].get(trace, [])
            if allocs and deallocs:
                turnover_rate = sum(d['size'] for d in deallocs) / sum(a['size'] for a in allocs)
                pattern_metrics['memory_churn']['turnover_rates'][trace] = turnover_rate

        # Analyze object lifetimes
        gc.collect()
        for obj in gc.get_objects():
            obj_id = id(obj)
            if obj_id not in object_creation_times:
                object_creation_times[obj_id] = time.time()
                object_sizes[obj_id] = sys.getsizeof(obj)

        # Calculate lifetime distributions
        current_time = time.time()
        for obj_id, creation_time in object_creation_times.items():
            lifetime = current_time - creation_time
            size = object_sizes.get(obj_id, 0)
            pattern_metrics['memory_churn']['object_lifetimes'][size].append(lifetime)

        # Access Pattern Analysis
        block_accesses = defaultdict(int)
        spatial_locality = defaultdict(list)
        
        # Monitor memory blocks for access patterns
        for i in range(len(df)):
            memory_info = psutil.Process().memory_info()
            block_size = memory_info.rss // 100  # Divide memory into 100 blocks
            for j in range(100):
                block_start = j * block_size
                block_end = (j + 1) * block_size
                if df.iloc[i]['rss'] >= block_start and df.iloc[i]['rss'] < block_end:
                    block_accesses[j] += 1
                    spatial_locality[j].append(time.time())

        # Record access patterns
        pattern_metrics['access_patterns']['frequency_map'].update(block_accesses)
        pattern_metrics['access_patterns']['spatial_locality'].update(spatial_locality)

        # Detect hotspots
        mean_access = statistics.mean(block_accesses.values())
        std_access = statistics.stdev(block_accesses.values())
        for block, count in block_accesses.items():
            if count > mean_access + 2 * std_access:
                pattern_metrics['access_patterns']['hotspots'][block] = count

        # Enhanced Heap Analysis
        heap_blocks = []
        free_blocks = []
        
        # Track heap block sizes
        for obj in gc.get_objects():
            size = sys.getsizeof(obj)
            heap_blocks.append(size)
            
        heap_blocks.sort()
        pattern_metrics['heap_analysis']['block_sizes']['distribution'] = heap_blocks
        
        # Calculate fragmentation metrics
        total_size = sum(heap_blocks)
        largest_block = max(heap_blocks)
        fragmentation_index = 1 - (largest_block / total_size) if total_size > 0 else 0
        pattern_metrics['heap_analysis']['fragmentation_index']['current'] = fragmentation_index

        # Advanced Allocation Distribution Analysis
        from sklearn.cluster import KMeans
        
        # Size-based clustering
        sizes = np.array(heap_blocks).reshape(-1, 1)
        if len(sizes) >= 5:  # Minimum samples for clustering
            kmeans = KMeans(n_clusters=min(5, len(sizes)), random_state=42)
            clusters = kmeans.fit_predict(sizes)
            for i, cluster in enumerate(clusters):
                pattern_metrics['allocation_distribution']['size_clusters'][cluster].append(sizes[i][0])

        # Track allocation sources
        for stat in memory_diff:
            if stat.size_diff > 0:
                pattern_metrics['allocation_distribution']['source_patterns'][str(stat.traceback)].append({
                    'size': stat.size_diff,
                    'timestamp': time.time()
                })

        # Calculate allocation correlations
        if len(df) > 1:
            allocation_features = [
                'memory_delta',
                'rss',
                'duration'
            ]
            correlation_matrix = df[allocation_features].corr()
            for feature1 in allocation_features:
                for feature2 in allocation_features:
                    pattern_metrics['allocation_distribution']['correlation_matrix'][feature1][feature2] = \
                        correlation_matrix.loc[feature1, feature2]
        
        # Advanced Statistical Analysis
        # 1. Kolmogorov-Smirnov test for distribution analysis
        for pattern in df['pattern'].unique():
            pattern_data = df[df['pattern'] == pattern]['memory_delta']
            baseline_data = df[df['pattern'] == 'baseline']['memory_delta']
            if len(pattern_data) > 0 and len(baseline_data) > 0:
                ks_statistic, p_value = ks_2samp(pattern_data, baseline_data)
                pattern_metrics['distribution_tests'][pattern] = {
                    'ks_statistic': ks_statistic,
                    'p_value': p_value
                }

        # 2. CUSUM analysis for change detection
        def detect_changes(data, threshold=1.0):
            cumsum = np.cumsum(data - np.mean(data))
            change_points = np.where(np.abs(cumsum) > threshold * np.std(data))[0]
            return change_points

        memory_changes = detect_changes(df['memory_delta'].values)
        pattern_metrics['change_points'] = memory_changes.tolist()

        # 3. Seasonal decomposition for cyclical patterns
        if len(df) >= 4:  # Minimum length for seasonal decomposition
            try:
                seasonal_result = seasonal_decompose(
                    df['memory_delta'],
                    period=min(len(df) // 2, 4),
                    extrapolate_trend=True
                )
                pattern_metrics['seasonal_components'] = {
                    'trend': seasonal_result.trend.tolist(),
                    'seasonal': seasonal_result.seasonal.tolist(),
                    'resid': seasonal_result.resid.tolist()
                }
            except Exception as e:
                performance_metrics.error_counts['seasonal_decompose'] = str(e)

        # 4. Allocation size distribution analysis
        allocation_sizes = np.diff(df['rss'].values)
        pattern_metrics['allocation_stats']['sizes'] = {
            'mean': np.mean(allocation_sizes),
            'std': np.std(allocation_sizes),
            'percentiles': np.percentile(allocation_sizes, [25, 50, 75, 90, 95, 99]).tolist()
        }

        # 5. Memory fragmentation monitoring
        fragmentation_index = lambda x, y: 1 - (x.min() / x.mean()) if x.mean() != 0 else 0
        rolling_window = min(5, len(df))
        df['fragmentation_index'] = df['memory_delta'].rolling(
            window=rolling_window
        ).apply(lambda x: fragmentation_index(x, None))

        # 6. MACD for trend analysis
        exp1 = df['memory_delta'].ewm(span=12, adjust=False).mean()
        exp2 = df['memory_delta'].ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        pattern_metrics['trend_analysis'] = {
            'macd': macd.tolist(),
            'signal': signal.tolist(),
            'histogram': (macd - signal).tolist()
        }

        # 7. Bollinger Bands for volatility
        rolling_mean = df['memory_delta'].rolling(window=rolling_window).mean()
        rolling_std = df['memory_delta'].rolling(window=rolling_window).std()
        pattern_metrics['volatility_bands'] = {
            'upper': (rolling_mean + 2 * rolling_std).tolist(),
            'lower': (rolling_mean - 2 * rolling_std).tolist(),
            'mean': rolling_mean.tolist()
        }

        # 8. Isolation Forest for outlier detection
        if len(df) >= 10:
            iso_forest = IsolationForest(random_state=42, contamination=0.1)
            pattern_metrics['anomaly_scores'] = iso_forest.fit_predict(
                df[['memory_delta', 'rss', 'duration']].values
            ).tolist()

        # 9. Cross-correlation analysis
        metrics_for_correlation = ['memory_delta', 'duration', 'rss']
        correlation_matrix = df[metrics_for_correlation].corr()
        pattern_metrics['correlation_analysis'] = correlation_matrix.to_dict()

        # Analyze patterns per workload type
        for pattern, samples in pattern_metrics['samples'].items():
            pattern_df = df[df['pattern'] == pattern]
            
            # Calculate comprehensive baseline statistics
            stats_dict = {
                'memory_delta': pattern_df['memory_delta'].agg(['mean', 'std', 'min', 'max']).to_dict(),
                'duration': pattern_df['duration'].agg(['mean', 'std', 'min', 'max']).to_dict(),
                'rss': pattern_df['rss'].agg(['mean', 'std', 'min', 'max']).to_dict()
            }
            
            pattern_metrics['baselines'][pattern] = stats_dict
            
            # Detect anomalies using Z-score and IQR
            for metric in ['memory_delta', 'duration', 'rss']:
                z_scores = stats.zscore(pattern_df[metric])
                iqr = pattern_df[metric].quantile(0.75) - pattern_df[metric].quantile(0.25)
                threshold = pattern_df[metric].quantile(0.75) + 1.5 * iqr
                
                # Combine Z-score and IQR methods
                anomalies = pattern_df[
                    (abs(z_scores) > 2) | (pattern_df[metric] > threshold)
                ].index.tolist()
                
                if anomalies:
                    pattern_metrics['anomalies'].append({
                        'pattern': pattern,
                        'metric': metric,
                        'anomalies': anomalies
                    })
        
        # Analyze memory growth trends using rolling statistics
        if len(df) > 2:
            df['memory_growth'] = df['rss'].diff() / df['duration']
            df['rolling_growth'] = df['memory_growth'].rolling(
                window=3, min_periods=1
            ).mean()
            
            # Detect trend changes
            trend_changes = df[
                df['rolling_growth'].diff().abs() > df['rolling_growth'].std()
            ].index.tolist()
            
            pattern_metrics['growth_trends'] = [
                {
                    'index': idx,
                    'timestamp': df.loc[idx, 'timestamp'],
                    'growth_rate': df.loc[idx, 'rolling_growth']
                }
                for idx in trend_changes
            ]
        
        # Detect cyclic patterns using autocorrelation
        if len(df) > 10:
            # Normalize memory values
            normalized_rss = (df['rss'] - df['rss'].mean()) / df['rss'].std()
            
            # Calculate autocorrelation
            autocorr = np.correlate(normalized_rss, normalized_rss, mode='full')
            autocorr = autocorr[len(autocorr)//2:]
            
            # Find peaks
            peaks, properties = find_peaks(
                autocorr,
                height=0.3,
                distance=2,
                prominence=0.1
            )
            
            if len(peaks) > 1:
                pattern_metrics['cyclic_patterns'] = [
                    {
                        'period': int(peak),
                        'correlation': float(autocorr[peak]),
                        'prominence': float(properties['prominences'][i])
                    }
                    for i, peak in enumerate(peaks)
                ]
        
        # Record comprehensive metrics
        performance_metrics.memory_usage['pattern_analysis'] = {
            'baselines': pattern_metrics['baselines'],
            'anomalies': len(pattern_metrics['anomalies']),
            'trend_changes': len(pattern_metrics['growth_trends']),
            'cyclic_patterns': len(pattern_metrics['cyclic_patterns']),
            'statistics': {
                'total_memory_growth': float(df['rss'].iloc[-1] - df['rss'].iloc[0]),
                'max_growth_rate': float(df['memory_growth'].max()),
                'mean_growth_rate': float(df['memory_growth'].mean()),
                'growth_rate_std': float(df['memory_growth'].std())
            },
            'advanced_analysis': {
                'distribution_tests': pattern_metrics['distribution_tests'],
                'change_points': len(pattern_metrics['change_points']),
                'seasonal_analysis': {
                    k: len(v) for k, v in pattern_metrics.get('seasonal_components', {}).items()
                },
                'allocation_statistics': pattern_metrics['allocation_stats'],
                'trend_analysis': {
                    'macd_crossovers': sum(1 for x, y in zip(
                        pattern_metrics['trend_analysis']['histogram'][:-1],
                        pattern_metrics['trend_analysis']['histogram'][1:]
                    ) if x * y < 0),
                    'volatility_breaches': sum(1 for x, y in zip(
                        df['memory_delta'],
                        pattern_metrics['volatility_bands']['upper']
                    ) if x > y)
                },
                'memory_churn_analysis': {
                    'turnover_rates': {
                        k: v for k, v in pattern_metrics['memory_churn']['turnover_rates'].items()
                    },
                    'lifetime_stats': {
                        size: {
                            'mean': statistics.mean(lifetimes),
                            'median': statistics.median(lifetimes),
                            'std': statistics.stdev(lifetimes) if len(lifetimes) > 1 else 0
                        }
                        for size, lifetimes in pattern_metrics['memory_churn']['object_lifetimes'].items()
                        if lifetimes
                    },
                    'churn_rate': len(pattern_metrics['memory_churn']['allocation_frequency']) / len(df)
                },
                'access_pattern_analysis': {
                    'hotspot_count': len(pattern_metrics['access_patterns']['hotspots']),
                    'spatial_locality_score': sum(
                        len(accesses) for accesses in pattern_metrics['access_patterns']['spatial_locality'].values()
                    ) / len(df),
                    'access_distribution': {
                        'mean': statistics.mean(pattern_metrics['access_patterns']['frequency_map'].values()),
                        'std': statistics.stdev(pattern_metrics['access_patterns']['frequency_map'].values())
                        if len(pattern_metrics['access_patterns']['frequency_map']) > 1 else 0
                    }
                },
                'heap_analysis': {
                    'fragmentation_index': pattern_metrics['heap_analysis']['fragmentation_index']['current'],
                    'block_size_stats': {
                        'mean': statistics.mean(pattern_metrics['heap_analysis']['block_sizes']['distribution']),
                        'median': statistics.median(pattern_metrics['heap_analysis']['block_sizes']['distribution']),
                        'std': statistics.stdev(pattern_metrics['heap_analysis']['block_sizes']['distribution'])
                        if len(pattern_metrics['heap_analysis']['block_sizes']['distribution']) > 1 else 0
                    }
                },
                'anomaly_detection': {
                    'isolation_forest_outliers': sum(1 for x in pattern_metrics['anomaly_scores'] if x == -1),
                    'correlation_strength': {
                        k: v for k, v in pattern_metrics['correlation_analysis'].items()
                        if isinstance(v, dict)
                    }
                }
            }
        }
        # Verify pattern characteristics
        # 1. Check baseline consistency and distribution
        for pattern, baseline in pattern_metrics['baselines'].items():
            memory_cv = baseline['memory_delta']['std'] / abs(baseline['memory_delta']['mean'])
            assert memory_cv < 0.5, \
                f"High memory variability in {pattern} pattern (CV: {memory_cv:.2f})"
            
            # Verify distribution characteristics
            if pattern in pattern_metrics['distribution_tests']:
                dist_test = pattern_metrics['distribution_tests'][pattern]
                assert dist_test['p_value'] > 0.01, \
                    f"Significant distribution deviation in {pattern} pattern (p={dist_test['p_value']:.4f})"

            # Verify memory churn characteristics
            if pattern in pattern_metrics['memory_churn']['turnover_rates']:
                turnover_rate = pattern_metrics['memory_churn']['turnover_rates'][pattern]
                assert turnover_rate < 0.8, f"Excessive memory churn in {pattern} pattern (rate: {turnover_rate:.2f})"

            # Check access pattern distribution
            if pattern_metrics['access_patterns']['hotspots']:
                hotspot_ratio = len(pattern_metrics['access_patterns']['hotspots']) / len(block_accesses)
                assert hotspot_ratio < 0.2, f"Too many memory access hotspots: {hotspot_ratio:.2%}"

            # Validate heap fragmentation
            current_fragmentation = pattern_metrics['heap_analysis']['fragmentation_index']['current']
            assert current_fragmentation < 0.6, f"High heap fragmentation detected: {current_fragmentation:.2%}"
        # 2. Verify anomaly frequency and characteristics
        total_measurements = len(df) * 3  # 3 metrics per sample
        anomaly_rate = sum(len(a['anomalies']) for a in pattern_metrics['anomalies']) / total_measurements
        
        # Check both traditional and isolation forest anomalies
        isolation_forest_rate = sum(1 for x in pattern_metrics['anomaly_scores'] if x == -1) / len(df)
        combined_anomaly_rate = (anomaly_rate + isolation_forest_rate) / 2
        
        assert anomaly_rate < 0.1, f"Too many traditional anomalies detected: {anomaly_rate:.2%}"
        assert isolation_forest_rate < 0.15, f"Too many isolation forest anomalies: {isolation_forest_rate:.2%}"
        assert combined_anomaly_rate < 0.12, f"Too many combined anomalies: {combined_anomaly_rate:.2%}"
        
        # Verify MACD crossovers aren't too frequent
        macd_crossover_rate = performance_metrics.memory_usage['pattern_analysis']['advanced_analysis']['trend_analysis']['macd_crossovers'] / len(df)
        assert macd_crossover_rate < 0.3, f"Too many trend reversals: {macd_crossover_rate:.2%}"
        # 3. Check growth trends and patterns
        if pattern_metrics['growth_trends']:
            max_growth_rate = max(abs(t['growth_rate']) for t in pattern_metrics['growth_trends'])
            assert max_growth_rate < 1024 * 1024 * 10, \
                f"Excessive memory growth rate: {max_growth_rate/1024/1024:.2f} MB/s"

            # Verify trend stability using volatility bands
            volatility_breach_rate = performance_metrics.memory_usage['pattern_analysis']['advanced_analysis']['trend_analysis']['volatility_breaches'] / len(df)
            assert volatility_breach_rate < 0.2, f"High memory volatility: {volatility_breach_rate:.2%} breaches"

            # Check change point frequency
            change_point_rate = len(pattern_metrics['change_points']) / len(df)
            assert change_point_rate < 0.25, f"Too many change points detected: {change_point_rate:.2%}"

            # Verify allocation size distribution
            alloc_stats = pattern_metrics['allocation_stats']['sizes']
            assert alloc_stats['percentiles'][5] < alloc_stats['mean'] * 5, "Suspicious allocation size distribution"
        # 4. Analyze cyclic patterns and seasonal components
        if pattern_metrics['cyclic_patterns']:
            # Verify pattern significance
            significant_patterns = [
                p for p in pattern_metrics['cyclic_patterns']
                if p['correlation'] > 0.5 and p['prominence'] > 0.2
            ]
            min_period = min(
                (p['period'] for p in significant_patterns),
                default=float('inf')
            )
            assert min_period >= 2, \
                f"Suspiciously short memory cycle: {min_period} samples"

            # Analyze seasonal components if available
            if 'seasonal_components' in pattern_metrics:
                seasonal = pattern_metrics['seasonal_components']
                if 'seasonal' in seasonal and len(seasonal['seasonal']) > 0:
                    seasonal_strength = np.std(seasonal['seasonal']) / np.std(seasonal['trend'])
                    assert seasonal_strength < 0.7, f"Excessive seasonal variation: {seasonal_strength:.2f}"

                    # Verify trend-seasonal relationship
                    trend_seasonal_corr = np.corrcoef(
                        seasonal['trend'][~np.isnan(seasonal['trend'])],
                        seasonal['seasonal'][~np.isnan(seasonal['seasonal'])]
                    )[0, 1]
                    assert abs(trend_seasonal_corr) < 0.8, f"Suspicious trend-seasonal correlation: {trend_seasonal_corr:.2f}"

            # Verify cross-correlation significance
            if 'correlation_analysis' in pattern_metrics:
                for metric1, corr_dict in pattern_metrics['correlation_analysis'].items():
                    for metric2, corr_val in corr_dict.items():
                        if metric1 != metric2 and isinstance(corr_val, (int, float)):
                            assert abs(corr_val) < 0.95, \
                                f"Suspicious correlation between {metric1} and {metric2}: {corr_val:.2f}"

@pytest.mark.memory
@pytest.mark.pressure
@pytest.mark.asyncio
async def test_memory_pressure_handling(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext],
    memory_tracker: Dict[str, Any]
):
    """Test pipeline behavior under memory pressure."""
    import resource
    import signal
    from functools import partial
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Operation timed out under memory pressure")
    
    async with benchmark_context("memory_pressure"):
        # Get initial memory limits and set up monitoring
        soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_AS)
        initial_usage = psutil.Process().memory_info()
        
        # Set up timeout handler
        original_handler = signal.signal(signal.SIGALRM, timeout_handler)
        
        try:
            # Set a lower memory limit (75% of current usage)
            current_memory = initial_usage.rss
            new_limit = current_memory + (current_memory * 0.75)
            resource.setrlimit(resource.RLIMIT_AS, (new_limit, hard_limit))
            
            # Create memory pressure
            pressure_data = []
            pressure_size = 1024 * 1024 * 10  # 10MB chunks
            pressure_metrics = {
                'allocations': 0,
                'total_size': 0,
                'peak_rss': 0
            }
            
            async def apply_memory_pressure():
                """Apply incremental memory pressure."""
                try:
                    while True:
                        pressure_data.append(bytearray(pressure_size))
                        pressure_metrics['allocations'] += 1
                        pressure_metrics['total_size'] += pressure_size
                        pressure_metrics['peak_rss'] = max(
                            pressure_metrics['peak_rss'],
                            psutil.Process().memory_info().rss
                        )
                        await asyncio.sleep(0.1)
                except (MemoryError, MemoryWarning) as e:
                    performance_metrics.error_counts['memory_pressure'] = str(e)
            
            # Start memory pressure task
            pressure_task = asyncio.create_task(apply_memory_pressure())
            
            # Execute operations under pressure
            results = []
            errors = []
            operation_metrics = defaultdict(list)
            
            for i in range(5):
                signal.alarm(30)  # Set 30-second timeout
                try:
                    async with benchmark_context(f"pressure_test_{i}"):
                        start_time = time.time()
                        result = await research_pipeline.execute_research(
                            Topic(
                                title=f"Pressure Test {i}",
                                description=f"Testing under memory pressure {i}",
                                keywords=[f"keyword{i}", "pressure", "test"]
                            ),
                            sample_document_template
                        )
                        results.append(result)
                        
                        # Record operation metrics
                        operation_metrics['duration'].append(time.time() - start_time)
                        memory_info = psutil.Process().memory_info()
                        operation_metrics['memory_used'].append(memory_info.rss - current_memory)
                        
                except Exception as e:
                    errors.append((i, type(e).__name__, str(e)))
                finally:
                    signal.alarm(0)  # Clear timeout
                
                # Record memory state
                memory_info = psutil.Process().memory_info()
                memory_tracker['rss'].append(memory_info.rss)
                memory_tracker['vms'].append(memory_info.vms)
                
                # Force cleanup and stabilization
                gc.collect()
                await asyncio.sleep(0.2)
            
            # Stop pressure task
            pressure_task.cancel()
            try:
                await pressure_task
            except asyncio.CancelledError:
                pass
            
            # Clear pressure data and cleanup
            pressure_data.clear()
            gc.collect()
            gc.collect()  # Double collection to ensure cleanup
            
            # Calculate and record metrics
            success_rate = len(results) / (len(results) + len(errors))
            avg_duration = statistics.mean(operation_metrics['duration'])
            avg_memory = statistics.mean(operation_metrics['memory_used'])
            
            performance_metrics.operation_counts.update({
                'pressure_test_success': len(results),
                'pressure_test_errors': len(errors),
                'pressure_test_avg_duration': avg_duration,
                'pressure_test_avg_memory': avg_memory,
                'pressure_allocations': pressure_metrics['allocations'],
                'pressure_total_size': pressure_metrics['total_size']
            })
            
            # Record error distribution
            error_types = Counter(error[1] for error in errors)
            performance_metrics.error_counts.update(error_types)
            
            # Verify test outcomes
            assert success_rate >= 0.6, f"Too many failures under pressure: {success_rate:.2%} success rate"
            assert not any(
                isinstance(e[1], MemoryError) for e in errors
            ), "Memory errors not handled gracefully"
            
            # Verify memory cleanup
            final_memory = psutil.Process().memory_info().rss
            assert final_memory < new_limit, f"Memory not cleaned up: {final_memory} > {new_limit}"
            
            # Verify operation stability
            duration_variance = statistics.variance(operation_metrics['duration'])
            assert duration_variance < avg_duration, "High operation time variance under pressure"
            
        finally:
            # Restore original limits and handlers
            signal.signal(signal.SIGALRM, original_handler)
            resource.setrlimit(resource.RLIMIT_AS, (soft_limit, hard_limit))
            gc.collect()

@pytest.mark.memory
@pytest.mark.resource_limits
@pytest.mark.asyncio
async def test_resource_limit_handling(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test handling of system resource limits."""
    import resource
    import signal
    
    def alarm_handler(signum, frame):
        raise TimeoutError("Resource limit test timed out")
    
    async with benchmark_context("resource_limits"):
        # Track resource usage
        resource_usage = {
            'cpu_time': [],
            'memory_usage': [],
            'io_operations': [],
            'file_descriptors': [],
            'context_switches': [],
            'page_faults': []
        }
        
        # Set up timeout handler
        original_handler = signal.signal(signal.SIGALRM, alarm_handler)
        
        # Get initial limits
        original_limits = {
            'cpu': resource.getrlimit(resource.RLIMIT_CPU),
            'nofile': resource.getrlimit(resource.RLIMIT_NOFILE),
            'as': resource.getrlimit(resource.RLIMIT_AS),
            'data': resource.getrlimit(resource.RLIMIT_DATA)
        }
        
        try:
            # Set stricter limits
            resource.setrlimit(resource.RLIMIT_NOFILE, (256, original_limits['nofile'][1]))
            
            for i in range(5):
                signal.alarm(20)  # 20-second timeout per iteration
                try:
                    async with benchmark_context(f"resource_test_{i}"):
                        # Record pre-operation state
                        usage = resource.getrusage(resource.RUSAGE_SELF)
                        resource_usage['cpu_time'].append(usage.ru_utime + usage.ru_stime)
                        resource_usage['memory_usage'].append(usage.ru_maxrss)
                        resource_usage['io_operations'].append(
                            usage.ru_inblock + usage.ru_oublock
                        )
                        resource_usage['file_descriptors'].append(
                            len(psutil.Process().open_files())
                        )
                        resource_usage['context_switches'].append(
                            usage.ru_nvcsw + usage.ru_nivcsw
                        )
                        resource_usage['page_faults'].append(
                            usage.ru_majflt + usage.ru_minflt
                        )
                        
                        # Execute operation
                        await research_pipeline.execute_research(
                            Topic(
                                title=f"Resource Test {i}",
                                description=f"Testing resource limits {i}",
                                keywords=[f"keyword{i}", "resource", "test"]
                            ),
                            sample_document_template
                        )
                finally:
                    signal.alarm(0)  # Clear timeout
            
            # Analyze resource usage patterns
            for metric, values in resource_usage.items():
                if len(values) > 1:
                    growth_rate = (values[-1] - values[0]) / len(values)
                    peak_value = max(values)
                    variance = statistics.variance(values) if len(values) > 2 else 0
                    
                    performance_metrics.operation_counts.update({
                        f'{metric}_growth': growth_rate,
                        f'{metric}_peak': peak_value,
                        f'{metric}_variance': variance
                    })
                    
                    # Verify reasonable growth
                    assert growth_rate < 100, f"Excessive {metric} growth: {growth_rate:.2f}/iteration"
                    assert variance < peak_value, f"High {metric} variance: {variance:.2f}"
            
            # Verify cleanup and stability
            final_usage = resource.getrusage(resource.RUSAGE_SELF)
            
            assert resource_usage['file_descriptors'][-1] <= (
                resource_usage['file_descriptors'][0] + 5
            ), "File descriptors not cleaned up"
            
            # Verify reasonable context switch rate
            ctx_switch_rate = (
                resource_usage['context_switches'][-1] - resource_usage['context_switches'][0]
            ) / 5  # per iteration
            assert ctx_switch_rate < 1000, f"Excessive context switching: {ctx_switch_rate:.2f}/iteration"
            
        finally:
            # Restore original limits and handler
            signal.signal(signal.SIGALRM, original_handler)
            for limit_type, (soft, hard) in original_limits.items():
                try:
                    resource.setrlimit(
                        getattr(resource, f'RLIMIT_{limit_type.upper()}'),
                        (soft, hard)
                    )
                except (ValueError, resource.error):
                    pass  # Skip if limit can't be restored
            gc.collect()
    # Suppress warnings
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    # Initialize memory monitoring
    process = psutil.Process()
    initial_memory = process.memory_info()
    
    yield
    
    # Cleanup after test
    gc.enable()
    gc.collect()
    gc.collect()  # Double collection to ensure cleanup
    
    # Stop memory tracking
    if tracemalloc.is_tracing():
        tracemalloc.stop()
    
    # Verify cleanup
    final_memory = process.memory_info()
    memory_delta = final_memory.rss - initial_memory.rss
    if memory_delta > 1024 * 1024:  # More than 1MB growth
        warnings.warn(
            f"Memory growth detected during test: {memory_delta / 1024 / 1024:.2f}MB",
            ResourceWarning
        )

@pytest.fixture
def memory_tracker():
    """Create a memory tracking dictionary."""
    return {
        'rss': [],
        'vms': [],
        'shared': [],
        'data': [],
        'gc_counts': [],
        'timestamps': [],
        'allocated_objects': [],
        'heap_sizes': [],
        'object_types': defaultdict(list)
    }

@pytest.mark.memory
@pytest.mark.asyncio
async def test_memory_leak_detection(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext],
    memory_tracker: Dict[str, Any]
):
    """Test for memory leaks during extended operation."""
    async with benchmark_context("memory_test"):
        # Enable memory tracking
        tracemalloc.start()
        gc.collect()
        
        initial_snapshot = tracemalloc.take_snapshot()
        initial_types = Counter(type(obj).__name__ for obj in gc.get_objects())
        
        for i in range(20):  # 20 iterations
            async with benchmark_context(f"iteration_{i}"):
                # Record pre-iteration state
                gc.collect()
                pre_types = Counter(type(obj).__name__ for obj in gc.get_objects())
                
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
                
                memory_tracker['timestamps'].append(current_time)
                memory_tracker['rss'].append(memory_info.rss)
                memory_tracker['vms'].append(memory_info.vms)
                memory_tracker['shared'].append(memory_info.shared)
                memory_tracker['data'].append(memory_info.data)
                
                # Track heap statistics
                heap_size = sum(map(sys.getsizeof, gc.get_objects()))
                memory_tracker['heap_sizes'].append(heap_size)
                
                # Record object type counts
                gc.collect()
                post_types = Counter(type(obj).__name__ for obj in gc.get_objects())
                type_diff = post_types - pre_types
                
                for type_name, count in type_diff.items():
                    memory_tracker['object_types'][type_name].append(count)
                
                # Track garbage collection
                memory_tracker['gc_counts'].append(sum(gc.get_count()))
                memory_tracker['allocated_objects'].append(len(gc.get_objects()))
                
                # Force cleanup
                del result
                await asyncio.sleep(0.1)
        
        # Final analysis
        final_snapshot = tracemalloc.take_snapshot()
        final_types = Counter(type(obj).__name__ for obj in gc.get_objects())
        tracemalloc.stop()
        
        # Analyze growth patterns
        for metric in ['rss', 'vms', 'shared', 'data', 'heap_sizes']:
            values = memory_tracker[metric]
            growth_rates = [
                (y - x) / (t2 - t1)
                for (x, t1), (y, t2) in zip(
                    zip(values[:-1], memory_tracker['timestamps'][:-1]),
                    zip(values[1:], memory_tracker['timestamps'][1:])
                )
            ]
            
            if growth_rates:
                avg_growth_rate = statistics.mean(growth_rates)
                max_spike = max(abs(r) for r in growth_rates)
                
                # Record metrics
                performance_metrics.memory_usage[f'{metric}_growth_rate'] = avg_growth_rate
                performance_metrics.memory_usage[f'{metric}_final'] = values[-1]
                performance_metrics.memory_usage[f'{metric}_peak'] = max(values)
                
                # Verify stability
                assert avg_growth_rate < 1024 * 1024, f"{metric} shows consistent growth"
                assert max_spike < 5 * 1024 * 1024, f"{metric} shows large spikes"
        
        # Analyze object patterns
        for type_name, counts in memory_tracker['object_types'].items():
            if counts:
                type_growth_rate = (counts[-1] - counts[0]) / len(counts)
                assert type_growth_rate <= 0, f"Object type {type_name} shows growth"
        
        # Compare snapshots
        stats = final_snapshot.compare_to(initial_snapshot, 'lineno')
        total_growth = sum(stat.size_diff for stat in stats)
        assert total_growth < 1024 * 1024, "Significant memory growth detected"
        
        # Verify object counts
        type_growth = final_types - initial_types
        significant_growth = {
            t: c for t, c in type_growth.items()
            if c > 100  # More than 100 instances growth
        }
        assert not significant_growth, f"Significant object growth detected: {significant_growth}"

@pytest.mark.memory
@pytest.mark.fragmentation
@pytest.mark.asyncio
async def test_memory_fragmentation(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test for memory fragmentation patterns."""
    async with benchmark_context("fragmentation_test"):
        import gc
        import sys
        
        fragmentation_metrics = {
            'allocated_blocks': [],
            'free_blocks': [],
            'block_sizes': [],
            'fragmentation_ratio': []
        }
        
        # Execute operations that might cause fragmentation
        for i in range(10):
            async with benchmark_context(f"fragmentation_iteration_{i}"):
                # Allocate objects of varying sizes
                objects = []
                for size in [100, 1000, 10000, 100000]:
                    objects.append('x' * size)
                
                # Execute research
                result = await research_pipeline.execute_research(
                    Topic(
                        title=f"Fragmentation Test {i}",
                        description=f"Testing memory fragmentation {i}",
                        keywords=[f"keyword{i}", "fragmentation", "test"]
                    ),
                    sample_document_template
                )
                
                # Record fragmentation metrics
                gc.collect()
                allocated = len(gc.get_objects())
                block_sizes = [sys.getsizeof(obj) for obj in gc.get_objects()]
                
                fragmentation_metrics['allocated_blocks'].append(allocated)
                fragmentation_metrics['block_sizes'].append(block_sizes)
                
                # Calculate fragmentation ratio
                if block_sizes:
                    total_size = sum(block_sizes)
                    max_block = max(block_sizes)
                    fragmentation_ratio = 1 - (max_block / total_size)
                    fragmentation_metrics['fragmentation_ratio'].append(fragmentation_ratio)
                
                # Clear objects
                objects.clear()
                del result
                gc.collect()
                await asyncio.sleep(0.1)
        
        # Analyze fragmentation patterns
        if fragmentation_metrics['fragmentation_ratio']:
            avg_fragmentation = statistics.mean(fragmentation_metrics['fragmentation_ratio'])
            max_fragmentation = max(fragmentation_metrics['fragmentation_ratio'])
            
            performance_metrics.memory_usage.update({
                'avg_fragmentation_ratio': avg_fragmentation,
                'max_fragmentation_ratio': max_fragmentation,
                'allocated_blocks_trend': [
                    b2 - b1 for b1, b2 in zip(
                        fragmentation_metrics['allocated_blocks'][:-1],
                        fragmentation_metrics['allocated_blocks'][1:]
                    )
                ]
            })
            
            # Verify fragmentation levels
            assert avg_fragmentation < 0.5, \
                f"High average memory fragmentation: {avg_fragmentation:.2%}"
            assert max_fragmentation < 0.7, \
                f"Excessive peak fragmentation: {max_fragmentation:.2%}"

@pytest.mark.memory
@pytest.mark.profiling
@pytest.mark.asyncio
async def test_detailed_memory_profiling(
    research_pipeline: ResearchPipeline,
    sample_topic: Topic,
    sample_document_template: DocumentTemplate,
    performance_metrics: PerformanceMetrics,
    benchmark_context: Callable[[str], BenchmarkContext]
):
    """Test detailed memory allocation patterns."""
    async with benchmark_context("memory_profiling"):
        tracemalloc.start(25)  # Track 25 frames
        
        # Track different operation types
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
            # Take snapshot before operation
            gc.collect()
            before = tracemalloc.take_snapshot()
            
            # Execute operation
            async with benchmark_context(f"profile_{op_name}"):
                await op_func()
            
            # Take snapshot after operation
            after = tracemalloc.take_snapshot()
            
            # Analyze memory changes
            stats = after.compare_to(before, 'traceback')
            
            # Record statistics
            performance_metrics.memory_usage[f"{op_name}_allocations"] = {
                'total': sum(stat.size for stat in stats),
                'count': sum(stat.count for stat in stats),
                'peak': max((stat.size for stat in stats), default=0)
            }
            
            # Record top memory users
            top_stats = stats.statistics('traceback')
            if top_stats:
                performance_metrics.memory_usage[f"{op_name}_top_allocations"] = [
                    {
                        'size': stat.size,
                        'count': stat.count,
                        'traceback': str(stat.traceback)
                    }
                    for stat in top_stats[:5]  # Top 5 memory users
                ]
            
        # Allow cleanup
            await asyncio.sleep(0.1)
            
            # Record allocation info
            performance_metrics.memory_usage[f"{op_name}_allocation_info"] = {
                'start_objects': before_objects,
                'end_objects': after_objects,
                'memory_growth': after_mem - before_mem
            }
        
        tracemalloc.stop()
        
        # Verify allocation patterns
        for op_name, alloc_info in performance_metrics.memory_usage.items():
            if op_name.endswith('_allocation_info'):
                memory_growth = alloc_info['memory_growth']
                assert memory_growth < 50 * 1024 * 1024, \
                    f"Excessive memory growth in {op_name}: {memory_growth / 1024 / 1024:.2f}MB"

