

## 📁 Project Structure

```
aviator-2/
├── bin/
│   ├── server          # Server executable
│   └── client          # Client executable
├── common.h            # Shared definitions
├── server.c            # Server implementation
├── client.c            # Client implementation
├── test.py             # Comprehensive test suite
├── Makefile            # Build configuration
└── README.md           # Documentation
```

## 🧪 Testing

The project includes a comprehensive test suite that covers all functionality:

**Automated Tests:**
```bash
make test          # Run all automated tests
python3 test.py --auto
```

**Stress Tests:**
```bash
make test-stress   # Run stress/load tests  
python3 test.py --stress
```

**Manual Test Guide:**
```bash
make test-manual   # Show manual testing guide
python3 test.py --manual
```

**All Tests:**
```bash
make test-all      # Run everything
python3 test.py --all
```

**Manual Testing:**
1. Start server: `./bin/server v4 8080`
2. Connect clients: `./bin/client 127.0.0.1 8080 -nick Player1`
3. Test scenarios: betting, cash-out, and explosion

**Desenvolvido para:** Disciplina de Redes  
**Linguagem:** C (padrão C99)  
**Compilador:** GCC com flags: `-pthread -Wall -Wextra -O2` 
