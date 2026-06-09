import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os

st.set_page_config(page_title="Ekonomi Makro Daerah", layout="wide", page_icon="📍")

# ==============================================================================
# Bagian 1: SMART DATA LOADER (Prioritas Utama: File Excel .xlsx)
# ==============================================================================
@st.cache_data
def smart_load(filename_base):
    """Mencari file dengan prioritas .xlsx, kemudian fallback ke .csv"""
    formats = ['.xlsx', '.csv']
    folders = ['', 'data/']
    
    for fldr in folders:
        for fmt in formats:
            path = f"{fldr}{filename_base}{fmt}"
            if os.path.exists(path):
                try:
                    if fmt == '.xlsx':
                        # Eksekusi prioritas untuk Excel
                        df = pd.read_excel(path, engine='openpyxl')
                    else:
                        # Fallback jika masih memakai CSV
                        try:
                            df = pd.read_csv(path, sep=";", engine='python')
                            if len(df.columns) < 2: 
                                df = pd.read_csv(path, sep=",", engine='python')
                        except:
                            df = pd.read_csv(path, sep=",", engine='python')
                    
                    # Bersihkan nama kolom (hilangkan spasi berlebih dan jadikan huruf kecil)
                    df.columns = df.columns.astype(str).str.strip().str.lower()
                    return df
                except Exception as e:
                    st.error(f"Gagal membaca file {path}: {e}")
                    return pd.DataFrame()
                    
    return pd.DataFrame() # Return DF kosong jika file tidak ditemukan sama sekali

def load_data_aman(provinsi, tahun):
    df_all = smart_load("data_ekonomi")
    if df_all is None or df_all.empty:
        return pd.DataFrame(columns=['provinsi', 'tahun', 'klasifikasi', 'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc'])

    try:
        df_all['provinsi'] = df_all['provinsi'].astype(str).str.strip()
        df_all['tahun'] = pd.to_numeric(df_all['tahun'], errors='coerce').fillna(0).astype(int)
        
        # Kolom ini diamankan secara spesifik agar bisa membaca angka desimal Excel maupun teks ber-koma
        kolom_angka = [
            'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc', 
            'kontribusi', 'pdrb_perkapita', 'inflasi', 'pma', 'pmdn', 
            'ipm', 'kemiskinan', 'tpt', 'gini'
        ]
        
        for kol in kolom_angka:
            if kol in df_all.columns:
                df_all[kol] = df_all[kol].astype(str).str.strip().replace(['-', '', 'nan', 'None'], np.nan)
                df_all[kol] = df_all[kol].str.replace(',', '.', regex=False)
                df_all[kol] = pd.to_numeric(df_all[kol], errors='coerce')
        
        df_filtered = df_all[df_all['tahun'] == int(tahun)]
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_all.columns)
            
    except Exception as e:
        return pd.DataFrame(columns=['provinsi', 'tahun', 'klasifikasi', 'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc'])

def load_data_sektoral_aman(provinsi):
    df_sektoral = smart_load("data_sektoral")
    if df_sektoral is None or df_sektoral.empty: return pd.DataFrame()
    try:
        df_sektoral['provinsi'] = df_sektoral['provinsi'].astype(str).str.strip()
        df_filtered = df_sektoral[df_sektoral['provinsi'] == str(provinsi).strip()]
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_sektoral.columns)
    except:
        return pd.DataFrame()

def load_data_struktur_aman(provinsi):
    df_all = smart_load("data_struktur")
    if df_all is None or df_all.empty: return pd.DataFrame()
    try:
        df_all['provinsi'] = df_all['provinsi'].astype(str).str.strip()
        df_filtered = df_all[df_all['provinsi'] == str(provinsi).strip()]
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_all.columns)
    except:
        return pd.DataFrame()

# ==============================================================================
# Bagian 2: VISUALISASI CHART & PETA
# ==============================================================================
WARNA_SEKTOR_GLOBAL = {
    "pertanian": "#22C55E", "pertambangan": "#D97706", "industri": "#6B21A8",
    "pengadaan listrik": "#EA580C", "pengadaan air": "#1E3A1E", "konstruksi": "#8B5CF6",
    "perdagangan": "#1D4ED8", "transportasi": "#FBBF24", "akmamin": "#F472B6",
    "informasi dan komunikasi": "#3B82F6", "jasa keuangan": "#EC4899", "real estat": "#6B7280",
    "jasa perusahaan": "#9CA3AF", "adm. pemerintahan": "#DC2626", "jasa pendidikan": "#0D9488",
    "jasa kesehatan": "#78350F", "jasa lainnya": "#D97706"
}

def get_warna_sektor_map(df_column):
    return {sektor: WARNA_SEKTOR_GLOBAL.get(str(sektor).lower(), "#6B7280") for sektor in df_column.unique()}

def buat_bar_chart_makro(df_aktif, tipe_chart):
    if df_aktif is None or df_aktif.empty:
        st.warning("Data makro untuk grafik batang kosong.")
        return

    if tipe_chart == "Pertumbuhan Ekonomi":
        if "lpe_ctc" not in df_aktif.columns: return st.warning("Kolom lpe_ctc tidak ditemukan.")
        df_sorted = df_aktif.dropna(subset=["lpe_ctc"]).sort_values(by="lpe_ctc", ascending=True)
        fig = px.bar(df_sorted, x="lpe_ctc", y="provinsi", labels={"lpe_ctc": "LPE c-to-c (%)", "provinsi": "Provinsi"}, color="lpe_ctc", color_continuous_scale="Viridis")
    else:
        if "kontribusi" not in df_aktif.columns: return st.warning("Kolom kontribusi tidak ditemukan.")
        df_sorted = df_aktif.dropna(subset=["kontribusi"]).sort_values(by="kontribusi", ascending=True)
        fig = px.bar(df_sorted, x="kontribusi", y="provinsi", labels={"kontribusi": "Kontribusi PDRB (%)", "provinsi": "Provinsi"}, color="kontribusi", color_continuous_scale="Cividis")
        
    fig.update_layout(height=600, margin={"r":10,"t":10,"l":10,"b":10})
    st.plotly_chart(fig, use_container_width=True)

def buat_peta_klasifikasi(df_aktif):
    if df_aktif is None or df_aktif.empty or "klasifikasi" not in df_aktif.columns:
        st.warning("Data kosong atau kolom klasifikasi tidak ditemukan, peta tidak dapat dimuat.")
        return
        
    try:
        geojson_path = "data/indonesia_provinces.geojson" if os.path.exists("data/indonesia_provinces.geojson") else "indonesia_provinces.geojson"
        if not os.path.exists(geojson_path):
            st.info("🗺️ *[File GeoJSON batas wilayah tidak ditemukan. Peta Spasial belum bisa dimuat.]*")
            return
        with open(geojson_path, "r") as f:
            geojson_indonesia = json.load(f)
            
        fig = px.choropleth_mapbox(
            df_aktif, geojson=geojson_indonesia, locations="provinsi", featureidkey="properties.PROVINSI", color="klasifikasi",                 
            color_discrete_map={                
                "Daerah Maju dan Cepat Tumbuh": "#0D415C",  
                "Daerah Berkembang Cepat": "#13BA8E",       
                "Daerah Maju tapi Tertekan": "#A7E048",    
                "Daerah Relatif Tertinggal": "#D9DADB"      
            },
            mapbox_style="carto-positron", center={"lat": -2.5, "lon": 118.0}, zoom=3.5, opacity=0.8, labels={"klasifikasi": "Status Klasifikasi"}
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.info(f"🗺️ *[Gagal memuat peta GeoJSON. Error: {e}]*")

def buat_line_growth(provinsi):
    df_raw = smart_load("data_ekonomi")
    if df_raw is None or df_raw.empty: return
    try:
        df_raw['provinsi'] = df_raw['provinsi'].astype(str).str.strip()
        df_prov = df_raw[df_raw['provinsi'] == provinsi].sort_values(by="tahun")
        
        if df_prov.empty:
            st.warning(f"Data tren historis untuk {provinsi} tidak ditemukan.")
            return
            
        df_prov['lpe_ctc'] = pd.to_numeric(df_prov['lpe_ctc'].astype(str).str.replace(',', '.', regex=False).str.strip().replace('-', np.nan), errors='coerce')
        df_prov['inflasi'] = pd.to_numeric(df_prov['inflasi'].astype(str).str.replace(',', '.', regex=False).str.strip().replace('-', np.nan), errors='coerce')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_prov['tahun'], y=df_prov['lpe_ctc'], name=f"{provinsi} (c-to-c)", mode='lines+markers', line=dict(width=3, color='#1D4ED8')))
        fig.add_trace(go.Scatter(x=df_prov['tahun'], y=df_prov['inflasi'], name='Inflasi Wilayah', mode='lines+markers', line=dict(dash='dash', color='#DC2626')))
        
        fig.update_layout(xaxis=dict(dtick=1, type='category'), xaxis_title="Tahun", yaxis_title="Persentase (%)", margin={"r":10,"t":30,"l":10,"b":10}, legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Gagal memuat tren pertumbuhan makro historis: {e}")

def buat_area_struktur(df_aktif):
    if df_aktif is not None and not df_aktif.empty and 'sektor' in df_aktif.columns and 'kontribusi_sektor' in df_aktif.columns:
        df_display = df_aktif.sort_values(by="tahun")
        warna_map = get_warna_sektor_map(df_display['sektor'])
        
        fig = px.area(
            df_display, x="tahun", y="kontribusi_sektor", color="sektor", line_group="sektor", color_discrete_map=warna_map,
            labels={"tahun": "Tahun Analisis", "kontribusi_sektor": "Kontribusi Sektor PDRB (%)"}
        )
        fig.update_layout(showlegend=True, xaxis=dict(dtick=1, type='category'), margin={"r": 10, "t": 10, "l": 10, "b": 10})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 *[Grafik Tren Area Struktur Ekonomi belum dapat dimuat karena data kosong]*")

def buat_scatter_sektoral(df_aktif, jenis_analisis):
    if df_aktif is None or df_aktif.empty:
        st.info(f"🎯 *[Grafik Scatter Plot {jenis_analisis} akan muncul otomatis setelah data sektoral provinsi termuat]*")
        return

    if jenis_analisis == "Overlay":
        judul_full = 'Scatter Plot "Overlay (MRP - LQ) 2025"'
        help_teks = "Metode Overlay..."
        kriteria_teks = "- Kriteria I (Rasio Pertumbuhan > 1 dan LQ > 1): Sektor Unggulan...\n"
        col_x, col_y = "lq_2025", "rps_2025"
        garis_x, garis_y = 1.0, 1.0  
        labels_x, labels_y = "Location Quotient (LQ)", "Rasio Pertumbuhan Sektoral (RPS)"

    elif jenis_analisis == "Shift Share":
        judul_full = 'Scatter Plot "Shift Share 2015/2025"'
        help_teks = "Metode Shift Share..."
        kriteria_teks = "- Kriteria I (RS + IM +): Sektor Tumbuh Pesat...\n"
        col_x, col_y = "im_2025", "rs_2025"
        garis_x, garis_y = 0.0, 0.0  
        labels_x, labels_y = "Regional Share (RS)", "Industrial Mix (IM)"

    else:  
        judul_full = 'Scatter Plot "Tipologi Klassen Rata-Rata 2022-2025"'
        help_teks = "Tipologi Klassen..."
        kriteria_teks = "- Kriteria I (Pertumbuhan > Nas & Kontribusi > Nas): Sektor Andalan...\n"
        col_x, col_y = "kontribusi_2025", "pertumbuhan_2025"
        garis_x, garis_y = 5.6, 5.1  
        labels_x, labels_y = "Rata-Rata Kontribusi (%)", "Rata-Rata Pertumbuhan (%)"

    if col_x not in df_aktif.columns or col_y not in df_aktif.columns:
        return st.warning(f"Kolom {col_x} atau {col_y} tidak ditemukan pada data sektoral.")

    st.markdown(f"##### {judul_full}", help=help_teks)
    col_grafik, col_narasi = st.columns([2, 1])
    
    with col_grafik:
        warna_map = get_warna_sektor_map(df_aktif.get('sektor', pd.Series(dtype=str)))
        fig = px.scatter(
            df_aktif, x=col_x, y=col_y, text="sektor" if "sektor" in df_aktif.columns else None,        
            color="sektor" if "sektor" in df_aktif.columns else None,        
            labels={col_x: labels_x, col_y: labels_y}, color_discrete_map=warna_map  
        )
        fig.add_hline(y=garis_y, line_dash="dash", line_color="#475569", line_width=1.5)
        fig.add_vline(x=garis_x, line_dash="dash", line_color="#475569", line_width=1.5)
        fig.update_traces(textposition='top center', marker=dict(size=14))
        fig.update_layout(showlegend=False, margin={"r": 20, "t": 30, "l": 20, "b": 20})
        st.plotly_chart(fig, use_container_width=True)
        
    with col_narasi:
        st.markdown("**Deskripsi Pembagian Kuadran Sektor:**")
        st.markdown(kriteria_teks)

# ==============================================================================
# Bagian 3: UI DASHBOARD UTAMA
# ==============================================================================
st.title("🏛️ Dashboard Ekonomi Makro Daerah (Test Sandbox)")
st.markdown("---")

col_provinsi, col_tahun = st.columns(2)

with col_provinsi:
    list_provinsi = [
        "Aceh", "Sumatera Utara", "Sumatera Barat", "Riau", "Jambi", 
        "Sumatera Selatan", "Bengkulu", "Lampung", "Kepulauan Bangka Belitung", 
        "Kepulauan Riau", "DKI Jakarta", "Jawa Barat", "Jawa Tengah", 
        "DI Yogyakarta", "Jawa Timur", "Banten", "Bali", "Nusa Tenggara Barat", 
        "Nusa Tenggara Timur", "Kalimantan Barat", "Kalimantan Tengah", 
        "Kalimantan Selatan", "Kalimantan Timur", "Kalimantan Utara", 
        "Sulawesi Utara", "Sulawesi Tengah", "Sulawesi Selatan", 
        "Sulawesi Tenggara", "Gorontalo", "Sulawesi Barat", "Maluku", 
        "Maluku Utara", "Papua Barat", "Papua Barat Daya", "Papua", 
        "Papua Selatan", "Papua Tengah", "Papua Pegunungan"
    ]
    provinsi_terpilih = st.selectbox("Pilih Wilayah Analisis:", list_provinsi)

with col_tahun:
    # Memilih tahun secara default ke tahun terbaru (2025/2026 tergantung data yang ada)
    tahun_terpilih = st.selectbox("Tahun Analisis:", list(range(2011, 2027)), index=14)

st.markdown("---")

# Mengambil Data (Proses aman, mendukung Excel dan CSV secara dinamis)
df_all_prov = load_data_aman(provinsi_terpilih, tahun_terpilih) 
df_sektoral_aktif = load_data_sektoral_aman(provinsi_terpilih)
df_struktur_aktif = load_data_struktur_aman(provinsi_terpilih)

# Status Indikator Load Data
st.markdown("#### 📊 Status Pemuatan Data Monitoring")
status_makro, status_sektoral, status_struktur = st.columns(3)

with status_makro:
    if not df_all_prov.empty: st.success(f"✓ Data Makro ({len(df_all_prov)} Wilayah Terload)")
    else: st.error(f"❌ Data Makro {tahun_terpilih} Kosong/Tidak Ditemukan")

with status_sektoral:
    if not df_sektoral_aktif.empty: st.success(f"✓ Data Sektoral ({len(df_sektoral_aktif)} Sektor Terload)")
    else: st.error("❌ Data Sektoral Kosong")

with status_struktur:
    if not df_struktur_aktif.empty: st.success(f"✓ Data Struktur ({len(df_struktur_aktif)} Tren Terload)")
    else: st.error("❌ Data Struktur Kosong")

st.markdown("---")

df_row = df_all_prov[(df_all_prov['provinsi'] == provinsi_terpilih) & (df_all_prov['tahun'] == int(tahun_terpilih))]
df_active_dict = df_row.iloc[0].to_dict() if not df_row.empty else {}

def format_val(val, unit=""):
    if pd.isna(val) or val == "" or str(val).lower() == 'nan': return "-"
    return f"{val}{unit}"

# ==========================================
# TAMPILAN DASHBOARD
# ==========================================
st.header("1. KONDISI EKONOMI MAKRO DAERAH 38 PROVINSI")
col_Grafik1, col_Grafik2 = st.columns(2)
with col_Grafik1:
    st.subheader(f"Laju Pertumbuhan Ekonomi ({tahun_terpilih})")
    buat_bar_chart_makro(df_all_prov, "Pertumbuhan Ekonomi")
with col_Grafik2:
    st.subheader(f"Kontribusi PDRB terhadap Nasional ({tahun_terpilih})")
    buat_bar_chart_makro(df_all_prov, "Kontribusi PDRB")

st.subheader(f"🗺️ Sebaran Klasifikasi Wilayah")
buat_peta_klasifikasi(df_all_prov)

st.markdown("---")
st.header(f"2. KINERJA INDIKATOR EKONOMI DAN SOSIAL {provinsi_terpilih.upper()}")

st.markdown("#### Pertumbuhan Ekonomi (YoY)")
buat_line_growth(provinsi_terpilih)

st.write(f"**Capaian Laju Pertumbuhan Ekonomi Makro Daerah**")
q1, q2, q3, q4, q5 = st.columns(5)
q1.metric("TW I YoY", format_val(df_active_dict.get("lpe_tw1"), "%"))
q2.metric("TW II YoY", format_val(df_active_dict.get("lpe_tw2"), "%"))
q3.metric("TW III YoY", format_val(df_active_dict.get("lpe_tw3"), "%"))
q4.metric("TW IV YoY", format_val(df_active_dict.get("lpe_tw4"), "%"))

capaian_ctc = df_active_dict.get("lpe_ctc", np.nan)
capaian_ctc_str = format_val(capaian_ctc, "%")

with q5:
    st.markdown(
        f'<div style="background-color:#0A192F; color:white; padding:10px; border-radius:5px; text-align:center;">'
        f'<p style="margin:0; font-size:12px;">Capaian c-to-c</p>'
        f'<h3 style="margin:0; color:#00CC96;">{capaian_ctc_str}</h3>'
        f'</div>', unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown('<div style="background-color:#1E293B; padding:5px; border-radius:10px;"><h4 style="color:#F8FAFC; margin-top:0; padding-left:10px;">Simulasi Pencapaian Target Pertumbuhan Ekonomi Tahun 2026</h4></div>', unsafe_allow_html=True)
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        target_2026 = st.number_input("**Target Pertumbuhan Ekonomi (Persen):**", value=5.0, step=0.1)
        try: capaian_realitas = float(capaian_ctc) if pd.notna(capaian_ctc) else 0.0
        except ValueError: capaian_realitas = 0.0
            
        status_track = "On Track / Realistis untuk Dicapai" if capaian_realitas >= target_2026 else "Memerlukan Dukungan Percepatan / Upaya Ekstra"
        st.write(f"**Status Capaian:** {status_track}")
        pembagi = max(target_2026, 0.1)
        st.progress(min(max(float(capaian_realitas / pembagi), 0.0), 1.0))
        
    with col_sim2:
        sisa_target = max((target_2026 * 4 - capaian_realitas) / 3, 0.0)
        st.write(f"**Interpretasi Singkat:** Untuk mencapai target pertumbuhan sebesar {target_2026}%, laju pertumbuhan rata-rata pada Triwulan selanjutnya minimal harus didorong sebesar {sisa_target:.2f}%.")

st.markdown("#### Struktur Ekonomi Daerah")
buat_area_struktur(df_struktur_aktif)

st.markdown("#### Indikator Ekonomi dan Sosial Lainnya")
col_ek1, col_ek2, col_ek3, col_ek4, col_ek5 = st.columns(5)
with col_ek1: st.metric(label="PDRB Perkapita (Juta Rp)", value=format_val(df_active_dict.get('pdrb_perkapita')))
with col_ek2: st.metric(label="Inflasi Tahunan (Persen)", value=format_val(df_active_dict.get('inflasi'), "%"))
with col_ek3:
    st.markdown("**Nilai Investasi:**")
    st.write(f"• PMA: {format_val(df_active_dict.get('pma'))}")
    st.write(f"• PMDN: {format_val(df_active_dict.get('pmdn'))}")
with col_ek4: st.metric(label="Ekspor Terbesar", value=format_val(df_active_dict.get('ekspor_top3')))
with col_ek5: st.metric(label="Tenaga Kerja Terbesar", value=format_val(df_active_dict.get('naker_top')))

col_sos1, col_sos2, col_sos3, col_sos4 = st.columns(4)
with col_sos1: st.metric(label="IPM", value=format_val(df_active_dict.get('ipm')))
with col_sos2: st.metric(label="Kemiskinan (%)", value=format_val(df_active_dict.get('kemiskinan'), "%"))
with col_sos3: st.metric(label="TPT (%)", value=format_val(df_active_dict.get('tpt'), "%"))
with col_sos4: st.metric(label="Rasio Gini", value=format_val(df_active_dict.get('gini')))

st.markdown("---")
st.header(f"3. ANALISIS SECTOR UNGGULAN DAERAH {provinsi_terpilih.upper()}")
buat_scatter_sektoral(df_sektoral_aktif, "Overlay")
buat_scatter_sektoral(df_sektoral_aktif, "Shift Share")
buat_scatter_sektoral(df_sektoral_aktif, "Tipologi Klassen")

st.markdown("---")
st.header("4. INTERPRETASI DAN REKOMENDASI")
st.markdown("### Interpretasi Sisi Ekonomi")
st.info(format_val(df_active_dict.get("interpretasi_ekonomi_riil")))
st.markdown("### Rekomendasi Sisi Ekonomi")
st.success(format_val(df_active_dict.get("rekomendasi_ekonomi_riil")))
