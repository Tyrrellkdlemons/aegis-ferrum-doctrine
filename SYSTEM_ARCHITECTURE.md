# An Automated “Filterless” Social-Media Content Generation System

## Academic exhibition dossier

### Curatorial thesis

“Filterless” is best understood as a deliberately provocative label, not a literal technical property. The system removes the traditional sequence of editor, producer, designer, and distributor as separate human gatekeepers, but it does not remove filters. Topic scoring filters the world before scripting; generative models filter it through training distributions; visual QA filters outputs through a brand rubric; and platforms filter publication through policy and recommendation systems. The machine is therefore an **automated editorial assemblage whose filters have moved into code, models, metrics, and interfaces**.

This distinction matters historically. Vannevar Bush’s 1945 “memex” imagined mechanized associative trails through a growing archive. J. C. R. Licklider’s 1960 “man-computer symbiosis” proposed a division of labor between human judgment and machine processing. Contemporary creator systems collapse those ideas into a single loop: retrieve, synthesize, render, distribute, observe, and revise. The loop is cybernetic in structure, but its output is cultural rather than industrial.

### System diagram

```text
                    ARCHIVAL / LIVE SIGNAL FIELD
       trends · search · forums · competitors · analytics · sources
                                  |
                                  v
                     +---------------------------+
                     |  1. STRATEGOS / SENSING   |
                     | collect -> verify -> rank |
                     +-------------+-------------+
                                   | topic brief + provenance
                                   v
                     +---------------------------+
                     |  2. SCRIPTOR / SYNTHESIS  |
                     | thesis -> script -> cuts  |
                     +------+------+-------------+
                            |      | \
                    narration      |  \ metadata / social derivatives
                            v      v   v
                  +------------+ +-------------+ +------------------+
                  | 3. VOCEM   | | 4. VISUALIS | | 5. PUBLICATOR   |
                  | voice/music| | frames/cards| | title/desc/tags  |
                  +------+-----+ +------+------+ +---------+--------+
                         |              |                  |
                         +-------+------+                  |
                                 v                         |
                    +---------------------------+          |
                    | 6. EDITORIUS / ASSEMBLY   |<---------+
                    | timing · motion · captions|
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | 7. PROMETHEUS / QA GATE   |
                    | technical + visual + truth|
                    +------+------+-------------+
                           veto | pass
                                v
                    +---------------------------+
                    | 8. PLATFORM PUBLICATION   |
                    | disclosure · rights · SEO |
                    +-------------+-------------+
                                  |
                                  v
                    +---------------------------+
                    | 9. ANALYTICA / FEEDBACK   |
                    | CTR · retention · quality |
                    +-------------+-------------+
                                  |
                                  +----> back to sensing

        CROSS-CUTTING CONTROL: task board · provenance · audit log · human veto
```

### Parts catalogue

#### 1. Signal acquisition and archival layer

The acquisition layer samples current attention from search, platforms, and community discourse, then stores both the observations and their provenance. Its crucial part is not scraping speed but **epistemic labeling**: a measured count, a search result, an anecdotal forum signal, and an agent inference must not be stored as if they have equal evidentiary status. The archive allows later curators to reconstruct why a topic was selected.

The historical analogue is Bush’s associative archive: useful records must be stored, consulted, and extended. Here, the “trail” is a reproducible chain from source to topic brief, not merely a pile of links.

#### 2. Strategos topic scorer

Strategos converts heterogeneous signals into a topic proposal. A defensible scorer includes audience fit, freshness, emotional relevance, search intent, saturation, evidence quality, production feasibility, and risk. The scorer should expose its weights and confidence. A single composite number without source-level support is theater, not analysis.

#### 3. Scriptor language engine

Scriptor turns the brief into an original argument. Its material parts are a hook, thesis, structure, evidence notes, practical protocol, counterclaim, and platform adaptations. The best measure is not word count but **transformative value**: what interpretive work did the channel add that a search summary or competitor imitation did not?

#### 4. Vocem audio engine

Vocem creates narration, music, and timing metadata. It must preserve intelligibility, rights provenance, and honest voice identity. A synthetic voice should not impersonate a real person. Loudness normalization and music ducking are production controls, while paragraph and word timing form the temporal spine for captions and editing.

#### 5. Visualis asset engine

Visualis produces thumbnails, scene frames, vertical adaptations, and carousel slides. It operates through prompt specifications, generated or licensed media, typography, layout, and aspect-ratio transforms. A style guide is a constraint system, not a substitute for visual content. Repeating a dark gradient, red stripe, and bold label across empty frames is templating, not B-roll.

#### 6. Editorius temporal compositor

Editorius joins voice, music, images, footage, captions, and transitions. The compositor must maintain semantic correspondence: the image shown should illuminate the sentence being spoken. Motion should be perceptible but not distracting, captions should be synchronized and readable, and audio should remain intelligible on phones and televisions.

#### 7. Prometheus quality gate

Prometheus is a veto layer. It combines technical validation (file integrity, streams, duration, resolution, loudness), visual inspection (legibility, hierarchy, artifact detection, scene variety), editorial review (originality, evidence, safety), and platform review (rights, disclosures, metadata truth). A contrast-and-color heuristic can assist inspection but cannot certify “quality” by itself.

#### 8. Publicator interface

Publicator writes metadata and transmits the finished work to a platform. This is where an internal file becomes public speech. It therefore carries the strongest provenance obligations: accurate title and description, actual links only, correct audience designation, synthetic-media disclosure, cleared rights, and an intentionally chosen privacy state.

#### 9. Analytica feedback controller

Analytica measures outcomes and returns them to planning. It should separate reach metrics (impressions, views), choice metrics (click-through rate), consumption metrics (retention, watch time), satisfaction proxies, and business outcomes. Feedback should improve future hypotheses without turning every decision into engagement maximization.

### Assembly narrative

The exhibit begins with an empty directory, representing the promise that automation can materialize an entire media operation from a prompt. Configuration files establish roles, thresholds, and brand rules. The sensing module records topical signals and promotes one into a brief. The language module expands the brief into a master script and simultaneously emits fragments for short video, threads, and carousels. Audio and visual modules convert the script into timed sound and imagery. The compositor aligns these streams into a rendered object. Prometheus then interrupts the apparent inevitability of the pipeline: it can return the work for revision, preserving the possibility that quality is not reducible to throughput. Publicator moves the object into a platform whose own candidate-generation and ranking systems determine visibility. Analytics closes the loop by turning audience behavior into the next cycle’s input.

The assembly also stages a contradiction. The system claims to be “filterless,” yet every joint is a filter. The absence of a conventional editor does not eliminate editorial power; it obscures and redistributes it. The responsible reconstruction therefore makes each filter legible through source records, manifests, thresholds, disclosures, and vetoes.

### Archival and scholarly sources

1. Bush, Vannevar. “As We May Think.” *The Atlantic Monthly* 176, no. 1 (July 1945). [W3C historical transcription](https://www.w3.org/History/1945/vbush/).
2. Licklider, J. C. R. “Man-Computer Symbiosis.” *IRE Transactions on Human Factors in Electronics* HFE-1 (1960): 4–11. [MIT CSAIL historical copy](https://groups.csail.mit.edu/medg/people/psz/Licklider.html).
3. Covington, Paul, Jay Adams, and Emre Sargin. “Deep Neural Networks for YouTube Recommendations.” *Proceedings of RecSys ’16* (2016). [Google Research publication](https://research.google/pubs/deep-neural-networks-for-youtube-recommendations/).
4. Anderson, Torin, and Shuo Niu. “Making AI-Enhanced Videos: Analyzing Generative AI Use Cases in YouTube Content Creation.” arXiv:2503.03134 (2025). [Paper record](https://arxiv.org/abs/2503.03134).
5. YouTube. “YouTube Channel Monetization Policies.” Current policy record, including the 2025 clarification on mass-produced and repetitive content. [Official policy](https://support.google.com/youtube/answer/1311392?hl=en-EN).
6. YouTube. “Disclosing Use of Altered or Synthetic Content.” [Official policy](https://support.google.com/youtube/answer/14328491).

### Exhibition note

The installation should present the ASCII diagram beside the live task board and source archive. A split-screen view can contrast an automated quality score with the actual thumbnail or video frame it claims to certify. That juxtaposition makes the system’s central question visible: **when editorial labor is automated, where does judgment go?**
