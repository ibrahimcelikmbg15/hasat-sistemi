import streamlit as st
import pandas as pd
import io

# Sayfa Ayarları
st.set_page_config(page_title="HASAT v3.0 | Dijital Tarım", layout="wide")

st.title("🌾 HASAT v3.0")
st.subheader("Hesaplamalı Akreditasyon Sistemi ve Analiz Tabanı")
st.markdown("**PAÜ Çal MYO - Dijital Tarım Teknolojileri | Geliştirici: Doç. Dr. İbrahim Çelik**")
st.divider()

st.info("Lütfen içinde 'Notlar', 'Sorular' ve 'Matris' sekmeleri olan Excel şablonunuzu yükleyin.")

# Dosya Yükleme Aracı
uploaded_file = st.file_uploader("Excel Dosyası Seçin", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_notlar = pd.read_excel(uploaded_file, sheet_name='Notlar')
        df_sorular = pd.read_excel(uploaded_file, sheet_name='Sorular')
        df_matris = pd.read_excel(uploaded_file, sheet_name='Matris')
        st.success(f"Dosya başarıyla yüklendi! {len(df_notlar)} öğrencinin verisi işleniyor...")
    except Exception as e:
        st.error(f"HATA: Excel dosyanızda sekmeler eksik veya hatalı. Detay: {e}")
        st.stop()

    # Veri Hazırlığı
    ogrenciler = df_notlar.to_dict('records')
    
    sorular = {}
    for index, row in df_sorular.iterrows():
        sorular[row['Soru']] = {
            'ok': row['ÖK'],
            'tam_puan': row['Tam Puan'],
            'baraj': row['Baraj']
        }

    ok_py_matrisi = {}
    py_listesi = [col for col in df_matris.columns if col != 'ÖK']
    for index, row in df_matris.iterrows():
        ok_py_matrisi[row['ÖK']] = {py: row[py] for py in py_listesi}

    # Hesaplama Motoru
    toplam_ogrenci = len(ogrenciler)
    ok_basari_oranlari = {}
    ok_soru_sayilari = {}
    
    st.subheader("1. Aşama: Soru Bazlı Sınıf Başarı Analizi")
    soru_sonuclari = []

    for soru_id, detay in sorular.items():
        if soru_id not in df_notlar.columns:
            continue 
            
        gecme_notu = detay['tam_puan'] * detay['baraj']
        basarili_ogrenci_sayisi = sum(1 for ogr in ogrenciler if pd.notna(ogr[soru_id]) and ogr[soru_id] >= gecme_notu)
                
        soru_basari_orani = basarili_ogrenci_sayisi / toplam_ogrenci
        ilgili_ok = detay['ok']
        
        if ilgili_ok in ok_basari_oranlari:
            ok_basari_oranlari[ilgili_ok] += soru_basari_orani
            ok_soru_sayilari[ilgili_ok] += 1
        else:
            ok_basari_oranlari[ilgili_ok] = soru_basari_orani
            ok_soru_sayilari[ilgili_ok] = 1
            
        soru_sonuclari.append({
            "Soru": soru_id,
            "İlgili ÖK": ilgili_ok,
            "Baraj Puanı": gecme_notu,
            "Sınıf Başarısı (%)": round(soru_basari_orani * 100, 1)
        })
        
    st.table(pd.DataFrame(soru_sonuclari))

    st.subheader("2. Aşama: Öğrenme Kazanımı (ÖK) Genel Başarı Oranları")
    ok_sonuclari = []
    for ok, toplam_oran in ok_basari_oranlari.items():
        ok_basari_oranlari[ok] = toplam_oran / ok_soru_sayilari[ok]
        ok_sonuclari.append({
            "Öğrenme Kazanımı": ok,
            "Genel Başarı Oranı (%)": round(ok_basari_oranlari[ok] * 100, 1)
        })
    st.table(pd.DataFrame(ok_sonuclari))

    st.subheader("3. Aşama: MEDEK/KAVDEM Yeterlilik (PY) Sağlama Düzeyleri")
    py_sonuclari = []
    
    for py_id in py_listesi:
        pay_toplami = 0
        payda_toplami = 0
        
        for ok_id, oran in ok_basari_oranlari.items():
            if ok_id in ok_py_matrisi and py_id in ok_py_matrisi[ok_id]:
                matris_degeri = ok_py_matrisi[ok_id][py_id]
                pay_toplami += (oran * matris_degeri)
                payda_toplami += matris_degeri
            
        py_nihai_skor = pay_toplami / payda_toplami if payda_toplami > 0 else 0
        py_sonuclari.append({
            "Program Yeterliliği": py_id,
            "Sağlama Düzeyi (%)": round(py_nihai_skor * 100, 1)
        })
        
    st.dataframe(pd.DataFrame(py_sonuclari), use_container_width=True)
    st.success("✅ KAVDEM Analizi başarıyla tamamlandı. Tabloyu seçerek Word'e veya Excel'e kopyalayabilirsiniz.")