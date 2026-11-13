# What is one vote worth? Spain, 29 November 2026

A seat simulation of Spain's general election of 29 November 2026, built to answer one
question: how likely is one more vote to change the result, a seat or who is invested prime
minister? Every list is treated alike, each list votes in the investiture as its group did in
2023, and nothing here advises anyone how, or whether, to vote.

Polls with fieldwork ending {{window}} ({{firms}} firms, {{lead}} days before the election);
{{n}} simulated elections (seed `{{seed}}`).

| One more vote, for the average voter | Probability | 95% Monte Carlo interval |
|---|---:|---:|
| changes a seat | 1 in {{seat.one_in}} | 1 in {{seat.ci}} |
| changes who is invested | 1 in {{government.one_in}} | 1 in {{government.ci}} |
| changes whether either 2023 investiture bloc reaches 176 seats | 1 in {{majority_any.one_in}} | 1 in {{majority_any.ci}} |

With every list voting as its group did in 2023, the PP's candidate is invested in
{{gov.PP.p1}} of the simulated elections, the PSOE's candidate in {{gov.PSOE.p1}}, and nobody in
{{gov.blocked}} ([Who is invested](#who-is-invested)). Across the variants of
[What was checked](#what-was-checked), the PP's candidate is invested in {{rob.range.PP}} of
the runs.

For scale: picking all six numbers of 49 is 1 in {{lottery}} ({{lottery_exact}} combinations),
and Gelman, Silver and Edlin (2012) put the chance that one vote decided the 2008 US presidency
at about 1 in {{gse}} for the average voter. One vote changing who is invested in Spain is
{{cmp.gov.lottery}}, and {{cmp.gov.gse}}.

The Monte Carlo intervals measure only simulation noise. The real uncertainty is in the model:
the bandwidth choice moves the answers by {{seat.bw_spread}} (seat) and
{{government.bw_spread}} (investiture), and [What was checked](#what-was-checked) shows what the
main assumptions do.

![The odds of deciding, against two references](figures/fig-odds.png)

The carousel is a summary in paper form: [in Spanish](carousel/carousel.pdf) (the one posted;
[plain text](carousel/slides.txt)) and [in English](carousel/en/carousel.pdf)
([plain text](carousel/en/slides.txt)). [POST.md](POST.md) is the LinkedIn post.

## The question

Spain elects 350 deputies in 52 constituencies by D'Hondt, with a 3% threshold of valid votes
in each; Ceuta and Melilla elect one each. One more vote matters if it moves a seat from one
list to another, and more if that seat changes who is invested.

**The investiture.** Congress invests the prime minister (Constitution, art. 99; Reglamento del
Congreso, arts. 170–172). After consulting the groups, the King proposes a candidate through
the Speaker. The candidate is invested in a first vote with the absolute majority of the 350
deputies, 176 yes votes; if not, in a second vote 48 hours later, with more yes than no votes.
Further candidates may be proposed; if nobody is invested two months after the first vote, both
chambers are dissolved and a new election is called.

**How each list votes.** Two candidates are modelled: the PP's and the PSOE's. The base rule
takes each 2026 list's vote from its group's vote in the two investitures of the 2023
legislature, with no abstentions, as then:

- On the PP's candidate, as on Feijóo (27 September 2023): {{inv.feijoo.yes}} yes (PP
  {{inv.feijoo.PP}}, Vox {{inv.feijoo.VOX}}, UPN {{inv.feijoo.UPN}}, CC {{inv.feijoo.CC}}) and
  {{inv.feijoo.no}} no.
- On the PSOE's candidate, as on Sánchez (16 November 2023): {{inv.sanchez.yes}} yes (PSOE
  {{inv.sanchez.PSOE}}, Sumar {{inv.sanchez.SUMAR}}, ERC {{inv.sanchez.ERC}}, Junts
  {{inv.sanchez.JUNTS}}, EH Bildu {{inv.sanchez.BILDU}}, PNV {{inv.sanchez.PNV}}, BNG
  {{inv.sanchez.BNG}}, CC {{inv.sanchez.CC}}) and {{inv.sanchez.no}} no.

A 2026 list inherits the vote of the 2023 group it comes from: the PP's lists include UPN (the
UPN–PP list in Navarra), and Frente Amplio and Podemos sat in the Sumar group. Lists with no
seat in 2023 (SALF, Adelante Andalucía, Teruel Existe, Soria ¡Ya!) have no record: they vote no,
and in a variant they abstain. Coalición Canaria voted yes to both. With nobody abstaining, the
second vote also needs 176, so a candidate is invested exactly when its 2023 coalition holds 176
seats. If both candidates could be invested, which only happens when Coalición Canaria holds the
balance, the candidate of the larger party is proposed first, as in 2023, and a tie goes to the
PP's candidate: an assumption, needed in {{gov.both}} of the runs. The totals are those of the
Diario de Sesiones
([27 Sep 2023](https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-5.PDF),
[16 Nov 2023](https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-8.PDF)).

**The record.** Votes change. Since {{rec.first}}, Congress has voted {{rec.votes}} times in
{{rec.debates}} investiture debates. The table adds the censure motion of 2018, the only one to
pass, which needs 176 yes votes and invests its candidate (Constitution, art. 113). Each vote
with the groups that voted yes or abstained (the others voted no, but for absences), from the
roll calls in the Diario de Sesiones
([data/curated/investitures.csv](data/curated/investitures.csv)):

{{table:record}}

Groups are the lists as elected, with their joint lists (the file's notes name each case).
"Other": absent, not called, a seat vacant that day, or a null vote (29 September 2023). In
{{rec.decided}}, a candidate passed the second vote with fewer than 176 yes votes because
deputies abstained. In {{rec.last}} {{rec.last.abstained}}, which is where the base rule comes
from; its variant lets only the lists with no 2023 seat abstain, and no 2023 group changes
sides.

**The average voter.** Each constituency's probability for each list, averaged with weights
equal to the list's expected votes there: the chance for a vote picked at random from all the
votes cast for the modelled lists.

## Results

### Who is invested

{{table:government}}

"Invested" adds both votes. Under the base rule nobody abstains, so the second vote needs 176
too and nobody is invested only in it. If the lists with no 2023 seat abstain instead, the PP's
candidate is invested in {{gov.no_record_abstain.PP.p1}} of the runs
({{gov.no_record_abstain.PP.second}} only in the second vote), the PSOE's in
{{gov.no_record_abstain.PSOE.p1}} ({{gov.no_record_abstain.PSOE.second}}), and nobody in
{{gov.no_record_abstain.blocked}}. "Nobody" means that neither candidate passes with the 2023
votes; the two months of talks that would follow are not simulated, so it is not a forecast of
a repeat election.

### Who holds the key

Seats are not power, and power has two readings here.

- **A priori power.** The Shapley–Shubik index (Shapley and Shubik, 1954) is the share of all
  orderings of the lists in which a list's seats are the ones that carry a growing coalition
  past 176; the Banzhaf index (Banzhaf, 1965) is the share of winning coalitions in which a list
  is decisive, normalised to sum to one. Both let any coalition form.
- **The key.** The probability that, with every list voting as in 2023, a list's votes are
  necessary for the investiture that happens: had it voted no instead of yes, the invested
  candidate would have lost both votes. Only the two coalitions of 2023 count.

{{table:keys}}

Mean seats and a priori power are averaged over {{pw.sample}} simulated parliaments; the key
over all {{n}}. A priori power, then and now:

{{table:power}}

### Blocs and lists

The coalitions of the two 2023 investitures, as blocs: F voted yes to Feijóo, S to Sánchez, and
S without Junts is reported too. A bloc with 176 seats is the base rule's investiture:

{{table:blocs}}

![Seats per list: means and 80% and 95% intervals](figures/fig-seats.png)

{{table:lists}}

"Vote share (centre)" is the share the simulation is centred on: the poll median for polled
lists, rescaled with the unpolled lists and blank votes; Teruel Existe and Soria ¡Ya! keep
their 2023 share.

### Constituencies

Small constituencies weigh more per elector: {{eps.min}} electors per seat in {{eps.min.name}}
against {{eps.max}} in {{eps.max.name}}, {{eps.ratio}} times as many. Across constituencies the
chance of changing a seat varies {{seat.spread}}-fold, and the chance of changing who is
invested {{government.spread}}-fold: from 1 in {{government.top1.one_in}} in
{{government.top1}} to 1 in {{government.bottom1.one_in}} in {{government.bottom1}}.

![The odds in each constituency against its seats](figures/fig-constituencies.png)

Every constituency, sorted by the chance of changing a seat:

{{table:provinces}}

"—": no such event in the runs. The investiture and bloc figures of a single constituency rest
on few simulated events and are noisy; the national figures above are precise.

The same numbers, with expected votes, are in
[results/provinces.csv](results/provinces.csv); simulated mean seats by constituency and list
are in [results/seats_by_province.csv](results/seats_by_province.csv).

### What was checked

**Inputs against the 2026 BOE.** The seats per constituency are those of the decree calling the
election, and the lists those proclaimed by the electoral boards. The PP and UPN run together in
Navarra (UPN–PP), counted as the PP's list; Frente Amplio and Podemos run apart, and the 2023
Sumar vote is split between them; SALF and Adelante Andalucía are polled and modelled; Teruel
Existe and Soria ¡Ya! stand again and keep their 2023 base. No CUP, PRC or Aliança Catalana
candidacy was proclaimed for the Congreso.

**Lists that could win a seat.** Of the {{comp.candidacies}} candidacies proclaimed,
{{comp.others}} are pooled as "others", which win no seat in the model. Matched by name to
every list that ran for the Congreso since 2015, {{comp.with_past}} have a past result in the
same constituency, and {{comp.verdict}}. The closest:

{{table:completeness}}

Poll columns that fewer than 5 firms report: {{comp.few_firms}}.

**The forecast under other assumptions.** Redone with one thing changed at a time, each with
the same {{rob.n}} simulated elections as the base (the same seed), so that only the change
differs:

{{table:robustness}}

The largest change comes from {{rob.max.name}}: the PP's candidate is invested in
{{rob.max.PP}} of the runs instead of {{rob.base.PP}}, the PSOE's in {{rob.max.PSOE}} instead
of {{rob.base.PSOE}}. The house effects are each firm's miss in its last poll before the 2023
election, on the logit scale, added to its 2026 figures ({{rob.house2023.adjusted}} firms had
such a poll; Frente Amplio and Podemos take Sumar's): the variant assumes each firm repeats its
2023 error. The weighted mean weights each firm's poll by its sample size.

## Why vote at all

With three or more options, no ranking rule meets all of Arrow's (1951) conditions, and
every non-dictatorial rule can reward voting against one's true ranking (Gibbard, 1973;
Satterthwaite, 1975). Spain's rule is given; the question is whether one vote is worth its
cost. In the calculus of voting (Riker and Ordeshook, 1968) a citizen votes when

    R = p·B − C + D > 0

with p the chance of being decisive, B the value of the outcome to the voter, C the cost of
voting and D the value of voting itself. Downs (1957) noted that p is tiny.

**Cost.** At {{minutes}} minutes and {{value_of_time}}, C = {{cost}}.

**Selfish benefit.** With p = 1 in {{government.one_in}}, who is invested would have to be
worth {{th.government.B}} to the voter to cover C; for a seat (p = 1 in {{seat.one_in}}),
{{th.seat.B}}.

**Social benefit.** If B counts the effect on everyone (Edlin, Gelman and Kaplan, 2007),
B = N·b·α, with N = {{population}} residents (INE, {{population_day}}, provisional), b the
average gain per person and α the weight the voter gives a stranger relative to themself. Then
p·N = {{th.government.pN}} for the investiture: with b = 100 €, voting pays once α passes
{{th.government.alpha100}} (about 1 in {{th.government.inv_alpha100}}); with b = 1,000 €, once
it passes {{th.government.alpha1000}}. For a seat, p·N = {{th.seat.pN}}.

![The weight on others at which voting pays](figures/fig-break-even.png)

**Others' votes.** Persuasion has, on average, no measurable effect in US general elections
(Kalla and Broockman, 2018); in France's 2012 presidential election, door-to-door canvassing
moved vote shares in the precincts it covered without moving turnout (Pons, 2018). Getting
people to vote is the other lever. In Europe, door-to-door canvassing raises turnout by
{{canvass.effect_pp}} points per voter reached (95% interval {{canvass.effect_lo}} to
{{canvass.effect_hi}}; {{canvass.experiments}} experiments pooled by Bhatti et al., 2019),
against {{canvass.us_effect_pp}} points in the US ({{canvass.us_experiments}} experiments;
Green, McGrath and Aronow, 2013). The only Spanish experiment, in Murcia's 2011 local
election, found no turnout effect (Morales, Ramiro and Jiménez-Buedo, 2023). The only pace
measured in Europe is {{canvass.minutes_per_door}} minutes per opened door (Cantoni and Pons,
2021), taken here as the time of a pair of canvassers, which the paper leaves open. With
{{canvass.voters_per_household}} registered voters per Spanish household (INE), a canvasser
reaches about {{canvass.voters_per_hour}} voters an hour, so an hour yields about {{vph_lo}}
extra voters, between 0 and {{vph_hi}}. At {{vph_lo}}, an hour
beats {{value_of_time}} only if who is invested is worth {{th.government.infl0.06}} to the
person spending it; at {{vph_hi}}, {{th.government.infl0.2}}; at 0, never. On the social
reckoning above, the same hour is worth {{vph_lo}} to {{vph_hi}} votes' worth of p·N·b·α.

## Method

1. **Polls.** Each firm's latest poll with fieldwork ending in the 14 days to the cutoff, from
   the Wikipedia list of opinion polls (revision fixed in `results/summary.json`); the median
   share of each list across firms. No firm is excluded. A list counts as polled if at least
   5 firms report it; joint columns are summed. Unpolled lists and blank votes keep their base
   share and the polled shares are rescaled around them. Other aggregations are variants
   ([What was checked](#what-was-checked)).
2. **National error.** Each polled share moves on the logit scale by an error of scale
   σ = {{sigma_nat}}: the root mean square of the same median's errors {{lead}} days before the
   2015, 2016, April 2019, November 2019 and 2023 elections ({{n_poll_errors}} list-elections
   with at least 1%; centred on zero, no bias correction). For lists that won at least 10%,
   those errors were {{big_err_rms_pp}} points RMS and at most {{big_err_max_pp}} points.
   {{sigma.how}} A rule written before the runs decided this ([Backtests](#backtests)). Past
   errors show no positive correlation within blocs, so none is added.
3. **Constituencies.** Proportional swing from 2023: each list's share in a constituency is its
   2023 share times its national ratio, times exp(δ), with δ the sum of a regional effect
   (σ = {{tau_ccaa}}) and a constituency effect (σ = {{tau_prov}}), both estimated from how
   {{n_residuals}} provincial swings departed from national ones; then shares are raked to the
   national draw. Sumar's 2023 vote is split between Frente Amplio and Podemos by their 2024
   European ratio in each province; SALF starts from its 2024 European vote; Adelante
   Andalucía, which in 2023 stood only in Cádiz, from a flat share across the Andalusian
   constituencies where it stands.
4. **Turnout.** National and constituency logit errors (σ = {{sigma_tn}} and {{sigma_tp}})
   around 2023 turnout.
5. **Seats.** D'Hondt with the 3% threshold in every constituency
   ([dhondt.py](src/spain_vote_ev/dhondt.py); official seats since 2015 are reproduced
   exactly), and for each list Δ, the extra votes it needs for one more seat, and the list
   that would lose it.
6. **The investiture.** In each simulated election the yes and no votes on each candidate are
   sums of the lists' seats under the base rule, and art. 99 decides who is invested
   ([investiture.py](src/spain_vote_ev/investiture.py)).
7. **One more vote.** The chance that a vote is decisive is the density of Δ at zero,
   p ≈ N_h / (n·h), where N_h counts the n runs with 0 < Δ ≤ h and h is 2% of the
   constituency's votes per seat; bandwidths of 1% and 5% are reported in `summary.json`. For
   the investiture, a run counts when the seat that changes hands changes who is invested: the
   tallies are recomputed with one seat moved from the list that would lose it to the list
   that would win it. For a bloc, a run counts when that seat moves the bloc across 176.

The 2026 lists are the candidacies proclaimed in the BOE, labelled by name. Modelled: every
list that at least 5 firms poll, plus Teruel Existe and Soria ¡Ya!, local lists with a large
vote in their province in 2023. All other candidacies are pooled as "others", which keep
their 2023 share and win no seats here.

## Backtests

The same code, run 7 days before the November 2019 and 2023 elections and calibrated only on
earlier elections. The widening rule was committed before the first backtest ran
([backtest.py](src/spain_vote_ev/backtest.py)): widen every error, by the first factor of
{{bt.factors}} that passes, if fewer than 75% of the actual seat counts fall in their 80%
intervals, or fewer than 90% in their 95% intervals.

Result: {{bt.in80}} inside the 80% intervals and {{bt.in95}} inside the 95% ones: {{bt.widen}}
(factor {{bt.factor}}).

![Backtests: intervals and actual seats](figures/fig-backtests.png)

{{table:backtests}}

The coalitions: in 2023 the forecast gave Feijóo's {{bt.2023.F.p}} and Sánchez's
{{bt.2023.S.p}} to reach 176; Feijóo's won {{bt.2023.F.actual}} seats ({{bt.2023.F.pctile}}
percentile of its simulated total) and Sánchez's {{bt.2023.S.actual}}
({{bt.2023.S.pctile}}). In November 2019 the coalition of PSOE, Unidas Podemos, PNV, Más País
and BNG had {{bt.2019N.S.p}} and won {{bt.2019N.S.actual}} ({{bt.2019N.S.pctile}}).

**σ's own uncertainty.** A second rule, also written in
[backtest.py](src/spain_vote_ev/backtest.py) before its runs: use Student-t errors if, at the
publication lead ({{sr.lead}} days) and pooled over four elections, they bring the coverage of
the 80% and 95% intervals closer to 80% and 95% than normal errors do, without moving it away
on November 2019 and 2023 together. Each backtest is calibrated on the elections before it;
2016, the first with an earlier election at that lead, borrows the later pairs for the swing
deviations, so it is not fully out of sample, and in April 2019 one seat went to a list not
modelled (PRC).

{{table:sigma_rule}}

The Student-t coverage is {{sr.closer}} the targets, {{sr.result}}. The misses at the 80% level,
with {{sr.adopted}} errors: 2016, {{sr.2016.misses80}}; April 2019, {{sr.2019A.misses80}};
November 2019, {{sr.2019N.misses80}}; 2023, {{sr.2023.misses80}}.

## Polls

{{table:polls}}

The CIS is in the median whenever its latest poll falls in the window. Its latest poll in the
data ended fieldwork on {{cis.end}}. Against the median of the {{cis.others}} other firms with
fieldwork in the 14 days to that date:

{{table:cis}}

## Inventory: the variables

Every input that can change the answer, where it comes from, how it enters, and what happens
when it is varied. "Effect" is the PP's candidate's chance of being invested under the variant
(base: {{rob.base.PP}}); [What was checked](#what-was-checked) has the rest.

| Variable | Value | Source | How it enters | Range tested | Effect |
|---|---|---|---|---|---|
| Poll summary | median of {{firms}} firms | Wikipedia lists of polls, at a recorded revision | each list's national centre | mean weighted by sample size | {{rob.weighted_mean.effect}} |
| Poll window | each firm's latest poll in the 14 days to the cutoff | design | which polls count | the last 7 days | {{rob.days7.effect}} |
| House effects | none | each firm's last poll before the 2023 election | added to the firm's 2026 figures | each firm repeats its 2023 error | {{rob.house2023.effect}} |
| The CIS | in the median when its poll is in the window | CIS barometers, via the same lists | like any firm | without it | {{rob.no_cis.effect}} |
| Polls released by parties | included | Wikipedia lists | like any firm | without them | {{rob.no_party_polls.effect}} |
| Lists modelled | polled by at least 5 firms, plus Teruel Existe and Soria ¡Ya! | BOE candidacies; polls | the rest pooled as "others", with no seats | every 2026 candidacy against past results | {{comp.flagged}} flagged |
| National error | σ = {{sigma_nat}}, logit scale | the same median's past errors, {{n_poll_errors}} cases | {{sigma.dist}} | {{sigma.alt}} | {{sigma.alt.effect}} |
| Widening factor | {{bt.factor}} | pre-declared backtests | multiplies every error | {{bt.factors}} | none chosen |
| Regional and provincial deviations | σ = {{tau_ccaa}} and {{tau_prov}} | {{n_residuals}} past provincial swings | normal, logit scale | not varied | [Limits](#limits) |
| Turnout | σ = {{sigma_tn}} national, {{sigma_tp}} provincial | past turnout changes | normal around 2023 turnout | not varied | [Limits](#limits) |
| Swing | proportional from 2023 | BOE results; 2024 European vote | provincial share × national ratio | not varied | [Limits](#limits) |
| Seats | 350 in 52 constituencies | the 2026 decree | exact | — | — |
| Seat rule | D'Hondt, 3% threshold | LOREG art. 163 | exact | every official result since 2015 reproduced | — |
| Investiture votes | each list as its group in 2023 | Diario de Sesiones | yes or no on each candidate | lists with no 2023 seat abstain | {{rob.no_record_abstain.effect}} |
| Candidate order | the larger party's first | the 2023 precedent | only if both could pass | — | {{gov.both}} of runs |
| Bandwidth h | 2% of the votes per seat | design | density of Δ at zero | 1% and 5% | the odds move {{government.bw_spread}} |
| Cost of voting | {{minutes}} minutes at {{value_of_time}} | assumption | C = {{cost}} | — | the theory only |
| Canvassing yield | {{vph_lo}} voters per canvasser-hour | European experiments | the value of an hour | 0 to {{vph_hi}} | the theory only |
| Population | {{population}} | INE | N in B = N·b·α | — | the theory only |

## Inventory: the players

Who can change the result, what they want, what they can do, and how the model takes them in.

| Player | Objective | Instruments | Channel | In the model |
|---|---|---|---|---|
| Voters | the outcome (B) and voting itself (D), at a cost (C) | vote, abstain, persuade or mobilise others | vote shares, turnout | the polls and their past errors; turnout noise; p is this study |
| Abstainers | the same, with D below C or B small | stay home, or vote if mobilised | turnout | turnout noise; canvassing in [Why vote at all](#why-vote-at-all) |
| Parties | votes, office and policy (Strøm, 1990) | lists, platforms, campaigns, pacts, investiture votes | vote shares; the investiture | the polls; the 2023 investiture votes and a variant |
| Leaders | the same, and their own office | candidacy, campaign, negotiation | vote shares; the investiture | through their party; not separately |
| The King (art. 99) | a government within the Constitution | proposes candidates after consulting the groups | who is proposed, and in what order | two candidates; the larger party's first if both could pass |
| The Congress Bureau and the Speaker | the chamber's procedure | the calendar of the investiture debate | timing | not modelled: timing does not change who can be invested |
| Junta Electoral Central and the provincial boards | a clean election under the LOREG | proclaim candidacies, rule on complaints, scrutinise | which lists run; the count | the proclaimed candidacies; counts taken as exact |
| Poll workers | count the votes | the count at each table | the count | taken as exact |
| Pollsters | accuracy, attention, clients | publish estimates, never in the last five days (LOREG art. 69.7) | expectations, maybe votes | the median and its past errors; house effects as a variant |
| The CIS | the same, as a public body | monthly barometers | expectations | in the median when in the window; a variant without it |
| Media | audience, influence | coverage, framing | expectations, vote shares | through the polls and their past errors |
| Platforms | engagement, revenue | ranking, ads, moderation | vote shares, turnout | through the polls' past errors |
| Foreign disinformation | division, lower trust | false content, amplification | vote shares, turnout | the same; an effect larger than in 2015–2023 is not covered |
| Unions and employers | their members' interests | endorsements, campaigns, mobilisation | vote shares, turnout | through the polls |
| Regional governments | their region and party | agenda, regional campaigns | vote shares by region | the regional deviations |
| The EU and markets | fiscal rules, stability | rules, spreads | what any government can do | not in the vote: an outside constraint |

**Why the list is complete enough.** A player can change who is invested only through four
channels: which lists run, how many people vote and for which list, how votes become seats, and
how deputies vote in the investiture. The first is fixed by the proclaimed candidacies and
checked above. The second is the poll error, the regional and provincial deviations and the
turnout noise, all sized on 2015–2023, so they already contain what campaigns, media, platforms
and outside interference did in those years. The third is the law, applied exactly. The fourth
is the 2023 rule and its variant. A player missing from the table still acts through one of
these channels. What the model cannot cover is an effect larger than any in 2015–2023, such as
a shock in the last days, or investiture votes unlike 2023's, such as a new pact: both are in
[Limits](#limits).

## Data

All files are downloaded by `voteev download` into `data/raw/`, with a SHA-256 manifest
([data/raw/MANIFEST.tsv](data/raw/MANIFEST.tsv)); nothing else touches the network.

- Official results, Congreso 2015 to 2023: the Junta Electoral Central's publications of the
  general count in the BOE
  ([2015](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2016-867),
  [2016](https://www.boe.es/boe/dias/2016/07/22/pdfs/BOE-A-2016-7133.pdf),
  [April 2019](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2019-8070),
  [November 2019](https://www.boe.es/boe/dias/2019/12/02/pdfs/BOE-A-2019-17344.pdf) and its
  [tables](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2019-18147),
  [2023](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2023-18907)).
- European Parliament 2024 by province
  ([BOE-A-2024-13092](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-13092), corrected by
  [BOE-A-2024-15344](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2024-15344)).
- 2026: the decree calling the election, with the seats per constituency
  ([BOE-A-2026-20742](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-20742)); the
  proclaimed candidacies
  ([BOE-A-2026-23103](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-23103), corrected
  by [BOE-A-2026-23383](https://www.boe.es/diario_boe/xml.php?id=BOE-A-2026-23383)); electors
  per constituency ([INE](https://www.ine.es/dyngs/Prensa/EG2026.pdf)); population
  ([INE](https://www.ine.es/dyngs/Prensa/ECP3T26.pdf)).
- Polls: the English Wikipedia lists of opinion polls for each election, read through the
  MediaWiki API at a recorded revision.
- The 2023 investiture votes, which the base rule repeats: the Diario de Sesiones of
  [27 September](https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-5.PDF) and
  [16 November 2023](https://www.congreso.es/public_oficiales/L15/CONG/DS/PL/DSCD-15-PL-8.PDF),
  downloaded with the rest.
- Investiture votes since 2016: [data/curated/investitures.csv](data/curated/investitures.csv),
  transcribed from the roll call of each vote in the Diario de Sesiones del Congreso (the URL
  is on every row); each vote's group totals add up to 350 and match the result announced in
  the chamber. The Senate's seats, rule and designated senators:
  [data/curated/senate.json](data/curated/senate.json), with its sources.
- The Ministry of the Interior's results archive (infoelectoral) is not used: its download
  area sits behind a browser check that a script cannot pass, and the BOE holds the same
  counts.

## Limits

- **Polls {{lead}} days out.** The errors are sized for that lead, but campaigns can move more.
- **Proportional swing.** Lists are assumed to gain or lose in proportion to their 2023 vote
  everywhere, plus noise. Where a list's base is thin or missing (SALF, Adelante Andalucía, the
  split of Sumar), the starting point is a guess.
- **Local lists.** Teruel Existe and Soria ¡Ya! are not in national polls; they keep their 2023
  share with constituency noise only. Other local lists are pooled as "others" and win no seat,
  which the completeness check supports but cannot guarantee: a new list has no past result.
- **The investiture repeats 2023.** Parties can change sides, make new pacts or abstain, as the
  record above shows; the base rule allows none of it, and the variant only lets the lists with
  no 2023 seat abstain. Only the PP's and the PSOE's candidates are modelled.
- **σ's own uncertainty.** Errors of the same election move together, so the
  {{n_poll_errors}} past errors are worth fewer independent ones. {{sigma.limit}} With
  {{sigma.alt}}, the PP's candidate is invested in {{sigma.alt.effect}} of the runs instead of
  {{gov.PP.p1}}.
- **House effects.** The variant assumes each firm repeats its 2023 error; firms change their
  methods, so it is a sensitivity, not a correction.
- **Independence.** Errors are independent across lists except for the rescaling that keeps
  shares summing to one.
- **The Senate is left out.** On 29 November, {{senate.elected_2026}} senators are elected
  directly, one more than in 2023, since Ibiza and Formentera now elect one each
  ([the decree calling the election, art. 3.2](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-20742)).
  A province elects four and its voters mark up to three candidates; Gran Canaria, Mallorca and
  Tenerife elect three, with two marks; Ceuta and Melilla two, with two; the other islands one.
  The most voted are elected (LOREG art. 166). On the 2023 count, that rule picks
  all {{senate.rule_reproduces_2023}} elected senators from {{senate.candidates_2023}}
  candidates. What is not validated is the step a model fed by Congreso polls needs: from a
  list's Congreso vote to its candidates' Senate votes. Giving each 2023 candidate outside the
  islands their list's Congreso vote changes {{senate.party_line_changes_2023}} of those
  {{senate.party_line_seats_2023}} seats ({{senate.party_line_where}}): candidates of one list
  draw different votes, and some lists do better in the Senate than in the Congreso. The
  regional parliaments designate the other senators (Constitution, art. 69.5):
  {{senate.designated_at_dissolution}} at the dissolution, in a Senate of
  {{senate.members_at_dissolution}} with an absolute majority of
  {{senate.majority_at_dissolution}}
  ([Senado](https://www.senado.es/web/composicionorganizacion/senadores/composicionsenado/modificacionescomposicion/designadosca/index.html)),
  a number that can change with the population. So the Senate's majority and its pivot are
  left out too. These figures come from a one-off check on 12 November 2026, not from the
  pipeline ([data/curated/senate.json](data/curated/senate.json)).
- **The count.** Counting errors and challenges are left out; recounts move few votes.
- **Not a forecast of government.** Who is invested follows from the 2023 votes; the power
  indices and the key are arithmetic, not predictions of who will govern.

## Reproduce

Requires [uv](https://docs.astral.sh/uv/). From the repository root, one command refetches the
polls and rebuilds everything, ending with the check:

```bash
uv run voteev all                  # --keep-polls: no refetch; --cutoff YYYY-MM-DD: older polls
```

Step by step, the same:

```bash
uv sync
uv run voteev download    # fetch the sources (polls are refetched each time)
uv run voteev prepare     # parse them into data/processed/
uv run voteev analyze     # backtests, the 2026 simulation and its variants: results/summary.json
uv run voteev figures     # figures/*.png
uv run voteev carousel    # in Spanish: carousel/carousel.pdf, slide-NN.png, slides.txt
uv run voteev carousel --lang en   # in English, in carousel/en/ (and the README's figures)
uv run voteev texts       # README.md and POST.md from their templates
uv run voteev check       # every number in the texts is in summary.json; no gaping lines
uv run pytest && uv run ruff check
```

The `Makefile` runs the same steps (`make all`, with `CUTOFF=YYYY-MM-DD` if wanted). `results/summary.json` is the only source of
the numbers in this README, the carousels and the post: README.md and POST.md are written from
templates in `src/spain_vote_ev/templates/`, so a rerun with new polls rewrites every number
and every word that depends on one. `voteev check` fails if a number in them is not in
summary.json, or is not written in its language's format (`76,000` and `94.2%` in English;
`76.000` and `94,2 %` in Spanish, with a no-break space before % and €), or if a justified line
of a carousel has a gap wider than twice a space; a page where justifying would leave one is
set ragged-right.

Fonts: STIX Two (SIL Open Font License, in `src/spain_vote_ev/fonts/`).

## Neutrality

The model treats every list with the same rules. Investiture votes come from recorded votes, not
from judgement. Figures use black, greys and one brown accent, never party colours. Nothing here
says how, or whether, anyone should vote; the numbers describe how much one vote can move a
seat or who is invested.

## References

- Arrow, K. J. (1951). *Social Choice and Individual Values*. Wiley.
- Banzhaf, J. F. (1965). Weighted voting doesn't work. *Rutgers Law Review* 19(2), 317–343.
- Bhatti, Y., Dahlgaard, J. O., Hansen, J. H., & Hansen, K. M. (2019). Is door-to-door
  canvassing effective in Europe? Evidence from a meta-study across six European countries.
  *British Journal of Political Science* 49(1), 279–290.
  [doi:10.1017/S0007123416000521](https://doi.org/10.1017/S0007123416000521)
- Cantoni, E., & Pons, V. (2021). Do interactions with candidates increase voter support and
  participation? Experimental evidence from Italy. *Economics & Politics* 33(2), 379–402.
  [doi:10.1111/ecpo.12167](https://doi.org/10.1111/ecpo.12167)
- Downs, A. (1957). *An Economic Theory of Democracy*. Harper.
- Edlin, A., Gelman, A., & Kaplan, N. (2007). Voting as a rational choice. *Rationality and
  Society* 19(3), 293–314.
- Gelman, A., Silver, N., & Edlin, A. (2012). What is the probability your vote will make a
  difference? *Economic Inquiry* 50(2), 321–326.
- Gibbard, A. (1973). Manipulation of voting schemes. *Econometrica* 41(4), 587–601.
- Green, D. P., McGrath, M. C., & Aronow, P. M. (2013). Field experiments and the study of voter
  turnout. *Journal of Elections, Public Opinion and Parties* 23(1), 27–48.
  [doi:10.1080/17457289.2012.728223](https://doi.org/10.1080/17457289.2012.728223)
- Kalla, J. L., & Broockman, D. E. (2018). The minimal persuasive effects of campaign contact
  in general elections. *American Political Science Review* 112(1), 148–166.
- Morales, L., Ramiro, L., & Jiménez-Buedo, M. (2023). Assessing the electoral payoffs of
  partisan mobilization in adverse contexts: a field experimental study of the 2011 Spanish
  local elections. In T. Faas et al. (Eds.), *Informationsflüsse, Wahlen und Demokratie*,
  213–246. Nomos. [doi:10.5771/9783748915553-213](https://doi.org/10.5771/9783748915553-213)
- Pons, V. (2018). Will a five-minute discussion change your mind? A countrywide experiment on
  voter choice in France. *American Economic Review* 108(6), 1322–1363.
  [doi:10.1257/aer.20160524](https://doi.org/10.1257/aer.20160524)
- Riker, W. H., & Ordeshook, P. C. (1968). A theory of the calculus of voting. *American
  Political Science Review* 62(1), 25–42.
- Satterthwaite, M. A. (1975). Strategy-proofness and Arrow's conditions. *Journal of Economic
  Theory* 10(2), 187–217.
- Shapley, L. S., & Shubik, M. (1954). A method for evaluating the distribution of power in a
  committee system. *American Political Science Review* 48(3), 787–792.
- Strøm, K. (1990). A behavioral theory of competitive political parties. *American Journal of
  Political Science* 34(2), 565–598.
