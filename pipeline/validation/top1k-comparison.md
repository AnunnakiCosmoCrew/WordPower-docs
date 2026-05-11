# Top-1k Validation — Gemini 2.5 Flash vs Claude Haiku 4.5

Same 1000 SUBTLEX-US words, same prompt-v1, same forced-tool-call schema. Haiku results from PR #539; Gemini results from this validation run.

## Headline

| Metric | Haiku 4.5 | Gemini 2.5 Flash |
|---|---|---|
| Cost ($1000 words) | $1.7058 | $1.8998 |
| Confidence: high | 186 | 157 |
| Confidence: medium | 14 | 3 |
| Confidence: low | 800 | 840 |

## Cross-model agreement

- **Agreement rate:** 901/1000 = **90.1%** (threshold ≥ 90% → **PASS**)
- Shape disagreements (both decomposed, different morpheme count or confidence): 7
- Only Haiku decomposed (Gemini refused): 66
- Only Gemini decomposed (Haiku refused): 26

## Verdict

**Gemini validated. Locked-architecture switch should proceed.** Gemini agrees with Haiku on at least 90% of the top-1k production words. Combined with the -30% cost from Spike D, switching to Gemini for the top-10k production build is the right call.

## Shape disagreements (first 25)

| Word | Haiku conf | Gemini conf | Haiku morphemes | Gemini morphemes |
|---|---|---|---|---|
| `different` | medium | high | differ + -ent | dif- + fer + -ent |
| `lawyer` | high | medium | law + -yer | law + -yer |
| `remember` | medium | high | re- + member + -er | re- + member |
| `sometimes` | medium | high | some + -times | some + time + -s |
| `supposed` | high | medium | sup- + pos + -ed | sup- + pos + -ed |
| `surprise` | high | medium | sur- + prise | sur- + prise |
| `terrible` | medium | high | terr + -ible | terr + -ible |

## Only Haiku decomposed (Gemini refused) — first 25

These are cases where Haiku tried; Gemini said low-confidence. Manual review needed: are these legitimate decompositions Gemini is missing, or false-positives Gemini is correctly refusing?

| Word | Haiku conf | Haiku decomp |
|---|---|---|
| `Alright` | medium | all + right |
| `American` | medium | America + -n |
| `Captain` | medium | capit + -ain |
| `Congratulations` | high | con- + gratulat + -ion |
| `English` | high | Angle + -ish |
| `Goodbye` | high | good + bye |
| `Lieutenant` | high | lieu- + -ten- + -ant |
| `Major` | medium | maj |
| `across` | high | a- + cross |
| `ahead` | high | a- + head |
| `already` | high | all + ready |
| `amazing` | high | a- + maze + -ing |
| `around` | high | a- + round |
| `attack` | high | at- + tack |
| `beautiful` | high | beauty + -ful |
| `before` | high | be- + fore |
| `behind` | medium | be- + hind |
| `believe` | medium | be- + lieve |
| `between` | high | be- + tween |
| `called` | high | call + -ed |
| `cannot` | high | can + not |
| `certain` | high | cert + -ain |
| `college` | high | col- + leg |
| `control` | medium | con- + trol |
| `course` | medium | cour + -e |

## Only Gemini decomposed (Haiku refused) — first 25

These are cases where Gemini tried; Haiku said low-confidence. Manual review needed: legitimate or false-positive?

| Word | Gemini conf | Gemini decomp |
|---|---|---|
| `accident` | high | ac- + cid + -ent |
| `being` | high | be + -ing |
| `broken` | high | brok + -en |
| `business` | high | busi + -ness |
| `enjoy` | high | en- + joy |
| `eyes` | high | eye + -s |
| `forever` | high | for + ever |
| `funny` | high | fun + -y |
| `girls` | high | girl + -s |
| `given` | high | give + -en |
| `going` | high | go + -ing |
| `hands` | high | hand + -s |
| `happened` | high | happen + -ed |
| `himself` | high | him + self |
| `kids` | high | kid + -s |
| `likes` | high | like + -s |
| `lucky` | high | luck + -y |
| `needs` | high | need + -s |
| `ones` | high | one + -s |
| `shoes` | high | shoe + -s |
| `somewhere` | high | some + where |
| `things` | high | thing + -s |
| `thinks` | high | think + -s |
| `wedding` | high | wed + -ing |
| `whatever` | high | what + ever |
