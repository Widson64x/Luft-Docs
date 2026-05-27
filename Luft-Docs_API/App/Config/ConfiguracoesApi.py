"""Configuracoes centralizadas da API LuftDocs."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import quote_plus

from dotenv import load_dotenv
from luftcore import SqlAlchemyExtension

from App.Shared.ExcecoesAplicacao import ConfiguracaoAplicacaoErro


MONOREPO_ROOT = Path(__file__).resolve().parents[3]
CAMINHO_DOTENV = MONOREPO_ROOT / ".env"

load_dotenv(dotenv_path=CAMINHO_DOTENV, override=False)


def obterVersaoMonorepo() -> str:
	caminhoVersao = MONOREPO_ROOT / "_version.py"

	try:
		namespace: Dict[str, str] = {}
		exec(caminhoVersao.read_text(encoding="utf-8"), namespace)
		versao = str(namespace.get("__version__", "")).strip()
		if versao:
			return versao
	except OSError:
		pass

	return "0.1.0"


def _removerAspasOpcionais(valor: Optional[str]) -> Optional[str]:
	if valor is None:
		return None

	valorNormalizado = valor.strip()
	if (
		len(valorNormalizado) >= 2
		and valorNormalizado[0] == valorNormalizado[-1]
		and valorNormalizado[0] in {'"', "'"}
	):
		return valorNormalizado[1:-1].strip()
	return valorNormalizado


def obterVariavelAmbiente(nomeVariavel: str, valorPadrao: Optional[str] = None) -> Optional[str]:
	valorVariavel = _removerAspasOpcionais(os.getenv(nomeVariavel))
	if not valorVariavel:
		return valorPadrao
	return valorVariavel


def obterPrimeiraVariavelAmbiente(*nomesVariaveis: str, valorPadrao: Optional[str] = None) -> Optional[str]:
	for nomeVariavel in nomesVariaveis:
		valorVariavel = obterVariavelAmbiente(nomeVariavel)
		if valorVariavel:
			return valorVariavel
	return valorPadrao


def sincronizarTokenAcessoLuftCore() -> None:
	tokenProjeto = obterVariavelAmbiente("TOKEN_ACESSO")
	tokenFramework = _removerAspasOpcionais(os.getenv("LUFTCORE_TOKEN_ACESSO"))
	if tokenProjeto and not tokenFramework:
		os.environ["LUFTCORE_TOKEN_ACESSO"] = tokenProjeto


def obterVariavelAmbienteObrigatoria(nomeVariavel: str, tamanhoMinimo: int = 1) -> str:
	"""Recupera uma variavel obrigatoria do ambiente com validacao minima.

	Args:
		nomeVariavel: Nome da variavel esperada no ambiente.
		tamanhoMinimo: Quantidade minima de caracteres aceita para o valor.

	Returns:
		str: Valor lido do ambiente apos normalizacao.
	"""
	valorVariavel = obterVariavelAmbiente(nomeVariavel, "") or ""
	if not valorVariavel:
		raise ConfiguracaoAplicacaoErro(
			f"A variavel {nomeVariavel} deve ser definida no arquivo .env ou no ambiente."
		)
	if len(valorVariavel) < tamanhoMinimo:
		raise ConfiguracaoAplicacaoErro(
			f"A variavel {nomeVariavel} deve conter ao menos {tamanhoMinimo} caracteres."
		)
	return valorVariavel


def obterBooleanoAmbiente(nomeVariavel: str, valorPadrao: bool = False) -> bool:
	valorVariavel = obterVariavelAmbiente(nomeVariavel)
	if valorVariavel is None:
		return valorPadrao
	return valorVariavel.lower() in {"1", "true", "yes", "sim", "on"}


def obterTokenVaultCriptografado() -> str:
	tokenVault = (
		obterVariavelAmbiente("VAULT_TOKEN_CRIPTOGRAFADO")
		or obterVariavelAmbiente("VAULT_TOKEN")
		or ""
	)
	if tokenVault.startswith(("hvs.", "s.")):
		raise ConfiguracaoAplicacaoErro(
			"VAULT_TOKEN deve conter o valor criptografado gerado pela CLI do LuftCore."
		)
	return tokenVault


sincronizarTokenAcessoLuftCore()


def resolverAmbienteVault(ambienteAplicacao: str, ambienteVault: Optional[str]) -> str:
	ambienteVaultNormalizado = (ambienteVault or "").strip().lower()
	if ambienteVaultNormalizado in {"desenvolvimento", "dev", "development"}:
		return "desenvolvimento"
	if ambienteVaultNormalizado in {"homolog", "homologacao", "homologation", "hml"}:
		return "homologacao"
	if ambienteVaultNormalizado in {"prod", "producao", "production"}:
		return "producao"

	ambienteAplicacaoNormalizado = (ambienteAplicacao or "development").strip().lower()
	if ambienteAplicacaoNormalizado in {"prod", "producao", "production"}:
		return "producao"
	if ambienteAplicacaoNormalizado in {"homolog", "homologacao", "homologation", "hml"}:
		return "homologacao"
	return "desenvolvimento"


@dataclass(frozen=True)
class ConfiguracoesApi:
	"""Representa todas as configuracoes de execucao da API."""

	nomeAplicacao: str
	versaoAplicacao: str
	ambienteAplicacao: str
	prefixoApi: str
	nomeCabecalhoChaveApi: str
	chaveAcessoApi: str
	chaveSecreta: str
	algoritmoToken: str
	horasExpiracaoToken: int
	segredoSessao: str
	modoApiFalso: bool
	exibirLogsBanco: bool
	usuarioBancoDados: str = ""
	senhaBancoDados: str = ""
	hostBancoDados: str = ""
	portaBancoDados: str = ""
	nomeBancoDados: str = ""
	vaultAddr: str = ""
	vaultNamespace: str = "luft"
	vaultTokenCriptografado: str = ""
	tokenAcesso: str = ""
	ambienteVaultAtual: str = "desenvolvimento"
	caminhoSegredoSqlServer: str = ""
	driverBancoDados: str = "ODBC Driver 17 for SQL Server"
	trustServerCertificate: str = "yes"
	claimSubjectToken: str = "s"
	claimExpiracaoToken: str = "e"

	def obterCabecalhoJwt(self) -> Dict[str, str]:
		"""Retorna o cabecalho minimo utilizado na criacao dos tokens JWT."""
		return {"alg": self.algoritmoToken}

	def possuiConfiguracaoVaultCompleta(self) -> bool:
		return all([self.vaultAddr, self.vaultTokenCriptografado, self.tokenAcesso])

	def possuiConfiguracaoVaultParcial(self) -> bool:
		return any([self.vaultAddr, self.vaultTokenCriptografado, self.tokenAcesso]) and not self.possuiConfiguracaoVaultCompleta()

	def utilizaDriverPyodbc(self) -> bool:
		driverNormalizado = (self.driverBancoDados or "").strip().lower()
		return driverNormalizado.startswith("odbc driver") or driverNormalizado in {"pyodbc", "mssql+pyodbc"}

	def obterExtensaoBancoDados(self) -> Optional[SqlAlchemyExtension]:
		if self.modoApiFalso:
			return None

		if self.possuiConfiguracaoVaultParcial():
			ausentes = [
				nomeVariavel
				for nomeVariavel, valor in {
					"VAULT_ADDR": self.vaultAddr,
					"VAULT_TOKEN": self.vaultTokenCriptografado,
					"TOKEN_ACESSO": self.tokenAcesso,
				}.items()
				if not valor
			]
			raise ConfiguracaoAplicacaoErro(
				"Configuracao do Vault incompleta. Variaveis ausentes: " + ", ".join(ausentes)
			)

		if not self.possuiConfiguracaoVaultCompleta():
			return None

		parametrosConexao = None
		if self.utilizaDriverPyodbc():
			parametrosConexao = {"TrustServerCertificate": self.trustServerCertificate}

		return SqlAlchemyExtension(
			vault_addr=self.vaultAddr,
			vault_token_criptografado=self.vaultTokenCriptografado,
			token_acesso=self.tokenAcesso,
			caminho_segredo=self.caminhoSegredoSqlServer,
			tipo_banco="mssql",
			driver_banco=self.driverBancoDados,
			parametros_conexao=parametrosConexao,
		)

	def obterDescricaoBancoDados(self) -> Dict[str, str]:
		extensaoBanco = self.obterExtensaoBancoDados()
		if extensaoBanco is not None:
			urlBanco = extensaoBanco.obter_engine().url
			return {
				"usuario": getattr(urlBanco, "username", None) or "N/D",
				"host": getattr(urlBanco, "host", None) or "N/D",
				"porta": str(getattr(urlBanco, "port", None) or ""),
				"nome_banco": getattr(urlBanco, "database", None) or "N/D",
				"via_luftcore": "true",
			}

		return {
			"usuario": self.usuarioBancoDados or "N/D",
			"host": self.hostBancoDados or "N/D",
			"porta": self.portaBancoDados or "",
			"nome_banco": self.nomeBancoDados or "N/D",
			"via_luftcore": "false",
		}

	def obterUrlBancoDados(self) -> str:
		"""Monta a URL de conexao com o banco SQL Server."""
		extensaoBanco = self.obterExtensaoBancoDados()
		if extensaoBanco is not None:
			return extensaoBanco.obter_uri_conexao()

		configuracoesBanco = {
			"DB_USER": self.usuarioBancoDados,
			"DB_PASS": self.senhaBancoDados,
			"DB_HOST": self.hostBancoDados,
			"DB_PORT": self.portaBancoDados,
			"DB_NAME": self.nomeBancoDados,
		}
		camposFaltantes = [nomeCampo for nomeCampo, valorCampo in configuracoesBanco.items() if not valorCampo]
		if camposFaltantes:
			raise ConfiguracaoAplicacaoErro(
				"Variaveis de banco ausentes: " + ", ".join(camposFaltantes)
			)

		senhaCodificada = quote_plus(self.senhaBancoDados)
		if self.utilizaDriverPyodbc():
			nomeDriverOdbc = self.driverBancoDados or "ODBC Driver 17 for SQL Server"
			driverNormalizado = nomeDriverOdbc.strip().lower()
			if driverNormalizado in {"pyodbc", "mssql+pyodbc", ""}:
				nomeDriverOdbc = "ODBC Driver 17 for SQL Server"

			driverCodificado = quote_plus(nomeDriverOdbc)
			trustServer = quote_plus(self.trustServerCertificate or "yes")
			return (
				f"mssql+pyodbc://{self.usuarioBancoDados}:{senhaCodificada}"
				f"@{self.hostBancoDados}:{self.portaBancoDados}/{self.nomeBancoDados}"
				f"?TrustServerCertificate={trustServer}&driver={driverCodificado}"
			)

		driverNormalizado = (self.driverBancoDados or "").strip().lower()
		dialetoBanco = "mssql+pymssql"
		if driverNormalizado.startswith("mssql+"):
			dialetoBanco = self.driverBancoDados
		return (
			f"{dialetoBanco}://{self.usuarioBancoDados}:{senhaCodificada}"
			f"@{self.hostBancoDados}:{self.portaBancoDados}/{self.nomeBancoDados}"
		)


def carregarConfiguracoesApi() -> ConfiguracoesApi:
	"""Carrega as configuracoes da API a partir das variaveis de ambiente."""
	try:
		horasExpiracaoToken = int(obterVariavelAmbiente("ACCESS_TOKEN_EXPIRE_HOURS", "2") or "2")
	except ValueError as erro:
		raise ConfiguracaoAplicacaoErro(
			"A variavel ACCESS_TOKEN_EXPIRE_HOURS deve conter um numero inteiro valido."
		) from erro

	ambienteAplicacao = obterVariavelAmbiente("APP_ENV", "development") or "development"
	modoApiFalso = obterBooleanoAmbiente("MODO_API_FALSO", False)
	vaultNamespace = obterVariavelAmbiente("VAULT_NAMESPACE", "luft") or "luft"
	ambienteVaultAtual = resolverAmbienteVault(
		ambienteAplicacao,
		obterVariavelAmbiente("AMBIENTE_ATUAL"),
	)
	nomeCabecalhoChaveApi = (
		obterVariavelAmbiente("API_ACCESS_KEY_HEADER", "X-API-Key")
		or "X-API-Key"
	)

	return ConfiguracoesApi(
		nomeAplicacao=(
			obterPrimeiraVariavelAmbiente("API_APP_NAME", "APP_NAME", valorPadrao="luftdocs_api")
			or "luftdocs_api"
		),
		versaoAplicacao=(
			obterPrimeiraVariavelAmbiente(
				"API_APP_VERSION_OVERRIDE",
				"APP_VERSION_OVERRIDE",
				valorPadrao=obterVersaoMonorepo(),
			)
			or obterVersaoMonorepo()
		),
		ambienteAplicacao=ambienteAplicacao,
		prefixoApi=(
			obterPrimeiraVariavelAmbiente("API_PREFIX", "ROUTE_PREFIX", valorPadrao="/luft-api")
			or "/luft-api"
		),
		nomeCabecalhoChaveApi=nomeCabecalhoChaveApi,
		chaveAcessoApi=obterVariavelAmbienteObrigatoria("API_ACCESS_KEY", tamanhoMinimo=32),
		chaveSecreta=obterVariavelAmbienteObrigatoria("SECRET_KEY", tamanhoMinimo=32),
		algoritmoToken=obterVariavelAmbiente("ALGORITHM", "HS256") or "HS256",
		horasExpiracaoToken=horasExpiracaoToken,
		segredoSessao=obterVariavelAmbienteObrigatoria("SESSION_SECRET", tamanhoMinimo=32),
		modoApiFalso=modoApiFalso,
		exibirLogsBanco=obterBooleanoAmbiente("DB_CONNECT_LOGS", True),
		usuarioBancoDados=obterVariavelAmbiente("DB_USER", "") or "",
		senhaBancoDados=obterVariavelAmbiente("DB_PASS", "") or "",
		hostBancoDados=obterVariavelAmbiente("DB_HOST", "") or "",
		portaBancoDados=obterVariavelAmbiente("DB_PORT", "") or "",
		nomeBancoDados=obterVariavelAmbiente("DB_NAME", "") or "",
		vaultAddr=obterVariavelAmbiente("VAULT_ADDR", "") or "",
		vaultNamespace=vaultNamespace,
		vaultTokenCriptografado=obterTokenVaultCriptografado(),
		tokenAcesso=obterVariavelAmbiente("TOKEN_ACESSO", "") or "",
		ambienteVaultAtual=ambienteVaultAtual,
		caminhoSegredoSqlServer=f"{vaultNamespace}/{ambienteVaultAtual}/sqlserver",
		driverBancoDados=(
			obterVariavelAmbiente("DB_DRIVER")
			or obterVariavelAmbiente("SQL_DRIVER")
			or obterVariavelAmbiente("SS_ODBC_DRIVER")
			or "ODBC Driver 17 for SQL Server"
		),
		trustServerCertificate=(
			obterVariavelAmbiente("SQL_TRUST_SERVER_CERTIFICATE", "yes")
			or "yes"
		),
	)
