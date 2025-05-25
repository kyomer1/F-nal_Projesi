from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "stok_secret"
app.config['DATABASE'] = 'stok.db'

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    db = get_db()
    kritik_urunler = db.execute("SELECT * FROM urunler WHERE miktar < 10").fetchall()
    urun_sayisi = db.execute("SELECT COUNT(*) FROM urunler").fetchone()[0]
    hareketler = db.execute("SELECT * FROM depo_hareketleri ORDER BY tarih DESC LIMIT 5").fetchall()
    return render_template('index.html', kritik_urunler=kritik_urunler, urun_sayisi=urun_sayisi, hareketler=hareketler)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['logged_in'] = True
            return redirect(url_for('index'))
        flash("Kullanıcı adı veya şifre yanlış.")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/urunler', methods=['GET', 'POST'])
def urunler():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    db = get_db()
    query = "SELECT * FROM urunler WHERE 1=1"
    params = []
    ad = request.args.get('ad', '')
    kategori = request.args.get('kategori', '')
    if ad:
        query += " AND ad LIKE ?"
        params.append(f"%{ad}%")
    if kategori:
        query += " AND kategori LIKE ?"
        params.append(f"%{kategori}%")
    urunler = db.execute(query, params).fetchall()
    return render_template('urunler.html', urunler=urunler, ad=ad, kategori=kategori)

@app.route('/urun-ekle', methods=['GET', 'POST'])
def urun_ekle():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    if request.method == 'POST':
        ad = request.form['ad']
        kategori = request.form['kategori']
        miktar = int(request.form['miktar'])
        fiyat = float(request.form['fiyat'])
        db = get_db()
        db.execute("INSERT INTO urunler (ad, kategori, miktar, fiyat) VALUES (?, ?, ?, ?)", (ad, kategori, miktar, fiyat))
        db.commit()
        return redirect(url_for('urunler'))
    return render_template('urun_ekle.html')

@app.route('/urun-sil/<int:id>')
def urun_sil(id):
    db = get_db()
    db.execute("DELETE FROM urunler WHERE id = ?", (id,))
    db.commit()
    return redirect(url_for('urunler'))

@app.route('/urun-duzenle/<int:id>', methods=['GET', 'POST'])
def urun_duzenle(id):
    db = get_db()
    urun = db.execute("SELECT * FROM urunler WHERE id = ?", (id,)).fetchone()
    if request.method == 'POST':
        ad = request.form['ad']
        kategori = request.form['kategori']
        miktar = int(request.form['miktar'])
        fiyat = float(request.form['fiyat'])
        db.execute("UPDATE urunler SET ad=?, kategori=?, miktar=?, fiyat=? WHERE id=?", (ad, kategori, miktar, fiyat, id))
        db.commit()
        return redirect(url_for('urunler'))
    return render_template('urun_duzenle.html', urun=urun)

@app.route('/istatistikler')
def istatistikler():
    if not session.get("logged_in"):
        return redirect(url_for('login'))
    db = get_db()
    # Günlük tüketim (bugünkü çıkışlar)
    today = datetime.now().strftime("%Y-%m-%d")
    gunluk_tuketim = db.execute("SELECT SUM(miktar) as toplam FROM depo_hareketleri WHERE hareket_tipi='cikis' AND tarih LIKE ?", (f"{today}%",)).fetchone()["toplam"] or 0
    # Haftalık dolum (son 7 gün girişler)
    haftalik_giris = db.execute("SELECT SUM(miktar) as toplam FROM depo_hareketleri WHERE hareket_tipi='giris' AND tarih >= date('now', '-7 days')").fetchone()["toplam"] or 0
    # Kritik stokta olan ürünler
    kritik_urunler = db.execute("SELECT * FROM urunler WHERE miktar < 10").fetchall()
    return render_template('istatistikler.html', gunluk_tuketim=gunluk_tuketim, haftalik_giris=haftalik_giris, kritik_urunler=kritik_urunler)

@app.route('/hareket-ekle/<int:id>', methods=['GET', 'POST'])
def hareket_ekle(id):
    db = get_db()
    urun = db.execute("SELECT * FROM urunler WHERE id = ?", (id,)).fetchone()
    if request.method == 'POST':
        hareket_tipi = request.form['hareket_tipi']
        miktar = int(request.form['miktar'])
        tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT INTO depo_hareketleri (urun_id, hareket_tipi, miktar, tarih) VALUES (?, ?, ?, ?)", (id, hareket_tipi, miktar, tarih))
        # Stoğu güncelle
        if hareket_tipi == "giris":
            db.execute("UPDATE urunler SET miktar = miktar + ? WHERE id = ?", (miktar, id))
        else:
            db.execute("UPDATE urunler SET miktar = miktar - ? WHERE id = ?", (miktar, id))
        db.commit()
        return redirect(url_for('urunler'))
    return render_template('hareket_ekle.html', urun=urun)
import os
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
