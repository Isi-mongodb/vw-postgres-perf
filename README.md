# Aurora PostgreSQL Performance Tester

A **simple, single-file** performance testing tool for AWS Aurora PostgreSQL. Tests read-modify-write operations on realistic vehicle data with real-time metrics.

## ✨ **Features**

- 🚗 **Vehicle Data Model** - Realistic automotive telemetry testing
- 🚀 **High Performance** - Concurrent workers with connection pooling  
- 📊 **Real-time Metrics** - Live throughput and latency reporting
- 🎯 **VIN-based Operations** - Authentic vehicle identification workflows
- ⚡ **Single File** - No complex configuration, just one Python file
- 📈 **Comprehensive Stats** - Average, P95, P99 latency metrics

## 🏃 **Quick Start**

### **1. Install**
```bash
git clone <this-repo>
cd aurora_perf
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **2. Run Test**
```bash
python aurora_perf.py \
  --host your-aurora-cluster.cluster-xyz.region.rds.amazonaws.com \
  --password your-password \
  --workers 10 \
  --duration 60
```

### **3. Example Output**
```
🚗 Aurora PostgreSQL Vehicle Performance Tester
==================================================
Target: database-1.cluster-c7qrltnpbuzd.eu-central-1.rds.amazonaws.com:5432/postgres
✅ Database connection established
✅ Table populated: 10,000 total records

📊 Ops: 6,832 | Success: 100.0% | Throughput: 113.7 ops/s | 
Latency: avg=67.9ms, p95=105.8ms | Runtime: 60.1s

🎊 Outstanding! Your Aurora cluster achieved 113.7 ops/sec!
```

## ⚙️ **Configuration Options**

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--host` | Required | Aurora cluster endpoint |
| `--port` | 5432 | Database port |
| `--database` | postgres | Database name |
| `--username` | postgres | Database username |
| `--password` | Required | Database password |
| `--workers` | 10 | Concurrent workers |
| `--duration` | 60 | Test duration (seconds) |
| `--pool-size` | 50 | Connection pool size |
| `--table-name` | vehicles | Test table name |
| `--initial-records` | 10000 | Records to create |
| `--recreate-table` | false | Drop/recreate table |

## 🔧 **Advanced Usage**

### **High Concurrency Test**
```bash
python aurora_perf.py \
  --host your-cluster-endpoint \
  --password your-password \
  --workers 50 \
  --duration 300 \
  --pool-size 100
```

### **Fresh Table Test**
```bash
python aurora_perf.py \
  --host your-cluster-endpoint \
  --password your-password \
  --recreate-table \
  --initial-records 50000
```

### **Quick Test**
```bash
python aurora_perf.py \
  --host your-cluster-endpoint \
  --password your-password \
  --workers 5 \
  --duration 30
```

## 🗄️ **What It Tests**

The tool performs realistic vehicle data operations:

1. **VIN Selection** - Random vehicle identification number selection
2. **Data Read** - Fetch vehicle record with compressed telemetry
3. **Data Modification** - Update sensor readings, diagnostics, timestamps
4. **Data Write** - Save modified telemetry back to database
5. **Metrics Collection** - Record latency and success rates

### **Vehicle Data Schema**
```sql
CREATE TABLE vehicles (
    vin VARCHAR(17) PRIMARY KEY,           -- Vehicle ID
    brand VARCHAR(50) NOT NULL,            -- Manufacturer  
    country CHAR(2) NOT NULL,              -- Country code
    created_at TIMESTAMP WITH TIME ZONE,   -- Creation time
    updated_at TIMESTAMP WITH TIME ZONE,   -- Last update
    entries_compressed TEXT NOT NULL,      -- Base64 telemetry data
    is_fleet_vehicle BOOLEAN               -- Fleet flag
);
```

## 📊 **Performance Metrics**

- **Throughput**: Operations per second
- **Latency**: Average, min, max, P95, P99 response times  
- **Success Rate**: Percentage of successful operations
- **Concurrency**: Active worker performance
- **Real-time Updates**: Live metrics every 10 seconds

## 🔒 **Aurora Setup Requirements**

1. **Security Groups**: Allow inbound connections on port 5432
2. **Public Access**: Enable if testing from outside VPC
3. **Credentials**: Valid PostgreSQL username/password
4. **Networking**: Ensure connectivity from your test location

### **Test Connection**
```bash
# Verify basic connectivity first
python -c "import asyncpg; print('asyncpg ready')"
```

## 🎯 **Expected Performance**

| Aurora Instance | Expected Throughput |
|-----------------|-------------------|
| t3.medium | 20-50 ops/sec |
| r5.large | 50-150 ops/sec |
| r5.xlarge+ | 150+ ops/sec |

*Results vary based on network latency, Aurora configuration, and workload complexity.*

## 🚀 **Why This Tool?**

- **Single File**: No complex setup or configuration files
- **Realistic Workload**: Actual vehicle data patterns, not synthetic tests
- **Production-Ready**: SSL connections, proper error handling
- **Immediate Results**: Start testing in under 2 minutes
- **Comprehensive**: All metrics you need in one place

## 📝 **Requirements**

- **Python 3.7+**
- **asyncpg** (PostgreSQL async driver)
- **Aurora PostgreSQL** cluster with network access

## 📄 **License**

MIT License - Use freely for testing your Aurora clusters!