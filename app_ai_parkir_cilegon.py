# app_ai_parkir_cilegon.py
# Dashboard AI Potensi Retribusi Parkir Kota Cilegon
# Versi dengan Plotly dan layout mirip dashboard OSS

import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans
import plotly.express as px

# ======================================================
# FUNGSI BANTU
# ======================================================

def format_rupiah(angka: float) -> str:
    """Format angka ke Rupiah dengan titik sebagai pemisah ribuan."""
    return "Rp {:,}".format(int(round(angka))).replace(",", ".")


def load_excel_titik_parkir(uploaded_file):
    """
    Membaca file Excel titik retribusi parkir dengan struktur:
    Jenis, Kecamatan, Kelurahan, Lokasi, RATA-RATA YANG PARKIR
    """
    df_raw = pd.read_excel(uploaded_file, sheet_name=0)

    # Cek kolom wajib
    required_cols = ["Jenis", "Kecamatan", "Kelurahan", "Lokasi", "RATA-RATA YANG PARKIR"]
    missing = [c for c in required_cols if c not in df_raw.columns]
    if missing:
        st.error(f"Kolom berikut tidak ditemukan di file Excel: {missing}")
        return df_raw, None

    df_titik = df_raw.copy()
    df_titik["RataRataParkir"] = pd.to_numeric(
        df_titik["RATA-RATA YANG PARKIR"],
        errors="coerce"
    )
    df_titik = df_titik.dropna(subset=["RataRataParkir"])
    df_titik["RataRataParkir"] = df_titik["RataRataParkir"].astype(float)

    return df_raw, df_titik


def buat_cluster_ai(df_titik, n_clusters=3):
    """K-Means clustering berdasarkan RataRataParkir."""
    if df_titik is None or df_titik.empty:
        return None, None

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(df_titik[["RataRataParkir"]])

    centers = model.cluster_centers_.ravel()
    order = centers.argsort()

    label_map = {}
    label_map[order[0]] = "Rendah"
    label_map[order[1]] = "Sedang"
    if n_clusters > 2:
        label_map[order[2]] = "Tinggi"

    df_titik = df_titik.copy()
    df_titik["Cluster_ID"] = model.labels_
    df_titik["Kategori_AI"] = df_titik["Cluster_ID"].map(label_map)

    return df_titik, centers


# ======================================================
# KONFIGURASI HALAMAN + CSS
# ======================================================

st.set_page_config(
    page_title="Dashboard AI Retribusi Parkir Cilegon",
    page_icon="🅿️",
    layout="wide",
)

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    .oss-header {
        background: linear-gradient(90deg, #7c0a02, #b71c1c);
        padding: 0.7rem 1.8rem;
        color: white;
        border-radius: 0 0 8px 8px;
        margin-bottom: 0.7rem;
    }
    .oss-title {
        font-size: 1.25rem;
        font-weight: 700;
    }
    .oss-subtitle {
        font-size: 0.85rem;
        opacity: 0.9;
    }
    .card-box {
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
    }
    .card-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        color: #64748b;
        font-weight: 600;
    }
    .card-value-big {
        font-size: 1.3rem;
        font-weight: 700;
        color: #111827;
    }
    .card-sub {
        font-size: 0.8rem;
        color: #6b7280;
    }
    .section-title {
        font-size: 0.9rem;
        font-weight: 700;
        margin-bottom: 0.1rem;
    }
    .section-subtitle {
        font-size: 0.75rem;
        color: #6b7280;
        margin-bottom: 0.4rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================================================
# HEADER
# ======================================================

with st.container():
    st.markdown(
        """
        <div class="oss-header">
          <div class="oss-title">Dashboard Potensi Retribusi Parkir Kota Cilegon</div>
          <div class="oss-subtitle">Estimasi potensi, target, dan segmentasi titik parkir berbasis kecerdasan buatan menggunakan K-Means:</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ======================================================
# SIDEBAR – PENGATURAN
# ======================================================

st.sidebar.title("⚙️ Pengaturan")

st.sidebar.subheader("Data Makro Kota")

roda_dua = st.sidebar.number_input(
    "Total kendaraan roda dua",
    min_value=0,
    value=41564,
    step=1
)
roda_empat = st.sidebar.number_input(
    "Total kendaraan roda empat",
    min_value=0,
    value=13369,
    step=1
)
tarif = st.sidebar.number_input(
    "Tarif rata-rata parkir (Rp / kendaraan)",
    min_value=0,
    value=2000,
    step=500
)
persen_bayar = st.sidebar.number_input(
    "Persentase kendaraan yang membayar retribusi (%)",
    min_value=0.0,
    max_value=100.0,
    value=25.0,
    step=1.0
)
target_realisasi = st.sidebar.number_input(
    "Target realisasi dari potensi (%)",
    min_value=0.0,
    max_value=150.0,
    value=80.0,
    step=5.0,
    help="Misal 80% berarti target resmi = 80% dari potensi maksimum."
)

st.sidebar.subheader("Upload Data Titik Parkir")
uploaded_file = st.sidebar.file_uploader(
    "File Excel (*.xlsx) dengan kolom:\nJenis, Kecamatan, Kelurahan, Lokasi, RATA-RATA YANG PARKIR",
    type=["xlsx", "xls"]
)

st.sidebar.markdown(
    "<span class='section-subtitle'>Data Excel digunakan untuk analisis per kelurahan, per lokasi, dan AI clustering.</span>",
    unsafe_allow_html=True,
)

# ======================================================
# PERHITUNGAN MAKRO
# ======================================================

total_kendaraan = roda_dua + roda_empat
kendaraan_bayar = total_kendaraan * persen_bayar / 100.0

potensi_harian = kendaraan_bayar * tarif
potensi_bulanan = potensi_harian * 30
potensi_tahunan = potensi_harian * 365

target_harian = potensi_harian * target_realisasi / 100.0
target_bulanan = potensi_bulanan * target_realisasi / 100.0
target_tahunan = potensi_tahunan * target_realisasi / 100.0

# ======================================================
# LAYOUT UTAMA: GRID MIRIP DASHBOARD OSS
# ======================================================

# ——— Row 1: Kartu angka besar (makro kota) ———
row1_col1, row1_col2, row1_col3, row1_col4 = st.columns([1.3, 1.1, 1.1, 1.1])

with row1_col1:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<div class='card-label'>Total Kendaraan</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-value-big'>{total_kendaraan:,}</div>".replace(",", "."), unsafe_allow_html=True)
    st.markdown(
        f"<div class='card-sub'>Roda 2: {roda_dua:,} · Roda 4: {roda_empat:,}</div>".replace(",", "."),
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col2:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<div class='card-label'>Potensi Harian</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-value-big'>{format_rupiah(potensi_harian)}</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-sub'>Estimasi pendapatan / hari</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col3:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<div class='card-label'>Potensi Tahunan</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-value-big'>{format_rupiah(potensi_tahunan)}</div>", unsafe_allow_html=True)
    st.markdown("<div class='card-sub'>Proyeksi 365 hari</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with row1_col4:
    st.markdown("<div class='card-box'>", unsafe_allow_html=True)
    st.markdown("<div class='card-label'>Target Tahunan</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='card-value-big'>{format_rupiah(target_tahunan)}</div>", unsafe_allow_html=True)
    st.markdown(
        f"<div class='card-sub'>Target {target_realisasi:.0f}% dari potensi</div>",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("")

# Siapkan variabel untuk data mikro agar bisa dipakai di banyak panel
df_raw, df_titik = (None, None)
df_potensi = None
df_kelurahan = None
df_cluster = None
centers = None

if uploaded_file is not None:
    df_raw, df_titik = load_excel_titik_parkir(uploaded_file)
    if df_titik is not None and not df_titik.empty:
        # Perhitungan potensi / target per lokasi
        df_potensi = df_titik.copy()
        df_potensi["Kendaraan Membayar / Hari"] = df_potensi["RataRataParkir"] * persen_bayar / 100.0
        df_potensi["Potensi Harian (Rp)"] = df_potensi["Kendaraan Membayar / Hari"] * tarif
        df_potensi["Potensi Bulanan (Rp)"] = df_potensi["Potensi Harian (Rp)"] * 30
        df_potensi["Potensi Tahunan (Rp)"] = df_potensi["Potensi Harian (Rp)"] * 365

        df_potensi["Target Harian (Rp)"] = df_potensi["Potensi Harian (Rp)"] * target_realisasi / 100.0
        df_potensi["Target Bulanan (Rp)"] = df_potensi["Potensi Bulanan (Rp)"] * target_realisasi / 100.0
        df_potensi["Target Tahunan (Rp)"] = df_potensi["Potensi Tahunan (Rp)"] * target_realisasi / 100.0

        df_kelurahan = df_potensi.groupby(["Kecamatan", "Kelurahan"], as_index=False)[
            ["RataRataParkir", "Kendaraan Membayar / Hari",
             "Potensi Harian (Rp)", "Potensi Bulanan (Rp)", "Potensi Tahunan (Rp)",
             "Target Harian (Rp)", "Target Bulanan (Rp)", "Target Tahunan (Rp)"]
        ].sum()

        # AI clustering
        df_cluster, centers = buat_cluster_ai(df_titik, n_clusters=3)

# ——— Row 2: Donut clustering + bar per kelurahan + tabel sebaran singkat ———
row2_col1, row2_col2 = st.columns([1.2, 1.8])

with row2_col1:
    st.markdown("<div class='section-title'>Sebaran Titik Parkir berdasarkan Kategori AI</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Menggunakan K-Means: Rendah, Sedang, Tinggi berdasarkan rata-rata kendaraan parkir.</div>",
        unsafe_allow_html=True,
    )

    if df_cluster is not None and not df_cluster.empty:
        kategori_counts = df_cluster["Kategori_AI"].value_counts().reset_index()
        kategori_counts.columns = ["Kategori", "Jumlah"]

        fig_donut = px.pie(
            kategori_counts,
            names="Kategori",
            values="Jumlah",
            hole=0.6,
            color="Kategori",
            color_discrete_map={
                "Tinggi": "#d32f2f",
                "Sedang": "#ffb300",
                "Rendah": "#1976d2",
            }
        )
        fig_donut.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend_title_text="Kategori AI",
        )
        st.plotly_chart(fig_donut, use_container_width=True)
    else:
        st.info("Upload data Excel untuk melihat sebaran kategori AI.")

with row2_col2:
    st.markdown("<div class='section-title'>Sebaran Potensi Harian per Kelurahan</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Menampilkan 10 kelurahan dengan potensi harian tertinggi.</div>",
        unsafe_allow_html=True,
    )

    if df_kelurahan is not None and not df_kelurahan.empty:
        df_top_kel = df_kelurahan.copy()
        df_top_kel["Label"] = df_top_kel["Kelurahan"]
        df_top = df_top_kel.sort_values("Potensi Harian (Rp)", ascending=False).head(10)

        fig_bar_kel = px.bar(
            df_top,
            x="Potensi Harian (Rp)",
            y="Label",
            orientation="h",
            text="Potensi Harian (Rp)",
            color="Potensi Harian (Rp)",
            color_continuous_scale="Blues",
        )
        fig_bar_kel.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis_title="Kelurahan",
            xaxis_title="Potensi Harian (Rp)",
        )
        fig_bar_kel.update_traces(
            texttemplate="%{text:.0f}",
            textposition="outside",
            hovertemplate="Kelurahan=%{y}<br>Potensi=%{x:,.0f}<extra></extra>",
        )
        st.plotly_chart(fig_bar_kel, use_container_width=True)
    else:
        st.info("Belum ada data kelurahan. Upload file Excel terlebih dahulu.")

# ——— Row 3: Tabel per lokasi & grafik garis sederhana (opsional) ———
row3_col1, row3_col2 = st.columns([1.8, 1.2])

with row3_col1:
    st.markdown("<div class='section-title'>Tabel Potensi & Target per Lokasi</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Rangkuman per titik parkir berdasarkan rata-rata kendaraan parkir per hari.</div>",
        unsafe_allow_html=True,
    )

    if df_potensi is not None and not df_potensi.empty:
        st.dataframe(
            df_potensi[[
                "Kecamatan", "Kelurahan", "Lokasi",
                "RataRataParkir", "Kendaraan Membayar / Hari",
                "Potensi Harian (Rp)", "Target Harian (Rp)"
            ]],
            use_container_width=True,
            height=320
        )
    else:
        st.info("Tabel akan muncul setelah file Excel di-upload dan berhasil diproses.")

with row3_col2:
    st.markdown("<div class='section-title'>Ringkasan Potensi vs Target (Kota)</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='section-subtitle'>Perbandingan potensi dan target pada level kota.</div>",
        unsafe_allow_html=True,
    )

    df_ringkas = pd.DataFrame({
        "Jenis": ["Potensi Harian", "Target Harian", "Potensi Bulanan", "Target Bulanan", "Potensi Tahunan", "Target Tahunan"],
        "Nilai": [
            potensi_harian, target_harian,
            potensi_bulanan, target_bulanan,
            potensi_tahunan, target_tahunan
        ]
    })

    fig_bar_ringkas = px.bar(
        df_ringkas,
        x="Jenis",
        y="Nilai",
        text="Nilai",
        color="Jenis",
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig_bar_ringkas.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis_title="",
        yaxis_title="Nilai (Rp)",
    )
    fig_bar_ringkas.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside",
        hovertemplate="Jenis=%{x}<br>Nilai=%{y:,.0f}<extra></extra>",
    )
    st.plotly_chart(fig_bar_ringkas, use_container_width=True)

# ======================================================
# FOOTER PENJELASAN SINGKAT
# ======================================================

st.markdown("---")
st.markdown(
    """
    <span class="section-subtitle">
    Dashboard ini dikembangkan menggunakan <b>Streamlit</b>, <b>Pandas</b>, <b>scikit-learn</b>, dan <b>Plotly</b>.
    Data dan parameter pada sidebar dapat disesuaikan untuk simulasi berbagai skenario retribusi parkir Kota Cilegon.
    </span>
    """,
    unsafe_allow_html=True,
)
