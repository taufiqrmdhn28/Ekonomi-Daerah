# app.py

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# ==============================================================================
# Bagian 1: DATA LOADER (Disesuaikan Presisi dengan Format Kolom Baru)
# ==============================================================================

def load_data_aman(provinsi, tahun):
    """
    1. Membaca data utama dari data_ekonomi.csv untuk TAHUN terpilih (Seluruh Provinsi).
    """
    if os.path.exists("data/data_ekonomi.csv"):
        path_file = "data/data_ekonomi.csv"
    elif os.path.exists("data_ekonomi.csv"):
        path_file = "data_ekonomi.csv"
    else:
        return pd.DataFrame(columns=['provinsi', 'tahun', 'klasifikasi', 'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc'])

    try:
        # Membaca menggunakan separator titik koma (;) sesuai contoh data terbaru
        df_all = pd.read_csv(path_file, sep=";", engine='python')
        
        # Paksa nama kolom menjadi huruf kecil semua dan hapus spasi tersembunyi
        df_all.columns = df_all.columns.str.strip().str.lower()
        
        # Bersihkan spasi kosong di dalam data karakter nama provinsi
        df_all['provinsi'] = df_all['provinsi'].astype(str).str.strip()
        
        # Standarisasi kolom tahun ke tipe integer
        df_all['tahun'] = pd.to_numeric(df_all['tahun'], errors='coerce').fillna(0).astype(int)
        
        # Daftar semua kolom indikator kuantitatif yang harus berupa angka murni
        kolom_angka = [
            'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc', 
            'kontribusi', 'pdrb_perkapita', 'inflasi', 'pma', 'pmdn', 
            'ipm', 'kemiskinan', 'tpt', 'gini'
        ]
        
        for kol in kolom_angka:
            if kol in df_all.columns:
                # Ubah tanda strip (-) atau spasi kosong menjadi NaN agar tidak merusak komputasi chart
                df_all[kol] = df_all[kol].astype(str).str.strip().replace(['-', '', 'nan', 'None'], np.nan)
                # Ganti koma desimal khas wilayah menjadi titik jika ada
                df_all[kol] = df_all[kol].str.replace(',', '.', regex=False)
                df_all[kol] = pd.to_numeric(df_all[kol], errors='coerce')
        
        # Saring data berdasarkan tahun yang dipilih pengguna
        df_filtered = df_all[df_all['tahun'] == int(tahun)]
        
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_all.columns)
            
    except Exception as e:
        print(f"❌ Error pada load_data_aman: {e}")
        return pd.DataFrame(columns=['provinsi', 'tahun', 'klasifikasi', 'lpe_tw1', 'lpe_tw2', 'lpe_tw3', 'lpe_tw4', 'lpe_ctc'])

def load_data_sektoral_aman(provinsi):
    """
    2. Membaca data cross-section 17 sektor untuk provinsi terpilih dari data_sektoral.csv.
    """
    if os.path.exists("data/data_sektoral.csv"):
        path_file = "data/data_sektoral.csv"
    elif os.path.exists("data_sektoral.csv"):
        path_file = "data_sektoral.csv"
    else:
        return pd.DataFrame()

    try:
        df_sektoral = pd.read_csv(path_file, sep=";", engine='python')
        df_sektoral.columns = df_sektoral.columns.str.strip().str.lower()
        df_sektoral['provinsi'] = df_sektoral['provinsi'].astype(str).str.strip()
        
        df_filtered = df_sektoral[df_sektoral['provinsi'] == str(provinsi).strip()]
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_sektoral.columns)
    except Exception as e:
        print(f"❌ Error Sektoral: {e}")
        return pd.DataFrame()

def load_data_struktur_aman(provinsi):
    """
    3. Membaca tren historis kontribusi 17 sektor dari data_struktur.csv.
    """
    if os.path.exists("data/data_struktur.csv"):
        path_file = "data/data_struktur.csv"
    elif os.path.exists("data_struktur.csv"):
        path_file = "data_struktur.csv"
    else:
        return pd.DataFrame()

    try:
        df_all = pd.read_csv(path_file, sep=";", engine='python')
        df_all.columns = df_all.columns.str.strip().str.lower()
        df_all['provinsi'] = df_all['provinsi'].astype(str).str.strip()
        
        df_filtered = df_all[df_all['provinsi'] == str(provinsi).strip()]
        return df_filtered.reset_index(drop=True) if not df_filtered.empty else pd.DataFrame(columns=df_all.columns)
    except Exception as e:
        print(f"❌ Error Struktur: {e}")
        return pd.DataFrame()


# ==============================================================================
# Bagian 2: ANALISIS SEKTORAL (Asal file: modules/analisis_sektoral.py)
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
    """Fungsi helper untuk mencocokkan kolom sektor dengan palet warna tanpa sensitif huruf kapital"""
    return {sektor: WARNA_SEKTOR_GLOBAL.get(sektor.lower(), "#6B7280") for sektor in df_column.unique()}

def buat_bar_chart_makro(df_aktif, tipe_chart):
    """
    URUTAN 1: Visualisasi Bar Chart Horizontal Kondisi Makro 38 Provinsi.
    """
    if df_aktif.empty:
        st.warning("Data makro untuk grafik batang kosong.")
        return

    if tipe_chart == "Pertumbuhan Ekonomi":
        df_sorted = df_aktif.dropna(subset=["lpe_ctc"]).sort_values(by="lpe_ctc", ascending=True)
        fig = px.bar(df_sorted, x="lpe_ctc", y="provinsi", orientation='h',
                     labels={"lpe_ctc": "LPE c-to-c (%)", "provinsi": "Provinsi"},
                     color="lpe_ctc", color_continuous_scale="Viridis")
    else:
        df_sorted = df_aktif.dropna(subset=["kontribusi"]).sort_values(by="kontribusi", ascending=True)
        fig = px.bar(df_sorted, x="kontribusi", y="provinsi", orientation='h',
                     labels={"kontribusi": "Kontribusi PDRB (%)", "provinsi": "Provinsi"},
                     color="kontribusi", color_continuous_scale="Cividis")
        
    fig.update_layout(height=600, margin={"r":10,"t":10,"l":10,"b":10})
    st.plotly_chart(fig, use_container_width=True)

def buat_peta_klasifikasi(df_aktif):
    """
    URUTAN 1: Visualisasi Peta Choropleth 38 Provinsi dengan Skema Warna KEMD resmi.
    """
    if df_aktif.empty:
        st.warning("Data kosong, peta tidak dapat dimuat.")
        return
        
    try:
        with open("data/indonesia_provinces.geojson", "r") as f:
            geojson_indonesia = json.load(f)
            
        fig = px.choropleth_mapbox(
            df_aktif,
            geojson=geojson_indonesia,
            locations="provinsi",               
            featureidkey="properties.PROVINSI",  
            color="klasifikasi",                 
            color_discrete_map={                
                "Daerah Maju dan Cepat Tumbuh": "#0D415C",  
                "Daerah Berkembang Cepat": "#13BA8E",      
                "Daerah Maju tapi Tertekan": "#A7E048",    
                "Daerah Relatif Tertinggal": "#D9DADB"     
            },
            mapbox_style="carto-positron",
            center={"lat": -2.5, "lon": 118.0}, 
            zoom=3.5,
            opacity=0.8,
            labels={"klasifikasi": "Status Klasifikasi"}
        )
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, height=450)
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.info(f"🗺️ *[Gagal memuat batas spasial GeoJSON. Pastikan file data/indonesia_provinces.geojson tersedia. Error: {e}]*")

def buat_line_growth(df_aktif, provinsi):
    """
    URUTAN 2: Grafik Tren Pertumbuhan Ekonomi Wilayah Tren Tahunan.
    """
    try:
        if os.path.exists("data/data_ekonomi.csv"):
            path_file = "data/data_ekonomi.csv"
        else:
            path_file = "data_ekonomi.csv"
            
        df_raw = pd.read_csv(path_file, sep=";", engine='python')
        df_raw.columns = df_raw.columns.str.strip().str.lower()
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
        
        fig.update_layout(xaxis=dict(dtick=1, type='category'), xaxis_title="Tahun", yaxis_title="Persentase (%)",
                          margin={"r":10,"t":30,"l":10,"b":10}, legend_orientation="h")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.error("Gagal memuat tren pertumbuhan makro historis.")

def buat_area_struktur(df_aktif):
    """
    URUTAN 2: Grafik Struktur Ekonomi 17 Lapangan Usaha (Kunci Perbaikan: Huruf Kecil Kolom).
    """
    if not df_aktif.empty:
        df_display = df_aktif.sort_values(by="tahun")
        warna_map = get_warna_sektor_map(df_display['sektor'])
        
        fig = px.area(
            df_display,
            x="tahun",
            y="kontribusi_sektor",
            color="sektor",
            line_group="sektor",
            color_discrete_map=warna_map,
            labels={"tahun": "Tahun Analisis", "kontribusi_sektor": "Kontribusi Sektor PDRB (%)"}
        )
        fig.update_layout(
            showlegend=True,    
            xaxis=dict(dtick=1, type='category'), 
            margin={"r": 10, "t": 10, "l": 10, "b": 10}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("📊 *[Grafik Tren Area Struktur Ekonomi belum dapat dimuat karena data kosong]*")

def buat_scatter_sektoral(df_aktif, jenis_analisis):
    """
    URUTAN 3: Scatter Plot Sektoral RIIL menggunakan Input Data dari CSV Aktif.
    """
    if df_aktif.empty:
        st.info(f"🎯 *[Grafik Scatter Plot {jenis_analisis} akan muncul otomatis setelah data sektoral provinsi termuat]*")
        return

    if jenis_analisis == "Overlay":
        judul_full = 'Scatter Plot "Overlay (MRP - LQ) 2025"'
        help_teks = "Metode Overlay merupakan teknik yang menggabungkan hasil analisis Location Quotient (LQ) dan Model Rasio Pertumbuhan (MRP) untuk mengidentifikasi sektor yang memiliki keunggulan sekaligus pertumbuhan yang kuat. Dengan mengombinasikan kedua pendekatan tersebut, metode ini menghasilkan penentuan sektor prioritas yang lebih robust dibandingkan penggunaan satu metode secara terpisah."
        kriteria_teks = (
            "- **Kriteria I (Rasio Pertumbuhan > 1 dan LQ > 1):** Sektor Unggulan dan Dominan $\\rightarrow$ sektor dengan pertumbuhan tinggi dan kontribusi besar yang menjadi motor utama perekonomian daerah.\n"
            "- **Kriteria II (Rasio Pertumbuhan > 1 dan LQ < 1):** Sektor Berkembang $\\rightarrow$ sektor dengan pertumbuhan tinggi namun kontribusinya masih kecil, sehingga berpotensi menjadi sumber pertumbuhan baru.\n"
            "- **Kriteria III (Rasio Pertumbuhan < 1 dan LQ > 1):** Sektor Potensial $\\rightarrow$ sektor dengan kontribusi besar tetapi pertumbuhannya mulai melambat, sehingga perlu dijaga keberlanjutannya.\n"
            "- **Kriteria IV (Rasio Pertumbuhan < 1 dan LQ < 1):** Sektor Tertinggal $\\rightarrow$ sektor dengan pertumbuhan dan kontribusi yang rendah, sehingga belum memiliki peran signifikan dalam perekonomian."
        )
        col_x, col_y = "lq_2025", "rps_2025"
        garis_x, garis_y = 1.0, 1.0  
        labels_x, labels_y = "Komponen Kontribusi (Location Quotient)", "Komponen Pertumbuhan (Rasio Pertumbuhan)"

    elif jenis_analisis == "Shift Share":
        judul_full = 'Scatter Plot "Shift Share 2015/2025"'
        help_teks = "Metode Shift Share digunakan untuk menguraikan pertumbuhan suatu sektor ke dalam komponen pengaruh pertumbuhan nasional, struktur ekonomi, dan daya saing daerah. Melalui metode ini, dapat diketahui apakah kinerja suatu sektor didorong oleh dinamika nasional atau oleh keunggulan kompetitif yang dimiliki daerah."
        kriteria_teks = (
            "- **Kriteria I (RS + IM +):** Sektor Tumbuh Pesat $\\rightarrow$ sektor yang memiliki daya saing tinggi di tingkat lokal dan didukung oleh tren pertumbuhan nasional.\n"
            "- **Kriteria II (RS + IM -):** Sektor Berpotensi $\\rightarrow$ sektor yang kuat secara lokal meskipun secara nasional cenderung melambat, sehingga berpotensi menjadi keunggulan spesifik daerah.\n"
            "- **Kriteria III (RS - IM +):** Sektor Berkembang $\\rightarrow$ sektor yang tumbuh secara nasional namun belum diikuti oleh daya saing daerah, sehingga memerlukan penguatan kapasitas lokal.\n"
            "- **Kriteria IV (RS - IM -):** Sektor Tertinggal $\\rightarrow$ sektor dengan daya saing dan pertumbuhan yang rendah baik di tingkat lokal maupun nasional."
        )
        col_x, col_y = "im_2025", "rs_2025"
        garis_x, garis_y = 0.0, 0.0  
        labels_x, labels_y = "Komponen Daya Saing (Regional Share)", "Komponen Struktur Nasional (Industrial Mix)"

    else:  
        judul_full = 'Scatter Plot "Tipologi Klassen Rata-Rata 2022-2025"'
        help_teks = "Tipologi Klassen merupakan metode klasifikasi sektor berdasarkan tingkat pertumbuhan dan kontribusinya terhadap perekonomian daerah. Hasil analisisnya memberikan gambaran yang jelas mengenai posisi relatif setiap sektor, mulai dari sektor unggulan hingga sektor yang masih tertinggal, sehingga mendukung perumusan arah pembangunan ekonomi daerah."
        kriteria_teks = (
            "- **Kriteria I (Pertumbuhan > Nasional dan Kontribusi > Nasional):** Sektor Andalan $\\rightarrow$ sektor dengan pertumbuhan dan kontribusi tinggi yang menjadi prioritas utama pembangunan ekonomi.\n"
            "- **Kriteria II (Pertumbuhan > Nasional dan Kontribusi < Nasional):** Sektor Berkembang $\\rightarrow$ sektor dengan pertumbuhan tinggi namun kontribusi masih kecil, sehingga berpotensi menjadi andalan baru.\n"
            "- **Kriteria III (Pertumbuhan < Nasional dan Kontribusi > Nasional):** Sektor Potensial $\\rightarrow$ sektor dengan kontribusi besar tetapi pertumbuhan melambat, sehingga perlu dijaga agar tidak menurun.\n"
            "- **Kriteria IV (Pertumbuhan < Nasional dan Kontribusi < Nasional):** Sektor Tertinggal $\\rightarrow$ sektor dengan pertumbuhan dan kontribusi rendah yang memerlukan perhatian dan intervensi khusus."
        )
        col_x, col_y = "kontribusi_2025", "pertumbuhan_2025"
        garis_x, garis_y = 5.6, 5.1  
        labels_x, labels_y = "Rata-Rata Kontribusi Sektor terhadap PDRB (%)", "Rata-Rata Pertumbuhan Sektor (%)"

    st.markdown(f"##### {judul_full}", help=help_teks)
    col_grafik, col_narasi = st.columns([2, 1])
    
    with col_grafik:
        warna_map = get_warna_sektor_map(df_aktif['sektor'])
        
        fig = px.scatter(
            df_aktif, 
            x=col_x, 
            y=col_y, 
            text="sektor",        
            color="sektor",       
            labels={col_x: labels_x, col_y: labels_y},
            color_discrete_map=warna_map  
        )
        
        fig.add_hline(y=garis_y, line_dash="dash", line_color="#475569", line_width=1.5)
        fig.add_vline(x=garis_x, line_dash="dash", line_color="#475569", line_width=1.5)
        
        fig.update_traces(textposition='top center', marker=dict(size=14))
        fig.update_layout(
            showlegend=False,          
            margin={"r": 20, "t": 30, "l": 20, "b": 20}
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col_narasi:
        st.markdown("**Deskripsi Pembagian Kuadran Sektor:**")
        st.markdown(kriteria_teks)


# ==============================================================================
# Bagian 3: APLIKASI UTAMA (Asal file: app.py)
# ==============================================================================

st.set_page_config(page_title="Ekonomi Makro Daerah", layout="wide")

st.title("🏛️ Dashboard Ekonomi Makro Daerah")
st.markdown("---")

st.markdown("#### Pilihan Filter Analisis")
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
    tahun_terpilih = st.selectbox("Tahun Analisis:", list(range(2011, 2027)), index=14)

st.markdown("---")

df_all_prov = load_data_aman(provinsi_terpilih, tahun_terpilih) 
df_sektoral_aktif = load_data_sektoral_aman(provinsi_terpilih)
df_struktur_aktif = load_data_struktur_aman(provinsi_terpilih)

# ==========================================
# BAGIAN INDIKATOR PEMUATAN DATA (DATA FRAME TRACKER)
# ==========================================
st.markdown("#### 📊 Status Pemuatan Data Monitoring")
status_makro, status_sektoral, status_struktur = st.columns(3)

with status_makro:
    if not df_all_prov.empty:
        st.success(f"✓ Data Makro ({len(df_all_prov)} Wilayah Terload)")
    else:
        st.error("❌ Data Makro Kosong / Gagal Load")

with status_sektoral:
    if not df_sektoral_aktif.empty:
        st.success(f"✓ Data Sektoral ({len(df_sektoral_aktif)} Sektor Terload)")
    else:
        st.error("❌ Data Sektoral Kosong (Cek data_sektoral.csv)")

with status_struktur:
    if not df_struktur_aktif.empty:
        st.success(f"✓ Data Struktur ({len(df_struktur_aktif)} Tren Terload)")
    else:
        st.error("❌ Data Struktur Kosong (Cek data_struktur.csv)")

st.markdown("---")

df_row = df_all_prov[(df_all_prov['provinsi'] == provinsi_terpilih) & (df_all_prov['tahun'] == int(tahun_terpilih))]

if not df_row.empty:
    df_active_dict = df_row.iloc[0].to_dict()
else:
    df_active_dict = {}

# Fungsi pembantu untuk memformat nilai kosong agar rapi di Metric Card
def format_val(val, unit=""):
    if pd.isna(val) or val == "":
        return "-"
    return f"{val}{unit}"

# ==========================================
# URUTAN 1: KONDISI EKONOMI MAKRO DAERAH 38 PROVINSI
# ==========================================
st.header("KONDISI EKONOMI MAKRO DAERAH 38 PROVINSI")

col_Grafik1, col_Grafik2 = st.columns(2)

with col_Grafik1:
    st.subheader(f"Laju Pertumbuhan Ekonomi ({tahun_terpilih})")
    buat_bar_chart_makro(df_all_prov, "Pertumbuhan Ekonomi")

with col_Grafik2:
    st.subheader(f"Kontribusi PDRB terhadap Nasional ({tahun_terpilih})")
    buat_bar_chart_makro(df_all_prov, "Kontribusi PDRB")

st.subheader(f"🗺️ Sebaran Klasifikasi Wilayah")
buat_peta_klasifikasi(df_all_prov)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# URUTAN 2: KINERJA INDIKATOR EKONOMI DAN SOSIAL
# ==========================================
st.header(f"KINERJA INDIKATOR EKONOMI DAN SOSIAL {provinsi_terpilih.upper()}")

st.markdown("#### Pertumbuhan Ekonomi (YoY)")
buat_line_growth(df_all_prov, provinsi_terpilih)

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
        f'</div>', 
        unsafe_allow_html=True
    )

st.markdown("<br>", unsafe_allow_html=True)
with st.container():
    st.markdown(
        '<div style="background-color:#1E293B; padding:5px; border-radius:10px;">'
        '<h4 style="color:#F8FAFC; margin-top:0; padding-left:10px;">Simulasi Pencapaian Target Pertumbuhan Ekonomi Tahun 2026</h4>'
        '</div>', 
        unsafe_allow_html=True
    )
    
    col_sim1, col_sim2 = st.columns(2)
    with col_sim1:
        target_2026 = st.number_input("**Target Pertumbuhan Ekonomi (Persen):**", value=5.0, step=0.1)
        
        try:
            capaian_realitas = float(capaian_ctc) if pd.notna(capaian_ctc) else 0.0
        except ValueError:
            capaian_realitas = 0.0
            
        status_track = "On Track / Realistis untuk Dicapai" if capaian_realitas >= target_2026 else "Memerlukan Dukungan Percepatan / Upaya Ekstra"
        st.write(f"**Status Capaian:** {status_track}")
        
        pembagi = max(target_2026, 0.1)
        st.progress(min(max(float(capaian_realitas / pembagi), 0.0), 1.0))
        
    with col_sim2:
        sisa_target = max((target_2026 * 4 - capaian_realitas) / 3, 0.0)
        st.write(f"**Interpretasi Singkat:** Untuk mencapai target pertumbuhan sebesar {target_2026}%, laju pertumbuhan rata-rata pada Triwulan selanjutnya minimal harus didorong sebesar {sisa_target:.2f}%.")

# 2. Struktur Ekonomi Daerah (Area Chart)
st.markdown("#### Struktur Ekonomi Daerah")
buat_area_struktur(df_struktur_aktif)

# 3. Indikator Ekonomi dan Sosial Lainnya
st.markdown("#### Indikator Ekonomi dan Sosial Lainnya")

col_ek1, col_ek2, col_ek3, col_ek4, col_ek5 = st.columns(5)
with col_ek1:
    st.metric(label="PDRB Perkapita (Juta Rp)", value=format_val(df_active_dict.get('pdrb_perkapita')))
with col_ek2:
    st.metric(label="Tingkat Inflasi Tahunan (Persen)", value=format_val(df_active_dict.get('inflasi'), "%"))
with col_ek3:
    with st.container():
        st.markdown("**Nilai Investasi:**")
        st.write(f"• PMA (Juta USD): {format_val(df_active_dict.get('pma'))}")
        st.write(f"• PMDN (Miliar Rp): {format_val(df_active_dict.get('pmdn'))}")
with col_ek4:
    st.metric(label="Komoditas Ekspor Terbesar", value=format_val(df_active_dict.get('ekspor_top3')))
with col_ek5:
    st.metric(label="Tenaga Kerja Terbesar", value=format_val(df_active_dict.get('naker_top')))

col_sos1, col_sos2, col_sos3, col_sos4 = st.columns(4)
with col_sos1:
    st.metric(label="Indeks Pembangunan Manusia - IPM", value=format_val(df_active_dict.get('ipm')))
with col_sos2:
    st.metric(label="Tingkat Kemiskinan (%)", value=format_val(df_active_dict.get('kemiskinan'), "%"))
with col_sos3:
    st.metric(label="Tingkat Pengangguran Terbuka (TPT) (%)", value=format_val(df_active_dict.get('tpt'), "%"))
with col_sos4:
    st.metric(label="Rasio Gini", value=format_val(df_active_dict.get('gini')))

st.markdown("---")

# ==========================================
# URUTAN 3: ANALISIS SEKTOR UNGGULAN DAERAH
# ==========================================
st.header(f"ANALISIS SECTOR UNGGULAN DAERAH {provinsi_terpilih.upper()}")
buat_scatter_sektoral(df_sektoral_aktif, "Overlay")
buat_scatter_sektoral(df_sektoral_aktif, "Shift Share")
buat_scatter_sektoral(df_sektoral_aktif, "Tipologi Klassen")

st.markdown("---")

# ==========================================
# URUTAN 4: INTERPRETASI DAN REKOMENDASI
# ==========================================
st.header("INTERPRETASI DAN REKOMENDASI")

st.markdown("### Interpretasi Sisi Ekonomi")
st.info(format_val(df_active_dict.get("interpretasi_ekonomi_riil")))

st.markdown("### Rekomendasi Sisi Ekonomi")
st.success(format_val(df_active_dict.get("rekomendasi_ekonomi_riil")))
