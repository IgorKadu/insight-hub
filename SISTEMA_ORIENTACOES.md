# Guia de Orientação - Insight Hub Fleet Monitor

## Visão Geral
O Insight Hub é um sistema completo de monitoramento de frota que integra análise preditiva, insights automáticos e geração de relatórios robustos. Este documento serve como guia técnico para deploy, configuração e resolução de problemas.

## Requisitos do Sistema

### Dependências Principais
```
streamlit>=1.49.1          # Interface web principal
pandas>=2.3.2              # Manipulação de dados
plotly>=6.3.0              # Visualizações interativas
numpy>=2.3.3               # Computação numérica
psycopg2-binary>=2.9.10    # Conexão PostgreSQL
sqlalchemy>=2.0.43         # ORM de banco de dados
streamlit-folium>=0.25.1   # Mapas interativos
folium>=0.20.0             # Biblioteca de mapas
scikit-learn>=1.7.2        # Machine Learning (opcional)
fpdf2>=2.8.4               # Geração de PDF
reportlab>=4.4.3           # Relatórios avançados
```

### Dependências Opcionais (Para funcionalidades avançadas)
```
kaleido                    # Exportação de gráficos para PDF
DejaVuSans.ttf            # Fonte Unicode para PDFs (assets/fonts/)
```

## Configuração do Ambiente

### Variáveis de Ambiente Essenciais
```bash
# Database (Configuradas automaticamente pelo Replit)
DATABASE_URL=postgresql://user:pass@host:port/db
PGHOST=host
PGPORT=5432
PGUSER=user
PGPASSWORD=password
PGDATABASE=database

# Configurações da aplicação
STREAMLIT_SERVER_PORT=5000
STREAMLIT_SERVER_ADDRESS=0.0.0.0
```

### Estrutura de Diretórios
```
projeto/
├── app.py                 # Aplicação principal
├── pages/                 # Páginas do Streamlit
│   ├── 1_📊_Dashboard.py
│   ├── 2_📁_Upload_CSV.py
│   ├── 3_🔍_Análise_Detalhada.py
│   ├── 4_🔮_Manutenção_Preditiva.py
│   ├── 5_🗺️_Mapa_de_Rotas.py
│   ├── 5_🧠_Insights_Automáticos.py
│   ├── 6_📄_Relatórios.py
│   └── 8_🚨_Controle_Operacional.py
├── database/              # Camada de dados
│   ├── connection.py      # Conexões de banco
│   ├── db_manager.py      # Gerenciador principal
│   ├── models.py          # Modelos de dados
│   └── services.py        # Serviços de banco
├── utils/                 # Utilitários
│   ├── data_analyzer.py   # Análise de dados
│   ├── insights_generator.py # IA para insights
│   ├── ml_predictive.py   # Manutenção preditiva
│   ├── pdf_reports.py     # Geração de PDF robusta
│   ├── report_aggregator.py # Agregação de relatórios
│   └── visualizations.py # Visualizações
└── data/                  # Dados temporários
```

## Funcionalidades Principais

### 1. Upload e Processamento de CSV
- Suporte a múltiplos encodings (UTF-8, Latin-1, Windows-1252)
- Detecção automática de separadores (, e ;)
- Validação de 25 campos obrigatórios
- Processamento em lote com progresso em tempo real
- Limite: 200MB total, 50MB por arquivo

### 2. Banco de Dados PostgreSQL
- Conexão robusta com retry automático
- Pool de conexões configurado
- SSL obrigatório para segurança
- Tabelas: telematics_data, vehicles, clients, processing_history

### 3. Geração de PDF Robusta
- Tratamento de emojis e caracteres Unicode
- Fonte DejaVu Sans para suporte Unicode (opcional)
- Fallback seguro para fonte Arial
- Output em BytesIO para integração Streamlit
- Contextos pré-processados de 5 painéis

### 4. Machine Learning (Opcional)
- Análise preditiva de manutenção
- Health scores por sistema
- Detecção de anomalias
- Recomendações automáticas

## Resolução de Problemas

### Erro de Conexão com Banco de Dados
```bash
# Verificar variáveis de ambiente
echo $DATABASE_URL

# Testar conexão
python -c "from database.connection import test_connection; print('OK' if test_connection() else 'FAIL')"
```

**Solução:** Verificar se o PostgreSQL está provisionado e as variáveis estão corretas.

### Erro na Geração de PDF
**Sintomas:**
- "UnicodeEncodeError" 
- "Font not found"
- Caracteres especiais não aparecem

**Soluções:**
1. O sistema agora remove emojis automaticamente
2. Usa fonte DejaVu Sans se disponível, senão fallback para Arial
3. Converte todos os textos para formato seguro

### Erro de Importação ML
**Sintoma:** "ModuleNotFoundError: scikit-learn"

**Solução:** 
- Funcionalidade preditiva é opcional
- Sistema continua funcionando sem ML
- Para ativar: instalar scikit-learn>=1.7.2

### Performance Lenta
**Otimizações:**
- Cache de dados com TTL de 5 minutos
- Limite de registros em tabelas (15 veículos max)
- Paginação automática em listas grandes
- Processamento por lotes

## Deploy em Produção

### Checklist de Deploy
- [ ] Banco PostgreSQL configurado e acessível
- [ ] Variáveis de ambiente definidas
- [ ] Dependências instaladas (requirements.txt)
- [ ] Porta 5000 aberta e disponível
- [ ] SSL/TLS configurado para banco
- [ ] Backup automático do banco configurado

### Comandos de Deploy
```bash
# Instalar dependências
pip install -r requirements.txt

# Ou usar uv (recomendado)
uv add streamlit pandas plotly numpy psycopg2-binary sqlalchemy

# Iniciar aplicação
streamlit run app.py --server.port=5000 --server.address=0.0.0.0
```

### Monitoramento
- Logs do Streamlit: verificar erro de módulos
- Logs do PostgreSQL: verificar conexões
- Métricas de performance: tempo de upload, geração PDF
- Uso de memória: especialmente em uploads grandes

## Manutenção

### Limpeza Regular
```python
# Limpar dados antigos (se necessário)
from database.db_manager import DatabaseManager
result = DatabaseManager.clear_all_data()
print(f"Removidos: {result}")
```

### Backup de Dados
```bash
# Backup PostgreSQL
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restaurar
psql $DATABASE_URL < backup_20240914.sql
```

### Updates de Segurança
- Manter bibliotecas atualizadas
- Revisar logs de segurança
- Validar entradas de usuário
- Não expor credenciais nos logs

## Notas de Versão

### Versão Atual (Robusta)
- ✅ Corrigido: Erros Unicode/emoji em PDFs
- ✅ Corrigido: Problemas de conexão com banco
- ✅ Melhorado: Sistema de agregação de relatórios
- ✅ Melhorado: Tratamento de erros robusto
- ✅ Adicionado: Suporte a dependências opcionais
- ✅ Adicionado: Validação de dados aprimorada

### Compatibilidade
- Replit: Totalmente compatível
- Docker: Compatível (usar imagem Python 3.11+)
- Cloud: AWS, GCP, Azure (requer PostgreSQL)
- Local: Windows, Linux, macOS

## Suporte Técnico

### Logs Importantes
```bash
# Workflow logs
tail -f /tmp/logs/Streamlit_Fleet_Monitor_*.log

# Aplicação
streamlit run app.py --logger.level=debug

# Banco de dados
export SQLALCHEMY_LOG_LEVEL=INFO
```

### Contatos de Emergência
- Sistema: Verificar logs em tempo real
- Banco: Usar ferramentas de admin PostgreSQL
- Performance: Monitorar métricas via dashboard

---

**Criado:** 14/09/2025  
**Versão:** 2.0 (Robusta)  
**Compatibilidade:** Replit, Cloud, Local  
**Dependências:** Python 3.11+, PostgreSQL 12+