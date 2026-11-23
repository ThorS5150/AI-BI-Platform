# 05 Monitoring-Plan

| Was | Messgröße | Schwellenwert | Reaktion |
|---|---|---|---|
| RAG-Qualität | Trefferquote Top 3 | unter 70 % | Chunking und Embeddings prüfen |
| Agent | Routing-Genauigkeit | unter 80 % | Router-Regeln anpassen |
| Forecast | MAPE | über dem Wert der Model Card + 10 Prozentpunkte | Neutraining, Eintrag im Changelog |
| Datenqualität | fehlgeschlagene Prüfungen | mehr als 0 in Gold | Pipeline stoppen, Ursache dokumentieren |
