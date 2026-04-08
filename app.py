import streamlit as st
import pandas as pd
from datetime import datetime

# Sayfa Ayarları
st.set_page_config(page_title="HASAT v4.1 | Akreditasyon Analiz", layout="wide")

# --- ÜST BAŞLIK VE PROJE SORUMLUSU ---
st.title("🌾 HASAT v4.1")
st.subheader("Hesaplamalı Akreditasyon Sistemi ve Analiz Tabanı")
st.markdown("### **Proje Yürütücüsü: Doç. Dr. İbrahim Çelik**")
st.markdown("*PAÜ Çal MYO - Dijital Tarım Teknolojileri*")
st.divider()

# --- DERS VE AKREDİTASYON GİRİŞ ALANLARI ---
st.markdown("### 📋 Rapor Bilgileri")
col1, col2 = st.columns(2)
with col1:
    ders_adi = st.text_input("Dersin Adı", placeholder="Örn: Bitki Islahı")
    sinav_turu = st.selectbox("Sınav Türü", ["Ara Sınav (Vize)", "Yarıyıl Sonu (Final)", "Bütünleme", "Ödev / Proje"])
    olcme_araci = st.selectbox("Ölçme Aracı (Değerlendirme Yöntemi)", ["Çoktan Seçmeli Test", "Klasik Yazılı", "Uygulama Rubriği", "Laboratuvar Raporu", "Karma"])
with col2:
    ogretim_elemani = st.text_input("Dersi Veren Öğretim Elemanı", placeholder="Adınızı ve Soyadınızı Yazınız")
    donem = st.text_input("Eğitim-Öğretim Yılı ve Dönemi", placeholder="Örn: 2025-2026 Güz")
    eylem_plani = st.text_area("İyileştirme Önerisi / Eylem Planı (PUKÖ Döngüsü)", 
                               placeholder="Hedefin altında kalan kazanımlar için seneye alınacak önlemi buraya yazınız...", height=110)

st.divider()

# --- DOSYA YÜKLEME ---
uploaded_file = st.file_uploader("Lütfen Excel Şablonunuzu Yükleyin", type=["xlsx", "xls"])

if uploaded_file is not None:
    try:
        df_notlar = pd.read_excel(uploaded_file, sheet_name='Notlar')
        df_sorular = pd.read_excel(uploaded_file, sheet_name='Sorular')
        df_matris = pd.read_excel(uploaded_file, sheet_name='Matris')
    except Exception as e:
        st.error("HATA: Excel sayfaları (Notlar, Sorular, Matris) bulunamadı veya dosya formatı hatalı.")
        st.stop()

    # Veri Hazırlığı
    ogrenciler = df_notlar.to_dict('records')
    soru_basliklari = [s for s in df_notlar.columns if "Soru" in s]
    
    # Genel Sınıf Ortalaması Hesabı
    df_notlar['Toplam_Puan'] = df_notlar[soru_basliklari].sum(axis=1)
    sinif_ortalamasi = df_notlar['Toplam_Puan'].mean()

    # Sorular ve Matris Sözlüklerini Oluşturma
    sorular = {row['Soru']: {'ok': row['ÖK'], 'tam_puan': row['Tam Puan'], 'baraj': row['Baraj']} for _, row in df_sorular.iterrows()}
    ok_py_matrisi = {row['ÖK']: {py: row[py] for py in df_matris.columns if py != 'ÖK'} for _, row in df_matris.iterrows()}

    # --- RAPOR ÇIKTISI ---
    st.markdown("---")
    st.markdown("<h2 style='text-align: center; color: #2c3e50;'>📄 DERS DEĞERLENDİRME VE ANALİZ RAPORU</h2>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        st.write(f"**Dersin Adı:** {ders_adi}")
        st.write(f"**Öğretim Elemanı:** {ogretim_elemani}")
    with c2:
        st.write(f"**Sınav Türü:** {sinav_turu}")
        st.write(f"**Ölçme Aracı:** {olcme_araci}")
    with c3:
        st.write(f"**Dönem:** {donem}")
        st.write(f"**Sınıf Ortalaması:** <span style='color:red; font-weight:bold;'>{round(sinif_ortalamasi, 2)}</span>", unsafe_allow_html=True)

    st.divider()

    # 1. Aşama: Soru Bazlı Analiz
    st.subheader("1. Soru Bazlı Başarı Analizi")
    soru_data = []
    ok_basarilari = {}
    ok_sayaci = {}

    for s_id, d in sorular.items():
        if s_id in df_notlar.columns:
            # Barajı geçen öğrenci sayısı
            basarili_sayisi = sum(1 for ogr in ogrenciler if pd.notna(ogr[s_id]) and ogr[s_id] >= (d['tam_puan'] * d['baraj']))
            oran = basarili_sayisi / len(ogrenciler) if len(ogrenciler) > 0 else 0
            
            soru_data.append({
                "Soru": s_id, 
                "İlgili Kazanım": d['ok'], 
                "Başarı Oranı (%)": round(oran * 100, 1)
            })
            
            # Kazanım başarılarını toplama
            ok_basarilari[d['ok']] = ok_basarilari.get(d['ok'], 0) + oran
            ok_sayaci[d['ok']] = ok_sayaci.get(d['ok'], 0) + 1
            
    st.table(pd.DataFrame(soru_data))

    # 2. Aşama: ÖK Başarıları
    st.subheader("2. Öğrenme Kazanımı (ÖK) Genel Başarı Oranları")
    ok_final = []
    for ok in ok_basarilari:
        # Kazanım ortalamasını al
        ok_basarilari[ok] /= ok_sayaci[ok]
        ok_final.append({
            "Öğrenme Kazanımı": ok, 
            "Genel Başarı (%)": round(ok_basarilari[ok] * 100, 1)
        })
    st.table(pd.DataFrame(ok_final))

    # 3. Aşama: PY Sağlama Düzeyleri (Ağırlıklı Ortalama)
    st.subheader("3. Program Yeterliliği (PY) Sağlama Düzeyleri")
    py_data = []
    py_sutunlari = [c for c in df_matris.columns if c != 'ÖK']
    
    for py in py_sutunlari:
        pay, payda = 0, 0
        for ok, oran in ok_basarilari.items():
            katki = ok_py_matrisi.get(ok, {}).get(py, 0)
            if pd.notna(katki) and katki > 0:
                pay += (oran * katki)
                payda += katki
        
        py_skor = (pay / payda) if payda > 0 else 0
        py_data.append({
            "Program Yeterliliği": py, 
            "Sağlama Düzeyi (%)": round(py_skor * 100, 1)
        })
    st.table(pd.DataFrame(py_data))

    # --- PUKÖ VE İMZA ---
    st.divider()
    st.subheader("📝 İyileştirme Planı ve Değerlendirme (PUKÖ)")
    if eylem_plani:
        st.info(eylem_plani)
    else:
        st.warning("Bu sınav değerlendirmesi için iyileştirme planı belirtilmemiştir.")
    
    st.write("<br><br>", unsafe_allow_html=True)
    f1, f2 = st.columns([2, 1])
    with f1:
        st.write(f"**Rapor Tarihi:** {datetime.now().strftime('%d.%m.%Y')}")
    with f2:
        st.write("**Onay / İmza**")
        st.write(f"<br><br><strong>{ogretim_elemani}</strong>", unsafe_allow_html=True)

    st.success("✅ Analiz başarıyla tamamlandı. Tabloları seçerek kopyalayabilir ve kanıt dosyanıza ekleyebilirsiniz.")