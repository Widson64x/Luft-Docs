"""Excecoes padronizadas da aplicacao LuftDocs."""


class ExcecaoAplicacao(Exception):
    """Representa a excecao base para falhas controladas da aplicacao."""


class RecursoNaoEncontradoErro(ExcecaoAplicacao):
    """Indica que o recurso solicitado nao foi localizado."""


class AutenticacaoErro(ExcecaoAplicacao):
    """Indica falha de autenticacao, autorizacao ou validade de token."""


class ConfiguracaoAplicacaoErro(ExcecaoAplicacao):
    """Indica configuracao invalida ou incompleta da aplicacao."""


class InfraestruturaAplicacaoErro(ExcecaoAplicacao):
    """Indica falha de infraestrutura em componentes externos."""