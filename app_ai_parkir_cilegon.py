# app_ai_parkir_cilegon.py
# PENERAPAN KECERDASAN BUATAN DALAM MENGHITUNG POTENSI RETRIBUSI PARKIR DI KOTA CILEGON
#
# Versi UI lebih menarik + rekomendasi potensi & target per kelurahan dan per lokasi

import streamlit as st
import pandas as pd
from sklearn.cluster import KMeans

# =========================
# FUNGSI BANTU
# =========================

def format_rupiah(angka: float) -> str:
    """Format angka ke bentuk Rupiah dengan pemisah ribuan titik."""
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

    # Ambil hanya baris yang punya nilai rata-rata parkir (numeric)
    df_titik = df_raw.copy()
    df_titik["RataRataParkir"] = pd.to_numeric(
        df_titik["RATA-RATA YANG PARKIR"],
        errors="coerce"
    )
    df_titik = df_titik.dropna(subset=["RataRataParkir"])
    df_titik["RataRataParkir"] = df_titik["RataRataParkir"].astype(float)

    return df_raw, df_titik


def buat_cluster_ai(df_titik, n_clusters=3):
    """
    Menggunakan K-Means (AI / Machine Learning) untuk
    mengelompokkan titik parkir berdasarkan RataRataParkir.
    """
    if df_titik is None or df_titik.empty:
        return None, None

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model.fit(df_titik[["RataRataParkir"]])

    # Pusat cluster
    centers = model.cluster_centers_.ravel()
    order = centers.argsort()  # indeks cluster dari kecil ke besar

    label_map = {}
    label_map[order[0]] = "Rendah"
    label_map[order[1]] = "Sedang"
    if n_clusters > 2:
        label_map[order[2]] = "Tinggi"

    df_titik = df_titik.copy()
    df_titik["Cluster_ID"] = model.labels_
    df_titik["Kategori_AI"] = df_titik["Cluster_ID"].map(label_map)

    return df_titik, centers


# =========================
# KONFIGURASI HALAMAN + SEDIKIT CSS
# =========================

st.set_page_config(
    page_title="AI Potensi Retribusi Parkir Kota Cilegon",
    layout="wide"
)

# Sedikit styling biar lebih halus
st.markdown(
    """
    <style>
    .small-text { font-size: 0.85rem; color: #555; }
    .center-text { text-align: center; }
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# HEADER UTAMA
# =========================

st.title("Menghitung Potensi Retribusi Parkir Kota Cilegon")
st.markdown(
    """
Aplikasi ini menerapkan **kecerdasan buatan (K-Means clustering)** untuk menganalisis
titik retribusi parkir serta menghitung **potensi dan rekomendasi target retribusi** 
secara makro, per kelurahan, dan per lokasi.
"""
)

# =========================
# SIDEBAR – PENGATURAN
# =========================

st.sidebar.header("⚙️ Pengaturan Data Dasar Kota")

# Data makro kota (bisa diubah manual)
roda_dua = st.sidebar.number_input(
    "Total kendaraan roda dua",
    min_value=0,
    value=41564,   # default sesuai data
    step=1
)

roda_empat = st.sidebar.number_input(
    "Total kendaraan roda empat",
    min_value=0,
    value=13369,   # default sesuai data
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
    value=25.0,      # default 25%
    step=1.0
)

# Tambahan: target realisasi dari potensi (misal 80% dari potensi jadi target resmi)
target_realisasi = st.sidebar.number_input(
    "Target realisasi dari potensi (%)",
    min_value=0.0,
    max_value=150.0,
    value=80.0,
    step=5.0,
    help="Misal 80% berarti target resmi = 80% dari potensi maksimal."
)

st.sidebar.markdown("---")
st.sidebar.header("📄 Data Titik Parkir (Excel)")

uploaded_file = st.sidebar.file_uploader(
    "Upload file Excel titik retribusi parkir (*.xlsx)",
    type=["xlsx", "xls"]
)

st.sidebar.markdown(
    """
    <p class="small-text">
    Pastikan file memiliki kolom:<br>
    <code>Jenis, Kecamatan, Kelurahan, Lokasi, RATA-RATA YANG PARKIR</code>
    </p>
    """,
    unsafe_allow_html=True
)

# =========================
# PERHITUNGAN MAKRO (LEVEL KOTA)
# =========================

total_kendaraan = roda_dua + roda_empat
kendaraan_bayar = total_kendaraan * persen_bayar / 100.0

potensi_harian = kendaraan_bayar * tarif
potensi_bulanan = potensi_harian * 30       # asumsi 30 hari
potensi_tahunan = potensi_harian * 365      # asumsi 365 hari

target_harian = potensi_harian * target_realisasi / 100.0
target_bulanan = potensi_bulanan * target_realisasi / 100.0
target_tahunan = potensi_tahunan * target_realisasi / 100.0

# =========================
# TABS UTAMA
# =========================

tab_makro, tab_mikro, tab_ai, tab_tentang = st.tabs(
    ["📊 Potensi Kota (Makro)", "📍 Titik Parkir, Kelurahan & Lokasi", "🤖 Analisis AI (K-Means)", "ℹ️ Tentang Metode"]
)

# ---------- TAB MAKRO ----------
with tab_makro:
    st.subheader("📊 Potensi Retribusi Parkir Tingkat Kota")

    st.caption(
        f"Perhitungan menggunakan total kendaraan terdata dan asumsi "
        f"hanya **{persen_bayar:.0f}%** yang membayar retribusi.\n"
        f"Target realisasi saat ini diset **{target_realisasi:.0f}%** dari potensi."
    )

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("Roda Dua", f"{roda_dua:,}".replace(",", "."))
    with col2:
        st.metric("Roda Empat", f"{roda_empat:,}".replace(",", "."))
    with col3:
        st.metric("Total Kendaraan", f"{total_kendaraan:,}".replace(",", "."))
    with col4:
        st.metric("Kendaraan Membayar\n(asumsi %)", f"{int(kendaraan_bayar):,}".replace(",", "."))
    with col5:
        st.metric("Tarif Rata-rata", format_rupiah(tarif))

    st.markdown("")
    col6, col7, col8 = st.columns(3)

    with col6:
        st.metric("Potensi Harian", format_rupiah(potensi_harian), help="Potensi maksimum berdasarkan asumsi.")
        st.metric("Target Harian", format_rupiah(target_harian), help="Target = potensi × persen target realisasi.")
    with col7:
        st.metric("Potensi Bulanan (30 hari)", format_rupiah(potensi_bulanan))
        st.metric("Target Bulanan", format_rupiah(target_bulanan))
    with col8:
        st.metric("Potensi Tahunan (365 hari)", format_rupiah(potensi_tahunan))
        st.metric("Target Tahunan", format_rupiah(target_tahunan))

    with st.expander("📝 Interpretasi Singkat (Makro)", expanded=True):
        st.write(
            f"""
- Total kendaraan: **{total_kendaraan:,}** (roda dua: {roda_dua:,}, roda empat: {roda_empat:,}).
- Dengan asumsi **{persen_bayar:.0f}%** membayar dan tarif **{format_rupiah(tarif)}**, 
  maka potensi retribusi parkir per hari diperkirakan sekitar **{format_rupiah(potensi_harian)}**.
- Jika pemerintah daerah menargetkan **{target_realisasi:.0f}%** dari potensi, 
  maka target harian adalah **{format_rupiah(target_harian)}**.
""".replace(",", ".")
        )

# ---------- TAB MIKRO (PER KELURAHAN & LOKASI) ----------
with tab_mikro:
    st.subheader("📍 Analisis Titik Retribusi Parkir, Kelurahan, dan Lokasi")

    if uploaded_file is None:
        st.info("Silakan upload file Excel titik retribusi parkir di sidebar untuk melihat analisis detail.")
    else:
        df_raw, df_titik = load_excel_titik_parkir(uploaded_file)

        if df_titik is not None and not df_titik.empty:
            # === Perhitungan potensi & target per lokasi ===
            df_potensi = df_titik.copy()
            df_potensi["Kendaraan Membayar / Hari"] = df_potensi["RataRataParkir"] * persen_bayar / 100.0
            df_potensi["Potensi Harian (Rp)"] = df_potensi["Kendaraan Membayar / Hari"] * tarif
            df_potensi["Potensi Bulanan (Rp)"] = df_potensi["Potensi Harian (Rp)"] * 30
            df_potensi["Potensi Tahunan (Rp)"] = df_potensi["Potensi Harian (Rp)"] * 365

            df_potensi["Target Harian (Rp)"] = df_potensi["Potensi Harian (Rp)"] * target_realisasi / 100.0
            df_potensi["Target Bulanan (Rp)"] = df_potensi["Potensi Bulanan (Rp)"] * target_realisasi / 100.0
            df_potensi["Target Tahunan (Rp)"] = df_potensi["Potensi Tahunan (Rp)"] * target_realisasi / 100.0

            total_rata_parkir = df_potensi["RataRataParkir"].sum()
            total_potensi_harian_excel = df_potensi["Potensi Harian (Rp)"].sum()
            total_target_harian_excel = df_potensi["Target Harian (Rp)"].sum()

            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("Jumlah Titik Parkir (valid)", f"{len(df_potensi)}")
            with col_b:
                st.metric("Total Rata-rata Kendaraan Parkir / Hari", f"{int(total_rata_parkir):,}".replace(",", "."))
            with col_c:
                st.metric("Total Potensi Harian (dari Excel)", format_rupiah(total_potensi_harian_excel))

            st.caption(
                "Perhitungan ini menggunakan kolom **'RATA-RATA YANG PARKIR'** dari file Excel, "
                f"asumsi **{persen_bayar:.0f}%** kendaraan membayar, tarif **{format_rupiah(tarif)}**, "
                f"dan target realisasi **{target_realisasi:.0f}%**."
            )

            # --- Tabel potensi & rekomendasi per lokasi ---
            st.markdown("### 📍 Potensi & Rekomendasi Target Retribusi per Lokasi")
            st.dataframe(
                df_potensi[[
                    "Kecamatan", "Kelurahan", "Lokasi",
                    "RataRataParkir", "Kendaraan Membayar / Hari",
                    "Potensi Harian (Rp)", "Target Harian (Rp)",
                    "Potensi Bulanan (Rp)", "Target Bulanan (Rp)",
                    "Potensi Tahunan (Rp)", "Target Tahunan (Rp)"
                ]],
                use_container_width=True
            )

            # --- Agregasi per kelurahan ---
            df_kelurahan = df_potensi.groupby(["Kecamatan", "Kelurahan"], as_index=False)[
                ["RataRataParkir", "Kendaraan Membayar / Hari",
                 "Potensi Harian (Rp)", "Potensi Bulanan (Rp)", "Potensi Tahunan (Rp)",
                 "Target Harian (Rp)", "Target Bulanan (Rp)", "Target Tahunan (Rp)"]
            ].sum()

            st.markdown("### 🏘️ Potensi & Rekomendasi Target Retribusi per Kelurahan")
            st.dataframe(df_kelurahan, use_container_width=True)

            # --- Grafik ringkas per kelurahan ---
            st.markdown("### 📊 Grafik Potensi Harian per Kelurahan")
            st.bar_chart(
                df_kelurahan.set_index("Kelurahan")["Potensi Harian (Rp)"]
            )

            st.markdown("### 🎯 Grafik Target Harian per Kelurahan")
            st.bar_chart(
                df_kelurahan.set_index("Kelurahan")["Target Harian (Rp)"]
            )

            with st.expander("📝 Interpretasi Singkat (Per Kelurahan & Lokasi)", expanded=False):
                st.write(
                    """
- Tabel **per lokasi** menunjukkan potensi dan target untuk tiap titik parkir.
- Tabel **per kelurahan** menjumlahkan seluruh lokasi di kelurahan tersebut.
- Nilai **target** dihitung sebagai persentase dari potensi (misalnya 80%).
- Kelurahan dengan potensi dan target terbesar dapat dijadikan **prioritas pengawasan dan optimalisasi**.
"""
                )

# ---------- TAB AI ----------
with tab_ai:
    st.subheader("🤖 Pengelompokan Titik Parkir dengan Kecerdasan Buatan (K-Means)")

    if uploaded_file is None:
        st.info("Upload dulu file Excel di sidebar untuk menjalankan analisis AI.")
    else:
        _, df_titik = load_excel_titik_parkir(uploaded_file)

        if df_titik is not None and not df_titik.empty:
            df_cluster, centers = buat_cluster_ai(df_titik, n_clusters=3)

            if df_cluster is not None:
                st.write(
                    "Model K-Means mengelompokkan titik parkir menjadi tiga kategori "
                    "berdasarkan **RataRataParkir**: **Rendah**, **Sedang**, dan **Tinggi**."
                )

                show_cols = [
                    "Jenis", "Kecamatan", "Kelurahan", "Lokasi",
                    "RataRataParkir", "Kategori_AI"
                ]
                st.dataframe(df_cluster[show_cols], use_container_width=True)

                tab_g1, tab_g2 = st.tabs(
                    ["📈 Distribusi Rata-rata Parkir", "📊 Jumlah Titik per Kategori AI"]
                )

                with tab_g1:
                    st.bar_chart(df_cluster["RataRataParkir"])

                with tab_g2:
                    kategori_counts = df_cluster["Kategori_AI"].value_counts().sort_index()
                    st.bar_chart(kategori_counts)

                centers_sorted = sorted(list(centers))
                with st.expander("📌 Pusat Cluster (Interpretasi AI)", expanded=True):
                    st.markdown(
                        f"""
- **Kategori Rendah**  ≈ {centers_sorted[0]:.1f} kendaraan per titik  
- **Kategori Sedang**  ≈ {centers_sorted[1]:.1f} kendaraan per titik  
- **Kategori Tinggi**  ≈ {centers_sorted[2]:.1f} kendaraan per titik  

Titik parkir yang termasuk kategori **Tinggi** dapat diprioritaskan dalam:
- Pengawasan petugas,
- Penambahan fasilitas parkir,
- Atau penyesuaian kebijakan tarif.
"""
                    )

# ---------- TAB TENTANG ----------
with tab_tentang:
    st.subheader("ℹ️ Tentang Metode & Konsep")

    st.markdown(
        """
### 1. Data Makro Kota
- Menggunakan total kendaraan roda dua dan roda empat di Kota Cilegon.
- Tidak semua kendaraan diasumsikan membayar retribusi, sehingga digunakan parameter
  **persentase kendaraan yang membayar** (misal 25%).
- Potensi pendapatan dihitung dengan rumus:
  
  > Potensi Harian = (Total Kendaraan × Persentase Membayar × Tarif Rata-rata)

---

### 2. Data Mikro Titik Parkir (Excel)
- Menggunakan file Excel berisi titik retribusi parkir dengan kolom:
  `No, Jenis, Kecamatan, Kelurahan, Lokasi, RATA-RATA YANG PARKIR`.
- Kolom **RATA-RATA YANG PARKIR** merepresentasikan rata-rata kendaraan yang parkir di titik tersebut per hari.
- Dari sini dapat dihitung **potensi & target** per lokasi dan per kelurahan.

---

### 3. Kecerdasan Buatan (K-Means Clustering)
- **K-Means** adalah algoritma _unsupervised learning_ (pembelajaran tanpa label) yang bertujuan mengelompokkan data ke dalam *k* cluster.
- Dalam aplikasi ini:
  - Data yang digunakan: nilai **RataRataParkir** tiap titik.
  - Nilai tersebut dikelompokkan menjadi 3 kategori:
    - Cluster dengan rata-rata terendah → **Rendah**
    - Cluster nilai tengah → **Sedang**
    - Cluster dengan rata-rata tertinggi → **Tinggi**
- Hasilnya membantu memberikan:
  - Prioritas pengelolaan titik parkir,
  - Dasar perencanaan kebijakan peningkatan retribusi,
  - Insight untuk pemetaan titik parkir yang potensial.

---

### 4. Rekomendasi Target Retribusi
- Potensi menunjukkan **kemampuan maksimum teoritis**.
- Pemerintah biasanya menetapkan **target** di bawah potensi (misalnya 70–90%).
- Di aplikasi ini, target dapat diatur melalui parameter **Target Realisasi (%)** di sidebar,
  dan otomatis dibagi:
  - **Per kota (makro)**
  - **Per kelurahan**
  - **Per lokasi**

---

### 5. Pengembangan Lanjutan
- Menambahkan variabel lain (jenis kawasan, waktu, hari kerja/libur).
- Menggunakan model prediktif (regresi, time series).
- Integrasi dengan sistem pembayaran elektronik atau data real-time.
"""
    )
