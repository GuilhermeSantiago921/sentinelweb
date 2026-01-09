# 📊 Google PageSpeed Insights API - Setup Guide

## O que é?

O Google PageSpeed Insights é uma ferramenta gratuita que analisa a performance do seu site e fornece recomendações de otimização. A API permite automatizar essas análises.

## Por que usar?

- ✅ **SEO**: Sites lentos são penalizados pelo Google
- ✅ **Conversão**: 1 segundo de atraso = 7% menos conversões
- ✅ **UX**: Usuários abandonam sites que demoram >3s
- ✅ **Core Web Vitals**: Métricas oficiais do Google

## Como obter a API Key (GRÁTIS)

### Passo 1: Acessar o Google Cloud Console

1. Acesse: https://console.cloud.google.com/
2. Faça login com sua conta Google (pode ser Gmail pessoal)

### Passo 2: Criar um Projeto

1. No topo da página, clique em **"Select a project"** (Selecionar projeto)
2. Clique em **"NEW PROJECT"** (Novo projeto)
3. Nome do projeto: `SentinelWeb` (ou outro nome de sua preferência)
4. Clique em **"CREATE"** (Criar)
5. Aguarde alguns segundos até o projeto ser criado

### Passo 3: Ativar a API PageSpeed Insights

1. No menu lateral, vá em **"APIs & Services"** > **"Library"** (Biblioteca)
   - OU acesse direto: https://console.cloud.google.com/apis/library
2. Na busca, digite: `PageSpeed Insights API`
3. Clique no card **"PageSpeed Insights API"**
4. Clique em **"ENABLE"** (Ativar)
5. Aguarde a ativação (leva ~10 segundos)

### Passo 4: Criar a API Key

1. No menu lateral, vá em **"APIs & Services"** > **"Credentials"** (Credenciais)
   - OU acesse: https://console.cloud.google.com/apis/credentials
2. Clique no botão **"+ CREATE CREDENTIALS"** (Criar credenciais)
3. Selecione **"API key"**
4. A chave será gerada automaticamente. **COPIE E GUARDE** ela!

Exemplo de chave: `AIzaSyD1234567890abcdefghijklmnopqrstuv`

### Passo 5: (RECOMENDADO) Restringir a API Key

**Por segurança**, restrinja a chave para usar apenas a API do PageSpeed:

1. Na tela de credenciais, clique no **ícone de lápis** (editar) ao lado da sua chave
2. Em **"API restrictions"** (Restrições de API), selecione:
   - ✅ **"Restrict key"** (Restringir chave)
3. Na lista, marque apenas: `PageSpeed Insights API`
4. Clique em **"SAVE"** (Salvar)

Isso impede que sua chave seja usada para outras APIs caso vaze.

### Passo 6: Configurar no SentinelWeb

1. Abra o arquivo `.env` na raiz do projeto
2. Adicione a linha:

```bash
GOOGLE_PAGESPEED_API_KEY=SUA_CHAVE_AQUI
```

Exemplo:
```bash
GOOGLE_PAGESPEED_API_KEY=AIzaSyD1234567890abcdefghijklmnopqrstuv
```

3. Salve o arquivo
4. Reinicie o Docker:

```bash
docker-compose restart
```

## Quota Gratuita

- **25,000 requisições por dia** (GRÁTIS)
- Suficiente para monitorar **~833 sites** (1 auditoria/dia por site)
- Cada auditoria demora ~10-30 segundos

### Se precisar de mais:

- Quota adicional custa **$5 USD por 1,000 requisições**
- Para 100 sites rodando 1x/dia = apenas **0,5 requisições extras por dia** = GRATUITO

## Como funciona no SentinelWeb

1. **Agendamento**: Celery Beat executa `run_pagespeed_audit_all` às **3h da manhã** todos os dias
2. **Espaçamento**: Auditorias são espaçadas em **1 minuto cada** para não sobrecarregar
3. **Armazenamento**: Scores são salvos na tabela `sites` do banco
4. **Visualização**: Acesse `/sites/{id}/details` para ver o card de Performance

## Testar a API Key

Teste se a chave está funcionando:

```bash
curl "https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=https://google.com&key=SUA_CHAVE_AQUI"
```

Se funcionar, você verá um JSON grande com os resultados.

## Troubleshooting

### Erro: "API key not valid"

- Verifique se copiou a chave completa (sem espaços no início/fim)
- Certifique-se de que a API PageSpeed Insights está ativada no projeto
- Aguarde 1-2 minutos após criar a chave (pode demorar para propagar)

### Erro: "The caller does not have permission"

- Ative a API PageSpeed Insights no Console
- Verifique se o projeto correto está selecionado

### Erro: "Quota exceeded"

- Você estourou o limite de 25k/dia
- Aguarde até meia-noite (horário do Pacífico) para resetar
- Ou adicione um método de pagamento para quota adicional

### Performance Score sempre baixo?

Algumas dicas para melhorar:

1. **Imagens**: Comprima e use formatos modernos (WebP)
2. **Cache**: Configure cache de navegador
3. **CDN**: Use Cloudflare ou similar
4. **Minificação**: Minifique CSS e JS
5. **Font Display**: Use `font-display: swap`

## Links Úteis

- 📖 Documentação oficial: https://developers.google.com/speed/docs/insights/v5/get-started
- 🎯 Web.dev (guias de otimização): https://web.dev/
- 📊 Core Web Vitals: https://web.dev/vitals/
- 💰 Pricing Calculator: https://cloud.google.com/products/calculator

## Suporte

Dúvidas sobre a configuração? Abra uma issue no GitHub ou entre em contato.

---

**Última atualização:** Janeiro 2026
