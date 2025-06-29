#!/usr/bin/env python3
"""
Comprehensive Test Suite for Aviator Game
Enhanced with debugging capabilities and protocol fixes
"""
import socket
import struct
import threading
import time
import sys
import subprocess
import random

# Debug settings
DEBUG_VERBOSE = False
DEBUG_MESSAGES = False

def debug_print(msg, level="INFO"):
    """Print debug messages if verbose mode is enabled"""
    if DEBUG_VERBOSE:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {msg}")

def debug_message(direction, client_name, msg_data):
    """Print message debug info if message debugging is enabled"""
    if DEBUG_MESSAGES:
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {direction} {client_name}: {msg_data}")

class AviatorTestClient:
    def __init__(self, server_ip, port, nickname, debug=False):
        self.server_ip = server_ip
        self.port = port
        self.nickname = nickname
        self.socket = None
        self.running = True
        self.betting_phase = False
        self.flight_phase = False
        self.current_multiplier = 1.0
        self.last_messages = []
        self.test_actions = []
        self.action_index = 0
        self.debug = debug or DEBUG_VERBOSE
        self.connection_success = False
        
    def pack_message(self, player_id, value, msg_type, player_profit=0.0, house_profit=0.0):
        """Pack message according to aviator_msg struct - FIXED"""
        # C struct: int32_t(4) + float(4) + char[11](11) + float(4) + float(4) = 27 bytes
        # But due to alignment, it's actually 28 bytes with 1 byte padding after char[11]
        type_bytes = msg_type.encode('utf-8')[:10].ljust(11, b'\0')  # Exactly 11 bytes
        
        data = struct.pack('<i', player_id)      # 4 bytes: player_id
        data += struct.pack('<f', value)         # 4 bytes: value  
        data += type_bytes                       # 11 bytes: type
        data += b'\0'                           # 1 byte: padding for alignment
        data += struct.pack('<f', player_profit) # 4 bytes: player_profit
        data += struct.pack('<f', house_profit)  # 4 bytes: house_profit
        
        if self.debug:
            debug_message("PACK", self.nickname, f"type={msg_type}, value={value}, size={len(data)}")
        
        return data
    
    def unpack_message(self, data):
        """Unpack message from server - FIXED"""
        if len(data) != 28:
            if self.debug:
                debug_print(f"Invalid message size: {len(data)}, expected 28", "ERROR")
            return None
        
        try:
            player_id = struct.unpack('<i', data[0:4])[0]
            value = struct.unpack('<f', data[4:8])[0]
            type_bytes = data[8:19]  # 11 bytes for type field
            # Skip padding byte at position 19
            player_profit = struct.unpack('<f', data[20:24])[0]
            house_profit = struct.unpack('<f', data[24:28])[0]
            
            # Extract string from type_bytes
            null_pos = type_bytes.find(b'\0')
            if null_pos >= 0:
                msg_type = type_bytes[:null_pos].decode('utf-8')
            else:
                msg_type = type_bytes.decode('utf-8').rstrip('\0')
            
            result = {
                'player_id': player_id,
                'value': value,
                'type': msg_type,
                'player_profit': player_profit,
                'house_profit': house_profit
            }
            
            if self.debug:
                debug_message("RECV", self.nickname, result)
            
            return result
        except Exception as e:
            if self.debug:
                debug_print(f"Failed to unpack message: {e}", "ERROR")
            return None
    
    def send_message(self, msg_type, value=0.0):
        """Send message to server"""
        if not self.socket:
            if self.debug:
                debug_print(f"Cannot send {msg_type}: no socket", "ERROR")
            return False
            
        try:
            msg_data = self.pack_message(0, value, msg_type)
            total_sent = 0
            while total_sent < len(msg_data):
                sent = self.socket.send(msg_data[total_sent:])
                if sent == 0:
                    if self.debug:
                        debug_print(f"Socket closed while sending {msg_type}", "ERROR")
                    return False
                total_sent += sent
            
            if self.debug:
                debug_message("SEND", self.nickname, f"type={msg_type}, value={value}")
            return True
        except Exception as e:
            if self.debug:
                debug_print(f"Failed to send {msg_type}: {e}", "ERROR")
            return False
    
    def receive_message(self):
        """Receive complete message from server"""
        if not self.socket:
            return None
            
        try:
            data = b''
            while len(data) < 28:
                chunk = self.socket.recv(28 - len(data))
                if not chunk:
                    if self.debug:
                        debug_print("Connection closed by server", "INFO")
                    return None
                data += chunk
            return self.unpack_message(data)
        except socket.timeout:
            if self.debug:
                debug_print("Receive timeout", "WARN")
            return None
        except Exception as e:
            if self.debug:
                debug_print(f"Receive error: {e}", "ERROR")
            return None
    
    def receiver_thread(self):
        """Thread to receive messages from server"""
        while self.running:
            msg = self.receive_message()
            if not msg:
                if self.running:  # Only log if we're still supposed to be running
                    if self.debug:
                        debug_print("Receiver thread stopping", "INFO")
                break
                
            self.last_messages.append(msg)
            if len(self.last_messages) > 20:
                self.last_messages.pop(0)
            
            msg_type = msg['type']
            if msg_type == 'start':
                self.betting_phase = True
                self.flight_phase = False
                if self.debug:
                    debug_print(f"Betting phase started, {msg['value']} seconds", "INFO")
            elif msg_type == 'closed':
                self.betting_phase = False
                self.flight_phase = True
                if self.debug:
                    debug_print("Flight phase started", "INFO")
            elif msg_type == 'multiplier':
                self.current_multiplier = msg['value']
                if self.debug and msg['value'] % 0.1 < 0.01:  # Log every 0.1x
                    debug_print(f"Multiplier: {msg['value']:.2f}x", "INFO")
            elif msg_type == 'explode':
                self.betting_phase = False
                self.flight_phase = False
                if self.debug:
                    debug_print(f"Explosion at {msg['value']:.2f}x", "INFO")
            elif msg_type == 'payout':
                if self.debug:
                    debug_print(f"Payout received: R$ {msg['value']:.2f}", "INFO")
            elif msg_type == 'bye':
                if self.debug:
                    debug_print("Server sent bye", "INFO")
                self.running = False
                break
                
            self.execute_next_action()
    
    def execute_next_action(self):
        """Execute the next programmed action if conditions are met"""
        if self.action_index >= len(self.test_actions):
            return
        
        action = self.test_actions[self.action_index]
        can_execute = False
        
        if action['trigger'] == 'betting_open' and self.betting_phase:
            can_execute = True
        elif action['trigger'] == 'flight_phase' and self.flight_phase:
            can_execute = True
        elif action['trigger'] == 'multiplier_reached':
            target = action.get('multiplier', 1.0)
            if self.flight_phase and self.current_multiplier >= target:
                if not hasattr(self, '_cashout_executed'):
                    can_execute = True
                    self._cashout_executed = True
        
        if can_execute:
            if 'delay' in action:
                time.sleep(action['delay'])
            
            if self.debug:
                debug_print(f"Executing action: {action['action']}", "INFO")
            
            if action['action'] == 'bet':
                self.send_message('bet', action['amount'])
            elif action['action'] == 'cashout':
                self.send_message('cashout')
            elif action['action'] == 'quit':
                self.send_message('bye')
                self.running = False
            
            self.action_index += 1
    
    def add_action(self, trigger, action, **kwargs):
        """Add a programmed action to execute"""
        self.test_actions.append({'trigger': trigger, 'action': action, **kwargs})
    
    def connect(self):
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(30)  # Increased timeout
            self.socket.connect((self.server_ip, self.port))
            
            if self.debug:
                debug_print(f"Connected to {self.server_ip}:{self.port}", "INFO")
            
            # The server doesn't seem to expect an initial nickname message
            # It assigns player IDs automatically
            self.connection_success = True
            return True
        except Exception as e:
            if self.debug:
                debug_print(f"Connection failed: {e}", "ERROR")
            return False
    
    def run(self):
        """Run the client"""
        if not self.connect():
            return False
            
        receiver = threading.Thread(target=self.receiver_thread)
        receiver.daemon = True
        receiver.start()
        
        # Wait a bit for initial messages
        time.sleep(0.5)
        
        # Keep alive until disconnected
        while self.running:
            time.sleep(0.1)
            
        if self.socket:
            self.socket.close()
        return self.connection_success

class AviatorTestSuite:
    def __init__(self, server_port=51511, debug=False):
        self.server_port = server_port
        self.server_process = None
        self.test_results = []
        self.debug = debug
        
    def start_server(self):
        """Start the server in background"""
        try:
            cmd = ['./bin/server', 'v4', str(self.server_port)]
            if self.debug:
                # In debug mode, show server output
                self.server_process = subprocess.Popen(cmd, text=True)
            else:
                self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            time.sleep(2)  # Give server more time to start
            
            if self.server_process.poll() is not None:
                if not self.debug:
                    stdout, stderr = self.server_process.communicate()
                    print(f"❌ Server failed to start:")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                return False
                
            print(f"✅ Server started on port {self.server_port}")
            if self.debug:
                debug_print("Server started in debug mode", "INFO")
            return True
        except Exception as e:
            print(f"❌ Error starting server: {e}")
            return False
    
    def stop_server(self):
        """Stop the server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                if self.debug:
                    debug_print("Server stopped", "INFO")
            except:
                self.server_process.kill()
                if self.debug:
                    debug_print("Server force killed", "WARN")
    
    def log_test_result(self, test_name, passed, details=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({'name': test_name, 'passed': passed, 'details': details})
    
    def test_argument_validation(self):
        """Test argument validation"""
        print("\n🧪 Test: Argument Validation")
        
        result1 = subprocess.run(['./bin/server'], capture_output=True, text=True)
        result2 = subprocess.run(['./bin/client'], capture_output=True, text=True)
        result3 = subprocess.run(['./bin/client', '127.0.0.1', '8080', '-nick', 'verylongnicknamethatiswaytoobig'], capture_output=True, text=True)
        
        success = result1.returncode != 0 and result2.returncode != 0 and result3.returncode != 0
        
        if self.debug:
            debug_print(f"Server without args exit code: {result1.returncode}", "INFO")
            debug_print(f"Client without args exit code: {result2.returncode}", "INFO")
            debug_print(f"Client with long nick exit code: {result3.returncode}", "INFO")
        
        self.log_test_result("Argument validation", success)
        return success
    
    def test_ipv6_support(self):
        """Test IPv6 support"""
        print("\n🧪 Test: IPv6 Support")
        
        try:
            ipv6_process = subprocess.Popen(['./bin/server', 'v6', str(self.server_port + 1)], 
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            success = ipv6_process.poll() is None
            
            if ipv6_process:
                ipv6_process.terminate()
                try:
                    ipv6_process.wait(timeout=5)
                except:
                    ipv6_process.kill()
            
            if self.debug:
                debug_print(f"IPv6 server test result: {success}", "INFO")
                
            self.log_test_result("IPv6 support", success)
            return success
        except Exception as e:
            if self.debug:
                debug_print(f"IPv6 test error: {e}", "ERROR")
            self.log_test_result("IPv6 support", False)
            return False
    
    def test_connection_and_betting(self):
        """Test connection and betting scenario - ENHANCED"""
        print("\n🧪 Test: Connection and Betting")
        
        if self.debug:
            debug_print("Starting connection and betting test", "INFO")
        
        client1 = AviatorTestClient('127.0.0.1', self.server_port, 'Flip', debug=self.debug)
        client2 = AviatorTestClient('127.0.0.1', self.server_port, 'Flop', debug=self.debug)
        
        client1.add_action('betting_open', 'bet', amount=50.0, delay=1.0)
        client1.add_action('multiplier_reached', 'cashout', multiplier=1.70)
        client2.add_action('betting_open', 'bet', amount=50.0, delay=2.0)
        
        def run_client1():
            if self.debug:
                debug_print("Starting client1 thread", "INFO")
            client1.run()
            
        def run_client2():
            if self.debug:
                debug_print("Starting client2 thread", "INFO") 
            time.sleep(1)  # Slight delay for second client
            client2.run()
            
        t1 = threading.Thread(target=run_client1)
        t2 = threading.Thread(target=run_client2)
        t1.daemon = True
        t2.daemon = True
        
        t1.start()
        t2.start()
        
        # Wait for test to complete
        if self.debug:
            debug_print("Waiting for test completion (30 seconds)...", "INFO")
        
        time.sleep(30)  # Increased wait time
        
        # Analyze results
        start_received = any(msg.get('type') == 'start' for msg in client1.last_messages)
        cashout_received = any(msg.get('type') == 'payout' for msg in client1.last_messages)
        explosion_seen = any(msg.get('type') == 'explode' for msg in client1.last_messages + client2.last_messages)
        
        # Debug information
        if self.debug or not (start_received and explosion_seen):
            print(f"    🔍 Debug Info:")
            print(f"    Client1 connected: {client1.connection_success}")
            print(f"    Client2 connected: {client2.connection_success}")
            print(f"    Messages received by Client1: {len(client1.last_messages)}")
            print(f"    Messages received by Client2: {len(client2.last_messages)}")
            print(f"    Start message received: {start_received}")
            print(f"    Cashout received: {cashout_received}")
            print(f"    Explosion seen: {explosion_seen}")
            
            if client1.last_messages:
                print(f"    Client1 last messages: {[msg['type'] for msg in client1.last_messages[-5:]]}")
            if client2.last_messages:
                print(f"    Client2 last messages: {[msg['type'] for msg in client2.last_messages[-5:]]}")
        
        success = start_received and explosion_seen
        details = ""
        if not success:
            if not start_received:
                details += "No 'start' message received. "
            if not explosion_seen:
                details += "No 'explode' message received. "
        
        self.log_test_result("Connection and game flow", success, details)
        
        client1.running = False
        client2.running = False
        
        # Wait for threads to finish
        t1.join(timeout=2)
        t2.join(timeout=2)
        
        return success
    
    def run_automated_tests(self):
        """Run all automated tests"""
        print("\n🚀 Running Automated Tests")
        print("=" * 50)
        
        if self.debug:
            debug_print("Starting automated test suite", "INFO")
        
        if not self.start_server():
            print("❌ Failed to start server")
            return False
            
        try:
            tests = [
                self.test_argument_validation,
                self.test_ipv6_support,
                self.test_connection_and_betting
            ]
            
            for i, test in enumerate(tests):
                if self.debug:
                    debug_print(f"Running test {i+1}/{len(tests)}: {test.__name__}", "INFO")
                test()
                time.sleep(3)  # Longer pause between tests
                
        finally:
            self.stop_server()
        
        passed = sum(1 for r in self.test_results if r['passed'])
        total = len(self.test_results)
        print(f"\n📈 Results: {passed}/{total} tests passed ({100*passed/total:.1f}%)")
        
        if passed == total:
            print("🎉 All tests passed!")
            return True
        else:
            print("❌ Some tests failed.")
            if self.debug:
                for result in self.test_results:
                    if not result['passed']:
                        debug_print(f"Failed test: {result['name']} - {result['details']}", "ERROR")
            return False

def run_stress_test(debug=False):
    """Run stress test with optional debugging"""
    print("\n💪 Running Stress Test")
    print("=" * 50)
    
    server_process = None
    try:
        if debug:
            server_process = subprocess.Popen(['./bin/server', 'v4', '52000'])
        else:
            server_process = subprocess.Popen(['./bin/server', 'v4', '52000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        if server_process.poll() is not None:
            print("❌ Failed to start server for stress test")
            return False
        
        print("🧪 Testing 5 concurrent clients...")
        clients = []
        threads = []
        
        for i in range(5):
            client = AviatorTestClient('127.0.0.1', 52000, f'Stress{i+1}', debug=debug)
            client.add_action('betting_open', 'bet', amount=random.uniform(10, 100), delay=random.uniform(0.5, 2.0))
            clients.append(client)
            
            def run_client(c):
                c.run()
            
            thread = threading.Thread(target=run_client, args=(client,))
            thread.daemon = True
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        time.sleep(25)  # Longer wait for stress test
        
        for client in clients:
            client.running = False
        
        for thread in threads:
            thread.join(timeout=2)
        
        successful_connections = sum(1 for c in clients if c.connection_success)
        print(f"Successful connections: {successful_connections}/5")
        
        success = successful_connections >= 3  # Allow some failures
        print("✅ Stress test completed" if success else "❌ Stress test failed")
        return success
        
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
        return False
    finally:
        if server_process:
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
            except:
                server_process.kill()

def run_manual_guide():
    """Show manual test guide"""
    print("\n🎮 Manual Test Guide")
    print("=" * 50)
    print("""
Follow these steps to manually test the system:

1. Start server: ./bin/server v4 8080
2. Connect client: ./bin/client 127.0.0.1 8080 -nick Player1
3. Wait for round to start and place a bet: 50
4. Connect second client: ./bin/client 127.0.0.1 8080 -nick Player2
5. Place bet in second client: 50
6. When multiplier reaches ~1.70x, cash out in first client: C
7. Let second client wait for explosion
8. Observe results and disconnect: Q

Expected behavior:
- First client should receive payout of R$ 85.00 (50 * 1.70)
- Second client should lose R$ 50 on explosion
- Server should log all events properly

For debugging, add --debug flag to any test command.
""")

def main():
    """Main function with enhanced debugging options"""
    global DEBUG_VERBOSE, DEBUG_MESSAGES
    
    # Check for debug flags
    debug_mode = '--debug' in sys.argv or '-d' in sys.argv
    if debug_mode:
        DEBUG_VERBOSE = True
        DEBUG_MESSAGES = True
        sys.argv = [arg for arg in sys.argv if arg not in ['--debug', '-d']]
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--auto', '-a']:
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            suite = AviatorTestSuite(debug=debug_mode)
            return 0 if suite.run_automated_tests() else 1
            
        elif sys.argv[1] in ['--stress', '-s']:
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            return 0 if run_stress_test(debug=debug_mode) else 1
            
        elif sys.argv[1] in ['--manual', '-m']:
            run_manual_guide()
            return 0
            
        elif sys.argv[1] == '--all':
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            suite = AviatorTestSuite(debug=debug_mode)
            auto_success = suite.run_automated_tests()
            time.sleep(2)
            stress_success = run_stress_test(debug=debug_mode)
            
            success = auto_success and stress_success
            print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
            return 0 if success else 1
    
    print("🧪 Aviator Test Suite")
    print("Usage:")
    print("  python3 test.py --auto     Run automated tests")
    print("  python3 test.py --stress   Run stress tests") 
    print("  python3 test.py --manual   Show manual test guide")
    print("  python3 test.py --all      Run all tests")
    print("\nDebugging:")
    print("  Add --debug or -d to any command for verbose output")
    print("  Example: python3 test.py --auto --debug")
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        sys.exit(1) 
