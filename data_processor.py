import pandas as pd
from datetime import datetime
from sqlalchemy import delete
from database import EnergyData, get_session

def parse_csv_file(uploaded_file):
    try:
        df = pd.read_csv(
            uploaded_file, 
            sep=';', 
            encoding='utf-8-sig',
            quotechar='"',
            decimal=','
        )
        
        df.columns = df.columns.str.strip()
        
        column_mapping = {
            'Zeitstempel': 'zeitstempel',
            'Direktverbrauch [W]': 'direktverbrauch',
            'Batterie Entladen [W]': 'batterie_entladen',
            'Netzbezug [W]': 'netzbezug',
            'Hausverbrauch [W]': 'hausverbrauch'
        }
        
        df = df.rename(columns=column_mapping)
        
        df['zeitstempel'] = pd.to_datetime(df['zeitstempel'], format='%d.%m.%Y %H:%M:%S')
        
        for col in ['direktverbrauch', 'batterie_entladen', 'netzbezug', 'hausverbrauch']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        nan_counts = df[['direktverbrauch', 'batterie_entladen', 'netzbezug', 'hausverbrauch']].isna().sum()
        if nan_counts['netzbezug'] > len(df) * 0.5:
            return None, "Fehler: Die meisten Netzbezug-Werte konnten nicht gelesen werden. Bitte überprüfen Sie das Dateiformat."
        
        return df, None
        
    except Exception as e:
        return None, f"Fehler beim Verarbeiten der CSV-Datei: {str(e)}"

def save_to_database(df):
    session = get_session()
    try:
        timestamps = df['zeitstempel'].tolist()
        
        session.query(EnergyData).filter(
            EnergyData.zeitstempel.in_(timestamps)
        ).delete(synchronize_session=False)
        
        records = df.to_dict('records')
        for record in records:
            energy_record = EnergyData(**record)
            session.add(energy_record)
        
        session.commit()
        return len(records), None
        
    except Exception as e:
        session.rollback()
        return 0, f"Fehler beim Speichern in der Datenbank: {str(e)}"
        
    finally:
        session.close()

def get_data_from_database(start_date=None, end_date=None):
    session = get_session()
    try:
        query = session.query(EnergyData)
        
        if start_date:
            query = query.filter(EnergyData.zeitstempel >= start_date)
        
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())
            query = query.filter(EnergyData.zeitstempel <= end_datetime)
        
        query = query.order_by(EnergyData.zeitstempel)
        
        results = query.all()
        
        data = [{
            'zeitstempel': r.zeitstempel,
            'direktverbrauch': r.direktverbrauch,
            'batterie_entladen': r.batterie_entladen,
            'netzbezug': r.netzbezug,
            'hausverbrauch': r.hausverbrauch
        } for r in results]
        
        return pd.DataFrame(data)
        
    finally:
        session.close()

def calculate_netzbezug_analysis(df):
    if df.empty:
        return None
    
    df_copy = df.copy()
    df_copy['stunde'] = df_copy['zeitstempel'].dt.hour
    df_copy['datum'] = df_copy['zeitstempel'].dt.date
    
    df_copy['netzbezug_kwh'] = df_copy['netzbezug'] / 1000
    
    df_copy['zeitintervall'] = df_copy['stunde'].apply(
        lambda x: '0-5 Uhr' if 1 <= x <= 5 else '5-24 Uhr'
    )
    
    summary = df_copy.groupby(['datum', 'zeitintervall'])['netzbezug_kwh'].sum().reset_index()
    
    pivot_table = summary.pivot(index='datum', columns='zeitintervall', values='netzbezug_kwh').fillna(0)
    pivot_table.index.name = 'datum'
    
    if '0-5 Uhr' not in pivot_table.columns:
        pivot_table['0-5 Uhr'] = 0
    if '5-24 Uhr' not in pivot_table.columns:
        pivot_table['5-24 Uhr'] = 0
    
    pivot_table = pivot_table[['0-5 Uhr', '5-24 Uhr']]
    
    pivot_table['Gesamt'] = pivot_table['0-5 Uhr'] + pivot_table['5-24 Uhr']
    
    total_row = pd.DataFrame({
        '0-5 Uhr': [pivot_table['0-5 Uhr'].sum()],
        '5-24 Uhr': [pivot_table['5-24 Uhr'].sum()],
        'Gesamt': [pivot_table['Gesamt'].sum()]
    }, index=['Gesamt'])
    
    pivot_table = pd.concat([pivot_table, total_row])
    
    return pivot_table
