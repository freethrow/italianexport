import os
import streamlit as st
import pandas as pd
import comtradeapicall
import plotly.graph_objects as go
from datetime import datetime
import time

from dotenv import load_dotenv

# load API key
load_dotenv()
API_KEY = os.getenv("API_KEY")

# Define sectors dictionary
sectors = {
    "84": "Macchinari e apparecchi meccanici",
    "85": "Macchinari e apparecchiature elettriche",
    "87": "Veicoli",
    "39": "Materie plastiche",
    "73": "Articoli in ferro e acciaio",
    "94": "Mobili",
    "64": "Calzature",
    "42": "Articoli in pelle",
    "69": "Prodotti ceramici",
    "33": "Profumeria e cosmetici",
    "71": "Pietre e metalli preziosi",
    "62": "Abbigliamento",
    "30": "Prodotti farmaceutici",
    "88": "Aeromobili e parti",
    "22": "Bevande alcoliche e spiriti",
    "70": "Vetro e articoli in vetro",
    "9004": "Occhiali e dispositivi simili",
    "9003": "Montature per occhiali",
    "9001": "Fibre ottiche, lenti e prismi",
    "68": "Articoli in pietra, gesso, cemento",
    "49": "Libri e giornali stampati",
    "19": "Preparazioni di cereali, pasticceria, pane",
    "20": "Preparazioni di ortaggi e frutta",
    "61": "Abbigliamento a maglia",
    "9506": "Attrezzature sportive e per il fitness",
    "89": "Navi, imbarcazioni e strutture galleggianti",
    "8432": "Macchine agricole per la preparazione del terreno",
    "8433": "Macchine per la raccolta e la trebbiatura",
    "8438": "Macchinari per l'industria alimentare",
}


@st.cache_data
def get_trade_data(year, sector_code):
    """
    Recupera i dati commerciali per un anno e settore specifico
    """
    try:
        df = comtradeapicall.getFinalData(
            API_KEY,
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=str(year),
            reporterCode=None,
            cmdCode=sector_code,
            flowCode="X",
            partnerCode="0",
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=500,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )

        if df is not None and not df.empty:
            simplified_df = df[["reporterCode", "reporterDesc", "primaryValue"]].copy()
            simplified_df.columns = ["Codice Paese", "Paese", "Esportazioni (USD)"]
            simplified_df["Codice Paese"] = pd.to_numeric(simplified_df["Codice Paese"])
            simplified_df = simplified_df.sort_values(
                "Esportazioni (USD)", ascending=False
            ).reset_index(drop=True)
            return simplified_df
        return None
    except Exception as e:
        st.error(f"Errore nel recupero dei dati: {str(e)}")
        return None


def create_top_10_chart(df, sector_name):
    """
    Crea un grafico a barre dei primi 10 esportatori con l'Italia evidenziata
    """
    top_10 = df.head(10).copy()

    # Converti valori in milioni e calcola quota di mercato
    top_10["Esportazioni (Milioni USD)"] = top_10["Esportazioni (USD)"] / 1_000_000
    total_value = df["Esportazioni (USD)"].sum()
    top_10["Quota di Mercato"] = (top_10["Esportazioni (USD)"] / total_value) * 100

    # Crea etichette con valore e quota di mercato
    text_labels = [
        f'<b>${value:,.0f}M</b><br><span style="color: gray;">─────</span><br><span style="font-family: Arial; font-weight: normal;">{share:.1f}%</span>'
        for value, share in zip(
            top_10["Esportazioni (Milioni USD)"], top_10["Quota di Mercato"]
        )
    ]

    # Trova la posizione dell'Italia
    italy_data = df[df["Codice Paese"] == 380]
    italy_position = (
        df.index[df["Codice Paese"] == 380][0] + 1 if not italy_data.empty else None
    )

    # Crea array di colori (blu per gli altri, rosso per l'Italia)
    colors = ["rgb(49, 130, 189)"] * 10
    if not italy_data.empty and italy_position <= 10:
        colors[italy_position - 1] = "rgb(204, 0, 0)"

    fig = go.Figure()

    # Aggiungi barre
    fig.add_trace(
        go.Bar(
            x=top_10["Paese"],
            y=top_10["Esportazioni (Milioni USD)"],
            marker_color=colors,
            text=text_labels,
            textposition="auto",
            textfont=dict(size=16, family="Arial Black"),
            marker=dict(line_width=0, cornerradius=8),
            textangle=0,
            insidetextanchor="middle",
        )
    )

    # Aggiorna layout
    fig.update_layout(
        title=f"Top 10 Esportatori - {sector_name}",
        xaxis_title="Paese",
        yaxis_title="Esportazioni (Milioni USD)",
        showlegend=False,
        height=600,
        bargap=0.2,
        margin=dict(t=100, b=100),
    )

    return fig, italy_position


def create_position_trend_chart(historical_df, sector_name):
    """
    Crea un grafico dell'andamento della posizione dell'Italia nel tempo
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=historical_df["Anno"],
            y=historical_df["Posizione"],
            name="Posizione",
            line=dict(color="red", width=3),
            mode="lines+markers",
            marker=dict(size=10),
        )
    )

    fig.update_layout(
        title=dict(
            text="Posizione<br>Competitiva Italia",
            y=0.95,
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(size=14),
        ),
        xaxis=dict(title="Anno", dtick=1),
        yaxis=dict(
            title="Ranking Globale",
            autorange="reversed",
            tickmode="linear",
            dtick=1,
            range=[historical_df["Posizione"].max() + 1, 0],
        ),
        height=350,
        showlegend=False,
        margin=dict(t=60),
    )

    return fig


def create_value_trend_chart(historical_df, sector_name):
    """
    Crea un grafico dell'andamento del valore delle esportazioni dell'Italia
    """
    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=historical_df["Anno"],
            y=historical_df["Valore"],
            name="Valore Esportazioni",
            line=dict(color="blue", width=3, shape="spline"),
            mode="lines+markers",
            marker=dict(size=8),
        )
    )

    fig.update_layout(
        title=dict(
            text="Trend del<br>Valore Esportato",
            y=0.95,
            x=0.5,
            xanchor="center",
            yanchor="top",
            font=dict(size=14),
        ),
        xaxis=dict(title="Anno", dtick=1),
        yaxis=dict(title="Esportazioni (Milioni USD)", tickformat=",.0f"),
        height=350,
        showlegend=False,
        margin=dict(t=60),
    )

    return fig


@st.cache_data
def get_historical_data(sector_code, end_year, years=5):
    """
    Recupera i dati storici per la posizione dell'Italia
    """
    historical_data = []

    for year in range(end_year - years + 1, end_year + 1):
        try:
            df = get_trade_data(year, sector_code)
            if df is not None:
                italy_data = df[df["Codice Paese"] == 380]
                if not italy_data.empty:
                    position = df.index[df["Codice Paese"] == 380][0] + 1
                    value = italy_data["Esportazioni (USD)"].iloc[0] / 1_000_000
                    historical_data.append(
                        {"Anno": year, "Posizione": position, "Valore": value}
                    )
                time.sleep(1)
        except Exception as e:
            st.warning(f"Impossibile recuperare i dati per l'anno {year}: {str(e)}")

    return pd.DataFrame(historical_data)


def main():
    st.title("Analisi del Commercio Internazionale")
    st.write("Analisi dei principali esportatori per settore con focus sull'Italia")

    # Citazione fonte dati
    st.markdown(
        """
        <div style='font-size: 0.75em; color: #808080; margin: 1em 0; line-height: 1.5;'>
            Fonte dati: United Nations Comtrade Database (UN Comtrade)<br>
            Dati estratti da <a href="https://comtradeplus.un.org" style="color: #808080; text-decoration: none;">https://comtradeplus.un.org</a>
            <br><br>
            Elaborazione dati: Antonio Ventresca e <a href="https://github.com/freethrow" style="color: #808080; text-decoration: none; border-bottom: 1px dotted #808080;">Marko Aleksendrić</a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Controlli sidebar
    st.sidebar.header("Impostazioni")
    selected_year = st.sidebar.selectbox(
        "Seleziona Anno", range(datetime.now().year - 1, 2017, -1)
    )

    selected_sector = st.sidebar.selectbox(
        "Seleziona Settore",
        options=list(sectors.keys()),
        format_func=lambda x: f"{sectors[x]} ({x})",
    )

    # Contenuto principale
    if st.button("Analizza Settore"):
        with st.spinner("Caricamento dati in corso..."):
            df = get_trade_data(selected_year, selected_sector)

            if df is not None:
                fig_current, italy_position = create_top_10_chart(
                    df, sectors[selected_sector]
                )
                st.plotly_chart(fig_current, use_container_width=True)

                with st.spinner("Caricamento dati storici..."):
                    historical_df = get_historical_data(selected_sector, selected_year)
                    if not historical_df.empty:
                        col1, col2 = st.columns(2)
                        with col1:
                            fig_position = create_position_trend_chart(
                                historical_df, sectors[selected_sector]
                            )
                            st.plotly_chart(fig_position, use_container_width=True)

                        with col2:
                            fig_value = create_value_trend_chart(
                                historical_df, sectors[selected_sector]
                            )
                            st.plotly_chart(fig_value, use_container_width=True)


if __name__ == "__main__":
    main()
