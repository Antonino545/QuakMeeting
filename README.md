# 🦆 QuakMeeting - Meeting Reminders per macOS

**QuakMeeting** è un'applicazione nativa per la barra dei menu di macOS, ispirata a [QuakPit](https://github.com/Ooble-Studio/QuakPit).

Scansiona automaticamente i calendari del tuo Mac (Google Calendar, iCloud, Outlook, ecc.), rileva le riunioni che contengono link di videochiamata (**Google Meet, Zoom, Microsoft Teams, Webex, Jitsi**) e mostra avvisi fluttuanti in stile HUD con il pulsante **"🚀 PARTECIPA AL MEETING"** per accedere con un singolo click.

---

## 🌟 Caratteristiche

- 📅 **Integrazione Nativa macOS Calendar**: Legge in automatico tutti i calendari sincronizzati sul Mac (nessuna chiave API richiesta).
- 🔗 **Rilevamento Automatico Link Video**: Riconosce Meet, Zoom, Teams, Webex, Jitsi e altri provider.
- 🦆 **Banner Fluttuante Stile QuakPit**: Pop-up in primo piano al centro dello schermo 5 minuti prima della riunione con conto alla rovescia e pulsante di accesso rapido.
- 🍏 **Icona nella Barra dei Menu macOS**: Mostra la prossima riunione, l'elenco dei meeting odierni e consente il lancio rapido con 1 click.
- ⚡ **Zero Dipendenze Esterne**: Utilizza la libreria nativa macOS AppKit & Tkinter di Python.

---

## 🚀 Come Avviare QuakMeeting

Puoi avviare l'applicazione in due modi:

1. **Doppio Click sul File Eseguibile**:
   Vai nella cartella `Documenti/QuakMeeting` e fai doppio click su:
   `start_quakmeeting.command`

2. **Da Terminale**:
   ```bash
   python3 /Users/antonino54/Documents/QuakMeeting/main.py
   ```

---

## 📁 Struttura della Cartella (`/Users/antonino54/Documents/QuakMeeting`)

- `main.py`: Punto d'ingresso principale dell'applicazione.
- `calendar_scanner.py`: Modulo di scansione ed estrazione link riunioni dal calendario Mac.
- `banner_window.py`: Finestra fluttuante pop-up in stile QuakPit per i reminder.
- `menu_bar_app.py`: Gestore dell'icona e del menu a tendina nella barra dei menu di macOS.
- `start_quakmeeting.command`: File eseguibile con doppio click.
- `README.md`: Documentazione d'uso.
