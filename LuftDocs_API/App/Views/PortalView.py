"""Renderizacao do portal HTML da API."""

from App.Config.ConfiguracoesApi import ConfiguracoesApi


def gerarHtmlPortal(configuracoes: ConfiguracoesApi) -> str:
    """Gera o HTML do portal visual da API.

    Args:
        configuracoes: Configuracoes centralizadas da aplicacao.

    Returns:
        str: Documento HTML exibido no endpoint de portal da API.
    """
    return f"""
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>LuftDocs API</title>
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;700;800&display=swap" rel="stylesheet" />
<style>
:root {{
  --fundo: #edf3f8;
  --painel: #ffffff;
  --painel-secundario: #f6f9fc;
  --texto: #102033;
  --texto-suave: #5f7287;
  --primaria: #0a3d6b;
  --primaria-clara: #1677c5;
  --borda: rgba(16, 32, 51, 0.12);
  --sombra: 0 20px 40px rgba(10, 61, 107, 0.10);
  --raio: 20px;
}}
* {{ box-sizing: border-box; }}
body {{
  margin: 0;
  min-height: 100vh;
  background:
    radial-gradient(circle at top right, rgba(22, 119, 197, 0.18), transparent 30%),
    linear-gradient(180deg, #f7fbfe 0%, var(--fundo) 100%);
  color: var(--texto);
  font-family: "Manrope", "Segoe UI", sans-serif;
}}
.cabecalho {{
  padding: 24px clamp(20px, 4vw, 48px);
}}
.marca {{
  display: inline-flex;
  align-items: center;
  gap: 14px;
  padding: 12px 18px;
  border: 1px solid var(--borda);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.78);
  backdrop-filter: blur(12px);
}}
.marca-sigla {{
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, var(--primaria), var(--primaria-clara));
  color: #ffffff;
  font-weight: 800;
  letter-spacing: 0.08em;
}}
.marca-texto strong {{
  display: block;
  font-size: 0.95rem;
}}
.marca-texto span {{
  color: var(--texto-suave);
  font-size: 0.82rem;
}}
.conteudo {{
  width: min(1180px, calc(100% - 40px));
  margin: 0 auto 40px auto;
  display: grid;
  gap: 24px;
}}
.hero {{
  display: grid;
  grid-template-columns: minmax(0, 1.3fr) minmax(280px, 0.7fr);
  gap: 24px;
}}
.cartao {{
  background: var(--painel);
  border: 1px solid var(--borda);
  border-radius: var(--raio);
  box-shadow: var(--sombra);
  padding: clamp(22px, 3vw, 32px);
}}
.cartao-destaque {{
  background:
    linear-gradient(160deg, rgba(10, 61, 107, 0.96), rgba(22, 119, 197, 0.92)),
    var(--painel);
  color: #ffffff;
}}
.cartao-destaque p,
.cartao-destaque li,
.cartao-destaque small {{
  color: rgba(255, 255, 255, 0.82);
}}
h1 {{
  margin: 0 0 10px 0;
  font-size: clamp(2rem, 4vw, 3.1rem);
  line-height: 1.05;
}}
h2 {{
  margin: 0 0 18px 0;
  font-size: 1.35rem;
}}
p {{
  margin: 0;
  line-height: 1.6;
}}
.acoes {{
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 26px;
}}
.botao {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
  border-radius: 999px;
  text-decoration: none;
  font-weight: 700;
  border: 1px solid transparent;
}}
.botao-primario {{
  background: #ffffff;
  color: var(--primaria);
}}
.botao-secundario {{
  background: transparent;
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.24);
}}
.estado {{
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
  padding: 10px 14px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.14);
  font-size: 0.9rem;
}}
.estado::before {{
  content: "";
  width: 10px;
  height: 10px;
  border-radius: 999px;
  background: #78f0a8;
}}
.grade-kpi {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 28px;
}}
.kpi {{
  padding: 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.16);
}}
.kpi strong {{
  display: block;
  font-size: 1.1rem;
  margin-bottom: 4px;
}}
.lista-links {{
  display: grid;
  gap: 12px;
}}
.item-link {{
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  background: var(--painel-secundario);
  border: 1px solid var(--borda);
}}
.item-link a {{
  color: var(--primaria);
  font-weight: 700;
  text-decoration: none;
}}
.item-link span {{
  color: var(--texto-suave);
  font-size: 0.92rem;
}}
.mapa-endpoints {{
  display: grid;
  gap: 14px;
}}
.endpoint {{
  display: flex;
  justify-content: space-between;
  gap: 14px;
  align-items: center;
  padding: 16px 18px;
  border-radius: 18px;
  border: 1px solid var(--borda);
  background: #ffffff;
}}
.endpoint code {{
  font-family: "Cascadia Code", Consolas, monospace;
  font-size: 0.95rem;
  color: var(--primaria);
}}
.endpoint small {{
  color: var(--texto-suave);
}}
@media (max-width: 900px) {{
  .hero {{
    grid-template-columns: 1fr;
  }}
  .grade-kpi {{
    grid-template-columns: 1fr 1fr;
  }}
}}
@media (max-width: 560px) {{
  .conteudo {{
    width: min(100%, calc(100% - 24px));
  }}
  .grade-kpi {{
    grid-template-columns: 1fr;
  }}
  .endpoint {{
    flex-direction: column;
    align-items: flex-start;
  }}
}}
</style>
</head>
<body>
  <header class="cabecalho">
    <div class="marca">
      <div class="marca-sigla">LD</div>
      <div class="marca-texto">
        <strong>LuftDocs API</strong>
        <span>Portal tecnico da aplicacao</span>
      </div>
    </div>
  </header>

  <main class="conteudo">
    <section class="hero">
      <article class="cartao cartao-destaque">
        <div class="estado">Aplicacao ativa em {configuracoes.ambienteAplicacao}</div>
        <h1>Camada de autenticacao e consulta do LuftDocs.</h1>
        <p>
          Esta API foi reorganizada com separacao explicita entre bootstrap, controllers,
          services, repositories, models e infraestrutura. Abaixo estao os atalhos operacionais
          mais usados para documentacao, monitoramento e validacao da aplicacao.
        </p>
        <div class="acoes">
          <a class="botao botao-primario" href="./docs">Abrir Swagger</a>
          <a class="botao botao-secundario" href="./redoc">Abrir Redoc</a>
          <a class="botao botao-secundario" href="./metrics">Ver metricas</a>
        </div>
        <div class="grade-kpi">
          <div class="kpi">
            <strong>/docs</strong>
            <small>Interface interativa da API</small>
          </div>
          <div class="kpi">
            <strong>/metrics</strong>
            <small>Observabilidade Prometheus</small>
          </div>
          <div class="kpi">
            <strong>v{configuracoes.versaoAplicacao}</strong>
            <small>Versao publicada da API</small>
          </div>
        </div>
      </article>

      <aside class="cartao">
        <h2>Navegacao rapida</h2>
        <div class="lista-links">
          <div class="item-link">
            <a href="./docs">Swagger UI</a>
            <span>Exploracao e testes de endpoints.</span>
          </div>
          <div class="item-link">
            <a href="./redoc">Redoc</a>
            <span>Leitura descritiva do contrato OpenAPI.</span>
          </div>
          <div class="item-link">
            <a href="./openapi.json">OpenAPI JSON</a>
            <span>Schema consumivel por automacoes e clientes.</span>
          </div>
          <div class="item-link">
            <a href="./links">Colecao de links</a>
            <span>Atalhos de operacao publicados pela API.</span>
          </div>
        </div>
      </aside>
    </section>

    <section class="cartao">
      <h2>Mapa de endpoints</h2>
      <div class="mapa-endpoints">
        <div class="endpoint">
          <div>
            <code>{configuracoes.prefixoApi}/</code>
            <small>Health check da API montada.</small>
          </div>
          <strong>GET</strong>
        </div>
        <div class="endpoint">
          <div>
            <code>{configuracoes.prefixoApi}/api/user</code>
            <small>Recupera usuario e emite token JWT a partir do hash do login.</small>
          </div>
          <strong>GET</strong>
        </div>
        <div class="endpoint">
          <div>
            <code>{configuracoes.prefixoApi}/api/token</code>
            <small>Valida um token e devolve o contexto do usuario autenticado.</small>
          </div>
          <strong>GET</strong>
        </div>
        <div class="endpoint">
          <div>
            <code>{configuracoes.prefixoApi}/api/logout_token</code>
            <small>Revoga um token previamente emitido.</small>
          </div>
          <strong>POST</strong>
        </div>
      </div>
    </section>
  </main>
</body>
</html>
""".strip()