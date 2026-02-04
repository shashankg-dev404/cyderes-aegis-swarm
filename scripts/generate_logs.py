"""
Day 1: Security Logs Data Lake Generator
Generates 50k realistic firewall logs with embedded attack patterns
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path
from faker import Faker

# Initialize Faker
fake = Faker()

# Configuration
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "raw"
OUTPUT_FILE = OUTPUT_DIR / "firewall_logs.csv"
TOTAL_RECORDS = 50000

# Attack patterns for multi-agent detection
ATTACK_PATTERNS = {
    "sql_injection": {
        "user_agents": ["sqlmap/1.0", "Nikto/2.1.5", "ZmEu", "acunetix/13.0"],
        "paths": [
            "/login.php?id=1' OR '1'='1",
            "/admin/users?id=1 UNION SELECT password FROM users--",
            "/search?q='; DROP TABLE users; --",
            "/api/user?id=1' AND 1=1--"
        ],
        "status_codes": [403, 500, 400, 200]
    },
    "brute_force": {
        "paths": ["/wp-login.php", "/admin/login", "/api/auth", "/ssh"],
        "status_codes": [401, 403, 200],
        "usernames": ["admin", "root", "test", "user", "administrator"]
    },
    "port_scan": {
        "ports": list(range(20, 100)),  # Sequential scanning
        "protocol": "TCP"
    },
    "data_exfil": {
        "paths": ["/api/export/all", "/download/database.sql", "/backup/users.csv"],
        "data_size_mb": [100, 250, 500, 1000, 2000]
    },
    "dos_attack": {
        "paths": ["/", "/api/search", "/products"],
        "request_rate": "extreme"  # 1000+ requests per minute
    }
}

# Known malicious IPs (real TOR exit nodes and known scanners)
MALICIOUS_IPS = [
    "45.155.205.0", "185.220.101.17", "23.129.64.100",
    "198.98.54.71", "162.247.74.27", "185.100.87.41"
]

# Known benign IPs
BENIGN_IPS = ["8.8.8.8", "1.1.1.1", "192.168.1.100", "10.0.0.50", "172.16.0.10"]


def generate_timestamp(base_time, offset_seconds):
    """Generate ISO timestamp with offset"""
    return (base_time + timedelta(seconds=offset_seconds)).isoformat()


def generate_benign_traffic(base_time, record_num):
    """Generate normal user traffic (70% of dataset)"""
    return {
        "timestamp": generate_timestamp(base_time, record_num * 10),
        "source_ip": fake.ipv4_private() if random.random() > 0.3 else random.choice(BENIGN_IPS),
        "dest_ip": fake.ipv4(),
        "source_port": random.randint(1024, 65535),
        "dest_port": random.choice([80, 443, 8080, 8443]),
        "protocol": "TCP",
        "action": "ALLOW",
        "bytes_sent": random.randint(500, 5000),
        "bytes_received": random.randint(1000, 10000),
        "user_agent": fake.user_agent(),
        "request_path": random.choice(["/", "/home", "/products", "/api/status", "/about"]),
        "http_status": 200,
        "session_id": fake.uuid4(),
        "alert_type": "benign"
    }


def generate_sql_injection(base_time, record_num):
    """SQL Injection attack - Intel Agent should flag malicious IPs"""
    pattern = ATTACK_PATTERNS["sql_injection"]
    return {
        "timestamp": generate_timestamp(base_time, record_num * 10),
        "source_ip": random.choice(MALICIOUS_IPS),
        "dest_ip": "192.168.10.5",  # Internal web server
        "source_port": random.randint(40000, 60000),
        "dest_port": 443,
        "protocol": "TCP",
        "action": random.choice(["BLOCK", "ALLOW"]),  # Some get through
        "bytes_sent": random.randint(200, 800),
        "bytes_received": random.randint(0, 5000),
        "user_agent": random.choice(pattern["user_agents"]),
        "request_path": random.choice(pattern["paths"]),
        "http_status": random.choice(pattern["status_codes"]),
        "session_id": fake.uuid4(),
        "alert_type": "sql_injection"
    }


def generate_brute_force(base_time, record_num, attack_ip, username):
    """Brute Force attack - Analyst Agent should detect 500+ attempts from same IP"""
    pattern = ATTACK_PATTERNS["brute_force"]
    return {
        "timestamp": generate_timestamp(base_time, record_num * 2),  # Rapid requests
        "source_ip": attack_ip,
        "dest_ip": "192.168.10.10",  # Login server
        "source_port": random.randint(50000, 60000),
        "dest_port": 443,
        "protocol": "TCP",
        "action": "ALLOW",
        "bytes_sent": random.randint(100, 300),
        "bytes_received": random.randint(200, 500),
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "request_path": f"{random.choice(pattern['paths'])}?username={username}",
        "http_status": random.choice(pattern["status_codes"]),
        "session_id": fake.uuid4(),
        "alert_type": "brute_force"
    }


def generate_port_scan(base_time, record_num, scanner_ip, target_port):
    """Port Scanning - Analyst Agent should detect sequential port probing"""
    return {
        "timestamp": generate_timestamp(base_time, record_num),
        "source_ip": scanner_ip,
        "dest_ip": "192.168.10.1",  # Gateway/Firewall
        "source_port": random.randint(55000, 65000),
        "dest_port": target_port,
        "protocol": "TCP",
        "action": "BLOCK",
        "bytes_sent": 60,  # SYN packet
        "bytes_received": 0,
        "user_agent": "N/A",
        "request_path": "N/A",
        "http_status": 0,
        "session_id": "N/A",
        "alert_type": "port_scan"
    }


def generate_data_exfil(base_time, record_num):
    """Data Exfiltration - Analyst Agent should detect large uploads to external IPs"""
    pattern = ATTACK_PATTERNS["data_exfil"]
    return {
        "timestamp": generate_timestamp(base_time, record_num * 10),
        "source_ip": "192.168.5.77",  # Compromised internal host
        "dest_ip": random.choice(MALICIOUS_IPS),
        "source_port": random.randint(50000, 60000),
        "dest_port": 443,
        "protocol": "TCP",
        "action": "ALLOW",
        "bytes_sent": random.choice(pattern["data_size_mb"]) * 1024 * 1024,
        "bytes_received": random.randint(200, 500),
        "user_agent": random.choice(["curl/7.68.0", "python-requests/2.28.0", "wget/1.20.3"]),
        "request_path": random.choice(pattern["paths"]),
        "http_status": 200,
        "session_id": fake.uuid4(),
        "alert_type": "data_exfiltration"
    }


def generate_dos_attack(base_time, record_num, attacker_ip):
    """DoS Attack - Analyst Agent should detect high request rate from single IP"""
    pattern = ATTACK_PATTERNS["dos_attack"]
    return {
        "timestamp": generate_timestamp(base_time, record_num * 0.5),  # Very rapid
        "source_ip": attacker_ip,
        "dest_ip": "192.168.10.5",
        "source_port": random.randint(10000, 60000),
        "dest_port": 80,
        "protocol": "TCP",
        "action": random.choice(["ALLOW", "BLOCK"]),
        "bytes_sent": random.randint(50, 200),
        "bytes_received": random.randint(0, 1000),
        "user_agent": "N/A",
        "request_path": random.choice(pattern["paths"]),
        "http_status": random.choice([200, 503, 429]),
        "session_id": "N/A",
        "alert_type": "dos_attack"
    }


def main():
    """Generate the complete security logs dataset"""
    print("=" * 70)
    print("CYDERES AEGIS SWARM - DAY 1: DATA LAKE GENERATION")
    print("=" * 70)
    print(f"\n🎯 Target: {TOTAL_RECORDS:,} records")
    print(f"📁 Output: {OUTPUT_FILE}")
    
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Base timestamp (7 days ago)
    base_time = datetime.now() - timedelta(days=7)
    
    logs = []
    
    # 1. Generate 65% benign traffic
    benign_count = int(TOTAL_RECORDS * 0.65)
    print(f"\n🟢 Generating {benign_count:,} benign records...")
    for i in range(benign_count):
        logs.append(generate_benign_traffic(base_time, i))
    
    # 2. Generate 12% SQL injection attempts
    sql_injection_count = int(TOTAL_RECORDS * 0.12)
    print(f"🔴 Generating {sql_injection_count:,} SQL injection records...")
    for i in range(sql_injection_count):
        logs.append(generate_sql_injection(base_time, benign_count + i))
    
    # 3. Generate 10% Brute force (concentrated from 3 IPs, each trying different usernames)
    brute_force_count = int(TOTAL_RECORDS * 0.10)
    brute_force_ips = ["89.248.172.16", "103.253.145.28", "194.26.192.64"]
    print(f"🔴 Generating {brute_force_count:,} brute force records from {len(brute_force_ips)} IPs...")
    for i in range(brute_force_count):
        attack_ip = brute_force_ips[i % len(brute_force_ips)]
        username = random.choice(ATTACK_PATTERNS["brute_force"]["usernames"])
        logs.append(generate_brute_force(base_time, benign_count + sql_injection_count + i, attack_ip, username))
    
    # 4. Generate 5% Port scanning (2 IPs, sequential ports)
    port_scan_count = int(TOTAL_RECORDS * 0.05)
    port_scanners = ["198.50.201.145", "104.244.79.196"]
    print(f"🔴 Generating {port_scan_count:,} port scan records from {len(port_scanners)} IPs...")
    for i in range(port_scan_count):
        scanner_ip = port_scanners[i % len(port_scanners)]
        target_port = 20 + (i % 80)  # Ports 20-99
        logs.append(generate_port_scan(base_time, benign_count + sql_injection_count + brute_force_count + i, scanner_ip, target_port))
    
    # 5. Generate 3% Data exfiltration
    data_exfil_count = int(TOTAL_RECORDS * 0.03)
    print(f"🔴 Generating {data_exfil_count:,} data exfiltration records...")
    for i in range(data_exfil_count):
        logs.append(generate_data_exfil(base_time, len(logs)))
    
    # 6. Generate 5% DoS attacks (2 attacker IPs)
    dos_count = TOTAL_RECORDS - len(logs)  # Remaining records
    dos_attackers = ["172.58.224.198", "91.219.237.244"]
    print(f"🔴 Generating {dos_count:,} DoS attack records from {len(dos_attackers)} IPs...")
    for i in range(dos_count):
        attacker_ip = dos_attackers[i % len(dos_attackers)]
        logs.append(generate_dos_attack(base_time, len(logs), attacker_ip))
    
    # Shuffle to mix attack patterns realistically
    print(f"\n🔀 Shuffling {len(logs):,} records...")
    random.shuffle(logs)
    
    # Write to CSV
    print(f"💾 Writing to {OUTPUT_FILE}...")
    fieldnames = [
        "timestamp", "source_ip", "dest_ip", "source_port", "dest_port",
        "protocol", "action", "bytes_sent", "bytes_received", "user_agent",
        "request_path", "http_status", "session_id", "alert_type"
    ]
    
    with open(OUTPUT_FILE, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(logs)
    
    # Statistics
    file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
    
    print("\n" + "=" * 70)
    print("✅ DATA GENERATION COMPLETE")
    print("=" * 70)
    print(f"\n📊 ATTACK DISTRIBUTION:")
    print(f"   - Benign Traffic:      {benign_count:>6,} ({benign_count/TOTAL_RECORDS*100:>5.1f}%)")
    print(f"   - SQL Injection:       {sql_injection_count:>6,} ({sql_injection_count/TOTAL_RECORDS*100:>5.1f}%)")
    print(f"   - Brute Force:         {brute_force_count:>6,} ({brute_force_count/TOTAL_RECORDS*100:>5.1f}%)")
    print(f"   - Port Scanning:       {port_scan_count:>6,} ({port_scan_count/TOTAL_RECORDS*100:>5.1f}%)")
    print(f"   - Data Exfiltration:   {data_exfil_count:>6,} ({data_exfil_count/TOTAL_RECORDS*100:>5.1f}%)")
    print(f"   - DoS Attacks:         {dos_count:>6,} ({dos_count/TOTAL_RECORDS*100:>5.1f}%)")
    
    print(f"\n📁 FILE INFO:")
    print(f"   - Path: {OUTPUT_FILE}")
    print(f"   - Size: {file_size_mb:.2f} MB")
    print(f"   - Records: {len(logs):,}")
    
    print(f"\n🎯 KEY ATTACK INDICATORS (For Agent Testing):")
    print(f"   - Brute Force IPs: {', '.join(brute_force_ips)}")
    print(f"   - Port Scanners: {', '.join(port_scanners)}")
    print(f"   - DoS Attackers: {', '.join(dos_attackers)}")
    print(f"   - Compromised Internal: 192.168.5.77 (Data Exfil)")
    print(f"   - Known Malicious: {', '.join(MALICIOUS_IPS[:3])}")
    
    print("\n🚀 NEXT STEPS:")
    print("   1. Review the generated CSV: data/raw/firewall_logs.csv")
    print("   2. Upload to Azure Blob Storage: python scripts/upload_to_blob.py")
    print("   3. Day 2: Build the Analyst Agent (Code Interpreter)")
    print("=" * 70)


if __name__ == "__main__":
    main()
