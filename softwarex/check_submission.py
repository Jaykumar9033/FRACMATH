"""Check the local manuscript/package against the March 2026 template.

This checks inspectable files and limits; it does not predict acceptance.
Run from any folder: python softwarex/check_submission.py
"""
import hashlib
import json
from pathlib import Path
import re


def words(text):
    text = re.sub(r'(?m)^\s*%.*$', '', text)
    text = re.sub(r'\\(?:label|ref|eqref|citep|citet)\{[^}]*\}', '', text)
    text = re.sub(r'\\href\{[^}]*\}\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[A-Za-z]+\*?', ' ', text)
    return re.findall(r"[A-Za-z0-9]+(?:['-][A-Za-z0-9]+)*", text)


def main():
    package = Path(__file__).resolve().parent
    repo = package.parent
    text = (package / 'manuscript.tex').read_text(encoding='utf-8')
    abstract = re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}', text, re.S).group(1)
    keywords = re.search(r'\\begin\{keyword\}(.*?)\\end\{keyword\}', text, re.S).group(1)
    body = text.split(r'\section*{Motivation and significance}', 1)[1].split(r'\section*{Data availability}', 1)[0]
    # The template excludes metadata, tables, figures, and references from the body.
    for environment in ['table', 'figure']:
        body = re.sub(r'\\begin\{' + environment + r'\}.*?\\end\{' + environment + r'\}', '', body, flags=re.S)
    main_sections = ['Motivation and significance', 'Software description', 'Illustrative examples', 'Impact', 'Conclusions']
    checks = {
        'five_required_sections': all(r'\section*{' + title + '}' in text for title in main_sections),
        'figure_count_at_most_six': text.count(r'\begin{figure}') <= 6,
        'keyword_count_at_most_six': len(keywords.split(r'\sep')) <= 6,
        'abstract_approximately_100_words': 80 <= len(words(abstract)) <= 120,
        'main_text_below_4000_words': len(words(body)) < 4000,
        'metadata_C1_to_C8': all('C%d &' % index in text for index in range(1, 9)),
        'GitHub_code_link': 'https://github.com/Jaykumar9033/FRACMATH/' in text,
        'package_license': (package / 'Licence.txt').exists(),
        'beginner_entry_and_guide': all((package / name).exists() for name in ['start_here.m', 'BEGINNER_GUIDE.md']),
        'six_figure_assets': all((package / 'figures' / name).exists() for name in [
            'load_cmod_verified.png', 'damage_verified.png', 'scaling_timings.pdf',
            'nooru_damage_evolution_shared_bar.png', 'torsion_damage_evolution_shared_bar.png',
            'mesh_study_overview.pdf']),
        'declarations': all(title in text for title in ['CRediT authorship contribution statement',
                                                      'Declaration of competing interest', 'Declaration of AI-assisted technologies']),
        'five_highlights_at_most_85_characters': len([line for line in (package / 'highlights.txt').read_text().splitlines()
                                                    if line.startswith('- ')]) == 5 and all(
            len(line[2:]) <= 85 for line in (package / 'highlights.txt').read_text().splitlines() if line.startswith('- ')),
        'first_presentation_wording': not re.search(r'\b(?:corrected|updated|revision|AES)\b', text, re.I),
    }
    if (repo / '3pb/matlab/solver_main_3pb.m').exists():
        checks['solver_copies_identical'] = ((repo / '3pb/matlab/solver_main_3pb.m').read_bytes()
                                              == (package / 'reproducibility/2d/solver_main_3pb.m').read_bytes())
        checks['repository_readme_and_license'] = (repo / 'README.md').exists() and (repo / 'Licence.txt').exists()
    report = dict(template='SoftwareX original software article, Version 6 (March 2026)',
                  template_url='https://legacyfileshare.elsevier.com/promis_misc/softwarex-osp-template.docx',
                  abstract_words=len(words(abstract)), main_text_words_estimate=len(words(body)),
                  word_count_scope='Includes equations and code; excludes metadata, tables, figures and references.',
                  figures=text.count(r'\begin{figure}'), keywords=len(keywords.split(r'\sep')),
                  manuscript_sha256=hashlib.sha256((package / 'manuscript.tex').read_bytes()).hexdigest(),
                  checks=checks, all_file_checks_pass=all(checks.values()),
                  manual_checks=['Inspect compiled PDF layout.', 'Verify version-specific release and DOI.',
                                 'Authors confirm declarations and final submission details.'],
                  interpretation='File and formatting checks are not a prediction of editorial acceptance.')
    (package / 'submission_checks.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2))
    if not all(checks.values()):
        raise SystemExit('Submission file checks failed')


if __name__ == '__main__':
    main()
