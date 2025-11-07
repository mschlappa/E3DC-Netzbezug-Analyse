import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date
from data_processor import (
    parse_csv_file, 
    save_to_database, 
    get_data_from_database,
    calculate_netzbezug_analysis
)

st.set_page_config(
    page_title="Netzbezug Analyse",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Netzbezug Analyse - Stromverbrauch")

tab1, tab2 = st.tabs(["📤 Daten hochladen", "📊 Auswertung"])

with tab1:
    st.header("CSV-Datei hochladen")
    st.write("Laden Sie Ihre E3DC-Exportdatei hoch. Die Daten werden in der Datenbank gespeichert.")
    
    uploaded_file = st.file_uploader(
        "Wählen Sie eine CSV-Datei aus",
        type=['csv'],
        help="CSV-Datei im E3DC-Format mit Zeitstempel, Direktverbrauch, Batterie Entladen, Netzbezug und Hausverbrauch"
    )
    
    if uploaded_file is not None:
        with st.spinner('Verarbeite CSV-Datei...'):
            df, error = parse_csv_file(uploaded_file)
        
        if error:
            st.error(error)
        else:
            st.success(f"✅ CSV-Datei erfolgreich gelesen: {len(df)} Datensätze")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Zeitraum von", df['zeitstempel'].min().strftime('%d.%m.%Y'))
            with col2:
                st.metric("Zeitraum bis", df['zeitstempel'].max().strftime('%d.%m.%Y'))
            
            with st.expander("Datenvorschau anzeigen"):
                st.dataframe(df.head(20), use_container_width=True)
            
            if st.button("In Datenbank speichern", type="primary"):
                with st.spinner('Speichere Daten in der Datenbank...'):
                    count, save_error = save_to_database(df)
                
                if save_error:
                    st.error(save_error)
                else:
                    st.success(f"✅ {count} Datensätze erfolgreich in der Datenbank gespeichert!")
                    st.info("Die Daten können jetzt im Tab 'Auswertung' analysiert werden.")

with tab2:
    st.header("Netzbezug Auswertung")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "Startdatum",
            value=date(2025, 5, 1),
            help="Wählen Sie das Startdatum für die Auswertung"
        )
    
    with col2:
        end_date = st.date_input(
            "Enddatum",
            value=date(2025, 5, 31),
            help="Wählen Sie das Enddatum für die Auswertung"
        )
    
    if start_date > end_date:
        st.error("⚠️ Das Startdatum muss vor dem Enddatum liegen!")
    else:
        if st.button("Auswertung erstellen", type="primary"):
            with st.spinner('Lade Daten aus der Datenbank...'):
                df_filtered = get_data_from_database(
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=end_date
                )
            
            if df_filtered.empty:
                st.warning("⚠️ Keine Daten für den gewählten Zeitraum gefunden. Bitte laden Sie zuerst Daten hoch.")
            else:
                st.success(f"✅ {len(df_filtered)} Datensätze für den Zeitraum {start_date.strftime('%d.%m.%Y')} bis {end_date.strftime('%d.%m.%Y')} gefunden")
                
                st.subheader("Netzbezug nach Tageszeitintervallen")
                st.write("**0-5 Uhr:** Netzbezug zwischen Mitternacht und 5 Uhr morgens")
                st.write("**5-24 Uhr:** Netzbezug zwischen 5 Uhr morgens und Mitternacht")
                
                analysis = calculate_netzbezug_analysis(df_filtered)
                
                if analysis is not None:
                    st.dataframe(
                        analysis.style.format("{:.0f} W"),
                        use_container_width=True
                    )
                    
                    st.subheader("Visualisierung")
                    
                    analysis_without_total = analysis.iloc[:-1].copy()
                    analysis_without_total = analysis_without_total.reset_index()
                    analysis_without_total['datum'] = pd.to_datetime(analysis_without_total['datum'])
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=analysis_without_total['datum'],
                        y=analysis_without_total['0-5 Uhr'],
                        name='0-5 Uhr',
                        marker_color='#636EFA'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=analysis_without_total['datum'],
                        y=analysis_without_total['5-24 Uhr'],
                        name='5-24 Uhr',
                        marker_color='#EF553B'
                    ))
                    
                    fig.update_layout(
                        barmode='group',
                        title='Netzbezug nach Tageszeitintervallen',
                        xaxis_title='Datum',
                        yaxis_title='Netzbezug (W)',
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.subheader("Gesamtübersicht")
                    
                    total_0_5 = analysis.loc['Gesamt', '0-5 Uhr']
                    total_5_24 = analysis.loc['Gesamt', '5-24 Uhr']
                    total_gesamt = analysis.loc['Gesamt', 'Gesamt']
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Netzbezug 0-5 Uhr", f"{total_0_5:,.0f} W")
                    
                    with col2:
                        st.metric("Netzbezug 5-24 Uhr", f"{total_5_24:,.0f} W")
                    
                    with col3:
                        st.metric("Gesamt Netzbezug", f"{total_gesamt:,.0f} W")
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['0-5 Uhr', '5-24 Uhr'],
                        values=[total_0_5, total_5_24],
                        hole=.3
                    )])
                    
                    fig_pie.update_layout(
                        title='Verteilung Netzbezug nach Tageszeitintervallen',
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)

st.sidebar.header("ℹ️ Informationen")
st.sidebar.write("""
**Über diese App:**

Diese Anwendung analysiert Ihren Stromnetzbezug aus E3DC-Exportdateien.

**Funktionen:**
- CSV-Datei hochladen
- Daten in Datenbank speichern
- Zeitintervall-Filter
- Auswertung nach Tageszeitintervallen:
  - 0-5 Uhr (Nachtzeit)
  - 5-24 Uhr (Tagzeit)
- Visualisierungen und Statistiken

**Datenformat:**
Die CSV-Datei sollte folgende Spalten enthalten:
- Zeitstempel
- Direktverbrauch [W]
- Batterie Entladen [W]
- Netzbezug [W]
- Hausverbrauch [W]
""")
