# Xinhao Guan's research website

Static GitHub Pages site for `https://howardguan24.github.io/` and the ProSing project page at `https://howardguan24.github.io/prosing-demo/`.

## Publishing

GitHub Pages publishes from the `main` branch, repository root. Edits to `index.html`, `prosing-demo/index.html`, or `assets/site.css` are published after a push to `main`.

## Adding audio demos

Place approved public audio files under `prosing-demo/audio/`. Add each example to `prosing-demo/index.html` with a labeled HTML `<audio controls>` element and accompanying source, target-technique, and result descriptions. Check permissions and singer consent before publishing recordings.

## Visitor analytics

The ProSing demo page includes the Cloudflare Web Analytics snippet for `howardguan24.github.io`. View reports in Cloudflare under **Observability → Analytics → Web analytics**, selecting this hostname and filtering the path to `/prosing-demo/` when needed. The personal homepage does not currently include the snippet.

Analytics starts after installation; visits before installation cannot be recovered. The beacon token in the public HTML identifies the analytics site and is not an account API credential. Preserve the snippet when updating the demo page.
