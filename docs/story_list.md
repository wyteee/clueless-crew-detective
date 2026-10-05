# Candidate story list (5 pilot + 30 main + reserves)

> **Culprit names below are recalled from memory and are NOT ground truth.** They exist only to pre-screen. Every row must be confirmed by reading the text; `manifest/annotations.csv` is the source of truth.

## Pilot (5) - development only, excluded from cross-validation

| ID | Title | Source (PG #) | Expected culprit (unverified) | Crime | Conf. | Exclusion risk / note |
|---|---|---|---|---|---|---|
| P1 | The Adventure of the Speckled Band | The Adventures of Sherlock Holmes (1661) | Dr. Grimesby Roylott | murder | high |  |
| P2 | The Red-Headed League | The Adventures of Sherlock Holmes (1661) | John Clay (alias: Vincent Spaulding / William Morris) | attempted robbery | high | good alias test |
| P3 | The Adventure of the Blue Carbuncle | The Adventures of Sherlock Holmes (1661) | James Ryder | theft | high | maid Catherine Cusack is a minor accomplice |
| P4 | A Case of Identity | The Adventures of Sherlock Holmes (1661) | James Windibank (alias: Hosmer Angel) | fraud | high | good alias test; not a violent crime |
| P5 | The Adventure of the Copper Beeches | The Adventures of Sherlock Holmes (1661) | Jephro Rucastle | unlawful confinement | medium | crime type borderline; swap if the team prefers |

## Main corpus - likely eligible (19)

| ID | Title | Source (PG #) | Expected culprit (unverified) | Crime | Conf. | Exclusion risk / note |
|---|---|---|---|---|---|---|
| M01 | The Boscombe Valley Mystery | The Adventures of Sherlock Holmes (1661) | John Turner | murder | high |  |
| M02 | The Adventure of the Naval Treaty | The Memoirs of Sherlock Holmes (834) | Joseph Harrison | theft | high |  |
| M03 | The Adventure of the Cardboard Box | The Memoirs of Sherlock Holmes (834) | Jim Browner | double murder | high | in PG #834 (story II); not in PG #2350 |
| M04 | The Adventure of the Empty House | The Return of Sherlock Holmes (108) | Colonel Sebastian Moran | murder | high |  |
| M05 | The Adventure of the Norwood Builder | The Return of Sherlock Holmes (108) | Jonas Oldacre | frame-up (no completed murder) | high | no actual victim; crime is the frame-up |
| M06 | The Adventure of the Dancing Men | The Return of Sherlock Holmes (108) | Abe Slaney | murder | high |  |
| M07 | The Adventure of Black Peter | The Return of Sherlock Holmes (108) | Patrick Cairns | murder | high |  |
| M08 | The Adventure of the Six Napoleons | The Return of Sherlock Holmes (108) | Beppo | murder / theft | medium | check who is named as culprit at reveal |
| M09 | The Adventure of the Abbey Grange | The Return of Sherlock Holmes (108) | Captain Jack Croker | homicide | medium | justified-killing framing; others conceal facts |
| M10 | The Adventure of the Dying Detective | His Last Bow (2350) | Culverton Smith | murder | high |  |
| M11 | The Adventure of the Three Garridebs | The Case-Book of Sherlock Holmes (69700) | 'Killer' Evans (alias: John Garrideb) | counterfeiting / shooting | high | good alias test |
| M12 | The Adventure of the Retired Colourman | The Case-Book of Sherlock Holmes (69700) | Josiah Amberley | double murder | high |  |
| M13 | A Study in Scarlet | A Study in Scarlet (244) | Jefferson Hope | murder | high | long; two-part structure; annotate last |
| M14 | The Hound of the Baskervilles | The Hound of the Baskervilles (2852) | Jack Stapleton (alias: Vandeleur) | murder | high | long; good alias test; annotate last |
| M15 | The Blue Cross (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | Flambeau | theft | high | different author and style |
| M16 | The Secret Garden (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | Aristide Valentin | murder | high |  |
| M17 | The Invisible Man (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | Isidore Smythe | murder | high |  |
| M18 | The Hammer of God (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | Rev. Wilfred Bohun | murder | high |  |
| M19 | The Flying Stars (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | Flambeau | theft | high |  |

## Main corpus - screen carefully (11); expect some to be excluded

| ID | Title | Source (PG #) | Expected culprit (unverified) | Crime | Conf. | Exclusion risk / note |
|---|---|---|---|---|---|---|
| M20 | The Adventure of the Beryl Coronet | The Adventures of Sherlock Holmes (1661) | Sir George Burnwell | theft | medium | Mary Holder may count as second culprit |
| M21 | The Adventure of the Bruce-Partington Plans | His Last Bow (2350) | Colonel Valentine Walter | treason / murder | medium | Oberstein is an accomplice -> maybe multiple |
| M22 | The Adventure of the Three Gables | The Case-Book of Sherlock Holmes (69700) | Isadora Klein | conspiracy / burglary | low | acts through hired thugs |
| M23 | The Adventure of the Three Students | The Return of Sherlock Holmes (108) | Gilchrist | cheating | medium | may be non-criminal |
| M24 | Silver Blaze | The Memoirs of Sherlock Holmes (834) | John Straker | attempted horse-lamer / theft | low | culprit dies; crime type unclear |
| M25 | The Adventure of the Second Stain | The Return of Sherlock Holmes (108) | Madame Fournaye (killer of Lucas) / Lady Hilda (letter) | murder / theft | low | two candidate culprits |
| M26 | The Adventure of the Golden Pince-Nez | The Return of Sherlock Holmes (108) | Anna (surname uncertain) | homicide | low | culprit identity unclear from memory |
| M27 | The 'Gloria Scott' | The Memoirs of Sherlock Holmes (834) | Hudson | blackmail / past mutiny | low | may be non-criminal in present timeline |
| M28 | The Adventure of the Priory School | The Return of Sherlock Holmes (108) | Reuben Hayes / James Wilder | murder / kidnapping | low | likely multiple culprits |
| M29 | The Musgrave Ritual | The Memoirs of Sherlock Holmes (834) | Rachel Howells | manslaughter | low | may be unresolved |
| M30 | The Adventure of the Illustrious Client | The Case-Book of Sherlock Holmes (69700) | Baron Adelbert Gruner | attempted murder / abuse | low | crime by Gruner may not occur in-story |

## Reserves - use to replace excluded stories

| ID | Title | Source (PG #) | Expected culprit (unverified) | Crime | Conf. | Exclusion risk / note |
|---|---|---|---|---|---|---|
| R01 | The Queer Feet (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | ? | ? | low | screen before use |
| R02 | The Wrong Shape (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | ? | ? | low | screen before use |
| R03 | The Eye of Apollo (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | ? | ? | low | screen before use |
| R04 | The Sign of the Broken Sword (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | ? | ? | low | screen before use |
| R05 | The Sins of Prince Saradine (Father Brown) | The Innocence of Father Brown (Chesterton) (204) | ? | ? | low | screen before use |


## Extra reserves (added 2026-10-05, unscreened)

All remaining stories in the books already downloaded. No culprit is pre-filled; screen reveal-first (guideline v0.8).

| ID | Title | Source (PG #) |
|---|---|---|
| R06 | A Scandal in Bohemia | The Adventures of Sherlock Holmes (1661) |
| R07 | The Five Orange Pips | The Adventures of Sherlock Holmes (1661) |
| R08 | The Man with the Twisted Lip | The Adventures of Sherlock Holmes (1661) |
| R09 | The Adventure of the Engineer’s Thumb | The Adventures of Sherlock Holmes (1661) |
| R10 | The Adventure of the Noble Bachelor | The Adventures of Sherlock Holmes (1661) |
| R11 | The Yellow Face | The Memoirs of Sherlock Holmes (834) |
| R12 | The Stockbroker’s Clerk | The Memoirs of Sherlock Holmes (834) |
| R13 | The Reigate Squires | The Memoirs of Sherlock Holmes (834) |
| R14 | The Crooked Man | The Memoirs of Sherlock Holmes (834) |
| R15 | The Resident Patient | The Memoirs of Sherlock Holmes (834) |
| R16 | The Greek Interpreter | The Memoirs of Sherlock Holmes (834) |
| R17 | The Final Problem | The Memoirs of Sherlock Holmes (834) |
| R18 | The Adventure of the Solitary Cyclist | The Return of Sherlock Holmes (108) |
| R19 | The Adventure of Charles Augustus Milverton | The Return of Sherlock Holmes (108) |
| R20 | The Adventure of the Missing Three-quarter | The Return of Sherlock Holmes (108) |
| R21 | The Adventure of Wisteria Lodge | His Last Bow (2350) |
| R22 | The Adventure of the Devil’s Foot | His Last Bow (2350) |
| R23 | The Adventure of the Red Circle | His Last Bow (2350) |
| R24 | The Disappearance of Lady Frances Carfax | His Last Bow (2350) |
| R25 | His Last Bow: the War Service of Sherlock Holmes | His Last Bow (2350) |
| R26 | The Adventure of the Blanched Soldier | The Case-Book of Sherlock Holmes (69700) |
| R27 | The Adventure of the Mazarin Stone | The Case-Book of Sherlock Holmes (69700) |
| R28 | The Adventure of the Sussex Vampire | The Case-Book of Sherlock Holmes (69700) |
| R29 | The Problem of Thor Bridge | The Case-Book of Sherlock Holmes (69700) |
| R30 | The Adventure of the Creeping Man | The Case-Book of Sherlock Holmes (69700) |
| R31 | The Adventure of the Lion's Mane | The Case-Book of Sherlock Holmes (69700) |
| R32 | The Adventure of the Veiled Lodger | The Case-Book of Sherlock Holmes (69700) |
| R33 | The Adventure of Shoscombe Old Place | The Case-Book of Sherlock Holmes (69700) |
| R34 | The Honour of Israel Gow (Father Brown) | The Innocence of Father Brown (Chesterton) (204) |
| R35 | The Three Tools of Death (Father Brown) | The Innocence of Father Brown (Chesterton) (204) |

## Agatha Christie, Poirot Investigates (PG #61262; added 2026-10-05, unscreened)

Public domain in the US (1924). No culprit is pre-filled; screen reveal-first (guideline v0.8).

| ID | Title |
|---|---|
| C01 | The Adventure of “The Western Star” |
| C02 | The Tragedy at Marsdon Manor |
| C03 | The Adventure of the Cheap Flat |
| C04 | The Mystery of Hunter’s Lodge |
| C05 | The Million Dollar Bond Robbery |
| C06 | The Adventure of the Egyptian Tomb |
| C07 | The Jewel Robbery at the Grand Metropolitan |
| C08 | The Kidnapped Prime Minister |
| C09 | The Disappearance of Mr. Davenheim |
| C10 | The Adventure of the Italian Nobleman |
| C11 | The Case of the Missing Will |
