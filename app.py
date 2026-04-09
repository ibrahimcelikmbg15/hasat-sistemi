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
        py_final_data.append({"Yeterlilik": py, "Sağlama %": round((pay/payda)*100, 1) if payda > 0 else 0})
    df_py_sonuc = pd.DataFrame(py_final_data)

    # --- RAPOR ÇIKTISI ---
    st.markdown("---")
    st.markdown(f"<h2 style='text-align: center; color: #2c3e50;'>📄 DERS DEĞERLENDİRME VE ANALİZ RAPORU</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Ders:** {ders_adi}")
        st.write(f"**Öğretim Elemanı:** {ogretim_elemani}")
    with c2:
        st.write(f"**Sınav:** {sinav_turu}")
        st.write(f"**Yöntem:** {olcme_araci}")
    with c3:
        st.write(f"**Dönem:** {donem}")
        st.write(f"**Sınıf Ortalaması:** <span style='color:red; font-weight:bold;'>{round(sinif_ort, 2)}</span>", unsafe_allow_html=True)

    st.divider()

    st.subheader("1. Soru Bazlı Başarı Analizi")
    st.table(pd.DataFrame(soru_analiz_data))

    st.subheader("2. Kazanım ve Yeterlilik Özet Tabloları")
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.table(df_ok_sonuc)
    with t_col2:
        st.table(df_py_sonuc)

    st.subheader("3. Görsel Yetkinlik Analizi (Radar)")
    g_col1, g_col2 = st.columns(2)

    with g_col1:
        st.write("**Öğrenme Kazanımları (ÖK) Profili**")
        fig_ok = go.Figure(data=go.Scatterpolar(r=df_ok_sonuc['Başarı %'], theta=df_ok_sonuc['Kazanım'], fill='toself', name='Başarı %'))
        fig_ok.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_ok, use_container_width=True)

    with g_col2:
        st.write("**Program Yeterlilikleri (PY) Profili**")
        fig_py = go.Figure(data=go.Scatterpolar(r=df_py_sonuc['Sağlama %'], theta=df_py_sonuc['Yeterlilik'], fill='toself', fillcolor='rgba(255, 0, 0, 0.3)', line=dict(color='red'), name='Sağlama %'))
        fig_py.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False)
        st.plotly_chart(fig_py, use_container_width=True)

    st.divider()
    st.subheader("📝 İyileştirme Planı (PUKÖ)")
    st.info(eylem_plani if eylem_plani else "Sürekli iyileştirme planı belirtilmemiştir.")
    
    st.write("<br><br>", unsafe_allow_html=True)
    f1, f2 = st.columns([2, 1])
    with f1:
        st.write(f"**Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y')}")
    with f2:
        st.write("**İmza / Onay**")
        st.write(f"<br><strong>{ogretim_elemani}</strong>", unsafe_allow_html=True)

    st.success("✅ Analiz başarıyla tamamlandı. Raporu kopyalayarak dosyalarınıza ekleyebilirsiniz.")