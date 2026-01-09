# 📊 Testando os Gráficos de Performance

## ✅ Mudanças Aplicadas

1. **API Endpoint criada**: `/api/sites/{site_id}/history`
   - Retorna dados agregados em intervalos de 30 minutos
   - Calcula latência média e uptime por hora
   - Últimas 24 horas de histórico

2. **Frontend atualizado**:
   - Requisição com `credentials: 'same-origin'` para incluir cookies
   - Mensagem de erro mais detalhada mostrando o erro exato
   - Botão "Tentar novamente" no card de erro

## 🧪 Como Testar

### Passo 1: Acessar a Página de Detalhes do Site

1. Abra o navegador: **http://localhost:8000**
2. Faça login com suas credenciais
3. No dashboard, clique em qualquer site (ex: Site ID 3)
4. Você verá a página de detalhes com o card do gráfico

### Passo 2: Verificar o Gráfico

**Cenário A: Gráfico carrega com sucesso ✅**
- Você verá um gráfico de área com a curva de latência
- Estatísticas no topo: latência média, total de checks, uptime %
- Barras de uptime por hora abaixo do gráfico

**Cenário B: Erro aparece ❌**
- Mensagem de erro será exibida
- O erro detalhado aparecerá em texto vermelho
- Botão "Tentar novamente" disponível

### Passo 3: Verificar Console do Navegador

Abra o Console (F12 → Console):

**Se houver erro:**
```
Erro da API: 404 {"detail":"Not Found"}
```

**Se funcionar:**
```
(sem erros, gráfico renderizado)
```

## 🔍 Diagnóstico de Problemas

### Erro: "Não autenticado"

**Causa**: Cookie de sessão expirou

**Solução**:
1. Faça logout
2. Faça login novamente
3. Acesse a página do site

### Erro: "404 Not Found"

**Causa**: API endpoint não está registrada

**Diagnóstico**:
```bash
# Verificar se a função está no container
docker-compose exec web grep -c "get_site_history" main.py

# Deve retornar: 1 (se encontrou a função)

# Verificar logs do container
docker-compose logs web --tail 50 | grep -i error
```

**Solução**:
```bash
# Reiniciar o container
docker-compose restart web

# Aguardar 5 segundos e testar novamente
```

### Erro: "Site não encontrado"

**Causa**: O site não pertence ao usuário logado

**Solução**: Certifique-se de acessar um site que você criou

## 📝 Teste Manual da API

Se quiser testar a API diretamente:

```bash
# 1. Fazer login e obter o cookie
curl -c cookies.txt -X POST http://localhost:8000/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=admin@sentinelweb.com&password=admin123"

# 2. Testar a API usando o cookie
curl -b cookies.txt http://localhost:8000/api/sites/3/history | python3 -m json.tool

# Resposta esperada:
# {
#   "categories": ["10:00", "10:30", "11:00", ...],
#   "latency": [308.53, 360.6, 402.3, ...],
#   "status": [1, 1, 0.95, ...],
#   "uptime_hours": [
#     {"hour": "08/01 10:00", "uptime": 100, "checks": 12},
#     ...
#   ],
#   "total_checks": 69,
#   "avg_latency": 402.97,
#   "uptime_percent": 100
# }
```

## 🎯 Resultado Esperado

### Estrutura da Página

```
┌─────────────────────────────────────────┐
│  ← Voltar    Site Name        [Editar]  │
├─────────────────────────────────────────┤
│                                         │
│  📊 Latência - Últimas 24 Horas         │
│  ┌───────────────────────────────────┐  │
│  │   [Gráfico de área verde]        │  │
│  │    /\  /\                         │  │
│  │   /  \/  \__                      │  │
│  └───────────────────────────────────┘  │
│                                         │
│  📊 Uptime por Hora                     │
│  ┌─┬─┬─┬─┬─┬─┬─┬─┐ (barras verdes)     │
│  └─┴─┴─┴─┴─┴─┴─┴─┘                     │
│                                         │
│  📈 Status Atual                        │
│  ✅ Online (200) | 145ms                │
│                                         │
│  📋 Histórico de Monitoramento          │
│  (tabela com últimos 50 checks)         │
└─────────────────────────────────────────┘
```

## ✅ Checklist Final

Antes de considerar concluído, verifique:

- [ ] API endpoint `/api/sites/{site_id}/history` responde corretamente
- [ ] Função `get_site_history` existe em `main.py`
- [ ] Container web foi reiniciado após mudanças
- [ ] Template `site_details.html` foi atualizado
- [ ] Navegador carrega a página sem erros 404
- [ ] Console do navegador não mostra erros de autenticação
- [ ] Gráfico é renderizado com dados reais
- [ ] Estatísticas (latência média, checks, uptime) aparecem
- [ ] Barras de uptime por hora são exibidas

## 🚀 Próximos Passos (Opcional)

Se os gráficos estiverem funcionando, você pode:

1. **Adicionar mais períodos**:
   - Botões para 6h, 12h, 24h, 7 dias
   - Dropdown com seleção de período customizado

2. **Exportar dados**:
   - Botão para baixar dados em CSV
   - Botão para salvar gráfico como PNG

3. **Comparação de sites**:
   - Sobrepor gráficos de múltiplos sites
   - Tabela comparativa de métricas

4. **Alertas visuais**:
   - Marcar no gráfico quando houve queda
   - Anotações com eventos importantes

---

**Status**: ✅ API implementada | ✅ Frontend atualizado | 🧪 Pronto para testes
