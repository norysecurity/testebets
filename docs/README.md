# BetAuditor — Documentação

## Visão Geral
Ferramenta CLI de pentest e auditoria para APIs REST.

## Módulos
| Módulo          | Arquivo src/             | Finalidade                              |
|-----------------|--------------------------|------------------------------------------|
| Race Condition  | race_condition.py        | Testa TOCTOU com requisições simultâneas |
| JWT Brute Force | jwt_bruteforce.py        | Decodifica e força o secret do JWT       |
| Fuzzer Lógico   | fuzzer.py                | Injeta anomalias em parâmetros numéricos |

## Uso
```bash
python main.py race  --url <URL> --payload '<JSON>' --headers '<JSON>' --conexoes 50
python main.py jwt   --token <TOKEN> --wordlist wordlists/rockyou.txt
python main.py fuzz  --url <URL> --payload '<JSON>' --headers '<JSON>'
```

## ⚠ Aviso Legal
Use apenas em sistemas com autorização formal por escrito.
Uso não autorizado é crime (Lei 12.737/2012 — Lei Carolina Dieckmann).
