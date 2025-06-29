

## 📁 Project Structure

```
aviator-2/
├── bin/               # Compiled executables
├── server.c           # Server implementation (452 lines)
├── client.c           # Client implementation (277 lines)  
├── common.h           # Shared definitions (34 lines)
├── test.py           # Comprehensive test suite (654 lines)
├── debug_helper.py   # Quick debugging utilities (180 lines)
├── Makefile          # Build configuration (35 lines)
└── README.md         # Enhanced documentation (275 lines)
```


## 🧪 Testing & Debugging

The project includes a comprehensive test suite with advanced debugging capabilities:

### **Automated Tests**
```bash
make test              # Run all automated tests
python3 test.py --auto # Direct command
```

### **Stress Tests**
```bash
make test-stress       # Run stress/load tests  
python3 test.py --stress
```

### **Manual Test Guide**
```bash
make test-manual       # Show manual testing guide
python3 test.py --manual
```

### **All Tests**
```bash
make test-all          # Run everything
python3 test.py --all
```

### **Debug Mode**
Add `--debug` flag to any test for verbose output:
```bash
python3 test.py --auto --debug    # Detailed message tracing
python3 test.py --stress --debug  # Stress test debugging
```

### **Quick Debugging Tools**
```bash
# Test connection to server
python3 debug_helper.py connection 8080

# Verify struct compatibility
python3 debug_helper.py struct

# Monitor server logs
python3 debug_helper.py server 51511 15

# Run single client scenario
python3 debug_helper.py scenario 51511
```

### **Manual Testing**
1. Start server: `./bin/server v4 8080`
2. Connect clients: `./bin/client 127.0.0.1 8080 -nick Player1`
3. Test scenarios: betting, cash-out, and explosion

### **Debugging Features**
- 🔍 **Message Tracing**: See all client-server communications
- 📊 **Connection Monitoring**: Track client connections and disconnections  
- 🎯 **Protocol Validation**: Verify message structure and size
- 📈 **Game Flow Analysis**: Monitor betting, multipliers, and explosions
- ⚡ **Real-time Logs**: Live server event logging

