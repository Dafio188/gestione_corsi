import sqlite3

def add_corso_id_column():
    try:
        # Connetti al database
        conn = sqlite3.connect('gestione_corsi.db')
        cursor = conn.cursor()

        # Verifica se la colonna corso_id esiste già
        cursor.execute("PRAGMA table_info(disponibilita_docente);")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]

        if 'corso_id' not in column_names:
            # Aggiungi la colonna corso_id
            cursor.execute('ALTER TABLE disponibilita_docente ADD COLUMN corso_id INTEGER REFERENCES corso(id);')
            conn.commit()
            print('Colonna corso_id aggiunta con successo!')
        else:
            print('La colonna corso_id esiste già.')

        conn.close()
        return True
    except Exception as e:
        print(f'Errore durante l\'aggiunta della colonna: {str(e)}')
        return False

if __name__ == '__main__':
    add_corso_id_column() 