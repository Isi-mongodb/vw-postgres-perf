#!/usr/bin/env python3
"""Debug Aurora connection with detailed error reporting."""

import asyncio
import asyncpg
import socket
import time

async def test_aurora_connection():
    """Test Aurora connection with detailed diagnostics."""
    
    host = "database-1.cluster-c7qrltnpbuzd.eu-central-1.rds.amazonaws.com"
    port = 5432
    database = "postgres"
    username = "postgres"
    password = "hu*fpzXfCK#[e.fup4vtI1U[2|8_"
    
    print("🔍 Aurora PostgreSQL Connection Diagnostics")
    print("=" * 50)
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"Database: {database}")
    print(f"Username: {username}")
    print()
    
    # Test 1: DNS Resolution
    print("1️⃣  Testing DNS resolution...")
    try:
        ip = socket.gethostbyname(host)
        print(f"   ✅ DNS resolved: {host} → {ip}")
    except Exception as e:
        print(f"   ❌ DNS resolution failed: {e}")
        return
    
    # Test 2: Port connectivity
    print("2️⃣  Testing port connectivity...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"   ✅ Port {port} is reachable")
        else:
            print(f"   ❌ Port {port} is not reachable (error code: {result})")
            print("   💡 This suggests firewall/security group issues")
            return
    except Exception as e:
        print(f"   ❌ Port connectivity test failed: {e}")
        return
    
    # Test 3: PostgreSQL connection
    print("3️⃣  Testing PostgreSQL connection...")
    try:
        print("   🔗 Attempting connection...")
        start_time = time.time()
        
        conn = await asyncpg.connect(
            host=host,
            port=port,
            database=database,
            user=username,
            password=password,
            ssl="require",
            command_timeout=15
        )
        
        elapsed = time.time() - start_time
        print(f"   ✅ PostgreSQL connection successful! ({elapsed:.2f}s)")
        
        # Test simple query
        result = await conn.fetchval("SELECT 1")
        print(f"   ✅ Query test successful: {result}")
        
        # Get database info
        version = await conn.fetchval("SELECT version()")
        print(f"   🗄️  Database: {version[:50]}...")
        
        await conn.close()
        print("   ✅ Connection closed")
        
    except asyncpg.InvalidPasswordError:
        print("   ❌ Authentication failed - wrong username/password")
    except asyncpg.InvalidCatalogNameError:
        print(f"   ❌ Database '{database}' does not exist")
    except asyncio.TimeoutError:
        print("   ❌ Connection timeout - likely network/firewall issue")
    except Exception as e:
        error_msg = str(e).lower()
        if "does not exist" in error_msg:
            print(f"   ❌ Database '{database}' does not exist")
        elif "authentication" in error_msg or "password" in error_msg:
            print("   ❌ Authentication failed - wrong username/password")
        else:
            print(f"   ❌ Connection failed: {type(e).__name__}: {e}")
    
    print()
    print("🔧 Troubleshooting Tips:")
    print("- Ensure Aurora security groups allow inbound connections on port 5432")
    print("- Check that Aurora cluster is 'Publicly accessible'")
    print("- Verify you're not behind a corporate firewall blocking port 5432")
    print("- Consider running from an EC2 instance in the same VPC")

if __name__ == '__main__':
    asyncio.run(test_aurora_connection())
