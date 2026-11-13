<!-- Written by `voteev texts` from src/spain_vote_ev/templates/POST.md, with the numbers of results/summary.json. Edit the template, not this file. -->
# LinkedIn post (draft)

Posted in Spanish, with the Spanish carousel (`carousel/carousel.pdf`) attached and no link in
the body. Publish it before the last five days of the campaign: LOREG art. 69.7 bans publishing
polls in the five days before the vote. Every number below comes from `results/summary.json`
through `voteev texts`, and `voteev check` verifies it.

<!-- lang: es -->

---

¿Cuánto vale tu voto el 29 de noviembre? He simulado 100.000 veces las generales para ponerle cifra.

Para el votante medio, un voto más cambia un escaño con una probabilidad de 1 entre 77.000.

Y cambia quién es investido presidente con una de 1 entre 11,3 millones: parecida a la de acertar los seis números de la Primitiva (1 entre 14 millones) y unas 5 veces mayor que la de decidir las presidenciales de EE. UU. de 2008 (1 entre 60 millones, según Gelman, Silver y Edlin).

En la investidura, cada lista vota como su grupo en 2023: al candidato del PP, como a Feijóo, y al del PSOE, como a Sánchez. Con esa regla, el candidato del PP sale investido en el 93,8 % de las simulaciones, el del PSOE en el 4,6 % y ninguno en el 1,6 %.

La circunscripción importa: para cambiar un escaño, en Ceuta es 1 entre 10.000; en Madrid, 1 entre 130.000. Para la investidura, la diferencia entre circunscripciones llega a 330 veces.

Cómo funciona:
1. La mediana de las últimas encuestas de 16 empresas, sin excluir ninguna.
2. Errores del tamaño de los fallos de esa mediana en 2015–2023.
3. D'Hondt con el umbral del 3 % en las 52 circunscripciones.
4. La investidura del artículo 99 de la Constitución, con los votos de 2023.
5. Contar cuántas veces a una lista le faltan pocos votos para el escaño que cambia quién es investido.

¿Funciona? Siete días antes de las generales de noviembre de 2019 y julio de 2023, 22 de 26 resultados por lista cayeron en las horquillas del 80 % y 24 de 26 en las del 95 %, con la regla para ensanchar errores escrita de antemano.

¿Y si cambian los supuestos? He repetido el cálculo con 6 variantes. La que más lo mueve (cada empresa corregida por su error de 2023) deja al candidato del PP en el 80,9 % y al del PSOE en el 16,1 %. Supone que cada empresa repite su error de 2023.

¿Compensa votar? A un votante egoísta, con 30 minutos a 10 €/h, solo le compensa si para él quién es investido vale 56,5 millones de euros. Contando a los 49,9 millones de residentes, con 100 € por persona en juego, basta con que cada desconocido te importe un 1,1 % de lo que te importas tú (Edlin, Gelman y Kaplan, 2007).

Es aritmética, no un consejo: los votos de investidura salen de 2023, todas las listas siguen las mismas reglas y nada aquí dice a quién votar ni si hacerlo.

El análisis, en el carrusel; el código y los datos, en el primer comentario.

---

## First comment

Código, datos y método, en abierto (cada cifra se reproduce desde fuentes públicas): github.com/oscargarcialopez/spain-vote-ev

Encuestas hasta el 10 de noviembre de 2026. En el repositorio están las 52 circunscripciones, los contrastes con elecciones pasadas, las variantes, los límites y una versión en inglés del carrusel.

## Chuleta para responder (neutral)

- **«¿Entonces no merece la pena votar?»** El cálculo no dice eso: da la probabilidad de que un voto decida. Si compensa depende de cuánto valga el resultado para cada uno, para sí y para los demás, y de lo que valga votar en sí. No recomiendo nada.
- **«¿Por qué votan así en la investidura?»** Es la regla más simple que no depende de mi juicio: cada lista repite el voto de su grupo en las dos investiduras de 2023, la de Feijóo y la de Sánchez. Si las listas sin escaño en 2023 se abstienen en vez de votar no, el candidato del PP sale en el 94,5 % de las simulaciones y el del PSOE en el 5,4 %.
- **«¿Y si alguien cambia de voto?»** La regla no recoge pactos nuevos ni abstenciones como las de 2016 y 2020; está en los límites del README, con el historial de votaciones desde 2016.
- **«Las encuestas fallan» / «¿Y el CIS?»** Uso la mediana de las últimas encuestas de 16 empresas, sin excluir ninguna, y el error se mide con lo que esa misma mediana falló en 2015–2023. El CIS cae fuera del periodo de 14 días; su comparación con las demás empresas está en el repositorio.
- **«¿Y el Senado?»** Queda fuera: sus escaños van a los candidatos más votados, no a las listas, y dar a cada candidato de 2023 los votos de su lista al Congreso habría cambiado 7 de los 192 escaños de fuera de las islas. Está en los límites del README.
- **«¿Y en mi provincia?»** Las 52 circunscripciones están en el README, con la probabilidad de cambiar un escaño y la de cambiar quién es investido.
- **«Esto favorece a X»** Todas las listas siguen las mismas reglas y el código es público: cualquiera puede rehacerlo con otros supuestos.
- **«¿Por qué 176?»** Es la mayoría absoluta de la primera votación de investidura; en la segunda basta con más síes que noes. Como en 2023 nadie se abstuvo, con la regla base la segunda también pide 176.

<!-- lang: en -->

## Appendix: the English version (not posted)

Kept for reference; the post goes out in Spanish. English carousel: `carousel/en/carousel.pdf`.

---

What is one vote worth on 29 November? I simulated Spain's election 100,000 times to put a number on it.

For the average voter, one more vote changes a seat in Congress with probability 1 in 77,000.

It changes who is invested prime minister with probability 1 in 11.3 million: close to the odds of picking all six numbers of 49 (1 in 14 million), and about 5 times likelier than deciding the 2008 US presidency (1 in 60 million, by Gelman, Silver and Edlin's estimate).

In the investiture, each list votes as its group did in 2023: on the PP's candidate as on Feijóo, on the PSOE's candidate as on Sánchez. Under that rule the PP's candidate is invested in 93.8% of the runs, the PSOE's in 4.6%, and nobody in 1.6%.

The constituency matters. To change a seat, the odds are 1 in 10,000 in Ceuta and 1 in 130,000 in Madrid. For the investiture, the odds differ up to 330-fold between constituencies.

How it works:
1. The median of 16 pollsters' latest polls, with none excluded.
2. National errors sized on how that same median missed in 2015–2023, plus regional, provincial and turnout noise.
3. D'Hondt with the 3% threshold in all 52 constituencies.
4. The investiture of article 99 of the Constitution, with the 2023 votes.
5. Count how often a list ends up a handful of votes short of the seat that changes who is invested.

Does it work? Run seven days before the November 2019 and 2023 elections, 22 of 26 seat counts fell inside the 80% intervals and 24 of 26 inside the 95% ones. The rule for widening the errors was written down before the first backtest.

What if the assumptions change? I redid the calculation under 6 variants. The one that moves it most (each firm corrected by its 2023 error) puts the PP's candidate at 80.9% and the PSOE's at 16.1%. It assumes each firm repeats its 2023 error.

So is voting worth it? For a purely selfish voter, at 30 minutes and 10 €/h, who is invested would have to be worth 56.5 million € to them. Counting the outcome for 49.9 million residents changes the arithmetic: with 100 € per person at stake, weighing a stranger at 1.1% of yourself is enough (Edlin, Gelman and Kaplan, 2007).

This is arithmetic, not advice. The investiture votes come from 2023, every list is treated alike, and nothing here says how, or whether, anyone should vote.

The write-up is in the carousel; code and data are in the first comment.

---

### First comment

Code, data and method (open source, every number reproducible from public sources): github.com/oscargarcialopez/spain-vote-ev

Polls to 10 November 2026. The README has all 52 constituencies, the backtests, the variants and the limits.
