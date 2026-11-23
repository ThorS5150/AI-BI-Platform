# 02 Risikobewertung

| Nr. | Modul | Risiko | Wahrscheinlichkeit | Auswirkung | Maßnahme | Restrisiko |
|---|---|---|---|---|---|---|
| R1 | RAG | Halluzinierte Antwort | mittel | hoch | Quellenpflicht, Testset | mittel |
| R2 | Agent | Falsches Tool gewählt | mittel | mittel | Routing-Test, Logging | niedrig |
| R3 | SQL-Tool | Schreibende SQL-Abfrage | niedrig | hoch | Nur lesende Rechte | niedrig |
| R4 | Daten | Personenbezogene Daten im Datensatz | niedrig | hoch | Nur synthetische Daten | niedrig |
| R5 | Forecast | Systematisch falsche Prognose | mittel | mittel | Backtesting, Monitoring | mittel |
