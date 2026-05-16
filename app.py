import streamlit as st
import google.generativeai as genai
import pulp
import json
import re
import matplotlib.pyplot as plt
import numpy as np
import base64

# ==========================================
# KONFIGURASI TAMPILAN WEBSITE
# ==========================================
st.set_page_config(page_title="Smart Solver - UM Edition", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# --- FUNGSI UNTUK BACKGROUND LOKAL ---
def add_bg_from_local(image_file):
    try:
        with open(image_file, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/{"png"};base64,{encoded_string.decode()});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
        )
    except FileNotFoundError:
        pass

add_bg_from_local('bg_um.png')

# Custom CSS
st.markdown("""
    <style>
    h1, h2, h3, h4 { color: #004a87 !important; text-shadow: 1px 1px 2px rgba(255,255,255,0.8); }
    .paper-box {
        background-color: rgba(255, 255, 255, 0.95); 
        padding: 30px; 
        border-radius: 12px; 
        box-shadow: 0 8px 16px rgba(0,74,135,0.2); 
        margin-top: 20px;
        border-left: 6px solid #fcc200;
        border-top: 2px solid #004a87;
    }
    div.stButton > button:first-child { background-color: #004a87; color: white; border: none; border-radius: 8px; }
    div.stButton > button:first-child:hover { background-color: #fcc200; color: #004a87; font-weight: bold; }
    .step-box { background-color: #eef5fb; padding: 15px; border-radius: 8px; border-left: 4px solid #004a87; margin-bottom: 15px; }
    .error-box { background-color: #fdeaea; padding: 15px; border-radius: 8px; border-left: 4px solid #d62728; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# SIDEBAR
# ==========================================
with st.sidebar:
    try:
        st.image("Logo UM.png", use_container_width=True)
    except FileNotFoundError:
        st.error("⚠️ File 'Logo UM.png' tidak ditemukan.")
    
    st.markdown("""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h3 style='color: #004a87 !important; margin-bottom: 0;'>FAKULTAS MIPA</h3>
            <p style='color: #fcc200; font-weight: bold; font-size: 1.1rem; margin-top: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);'>DEPARTEMEN MATEMATIKA</p>
        </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.title("⚙️ Pengaturan")
    user_api_key = st.text_input("🔑 Gemini API Key:", type="password")
    st.divider()
    use_integer = st.toggle("Wajibkan Bilangan Bulat", value=True)
    st.info("🧠 Model: **gemini-2.5-flash**")

# ==========================================
# FUNGSI EKSTRAKSI (LLM)
# ==========================================
def extract_linear_program(soal_cerita, api_key):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash') 
    
    prompt = f"""
    Kamu adalah asisten ahli Riset Operasi. Analisis soal cerita berikut.
    Langkah PERTAMA dan PALING PENTING: Deteksi apakah soal ini merupakan masalah Program Linear atau Non-Linear (misal mengandung variabel kuadrat/pangkat, atau perkalian antar variabel).
    
    GAYA BAHASA UNTUK 'penjelasan_langkah': 
    Tulis bagian ini seolah-olah kamu adalah seorang mahasiswa cerdas yang sedang menjelaskan cara menjawab soal secara bertahap kepada dosen. Gunakan kata "kita" dan buat kalimatnya mengalir bernalar (jangan kaku seperti buku teks). 
    Contoh: "Pertama-tama, kita misalkan dulu...", "Karena target kita adalah mencari keuntungan maksimal, maka fungsinya...", "Lalu untuk kendalanya, kita lihat batasan bahan baku di soal..."
    
    SOAL: {soal_cerita}
    
    Aturan Format JSON yang WAJIB dipatuhi:
    {{
      "is_linear": true,
      "alasan_tipe": "Jelaskan alasan tipe soal secara singkat",
      "diketahui": ["Info 1", "Info 2"],
      "dimisalkan": {{"x": "Deskripsi x", "y": "Deskripsi y"}},
      "ditanya": "Pertanyaan",
      "penjelasan_langkah": [
        "Langkah 1 (Pemisalan): Disini kita misalkan...", 
        "Langkah 2 (Fungsi Tujuan): Karena kita ingin...",
        "Langkah 3 (Fungsi Kendala): Berdasarkan soal, kita punya batasan..."
      ],
      "matematika": {{
        "variabel": ["x", "y"], 
        "tujuan": {{"tipe": "maksimasi", "koefisien": {{"x": 300000, "y": 200000}}}},
        "kendala": [
          {{"koefisien": {{"x": 4, "y": 3}}, "relasi": "<=", "nilai": 120}}
        ]
      }}
    }}
    Hanya kembalikan JSON mentah tanpa markdown.
    """
    response = model.generate_content(prompt)
    clean_text = re.sub(r'```json\n?', '', response.text)
    clean_text = re.sub(r'```\n?', '', clean_text)
    return json.loads(clean_text.strip())

# ==========================================
# TAMPILAN UTAMA
# ==========================================
st.title("🎓 Smart Solver Riset Operasi")
st.markdown("**Universitas Negeri Malang (UM) Edition** | Mengubah soal cerita menjadi solusi matematis dan grafik.")

st.markdown('<div style="background-color: rgba(255,255,255,0.85); padding: 15px; border-radius: 10px;">', unsafe_allow_html=True)
soal_input = st.text_area("📝 Ketik atau Paste Soal Cerita Di Sini:", height=150)
st.markdown('</div><br>', unsafe_allow_html=True)

if st.button("✨ Selesaikan Soal Sekarang", type="primary", use_container_width=True):
    if not user_api_key or not soal_input:
        st.warning("⚠️ Mohon pastikan API Key dan Soal sudah diisi!")
    else:
        with st.status("🤖 AI UM sedang membedah soal...", expanded=True) as status:
            try:
                st.write("🔍 Mengekstrak logika dan menganalisis tipe soal...")
                data_json = extract_linear_program(soal_input, user_api_key)
                
                # 🛑 JALUR PERPISAHAN: CEK APAKAH NON-LINEAR 🛑
                if not data_json.get("is_linear", True):
                    status.update(label="Proses dihentikan!", state="error", expanded=False)
                    st.markdown('<div class="paper-box">', unsafe_allow_html=True)
                    st.error("🛑 **OPERASI DITOLAK: TERDETEKSI MASALAH NON-LINEAR**")
                    
                    st.markdown('<div class="error-box">', unsafe_allow_html=True)
                    st.markdown(f"**Analisis AI:** {data_json.get('alasan_tipe', 'Soal mengandung elemen non-linear.')}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.info("💡 **Informasi:** Aplikasi Smart Solver ini dirancang secara khusus untuk memecahkan persamaan **Program Linear** (menggunakan library `PuLP`). Sistem tidak dapat memproses soal yang mengandung variabel berpangkat (kuadrat/kubik) atau kurva non-linear. Silakan masukkan soal yang sesuai dengan batasan sistem.")
                    st.markdown('</div>', unsafe_allow_html=True)
                    st.stop() # Menghentikan program agar tidak lanjut menghitung
                
                # JIKA LINEAR, LANJUTKAN PERHITUNGAN NORMAL
                math_data = data_json['matematika']
                
                st.write("⚙️ Menghitung solusi optimal...")
                tipe_tujuan = pulp.LpMaximize if math_data['tujuan']['tipe'] == 'maksimasi' else pulp.LpMinimize
                prob = pulp.LpProblem("Solver_RO", tipe_tujuan)
                
                var_category = pulp.LpInteger if use_integer else pulp.LpContinuous
                vars_dict = {v: pulp.LpVariable(v, lowBound=0, cat=var_category) for v in math_data['variabel']}
                
                prob += pulp.lpSum([math_data['tujuan']['koefisien'].get(v, 0) * vars_dict[v] for v in math_data['variabel']])
                for kendala in math_data['kendala']:
                    ekspresi = pulp.lpSum([kendala['koefisien'].get(v, 0) * vars_dict[v] for v in math_data['variabel']])
                    if kendala['relasi'] == '<=': prob += ekspresi <= kendala['nilai']
                    elif kendala['relasi'] == '>=': prob += ekspresi >= kendala['nilai']
                    elif kendala['relasi'] == '==': prob += ekspresi == kendala['nilai']
                
                prob.solve()
                status.update(label="Selesai! Lembar jawaban siap.", state="complete", expanded=False)
                
                # ==========================================
                # TAMPILAN LEMBAR JAWABAN BERTAHAP
                # ==========================================
                st.markdown('<div class="paper-box">', unsafe_allow_html=True)
                st.subheader("📑 Lembar Penyelesaian Langkah Demi Langkah")
                st.divider()

                # --- TAHAP 1: ANALISIS MASALAH ---
                st.markdown("### 🔹 Tahap 1: Analisis Informasi Soal")
                col_dik, col_mis = st.columns(2)
                with col_dik:
                    st.markdown("**Diketahui:**")
                    for poin in data_json['diketahui']: st.markdown(f"- {poin}")
                    st.markdown(f"**Ditanya:** *{data_json['ditanya']}*")
                with col_mis:
                    st.markdown("**Variabel Keputusan:**")
                    for var_name, desc in data_json['dimisalkan'].items(): 
                        st.markdown(f"- **{var_name}** = {desc}")
                
                st.divider()

                # --- TAHAP 2: PENJELASAN & FORMULASI MODEL ---
                st.markdown("### 🔹 Tahap 2: Formulasi Model Matematika")
                st.markdown('<div class="step-box">', unsafe_allow_html=True)
                for langkah in data_json.get('penjelasan_langkah', []):
                    st.markdown(langkah)
                st.markdown('</div>', unsafe_allow_html=True)

                Z_tipe = "Z_{max}" if math_data['tujuan']['tipe'] == "maksimasi" else "Z_{min}"
                tujuan_str = " + ".join([f"{math_data['tujuan']['koefisien'].get(v, 0)}{v}" for v in math_data['variabel']])
                
                col_math1, col_math2 = st.columns([1, 2])
                with col_math1:
                    st.markdown("**Fungsi Tujuan:**")
                    st.latex(f"{Z_tipe} = {tujuan_str}")
                with col_math2:
                    st.markdown("**Fungsi Kendala:**")
                    for kendala in math_data['kendala']:
                        kendala_str = " + ".join([f"{kendala['koefisien'].get(v, 0)}{v}" for v in math_data['variabel']])
                        relasi_simbol = "\\le" if kendala['relasi'] == "<=" else "\\ge" if kendala['relasi'] == ">=" else "="
                        st.latex(f"{kendala_str} {relasi_simbol} {kendala['nilai']}")
                    st.latex(", ".join([f"{v} \\ge 0" for v in math_data['variabel']]))

                st.divider()

                # --- TAHAP 3: EKSEKUSI GRAFIK & KESIMPULAN ---
                st.markdown("### 🔹 Tahap 3: Penyelesaian Sistem & Grafik")
                
                col_grafik, col_kesimpulan = st.columns([1.2, 1])
                
                with col_grafik:
                    if len(math_data['variabel']) == 2 and prob.status == pulp.LpStatusOptimal:
                        var_x, var_y = math_data['variabel']
                        fig, ax = plt.subplots(figsize=(6, 5))
                        
                        max_val = max([k['nilai'] for k in math_data['kendala']] + [10])
                        x_vals = np.linspace(0, max_val, 400)
                        warna = ['#004a87', '#fcc200', '#2ca02c', '#d62728']
                        
                        for idx, kendala in enumerate(math_data['kendala']):
                            a = kendala['koefisien'].get(var_x, 0)
                            b = kendala['koefisien'].get(var_y, 0)
                            c = kendala['nilai']
                            if b != 0:
                                y_vals = (c - a * x_vals) / b
                                ax.plot(x_vals, y_vals, label=f"Kendala {idx+1}", color=warna[idx % len(warna)])
                            elif a != 0:
                                ax.axvline(x=c/a, label=f"Kendala {idx+1}", color=warna[idx % len(warna)])

                        opt_x, opt_y = [v.varValue for v in prob.variables()]
                        ax.plot(opt_x, opt_y, 'ro', markersize=10, label=f'Titik Optimal ({opt_x}, {opt_y})', zorder=5)
                        
                        ax.set_xlim(0, max_val * 0.8)
                        ax.set_ylim(0, max_val * 0.8)
                        ax.set_xlabel(f"Variabel {var_x}", fontweight='bold')
                        ax.set_ylabel(f"Variabel {var_y}", fontweight='bold')
                        ax.grid(True, linestyle='--', alpha=0.6)
                        ax.legend()
                        
                        st.pyplot(fig)
                    else:
                        st.info("Visualisasi grafik hanya tersedia untuk 2 variabel (x dan y).")

                with col_kesimpulan:
                    st.markdown("#### **Titik Solusi Optimal:**")
                    if prob.status == pulp.LpStatusOptimal:
                        for v in prob.variables():
                            nilai_var = int(v.varValue) if use_integer else v.varValue
                            nama_asli = data_json['dimisalkan'].get(v.name, v.name)
                            st.success(f"**{v.name} = {nilai_var}** ({nama_asli})")
                        
                        label_hasil = "Keuntungan Maksimal" if math_data['tujuan']['tipe'] == 'maksimasi' else "Biaya Minimal"
                        nilai_hasil = f"**Rp {int(pulp.value(prob.objective)):,}**".replace(',', '.')
                        
                        st.markdown("#### **Kesimpulan Akhir:**")
                        st.info(f"Berdasarkan perhitungan optimasi, keputusan terbaik akan menghasilkan **{label_hasil} sebesar {nilai_hasil}**.")
                    else:
                        st.error("Solusi optimal tidak ditemukan. Pastikan batasan logis.")

                st.markdown('</div>', unsafe_allow_html=True)
            except Exception as e:
                status.update(label="Terjadi Kesalahan", state="error", expanded=True)
                st.error(f"Error detail: {e}")