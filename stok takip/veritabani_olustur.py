import sqlite3

conn = sqlite3.connect('stok.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS urunler (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad TEXT NOT NULL,
    kategori TEXT NOT NULL,
    miktar INTEGER NOT NULL,
    fiyat REAL NOT NULL
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS depo_hareketleri (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    urun_id INTEGER NOT NULL,
    hareket_tipi TEXT NOT NULL,
    miktar INTEGER NOT NULL,
    tarih TEXT NOT NULL,
    FOREIGN KEY (urun_id) REFERENCES urunler(id)
)
''')

conn.commit()
conn.close()
print("Veritabanı oluşturuldu.")
