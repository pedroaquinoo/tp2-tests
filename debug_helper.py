#!/usr/bin/env python3
"""
Aviator Debug Helper
Quick debugging utilities for the Aviator game
"""

import subprocess
import sys
import time
import threading
from test import AviatorTestClient

def quick_connection_test(port=8080):
    """Quick test to see if server is responsive"""
    print(f"🔍 Testing connection to localhost:{port}")
    
    client = AviatorTestClient('127.0.0.1', port, 'DebugClient', debug=True)
    
    def run_client():
        client.run()
    
    thread = threading.Thread(target=run_client)
    thread.daemon = True
    thread.start()
    
    time.sleep(5)
    client.running = False
    thread.join(timeout=2)
    
    print(f"📊 Results:")
    print(f"   Connected: {client.connection_success}")
    print(f"   Messages received: {len(client.last_messages)}")
    if client.last_messages:
        print(f"   Last message types: {[msg['type'] for msg in client.last_messages[-5:]]}")

def struct_size_test():
    """Test struct size compatibility"""
    print("🔍 Testing struct size compatibility")
    
    client = AviatorTestClient('127.0.0.1', 0, 'TestClient')
    
    # Test message packing
    test_msg = client.pack_message(1, 50.0, 'bet', 0.0, 0.0)
    print(f"   Packed message size: {len(test_msg)} bytes")
    print(f"   Expected size: 28 bytes")
    
    if len(test_msg) == 28:
        print("   ✅ Struct size is correct")
        
        # Test unpacking
        unpacked = client.unpack_message(test_msg)
        if unpacked:
            print(f"   ✅ Unpacking successful: {unpacked}")
        else:
            print("   ❌ Unpacking failed")
    else:
        print("   ❌ Struct size mismatch")

def server_logs_test(port=51511, duration=10):
    """Start server and show logs for a specified duration"""
    print(f"🔍 Starting server on port {port} for {duration} seconds")
    
    try:
        server_process = subprocess.Popen(
            ['./bin/server', 'v4', str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        print("📊 Server output:")
        start_time = time.time()
        
        while time.time() - start_time < duration:
            if server_process.poll() is not None:
                print("   Server process terminated")
                break
                
            try:
                line = server_process.stdout.readline()
                if line:
                    print(f"   {line.strip()}")
            except:
                break
                
            time.sleep(0.1)
        
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
        except:
            server_process.kill()
            
        print("✅ Server test completed")
        
    except Exception as e:
        print(f"❌ Server test failed: {e}")

def run_single_client_scenario(port=51511):
    """Run a single client through a complete game scenario"""
    print(f"🔍 Running single client scenario on port {port}")
    
    client = AviatorTestClient('127.0.0.1', port, 'ScenarioClient', debug=True)
    
    # Program a complete scenario
    client.add_action('betting_open', 'bet', amount=25.0, delay=2.0)
    client.add_action('multiplier_reached', 'cashout', multiplier=1.50)
    
    def run_client():
        client.run()
    
    thread = threading.Thread(target=run_client)
    thread.daemon = True
    thread.start()
    
    # Wait for scenario to complete
    time.sleep(20)
    client.running = False
    thread.join(timeout=2)
    
    print(f"📊 Scenario Results:")
    print(f"   Connected: {client.connection_success}")
    print(f"   Total messages: {len(client.last_messages)}")
    print(f"   Message types seen: {list(set(msg['type'] for msg in client.last_messages))}")
    
    # Check for key events
    events = {
        'start': any(msg['type'] == 'start' for msg in client.last_messages),
        'closed': any(msg['type'] == 'closed' for msg in client.last_messages),
        'multiplier': any(msg['type'] == 'multiplier' for msg in client.last_messages),
        'payout': any(msg['type'] == 'payout' for msg in client.last_messages),
        'explode': any(msg['type'] == 'explode' for msg in client.last_messages),
    }
    
    for event, seen in events.items():
        status = "✅" if seen else "❌"
        print(f"   {status} {event} event")

def main():
    """Main debug menu"""
    if len(sys.argv) < 2:
        print("🛠️ Aviator Debug Helper")
        print("Usage:")
        print("  python3 debug_helper.py connection [port]     - Test connection")
        print("  python3 debug_helper.py struct               - Test struct compatibility")
        print("  python3 debug_helper.py server [port] [dur]  - Show server logs")
        print("  python3 debug_helper.py scenario [port]      - Run single client scenario")
        print("")
        print("Examples:")
        print("  python3 debug_helper.py connection 8080")
        print("  python3 debug_helper.py server 51511 15")
        print("  python3 debug_helper.py scenario 51511")
        return

    command = sys.argv[1]
    
    if command == 'connection':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        quick_connection_test(port)
        
    elif command == 'struct':
        struct_size_test()
        
    elif command == 'server':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 51511
        duration = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        server_logs_test(port, duration)
        
    elif command == 'scenario':
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 51511
        run_single_client_scenario(port)
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Run without arguments to see usage")

if __name__ == '__main__':
    main() 