# 📊 Brazilian E-Commerce Dashboard

Dashboard interaktif untuk analisis dataset publik E-Commerce Brazil (Olist) menggunakan **Streamlit**, **Pandas**, dan **Plotly**.

---

## 📝 Deskripsi
Dashboard ini menampilkan:
- **Overview**: Total customers, total orders, total revenue
- **Product Analysis**: Top 10 products by revenue
- **Payment Analysis**: Distribusi metode pembayaran
- **Delivery Status**: Persentase on-time vs late
- **Customer Geography**: Peta pelanggan berdasarkan lokasi
- **Review Analysis**: Distribusi review score pelanggan

---

## 💻 Instalasi dan Jalankan
1. Clone repository:
```bash
git clone https://github.com/halilanisa/Proyek-Belajar-Fundamental-Analisis-Data-Dicoding.git
cd Proyek-Belajar-Fundamental-Analisis-Data-Dicoding
```
2. Buat virtual environment (opsional tapi disarankan):
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. Install dependencies:
```
pip install -r requirements.txt
```
4. Jalankan Streamlit:
```
streamlit run Dashboard.py
