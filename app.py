import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="HASAT v4.2 | Görsel Akreditasyon", layout="wide")

# --- ÜST BAŞLIK ---
st.title("🌾 HASAT v4.2")
st.subheader("Hesaplamalı Akreditasyon Sistemi ve Analiz Tabanı")
st.markdown("### **Proje Yürütücüsü: Doç. Dr. İbrahim Çelik**")
st.divider()

# --- RAPOR BİLGİLERİ GİRİŞİ ---
st.markdown("### 📋 Rapor Bilgileri")
col1, col2 = st.columns(2)
with col1:
    ders_adi = st.text_input("Dersin Adı", placeholder="Örn: Bitki Islahı")
    sinav_turu = st.selectbox("Sınav Türü", ["Ara Sınav (Vize)", "Yarıyıl Sonu (Final)", "Bütünleme", "Ödev / Proje"])
    olcme_araci = st.selectbox("Ölçme Aracı", ["Çoktan Seçmeli Test", "Klasik Yazılı", "Uygulama Rubriği", "Laboratuvar Raporu", "Karma"])
with col2:
    ogretim_elemani = st.text_input("Dersi Veren Öğretim Elemanı", placeholder="Adınızı Yazınız")
    donem = st.text_input("Dönem", placeholder="Örn: 2025-2026 Güz")
    eylem_plani = st.text_area("İyileştirme Planı (PUKÖ)", height=110)

st.divider()

uploaded_file = st.file_uploader("Excel Şablonunuzu Yükleyin", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_notlar = pd.read_excel(uploaded_file, sheet_name='Notlar')
        df_sorular = pd.read_excel(uploaded_file, sheet_name='Sorular')
        df_matris = pd.read_excel(uploaded_file, sheet_name='Matris')
    except:
        st.error("HATA: Excel sayfaları eksik!")
        st.stop()

    # Veri İşleme
    ogrenciler = df_notlar.to_dict('records')
    soru_basliklari = [s for s in df_notlar.columns if "Soru" in s]
    df_notlar['Toplam'] = df_notlar[soru_basliklari].sum(axis=1)
    sinif_ort = df_notlar['Toplam'].mean()

    sorular = {row['Soru']: {'ok': row['ÖK'], 'tam_puan': row['Tam Puan'], 'baraj': row['Baraj']} for _, row in df_sorular.iterrows()}
    ok_py_matrisi = {row['ÖK']: {py: row[py] for py in df_matris.columns if py != 'ÖK'} for _, row in df_matris.iterrows()}

    # Analiz Hesaplamaları
    ok_basarilari, ok_sayaci = {}, {}
    for s_id, d in sorular.items():
        if s_id in df_notlar.columns:
            basarili = sum(1 for o in ogrenciler if o[s_id] >= (d['tam_puan'] * d['baraj']))
            oran = basarili / len(ogrenciler) if len(ogrenciler) > 0 else 0
            ok_basarilari[d['ok']] = ok_basarilari.get(d['ok'], 0) + oran
            ok_sayaci[d['ok']] = ok_sayaci.get(d['ok'], 0) + 1

    ok_final_data = [{"Kazanım": ok, "Başarı %": round((v/ok_sayaci[ok])*100, 1)} for ok, v in ok_basarilari.items()]
    df_ok_sonuc = pd.DataFrame(ok_final_data)

    py_final_data = []
    for py in [c for c in df_matris.columns if c != 'ÖK']:
        pay, payda = 0, 0
        for ok, v in ok_basarilari.items():
            oran = v / ok_sayaci[ok]
            katki = ok_py_matrisi.get(ok, {}).get(py, 0)
            if pd.notna(katki) and katki > 0:
                pay += (oran * katki)
                payda += katki
        py_final_data.append({"Yeterlilik": py, "Sağlama %": round((pay/payda)*100, 1) if payda > 0 else 0})
    df_py_sonuc = pd.DataFrame(py_final_data)

    # --- GÖRSEL ANALİZLER (RADAR GRAFİKLERİ) ---
    st.markdown("### 📊 Görsel Yetkinlik Analizi")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.write("**Öğrenme Kazanımları (ÖK) Radarı**")
        fig_ok = go.Figure(data=go.Scatterpolar(r=df_ok_sonuc['Başarı %'], theta=df_ok_sonuc['Kazanım'], fill='toself', name='Başarı %'))
        fig_ok.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_ok, use_container_width=True)

    with g_col2:
        st.write("**Program Yeterlilikleri (PY) Radarı**")
        fig_py = go.Figure(data=go.Scatterpolar(r=df_py_sonuc['Sağlama %'], theta=df_py_sonuc['Yeterlilik'], fill='toself', fillcolor='rgba(255, 0, 0, 0.3)', line=dict(color='red'), name='Sağlama %'))
        fig_py.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_py, use_container_width=True)

    # --- TABLOLAR VE RAPOR ---
    st.divider()
    st.markdown(f"<h2 style='text-align: center;'>📄 DERS ANALİZ RAPORU</h2>", unsafe_allow_html=True)
    st.write(f"**Ders:** {ders_adi} | **Öğretim Elemanı:** {ogretim_elemani} | **Sınıf Ortalaması:** {round(sinif_ort, 2)}")
    
    st.subheader("1. Kazanım ve Yeterlilik Tabloları")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.table(df_ok_sonuc)
    with t_col2:
        st.table(df_py_sonuc)

    st.subheader("📝 PUKÖ İyileştirme Planı")
    st.info(eylem_plani if eylem_plani else "Plan belirtilmedi.")
    st.write(f"**Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y')} | **İmza:** {ogretim_elemani}")