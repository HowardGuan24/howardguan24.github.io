#!/usr/bin/env python3
"""Copy selected questionnaire audio and render buildless, offline-friendly demos."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from typing import Any


PAGE_ROOT = Path(__file__).resolve().parent
MODEL_ORDER = ('prosinger', 'tcsinger', 'vevo')
MODEL_FILENAMES = {'prosinger': 'prosing.wav', 'tcsinger': 'tcsinger.wav', 'vevo': 'vevo.wav'}
MODEL_LABELS = {'prosinger': 'ProSing', 'tcsinger': 'TCSinger', 'vevo': 'Vevo'}


def escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def digest_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render_player(path: str, label: str, case_id: str, primary: bool = False) -> str:
    """Preload no audio: opening the page must not download every comparison."""
    extra_class = ' audio-player-primary' if primary else ''
    return (
        f'<div class="audio-player{extra_class}"><span class="audio-label">{escape(label)}</span>'
        f'<audio controls preload="none" aria-label="{escape(case_id)}: {escape(label)}">'
        f'<source src="{escape(path)}" type="audio/wav">'
        f'<a href="{escape(path)}">Download audio</a></audio></div>'
    )


def render_case(case: dict[str, Any], audio: dict[str, str], number: int, language: str) -> str:
    parts = case.get('lyric_parts', [])
    lyric_text = ''.join(
        f'<mark title="{escape(part["technique"])}">{escape(part["text"])}</mark>'
        if part.get('technique') else escape(part['text']) for part in parts
    )
    lyrics = f'<p class="sample-lyrics" lang="{language}">{lyric_text}</p>' if parts else ''
    instructions = ''.join(f'<li>{escape(line)}</li>' for line in case['instructions'])
    primary_audio = render_player(audio['source'], 'Source', case['case_id'])
    primary_audio += render_player(audio['prosinger'], 'ProSing (ours)', case['case_id'], True)
    baseline_audio = ''.join(
        render_player(audio[method], MODEL_LABELS[method], case['case_id'])
        for method in ('tcsinger', 'vevo') if method in audio
    )
    baseline_note = (
        f'<p class="listening-note">{escape(case["baseline_note"])}</p>'
        if case.get('baseline_note') else ''
    )
    return f'''<article class="demo-card" id="{escape(case['case_id'])}">
  <div class="demo-card-top"><span class="sample-family">{escape(case['family'])}</span><span class="sample-number">{number:02d}</span></div>
  <h5>{escape(case['title'])}</h5>
  <span class="sample-scope">{escape(case['scope'])}</span>
{lyrics}
  <ul class="sample-instructions">{instructions}</ul>
  <div class="audio-pair">{primary_audio}</div>
  <details class="baseline-comparisons"><summary>Compare with baselines</summary>{baseline_note}<div class="audio-pair">{baseline_audio}</div></details>
</article>'''


def render_section(language_key: str, selection: dict[str, Any], cards: dict[str, str]) -> str:
    language_name = {'chinese': 'Chinese', 'english': 'English'}[language_key]
    if not selection['single'] and not selection['composite']:
        return f'''<section class="language-demos language-demos-pending" id="{language_key}-demos" aria-labelledby="{language_key}-title">
  <div class="language-heading"><h3 id="{language_key}-title">{language_name} samples</h3><span class="language-count">In preparation</span></div>
  <p class="language-note">English examples are being prepared and will be added here.</p>
</section>'''
    groups = []
    for kind, heading in (('single', 'Single-technique control'), ('composite', 'Multi-technique control')):
        sample_cards = '\n'.join(cards[case['case_id']] for case in selection[kind])
        count = len(selection[kind])
        groups.append(f'''<section class="technique-demos" aria-labelledby="{language_key}-{kind}-title">
  <div class="demo-group-heading"><h4 id="{language_key}-{kind}-title">{heading}</h4><span>{count} {'example' if count == 1 else 'examples'}</span></div>
  <div class="demo-grid">{sample_cards}</div>
</section>''')
    counts = f'{len(selection["single"])} single-technique · {len(selection["composite"])} multi-technique'
    return f'''<section class="language-demos" id="{language_key}-demos" aria-labelledby="{language_key}-title">
  <div class="language-heading"><h3 id="{language_key}-title">{language_name} samples</h3><span class="language-count">{counts}</span></div>
  {''.join(groups)}
</section>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', required=True, type=Path, help='Verified local questionnaire library directory')
    args = parser.parse_args()
    library_manifest = json.loads((args.library / 'manifest.json').read_text(encoding='utf-8'))
    selection = json.loads((PAGE_ROOT / 'demos.json').read_text(encoding='utf-8'))
    library_cases = {case['case_id']: case for case in library_manifest['cases']}
    copied_files: list[dict[str, Any]] = []
    cards: dict[str, str] = {}
    used_cases: set[str] = set()
    for language_key in ('chinese', 'english'):
        language = {'chinese': 'zh', 'english': 'en'}[language_key]
        section = selection[language_key]
        if section['single'] and len(section['single']) != 6:
            raise ValueError(f'{language_key}: expected six single-technique examples')
        if len(section['composite']) > 2:
            raise ValueError(f'{language_key}: expected at most two multi-technique examples')
        for number, case in enumerate(section['single'] + section['composite'], start=1):
            case_id = case['case_id']
            if case_id in used_cases:
                raise ValueError(f'Duplicate selection: {case_id}')
            used_cases.add(case_id)
            original = library_cases[case_id]
            expected_kind = 'single' if case in section['single'] else 'composite'
            if original['language'] != language or original['kind'] != expected_kind:
                raise ValueError(f'Case language/kind mismatch: {case_id}')
            source_items = {item['model'] or 'source': item for item in original['audio']}
            paths = {}
            for method in ('source', *MODEL_ORDER):
                if method not in source_items:
                    continue
                item = source_items[method]
                source = args.library / item['path']
                override = case.get('audio_overrides', {}).get(method)
                if override:
                    # Keep reviewed regenerations separate from the immutable questionnaire archive.
                    source = (PAGE_ROOT / override['path']).resolve()
                    if not source.is_relative_to(PAGE_ROOT.resolve()):
                        raise ValueError(f'Override must stay inside the demo directory: {source}')
                metadata = override or item
                if digest_file(source) != metadata['sha256']:
                    raise ValueError(f'Local audio changed: {source}')
                filename = 'source.wav' if method == 'source' else MODEL_FILENAMES[method]
                relative_path = f'audio/{language}/{case_id}/{filename}'
                destination = PAGE_ROOT / relative_path
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
                if digest_file(destination) != metadata['sha256']:
                    raise ValueError(f'Copied audio hash mismatch: {destination}')
                paths[method] = relative_path
                copied_files.append({
                    'case_id': case_id, 'language': language, 'model': method,
                    'path': relative_path, 'sha256': metadata['sha256'],
                    'duration_seconds': metadata['duration_seconds'],
                    'questionnaire_path': None if override else item['original_path'],
                    **({'source': override['path'], 'provenance': override['provenance'],
                        'replaces_questionnaire_path': item['original_path']} if override else {}),
                })
            cards[case_id] = render_case(case, paths, number, language)

    content = '''<div class="demos-intro">
  <div class="section-label">03 / Listen</div>
  <div><h2 id="demos-title">Hear the control.</h2>
    <p>Compare each source performance with the requested conversion. Explore timbral changes, localized pitch edits, and combined techniques in the examples below.</p>
    <p class="listening-note">Highlighted lyrics indicate the edited regions. For timbral examples, the control applies to the entire excerpt. Expand any example to hear the baseline systems.</p>
    <nav class="demo-language-nav" aria-label="Demo languages"><a href="#chinese-demos">Chinese samples <span aria-hidden="true">↓</span></a><a href="#english-demos">English samples <span aria-hidden="true">↓</span></a></nav>
  </div>
</div>'''
    content += '\n' + '\n'.join(render_section(key, selection[key], cards) for key in ('chinese', 'english'))
    page_path = PAGE_ROOT / 'index.html'
    page = page_path.read_text(encoding='utf-8')
    updated, matches = re.subn(
        r'(?<=<!-- DEMOS:START -->).*?(?=<!-- DEMOS:END -->)',
        lambda _: '\n' + content + '\n      ', page, flags=re.DOTALL,
    )
    if matches != 1:
        raise ValueError('Expected exactly one DEMOS:START/END block')
    page_path.write_text(updated, encoding='utf-8')
    provenance = {
        'questionnaire_repository': library_manifest['repository'],
        'questionnaire_revision': library_manifest['revision'],
        'note': 'Byte-identical copies of selected questionnaire audio or explicitly reviewed regenerations. Regenerated files record their source and provenance; no cropping, resampling, or gain changes are applied by this builder.',
        'selection': {key: {kind: [case['case_id'] for case in selection[key][kind]] for kind in ('single', 'composite')} for key in selection},
        'audio_files': copied_files,
    }
    (PAGE_ROOT / 'audio-manifest.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Prepared {len(cards)} examples / {len(copied_files)} WAV files. English examples: {len(selection["english"]["single"]) + len(selection["english"]["composite"])}.')


if __name__ == '__main__':
    main()
