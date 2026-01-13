import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
from PIL import Image

# --- CONFIG & SETUP ---
st.set_page_config(page_title="Sunday Volley Stars", layout="wide")

if not os.path.exists("uploads"):
    os.makedirs("uploads")

# Fungsi untuk mengubah gambar lokal ke format yang bisa dibaca HTML
def get_image_base64(path):
    with open(path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode()
    return f"data:image/png;base64,{encoded_string}"

# --- DATABASE ---
conn = sqlite3.connect('voli_v3.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS pemain 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, nama TEXT, posisi TEXT, 
              img_path TEXT, total_skor REAL DEFAULT 0, jumlah_rating INTEGER DEFAULT 0, 
              rating_rata_rata REAL DEFAULT 0)''')
conn.commit()

# --- CSS CUSTOM (WARNA TEKS DIPERBAIKI) ---
st.markdown("""
    <style>
    /* Mengatur agar teks di dalam kartu selalu berwarna gelap */
    .player-card {
        background-color: #ffffff !important;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 1px solid #ddd;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 25px;
    }
    .player-card h3 {
        color: #111111 !important; /* Nama Pemain Hitam Pekat */
        margin: 10px 0 5px 0 !important;
    }
    .posisi-text { 
        color: #444444 !important; /* Posisi Abu Gelap */
        font-size: 0.9em; 
        margin-bottom: 5px; 
    }
    .penilai-text {
        color: #888888 !important; /* Jumlah Penilai Abu Terang */
        font-size: 0.8em;
    }
    .player-img {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #FF4B4B;
    }
    .rating-badge {
        background-color: #FF4B4B;
        color: white !important;
        padding: 4px 12px;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1.1em;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.title("🏐 Volley Rank")
    menu = st.radio("Menu:", ["🏆 Leaderboard", "⭐ Beri Rating", "⚙️ Kelola Pemain"])

# --- MENU 1: LEADERBOARD ---
if menu == "🏆 Leaderboard":
    st.title("🏆 Player Rankings")
    df = pd.read_sql_query("SELECT * FROM pemain ORDER BY rating_rata_rata DESC", conn)
    
    if df.empty:
        st.warning("Belum ada data pemain.")
    else:
        cols = st.columns(4)
        for index, row in df.iterrows():
            with cols[index % 4]:
                if row['img_path'] and os.path.exists(row['img_path']):
                    img_src = get_image_base64(row['img_path'])
                else:
                    img_src = "https://www.w3schools.com/howto/img_avatar.png"
                
                st.markdown(f"""
                <div class="player-card">
                    <img src="{img_src}" class="player-img">
                    <h3>{row['nama']}</h3>
                    <p class="posisi-text">{row['posisi']}</p>
                    <div style="margin: 10px 0;">
                        <span class="rating-badge">{row['rating_rata_rata']} ⭐</span>
                    </div>
                    <p class="penilai-text">{int(row['jumlah_rating'])} Penilai</p>
                </div>
                """, unsafe_allow_html=True)

# --- MENU 2 & 3 (Sama seperti sebelumnya) ---
elif menu == "⭐ Beri Rating":
    st.title("⭐ Kasih Rating")
    df_p = pd.read_sql_query("SELECT id, nama FROM pemain", conn)
    if df_p.empty:
        st.error("Tambahkan pemain terlebih dahulu!")
    else:
        with st.form("rating_form"):
            target_nama = st.selectbox("Siapa yang mau dinilai?", df_p['nama'])
            skor = st.select_slider("Berikan Skor Performa", options=[1, 2, 3, 4, 5], value=3)
            submit = st.form_submit_button("Kirim Rating")
            if submit:
                p_id = int(df_p[df_p['nama'] == target_nama]['id'].iloc[0])
                c.execute("SELECT total_skor, jumlah_rating FROM pemain WHERE id=?", (p_id,))
                data = c.fetchone()
                new_total = data[0] + skor
                new_count = data[1] + 1
                new_avg = round(new_total / new_count, 2)
                c.execute("UPDATE pemain SET total_skor=?, jumlah_rating=?, rating_rata_rata=? WHERE id=?",
                          (new_total, new_count, new_avg, p_id))
                conn.commit()
                st.success(f"Berhasil menilai {target_nama}!")
                st.rerun()

elif menu == "⚙️ Kelola Pemain":
    st.title("⚙️ Manajemen Pemain")
    tab1, tab2 = st.tabs(["Tambah", "Hapus"])
    with tab1:
        with st.form("add_p", clear_on_submit=True):
            n = st.text_input("Nama")
            p = st.selectbox("Posisi", ["Spiker", "Setter", "Libero", "Opposite", "MB"])
            up = st.file_uploader("Foto", type=['jpg','png','jpeg'])
            if st.form_submit_button("Simpan"):
                path = ""
                if up:
                    path = f"uploads/{n.replace(' ','_').lower()}.png"
                    with open(path, "wb") as f: f.write(up.getbuffer())
                c.execute("INSERT INTO pemain (nama, posisi, img_path) VALUES (?,?,?)",(n, p, path))
                conn.commit()
                st.success("Tersimpan!")
                st.rerun()
    with tab2:
        df_del = pd.read_sql_query("SELECT nama FROM pemain", conn)
        if not df_del.empty:
            h = st.selectbox("Hapus Pemain", df_del['nama'])
            if st.button("Hapus Permanen"):
                c.execute("DELETE FROM pemain WHERE nama=?", (h,))
                conn.commit()
                st.rerun()