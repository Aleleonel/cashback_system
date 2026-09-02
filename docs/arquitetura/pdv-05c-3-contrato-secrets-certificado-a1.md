# PDV-05C-3 - Contrato de secrets do certificado A1

## 1. Objetivo

Definir como a senha do certificado digital A1 deve ser recebida, protegida,
resolvida em runtime e descartada no fluxo fiscal do ProCash.

Este contrato aplica-se ao upload, assinatura XML, autorizacao NFC-e e consulta
de protocolo. A implementacao deve funcionar para multiplas empresas e lojas.

## 2. Principios obrigatorios

1. A senha A1 nunca deve ser persistida em texto puro.
2. A senha A1 nunca deve ser armazenada no repositorio, settings, fixtures,
   logs, mensagens, XML fiscal ou campos de auditoria.
3. O banco pode guardar apenas uma referencia opaca do segredo.
4. A chave-mestra usada para criptografia deve existir somente no ambiente de
   execucao e deve ser diferente por ambiente.
5. Certificado, senha e chave-mestra nao podem compartilhar o mesmo artefato de
   armazenamento.
6. A senha descriptografada deve existir apenas em memoria e pelo menor tempo
   necessario para abrir o PKCS#12.
7. Erros externos nunca devem revelar senha, chave-mestra ou conteudo secreto.
8. Testes devem usar exclusivamente PKCS#12 sintetico e senha ficticia.
9. Testes e validacoes nao podem comunicar com a SEFAZ.

## 3. Persistencia permitida

`ConfiguracaoEmissaoFiscalLoja` deve continuar guardando a referencia privada
do arquivo A1 e podera guardar uma referencia opaca separada para a senha:

- `certificado_a1_referencia`: referencia do arquivo PKCS#12 privado;
- `certificado_a1_segredo_referencia`: identificador opaco do segredo.

Nenhum desses campos pode conter a senha ou a chave-mestra.

## 4. Contrato do provedor de secrets

O dominio fiscal deve depender de um provedor com estas operacoes conceituais:

- `armazenar_senha_certificado_a1(loja_id, senha) -> referencia`;
- `resolver_senha_certificado_a1(referencia) -> senha`;
- `remover_senha_certificado_a1(referencia) -> None`.

A implementacao local inicial deve:

- criptografar a senha de forma autenticada;
- usar chave-mestra fornecida por variavel de ambiente obrigatoria;
- gravar o segredo criptografado em diretorio privado;
- aplicar permissoes restritivas quando suportadas pelo sistema operacional;
- gerar referencias aleatorias, sem dados da loja ou da senha;
- rejeitar referencia fora do diretorio privado;
- realizar gravacao atomica por arquivo temporario e substituicao;
- remover temporarios mesmo quando ocorrer erro.

O contrato deve permitir substituicao futura por um Secret Manager sem mudar os
servicos de assinatura, autorizacao ou consulta.

## 5. Fluxo de upload e rotacao

1. A view recebe arquivo e senha pelo formulario protegido.
2. O PKCS#12 sintetico ou real e validado em memoria.
3. O arquivo A1 e armazenado na area privada.
4. A senha e criptografada pelo provedor e uma referencia opaca e retornada.
5. As duas referencias sao persistidas na configuracao da loja.
6. A senha em texto puro nao e retornada, serializada ou persistida.
7. Em falha, arquivo novo e segredo novo devem ser removidos.
8. A substituicao antiga so pode ser removida depois do commit bem-sucedido.
9. Edicao sem novo upload deve preservar as duas referencias existentes.

## 6. Fluxo de runtime

Os entrypoints publicos nao devem exigir que view, PDV ou chamador forneca senha:

- `assinar_documento_fiscal(documento, ...)`;
- `executar_autorizacao_nfce_sp(documento, ...)`;
- `executar_consulta_protocolo_nfce_sp(documento, ...)`.

Cada entrypoint deve carregar a configuracao da loja, obter a referencia opaca,
resolver a senha apenas no limite de abertura do PKCS#12 e deixar de referencia-la
assim que o objeto `CertificadoA1` for construido.

Injecao de dependencias para testes e permitida por parametro nomeado privado ou
adaptador, mas senha em texto puro nao pode fazer parte da API publica.

## 7. Falhas seguras

Devem existir erros de dominio sem valores sensiveis para:

- chave-mestra ausente ou invalida;
- referencia de segredo ausente ou invalida;
- segredo inexistente, corrompido ou impossivel de descriptografar;
- senha incompativel com o PKCS#12;
- tentativa de acesso fora do diretorio privado.

Mensagens ao usuario devem ser genericas. A causa tecnica pode ser encadeada
internamente, mas sua representacao nao pode ser enviada a logs ou respostas.

## 8. Contrato minimo de testes

Antes da integracao, os testes devem provar:

1. round-trip com senha ficticia;
2. arquivo persistido nao contem a senha ficticia;
3. chave errada nao descriptografa;
4. segredo adulterado nao descriptografa;
5. chave-mestra ausente falha de forma segura;
6. referencia fora da area privada e rejeitada;
7. remocao e idempotente;
8. upload invalido nao deixa arquivo ou segredo;
9. edicao sem upload preserva ambas as referencias;
10. assinatura resolve a senha sem recebe-la na API publica;
11. autorizacao resolve a senha sem recebe-la na API publica;
12. consulta resolve a senha sem recebe-la na API publica;
13. erros e logs nao contem a senha ficticia;
14. nenhum teste acessa certificado corporativo ou SEFAZ real.

## 9. Fora de escopo deste bloco

- certificado corporativo real;
- senha real;
- comunicacao com a SEFAZ;
- Secret Manager de provedor de nuvem;
- rotacao automatica da chave-mestra;
- commit, push ou deploy automatico.

## 10. Criterio de aceite da implementacao

A implementacao somente podera ser integrada quando testes focais, suite fiscal,
`manage.py check`, verificacao de migrations e inspecao do diff estiverem verdes,
sem segredo real e sem comunicacao externa.
