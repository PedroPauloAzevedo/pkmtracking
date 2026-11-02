"""
TESTE DE SEGURANÇA: o painel recusa pedidos de outros sites e aceita os dele mesmo.
Uso:  python testes/teste_seguranca.py <pasta do programa (cópia de teste)>
Não muda nada: os pedidos recusados param antes de chegar às rotas; os aceitos só leem dados.
"""
import sys

sys.path.insert(0, sys.argv[1])
import app as programa  # noqa: E402

c = programa.app.test_client()
casos = [
    # (descrição, método, rota, cabeçalhos, código esperado)
    ("painel lendo o status", "get", "/api/status", {"Host": "127.0.0.1:8765"}, 200),
    ("painel (mesma origem, POST)", "post", "/api/regras/testar",
     {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765", "Sec-Fetch-Site": "same-origin"}, 200),
    ("script local sem Origin (POST)", "post", "/api/regras/testar", {"Host": "127.0.0.1:8765"}, 200),
    ("outro site tentando mudar a configuração", "post", "/api/config",
     {"Host": "127.0.0.1:8765", "Origin": "https://site-malicioso.example", "Sec-Fetch-Site": "cross-site"}, 403),
    ("outro site sem Origin, só Sec-Fetch-Site", "post", "/api/atualizacao/instalar",
     {"Host": "127.0.0.1:8765", "Sec-Fetch-Site": "cross-site"}, 403),
    ("outra porta local se passando pelo painel", "post", "/api/encerrar",
     {"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:9999"}, 403),
    ("DNS rebinding (Host de outro domínio)", "get", "/api/status", {"Host": "site-malicioso.example:8765"}, 403),
    # /web/ entrega só as partes do painel (CSS e JS de dentro de web/), nunca outros arquivos do programa
    ("parte do painel (web/js/base.js)", "get", "/web/js/base.js", {"Host": "127.0.0.1:8765"}, 200),
    ("/web/ não entrega outro tipo de arquivo", "get", "/web/LEIA-ME.md", {"Host": "127.0.0.1:8765"}, 404),
    ("/web/ não sai da pasta web (app.py)", "get", "/web/../app.py", {"Host": "127.0.0.1:8765"}, 404),
    ("/web/ não sai da pasta web (dados)", "get", "/web/%2e%2e/dados/config.js", {"Host": "127.0.0.1:8765"}, 404),
]
falhas = 0
for nome, metodo, rota, cab, esperado in casos:
    corpo = '{"linha": "Ana drew a card."}' if rota == "/api/regras/testar" else '{"github_repo": "atacante/repo"}'
    r = getattr(c, metodo)(rota, headers=cab, data=corpo if metodo == "post" else None, content_type="text/plain")
    ok = r.status_code == esperado
    falhas += not ok
    print(f"{'OK ' if ok else 'ERRO'} {nome:45} -> {r.status_code} (esperado {esperado})")
print("OK" if not falhas else f"{falhas} FALHA(S)")
sys.exit(1 if falhas else 0)
