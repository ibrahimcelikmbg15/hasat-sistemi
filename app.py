import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="HASAT v4.2 | Konsept Tasarım: İbrahim Çelik", layout="wide")

# --- ÜST BAŞLIK VE KONSEPT TASARIM ---
st.title("🌾 HASAT v4.2")
st.subheader("Hesaplamalı Akreditasyon Sistemi ve Analiz Tabanı")
st.markdown("### **Konsept Tasarım: Doç. Dr. İbrahim Çelik**")
st.markdown("*PAÜ Çal MYO - Dijital Tarım Teknolojileri*")
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
    eylem_plani = st.text_area("İyileştirme Planı (PUKÖ)", placeholder="İyileştirme önerilerinizi buraya yazınız...", height=110)

st.divider()

uploaded_file = st.file_uploader("Excel Şablonunuzu Yükleyin", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_notlar = pd.read_excel(uploaded_file, sheet_name='Notlar')
        df_sorular = pd.read_excel(uploaded_file, sheet_name='Sorular')
        df_matris = pd.read_excel(uploaded_file, sheet_name='Matris')
    except:
        st.error("HATA: Excel sayfaları (Notlar, Sorular, Matris) bulunamadı!")
        st.stop()

    # --- VERİ İŞLEME VE HESAPLAMA ---
    ogrenciler = df_notlar.to_dict('records')
    soru_basliklari = [s for s in df_notlar.columns if "Soru" in s]
    df_notlar['Toplam'] = df_notlar[soru_basliklari].sum(axis=1)
    sinif_ort = df_notlar['Toplam'].mean()

    sorular = {row['Soru']: {'ok': row['ÖK'], 'tam_puan': row['Tam Puan'], 'baraj': row['Baraj']} for _, row in df_sorular.iterrows()}
    ok_py_matrisi = {row['ÖK']: {py: row[py] for py in df_matris.columns if py != 'ÖK'} for _, row in df_matris.iterrows()}

    soru_analiz_data = []
    ok_basarilari, ok_sayaci = {}, {}

    for s_id, d in sorular.items():
        if s_id in df_notlar.columns:
            basarili = sum(1 for o in ogrenciler if pd.notna(o[s_id]) and o[s_id] >= (d['tam_puan'] * d['baraj']))
            oran = basarili / len(ogrenciler) if len(ogrenciler) > 0 else 0
            
            soru_analiz_data.append({
                "Soru": s_id, 
                "İlgili ÖK": d['ok'], 
                "Baraj Puan": d['tam_puan'] * d['baraj'],
                "Başarı %": round(oran * 100, 1)
            })
            
            ok_basarilari[d['ok']] = ok_basarilari.get(d['ok'], 0) + oran
            ok_sayaci[d['ok']] = ok_sayaci.get(d['ok'], 0) + 1

    df_ok_sonuc = pd.DataFrame([{"Kazanım": ok, "Başarı %": round((v/ok_sayaci[ok])*100, 1)} for ok, v in ok_basarilari.items()])
    
    py_final_data = []
    for py in [c for c in df_matris.columns if c != 'ÖK']:
        pay, payda = 0, 0
        for ok, v in ok_basarilari.items():
            oran = v / ok_sayaci[ok]
            katki = ok_py_matrisi.get(ok, {}).get(py, 0)
            if pd.notna(katki) and katki > 0:
                pay += (oran * katki)
                payda += katki
        py_final_data.append({"Yeterlilik": py, "Sağlama %": round((pay/payda)*100, 1) if payda