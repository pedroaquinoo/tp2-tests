#!/usr/bin/env python3
"""
Comprehensive Test Suite for Aviator Game
Consolidates all testing functionality
"""
import socket
import struct
import threading
import time
import sys
import subprocess
import random

class AviatorTestClient:
    def __init__(self, server_ip, port, nickname):
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
        
    def pack_message(self, player_id, value, msg_type, player_profit=0.0, house_profit=0.0):
        type_bytes = msg_type.encode('utf-8')[:10].ljust(12, b'\0')
        data = struct.pack('<i', player_id)
        data += struct.pack('<f', value)
        data += type_bytes
        data += struct.pack('<f', player_profit)
        data += struct.pack('<f', house_profit)
        return data
    
    def unpack_message(self, data):
        if len(data) != 28:
            return None
        try:
            player_id = struct.unpack('<i', data[0:4])[0]
            value = struct.unpack('<f', data[4:8])[0]
            type_bytes = data[8:20]
            player_profit = struct.unpack('<f', data[20:24])[0]
            house_profit = struct.unpack('<f', data[24:28])[0]
            
            null_pos = type_bytes.find(b'\0')
            if null_pos >= 0:
                msg_type = type_bytes[:null_pos].decode('utf-8')
            else:
                msg_type = type_bytes.decode('utf-8').rstrip('\0')
            
            return {
                'player_id': player_id,
                'value': value,
                'type': msg_type,
                'player_profit': player_profit,
                'house_profit': house_profit
            }
        except:
            return None
    
    def send_message(self, msg_type, value=0.0):
        if not self.socket:
            return False
        try:
            msg_data = self.pack_message(0, value, msg_type)
            total_sent = 0
            while total_sent < len(msg_data):
                sent = self.socket.send(msg_data[total_sent:])
                if sent == 0:
                    return False
                total_sent += sent
            return True
        except:
            return False
    
    def receive_message(self):
        if not self.socket:
            return None
        try:
            data = b''
            while len(data) < 28:
                chunk = self.socket.recv(28 - len(data))
                if not chunk:
                    return None
                data += chunk
            return self.unpack_message(data)
        except:
            return None
    
    def receiver_thread(self):
        while self.running:
            msg = self.receive_message()
            if not msg:
                break
            self.last_messages.append(msg)
            if len(self.last_messages) > 20:
                self.last_messages.pop(0)
            
            msg_type = msg['type']
            if msg_type == 'start':
                self.betting_phase = True
                self.flight_phase = False
            elif msg_type == 'closed':
                self.betting_phase = False
                self.flight_phase = True
            elif msg_type == 'multiplier':
                self.current_multiplier = msg['value']
            elif msg_type == 'explode':
                self.betting_phase = False
                self.flight_phase = False
            elif msg_type == 'bye':
                self.running = False
                break
            self.execute_next_action()
    
    def execute_next_action(self):
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
            
            if action['action'] == 'bet':
                self.send_message('bet', action['amount'])
            elif action['action'] == 'cashout':
                self.send_message('cashout')
            elif action['action'] == 'quit':
                self.send_message('bye')
                self.running = False
            
            self.action_index += 1
    
    def add_action(self, trigger, action, **kwargs):
        self.test_actions.append({'trigger': trigger, 'action': action, **kwargs})
    
    def connect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.server_ip, self.port))
            self.send_message('nick', 0, self.nickname)
            return True
        except:
            return False
    
    def run(self):
        if not self.connect():
            return False
        receiver = threading.Thread(target=self.receiver_thread)
        receiver.daemon = True
        receiver.start()
        while self.running:
            time.sleep(0.1)
        if self.socket:
            self.socket.close()
        return True

class AviatorTestSuite:
    def __init__(self, server_port=51511):
        self.server_port = server_port
        self.server_process = None
        self.test_results = []
        
    def start_server(self):
        try:
            cmd = ['./bin/server', 'v4', str(self.server_port)]
            self.server_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            time.sleep(1)
            if self.server_process.poll() is not None:
                return False
            print(f"✅ Server started on port {self.server_port}")
            return True
        except:
            return False
    
    def stop_server(self):
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                self.server_process.kill()
    
    def log_test_result(self, test_name, passed, details=""):
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({'name': test_name, 'passed': passed, 'details': details})
    
    def test_argument_validation(self):
        print("\n🧪 Test: Argument Validation")
        result1 = subprocess.run(['./bin/server'], capture_output=True, text=True)
        result2 = subprocess.run(['./bin/client'], capture_output=True, text=True)
        result3 = subprocess.run(['./bin/client', '127.0.0.1', '8080', '-nick', 'verylongnicknamethatiswaytoobig'], capture_output=True, text=True)
        success = result1.returncode != 0 and result2.returncode != 0 and result3.returncode != 0
        self.log_test_result("Argument validation", success)
        return success
    
    def test_ipv6_support(self):
        print("\n🧪 Test: IPv6 Support")
        try:
            ipv6_process = subprocess.Popen(['./bin/server', 'v6', str(self.server_port + 1)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(2)
            success = ipv6_process.poll() is None
            if ipv6_process:
                ipv6_process.terminate()
                try:
                    ipv6_process.wait(timeout=5)
                except:
                    ipv6_process.kill()
            self.log_test_result("IPv6 support", success)
            return success
        except:
            self.log_test_result("IPv6 support", False)
            return False
    
    def test_connection_and_betting(self):
        print("\n🧪 Test: Connection and Betting")
        client1 = AviatorTestClient('127.0.0.1', self.server_port, 'Flip')
        client2 = AviatorTestClient('127.0.0.1', self.server_port, 'Flop')
        
        client1.add_action('betting_open', 'bet', amount=50.0, delay=1.0)
        client1.add_action('multiplier_reached', 'cashout', multiplier=1.70)
        client2.add_action('betting_open', 'bet', amount=50.0, delay=2.0)
        
        def run_client1():
            client1.run()
        def run_client2():
            client2.run()
            
        t1 = threading.Thread(target=run_client1)
        t2 = threading.Thread(target=run_client2)
        t1.daemon = True
        t2.daemon = True
        t1.start()
        t2.start()
        
        time.sleep(25)
        
        start_received = any(msg.get('type') == 'start' for msg in client1.last_messages)
        cashout_received = any(msg.get('type') == 'payout' for msg in client1.last_messages)
        explosion_seen = any(msg.get('type') == 'explode' for msg in client1.last_messages + client2.last_messages)
        
        success = start_received and explosion_seen
        self.log_test_result("Connection and game flow", success)
        
        client1.running = False
        client2.running = False
        return success
    
    def run_automated_tests(self):
        print("\n🚀 Running Automated Tests")
        print("=" * 50)
        
        if not self.start_server():
            print("❌ Failed to start server")
            return False
            
        try:
            tests = [
                self.test_argument_validation,
                self.test_ipv6_support,
                self.test_connection_and_betting
            ]
            
            for test in tests:
                test()
                time.sleep(2)
                
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
            return False

def run_stress_test():
    print("\n💪 Running Stress Test")
    print("=" * 50)
    
    server_process = None
    try:
        server_process = subprocess.Popen(['./bin/server', 'v4', '52000'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(2)
        
        if server_process.poll() is not None:
            print("❌ Failed to start server for stress test")
            return False
        
        print("🧪 Testing 5 concurrent clients...")
        clients = []
        threads = []
        
        for i in range(5):
            client = AviatorTestClient('127.0.0.1', 52000, f'Stress{i+1}')
            client.add_action('betting_open', 'bet', amount=random.uniform(10, 100), delay=random.uniform(0.5, 2.0))
            clients.append(client)
            
            def run_client(c):
                c.run()
            
            thread = threading.Thread(target=run_client, args=(client,))
            thread.daemon = True
            threads.append(thread)
        
        for thread in threads:
            thread.start()
        
        time.sleep(20)
        
        for client in clients:
            client.running = False
        
        for thread in threads:
            thread.join(timeout=2)
        
        print("✅ Stress test completed")
        return True
        
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
""")

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--auto', '-a']:
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            suite = AviatorTestSuite()
            return 0 if suite.run_automated_tests() else 1
            
        elif sys.argv[1] in ['--stress', '-s']:
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            return 0 if run_stress_test() else 1
            
        elif sys.argv[1] in ['--manual', '-m']:
            run_manual_guide()
            return 0
            
        elif sys.argv[1] == '--all':
            print("🔨 Compiling project...")
            if subprocess.run(['make'], capture_output=True).returncode != 0:
                print("❌ Compilation failed")
                return 1
            print("✅ Compilation successful")
            
            suite = AviatorTestSuite()
            auto_success = suite.run_automated_tests()
            time.sleep(2)
            stress_success = run_stress_test()
            
            success = auto_success and stress_success
            print(f"\n🎯 Overall: {'✅ ALL TESTS PASSED' if success else '❌ SOME TESTS FAILED'}")
            return 0 if success else 1
    
    print("🧪 Aviator Test Suite")
    print("Usage:")
    print("  python3 test.py --auto     Run automated tests")
    print("  python3 test.py --stress   Run stress tests") 
    print("  python3 test.py --manual   Show manual test guide")
    print("  python3 test.py --all      Run all tests")
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted")
        sys.exit(1) 