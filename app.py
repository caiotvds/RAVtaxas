# app.py
# Para executar: pip install streamlit pandas

import streamlit as st
import pandas as pd
from datetime import date, timedelta

# Configuração da página
st.set_page_config(
    page_title="Calculadora de Taxa Efetiva", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado para tabela e tipografia
st.markdown(
    """
    <style>
        /* Tabela */
        .custom-table table {
            width: 70% !important;
            margin: auto;
            font-size: 18px;
            border-collapse: collapse;
        }
        .custom-table th, .custom-table td {
            padding: 10px;
            border: 1px solid #ddd;
            text-align: center;
        }
        /* Cabeçalhos */
        .section-title {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        /* Inputs */
        .stNumberInput label, .stSelectbox label, .stButton label {
            font-weight: 500;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Título principal
st.markdown("# Calculadora de Taxa Efetiva")

# Mapeamento de grupos de parcelamento
method_map = {
    "PIX": 0.0,
    "Débito": 0.0,
    "Crédito 1x": 1.0,
    "Crédito 2-6x": None,
    "Crédito 7-12x": None,
    "Crédito 13-21x": None
}

# Valores default (%) para MDR e antecipação mensal
default_mdr = {
    "PIX": 0.50,
    "Débito": 0.79,
    "Crédito 1x": 1.79,
    "Crédito 2-6x": 2.26,
    "Crédito 7-12x": 2.56,
    "Crédito 13-21x": 2.56
}
default_ant_rate_auto = 1.5

default_ant_rate_spot = 1.5

default_delay_days = 0

# Barra lateral: parâmetros gerais
with st.sidebar:
    st.header("Parâmetros Gerais")
    with st.form(key="params_form"):
        st.subheader("Taxas de MDR (%)")
        mdr_input = {}
        cols = st.columns(2)
        for idx, method in enumerate(method_map.keys()):
            col = cols[idx % 2]
            mdr_input[method] = col.number_input(
                label=method,
                min_value=0.0,
                value=default_mdr[method],
                step=0.01,
                format="%.2f"
            ) / 100
        st.markdown("---")
        ant_rate_auto = st.number_input(
            label="Taxa de Antecipação Automática a.m. (%)",
            min_value=0.0,
            value=default_ant_rate_auto,
            step=0.01,
            format="%.2f"
        ) / 100
        st.markdown("---")
        calc_auto = st.form_submit_button(label="Calcular Automática")

# Abas de conteúdo
tabs = st.tabs(["Antecipação Automática", "Spot"])

# Conteúdo: Antecipação Automática
with tabs[0]:
    st.markdown("<div class='section-title'>Antecipação Automática</div>", unsafe_allow_html=True)
    if calc_auto:
        methods = ["PIX", "Débito"] + [f"Crédito {i}x" for i in range(1, 22)]
        rows = []
        for method in methods:
            # Seleção da taxa MDR de acordo com grupo
            if method.startswith("Crédito"):
                n = int(method.split()[1][:-1])
                if n == 1:
                    rate_mdr = mdr_input["Crédito 1x"]
                elif 2 <= n <= 6:
                    rate_mdr = mdr_input["Crédito 2-6x"]
                elif 7 <= n <= 12:
                    rate_mdr = mdr_input["Crédito 7-12x"]
                else:
                    rate_mdr = mdr_input["Crédito 13-21x"]
                avg_months = (n + 1) / 2
            else:
                rate_mdr = mdr_input[method]
                avg_months = 0
            # Cálculo de antecipação efetiva e taxa total
            ant_eff = ((1 + ant_rate_auto) ** avg_months - 1) if avg_months > 0 else 0
            total_rate = rate_mdr + ant_eff
            rows.append({
                "Método": method,
                "MDR (%)": f"{rate_mdr*100:.2f}",
                "Antecipação Efetiva (%)": f"{ant_eff*100:.2f}",
                "Taxa Efetiva (%)": f"{total_rate*100:.2f}"
            })
        df_auto = pd.DataFrame(rows)
        st.markdown('<div class="custom-table">' + df_auto.to_html(index=False) + '</div>', unsafe_allow_html=True)
    else:
        st.info("Ajuste parâmetros na lateral e clique em **Calcular Automática**.")

# Conteúdo: Spot
with tabs[1]:
    st.markdown("<div class='section-title'>Simulação Spot</div>", unsafe_allow_html=True)
    # Inputs na aba (não sidebar)
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        value = st.number_input(
            "Valor da Transação (R$)",
            min_value=0.0,
            value=1000.00,
            step=0.01,
            format="%.2f"
        )
    with col2:
        parcelas = st.selectbox(
            "Parcelas",
            options=list(range(1, 22)),
            index=0
        )
    with col3:
        ant_rate_spot = st.number_input(
            "Antecipação Spot a.m. (%)",
            min_value=0.0,
            value=default_ant_rate_spot,
            step=0.01,
            format="%.2f"
        ) / 100
    with col4:
        delay_days = st.number_input(
            "Dias até Pedido de Antecipação",
            min_value=0,
            value=default_delay_days,
            step=1
        )

    gerar_spot = st.button("Gerar Agenda Spot")

    if gerar_spot:
        hoje = date.today()
        data = []
        total_face = 0
        total_net = 0
        for i in range(1, parcelas + 1):
            venc = hoje + timedelta(days=30 * i)
            original_dc = (venc - hoje).days
            dc_remaining = max(0, original_dc - delay_days)
            face = value / parcelas
            total_face += face
            # MDR por parcela
            if parcelas == 1:
                rate_mdr = mdr_input["Crédito 1x"]
            elif 2 <= parcelas <= 6:
                rate_mdr = mdr_input["Crédito 2-6x"]
            elif 7 <= parcelas <= 12:
                rate_mdr = mdr_input["Crédito 7-12x"]
            else:
                rate_mdr = mdr_input["Crédito 13-21x"]
            # Antecipação efetiva por dias restantes
            ant_eff_spot = (1 + ant_rate_spot) ** (dc_remaining / 30) - 1
            total_rate = rate_mdr + ant_eff_spot
            net = face * (1 - total_rate)
            total_net += net
            data.append({
                "Parcela": i,
                "Face (R$)": f"{face:.2f}",
                "Vencimento": venc.isoformat(),
                "DC Original": original_dc,
                "DC Restantes": dc_remaining,
                "MDR (%)": f"{rate_mdr*100:.2f}",
                "Antecipação (%)": f"{ant_eff_spot*100:.2f}",
                "Total (%)": f"{total_rate*100:.2f}"
            })
        df_spot = pd.DataFrame(data)
        # Exibir tabela
        st.markdown('<div class="custom-table">' + df_spot.to_html(index=False) + '</div>', unsafe_allow_html=True)
        # Taxa efetiva consolidada
        eff_total = (total_face - total_net) / total_face if total_face else 0
        st.markdown(f"**Taxa Efetiva Consolidada (%):** {eff_total*100:.2f}")
    else:
        st.info("Insira valor, parcelas, taxa de antecipação, dias até pedido e clique em **Gerar Agenda Spot**.")
