# LinkedIn post (draft)

Posted in Spanish, with the Spanish carousel (`carousel/carousel.pdf`) attached and no link in
the body. Publish it before the last five days of the campaign: LOREG art. 69.7 bans publishing
polls in the five days before the vote. Every number below is checked against
`results/summary.json` by `voteev check`.

---

¿Cuánto vale tu voto el 29 de noviembre? He simulado 100.000 veces las generales para ponerle cifra.

Para el votante medio, un voto más cambia un escaño con una probabilidad de 1 entre 76.000.

Y decide si uno de los bloques de las investiduras de 2023 llega a la mayoría absoluta, 176 escaños, con una de 1 entre 10,8 millones: parecida a la de acertar los seis números de la Primitiva (1 entre 14 millones) y unas 6 veces mayor que la de decidir las presidenciales de EE. UU. de 2008 (1 entre 60 millones, según Gelman, Silver y Edlin).

La circunscripción importa: para cambiar un escaño, en Ceuta, con un solo diputado, es 1 entre 10.000; en Madrid, 1 entre 130.000. Para la mayoría, la diferencia llega a 56 veces.

Cómo funciona:
1. La mediana de las últimas encuestas de 16 empresas, sin excluir ninguna.
2. Errores del tamaño de los fallos de esa mediana en 2015–2023.
3. D'Hondt con el umbral del 3 % en las 52 circunscripciones.
4. Contar cuántas veces a una lista le faltan pocos votos para otro escaño.

¿Funciona? Siete días antes de las generales de noviembre de 2019 y julio de 2023, 22 de 26 resultados por lista cayeron en las horquillas del 80 % y 24 de 26 en las del 95 %, con la regla para ensanchar errores escrita de antemano.

¿Compensa votar? A un votante egoísta, con 30 minutos a 10 €/h, solo le compensa si para él la mayoría vale 53,8 millones de euros. Contando a los 49,9 millones de residentes, con 100 € por persona en juego, basta con que cada desconocido te importe un 1,1 % de lo que te importas tú (Edlin, Gelman y Kaplan, 2007).

Es aritmética, no un consejo: los bloques salen de las investiduras de 2023, todas las listas siguen las mismas reglas y nada aquí dice a quién votar ni si hacerlo.

El análisis, en el carrusel; el código y los datos, en el primer comentario.

---

## First comment

Código, datos y método, en abierto (cada cifra se reproduce desde fuentes públicas): github.com/oscargarcialopez/spain-vote-ev

Encuestas hasta el 10 de noviembre de 2026. En el repositorio están las 52 circunscripciones, los contrastes con elecciones pasadas, los límites y una versión en inglés del carrusel.

## Chuleta para responder (neutral)

- **«¿Entonces no merece la pena votar?»** El cálculo no dice eso: da la probabilidad de que un voto decida. Si compensa depende de cuánto valga el resultado para cada uno, para sí y para los demás, y de lo que valga votar en sí. No recomiendo nada.
- **«¿Por qué esos bloques?»** Son los síes de las dos investiduras de 2023, la de Feijóo y la de Sánchez; nadie los asigna a mano. También doy S sin Junts.
- **«Las encuestas fallan» / «¿Y el CIS?»** Uso la mediana de las últimas encuestas de 16 empresas, sin excluir ninguna, y el error se mide con lo que esa misma mediana falló en 2015–2023. El CIS cae fuera de la ventana de 14 días; su comparación con las demás está en el repositorio.
- **«¿Y en mi provincia?»** Las 52 circunscripciones están en el README, con la probabilidad de cambiar un escaño y la mayoría.
- **«Esto favorece a X»** Todas las listas siguen las mismas reglas y el código es público: cualquiera puede rehacerlo con otros supuestos.
- **«¿Por qué 176?»** Es la mayoría absoluta de la primera votación de investidura; en la segunda basta la mayoría simple, y lo explico en los límites del README.

<!-- lang: en -->

## Appendix: the English version (not posted)

Kept for reference; the post goes out in Spanish. English carousel: `carousel/en/carousel.pdf`.

---

What is one vote worth on 29 November? I simulated Spain's election 100,000 times to put a number on it.

For the average voter, one more vote changes a seat in Congress with probability 1 in 76,000.

It changes whether either of the two 2023 investiture blocs reaches 176 seats with probability 1 in 10.8 million. That is close to the odds of picking all six numbers of 49 (1 in 14 million), and about 6 times likelier than deciding the 2008 US presidency (1 in 60 million, by Gelman, Silver and Edlin's estimate).

The constituency matters. In Ceuta, a one-seat race, the seat odds are 1 in 10,000; in Madrid, 1 in 130,000. For the majority, the odds differ up to 56-fold between constituencies.

How it works:
1. The median of 16 pollsters' latest polls, with none excluded.
2. National errors sized on how that same median missed in 2015–2023, plus regional, provincial and turnout noise.
3. D'Hondt with the 3% threshold in all 52 constituencies.
4. Count how often a list ends up a handful of votes short of a seat.

Does it work? Run seven days before the November 2019 and 2023 elections, 22 of 26 seat counts fell inside the 80% intervals and 24 of 26 inside the 95% ones. The rule for widening the errors was written down before the first backtest.

So is voting worth it? For a purely selfish voter, at 30 minutes and 10 €/h, the majority would have to be worth 53.8 million € to them. Counting the outcome for 49.9 million residents changes the arithmetic: with 100 € per person at stake, weighing a stranger at 1.1% of yourself is enough (Edlin, Gelman and Kaplan, 2007).

This is arithmetic, not advice. The blocs come from the 2023 investiture votes, every list is treated alike, and nothing here says how, or whether, anyone should vote.

The write-up is in the carousel; code and data are in the first comment.

---

### First comment

Code, data and method (open source, every number reproducible from public sources): github.com/oscargarcialopez/spain-vote-ev

Polls to 10 November 2026. The README has all 52 constituencies, the backtests, and the limits.
