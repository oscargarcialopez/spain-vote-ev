# LinkedIn post (draft)

Posted in Spanish, with the Spanish carousel (`carousel/carousel.pdf`) attached and no link in
the body. Publish it before the last five days of the campaign: LOREG art. 69.7 bans publishing
polls in the five days before the vote. Every number below comes from `results/summary.json`
through `voteev texts`, and `voteev check` verifies it.

<!-- lang: es -->

---

¿Cuánto vale tu voto el 29 de noviembre? He simulado {{n}} veces las generales para ponerle cifra.

Para el votante medio, un voto más cambia un escaño con una probabilidad de 1 entre {{seat.one_in}}.

Y cambia quién es investido presidente con una de 1 entre {{government.one_in}}: {{cmp.gov.lottery}} (1 entre {{lottery}}) y {{cmp.gov.gse}} (1 entre {{gse}}, según Gelman, Silver y Edlin).

En la investidura, cada lista vota como su grupo en 2023: al candidato del PP, como a Feijóo, y al del PSOE, como a Sánchez. Con esa regla, el candidato del PP sale investido en el {{gov.PP.p1}} de las simulaciones, el del PSOE en el {{gov.PSOE.p1}} y ninguno en el {{gov.blocked}}.

La circunscripción importa: para cambiar un escaño, en {{seat.top1}} es 1 entre {{seat.top1.one_in}}; en {{seat.bottom1}}, 1 entre {{seat.bottom1.one_in}}. Para la investidura, la diferencia entre circunscripciones llega a {{government.spread}} veces.

Cómo funciona:
1. La mediana de las últimas encuestas de {{firms}} empresas, sin excluir ninguna.
2. Errores del tamaño de los fallos de esa mediana en 2015–2023.
3. D'Hondt con el umbral del 3 % en las 52 circunscripciones.
4. La investidura del artículo 99 de la Constitución, con los votos de 2023.
5. Contar cuántas veces a una lista le faltan pocos votos para el escaño que cambia quién es investido.

¿Funciona? Siete días antes de las generales de noviembre de 2019 y julio de 2023, {{bt.in80}} resultados por lista cayeron en las horquillas del 80 % y {{bt.in95}} en las del 95 %, con la regla para ensanchar errores escrita de antemano.

¿Y si cambian los supuestos? He repetido el cálculo con {{rob.variants}} variantes. La que más lo mueve ({{rob.max.name}}) deja al candidato del PP en el {{rob.max.PP}} y al del PSOE en el {{rob.max.PSOE}}.{{rob.max.assumes}}

¿Compensa votar? A un votante egoísta, con {{minutes}} minutos a {{value_of_time}}, solo le compensa si para él quién es investido vale {{th.government.B}}. Contando a los {{population}} de residentes, con 100 € por persona en juego, basta con que cada desconocido te importe un {{th.government.alpha100}} de lo que te importas tú (Edlin, Gelman y Kaplan, 2007).

Es aritmética, no un consejo: los votos de investidura salen de 2023, todas las listas siguen las mismas reglas y nada aquí dice a quién votar ni si hacerlo.

El análisis, en el carrusel; el código y los datos, en el primer comentario.

---

## First comment

Código, datos y método, en abierto (cada cifra se reproduce desde fuentes públicas): github.com/oscargarcialopez/spain-vote-ev

Encuestas hasta el {{cutoff}}. En el repositorio están las 52 circunscripciones, los contrastes con elecciones pasadas, las variantes, los límites y una versión en inglés del carrusel.

## Chuleta para responder (neutral)

- **«¿Entonces no merece la pena votar?»** El cálculo no dice eso: da la probabilidad de que un voto decida. Si compensa depende de cuánto valga el resultado para cada uno, para sí y para los demás, y de lo que valga votar en sí. No recomiendo nada.
- **«¿Por qué votan así en la investidura?»** Es la regla más simple que no depende de mi juicio: cada lista repite el voto de su grupo en las dos investiduras de 2023, la de Feijóo y la de Sánchez. Si las listas sin escaño en 2023 se abstienen en vez de votar no, el candidato del PP sale en el {{gov.no_record_abstain.PP.p1}} de las simulaciones y el del PSOE en el {{gov.no_record_abstain.PSOE.p1}}.
- **«¿Y si alguien cambia de voto?»** La regla no recoge pactos nuevos ni abstenciones como las de 2016 y 2020; está en los límites del README, con el historial de votaciones desde 2016.
- **«Las encuestas fallan» / «¿Y el CIS?»** Uso la mediana de las últimas encuestas de {{firms}} empresas, sin excluir ninguna, y el error se mide con lo que esa misma mediana falló en 2015–2023. {{cis.status}}
- **«¿Y el Senado?»** Queda fuera: sus escaños van a los candidatos más votados, no a las listas, y dar a cada candidato de 2023 los votos de su lista al Congreso habría cambiado {{senate.party_line_changes_2023}} de los {{senate.party_line_seats_2023}} escaños de fuera de las islas. Está en los límites del README.
- **«¿Y en mi provincia?»** Las 52 circunscripciones están en el README, con la probabilidad de cambiar un escaño y la de cambiar quién es investido.
- **«Esto favorece a X»** Todas las listas siguen las mismas reglas y el código es público: cualquiera puede rehacerlo con otros supuestos.
- **«¿Por qué 176?»** Es la mayoría absoluta de la primera votación de investidura; en la segunda basta con más síes que noes. Como en 2023 nadie se abstuvo, con la regla base la segunda también pide 176.

<!-- lang: en -->

## Appendix: the English version (not posted)

Kept for reference; the post goes out in Spanish. English carousel: `carousel/en/carousel.pdf`.

---

What is one vote worth on 29 November? I simulated Spain's election {{n}} times to put a number on it.

For the average voter, one more vote changes a seat in Congress with probability 1 in {{seat.one_in}}.

It changes who is invested prime minister with probability 1 in {{government.one_in}}: {{cmp.gov.lottery}} (1 in {{lottery}}), and {{cmp.gov.gse}} (1 in {{gse}}, by Gelman, Silver and Edlin's estimate).

In the investiture, each list votes as its group did in 2023: on the PP's candidate as on Feijóo, on the PSOE's candidate as on Sánchez. Under that rule the PP's candidate is invested in {{gov.PP.p1}} of the runs, the PSOE's in {{gov.PSOE.p1}}, and nobody in {{gov.blocked}}.

The constituency matters. To change a seat, the odds are 1 in {{seat.top1.one_in}} in {{seat.top1}} and 1 in {{seat.bottom1.one_in}} in {{seat.bottom1}}. For the investiture, the odds differ up to {{government.spread}}-fold between constituencies.

How it works:
1. The median of {{firms}} pollsters' latest polls, with none excluded.
2. National errors sized on how that same median missed in 2015–2023, plus regional, provincial and turnout noise.
3. D'Hondt with the 3% threshold in all 52 constituencies.
4. The investiture of article 99 of the Constitution, with the 2023 votes.
5. Count how often a list ends up a handful of votes short of the seat that changes who is invested.

Does it work? Run seven days before the November 2019 and 2023 elections, {{bt.in80}} seat counts fell inside the 80% intervals and {{bt.in95}} inside the 95% ones. The rule for widening the errors was written down before the first backtest.

What if the assumptions change? I redid the calculation under {{rob.variants}} variants. The one that moves it most ({{rob.max.name}}) puts the PP's candidate at {{rob.max.PP}} and the PSOE's at {{rob.max.PSOE}}.{{rob.max.assumes}}

So is voting worth it? For a purely selfish voter, at {{minutes}} minutes and {{value_of_time}}, who is invested would have to be worth {{th.government.B}} to them. Counting the outcome for {{population}} residents changes the arithmetic: with 100 € per person at stake, weighing a stranger at {{th.government.alpha100}} of yourself is enough (Edlin, Gelman and Kaplan, 2007).

This is arithmetic, not advice. The investiture votes come from 2023, every list is treated alike, and nothing here says how, or whether, anyone should vote.

The write-up is in the carousel; code and data are in the first comment.

---

### First comment

Code, data and method (open source, every number reproducible from public sources): github.com/oscargarcialopez/spain-vote-ev

Polls to {{cutoff}}. The README has all 52 constituencies, the backtests, the variants and the limits.
