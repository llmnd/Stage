import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Supprimer les tables si elles existent
tables = [
    'stages_offredestage',
    'stages_profilentreprise',
    'stages_userprofile'
]

for table in tables:
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {table};")
        print(f"✅ Table supprimée : {table}")
    except Exception as e:
        print(f"❌ Erreur pour {table} : {e}")

conn.commit()
conn.close()
