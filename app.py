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
from pdf_export import create_pdf_report

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
    
    st.subheader("Strompreise")
    col3, col4 = st.columns(2)
    
    with col3:
        preis_0_5 = st.number_input(
            "Strompreis 0-5 Uhr (Cent/kWh)",
            min_value=0.0,
            max_value=100.0,
            value=14.85,
            step=0.01,
            help="Strompreis im Tageszeitintervall 0-5 Uhr in Cent pro kWh"
        )
    
    with col4:
        preis_5_24 = st.number_input(
            "Strompreis 6-23 Uhr (Cent/kWh)",
            min_value=0.0,
            max_value=100.0,
            value=25.85,
            step=0.01,
            help="Strompreis im Tageszeitintervall 6-23 Uhr in Cent pro kWh"
        )
    
    if start_date > end_date:
        st.error("⚠️ Das Startdatum muss vor dem Enddatum liegen!")
    else:
        if st.button("Auswertung erstellen", type="primary"):
            pdf_key = f"pdf_{start_date}_{end_date}_{preis_0_5}_{preis_5_24}"
            if pdf_key in st.session_state:
                del st.session_state[pdf_key]
            
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
                st.write("**6-23 Uhr:** Netzbezug zwischen 6 Uhr morgens und Mitternacht")
                
                analysis = calculate_netzbezug_analysis(df_filtered)
                
                if analysis is not None:
                    st.subheader("Netzbezug in kWh")
                    st.dataframe(
                        analysis.style.format("{:.2f} kWh"),
                        use_container_width=True
                    )
                    
                    total_0_5 = analysis.loc['Gesamt', '0-5 Uhr']
                    total_5_24 = analysis.loc['Gesamt', '6-23 Uhr']
                    total_gesamt = analysis.loc['Gesamt', 'Gesamt']
                    
                    kosten_0_5 = (total_0_5 * preis_0_5) / 100
                    kosten_5_24 = (total_5_24 * preis_5_24) / 100
                    kosten_gesamt = kosten_0_5 + kosten_5_24
                    
                    st.subheader("Gesamtübersicht")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Netzbezug 0-5 Uhr", f"{total_0_5:,.2f} kWh")
                        st.metric("Kosten 0-5 Uhr", f"{kosten_0_5:,.2f} €")
                    
                    with col2:
                        st.metric("Netzbezug 6-23 Uhr", f"{total_5_24:,.2f} kWh")
                        st.metric("Kosten 6-23 Uhr", f"{kosten_5_24:,.2f} €")
                    
                    with col3:
                        st.metric("Gesamt Netzbezug", f"{total_gesamt:,.2f} kWh")
                        st.metric("Gesamtkosten", f"{kosten_gesamt:,.2f} €")
                    
                    st.subheader("Visualisierung Netzbezug")
                    
                    analysis_without_total = analysis.iloc[:-1].copy()
                    
                    fig = go.Figure()
                    
                    fig.add_trace(go.Bar(
                        x=analysis_without_total.index,
                        y=analysis_without_total['0-5 Uhr'],
                        name='0-5 Uhr',
                        marker_color='#636EFA'
                    ))
                    
                    fig.add_trace(go.Bar(
                        x=analysis_without_total.index,
                        y=analysis_without_total['6-23 Uhr'],
                        name='6-23 Uhr',
                        marker_color='#EF553B'
                    ))
                    
                    fig.update_layout(
                        barmode='group',
                        title='Netzbezug nach Tageszeitintervallen',
                        xaxis_title='Datum',
                        yaxis_title='Netzbezug (kWh)',
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    fig_pie = go.Figure(data=[go.Pie(
                        labels=['0-5 Uhr', '6-23 Uhr'],
                        values=[total_0_5, total_5_24],
                        hole=.3
                    )])
                    
                    fig_pie.update_layout(
                        title='Verteilung Netzbezug nach Tageszeitintervallen (kWh)',
                        height=400
                    )
                    
                    st.plotly_chart(fig_pie, use_container_width=True)
                    
                    st.subheader("Visualisierung Kosten")
                    
                    fig_kosten = go.Figure(data=[go.Bar(
                        x=['0-5 Uhr', '6-23 Uhr', 'Gesamt'],
                        y=[kosten_0_5, kosten_5_24, kosten_gesamt],
                        marker_color=['#636EFA', '#EF553B', '#00CC96'],
                        text=[f"{kosten_0_5:.2f} €", f"{kosten_5_24:.2f} €", f"{kosten_gesamt:.2f} €"],
                        textposition='auto'
                    )])
                    
                    fig_kosten.update_layout(
                        title='Stromkosten nach Tageszeitintervallen',
                        xaxis_title='Zeitintervall',
                        yaxis_title='Kosten (€)',
                        height=400
                    )
                    
                    st.plotly_chart(fig_kosten, use_container_width=True)
                    
                    st.divider()
                    
                    st.subheader("📥 PDF-Export")
                    st.write("Laden Sie die komplette Auswertung als PDF-Dokument herunter.")
                    
                    pdf_key = f"pdf_{start_date}_{end_date}_{preis_0_5}_{preis_5_24}"
                    
                    if pdf_key not in st.session_state:
                        try:
                            with st.spinner('Erstelle PDF-Dokument...'):
                                pdf_bytes = create_pdf_report(
                                    analysis_df=analysis.iloc[:-1],
                                    total_0_5=total_0_5,
                                    total_5_24=total_5_24,
                                    total_gesamt=total_gesamt,
                                    kosten_0_5=kosten_0_5,
                                    kosten_5_24=kosten_5_24,
                                    kosten_gesamt=kosten_gesamt,
                                    preis_0_5=preis_0_5,
                                    preis_5_24=preis_5_24,
                                    start_date=start_date,
                                    end_date=end_date,
                                    fig_bar=fig,
                                    fig_pie=fig_pie,
                                    fig_kosten=fig_kosten
                                )
                                st.session_state[pdf_key] = pdf_bytes
                                st.success("✅ PDF wurde erstellt!")
                        except Exception as e:
                            st.error(f"❌ Fehler beim Erstellen des PDFs: {str(e)}")
                            st.session_state[pdf_key] = None
                    
                    if st.session_state.get(pdf_key):
                        filename = f"Netzbezug_Auswertung_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.pdf"
                        
                        st.download_button(
                            label="📄 PDF herunterladen",
                            data=st.session_state[pdf_key],
                            file_name=filename,
                            mime="application/pdf",
                            type="primary"
                        )

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
  - 6-23 Uhr (Tagzeit)
- Anzeige in kWh (Kilowattstunden)
- Strompreis-Kalkulation
- Kostenberechnung in Euro
- Visualisierungen und Statistiken

**Datenformat:**
Die CSV-Datei sollte folgende Spalten enthalten:
- Zeitstempel
- Direktverbrauch [W]
- Batterie Entladen [W]
- Netzbezug [W]
- Hausverbrauch [W]

**Hinweis:**
Die Werte in der CSV sind in Watt (W) pro Stunde angegeben und werden automatisch in Kilowattstunden (kWh) umgerechnet.
""")
