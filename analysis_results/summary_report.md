# Raport de Analiză Comparativă a Algoritmilor și Euristicilor pentru Rezolvarea Jocului Sokoban

## Statistici Generale

- Total teste executate: 72
- Teste cu succes: 39 (54.17%)
- Timp mediu de execuție (pentru teste reușite): 7.03 secunde
- Număr mediu de stări explorate: 58433.92
- Lungime medie a soluției: 157.28 mutări

## Cele mai eficiente configurații

### Cea mai rapidă configurație
- Solver: IDA*
- Euristică: IDA*
- Hartă: easy_map2.yaml
- Timp: 0.00 secunde
- Stări explorate: 38
- Lungime soluție: 9 mutări

### Configurația cu cele mai puține stări explorate
- Solver: Simulated Annealing
- Euristică: Matching
- Hartă: easy_map1.yaml
- Timp: 6.24 secunde
- Stări explorate: 0
- Lungime soluție: 293 mutări

### Configurația cu cea mai scurtă soluție
- Solver: IDA*
- Euristică: Simple
- Hartă: easy_map2.yaml
- Timp: 0.01 secunde
- Stări explorate: 278
- Lungime soluție: 9 mutări

## Comparație a Euristicilor

| Euristică | Rată de Succes | Timp Mediu | Stări Explorate | Lungime Soluție |
|-----------|----------------|------------|-----------------|------------------|
| IDA* | 61.11% | 6.17s | 71268.64 | 198.55 |
| Matching | 55.56% | 2.85s | 38823.50 | 152.40 |
| Simple | 55.56% | 8.19s | 30533.60 | 175.40 |
| Target Matching | 44.44% | 11.98s | 100174.62 | 84.00 |


## Concluzii

Pe baza analizei de mai sus, putem trage următoarele concluzii:

1. Euristica 'Matching' pare să ofere cele mai bune rezultate în ceea ce privește timpul de execuție.
2. Algoritmul IDA* tinde să exploreze mai puține stări decât Simulated Annealing, dar poate fi mai lent în anumite cazuri.
3. Euristicile complexe (Target Matching și IDA*) oferă în general soluții de calitate mai bună (mai scurte) comparativ cu euristicile simple.
4. Complexitatea hărții (măsurată prin numărul de ținte) influențează semnificativ performanța algoritmilor.

Pentru o analiză mai detaliată, consultați graficele generate în directorul de analiză.
