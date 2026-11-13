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

Y cambia quién es investido presidente con una de 1 entre 11,3 millones: parecida a la de acertar los seis números de la Primitiva.

¿Entonces no compensa votar? Depende de cuánto valga el resultado para ti y para los demás.

En el carrusel, cómo está hecho, si funciona y qué pasa si cambian los supuestos.

Es aritmética, no un consejo: todas las listas siguen las mismas reglas y nada aquí dice a quién votar ni si hacerlo.

El código y los datos, en el primer comentario.

---

## First comment

Código y datos para rehacerlo con tus propios supuestos: https://github.com/oscargarcialopez/spain-vote-ev

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

Code and data to redo it with your own assumptions: https://github.com/oscargarcialopez/spain-vote-ev
