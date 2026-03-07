#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    BetAuditor — main.py  (6 módulos)                       ║
║            Suite Completa de Pentest para Plataformas de Apostas           ║
║                                                                            ║
║  Módulos:                                                                  ║
║    race   → Race Condition TOCTOU (N conexões simultâneas)                 ║
║    jwt    → Análise + Brute Force de secret JWT                            ║
║    fuzz   → Fuzzing Lógico em parâmetros numéricos                        ║
║    otp    → Brute Force de OTP sem rate limit                              ║
║    paths  → Path Discovery estilo GoBuster                                 ║
║    scan   → Client-Side Trust Scan (seed, is_winner, AES, roles)           ║
║                                                                            ║
║  ⚠  Use APENAS com autorização formal e por escrito.                       ║
║     Uso não autorizado é crime (Lei 12.737/2012).                          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import argparse
import asyncio
import io
import os
import sys

# ── UTF-8 no stdout do Windows ────────────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# ── Path para importar src/ ───────────────────────────────────────────────────
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_BASE_DIR, "src"))

from race_condition    import race_condition_test
from jwt_bruteforce    import jwt_analisar_e_bruteforce
from fuzzer            import fuzzing_logico
from otp_bruteforce    import otp_bruteforce
from path_discovery    import path_discovery
from client_trust_scan import client_trust_scan


# ─────────────────────────────────────────────────────────────────────────────
#  BANNER
# ─────────────────────────────────────────────────────────────────────────────

BANNER = r"""
  ____       _      _             _ _ _
 | __ )  ___| |_   / \  _   _  __| (_) |_ ___  _ __
 |  _ \ / _ \ __| / _ \| | | |/ _` | | __/ _ \| '__|
 | |_) |  __/ |_ / ___ \ |_| | (_| | | || (_) | |
 |____/ \___|\__/_/   \_\__,_|\__,_|_|\__\___/|_|

   6 Módulos  |  Siente Pentest Suite  |  v2.0
   race · jwt · fuzz · otp · paths · scan
═══════════════════════════════════════════════════════
⚠  Apenas para uso em ambientes com autorização formal.
"""

# ─────────────────────────────────────────────────────────────────────────────
#  ARGPARSE — BUILDER
# ─────────────────────────────────────────────────────────────────────────────

def _add_arg_url(p):
    p.add_argument("--url", required=True, help="URL completa do endpoint alvo")

def _add_arg_payload(p):
    p.add_argument("--payload", required=True, help='Payload JSON (ex: \'{"amount":10}\')')

def _add_arg_headers(p, required=True):
    p.add_argument(
        "--headers", required=required,
        help='Headers HTTP em JSON (ex: \'{"Authorization":"Bearer TOKEN"}\')'
    )

def _add_arg_metodo(p):
    p.add_argument(
        "--metodo", default="POST", choices=["GET", "POST", "PUT", "PATCH"],
        help="Método HTTP (padrão: POST)"
    )


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="betauditor",
        description="BetAuditor v2.0 — Suite de Pentest para APIs de Apostas/Cursos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
REFERÊNCIA RÁPIDA DOS 6 MÓDULOS:
══════════════════════════════════════════════════════════════════════════
  race   Dispara N req. simultâneas → testa TOCTOU/Race Condition
  jwt    Decodifica JWT + força bruta do secret HMAC com wordlist
  fuzz   Injeta 13 anomalias (float, null, negativo...) em params numéricos
  otp    Força bruta de OTP numérico sem rate limit (ex: painel /zadmin)
  paths  Descobre rotas ocultas estilo GoBuster (/admin, /zadmin, /api/v1...)
  scan   Detecta lógica crítica no front-end (seed, is_winner, AES, roles)
══════════════════════════════════════════════════════════════════════════
Use python main.py <módulo> --help para detalhes de cada módulo.
        """,
    )

    sub = parser.add_subparsers(dest="modulo", required=True, metavar="MÓDULO")

    # ── 1. race ───────────────────────────────────────────────────────────────
    p_race = sub.add_parser("race", help="Race Condition (TOCTOU) — N req. simultâneas")
    _add_arg_url(p_race)
    _add_arg_payload(p_race)
    _add_arg_headers(p_race)
    p_race.add_argument("--conexoes", type=int, default=50, metavar="N",
                        help="Número de requisições paralelas (padrão: 50)")

    # ── 2. jwt ────────────────────────────────────────────────────────────────
    p_jwt = sub.add_parser("jwt", help="Análise + Brute Force JWT com wordlist")
    p_jwt.add_argument("--token",    required=True, help="Token JWT completo capturado")
    p_jwt.add_argument("--wordlist", required=True, help="Caminho para a wordlist .txt")

    # ── 3. fuzz ───────────────────────────────────────────────────────────────
    p_fuzz = sub.add_parser("fuzz", help="Fuzzing lógico em parâmetros numéricos")
    _add_arg_url(p_fuzz)
    _add_arg_payload(p_fuzz)
    _add_arg_headers(p_fuzz)
    _add_arg_metodo(p_fuzz)
    p_fuzz.add_argument("--timeout", type=int, default=15, metavar="SEG",
                        help="Timeout por requisição em segundos (padrão: 15)")

    # ── 4. otp ────────────────────────────────────────────────────────────────
    p_otp = sub.add_parser(
        "otp",
        help="Brute Force de OTP numérico sem rate limit (ex: painel /zadmin)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Força bruta de OTP numérico de N dígitos.\n"
            "Detecta o OTP correto por análise estatística (status/tamanho diferente da moda).\n\n"
            "Exemplo — OTP de 4 dígitos no painel /zadmin:\n"
            "  python main.py otp \\\n"
            "    --url https://alvo.com/zadmin/verify-otp \\\n"
            "    --payload '{\"email\":\"admin@email.com\"}' \\\n"
            "    --headers '{\"Content-Type\":\"application/json\"}' \\\n"
            "    --campo otp --digitos 4"
        ),
    )
    _add_arg_url(p_otp)
    _add_arg_payload(p_otp)
    _add_arg_headers(p_otp)
    p_otp.add_argument("--campo",       default="otp",
                       help="Nome do campo OTP no payload (padrão: 'otp')")
    p_otp.add_argument("--digitos",     type=int, default=4,
                       help="Quantidade de dígitos do OTP (padrão: 4 → 10.000 combos)")
    p_otp.add_argument("--tipo",        default="numerico",
                       choices=["numerico", "alfanumerico"],
                       help="Alfabeto: 'numerico' (0-9) ou 'alfanumerico' (a-z0-9)")
    p_otp.add_argument("--concorrencia", type=int, default=100,
                       help="Máximo de requisições simultâneas (padrão: 100)")
    p_otp.add_argument("--timeout",     type=int, default=20,
                       help="Timeout por requisição em segundos (padrão: 20)")

    # ── 5. paths ──────────────────────────────────────────────────────────────
    p_paths = sub.add_parser(
        "paths",
        help="Path Discovery estilo GoBuster — encontra rotas ocultas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Descobre caminhos/rotas ocultas em aplicações web.\n"
            "Usa lista embutida de 70+ paths comuns (admin, zadmin, api/v1...)\n"
            "ou wordlist customizada.\n\n"
            "Exemplo:\n"
            "  python main.py paths --url https://ruyter.com\n"
            "  python main.py paths --url https://alvo.com --wordlist wordlists/paths.txt\n"
            "  python main.py paths --url https://alvo.com --extensoes .php .asp"
        ),
    )
    p_paths.add_argument("--url",          required=True,
                         help="URL base do alvo (ex: https://refunds.ruyter.com)")
    p_paths.add_argument("--wordlist",     default=None,
                         help="Wordlist customizada (uma rota por linha). Padrão: lista embutida")
    p_paths.add_argument("--concorrencia", type=int, default=50,
                         help="Máximo de GETs simultâneos (padrão: 50)")
    p_paths.add_argument("--ignorar",      nargs="+", type=int, default=[404, 410],
                         metavar="STATUS",
                         help="Status HTTP a ignorar (padrão: 404 410)")
    p_paths.add_argument("--extensoes",    nargs="+", default=None,
                         metavar="EXT",
                         help="Extensões a concatenar nos paths (ex: .php .asp .json)")
    p_paths.add_argument("--timeout",      type=int, default=10,
                         help="Timeout por requisição em segundos (padrão: 10)")

    # ── 6. scan ───────────────────────────────────────────────────────────────
    p_scan = sub.add_parser(
        "scan",
        help="Client-Side Trust Scan — seed, is_winner, AES, roles no front-end",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Detecta vulnerabilidades de Client-Side Trust:\n"
            "  - Parâmetros que deveriam ser gerados pelo servidor (seed, is_winner, time_left...)\n"
            "  - Lógica crítica em JavaScript (Math.random, AES decrypt, role no front)\n"
            "  - Cookies sem HttpOnly/Secure\n"
            "  - Rotas admin expostas no bundle JS\n\n"
            "Exemplo — analisar payload + JS da plataforma:\n"
            "  python main.py scan \\\n"
            "    --url https://comunidade.ruyter.com \\\n"
            "    --payload '{\"amount\":100,\"seed\":1234567890,\"color\":\"green\"}' \\\n"
            "    --headers '{\"Authorization\":\"Bearer TOKEN\"}'"
        ),
    )
    p_scan.add_argument("--url",     default=None,
                        help="URL da plataforma para baixar e analisar o JavaScript")
    p_scan.add_argument("--payload", default=None,
                        help="Payload JSON capturado da requisição para analisar parâmetros")
    _add_arg_headers(p_scan, required=False)
    p_scan.add_argument("--apenas-payload", action="store_true",
                        help="Analisar apenas o payload (sem baixar JS)")
    p_scan.add_argument("--apenas-js",      action="store_true",
                        help="Analisar apenas o JavaScript (sem checar payload)")

    return parser


# ─────────────────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print(BANNER)
    parser = criar_parser()
    args = parser.parse_args()

    # ── race ──────────────────────────────────────────────────────────────────
    if args.modulo == "race":
        try:
            asyncio.run(
                race_condition_test(
                    url=args.url,
                    payload_str=args.payload,
                    headers_str=args.headers,
                    num_conexoes=args.conexoes,
                )
            )
        except ValueError as e:
            print(str(e)); sys.exit(1)

    # ── jwt ───────────────────────────────────────────────────────────────────
    elif args.modulo == "jwt":
        resultado = jwt_analisar_e_bruteforce(
            token=args.token,
            wordlist_path=args.wordlist,
        )
        if resultado.get("secret"):
            print(
                f"\n[RESUMO] SECRET: '{resultado['secret']}' | "
                f"Tentativas: {resultado['tentativas']:,}"
            )

    # ── fuzz ──────────────────────────────────────────────────────────────────
    elif args.modulo == "fuzz":
        try:
            alertas = fuzzing_logico(
                url=args.url,
                payload_str=args.payload,
                headers_str=args.headers,
                metodo=args.metodo,
                timeout=args.timeout,
            )
            sys.exit(1 if alertas else 0)
        except ValueError as e:
            print(str(e)); sys.exit(1)

    # ── otp ───────────────────────────────────────────────────────────────────
    elif args.modulo == "otp":
        try:
            suspeitos = asyncio.run(
                otp_bruteforce(
                    url=args.url,
                    payload_str=args.payload,
                    headers_str=args.headers,
                    campo_otp=args.campo,
                    digitos=args.digitos,
                    tipo=args.tipo,
                    concorrencia=args.concorrencia,
                    timeout_seg=args.timeout,
                )
            )
            sys.exit(0 if not suspeitos else 0)
        except ValueError as e:
            print(str(e)); sys.exit(1)

    # ── paths ─────────────────────────────────────────────────────────────────
    elif args.modulo == "paths":
        try:
            encontrados = asyncio.run(
                path_discovery(
                    url_base=args.url,
                    wordlist_path=args.wordlist,
                    concorrencia=args.concorrencia,
                    status_ignorados=args.ignorar,
                    timeout_seg=args.timeout,
                    extensoes=args.extensoes,
                )
            )
            sys.exit(0)
        except ValueError as e:
            print(str(e)); sys.exit(1)

    # ── scan ──────────────────────────────────────────────────────────────────
    elif args.modulo == "scan":
        if not args.url and not args.payload:
            print("[ERRO] Forneça pelo menos --url ou --payload para o scan.")
            sys.exit(1)

        achados = client_trust_scan(
            url=args.url,
            payload_str=args.payload,
            headers_str=args.headers,
            apenas_payload=args.apenas_payload,
            apenas_js=args.apenas_js,
        )
        sys.exit(1 if achados else 0)


if __name__ == "__main__":
    main()
