from app import db

class Produk(db.Model): # Atau MenuItem, dll.
    __tablename__ = 'produk' # Atau menu_items, dll.

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    deskripsi = db.Column(db.Text, nullable=True)
    harga = db.Column(db.Float, nullable=False)

    def __init__(self, nama, deskripsi, harga):
        self.nama = nama
        self.deskripsi = deskripsi
        self.harga = harga

    def serialize(self):
        return {
            'id': self.id,
            'nama': self.nama,
            'deskripsi': self.deskripsi,
            'harga': self.harga
        }

    def __repr__(self):
        return f'<Produk {self.nama}>'