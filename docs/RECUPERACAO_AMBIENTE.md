# Recuperacao do ambiente ProCash

Este documento descreve a reconstrucao minima do ambiente a partir do repositorio Git.

## O que o Git recupera

O repositorio deve preservar o codigo-fonte, migrations, dependencias declaradas e este contrato de configuracao.

O banco SQLite de desenvolvimento nao e considerado dado operacional. Ele pode ser recriado. O superuser tambem pode ser recriado.

## Segredos e arquivos privados

Nunca versionar:

- `.env` com valores reais;
- certificados A1 (`.pfx` / `.p12`);
- chaves privadas;
- senhas;
- banco SQLite local;
- backups locais com dados privados.

O arquivo `.env.example` e apenas um contrato sem segredos.

## Reconstrucao basica

1. Clonar o repositorio e entrar na branch/commit desejado.
2. Criar e ativar um ambiente virtual Python.
3. Instalar as dependencias:

   `pip install -r requirements.txt`

4. Copiar `.env.example` para `.env`.
5. Gerar uma `SECRET_KEY` nova e secreta para o ambiente.
6. Revisar `ENVIRONMENT`, `ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS`.
7. Se necessario, definir `PROCASH_CERTIFICADOS_A1_DIR` para um diretorio privado. Se omitida, o codigo atual usa `BASE_DIR/certificados`.
8. Aplicar as migrations:

   `python manage.py migrate`

9. Recriar o administrador local:

   `python manage.py createsuperuser`

10. Executar:

    `python manage.py check`

## Certificado A1

O certificado real e sua senha nao fazem parte da recuperacao via Git.

O diretorio configurado por `PROCASH_CERTIFICADOS_A1_DIR` deve ser tratado como armazenamento privado. A estrategia definitiva para disponibilizacao segura da senha A1 em runtime pertence ao bloco fiscal de seguranca e nao deve ser substituida por senha em texto puro no repositorio.

## Historico de diagnostico

A pasta `diagnostico` e ignorada pelo Git e funciona como trilha tecnica local. Os checkpoints de codigo publicados no Git sao a fonte de verdade para recuperar o estado atual do software.

Relatorios tecnicos que se deseje preservar a longo prazo devem ser copiados para um armazenamento externo/backup separado; nao e necessario versionar centenas de arquivos temporarios de diagnostico no repositorio principal.
