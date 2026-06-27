# Manual Técnico de Sensores - Turbina Industrial KY-9000

## Visão Geral

A turbina KY-9000 é monitorada por 21 sensores distribuídos ao longo do ciclo termodinâmico do motor. Os sensores capturam temperatura, pressão, velocidade de rotação e eficiência aerodinâmica em tempo real. O sistema de monitoramento registra uma leitura por ciclo de operação.

## Grupos de Sensores

### Grupo 1 - Sensores de Temperatura

**temp_entrada_fan (S1) - Temperatura Total na Entrada do Fan**
- Unidade: Kelvin (K)
- Faixa normal: 515 a 522 K
- Faixa de alerta: 522 a 530 K
- Faixa crítica: acima de 530 K
- Descrição: mede a temperatura do ar antes de entrar no fan. Valores elevados indicam problemas no sistema de admissão ou condições ambientais adversas.

**temp_saida_lpc (S2) - Temperatura Total na Saída do LPC**
- Unidade: Kelvin (K)
- Faixa normal: 638 a 648 K
- Faixa de alerta: 648 a 660 K
- Faixa crítica: acima de 660 K
- Descrição: temperatura após o compressor de baixa pressão. Elevação progressiva indica desgaste das palhetas do LPC.

**temp_saida_hpc (S3) - Temperatura Total na Saída do HPC**
- Unidade: Kelvin (K)
- Faixa normal: 1570 a 1620 K
- Faixa de alerta: 1620 a 1660 K
- Faixa crítica: acima de 1660 K
- Descrição: sensor crítico de degradação. Temperatura sobe progressivamente conforme o HPC perde eficiência. É o indicador mais confiável de degradação geral do motor.

**temp_saida_lpt (S4) - Temperatura Total na Saída do LPT**
- Unidade: Kelvin (K)
- Faixa normal: 1380 a 1440 K
- Faixa de alerta: 1440 a 1480 K
- Faixa crítica: acima de 1480 K
- Descrição: temperatura na saída da turbina de baixa pressão. Valores altos indicam combustão incompleta ou desgaste das palhetas da turbina.

---

### Grupo 2 - Sensores de Pressão

**pressao_entrada_fan (S5) - Pressão Total na Entrada do Fan**
- Unidade: psia
- Faixa normal: 14.4 a 14.9 psia
- Faixa de alerta: abaixo de 14.2 ou acima de 15.1 psia
- Descrição: pressão atmosférica corrigida na entrada. Variações bruscas indicam obstrução no duto de admissão.

**pressao_saida_lpc (S6) - Pressão Total na Saída do LPC**
- Unidade: psia
- Faixa normal: 21.3 a 22.0 psia
- Faixa crítica: abaixo de 20.5 psia
- Descrição: queda progressiva indica vazamento ou desgaste nas palhetas do compressor de baixa pressão.

**pressao_saida_hpc (S7) - Pressão Total na Saída do HPC**
- Unidade: psia
- Faixa normal: 548 a 562 psia
- Faixa de alerta: abaixo de 540 psia
- Faixa crítica: abaixo de 525 psia
- Descrição: pressão mais importante do sistema. Queda indica perda de compressão - componente mais custoso de reparar. Monitorar em conjunto com temp_saida_hpc.

**pressao_saida_hpt (S8) - Pressão Total na Saída do HPT**
- Unidade: psia
- Faixa normal: 2370 a 2410 psia
- Faixa crítica: abaixo de 2340 psia
- Descrição: queda de pressão na saída da turbina de alta pressão indica desgaste severo das palhetas ou vazamento de gás quente.

**pressao_saida_lpt (S9) - Pressão Total na Saída do LPT**
- Unidade: rpm (corrigido)
- Faixa normal: 9020 a 9120
- Faixa de alerta: abaixo de 8950
- Faixa crítica: abaixo de 8880
- Descrição: queda progressiva é indicador precoce de falha na turbina de baixa pressão. Deve ser monitorado em conjunto com velocidade_core.

---

### Grupo 3 - Sensores de Velocidade

**velocidade_fan (S10) - Velocidade de Rotação do Fan**
- Unidade: rpm normalizado
- Faixa normal: 1.28 a 1.33
- Faixa de alerta: abaixo de 1.26
- Descrição: velocidade do fan em relação ao ponto de projeto. Queda indica perda de eficiência aerodinâmica ou desbalanceamento.

**velocidade_core (S11) - Velocidade de Rotação do Núcleo**
- Unidade: rpm normalizado
- Faixa normal: 47.2 a 47.8
- Faixa de alerta: abaixo de 47.0
- Faixa crítica: abaixo de 46.5
- Descrição: velocidade do eixo de alta pressão. Queda progressiva é um dos melhores indicadores de degradação geral. Correlaciona diretamente com o RUL do motor.

---

### Grupo 4 - Sensores de Eficiência

**eficiencia_fan (S15) - Eficiência Aerodinâmica Corrigida do Fan**
- Unidade: adimensional
- Faixa normal: 8.40 a 8.45
- Faixa de alerta: abaixo de 8.37
- Faixa crítica: abaixo de 8.33
- Descrição: eficiência isentrópica do fan. Queda indica erosão ou dano nas palhetas. Queda de 1% na eficiência corresponde a aumento de consumo de combustível de aproximadamente 0.7%.

**eficiencia_hpc (S16) - Eficiência Aerodinâmica Corrigida do HPC**
- Unidade: adimensional
- Faixa normal: 0.0290 a 0.0315
- Faixa de alerta: abaixo de 0.0280
- Faixa crítica: abaixo de 0.0265
- Descrição: eficiência do compressor de alta pressão. É o sensor de degradação mais sensível. Queda contínua é o sinal mais confiável de que a manutenção preventiva deve ser agendada.

**eficiencia_lpt (S17) - Eficiência Aerodinâmica Corrigida do LPT**
- Unidade: rpm normalizado
- Faixa normal: 391 a 394
- Faixa de alerta: abaixo de 389
- Faixa crítica: abaixo de 386
- Descrição: eficiência da turbina de baixa pressão. Queda progressiva indica erosão nas palhetas por partículas ou desgaste térmico.

---

## Correlações Críticas entre Sensores

As seguintes combinações de leituras indicam situações de risco elevado:

1. **temp_saida_hpc subindo + eficiencia_hpc caindo**: degradação do HPC em andamento. Agendar inspeção em até 30 ciclos.

2. **velocidade_core caindo + pressao_saida_lpt caindo**: desgaste simultâneo de LPT e núcleo. Risco de falha em cascata. Manutenção urgente.

3. **eficiencia_fan caindo + velocidade_fan caindo**: erosão do fan. Inspeção visual imediata recomendada.

4. **temp_saida_hpc acima de 1640 K por 5 ciclos consecutivos**: risco de dano permanente às palhetas do HPC. Parada imediata recomendada.
