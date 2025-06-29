# Aviator Game - "Jogo do Aviãozinho"

Este é um jogo de cassino online multijogador implementado em **C puro** usando **sockets POSIX** e **threads**, desenvolvido para a disciplina de Redes.

## 📋 Descrição

O **Aviator** simula um avião que decola e sobe com multiplicador crescente (1.00×, 1.01×, …) até um ponto de explosão calculado dinamicamente. Permite que até **10 jogadores** façam apostas simultâneas, solicitem **cash-out** a qualquer momento e recebam **atualizações em tempo real**.

### 🎯 Características Principais

- ✅ **Suporte IPv4 e IPv6**
- ✅ **Até 10 jogadores simultâneos**
- ✅ **Protocolo binário customizado (32 bytes por mensagem)**
- ✅ **Threading com sincronização segura**
- ✅ **Logging padronizado de todas as ações**
- ✅ **Tratamento rigoroso de erros**
- ✅ **Framing completo de mensagens TCP**

## 🏗️ Compilação

```bash
make
```

Isso criará os executáveis `bin/server` e `bin/client`.

Para limpar os arquivos compilados:
```bash
make clean
```

## 🚀 Uso

### Servidor

```bash
./bin/server <v4|v6> <porta>
```

**Exemplos:**
```bash
./bin/server v4 8080    # IPv4 na porta 8080
./bin/server v6 51511   # IPv6 na porta 51511
```

### Cliente

```bash
./bin/client <IP_servidor> <porta> -nick <apelido>
```

**Exemplos:**
```bash
./bin/client 127.0.0.1 8080 -nick João     # IPv4
./bin/client ::1 51511 -nick Maria         # IPv6
```

**Restrições:**
- Apelido deve ter no máximo 13 caracteres
- Porta deve estar entre 1 e 65535

## 🎮 Como Jogar

### Fluxo de uma Rodada

1. **Espera**: O servidor aguarda pelo menos 1 jogador conectado
2. **Apostas (10s)**: Janela de apostas aberta por 10 segundos
3. **Voo**: Multiplicador cresce de 1.00× em incrementos de 0.01× a cada 100ms
4. **Cash-out**: Jogadores podem sacar a qualquer momento antes da explosão
5. **Explosão**: Ponto calculado pela fórmula: `√(1 + N + 0.01 × V)`
   - N = número de apostas
   - V = soma total apostada
6. **Resultados**: Pagamentos e perdas são calculados

### Comandos do Cliente

**Durante as apostas:**
- Digite um valor numérico (ex: `10.50`) para apostar
- Digite `Q` para sair

**Durante o voo:**
- Digite `C` para cash-out
- Digite `Q` para sair

### Cálculo de Lucros

- **Cash-out bem-sucedido**: `Payout = Aposta × Multiplicador_no_momento`
- **Perdeu na explosão**: `Payout = 0` (perde toda a aposta)
- **Lucro da casa**: Soma de todas as apostas perdidas menos pagamentos

## 📊 Protocolo de Comunicação

Todas as mensagens usam a estrutura fixa de 32 bytes:

```c
struct aviator_msg {
    int32_t   player_id;      // ID único do jogador
    float     value;          // Valor dependente do tipo
    char      type[11];       // Tipo da mensagem
    float     player_profit;  // Lucro acumulado do jogador
    float     house_profit;   // Lucro acumulado da casa
};
```

### Tipos de Mensagem

- `"start"` → Início de rodada (10s de apostas)
- `"bet"` → Envio de aposta pelo cliente
- `"closed"` → Fim da janela de apostas
- `"multiplier"` → Broadcast do multiplicador atual
- `"cashout"` → Pedido de saque pelo cliente
- `"explode"` → Fim da rodada (explosão)
- `"payout"` → Retorno individualizado de ganhos
- `"profit"` → Atualização de lucros
- `"bye"` → Encerramento de conexão

## 📝 Logging do Servidor

Todas as ações geram logs padronizados:

```
event=<tipo> | id=<jogador> | m=<multiplicador> | me=<explosão> | N=<num_jogadores> | V=<total_apostas> | bet=<aposta> | payout=<pagamento> | player_profit=<lucro_jogador> | house_profit=<lucro_casa>
```

**Exemplo de saída:**
```
Server listening on port 8080
event=start | id=* | m=0.00 | me=0.00 | N=0 | V=0.00 | bet=0.00 | payout=0.00 | player_profit=0.00 | house_profit=0.00
event=start | id=* | m=0.00 | me=0.00 | N=1 | V=0.00 | bet=0.00 | payout=0.00 | player_profit=0.00 | house_profit=0.00
event=bet | id=1 | m=0.00 | me=0.00 | N=1 | V=50.00 | bet=50.00 | payout=0.00 | player_profit=0.00 | house_profit=0.00
event=closed | id=* | m=0.00 | me=1.73 | N=1 | V=50.00 | bet=0.00 | payout=0.00 | player_profit=0.00 | house_profit=0.00
event=multiplier | id=* | m=1.01 | me=1.73 | N=0 | V=0.00 | bet=0.00 | payout=0.00 | player_profit=0.00 | house_profit=0.00
...
event=payout | id=1 | m=1.45 | me=0.00 | N=0 | V=0.00 | bet=0.00 | payout=72.50 | player_profit=22.50 | house_profit=-22.50
```

## 🧵 Arquitetura Threading

### Servidor
- **Thread Principal**: Inicialização e coordenação
- **Thread Acceptor**: Aceita novas conexões
- **Thread Round Manager**: Gerencia ciclo de rodadas
- **Threads Client Handler**: Uma por cliente conectado (até 10)

### Cliente
- **Thread Principal**: Interface de usuário e input
- **Thread Receiver**: Recebe mensagens do servidor

### Sincronização
- `clients_mtx`: Protege array de clientes
- `profit_mtx`: Protege cálculos de lucro
- `state_mtx`: Protege estado da rodada

## 🔧 Detalhes Técnicos

### Tratamento de Erros
- Validação completa de argumentos
- Verificação de retorno de todas as chamadas de sistema
- Cleanup adequado de recursos
- Tratamento de desconexões inesperadas

### Compatibilidade de Rede
- Suporte nativo IPv4 e IPv6
- Framing completo de mensagens TCP
- Loops de send/recv para transmissão garantida
- Reutilização de endereços (SO_REUSEADDR)

### Segurança Concorrencial
- Acesso mutuamente exclusivo a dados compartilhados
- Prevenção de race conditions
- Cleanup thread-safe na desconexão
- Detach de threads para evitar vazamentos

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

## ⚠️ Limitações Conhecidas

- Máximo de 10 jogadores simultâneos
- Janela de apostas fixa em 10 segundos
- Incremento de multiplicador fixo (0.01x/100ms)
- Sem persistência de dados entre reinicializações

## 📚 Requisitos Atendidos

✅ **Implementação em C puro**  
✅ **Uso de sockets POSIX**  
✅ **Threading com pthread**  
✅ **Suporte IPv4 e IPv6**  
✅ **Protocolo binário customizado**  
✅ **Até 10 jogadores simultâneos**  
✅ **Logging padronizado**  
✅ **Tratamento de erros rigoroso**  
✅ **Documentação completa**

---

**Desenvolvido para:** Disciplina de Redes  
**Linguagem:** C (padrão C99)  
**Compilador:** GCC com flags: `-pthread -Wall -Wextra -O2` 