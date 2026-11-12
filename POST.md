# LinkedIn post (draft)

Post text (no link in the body), with the carousel PDF attached:

---

What is one vote worth on 29 November? I simulated Spain's election 100,000 times to put a number on it.

For the average voter, one more vote changes a seat in Congress with probability 1 in 76,000.

It changes whether either of the two 2023 investiture blocs reaches 176 seats with probability 1 in 10.8 million. That is close to the odds of picking all six numbers of 49 (1 in 14 million), and about 6 times likelier than deciding the 2008 US presidency (1 in 60 million, by Gelman, Silver and Edlin's estimate).

Where the vote is cast matters a lot. In Ceuta, a one-seat race, the seat odds are 1 in 10,000; in Madrid, 1 in 130,000. For the majority, the odds differ up to 56-fold between constituencies.

How it works:
1. The median of 16 pollsters' latest polls, with none excluded.
2. National errors sized on how that same median missed in 2015–2023, plus regional, provincial and turnout noise.
3. D'Hondt with the 3% threshold in all 52 constituencies.
4. Count how often a list ends up a handful of votes short of a seat.

Does it work? Run seven days before the November 2019 and 2023 elections, 22 of 26 seat counts fell inside the 80% intervals and 24 of 26 inside the 95% ones. The rule for widening the errors was written down before the first backtest.

So is voting worth it? For a purely selfish voter, at 30 minutes and 10 €/h, the majority would have to be worth 53.8 million € to them. Counting the outcome for 49.9 million residents changes the arithmetic: with 100 € per person at stake, weighing a stranger at 1.1% of yourself is enough (Edlin, Gelman and Kaplan, 2007).

This is arithmetic, not advice. The blocs come from the 2023 investiture votes, every list is treated alike, and nothing here says how, or whether, anyone should vote.

The nine-page write-up is in the carousel; code and data are in the first comment.

---

## First comment

Code, data and method (open source, every number reproducible from public sources): github.com/oscargarcialopez/spain-vote-ev

Polls to 10 November 2026. The README has all 52 constituencies, the backtests, and the limits.

## Chuleta para responder (neutral)

- **«¿Entonces no merece la pena votar?»** El cálculo no dice eso: da la probabilidad de que un voto decida. Si compensa depende de cuánto valga el resultado para cada uno, para sí y para los demás, y de lo que valga votar en sí. No recomiendo nada.
- **«¿Por qué esos bloques?»** Son los síes de las dos investiduras de 2023, la de Feijóo y la de Sánchez; nadie los asigna a mano. También doy S sin Junts.
- **«Las encuestas fallan» / «¿Y el CIS?»** Uso la mediana de las últimas encuestas de 16 empresas, sin excluir ninguna, y el error se mide con lo que esa misma mediana falló en 2015–2023. El CIS cae fuera de la ventana de 14 días; su comparación con las demás está en el repositorio.
- **«¿Y en mi provincia?»** Las 52 circunscripciones están en el README, con la probabilidad de cambiar un escaño y la mayoría.
- **«Esto favorece a X»** Todas las listas siguen las mismas reglas y el código es público: cualquiera puede rehacerlo con otros supuestos.
- **«¿Por qué 176?»** Es la mayoría absoluta de la primera votación de investidura; en la segunda basta la mayoría simple, y lo explico en los límites.
