#!/usr/bin/env python3
"""
Port checker utility - Find and manage processes using ports in a range
"""

import subprocess
import sys
import argparse
from typing import List, Tuple, Optional
import re


def get_listening_ports(start_port: int, end_port: int) -> List[Tuple[int, str, int]]:
    """
    Get all listening ports in the specified range
    Returns list of (port, process_name, pid) tuples
    """
    ports_info = []
    
    try:
        # Use lsof to get port information
        cmd = f"lsof -i -P -n | grep LISTEN"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 9:
                    process_name = parts[0]
                    pid = int(parts[1])
                    address = parts[8]
                    
                    # Extract port number
                    port_match = re.search(r':(\d+)$', address)
                    if port_match:
                        port = int(port_match.group(1))
                        if start_port <= port <= end_port:
                            ports_info.append((port, process_name, pid))
    
    except Exception as e:
        print(f"Error with lsof: {e}", file=sys.stderr)
        
        # Fallback to ss command
        try:
            cmd = "ss -tulpn | grep LISTEN"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            for line in result.stdout.strip().split('\n'):
                # Parse ss output
                port_match = re.search(r':(\d+)\s', line)
                if port_match:
                    port = int(port_match.group(1))
                    if start_port <= port <= end_port:
                        # Try to get process info
                        process_match = re.search(r'users:\(\("([^"]+)",pid=(\d+)', line)
                        if process_match:
                            process_name = process_match.group(1)
                            pid = int(process_match.group(2))
                        else:
                            process_name = "unknown"
                            pid = 0
                        ports_info.append((port, process_name, pid))
        except Exception as e2:
            print(f"Error with ss: {e2}", file=sys.stderr)
    
    return sorted(ports_info, key=lambda x: x[0])


def kill_port(port: int) -> bool:
    """Kill process using specified port"""
    try:
        # Get PID using lsof
        cmd = f"lsof -ti:{port}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.stdout:
            pid = result.stdout.strip()
            kill_cmd = f"kill {pid}"
            subprocess.run(kill_cmd, shell=True)
            print(f"✓ Killed process {pid} on port {port}")
            return True
        else:
            print(f"✗ No process found on port {port}")
            return False
    except Exception as e:
        print(f"✗ Error killing port {port}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Check and manage ports in use')
    parser.add_argument('start', type=int, nargs='?', default=8000,
                       help='Start port (default: 8000)')
    parser.add_argument('end', type=int, nargs='?', default=9000,
                       help='End port (default: 9000)')
    parser.add_argument('-k', '--kill', type=int, metavar='PORT',
                       help='Kill process on specified port')
    parser.add_argument('-a', '--all', action='store_true',
                       help='Show all ports (not just in range)')
    
    args = parser.parse_args()
    
    if args.kill:
        kill_port(args.kill)
        return
    
    print(f"\n🔍 Checking ports {args.start}-{args.end}...")
    print("=" * 60)
    
    ports = get_listening_ports(args.start, args.end)
    
    if not ports:
        print(f"✓ No ports in use between {args.start}-{args.end}")
    else:
        print(f"Found {len(ports)} port(s) in use:\n")
        print(f"{'Port':<10} {'Process':<20} {'PID':<10} {'Action'}")
        print("-" * 60)
        
        for port, process, pid in ports:
            kill_cmd = f"kill {pid}" if pid > 0 else "N/A"
            print(f"{port:<10} {process:<20} {pid:<10} {kill_cmd}")
        
        print("\n💡 Tips:")
        print(f"  • Kill a specific port:  python {sys.argv[0]} -k PORT")
        print(f"  • Kill by PID:           kill PID")
        print(f"  • Force kill:            kill -9 PID")
        print(f"  • Kill all in range:     lsof -ti:{args.start}-{args.end} | xargs kill")
    
    # Also show commonly used development ports
    print("\n📊 Common development ports status:")
    common_ports = {
        3000: "React/Node.js",
        5000: "Flask",
        5432: "PostgreSQL", 
        6379: "Redis",
        8000: "Django/FastAPI",
        8010: "MCP API",
        8080: "Alternative HTTP",
        8090: "MCP Web UI",
        9000: "PHP/Monitoring",
    }
    
    for port, description in common_ports.items():
        # Quick check if port is open
        cmd = f"(timeout 0.1 bash -c 'echo > /dev/tcp/localhost/{port}' 2>/dev/null && echo OPEN) || echo FREE"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        status = result.stdout.strip()
        
        symbol = "🔴" if status == "OPEN" else "🟢"
        print(f"  {symbol} {port:<5} ({description:<15}): {status}")


if __name__ == "__main__":
    main()