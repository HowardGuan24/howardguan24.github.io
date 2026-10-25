# Xinhao Guan's research website

Static GitHub Pages site for `https://howardguan24.github.io/` and the ProSing project page at `https://howardguan24.github.io/prosing-demo/`.

The ProSing demo is a standalone, English-language single page: project description, supported techniques, listening guide, then all Chinese and English samples. It has no navigation links, homepage links, or language-jump links. Baseline comparisons expand inline; the separate personal homepage is unchanged.

## Publishing

GitHub Pages publishes from the `main` branch, repository root. Edits to `index.html`, `prosing-demo/index.html`, or `assets/site.css` are published after a push to `main`.

## Adding audio demos

Place approved public audio files under `prosing-demo/audio/`. Add each example to `prosing-demo/index.html` with a labeled HTML `<audio controls>` element and accompanying source, target-technique, and result descriptions. Check permissions and singer consent before publishing recordings.

The current selection is maintained in `prosing-demo/demos.json`. To rebuild the static demo markup and copy the selected, verified questionnaire WAVs, run:

```bash
python3 prosing-demo/prepare_demos.py --library /absolute/path/to/questionnaire_2026-10-25
```

The generator updates only the marked demo block in `prosing-demo/index.html` and writes `prosing-demo/audio-manifest.json` with the original questionnaire revision and audio checksums. Chinese examples appear first, followed by English examples; each language has six single-technique and two composite examples. Source and ProSing comparisons appear immediately, with baseline audio under expandable comparisons. All players use `preload="none"`.

Reviewed regenerations can be specified per model using `audio_overrides` in `demos.json`. Their source WAVs and provenance are retained under `prosing-demo/custom-audio/`, and the generator verifies their checksums just like questionnaire audio. The English `en_vibrato_02` and `en_combo_01` ProSing outputs use the approved ±40-cent, 5-Hz vibrato versions. Their baseline audio is unchanged from the questionnaire, as noted beside the baseline players. Do not replace files in the original questionnaire library to update public demos.

## Visitor analytics

The ProSing demo page includes the Cloudflare Web Analytics snippet for `howardguan24.github.io`. View reports in Cloudflare under **Observability → Analytics → Web analytics**, selecting this hostname and filtering the path to `/prosing-demo/` when needed. The personal homepage does not currently include the snippet.

Analytics starts after installation; visits before installation cannot be recovered. The beacon token in the public HTML identifies the analytics site and is not an account API credential. Preserve the snippet when updating the demo page.
