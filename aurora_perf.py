#!/usr/bin/env python3
"""
Aurora PostgreSQL Performance Testing Tool - Simplified Version
Tests read-modify-write operations on vehicle data with real-time metrics.
"""

import asyncio
import asyncpg
import os
import random
import string
import time
import statistics
from dataclasses import dataclass
from typing import List, Optional, Tuple
from collections import deque
import argparse


@dataclass
class TestConfig:
    """Simple test configuration."""
    host: str
    port: int = 5432
    database: str = "postgres"
    username: str = "postgres"
    password: str = ""
    ssl_mode: str = "require"
    
    # Test settings
    workers: int = 10
    duration: int = 60
    pool_size: int = 50
    table_name: str = "vehicles"
    
    # Data settings
    initial_records: int = 10000000
    recreate_table: bool = False


@dataclass
class TestResult:
    """Test operation result."""
    success: bool
    duration: float
    timestamp: float
    worker_id: int = 0


class AuroraPerformanceTester:
    """Main Aurora performance testing class."""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.pool: Optional[asyncpg.Pool] = None
        self.results: deque = deque(maxlen=1000)
        self.total_operations = 0
        self.successful_operations = 0
        self.failed_operations = 0
        self.start_time = None
        self.running = False
        
        # Vehicle data for realistic testing
        self.brands = ['Porsche', 'BMW', 'Mercedes-Benz', 'Audi', 'Toyota', 
                      'Honda', 'Ford', 'Chevrolet', 'Volkswagen', 'Nissan']
        self.countries = ['DE', 'US', 'JP', 'UK', 'FR', 'IT', 'KR', 'SE', 'CZ', 'ES']
    
    async def initialize(self):
        """Initialize database connection and setup."""
        print(f"🔗 Connecting to Aurora: {self.config.host}:{self.config.port}/{self.config.database}")
        
        try:
            self.pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                ssl=self.config.ssl_mode,
                min_size=5,
                max_size=self.config.pool_size,
                command_timeout=30
            )
            
            print("✅ Database connection established")
            await self.setup_test_table()
            
        except Exception as e:
            print(f"❌ Failed to initialize: {e}")
            raise
    
    async def setup_test_table(self):
        """Create and populate test table."""
        async with self.pool.acquire() as conn:
            # Check if table exists
            table_exists = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = $1)",
                self.config.table_name
            )
            
            # Drop table if recreate is requested
            if table_exists and self.config.recreate_table:
                print(f"🗑️  Dropping existing table '{self.config.table_name}'...")
                await conn.execute(f"DROP TABLE {self.config.table_name}")
                table_exists = False
            
            if not table_exists:
                print(f"📋 Creating table '{self.config.table_name}'...")
                
                # Create table with proper schema
                await conn.execute(f"""
                    CREATE TABLE {self.config.table_name} (
                        vin VARCHAR(17) PRIMARY KEY,
                        brand VARCHAR(50) NOT NULL,
                        country CHAR(2) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        entries_compressed BYTEA NOT NULL,
                        is_fleet_vehicle BOOLEAN DEFAULT false
                    )
                """)
                
                # Create indexes
                await conn.execute(f"CREATE INDEX idx_{self.config.table_name}_brand ON {self.config.table_name}(brand)")
                await conn.execute(f"CREATE INDEX idx_{self.config.table_name}_country ON {self.config.table_name}(country)")
                
                print(f"✅ Table '{self.config.table_name}' created")
                
                # Populate with test data
                await self.populate_test_data(conn)
            else:
                # Check if we have enough data
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.config.table_name}")
                if count < 1000:
                    print(f"📊 Adding more test data (current: {count})...")
                    await self.populate_test_data(conn, target=self.config.initial_records)
                else:
                    print(f"✅ Table '{self.config.table_name}' ready ({count:,} records)")
    
    async def populate_test_data(self, conn, target: int = None):
        """Populate table with realistic vehicle data."""
        if target is None:
            target = self.config.initial_records
            
        current_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.config.table_name}")
        needed = max(0, target - current_count)
        
        if needed == 0:
            return
            
        print(f"📝 Generating {needed:,} vehicle records...")
        
        # Generate test data in batches
        batch_size = 1000
        for i in range(0, needed, batch_size):
            batch_data = []
            for j in range(min(batch_size, needed - i)):
                vin = self.generate_vin(current_count + i + j)
                brand = random.choice(self.brands)
                country = random.choice(self.countries)
                
                # Generate random binary blob for telemetry data
                compressed_data = os.urandom(1024)
                is_fleet = random.choice([True, False])
                
                batch_data.append((vin, brand, country, compressed_data, is_fleet))
            
            # Insert batch with explicit timestamps
            await conn.executemany(f"""
                INSERT INTO {self.config.table_name} 
                (vin, brand, country, entries_compressed, is_fleet_vehicle, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                ON CONFLICT (vin) DO NOTHING
            """, batch_data)
        
        final_count = await conn.fetchval(f"SELECT COUNT(*) FROM {self.config.table_name}")
        print(f"✅ Table populated: {final_count:,} total records")
    
    def generate_vin(self, index: int) -> str:
        """Generate a realistic VIN."""
        wmi_prefixes = ['WP0', '1HG', 'WBA', 'JTD', 'WVW', '1G1', 'KNA', 'YV1', 'TMB', 'VF3']
        wmi = random.choice(wmi_prefixes)
        
        valid_chars = string.ascii_uppercase.replace('I', '').replace('O', '').replace('Q', '') + string.digits
        remaining = ''.join(random.choices(valid_chars, k=14))
        
        return f"{wmi}{remaining[:-6]}{index:06d}"[:17]
    
    async def get_random_vin(self) -> Optional[str]:
        """Get a random VIN from the database."""
        async with self.pool.acquire() as conn:
            return await conn.fetchval(f"SELECT vin FROM {self.config.table_name} ORDER BY RANDOM() LIMIT 1")
    
    def modify_vehicle_data(self, original_data: bytes, brand: str, vin: str) -> bytes:
        """Generate new random binary blob for vehicle telemetry data."""
        # Since we now use random binary blobs instead of structured data,
        # we simply generate a new random blob rather than modifying existing data
        return os.urandom(1024)
    
    async def perform_operation(self, worker_id: int) -> TestResult:
        """Perform a single read-modify-write operation."""
        start_time = time.time()
        
        try:
            async with self.pool.acquire() as conn:
                # Get random vehicle
                vin = await conn.fetchval(f"SELECT vin FROM {self.config.table_name} ORDER BY RANDOM() LIMIT 1")
                if not vin:
                    return TestResult(False, time.time() - start_time, start_time, worker_id)
                
                # Read vehicle data
                row = await conn.fetchrow(
                    f"SELECT vin, entries_compressed, brand FROM {self.config.table_name} WHERE vin = $1",
                    vin
                )
                
                if not row:
                    return TestResult(False, time.time() - start_time, start_time, worker_id)
                
                # Modify data
                modified_data = self.modify_vehicle_data(row['entries_compressed'], row['brand'], row['vin'])
                
                # Write back
                await conn.execute(
                    f"UPDATE {self.config.table_name} SET entries_compressed = $1, updated_at = NOW() WHERE vin = $2",
                    modified_data, vin
                )
                
                return TestResult(True, time.time() - start_time, start_time, worker_id)
                
        except Exception as e:
            return TestResult(False, time.time() - start_time, start_time, worker_id)
    
    async def worker(self, worker_id: int):
        """Individual worker performing operations."""
        operations = 0
        
        while self.running and time.time() < self.start_time + self.config.duration:
            result = await self.perform_operation(worker_id)
            
            # Record result
            self.results.append(result)
            self.total_operations += 1
            if result.success:
                self.successful_operations += 1
            else:
                self.failed_operations += 1
            
            operations += 1
        
        print(f"   Worker {worker_id}: {operations:,} operations")
    
    async def metrics_reporter(self):
        """Report metrics periodically."""
        while self.running:
            await asyncio.sleep(10)
            if not self.running:
                break
                
            elapsed = time.time() - self.start_time
            throughput = self.total_operations / elapsed if elapsed > 0 else 0
            success_rate = (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0
            
            # Calculate latency stats
            if self.results:
                recent_latencies = [r.duration * 1000 for r in list(self.results)[-100:]]  # Last 100 ops
                avg_latency = statistics.mean(recent_latencies)
                p95_latency = statistics.quantiles(recent_latencies, n=20)[18] if len(recent_latencies) > 1 else avg_latency
            else:
                avg_latency = p95_latency = 0
            
            print(f"📊 Ops: {self.total_operations:,} | Success: {success_rate:.1f}% | "
                  f"Throughput: {throughput:.1f} ops/s | "
                  f"Latency: avg={avg_latency:.1f}ms, p95={p95_latency:.1f}ms | "
                  f"Runtime: {elapsed:.1f}s")
    
    async def run_test(self):
        """Run the performance test."""
        print(f"\n🚀 Starting performance test:")
        print(f"   • Workers: {self.config.workers}")
        print(f"   • Duration: {self.config.duration}s")
        print(f"   • Target table: {self.config.table_name}")
        print()
        
        self.running = True
        self.start_time = time.time()
        
        # Start workers and metrics reporter
        tasks = []
        
        # Start workers
        for i in range(self.config.workers):
            tasks.append(asyncio.create_task(self.worker(i)))
        
        # Start metrics reporter
        tasks.append(asyncio.create_task(self.metrics_reporter()))
        
        try:
            # Wait for test duration
            await asyncio.sleep(self.config.duration)
            
        finally:
            self.running = False
            
            # Wait for all tasks to complete
            await asyncio.gather(*tasks, return_exceptions=True)
            
            # Final results
            await self.print_final_results()
    
    async def print_final_results(self):
        """Print final test results."""
        elapsed = time.time() - self.start_time
        throughput = self.total_operations / elapsed if elapsed > 0 else 0
        success_rate = (self.successful_operations / self.total_operations * 100) if self.total_operations > 0 else 0
        
        # Calculate comprehensive latency stats
        if self.results:
            latencies = [r.duration * 1000 for r in self.results]
            avg_latency = statistics.mean(latencies)
            min_latency = min(latencies)
            max_latency = max(latencies)
            p95_latency = statistics.quantiles(latencies, n=20)[18] if len(latencies) > 1 else avg_latency
            p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 1 else avg_latency
        else:
            avg_latency = min_latency = max_latency = p95_latency = p99_latency = 0
        
        print("\n" + "="*60)
        print("🎉 AURORA PERFORMANCE TEST RESULTS")
        print("="*60)
        print(f"📈 Total Operations:        {self.total_operations:,}")
        print(f"✅ Successful Operations:   {self.successful_operations:,}")
        print(f"❌ Failed Operations:       {self.failed_operations:,}")
        print(f"📊 Success Rate:            {success_rate:.1f}%")
        print(f"🚀 Average Throughput:      {throughput:.1f} operations/second")
        print(f"⏱️  Test Duration:           {elapsed:.1f}s")
        print()
        print("LATENCY METRICS:")
        print(f"   • Average:               {avg_latency:.1f}ms")
        print(f"   • Minimum:               {min_latency:.1f}ms")
        print(f"   • Maximum:               {max_latency:.1f}ms")
        print(f"   • 95th Percentile:       {p95_latency:.1f}ms")
        print(f"   • 99th Percentile:       {p99_latency:.1f}ms")
        print()
        print("VEHICLE DATA OPERATIONS:")
        print(f"   • VIN-based selections:   {self.total_operations:,}")
        print(f"   • Telemetry modifications: {self.successful_operations:,}")
        print(f"   • Database updates:       {self.successful_operations:,}")
        
        if throughput > 100:
            print(f"\n🎊 Outstanding! Your Aurora cluster achieved {throughput:.1f} ops/sec!")
        elif throughput > 50:
            print(f"\n🎯 Excellent performance: {throughput:.1f} ops/sec")
        elif throughput > 20:
            print(f"\n👍 Good performance: {throughput:.1f} ops/sec")
        else:
            print(f"\n💡 Consider Aurora instance scaling for better performance")
        
        print("="*60)
    
    async def close(self):
        """Clean up resources."""
        if self.pool:
            await self.pool.close()
            print("✅ Database connections closed")


async def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Aurora PostgreSQL Performance Testing Tool")
    parser.add_argument("--host", required=True, help="Aurora cluster host")
    parser.add_argument("--port", type=int, default=5432, help="Database port")
    parser.add_argument("--database", default="postgres", help="Database name")
    parser.add_argument("--username", default="postgres", help="Database username")
    parser.add_argument("--password", required=True, help="Database password")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--pool-size", type=int, default=50, help="Connection pool size")
    parser.add_argument("--table-name", default="vehicles", help="Table name")
    parser.add_argument("--initial-records", type=int, default=10000000, help="Initial records to create")
    parser.add_argument("--recreate-table", action="store_true", help="Drop and recreate table if it exists")
    
    args = parser.parse_args()
    
    # Create configuration
    config = TestConfig(
        host=args.host,
        port=args.port,
        database=args.database,
        username=args.username,
        password=args.password,
        workers=args.workers,
        duration=args.duration,
        pool_size=args.pool_size,
        table_name=args.table_name,
        initial_records=args.initial_records,
        recreate_table=args.recreate_table
    )
    
    print("🚗 Aurora PostgreSQL Vehicle Performance Tester")
    print("="*50)
    print(f"Target: {config.host}:{config.port}/{config.database}")
    print(f"Table: {config.table_name}")
    print(f"Configuration: {config.workers} workers, {config.duration}s duration")
    
    tester = None
    try:
        tester = AuroraPerformanceTester(config)
        await tester.initialize()
        await tester.run_test()
        
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if tester:
            await tester.close()


if __name__ == "__main__":
    asyncio.run(main())
