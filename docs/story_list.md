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
| M03 | The Adventure of the Cardboard Box | Memoirs or His Last Bow (834 / 2350) | Jim Browner | double murder | high | confirm which Gutenberg volume contains it |
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

