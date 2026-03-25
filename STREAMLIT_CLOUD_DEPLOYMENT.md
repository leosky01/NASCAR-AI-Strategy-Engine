# 🚀 Deploy su Streamlit Cloud - Guida Completa

## Prerequisiti ✅

Il progetto è già configurato correttamente per Streamlit Cloud:
- ✅ `app.py` nella root directory
- ✅ `requirements.txt` con tutte le dipendenze
- ✅ `pyproject.toml` per package management
- ✅ Codice su GitHub (https://github.com/leosky01/NASCAR-AI-Strategy-Engine)

## Passaggi per la Deploy

### 1. Verifica che tutto sia su GitHub

```bash
git status
# Dovrebbe mostrare: "nothing to commit, working tree clean"
```

Se ci sono cambi non committati:
```bash
git add .
git commit -m "Preparazione per Streamlit Cloud"
git push
```

### 2. Vai su Streamlit Cloud

1. Apri https://share.streamlit.io
2. Clicca su "Sign in" e accedi con il tuo account GitHub
3. Clicca su "New app"

### 3. Configura l'app

Compila il form con questi valori:

**Repository:**
- Repository: `leosky01/NASCAR-AI-Strategy-Engine`
- Branch: `main`
- Main file path: `app.py`

**Advanced Settings (opzionale ma consigliato):**
- Title: `NASCAR AI Strategy Engine`
- URL Subdomain: `nascar-strategy-engine` (o quello che preferisci)

### 4. Clicca "Deploy" 🚀

L'app sarà disponibile in 1-2 minuti a un URL tipo:
`https://nascar-strategy-engine.streamlit.app`

## Troubleshooting

### Se la deployment fallisce:

**Errore: Module not found**
- Verifica che `requirements.txt` contenga tutte le dipendenze
- Riaggiungi le modifiche e pusha

**Errore: App crash all'avvio**
- Controlla i logs su Streamlit Cloud
- Assicurati che non ci siano file paths hardcoded

**Performance lenta**
- Streamlit Cloud ha limiti di risorse (gratis)
- Riduci `num_simulations` nei settings della dashboard

### Logs e Monitoring

Su Streamlit Cloud puoi:
- Vedere i logs in tempo reale
- Monitorare l'utilizzo delle risorse
- Fare rollback a versioni precedenti

## Costi

- **Gratuito**: Fino a certi limiti di risorse
- **Pro**: $10/mese per più risorse e features

Per uso dimostrativo e portfolio, la versione gratis è perfetta!

## Dopo la Deploy

Una volta deployata, l'app sarà:
- ✅ Accessibile 24/7
- ✅ Automaticamente aggiornata quando fai push su GitHub
- ✅ Condivisibile con il link
- ✅ Perfetta per portfolio e demo
