# Procedimentos de Manutenção - Turbina KY-9000

## Classificação de Manutenção

### Manutenção Preventiva Programada (MPP)
Realizada com base no número de ciclos operados, independente do estado dos sensores.

- **MPP-100**: inspeção visual a cada 100 ciclos. Verificar integridade externa, vazamentos, vibração.
- **MPP-200**: inspeção interna a cada 200 ciclos. Endoscopia do fan, LPC e câmara de combustão.
- **MPP-500**: revisão geral a cada 500 ciclos. Substituição de palhetas de alto desgaste, recalibração de sensores.

### Manutenção Preditiva (MP)
Acionada pelos alertas do sistema de monitoramento, com base nas predições de RUL e leituras dos sensores.

---

## Protocolos por Status de RUL

### Status: NORMAL (RUL > 60 ciclos)
- Operação normal autorizada
- Registrar leituras no diário de bordo
- Verificar tendências a cada 10 ciclos

### Status: ATENÇÃO (RUL entre 31 e 60 ciclos)
- Operação permitida com monitoramento intensificado
- Notificar equipe de manutenção
- Agendar janela de manutenção preventiva
- Aumentar frequência de leitura para a cada 5 ciclos
- Verificar histórico dos sensores eficiencia_hpc, temp_saida_hpc e velocidade_core

### Status: ALERTA (RUL entre 11 e 30 ciclos)
- Operação permitida somente em missões essenciais
- Acionar engenheiro de manutenção imediatamente
- Preparar peças de reposição: palhetas HPC, rolamentos, vedações
- Planejar parada para manutenção na próxima janela disponível
- Monitoramento contínuo ciclo a ciclo obrigatório

### Status: CRÍTICO (RUL igual ou inferior a 10 ciclos)
- PARADA IMEDIATA recomendada
- Acionar protocolo de emergência
- Isolar o motor do sistema de operação
- Iniciar inspeção completa antes de qualquer novo acionamento
- Registrar ocorrência no sistema de gestão de manutenção

---

## Procedimentos por Anomalia de Sensor

### Anomalia em temp_saida_hpc ou temp_saida_lpt
1. Verificar sistema de refrigeração do HPC
2. Inspecionar vedações da câmara de combustão
3. Avaliar estado das palhetas de turbina com endoscópio
4. Se temperatura acima do nível crítico por mais de 3 ciclos: parada obrigatória

### Anomalia em eficiencia_hpc ou eficiencia_fan
1. Verificar presença de corpos estranhos no duto de admissão
2. Inspeção visual das palhetas de fan e compressor
3. Verificar calibração dos sensores de pressão associados
4. Lavar motor com água destilada se contaminação confirmada

### Anomalia em velocidade_core ou velocidade_fan
1. Verificar sistema de controle de velocidade (FADEC)
2. Inspecionar rolamentos do eixo principal
3. Verificar balanceamento dinâmico do rotor
4. Medir vibração com acelerômetro externo

### Anomalia em pressao_saida_hpc
1. Verificar válvulas de sangria (bleed valves)
2. Inspecionar selagens labirin do HPC
3. Verificar geometria variável das palhetas guia (VSV)
4. Comparar com leituras históricas dos últimos 20 ciclos

---

## Peças de Reposição Críticas

| Componente | Vida útil típica (ciclos) | Lead time de fornecimento |
|---|---|---|
| Palhetas fan (conjunto) | 800-1200 | 15 dias |
| Palhetas HPC (estágio 1-5) | 600-900 | 21 dias |
| Palhetas HPT (estágio 1) | 400-700 | 30 dias |
| Palhetas LPT (conjunto) | 700-1000 | 18 dias |
| Rolamentos eixo principal | 1000-1500 | 7 dias |
| Vedações câmara combustão | 300-500 | 5 dias |
| Sensores de temperatura | 500-800 | 3 dias |

---

## Registro de Manutenção

Toda intervenção deve ser registrada com:
- Data e ciclo de operação no momento da manutenção
- Código do técnico responsável
- Componentes inspecionados e substituídos
- Leituras dos sensores antes e após a manutenção
- RUL previsto pelo sistema antes da intervenção
- Observações sobre o estado físico dos componentes
