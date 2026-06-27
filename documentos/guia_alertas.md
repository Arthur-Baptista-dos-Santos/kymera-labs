# Guia de Interpretação de Alertas - Kymera Labs

## O que é RUL?

RUL significa Remaining Useful Life, ou Vida Útil Restante em português. Representa o número de ciclos operacionais que o motor pode completar antes de atingir o ponto de falha. Um ciclo equivale a um ciclo completo de operação da turbina: partida, operação em carga, desligamento.

O modelo de predição aprende o padrão de degradação de cada sensor ao longo do tempo e estima quantos ciclos restam com base na tendência atual.

## Diferença entre Anomalia e RUL Baixo

**Anomalia de sensor**: uma leitura pontual fora do padrão normal. Pode ser causada por ruído elétrico, sujeira no sensor, evento transitório ou início de degradação. Não significa necessariamente que o motor vai falhar em breve.

**RUL baixo**: o modelo identificou uma tendência de degradação acumulada ao longo de múltiplos ciclos que indica proximidade da falha. É mais confiável que uma anomalia isolada e exige ação imediata.

A situação mais crítica é a combinação de anomalia detectada + RUL baixo. Isso indica degradação confirmada e em fase avançada.

## Perguntas Frequentes

**O que fazer quando o RUL cai abruptamente em 1 ou 2 ciclos?**
Verificar se houve evento anômalo na operação (sobrecarga, variação brusca de temperatura ambiente). Re-avaliar no ciclo seguinte. Se persistir, acionar protocolo de alerta.

**Qual sensor monitorar primeiro quando há múltiplas anomalias?**
Prioridade: eficiencia_hpc > temp_saida_hpc > velocidade_core > pressao_saida_hpc. Anomalias nessa ordem têm maior correlação com falha iminente.

**É possível o RUL aumentar entre ciclos?**
Sim. O modelo usa médias móveis e pode ajustar a previsão conforme novas leituras chegam. Um motor operado em condições mais leves pode ter RUL aumentado temporariamente. Isso é comportamento esperado.

**Qual a precisão do modelo de predição?**
O modelo XGBoost treinado com dados históricos atinge MAE (Erro Médio Absoluto) de aproximadamente 15 ciclos. Isso significa que a previsão pode errar em até 15 ciclos para mais ou para menos. Para o status CRÍTICO (RUL menor ou igual a 10), considerar margem de segurança de 15 ciclos adicionais.

**Como interpretar o score de anomalia?**
O score varia de aproximadamente -0.5 (muito anômalo) a 0.0 (normal). Valores abaixo de -0.15 indicam anomalia de severidade alta. Entre -0.15 e 0.0 com predição positiva indicam anomalia de severidade média.

## Glossário Técnico

- **Fan**: componente frontal da turbina responsável por comprimir o ar de admissão
- **LPC**: Low Pressure Compressor - compressor de baixa pressão
- **HPC**: High Pressure Compressor - compressor de alta pressão, componente mais crítico
- **HPT**: High Pressure Turbine - turbina de alta pressão
- **LPT**: Low Pressure Turbine - turbina de baixa pressão
- **FADEC**: Full Authority Digital Engine Control - sistema eletrônico de controle do motor
- **Ciclo**: uma operação completa da turbina do acionamento ao desligamento
- **Palheta**: lâmina aerodinâmica rotatória nos compressores e turbinas
- **Sangria (bleed)**: extração controlada de ar comprimido para sistemas auxiliares
- **Endoscopia**: inspeção interna do motor com câmera flexível sem desmontagem
