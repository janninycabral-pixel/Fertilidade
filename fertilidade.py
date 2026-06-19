# app.py
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime
import requests
import io
import random
import math

# ===================== CONFIGURAÇÃO DA PÁGINA =====================
st.set_page_config(
    page_title="Sistema de Apoio à Decisão - Manejo de Nitrogênio",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===================== CSS PERSONALIZADO =====================
st.markdown("""
<style>
    .main {
        background-color: #f5f9f5;
    }
    .stApp {
        background-color: #f5f9f5;
    }
    .css-1d391kg {
        background-color: #f5f9f5;
    }
    .stButton > button {
        background-color: #2e7d32;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: #1b5e20;
        color: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .stButton > button:focus {
        box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.3);
    }
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        border-left: 4px solid #2e7d32;
        margin-bottom: 20px;
    }
    .card-azul {
        border-left-color: #1976d2;
    }
    .card-info {
        background-color: #e3f2fd;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #1976d2;
        margin: 10px 0;
    }
    .card-success {
        background-color: #e8f5e9;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #2e7d32;
        margin: 10px 0;
    }
    .card-warning {
        background-color: #fff3e0;
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #f57c00;
        margin: 10px 0;
    }
    .divider {
        border-top: 2px solid #e0e0e0;
        margin: 25px 0;
    }
    .title-main {
        color: #1b5e20;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        color: #4a4a4a;
        font-size: 1.1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        text-align: center;
    }
    .stSelectbox label, .stTextInput label, .stNumberInput label, .stRadio label {
        font-weight: 500;
        color: #333;
    }
    .highlight-box {
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
        padding: 20px;
        border-radius: 12px;
        border: 2px solid #2e7d32;
        margin: 15px 0;
    }
    .info-badge {
        background-color: #1976d2;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        display: inline-block;
        margin: 5px 0;
    }
    .stMetric {
        background-color: white;
        padding: 10px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    [data-testid="stMetric"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }
</style>
""", unsafe_allow_html=True)

# ===================== CHAVE API (FUTURA) =====================
GOOGLE_MAPS_API_KEY = "INSERIR_CHAVE_API_AQUI"
OPENWEATHER_API_KEY = "INSERIR_CHAVE_API_AQUI"

# ===================== FUNÇÕES DE APOIO =====================
def init_session_state():
    """Inicializa as variáveis de sessão."""
    if 'propriedade' not in st.session_state:
        st.session_state.propriedade = {}
    if 'analise_solo' not in st.session_state:
        st.session_state.analise_solo = {}
    if 'plantio' not in st.session_state:
        st.session_state.plantio = {}
    if 'recomendacao' not in st.session_state:
        st.session_state.recomendacao = {}
    if 'tem_analise' not in st.session_state:
        st.session_state.tem_analise = None
    if 'usa_bioinsumos' not in st.session_state:
        st.session_state.usa_bioinsumos = None
    if 'dados_salvos' not in st.session_state:
        st.session_state.dados_salvos = False

def get_valores_padrao():
    """Retorna valores médios de fertilidade para fins educativos."""
    return {
        'ph': 5.8,
        'materia_organica': 2.5,
        'fosforo': 15,
        'potassio': 120,
        'calcio': 4.0,
        'magnesio': 1.5,
        'aluminio': 0.3,
        'h_al': 4.5,
        'ctc': 8.5,
        'sb': 65,
        'enxofre': 10,
        'boro': 0.5,
        'zinco': 1.5,
        'textura': 'Média'
    }

def calcular_dose_nitrogenio(cultura, produtividade, ambiente, cultura_anterior, leguminosa, textura, materia_organica, manejo_solo, usa_bioinsumos):
    """
    Calcula a dose recomendada de nitrogênio (kg/ha) com base em regras agronômicas simplificadas.
    Agora com variação real baseada nos parâmetros informados.
    """
    # Converter produtividade para toneladas por hectare
    if produtividade > 0:
        produtividade_t_ha = produtividade / 1000
    else:
        produtividade_t_ha = 3.0  # valor padrão
    
    # Fatores base por cultura (kg N por tonelada de produto)
    fatores_base = {
        'Milho': 22,
        'Trigo': 25,
        'Soja': 5,    # Soja fixa N, precisa de pouco N mineral
        'Feijão': 35,
        'Sorgo': 20,
        'Algodão': 30
    }
    
    # Calcular dose base
    if cultura in fatores_base:
        dose_base = fatores_base[cultura] * produtividade_t_ha
    else:
        dose_base = 80  # valor padrão
    
    # Ajuste por cultura (específico)
    if cultura == 'Soja':
        # Soja precisa de pouco N mineral devido à fixação
        dose_base = max(dose_base, 10)  # mínimo 10 kg/ha
        dose_base = min(dose_base, 40)  # máximo 40 kg/ha
    
    # Ajuste por ambiente
    fator_ambiente = 1.0
    if ambiente == 'Irrigado':
        if produtividade_t_ha > 5.0:
            fator_ambiente = 1.20  # alta produtividade em irrigado
        else:
            fator_ambiente = 1.10
    else:  # Sequeiro
        if produtividade_t_ha > 3.0:
            fator_ambiente = 0.95
        else:
            fator_ambiente = 0.85
    
    dose_ambiente = dose_base * fator_ambiente
    
    # Ajuste por cultura anterior e leguminosa
    fator_cultura_anterior = 1.0
    if cultura_anterior in ['Soja', 'Feijão']:
        fator_cultura_anterior = 0.70
    elif cultura_anterior in ['Braquiária', 'Milheto']:
        fator_cultura_anterior = 0.85
    elif cultura_anterior in ['Milho', 'Sorgo', 'Trigo']:
        fator_cultura_anterior = 1.0
    
    if leguminosa == 'Sim':
        fator_cultura_anterior *= 0.80
    
    dose_anterior = dose_ambiente * fator_cultura_anterior
    
    # Ajuste por textura
    fator_textura = {'Arenosa': 1.15, 'Média': 1.0, 'Argilosa': 0.90, 'Muito argilosa': 0.85}
    fator_text = fator_textura.get(textura, 1.0)
    dose_textura = dose_anterior * fator_text
    
    # Ajuste por matéria orgânica
    fator_mo = 1.0
    if materia_organica:
        if materia_organica > 3.0:
            fator_mo = 0.80
        elif materia_organica > 2.0:
            fator_mo = 0.90
        elif materia_organica > 1.0:
            fator_mo = 1.10
        else:
            fator_mo = 1.20
    
    dose_mo = dose_textura * fator_mo
    
    # Ajuste por manejo do solo
    fator_manejo = 1.0
    if manejo_solo == 'Plantio direto':
        fator_manejo = 0.90
    elif manejo_solo == 'Plantio convencional':
        fator_manejo = 1.15
    elif manejo_solo == 'Sistema mínimo':
        fator_manejo = 1.0
    
    dose_manejo = dose_mo * fator_manejo
    
    # Ajuste por bioinsumos (pequeno ajuste, mantém a recomendação)
    if usa_bioinsumos == 'Sim':
        dose_manejo *= 0.95  # redução pequena devido à eficiência
        observacao_bio = "Bioinsumos podem aumentar a eficiência do N em até 15%"
    else:
        observacao_bio = "Considere uso de bioinsumos para melhor eficiência"
    
    # Arredondar para múltiplo de 5
    dose_final = round(dose_manejo / 5) * 5
    
    # Limites mínimos e máximos educativos
    if cultura == 'Soja':
        dose_final = min(max(dose_final, 10), 50)
    else:
        dose_final = min(max(dose_final, 30), 250)
    
    # Gerar explicação do cálculo
    explicacao = f"""
    Cálculo da dose de N:
    - Produtividade: {produtividade} kg/ha ({produtividade_t_ha:.1f} t/ha)
    - Fator base para {cultura}: {fatores_base.get(cultura, 80)} kg N/t
    - Dose base: {dose_base:.0f} kg N/ha
    - Ajuste ambiente ({ambiente}): {fator_ambiente:.2f} → {dose_ambiente:.0f}
    - Ajuste cultura anterior ({cultura_anterior}): {fator_cultura_anterior:.2f} → {dose_anterior:.0f}
    - Ajuste textura ({textura}): {fator_text:.2f} → {dose_textura:.0f}
    - Ajuste MO ({materia_organica:.1f}%): {fator_mo:.2f} → {dose_mo:.0f}
    - Ajuste manejo ({manejo_solo}): {fator_manejo:.2f} → {dose_manejo:.0f}
    - Dose final recomendada: {dose_final} kg N/ha
    """
    
    return int(dose_final), explicacao, observacao_bio

def escolher_fertilizante(dose_n, cultura, ambiente, ph):
    """
    Recomenda o fertilizante nitrogenado mais adequado.
    """
    # Dicionário com teores de N e características
    fertilizantes = {
        'Ureia': {'teor': 0.45, 'descricao': 'Alta concentração, recomendada para cobertura', 'ph_indicado': 'Todos'},
        'Sulfato de amônio': {'teor': 0.20, 'descricao': 'Fonte de N + S, acidificante', 'ph_indicado': '> 5.5'},
        'Nitrato de amônio': {'teor': 0.33, 'descricao': 'N de rápida disponibilidade', 'ph_indicado': 'Todos'},
    }
    
    # Seleção baseada na cultura e pH
    if cultura in ['Soja', 'Feijão']:
        # Para leguminosas, recomendação menor de N
        if dose_n < 30:
            return 'Ureia', fertilizantes['Ureia']['teor'], 'Aplicação em cobertura'
        else:
            return 'Sulfato de amônio', fertilizantes['Sulfato de amônio']['teor'], 'Aplicação em cobertura'
    elif ph and ph < 5.5:
        # Solos ácidos: preferir sulfato de amônio
        return 'Sulfato de amônio', fertilizantes['Sulfato de amônio']['teor'], 'Aplicação em cobertura'
    elif ambiente == 'Sequeiro':
        # Em sequeiro, preferir ureia
        return 'Ureia', fertilizantes['Ureia']['teor'], 'Aplicação em cobertura'
    else:
        return 'Ureia', fertilizantes['Ureia']['teor'], 'Aplicação em cobertura'

def calcular_quantidade_fertilizante(dose_n, teor_n):
    """
    Calcula a quantidade de fertilizante necessária (kg/ha).
    """
    if teor_n == 0:
        return 0
    return round(dose_n / teor_n, 1)

def recomendar_manejo_nitrogenio(cultura, dose_n, ambiente):
    """
    Recomenda estratégia de manejo para o nitrogênio.
    """
    if cultura == 'Soja':
        return {
            'estrategia': 'Aplicação única',
            'parcelamento': 'Plantio (ou sementes com inoculante)',
            'observacao': 'A soja depende da fixação biológica. Aplicar N apenas em casos de baixa nodulação.'
        }
    elif cultura == 'Milho' and ambiente == 'Irrigado':
        if dose_n > 120:
            return {
                'estrategia': 'Parcelamento em 3 vezes',
                'parcelamento': 'Plantio (30%) + V4 (40%) + V8/embonecamento (30%)',
                'observacao': 'Em irrigação, parcelar para maior eficiência e evitar perdas.'
            }
        else:
            return {
                'estrategia': 'Parcelamento em 2 vezes',
                'parcelamento': 'Plantio (50%) + Cobertura V4-V6 (50%)',
                'observacao': 'Dose moderada, parcelamento em duas etapas.'
            }
    elif cultura == 'Trigo':
        return {
            'estrategia': 'Parcelamento em 2 vezes',
            'parcelamento': 'Plantio (50%) + Perfilhamento (50%)',
            'observacao': 'O trigo responde bem ao parcelamento no perfilhamento.'
        }
    else:
        return {
            'estrategia': 'Aplicação única ou parcelada',
            'parcelamento': 'Plantio (100%) ou Plantio (50%) + Cobertura (50%)',
            'observacao': 'Avaliar condições de solo e clima.'
        }

def recomendar_bioinsumos(cultura, usa_bioinsumos, bioinsumos_selecionados):
    """
    Recomenda bioinsumos com base na cultura e uso atual.
    """
    recomendacoes = {
        'Milho': {
            'microrganismos': ['Azospirillum brasilense', 'Bacillus subtilis', 'Pseudomonas fluorescens'],
            'forma_uso': 'Tratamento de sementes ou aplicação no sulco de plantio',
            'cuidados': 'Evitar mistura com fungicidas. Proteger da luz solar direta.'
        },
        'Trigo': {
            'microrganismos': ['Azospirillum brasilense', 'Bacillus subtilis', 'Pseudomonas fluorescens'],
            'forma_uso': 'Tratamento de sementes ou aplicação foliar no perfilhamento',
            'cuidados': 'Aplicar em temperaturas amenas (manhã/tarde).'
        },
        'Soja': {
            'microrganismos': ['Bradyrhizobium japonicum', 'Azospirillum brasilense (coinoculação)'],
            'forma_uso': 'Tratamento de sementes',
            'cuidados': 'Não misturar com produtos fitossanitários no mesmo tanque.'
        },
        'Feijão': {
            'microrganismos': ['Rhizobium tropici', 'Azospirillum brasilense'],
            'forma_uso': 'Tratamento de sementes',
            'cuidados': 'Aplicar até 24h antes do plantio.'
        },
        'Sorgo': {
            'microrganismos': ['Azospirillum brasilense', 'Bacillus subtilis'],
            'forma_uso': 'Tratamento de sementes ou aplicação no sulco',
            'cuidados': 'Evitar dessecação do inoculante.'
        },
        'Algodão': {
            'microrganismos': ['Bacillus subtilis', 'Pseudomonas fluorescens', 'Trichoderma spp.'],
            'forma_uso': 'Aplicação no sulco ou via solo',
            'cuidados': 'Manter umidade do solo após aplicação.'
        }
    }
    
    if cultura in recomendacoes:
        rec = recomendacoes[cultura]
    else:
        rec = {
            'microrganismos': ['Azospirillum brasilense', 'Bacillus subtilis'],
            'forma_uso': 'Tratamento de sementes ou aplicação no solo',
            'cuidados': 'Seguir recomendações do fabricante.'
        }
    
    # Se o produtor já usa bioinsumos, complementar
    if usa_bioinsumos == 'Sim' and bioinsumos_selecionados:
        complemento = "\n\n**Bioinsumos atuais selecionados pelo produtor:**\n"
        for bio in bioinsumos_selecionados:
            complemento += f"- {bio}\n"
        rec['observacao'] = 'Recomendação complementar aos bioinsumos já utilizados.' + complemento
    else:
        rec['observacao'] = 'Recomendação inicial para a cultura.'
    
    return rec

def gerar_grafico_performance(dose_n, cultura, produtividade, ambiente, manejo_solo, usa_bioinsumos):
    """
    Gera gráfico educacional comparando cenários de manejo usando Plotly.
    Mais estável no Streamlit Cloud.
    """
    # Garantir que os valores são numéricos
    try:
        dose_n = float(dose_n) if dose_n is not None and dose_n != '' else 80
    except (ValueError, TypeError):
        dose_n = 80
    
    try:
        produtividade = float(produtividade) if produtividade is not None and produtividade != '' else 3000
    except (ValueError, TypeError):
        produtividade = 3000
    
    if produtividade <= 0:
        produtividade = 3000
    
    if dose_n <= 0:
        dose_n = 80
    
    # Estimativa de produtividade base (kg/ha)
    bases_produtividade = {
        'Milho': 6000,
        'Trigo': 3000,
        'Soja': 3000,
        'Feijão': 2000,
        'Sorgo': 4000,
        'Algodão': 3000
    }
    
    base = bases_produtividade.get(cultura, 3000)
    
    # Ajustar para a produtividade esperada do usuário
    if produtividade and produtividade > 0:
        base = produtividade
    
    # Ajuste por ambiente
    if ambiente == 'Irrigado':
        base *= 1.2
    
    # Cenários com incrementos percentuais educativos
    cenario_sem_manejo = base * 0.60
    
    # Com N recomendado (aumento baseado na dose)
    incremento_n = min(dose_n / 200, 0.40)  # máximo 40% de aumento
    cenario_adubacao = base * (0.75 + incremento_n * 0.5)
    
    # Com N + bioinsumos
    incremento_bio = 0.10 if usa_bioinsumos == 'Sim' else 0.05
    cenario_adubacao_bio = cenario_adubacao * (1 + incremento_bio)
    
    # Com manejo integrado (tudo otimizado)
    incremento_integrado = 0.15 + (0.05 if manejo_solo == 'Plantio direto' else 0)
    cenario_ideal = cenario_adubacao_bio * (1 + incremento_integrado)
    
    # Limitar valores para não ficarem abaixo do mínimo
    cenario_sem_manejo = max(cenario_sem_manejo, base * 0.50)
    cenario_adubacao = max(cenario_adubacao, base * 0.70)
    cenario_adubacao_bio = max(cenario_adubacao_bio, base * 0.80)
    cenario_ideal = max(cenario_ideal, base * 0.90)
    
    # Criar dados para o gráfico
    dados = {
        'Cenário': [
            'Sem manejo otimizado', 
            'Com adubação N', 
            'Com adubação + bioinsumos', 
            'Com manejo integrado'
        ],
        'Produtividade (kg/ha)': [
            cenario_sem_manejo, 
            cenario_adubacao, 
            cenario_adubacao_bio, 
            cenario_ideal
        ],
        'Cor': ['#d32f2f', '#ff9800', '#4caf50', '#2e7d32']
    }
    
    df_grafico = pd.DataFrame(dados)
    
    # Criar gráfico com Plotly
    fig = px.bar(
        df_grafico,
        x='Cenário',
        y='Produtividade (kg/ha)',
        text='Produtividade (kg/ha)',
        title=f'Estimativa educativa de produtividade - {cultura}',
        color='Cor',
        color_discrete_map='identity'
    )
    
    # Atualizar barras
    fig.update_traces(
        texttemplate='%{text:.0f}',
        textposition='outside',
        textfont=dict(size=11, color='black', weight='bold'),
        hovertemplate='<b>%{x}</b><br>Produtividade: %{text:.0f} kg/ha<extra></extra>'
    )
    
    # Atualizar layout
    fig.update_layout(
        height=450,
        xaxis_title='Cenário de manejo',
        yaxis_title='Produtividade estimada (kg/ha)',
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=80),
        plot_bgcolor='white',
        yaxis=dict(
            gridcolor='#e0e0e0',
            griddash='dash',
            title_font=dict(size=13, weight='bold'),
            tickfont=dict(size=11)
        ),
        xaxis=dict(
            title_font=dict(size=13, weight='bold'),
            tickfont=dict(size=11)
        ),
        title_font=dict(size=16, weight='bold')
    )
    
    # Adicionar anotação
    fig.add_annotation(
        text='* Valores são simulações educativas, não substituem avaliações de campo',
        xref='paper',
        yref='paper',
        x=0.5,
        y=-0.15,
        showarrow=False,
        font=dict(size=10, color='#666666', style='italic')
    )
    
    return fig

def criar_resumo_recomendacao(cultura, produtividade, dose_n, fertilizante, qtd_fertilizante, bioinsumo, manejo, explicacao):
    """
    Cria um resumo em card com as principais recomendações.
    """
    resumo = f"""
    <div style="background-color: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
        <h3 style="color: #1b5e20; margin-bottom: 15px;">📋 Resumo da Recomendação</h3>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div><strong>🌾 Cultura:</strong> {cultura}</div>
            <div><strong>📊 Produtividade esperada:</strong> {produtividade:.0f} kg/ha</div>
            <div><strong>🧪 Dose de N recomendada:</strong> {dose_n} kg/ha</div>
            <div><strong>🧴 Fertilizante sugerido:</strong> {fertilizante}</div>
            <div><strong>⚖️ Quantidade de fertilizante:</strong> {qtd_fertilizante:.1f} kg/ha</div>
            <div><strong>🦠 Bioinsumo recomendado:</strong> {bioinsumo}</div>
            <div style="grid-column: span 2;"><strong>📌 Estratégia de aplicação:</strong> {manejo['estrategia']}</div>
            <div style="grid-column: span 2;"><strong>📅 Parcelamento sugerido:</strong> {manejo['parcelamento']}</div>
            <div style="grid-column: span 2; color: #f57c00; font-size: 0.9rem; margin-top: 10px;">
                <i>ℹ️ {manejo['observacao']}</i>
            </div>
        </div>
        <div style="margin-top: 15px; padding: 10px; background-color: #f5f5f5; border-radius: 8px; font-size: 0.85rem; font-family: monospace; white-space: pre-wrap;">
            <strong>📐 Detalhamento do cálculo:</strong>
            {explicacao}
        </div>
        <div style="margin-top: 15px; padding: 10px; background-color: #fff8e1; border-radius: 8px; font-size: 0.9rem;">
            <strong>⚠️ Importante:</strong> Esta recomendação é uma estimativa educativa. 
            Para uso real, consulte um engenheiro agrônomo e siga boletins técnicos regionais.
        </div>
    </div>
    """
    return resumo

def validar_campos_obrigatorios():
    """Valida se os campos obrigatórios estão preenchidos."""
    if not st.session_state.propriedade.get('nome'):
        return False, "Nome da propriedade é obrigatório"
    if not st.session_state.analise_solo:
        return False, "Análise de solo não configurada"
    return True, "OK"

# ===================== INICIALIZAÇÃO DA SESSÃO =====================
init_session_state()

# ===================== BARRA LATERAL =====================
with st.sidebar:
    st.markdown("### 🌱 Navegação Rápida")
    st.markdown("---")
    
    # Status do sistema
    st.markdown("#### 📊 Status")
    if st.session_state.propriedade.get('nome'):
        st.success(f"✅ Propriedade: {st.session_state.propriedade['nome']}")
    else:
        st.warning("⚠️ Propriedade não cadastrada")
    
    if st.session_state.analise_solo:
        st.success("✅ Análise de solo configurada")
    else:
        st.warning("⚠️ Análise de solo não configurada")
    
    if st.session_state.recomendacao:
        st.success("✅ Recomendação disponível")
    else:
        st.info("ℹ️ Aguardando recomendação")
    
    st.markdown("---")
    st.markdown("""
    <div style="font-size: 0.8rem; color: #666;">
        <strong>Versão:</strong> 1.0.0<br>
        <strong>Desenvolvido para:</strong> Disciplina de IA<br>
        <strong>Propósito:</strong> Educacional
    </div>
    """, unsafe_allow_html=True)

# ===================== TÍTULO PRINCIPAL =====================
st.markdown('<div class="title-main">🌱 Sistema de Apoio à Decisão</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Manejo de nitrogênio, fertilidade e bioinsumos em sistemas agrícolas</div>', unsafe_allow_html=True)

# ===================== NAVEGAÇÃO POR ABAS =====================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Cadastro da Propriedade", 
    "🌿 Caracterização do Plantio", 
    "🧪 Recomendação Agronômica", 
    "📚 Referências e Metodologia"
])

# ===================== ABA 1 - CADASTRO DA PROPRIEDADE =====================
with tab1:
    st.header("📋 Cadastro da Propriedade")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Informações Gerais")
            
            nome_prop = st.text_input("Nome da propriedade*", value=st.session_state.propriedade.get('nome', ''), help="Campo obrigatório")
            nome_proprietario = st.text_input("Nome do proprietário", value=st.session_state.propriedade.get('proprietario', ''))
            municipio = st.text_input("Município", value=st.session_state.propriedade.get('municipio', ''))
            estado = st.text_input("Estado (UF)", value=st.session_state.propriedade.get('estado', ''))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Características da Área")
            
            area_irrigada = st.number_input(
                "Área agricultável irrigada (ha)", 
                min_value=0.0, 
                value=float(st.session_state.propriedade.get('area_irrigada', 0)),
                step=0.5,
                format="%.1f"
            )
            area_sequeiro = st.number_input(
                "Área agricultável de sequeiro (ha)", 
                min_value=0.0, 
                value=float(st.session_state.propriedade.get('area_sequeiro', 0)),
                step=0.5,
                format="%.1f"
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Coordenadas e tipo de manejo
    col3, col4 = st.columns(2)
    
    with col3:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🌍 Coordenadas Geográficas")
            
            lat = st.text_input("Latitude", value=st.session_state.propriedade.get('latitude', ''), placeholder="Ex: -22.9068")
            lon = st.text_input("Longitude", value=st.session_state.propriedade.get('longitude', ''), placeholder="Ex: -47.0616")
            
            st.caption("Formato: graus decimais (ex: -22.9068, -47.0616)")
            
            # Exibir status da API
            if GOOGLE_MAPS_API_KEY != "INSERIR_CHAVE_API_AQUI":
                st.success("✅ Chave API de mapas configurada")
                st.caption("🔑 API Key: " + GOOGLE_MAPS_API_KEY[:8] + "..." + GOOGLE_MAPS_API_KEY[-4:])
            else:
                st.warning("⚠️ Chave API não configurada")
                st.caption("Para integrar com Google Maps, insira a chave no código (variável GOOGLE_MAPS_API_KEY)")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🔄 Tipo de Manejo")
            
            manejo = st.selectbox(
                "Manejo predominante",
                ["Plantio direto", "Plantio convencional", "Sistema mínimo", "Integração lavoura-pecuária", "Outro"],
                index=0 if st.session_state.propriedade.get('manejo', '') == '' else 
                      ["Plantio direto", "Plantio convencional", "Sistema mínimo", "Integração lavoura-pecuária", "Outro"].index(st.session_state.propriedade.get('manejo', 'Plantio direto'))
            )
            
            outro_manejo = ""
            if manejo == "Outro":
                outro_manejo = st.text_input("Especificar manejo", value=st.session_state.propriedade.get('outro_manejo', ''))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Análise de solo
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.subheader("🧪 Análise de Solo")
    
    tem_analise = st.radio(
        "O produtor possui análise de solo?",
        ["Sim", "Não"],
        index=0 if st.session_state.tem_analise != "Não" else 1,
        horizontal=True
    )
    st.session_state.tem_analise = tem_analise
    
    if tem_analise == "Sim":
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.info("📊 Preencha os dados da análise de solo. Campos com * são recomendados para melhor precisão.")
        
        col5, col6 = st.columns(2)
        
        with col5:
            ph = st.number_input("pH (CaCl2 ou água)*", min_value=3.0, max_value=8.0, value=float(st.session_state.analise_solo.get('ph', 5.8)), step=0.1)
            materia_organica = st.number_input("Matéria orgânica (%)*", min_value=0.0, max_value=10.0, value=float(st.session_state.analise_solo.get('materia_organica', 2.5)), step=0.1)
            fosforo = st.number_input("Fósforo (mg/dm³)", min_value=0, max_value=200, value=int(st.session_state.analise_solo.get('fosforo', 15)), step=1)
            potassio = st.number_input("Potássio (mg/dm³)", min_value=0, max_value=500, value=int(st.session_state.analise_solo.get('potassio', 120)), step=1)
            calcio = st.number_input("Cálcio (cmolc/dm³)", min_value=0.0, max_value=20.0, value=float(st.session_state.analise_solo.get('calcio', 4.0)), step=0.1)
            magnesio = st.number_input("Magnésio (cmolc/dm³)", min_value=0.0, max_value=10.0, value=float(st.session_state.analise_solo.get('magnesio', 1.5)), step=0.1)
            
        with col6:
            aluminio = st.number_input("Alumínio (cmolc/dm³)", min_value=0.0, max_value=5.0, value=float(st.session_state.analise_solo.get('aluminio', 0.3)), step=0.1)
            h_al = st.number_input("H + Al (cmolc/dm³)", min_value=0.0, max_value=20.0, value=float(st.session_state.analise_solo.get('h_al', 4.5)), step=0.1)
            ctc = st.number_input("CTC (cmolc/dm³)", min_value=0.0, max_value=30.0, value=float(st.session_state.analise_solo.get('ctc', 8.5)), step=0.1)
            sb = st.number_input("Saturação por bases (%)", min_value=0, max_value=100, value=int(st.session_state.analise_solo.get('sb', 65)), step=1)
            enxofre = st.number_input("Enxofre (mg/dm³)", min_value=0, max_value=100, value=int(st.session_state.analise_solo.get('enxofre', 10)), step=1)
            boro = st.number_input("Boro (mg/dm³)", min_value=0.0, max_value=5.0, value=float(st.session_state.analise_solo.get('boro', 0.5)), step=0.1)
            zinco = st.number_input("Zinco (mg/dm³)", min_value=0.0, max_value=10.0, value=float(st.session_state.analise_solo.get('zinco', 1.5)), step=0.1)
            
            textura = st.selectbox(
                "Textura do solo*",
                ["Arenosa", "Média", "Argilosa", "Muito argilosa"],
                index=["Arenosa", "Média", "Argilosa", "Muito argilosa"].index(st.session_state.analise_solo.get('textura', 'Média'))
            )
        
        # Salvar no session_state
        st.session_state.analise_solo = {
            'ph': ph,
            'materia_organica': materia_organica,
            'fosforo': fosforo,
            'potassio': potassio,
            'calcio': calcio,
            'magnesio': magnesio,
            'aluminio': aluminio,
            'h_al': h_al,
            'ctc': ctc,
            'sb': sb,
            'enxofre': enxofre,
            'boro': boro,
            'zinco': zinco,
            'textura': textura
        }
        
        st.markdown('</div>', unsafe_allow_html=True)
        
    else:
        st.markdown('<div class="card-warning">', unsafe_allow_html=True)
        st.warning("⚠️ **Atenção:** Como não foi informada análise de solo, o sistema utilizará valores médios simulados apenas para fins educativos.")
        
        # Usar valores padrão
        valores_padrao = get_valores_padrao()
        st.session_state.analise_solo = valores_padrao
        
        # Mostrar valores que serão usados
        with st.expander("📊 Ver valores médios que serão utilizados"):
            col7, col8 = st.columns(2)
            with col7:
                st.write("**Macronutrientes:**")
                st.write(f"• pH: {valores_padrao['ph']}")
                st.write(f"• Matéria orgânica: {valores_padrao['materia_organica']}%")
                st.write(f"• Fósforo: {valores_padrao['fosforo']} mg/dm³")
                st.write(f"• Potássio: {valores_padrao['potassio']} mg/dm³")
                st.write(f"• Cálcio: {valores_padrao['calcio']} cmolc/dm³")
                st.write(f"• Magnésio: {valores_padrao['magnesio']} cmolc/dm³")
            with col8:
                st.write("**Outros atributos:**")
                st.write(f"• Alumínio: {valores_padrao['aluminio']} cmolc/dm³")
                st.write(f"• H + Al: {valores_padrao['h_al']} cmolc/dm³")
                st.write(f"• CTC: {valores_padrao['ctc']} cmolc/dm³")
                st.write(f"• Sat. bases: {valores_padrao['sb']}%")
                st.write(f"• Enxofre: {valores_padrao['enxofre']} mg/dm³")
                st.write(f"• Boro: {valores_padrao['boro']} mg/dm³")
                st.write(f"• Zinco: {valores_padrao['zinco']} mg/dm³")
                st.write(f"• Textura: {valores_padrao['textura']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Salvar dados da propriedade
    st.session_state.propriedade = {
        'nome': nome_prop,
        'proprietario': nome_proprietario,
        'municipio': municipio,
        'estado': estado,
        'area_irrigada': area_irrigada,
        'area_sequeiro': area_sequeiro,
        'latitude': lat,
        'longitude': lon,
        'manejo': manejo,
        'outro_manejo': outro_manejo if manejo == "Outro" else ''
    }
    
    # Botão para salvar
    if st.button("💾 Salvar Dados da Propriedade", use_container_width=True):
        st.session_state.dados_salvos = True
        st.success("✅ Dados da propriedade e análise de solo salvos com sucesso!")
        
        # Mostrar resumo
        with st.expander("📋 Resumo dos dados salvos"):
            st.write("**Propriedade:**", nome_prop)
            st.write("**Município:**", municipio)
            st.write("**Área irrigada:**", f"{area_irrigada} ha")
            st.write("**Área sequeiro:**", f"{area_sequeiro} ha")
            st.write("**Manejo:**", manejo)
            st.write("**Análise de solo:**", "✅ Disponível" if tem_analise == "Sim" else "⚠️ Valores médios")

# ===================== ABA 2 - CARACTERIZAÇÃO DO PLANTIO =====================
with tab2:
    st.header("🌿 Caracterização do Plantio")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Culturas e Sistemas")
            
            culturas = st.multiselect(
                "Quais culturas são plantadas atualmente?",
                ["Soja", "Milho", "Trigo", "Feijão", "Sorgo", "Algodão", "Braquiária", "Milheto", "Outra"],
                default=st.session_state.plantio.get('culturas', [])
            )
            
            outra_cultura = ""
            if "Outra" in culturas:
                outra_cultura = st.text_input("Especificar outra cultura", value=st.session_state.plantio.get('outra_cultura', ''))
            
            sistema = st.selectbox(
                "Sistema de cultivo",
                ["Solteiro", "Consorciado"],
                index=0 if st.session_state.plantio.get('sistema', '') == '' else
                      ["Solteiro", "Consorciado"].index(st.session_state.plantio.get('sistema', 'Solteiro'))
            )
            
            tipo_consorcio = None
            outro_consorcio = None
            
            if sistema == "Consorciado":
                # Lista de opções com validação
                opcoes_tipo_consorcio = [
                    "Milho + braquiária",
                    "Soja + braquiária",
                    "Sorgo + braquiária",
                    "Mix de cobertura",
                    "Outro"
                ]
                
                valor_salvo = st.session_state.plantio.get("tipo_consorcio", "Milho + braquiária")
                
                # Validar se o valor salvo está na lista
                if valor_salvo in opcoes_tipo_consorcio:
                    indice_tipo_consorcio = opcoes_tipo_consorcio.index(valor_salvo)
                else:
                    indice_tipo_consorcio = 0
                
                tipo_consorcio = st.selectbox(
                    "Tipo de consórcio",
                    opcoes_tipo_consorcio,
                    index=indice_tipo_consorcio
                )
                
                if tipo_consorcio == "Outro":
                    outro_consorcio = st.text_input("Especificar consórcio", value=st.session_state.plantio.get('outro_consorcio', ''))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Manejo e Rotação")
            
            revolvimento = st.selectbox(
                "Há revolvimento de solo?",
                ["Sim", "Não", "Ocasional"],
                index=0 if st.session_state.plantio.get('revolvimento', '') == '' else
                      ["Sim", "Não", "Ocasional"].index(st.session_state.plantio.get('revolvimento', 'Não'))
            )
            
            rotacao = st.selectbox(
                "Sistema de rotação de culturas",
                ["Sem rotação definida", "Soja/milho", "Soja/trigo", "Soja/milho/braquiária", "Soja/milheto", 
                 "Sistema com plantas de cobertura", "Outro"],
                index=0 if st.session_state.plantio.get('rotacao', '') == '' else
                      ["Sem rotação definida", "Soja/milho", "Soja/trigo", "Soja/milho/braquiária", "Soja/milheto", 
                       "Sistema com plantas de cobertura", "Outro"].index(st.session_state.plantio.get('rotacao', 'Sem rotação definida'))
            )
            
            outra_rotacao = ""
            if rotacao == "Outro":
                outra_rotacao = st.text_input("Especificar rotação", value=st.session_state.plantio.get('outra_rotacao', ''))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Bioinsumos
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    col3, col4 = st.columns([1, 1])
    
    with col3:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🦠 Uso de Bioinsumos")
            
            usa_bio = st.radio(
                "Uso de bioinsumos?",
                ["Sim", "Não"],
                index=0 if st.session_state.usa_bioinsumos != "Não" else 1,
                horizontal=True
            )
            st.session_state.usa_bioinsumos = usa_bio
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        if usa_bio == "Sim":
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                st.subheader("Bioinsumos Utilizados")
                
                bioinsumos = st.multiselect(
                    "Quais bioinsumos são utilizados?",
                    ["Azospirillum brasilense", "Bradyrhizobium", "Bacillus subtilis", 
                     "Bacillus amyloliquefaciens", "Pseudomonas fluorescens", "Trichoderma spp.", 
                     "Micorrizas", "Outros"],
                    default=st.session_state.plantio.get('bioinsumos', [])
                )
                
                st.session_state.plantio['bioinsumos'] = bioinsumos
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Salvar dados do plantio
    st.session_state.plantio.update({
        'culturas': culturas,
        'outra_cultura': outra_cultura if 'outra_cultura' in locals() else '',
        'sistema': sistema,
        'tipo_consorcio': tipo_consorcio if sistema == "Consorciado" else None,
        'outro_consorcio': outro_consorcio if sistema == "Consorciado" and tipo_consorcio == "Outro" else None,
        'revolvimento': revolvimento,
        'rotacao': rotacao,
        'outra_rotacao': outra_rotacao if rotacao == "Outro" else '',
        'usa_bioinsumos': usa_bio
    })
    
    if st.button("💾 Salvar Dados do Plantio", use_container_width=True):
        st.success("✅ Dados do plantio salvos com sucesso!")

# ===================== ABA 3 - RECOMENDAÇÃO AGRONÔMICA =====================
with tab3:
    st.header("🧪 Recomendação Agronômica")
    
    # Verificar se há dados de análise de solo
    if not st.session_state.analise_solo:
        st.warning("⚠️ Nenhuma análise de solo disponível. Acesse a aba 'Cadastro da Propriedade' para configurar.")
        st.stop()
    
    # Verificar se propriedade foi cadastrada
    if not st.session_state.propriedade.get('nome'):
        st.warning("⚠️ Propriedade não cadastrada. Acesse a aba 'Cadastro da Propriedade' primeiro.")
    
    # Inputs do usuário
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Informações para Recomendação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cultura_escolhida = st.selectbox(
                "Cultura que pretende cultivar*",
                ["Milho", "Trigo", "Soja", "Feijão", "Sorgo", "Algodão"],
                index=0,
                key="cultura_escolhida"
            )
            
            unidade_prod = st.selectbox(
                "Unidade de produtividade",
                ["kg/ha", "sacas/ha"],
                index=0,
                help="Escolha a unidade para a produtividade esperada",
                key="unidade_prod"
            )
            
            if unidade_prod == "kg/ha":
                produtividade = st.number_input(
                    "Produtividade esperada (kg/ha)*", 
                    min_value=100, 
                    max_value=20000, 
                    value=6000 if cultura_escolhida == "Milho" else 3000,
                    step=100,
                    help="Exemplo: 6000 kg/ha para milho",
                    key="produtividade_kg"
                )
            else:
                # Converter sacas para kg (assumindo 60kg por saca para maioria)
                produtividade_sacas = st.number_input(
                    "Produtividade esperada (sacas/ha)*", 
                    min_value=1, 
                    max_value=300, 
                    value=100 if cultura_escolhida == "Milho" else 50,
                    step=1,
                    help="Exemplo: 100 sacas/ha para milho",
                    key="produtividade_sacas"
                )
                produtividade = produtividade_sacas * 60  # kg/ha
        
        with col2:
            ambiente = st.selectbox(
                "Tipo de ambiente*",
                ["Irrigado", "Sequeiro"],
                index=0,
                help="Irrigado = com irrigação disponível | Sequeiro = sem irrigação",
                key="ambiente"
            )
            
            leguminosa = st.selectbox(
                "Possui palhada ou cultura anterior leguminosa?",
                ["Sim", "Não"],
                index=1,
                help="Leguminosas fixam nitrogênio, reduzindo a necessidade de adubação",
                key="leguminosa"
            )
            
            cultura_anterior = st.selectbox(
                "Cultura anterior*",
                ["Soja", "Milho", "Braquiária", "Milheto", "Trigo", "Feijão", "Outra"],
                index=0,
                key="cultura_anterior"
            )
            
            outra_cultura_anterior = ""
            if cultura_anterior == "Outra":
                outra_cultura_anterior = st.text_input("Especificar cultura anterior", key="outra_cultura_anterior")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botão para gerar recomendação
    if st.button("🔬 Gerar Recomendação", use_container_width=True, type="primary"):
        
        # Validar campos obrigatórios
        if not cultura_escolhida or not produtividade:
            st.error("❌ Por favor, preencha todos os campos obrigatórios (*)")
            st.stop()
        
        # Obter dados da análise de solo
        analise = st.session_state.analise_solo
        textura = analise.get('textura', 'Média')
        mo = analise.get('materia_organica', 2.5)
        ph = analise.get('ph', 5.8)
        
        # Obter manejo do solo da propriedade
        manejo_solo = st.session_state.propriedade.get('manejo', 'Plantio direto')
        
        # Obter uso de bioinsumos
        usa_bioinsumos = st.session_state.usa_bioinsumos
        
        # Calcular dose de N com a nova função
        dose_n, explicacao, observacao_bio = calcular_dose_nitrogenio(
            cultura_escolhida, 
            produtividade, 
            ambiente, 
            cultura_anterior, 
            leguminosa, 
            textura, 
            mo,
            manejo_solo,
            usa_bioinsumos
        )
        
        # Escolher fertilizante
        fertilizante, teor_n, descricao = escolher_fertilizante(dose_n, cultura_escolhida, ambiente, ph)
        
        # Calcular quantidade
        qtd_fertilizante = calcular_quantidade_fertilizante(dose_n, teor_n)
        
        # Recomendar manejo
        manejo = recomendar_manejo_nitrogenio(cultura_escolhida, dose_n, ambiente)
        
        # Recomendar bioinsumos
        bio_recomendacao = recomendar_bioinsumos(
            cultura_escolhida, 
            st.session_state.usa_bioinsumos,
            st.session_state.plantio.get('bioinsumos', [])
        )
        
        # Salvar no session_state
        st.session_state.recomendacao = {
            'cultura': cultura_escolhida,
            'produtividade': produtividade,
            'dose_n': dose_n,
            'fertilizante': fertilizante,
            'teor_n': teor_n,
            'qtd_fertilizante': qtd_fertilizante,
            'manejo': manejo,
            'bioinsumos': bio_recomendacao,
            'ambiente': ambiente,
            'leguminosa': leguminosa,
            'cultura_anterior': cultura_anterior,
            'explicacao': explicacao,
            'observacao_bio': observacao_bio
        }
        
        # Exibir resultados
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="highlight-box">', unsafe_allow_html=True)
        st.subheader("📋 Recomendação Gerada")
        st.caption(f"Baseada na análise de solo {'informada' if st.session_state.tem_analise == 'Sim' else 'média (educativa)'}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 1. Recomendação de Nitrogênio
        st.markdown('<div class="card card-azul">', unsafe_allow_html=True)
        st.subheader("🧪 1. Recomendação de Nitrogênio")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.metric("Dose estimada de N", f"{dose_n} kg/ha")
            st.metric("Fertilizante recomendado", fertilizante)
            st.metric("Quantidade aproximada", f"{qtd_fertilizante:.1f} kg/ha")
            st.caption(f"Teor de N do {fertilizante}: {teor_n*100:.0f}%")
        
        with col4:
            st.write("**Estratégia de manejo:**")
            st.write(f"📌 {manejo['estrategia']}")
            st.write(f"📅 {manejo['parcelamento']}")
            st.info(f"ℹ️ {manejo['observacao']}")
            if observacao_bio:
                st.info(f"🦠 {observacao_bio}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 2. Recomendação de Bioinsumos
        st.markdown('<div class="card card-success">', unsafe_allow_html=True)
        st.subheader("🦠 2. Recomendação de Bioinsumos")
        
        col5, col6 = st.columns(2)
        
        with col5:
            st.write("**Microrganismos recomendados:**")
            for micro in bio_recomendacao['microrganismos']:
                st.write(f"• {micro}")
        
        with col6:
            st.write("**Forma de uso recomendada:**")
            st.write(f"📋 {bio_recomendacao['forma_uso']}")
            st.write("**Cuidados importantes:**")
            st.write(f"⚠️ {bio_recomendacao['cuidados']}")
            if 'observacao' in bio_recomendacao:
                st.write(f"📝 {bio_recomendacao['observacao']}")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 3. Gráfico de desempenho
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("📊 3. Projeção de Desempenho")
        
        try:
            fig = gerar_grafico_performance(
                dose_n=dose_n,
                cultura=cultura_escolhida,
                produtividade=produtividade,
                ambiente=ambiente,
                manejo_solo=manejo_solo,
                usa_bioinsumos=usa_bioinsumos
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning("⚠️ Não foi possível gerar o gráfico de desempenho.")
            st.caption(f"Detalhe técnico: {e}")
        
        st.caption("* Os dados apresentados no gráfico são simulações educativas baseadas em incrementos percentuais estimados.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 4. Resumo Final
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        bio_principal = ', '.join(bio_recomendacao['microrganismos'][:2])
        resumo_html = criar_resumo_recomendacao(
            cultura_escolhida,
            produtividade,
            dose_n,
            fertilizante,
            qtd_fertilizante,
            bio_principal,
            manejo,
            explicacao
        )
        st.markdown(resumo_html, unsafe_allow_html=True)
        
        # Botão para baixar relatório
        if st.button("📥 Baixar Recomendação (Texto)", use_container_width=True):
            relatorio = f"""
            ========================================
            RELATÓRIO DE RECOMENDAÇÃO AGRONÔMICA
            ========================================
            
            PROPRIEDADE: {st.session_state.propriedade.get('nome', 'Não informado')}
            PROPRIETÁRIO: {st.session_state.propriedade.get('proprietario', 'Não informado')}
            MUNICÍPIO: {st.session_state.propriedade.get('municipio', 'Não informado')}
            
            ----------------------------------------
            RECOMENDAÇÃO DE NITROGÊNIO
            ----------------------------------------
            Cultura: {cultura_escolhida}
            Produtividade esperada: {produtividade:.0f} kg/ha
            Dose de N recomendada: {dose_n} kg/ha
            Fertilizante: {fertilizante}
            Quantidade: {qtd_fertilizante:.1f} kg/ha
            Estratégia: {manejo['estrategia']}
            Parcelamento: {manejo['parcelamento']}
            
            ----------------------------------------
            RECOMENDAÇÃO DE BIOINSUMOS
            ----------------------------------------
            Microrganismos: {', '.join(bio_recomendacao['microrganismos'])}
            Forma de uso: {bio_recomendacao['forma_uso']}
            Cuidados: {bio_recomendacao['cuidados']}
            
            ----------------------------------------
            DETALHAMENTO DO CÁLCULO
            ----------------------------------------
            {explicacao}
            
            ----------------------------------------
            OBSERVAÇÕES
            ----------------------------------------
            {manejo['observacao']}
            {observacao_bio}
            
            ⚠️ Esta recomendação é uma estimativa educativa.
            Para uso real, consulte um engenheiro agrônomo.
            
            Data de geração: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            """
            
            st.download_button(
                label="💾 Baixar como TXT",
                data=relatorio,
                file_name=f"recomendacao_{cultura_escolhida}_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
        
        st.success("✅ Recomendação gerada com sucesso!")

# ===================== ABA 4 - REFERÊNCIAS E METODOLOGIA =====================
with tab4:
    st.header("📚 Referências e Metodologia")
    
    # Introdução
    st.markdown("""
    <div class="card">
        <h3>📖 Sobre o Sistema</h3>
        <p>Este sistema foi desenvolvido como ferramenta educacional para apoio à decisão no manejo de nitrogênio, 
        fertilidade e bioinsumos em sistemas agrícolas. Utiliza regras condicionais baseadas em literatura 
        agronômica para estimar recomendações.</p>
        <p><span class="info-badge">Educacional</span></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metodologia
    st.markdown("""
    <div class="card card-azul">
        <h4>🔬 Metodologia de Cálculo</h4>
        <p><strong>1. Dose de Nitrogênio:</strong></p>
        <p>A dose recomendada é calculada utilizando a fórmula:</p>
        <div style="background: #f5f5f5; padding: 10px; border-radius: 6px; font-family: monospace; margin: 10px 0;">
        Dose N = (Fator_base × Produtividade_t) × Fator_ambiente × Fator_cultura_anterior × Fator_textura × Fator_MO × Fator_manejo × Fator_bioinsumos
        </div>
        <p><strong>Onde:</strong></p>
        <ul>
            <li><strong>Fator_base:</strong> kg de N por tonelada de produto (varia por cultura)</li>
            <li><strong>Produtividade_t:</strong> Produtividade em toneladas por hectare</li>
            <li><strong>Fator_ambiente:</strong> 1.0-1.2 para irrigado, 0.85-0.95 para sequeiro</li>
            <li><strong>Fator_cultura_anterior:</strong> 0.7 para leguminosas, 0.85 para braquiária/milheto</li>
            <li><strong>Fator_textura:</strong> 1.15 (arenosa), 1.0 (média), 0.9 (argilosa)</li>
            <li><strong>Fator_MO:</strong> 0.8-0.9 (MO alta), 1.1-1.2 (MO baixa)</li>
            <li><strong>Fator_manejo:</strong> 0.9 (plantio direto), 1.15 (convencional)</li>
            <li><strong>Fator_bioinsumos:</strong> 0.95 (com bioinsumos)</li>
        </ul>
        <br>
        <p><strong>2. Quantidade de Fertilizante:</strong></p>
        <p>Quantidade (kg/ha) = Dose N recomendada (kg/ha) / Teor de N do fertilizante</p>
        <p><strong>Exemplo:</strong> Ureia possui aproximadamente 45% de N.</p>
        <p>Se a dose recomendada for 120 kg/ha de N: 120 / 0,45 = 266,7 kg/ha de ureia</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Tabela de teores de N
    st.markdown("""
    <div class="card">
        <h4>📊 Teor Médio de Nitrogênio dos Fertilizantes</h4>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background-color: #e8f5e9;">
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Fertilizante</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Teor de N (%)</th>
                    <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Características</th>
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Ureia</td><td style="padding: 8px; border: 1px solid #ddd;">45%</td><td style="padding: 8px; border: 1px solid #ddd;">Alta concentração, cobertura</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Sulfato de amônio</td><td style="padding: 8px; border: 1px solid #ddd;">20% a 21%</td><td style="padding: 8px; border: 1px solid #ddd;">Fonte de N + S, acidificante</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Nitrato de amônio</td><td style="padding: 8px; border: 1px solid #ddd;">32% a 34%</td><td style="padding: 8px; border: 1px solid #ddd;">N de rápida disponibilidade</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">MAP</td><td style="padding: 8px; border: 1px solid #ddd;">10% a 11%</td><td style="padding: 8px; border: 1px solid #ddd;">Fosfato monoamônico</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">DAP</td><td style="padding: 8px; border: 1px solid #ddd;">18%</td><td style="padding: 8px; border: 1px solid #ddd;">Fosfato diamônico</td></tr>
            </tbody>
        </table>
        <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">* Teores aproximados para fins educativos</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Limitações
    st.markdown("""
    <div class="card card-warning">
        <h4>⚠️ Limitações do Sistema</h4>
        <ul>
            <li>As recomendações são <strong>estimativas educativas</strong>, não substituem avaliação técnica profissional.</li>
            <li>Quando não há análise de solo, o sistema utiliza <strong>valores médios simulados</strong>.</li>
            <li>O gráfico de desempenho é uma <strong>projeção didática</strong> baseada em incrementos percentuais estimados.</li>
            <li>Para uso real, consulte um <strong>engenheiro agrônomo</strong> e siga boletins técnicos regionais.</li>
            <li>O sistema não considera todos os fatores de campo (clima, pragas, doenças, etc.).</li>
            <li>Os valores são baseados em <strong>regras simplificadas</strong> e podem não refletir condições específicas.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Referências
    st.markdown("""
    <div class="card">
        <h4>📚 Referências Bibliográficas</h4>
        <ul>
            <li><strong>EMBRAPA.</strong> Sistemas de produção e recomendações técnicas para culturas anuais.</li>
            <li><strong>RAIJ, B. van et al.</strong> Recomendações de adubação e calagem para o Estado de São Paulo. Boletim Técnico 100. IAC.</li>
            <li><strong>MALAVOLTA, E.</strong> Manual de nutrição mineral de plantas.</li>
            <li><strong>TAIZ, L. et al.</strong> Fisiologia e desenvolvimento vegetal.</li>
            <li><strong>HUNGRIA, M. et al.</strong> Estudos sobre inoculação, fixação biológica de nitrogênio e uso de rizobactérias na agricultura.</li>
            <li><strong>DOBBELAERE, S.; VANDERLEYDEN, J.; OKON, Y.</strong> Plant growth-promoting effects of diazotrophs.</li>
            <li><strong>FAGERIA, N.K.</strong> Eficiência de uso de nitrogênio em culturas anuais.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Como funciona
    st.markdown("""
    <div class="card card-info">
        <h4>💡 Como o Sistema Funciona</h4>
        <ol>
            <li><strong>Coleta de dados:</strong> O sistema coleta informações sobre a propriedade, análise de solo e caracterização do plantio.</li>
            <li><strong>Cálculo da dose de N:</strong> A dose recomendada é calculada com base na cultura, produtividade esperada, ambiente, cultura anterior, textura do solo e teor de matéria orgânica.</li>
            <li><strong>Recomendação do fertilizante:</strong> O sistema sugere o fertilizante mais adequado com base na cultura, dose de N e características do solo.</li>
            <li><strong>Bioinsumos:</strong> Recomendação de microrganismos benéficos específicos para cada cultura.</li>
            <li><strong>Projeção educativa:</strong> Gráfico mostrando estimativas de produtividade em diferentes cenários de manejo.</li>
        </ol>
        <p style="margin-top: 10px; color: #1b5e20;"><strong>✅ Nota:</strong> Todas as recomendações são baseadas em regras agronômicas simplificadas e têm caráter educativo.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Fontes de dados
    st.markdown("""
    <div class="card">
        <h4>📊 Fontes de Dados Utilizadas</h4>
        <ul>
            <li><strong>Valores de referência:</strong> Embrapa, IAC e literatura científica</li>
            <li><strong>Fatores de cultura:</strong> Baseados em recomendações oficiais de adubação</li>
            <li><strong>Bioinsumos:</strong> Literatura sobre rizobactérias promotoras de crescimento</li>
            <li><strong>Eficiência de N:</strong> Estudos sobre eficiência de uso de nitrogênio</li>
            <li><strong>Valores médios:</strong> Quando não há análise de solo, utiliza-se dados de solos brasileiros</li>
        </ul>
        <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">* Para dados precisos, recomenda-se realizar análise de solo específica.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Status
    st.markdown("""
    <div class="card">
        <h4>🔌 Status das APIs</h4>
        <ul>
            <li><strong>Google Maps API:</strong> {} </li>
            <li><strong>OpenWeather API:</strong> {} </li>
        </ul>
        <p style="margin-top: 10px; font-size: 0.9rem; color: #666;">* APIs configuradas para futuras integrações</p>
    </div>
    """.format(
        "✅ Configurada" if GOOGLE_MAPS_API_KEY != "INSERIR_CHAVE_API_AQUI" else "⚠️ Não configurada",
        "✅ Configurada" if OPENWEATHER_API_KEY != "INSERIR_CHAVE_API_AQUI" else "⚠️ Não configurada"
    ), unsafe_allow_html=True)

# ===================== RODAPÉ =====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem; padding: 20px;">
    <p>🌱 Sistema de Apoio à Decisão - Manejo de Nitrogênio | Versão 1.0.0</p>
    <p>Desenvolvido para disciplina de IA | Propósito educacional</p>
    <p>© 2026 - Todos os direitos reservados</p>
</div>
""", unsafe_allow_html=True)
