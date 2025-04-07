# Gestione Corsi - Sistema di Gestione della Formazione

## Panoramica del Sistema

Gestione Corsi è un sistema gestionale completo progettato specificamente per la gestione di corsi di formazione nell'ambito del PNRR (Piano Nazionale di Ripresa e Resilienza). Il sistema offre una piattaforma integrata per amministratori, docenti e discenti, facilitando ogni aspetto del processo formativo.

### Funzionalità Principali

1. **Gestione Utenti Multi-Ruolo**
   - **Amministratori**: Controllo completo del sistema e monitoraggio attività
   - **Docenti**: Gestione corsi, disponibilità e materiali didattici
   - **Discenti**: Accesso ai corsi, materiali e attestati

2. **Gestione Corsi e Progetti**
   - Creazione e organizzazione progetti formativi
   - Gestione dettagliata dei singoli corsi
   - Sistema di iscrizioni integrato
   - Monitoraggio avanzamento corsi

3. **Pianificazione e Calendario**
   - Calendario interattivo per la pianificazione lezioni
   - Gestione disponibilità docenti
   - Coordinamento automatizzato tra corsi e docenti
   - Visualizzazione multi-prospettiva del calendario

4. **Gestione Documentale**
   - Generazione automatica attestati
   - Gestione materiale didattico
   - Creazione badge identificativi
   - Esportazione dati in formato CSV

5. **Monitoraggio e Reporting**
   - Dashboard interattiva con statistiche in tempo reale
   - Report dettagliati sulle attività formative
   - Tracciamento presenze e partecipazione
   - Analisi dell'andamento dei corsi

## Aggiornamento Interfaccia - Aprile 2024

### Miglioramenti Dashboard Amministratore

1. **Ottimizzazione Layout Responsive**
   - Uniformato il dimensionamento delle card
   - Migliorata la visualizzazione su tablet e dispositivi mobili
   - Implementato sistema di centering automatico per icone e contatori

2. **Miglioramenti Navbar**
   - Aggiunto nome dell'amministratore nella barra di navigazione
   - Ottimizzata visualizzazione responsive del nome utente
   - Rimossi elementi ridondanti per una migliore usabilità

3. **Pulizia Interfaccia**
   - Rimossi testi ripetitivi
   - Standardizzato il layout delle card
   - Migliorata la leggibilità complessiva

### Nuove Funzionalità

1. **Gestione Calendario**
   - Implementata visualizzazione calendario completo
   - Integrazione con disponibilità docenti
   - Interfaccia intuitiva per la gestione degli appuntamenti

2. **Gestione Disponibilità Docenti**
   - Nuova sezione dedicata alla gestione disponibilità
   - Interfaccia per inserimento e modifica disponibilità
   - Visualizzazione calendario personale docente

## Aggiornamento Database - Marzo 2024

### Motivazione della Ricostruzione del Database

È stato necessario ricreare il database per i seguenti motivi:

1. **Standardizzazione dei Ruoli Utente**
   - Uniformato il campo `ruolo` in tutto il sistema
   - Risolti problemi di inconsistenza tra `role` e `ruolo`
   - Garantita coerenza nelle autorizzazioni e nei permessi

2. **Gestione Calendario e Disponibilità**
   - Implementata nuova tabella `disponibilita_docente` per tracciare le disponibilità dei docenti
   - Aggiunto supporto per stati multipli (disponibile, occupato)
   - Migliorata l'integrazione con il calendario FullCalendar

3. **Dati di Test**
   - Inseriti utenti di test per ogni ruolo (admin, docenti, discenti)
   - Aggiunte disponibilità di esempio per i docenti
   - Facilitato il testing delle funzionalità del calendario

### Struttura del Nuovo Database

Il database include le seguenti tabelle principali:
- `user`: gestione utenti con ruoli differenziati
- `disponibilita_docente`: gestione delle disponibilità dei docenti
- `corso`: gestione dei corsi di formazione
- `progetto`: gestione dei progetti formativi
- `iscrizione`: gestione delle iscrizioni ai corsi

### Come Ricreare il Database

Per ricreare il database da zero:

1. Assicurarsi di essere nella directory del progetto
2. Attivare l'ambiente virtuale:
   ```
   .\venv_new\Scripts\activate
   ```
3. Eseguire lo script di creazione:
   ```
   python create_db_sqlite_new.py
   ```

### Credenziali di Test

- **Admin**:
  - Username: admin
  - Password: admin

- **Docenti**:
  - Username: docente1, docente2, docente3
  - Password: docente1, docente2, docente3

- **Discenti**:
  - Username: discente1, discente2
  - Password: discente1, discente2

### Note Importanti

- Il database viene ricreato da zero ogni volta che si esegue lo script
- Tutti i dati precedenti vengono eliminati
- Utilizzare solo in ambiente di sviluppo o test
- Per l'ambiente di produzione, effettuare un backup dei dati prima di procedere
