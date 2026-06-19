# app.py
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
</style>
""", unsafe_allow_html=True)

# ===================== CHAVE API (FUTURA) =====================
GOOGLE_MAPS_API_KEY = "INSERIR_CHAVE_API_AQUI"

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

def calcular_dose_nitrogenio(cultura, produtividade, ambiente, cultura_anterior, leguminosa, textura, materia_organica):
    """
    Calcula a dose recomendada de nitrogênio (kg/ha) com base em regras agronômicas simplificadas.
    """
    # Fatores base por cultura (kg de N por saca ou tonelada)
    fatores_base = {
        'Milho': 1.2,  # kg N por saca de 60kg
        'Trigo': 1.5,  # kg N por saca de 60kg
        'Soja': 0.3,   # kg N por saca de 60kg (fixação simbiótica)
        'Feijão': 0.8, # kg N por saca de 60kg
        'Sorgo': 1.0,  # kg N por saca de 60kg
        'Algodão': 2.0 # kg N por tonelada de pluma
    }
    
    # Ajuste por ambiente
    fator_ambiente = 1.3 if ambiente == 'Irrigado' else 1.0
    
    # Ajuste por cultura anterior e leguminosa
    fator_cultura_anterior = 1.0
    if cultura_anterior in ['Soja', 'Feijão']:
        fator_cultura_anterior = 0.7
    elif cultura_anterior in ['Braquiária', 'Milheto']:
        fator_cultura_anterior = 0.85
    
    if leguminosa == 'Sim':
        fator_cultura_anterior *= 0.8
    
    # Ajuste por textura e matéria orgânica
    fator_textura = {'Arenosa': 1.2, 'Média': 1.0, 'Argilosa': 0.9, 'Muito argilosa': 0.8}
    fator_text = fator_textura.get(textura, 1.0)
    
    # Ajuste por matéria orgânica
    fator_mo = 1.0
    if materia_organica:
        if materia_organica > 3.0:
            fator_mo = 0.85
        elif materia_organica > 2.0:
            fator_mo = 0.95
    
    # Cálculo da dose base
    if cultura in fatores_base:
        dose_base = fatores_base[cultura] * produtividade
    else:
        dose_base = 80  # valor padrão
    
    # Aplicar fatores
    dose_recomendada = dose_base * fator_ambiente * fator_cultura_anterior * fator_text * fator_mo
    
    # Arredondar para múltiplo de 5
    dose_recomendada = round(dose_recomendada / 5) * 5
    
    # Limites mínimos e máximos educativos
    if cultura == 'Soja':
        dose_recomendada = min(max(dose_recomendada, 10), 80)
    else:
        dose_recomendada = min(max(dose_recomendada, 30), 250)
    
    return int(dose_recomendada)

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

def gerar_grafico_performance(dose_n, cultura, produtividade, ambiente):
    """
    Gera gráfico educacional comparando cenários de manejo.
    """
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
    if ambiente == 'Irrigado':
        base *= 1.3
    
    # Ajustar para a produtividade esperada do usuário
    if produtividade:
        base = produtividade
    
    # Cenários com incrementos percentuais educativos
    cenario_sem_manejo = base * 0.65
    cenario_adubacao = base * 0.85
    cenario_adubacao_bio = base * 0.95
    cenario_ideal = base * 1.0
    
    # Ajuste baseado na dose de N
    if dose_n > 80:
        cenario_adubacao *= 1.05
        cenario_adubacao_bio *= 1.05
    
    cenarios = ['Sem manejo otimizado', 'Com adubação N', 'Com adubação + bioinsumos', 'Com manejo integrado']
    valores = [cenario_sem_manejo, cenario_adubacao, cenario_adubacao_bio, cenario_ideal]
    
    # Criar gráfico com Plotly
    fig = go.Figure()
    
    # Cores
    cores = ['#d32f2f', '#ff9800', '#4caf50', '#2e7d32']
    
    fig.add_trace(go.Bar(
        x=cenarios,
        y=valores,
        marker_color=cores,
        text=[f'{v:,.0f} kg/ha' for v in valores],
        textposition='auto',
        textfont=dict(size=12, color='white'),
        hovertemplate='<b>%{x}</b><br>Produtividade: %{text}<extra></extra>'
    ))
    
    fig.update_layout(
        title=f'Estimativa educativa de produtividade - {cultura}',
        xaxis_title='Cenário de manejo',
        yaxis_title='Produtividade estimada (kg/ha)',
        yaxis_gridcolor='#e0e0e0',
        plot_bgcolor='white',
        height=450,
        font=dict(size=12),
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    fig.add_annotation(
        text='* Valores são simulações educativas, não substituem avaliações de campo',
        xref='paper', yref='paper',
        x=0.5, y=-0.15,
        showarrow=False,
        font=dict(size=10, color='#666')
    )
    
    return fig

def criar_resumo_recomendacao(cultura, produtividade, dose_n, fertilizante, qtd_fertilizante, bioinsumo, manejo):
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
        <div style="margin-top: 15px; padding: 10px; background-color: #fff8e1; border-radius: 8px; font-size: 0.9rem;">
            <strong>⚠️ Importante:</strong> Esta recomendação é uma estimativa educativa. 
            Para uso real, consulte um engenheiro agrônomo e siga boletins técnicos regionais.
        </div>
    </div>
    """
    return resumo

# ===================== INICIALIZAÇÃO DA SESSÃO =====================
init_session_state()

# ===================== NAVEGAÇÃO POR ABAS =====================
st.markdown('<div class="title-main">🌱 Sistema de Apoio à Decisão</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Manejo de nitrogênio, fertilidade e bioinsumos em sistemas agrícolas</div>', unsafe_allow_html=True)

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
            
            nome_prop = st.text_input("Nome da propriedade", value=st.session_state.propriedade.get('nome', ''))
            nome_prop = st.text_input("Nome do proprietário", value=st.session_state.propriedade.get('proprietario', ''))
            municipio = st.text_input("Município", value=st.session_state.propriedade.get('municipio', ''))
            estado = st.text_input("Estado", value=st.session_state.propriedade.get('estado', ''))
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("Características da Área")
            
            area_irrigada = st.number_input(
                "Área agricultável irrigada (ha)", 
                min_value=0.0, 
                value=float(st.session_state.propriedade.get('area_irrigada', 0)),
                step=0.5
            )
            area_sequeiro = st.number_input(
                "Área agricultável de sequeiro (ha)", 
                min_value=0.0, 
                value=float(st.session_state.propriedade.get('area_sequeiro', 0)),
                step=0.5
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Coordenadas e tipo de manejo
    col3, col4 = st.columns(2)
    
    with col3:
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("🌍 Coordenadas Geográficas")
            
            lat = st.text_input("Latitude", value=st.session_state.propriedade.get('latitude', ''))
            lon = st.text_input("Longitude", value=st.session_state.propriedade.get('longitude', ''))
            
            st.caption("Exemplo: -22.9068, -47.0616")
            st.caption(f"🔑 Chave API de mapas configurada: {'✓ Sim' if GOOGLE_MAPS_API_KEY != 'INSERIR_CHAVE_API_AQUI' else '✗ Não configurada'}")
            
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
        st.info("Preencha os dados da análise de solo. Campos com * são recomendados.")
        
        col5, col6 = st.columns(2)
        
        with col5:
            ph = st.number_input("pH (CaCl2 ou água)", min_value=3.0, max_value=8.0, value=float(st.session_state.analise_solo.get('ph', 5.8)), step=0.1)
            materia_organica = st.number_input("Matéria orgânica (%)", min_value=0.0, max_value=10.0, value=float(st.session_state.analise_solo.get('materia_organica', 2.5)), step=0.1)
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
                "Textura do solo",
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
                st.write(f"pH: {valores_padrao['ph']}")
                st.write(f"Matéria orgânica: {valores_padrao['materia_organica']}%")
                st.write(f"Fósforo: {valores_padrao['fosforo']} mg/dm³")
                st.write(f"Potássio: {valores_padrao['potassio']} mg/dm³")
                st.write(f"Cálcio: {valores_padrao['calcio']} cmolc/dm³")
                st.write(f"Magnésio: {valores_padrao['magnesio']} cmolc/dm³")
            with col8:
                st.write("**Outros atributos:**")
                st.write(f"Alumínio: {valores_padrao['aluminio']} cmolc/dm³")
                st.write(f"H + Al: {valores_padrao['h_al']} cmolc/dm³")
                st.write(f"CTC: {valores_padrao['ctc']} cmolc/dm³")
                st.write(f"Sat. bases: {valores_padrao['sb']}%")
                st.write(f"Enxofre: {valores_padrao['enxofre']} mg/dm³")
                st.write(f"Boro: {valores_padrao['boro']} mg/dm³")
                st.write(f"Zinco: {valores_padrao['zinco']} mg/dm³")
                st.write(f"Textura: {valores_padrao['textura']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Salvar dados da propriedade
    st.session_state.propriedade = {
        'nome': nome_prop,
        'proprietario': nome_prop,
        'municipio': municipio,
        'estado': estado,
        'area_irrigada': area_irrigada,
        'area_sequeiro': area_sequeiro,
        'latitude': lat,
        'longitude': lon,
        'manejo': manejo,
        'outro_manejo': outro_manejo if manejo == "Outro" else ''
    }
    
    st.success("✅ Dados da propriedade e análise de solo salvos!")

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
            
            if "Outra" in culturas:
                outra_cultura = st.text_input("Especificar outra cultura", value=st.session_state.plantio.get('outra_cultura', ''))
            
            sistema = st.selectbox(
                "Sistema de cultivo",
                ["Solteiro", "Consorciado"],
                index=0 if st.session_state.plantio.get('sistema', '') == '' else
                      ["Solteiro", "Consorciado"].index(st.session_state.plantio.get('sistema', 'Solteiro'))
            )
            
            if sistema == "Consorciado":
                tipo_consorcio = st.selectbox(
                    "Tipo de consórcio",
                    ["Milho + braquiária", "Soja + braquiária", "Sorgo + braquiária", "Mix de cobertura", "Outro"],
                    index=0 if st.session_state.plantio.get('tipo_consorcio', '') == '' else
                          ["Milho + braquiária", "Soja + braquiária", "Sorgo + braquiária", "Mix de cobertura", "Outro"].index(st.session_state.plantio.get('tipo_consorcio', 'Milho + braquiária'))
                )
                
                if tipo_consorcio == "Outro":
                    outro_consorcio = st.text_input("Especificar consórcio", value=st.session_state.plantio.get('outro_consorcio', ''))
            else:
                tipo_consorcio = None
                outro_consorcio = None
            
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
    
    st.success("✅ Dados do plantio salvos!")

# ===================== ABA 3 - RECOMENDAÇÃO AGRONÔMICA =====================
with tab3:
    st.header("🧪 Recomendação Agronômica")
    
    # Verificar se há dados de análise de solo
    if not st.session_state.analise_solo:
        st.warning("⚠️ Nenhuma análise de solo disponível. Acesse a aba 'Cadastro da Propriedade' para configurar.")
        st.stop()
    
    # Inputs do usuário
    with st.container():
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Informações para Recomendação")
        
        col1, col2 = st.columns(2)
        
        with col1:
            cultura_escolhida = st.selectbox(
                "Cultura que pretende cultivar",
                ["Milho", "Trigo", "Soja", "Feijão", "Sorgo", "Algodão"],
                index=0
            )
            
            unidade_prod = st.selectbox(
                "Unidade de produtividade",
                ["kg/ha", "sacas/ha"],
                index=0
            )
            
            if unidade_prod == "kg/ha":
                produtividade = st.number_input(
                    "Produtividade esperada (kg/ha)", 
                    min_value=100, 
                    max_value=20000, 
                    value=6000 if cultura_escolhida == "Milho" else 3000,
                    step=100
                )
            else:
                # Converter sacas para kg (assumindo 60kg por saca para maioria)
                produtividade_sacas = st.number_input(
                    "Produtividade esperada (sacas/ha)", 
                    min_value=1, 
                    max_value=300, 
                    value=100 if cultura_escolhida == "Milho" else 50,
                    step=1
                )
                produtividade = produtividade_sacas * 60  # kg/ha
        
        with col2:
            ambiente = st.selectbox(
                "Tipo de ambiente",
                ["Irrigado", "Sequeiro"],
                index=0
            )
            
            leguminosa = st.selectbox(
                "Possui palhada ou cultura anterior leguminosa?",
                ["Sim", "Não"],
                index=1
            )
            
            cultura_anterior = st.selectbox(
                "Cultura anterior",
                ["Soja", "Milho", "Braquiária", "Milheto", "Trigo", "Feijão", "Outra"],
                index=0
            )
            
            if cultura_anterior == "Outra":
                outra_cultura_anterior = st.text_input("Especificar cultura anterior")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Botão para gerar recomendação
    if st.button("🔬 Gerar Recomendação", use_container_width=True):
        
        # Obter dados da análise de solo
        analise = st.session_state.analise_solo
        textura = analise.get('textura', 'Média')
        mo = analise.get('materia_organica', 2.5)
        ph = analise.get('ph', 5.8)
        
        # Calcular dose de N
        dose_n = calcular_dose_nitrogenio(
            cultura_escolhida, 
            produtividade, 
            ambiente, 
            cultura_anterior, 
            leguminosa, 
            textura, 
            mo
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
            'qtd_fertilizante': qtd_fertilizante,
            'manejo': manejo,
            'bioinsumos': bio_recomendacao
        }
        
        # Exibir resultados
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # 1. Recomendação de Nitrogênio
        st.markdown('<div class="card card-azul">', unsafe_allow_html=True)
        st.subheader("🧪 1. Recomendação de Nitrogênio")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.metric("Dose estimada de N", f"{dose_n} kg/ha")
            st.metric("Fertilizante recomendado", fertilizante)
            st.metric("Quantidade aproximada", f"{qtd_fertilizante:.1f} kg/ha")
        
        with col4:
            st.write("**Estratégia de manejo:**")
            st.write(f"📌 {manejo['estrategia']}")
            st.write(f"📅 {manejo['parcelamento']}")
            st.info(f"ℹ️ {manejo['observacao']}")
        
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
        
        fig = gerar_grafico_performance(dose_n, cultura_escolhida, produtividade, ambiente)
        st.plotly_chart(fig, use_container_width=True)
        
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
            manejo
        )
        st.markdown(resumo_html, unsafe_allow_html=True)
        
        st.success("✅ Recomendação gerada com sucesso!")

# ===================== ABA 4 - REFERÊNCIAS E METODOLOGIA =====================
with tab4:
    st.header("📚 Referências e Metodologia")
    
    st.markdown("""
    <div class="card">
        <h3>📖 Metodologia de Cálculo</h3>
        <p>O sistema utiliza regras condicionais baseadas em literatura agronômica para estimar recomendações.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card card-azul">
        <h4>🔬 Fórmulas Utilizadas</h4>
        <p><strong>Dose de nitrogênio:</strong></p>
        <p>Dose N = (Fator base da cultura × Produtividade) × Fator_ambiente × Fator_cultura_anterior × Fator_textura × Fator_MO</p>
        <br>
        <p><strong>Quantidade de fertilizante:</strong></p>
        <p>Quantidade (kg/ha) = Dose N recomendada (kg/ha) / Teor de N do fertilizante</p>
        <p><strong>Exemplo:</strong> Ureia possui aproximadamente 45% de N.</p>
        <p>Se a dose recomendada for 120 kg/ha de N:</p>
        <p>120 / 0,45 = 266,7 kg/ha de ureia</p>
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
                </tr>
            </thead>
            <tbody>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Ureia</td><td style="padding: 8px; border: 1px solid #ddd;">45%</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Sulfato de amônio</td><td style="padding: 8px; border: 1px solid #ddd;">20% a 21%</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">Nitrato de amônio</td><td style="padding: 8px; border: 1px solid #ddd;">32% a 34%</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">MAP</td><td style="padding: 8px; border: 1px solid #ddd;">10% a 11%</td></tr>
                <tr><td style="padding: 8px; border: 1px solid #ddd;">DAP</td><td style="padding: 8px; border: 1px solid #ddd;">18%</td></tr>
            </tbody>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card card-warning">
        <h4>⚠️ Limitações do Sistema</h4>
        <ul>
            <li>As recomendações são estimativas educativas, não substituem avaliação técnica profissional.</li>
            <li>Quando não há análise de solo, o sistema utiliza valores médios simulados.</li>
            <li>O gráfico de desempenho é uma projeção didática baseada em incrementos percentuais estimados.</li>
            <li>Para uso real, consulte um engenheiro agrônomo e siga boletins técnicos regionais.</li>
            <li>O sistema não considera todos os fatores de campo (clima, pragas, doenças, etc.).</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="card">
        <h4>📚 Referências Bibliográficas</h4>
        <ul>
            <li>EMBRAPA. Sistemas de produção e recomendações técnicas para culturas anuais.</li>
            <li>RAIJ, B. van et al. Recomendações de adubação e calagem para o Estado de São Paulo. Boletim Técnico 100. IAC.</li>
            <li>MALAVOLTA, E. Manual de nutrição mineral de plantas.</li>
            <li>TAIZ, L. et al. Fisiologia e desenvolvimento vegetal.</li>
            <li>HUNGRIA, M. et al. Estudos sobre inoculação, fixação biológica de nitrogênio e uso de rizobactérias na agricultura.</li>
            <li>DOBBELAERE, S.; VANDERLEYDEN, J.; OKON, Y. Plant growth-promoting effects of diazotrophs.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
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
        <p style="margin-top: 10px; color: #2e7d32;"><strong>Nota:</strong> Todas as recomendações são baseadas em regras agronômicas simplificadas e têm caráter educativo.</p>
    </div>
    """, unsafe_allow_html=True)
