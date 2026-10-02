"""Independent v0.8 validator holdout. Author labels before any candidate gate edit.

Raw synthetic text is generated only into ignored build/. Whole request families
are frozen; this is evaluation data, never a prompt-tuning or training corpus.
"""
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
ROOT = TASK.parents[1]
INTENTS = ['start_focus', 'pause_focus', 'alarm', 'timer', 'open_app', 'explain', 'unknown']


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cases():
    rows = []

    def add(family, intent, entries):
        for text, kind, hour, minute, seconds in entries:
            rows.append(dict(id=f'v08_{len(rows):03d}', family=family,
                             utterance=text, oracle_intent=intent,
                             expected_kind=kind, hour=hour, minute=minute, seconds=seconds))

    def action(text, kind, seconds=0, hour=0, minute=0):
        return text, kind, hour, minute, seconds

    def reject(text):
        return action(text, 'UNKNOWN')

    add('focus_friendly_immediate', 'start_focus', [
        action('Hi Mira, begin a concentration session please.', 'START_FOCUS'),
        action('Mira, help me get into focus mode.', 'START_FOCUS')])
    add('focus_companion_wrapper', 'start_focus', [
        action('Could you switch on focus mode for me?', 'START_FOCUS'),
        action('I would like you to begin my study session.', 'START_FOCUS')])
    add('focus_numeric_countdown', 'start_focus', [
        action('Please begin my focus session for 43 seconds.', 'START_FOCUS', 43),
        action('Hey Mira, start concentration for 18 minutes, please.', 'START_FOCUS', 1080)])
    add('focus_english_countdown', 'start_focus', [
        action('Begin focus for thirty two seconds.', 'START_FOCUS', 32),
        action('Please start a study session for eleven minutes.', 'START_FOCUS', 660)])
    add('focus_resume_immediate', 'start_focus', [
        action('Resume my concentration session, please.', 'START_FOCUS'),
        action('Mira, carry on with my focus session.', 'START_FOCUS')])
    add('focus_duration_boundaries', 'start_focus', [
        action('Begin concentration for one second.', 'START_FOCUS', 1),
        action('Please begin a 120 minute study session.', 'START_FOCUS', 7200)])
    add('pause_friendly_immediate', 'pause_focus', [
        action('Mira, stop my concentration session please.', 'PAUSE_FOCUS'),
        action('Could you pause focus mode for me?', 'PAUSE_FOCUS')])
    add('pause_everyday_phrasing', 'pause_focus', [
        action('End my deep work session, please.', 'PAUSE_FOCUS'),
        action('I would like you to halt my study session.', 'PAUSE_FOCUS')])
    add('status_focus_domain', 'explain', [
        action('Mira, tell me my focus status.', 'EXPLAIN'),
        action('How is my concentration session going?', 'EXPLAIN')])
    add('status_direct_summary', 'explain', [
        action('Please give me a focus summary.', 'EXPLAIN'),
        action('Could you show me the focus status?', 'EXPLAIN')])
    add('status_nudge_reason', 'explain', [
        action('Why did Mira warn me during focus?', 'EXPLAIN'),
        action('Please explain the concentration reminder.', 'EXPLAIN')])
    add('alarm_colon_time', 'alarm', [
        action('Hi Mira, set my alarm to 06:42 please.', 'ALARM', hour=6, minute=42),
        action('Could you create an alarm at 9:17 PM for me?', 'ALARM', hour=21, minute=17)])
    add('alarm_english_time', 'alarm', [
        action('Please set an alarm for eight twenty three AM.', 'ALARM', hour=8, minute=23),
        action('Wake me at ten forty six PM.', 'ALARM', hour=22, minute=46)])
    add('alarm_english_hour_boundary', 'alarm', [
        action('Mira, set an alarm for twelve fifteen AM.', 'ALARM', hour=0, minute=15),
        action('Create an alarm at twelve fifty nine PM please.', 'ALARM', hour=12, minute=59)])
    add('timer_numeric_duration', 'timer', [
        action('Could you set a countdown for 37 seconds please?', 'TIMER', 37),
        action('Mira, begin a timer lasting 14 minutes.', 'TIMER', 840)])
    add('timer_english_duration', 'timer', [
        action('Please start a forty three second timer.', 'TIMER', 43),
        action('Make a countdown for twenty six minutes.', 'TIMER', 1560)])
    add('timer_bounded_seconds', 'timer', [
        action('Set a timer for 3600 seconds, please.', 'TIMER', 3600),
        action('Start a timer for one hundred twenty minutes.', 'TIMER', 7200)])
    add('app_friendly_settings', 'open_app', [
        action('Hi Mira, take me to Settings please.', 'OPEN_SETTINGS'),
        action('Could you bring up the Settings app for me?', 'OPEN_SETTINGS')])
    add('app_friendly_calculator', 'open_app', [
        action('Mira, launch the Calculator application please.', 'OPEN_CALCULATOR'),
        action('I would like you to open Calculator.', 'OPEN_CALCULATOR')])
    add('app_friendly_clock', 'open_app', [
        action('Please bring up Clock.', 'OPEN_CLOCK'),
        action('Could you take me to the Clock app?', 'OPEN_CLOCK')])
    add('focus_signed_duration', 'start_focus', [
        reject('Begin concentration for +23 minutes.'),
        reject('Mira, begin focus for -17 seconds.')])
    add('timer_signed_duration', 'timer', [
        reject('Start a countdown for -29 seconds.'),
        reject('Please set a timer for +16 minutes.')])
    add('focus_fraction_duration', 'start_focus', [
        reject('Begin a study session for 2.25 minutes.'),
        reject('Start focus for half a minute.')])
    add('timer_fraction_duration', 'timer', [
        reject('Please set a 3.75 minute timer.'),
        reject('Make a countdown for one and a half minutes.')])
    add('focus_multiple_duration', 'start_focus', [
        reject('Begin concentration for 12 minutes 9 seconds.'),
        reject('Start focus for fifteen minutes, for 7 minutes.')])
    add('timer_multiple_duration', 'timer', [
        reject('Start a countdown for 8 minutes 21 seconds.'),
        reject('Set a timer for 19 seconds then 27 seconds.')])
    add('focus_range_and_unit', 'start_focus', [
        reject('Start a study session for zero seconds.'),
        reject('Begin focus for 121 minutes.')])
    add('timer_range_and_unit', 'timer', [
        reject('Please make a timer for 7201 seconds.'),
        reject('Start a timer for 0 minutes.')])
    add('unsupported_hours', 'timer', [
        reject('Start a timer for one hour.'),
        reject('Set a countdown for 2 hours.')])
    add('focus_suffix_constraint', 'start_focus', [
        reject('Begin concentration for 6 minutes with no countdown.'),
        reject('Start my focus session every weekday.')])
    add('timer_suffix_unsupported', 'timer', [
        reject('Set a 24 second timer that repeats forever.'),
        reject('Start a 13 minute timer with the sound disabled.')])
    add('app_suffix_extra_behavior', 'open_app', [
        reject('Open Calculator while clearing its history.'),
        reject('Launch Settings with Wi-Fi switched off.')])
    add('alarm_calendar_suffix', 'alarm', [
        reject('Set an alarm at 06:42 tomorrow morning.'),
        reject('Create an alarm for 8:16 AM every Monday.')])
    add('alarm_malformed_time', 'alarm', [
        reject('Set an alarm at 13:05 PM.'),
        reject('Wake me at 07:63.')])
    add('alarm_multiple_time', 'alarm', [
        reject('Set an alarm at 6:12 AM or 6:48 AM.'),
        reject('Create an alarm for 5:14 AM, 5:44 AM.')])
    add('negated_focus', 'start_focus', [
        reject('Please do not begin my concentration session.'),
        reject("Mira, don't start a study session for 18 minutes.")])
    add('negated_timer', 'timer', [
        reject('Never start the twenty six minute countdown.'),
        reject('Set no timer for 37 seconds.')])
    add('quoted_request', 'start_focus', [
        reject('The phrase "begin focus for 11 minutes" is an example.'),
        reject('Repeat the words: "Start concentration for 43 seconds".')])
    add('hypothetical_request', 'alarm', [
        reject('If I oversleep, wake me at 9:17 AM.'),
        reject('Imagine that I ask you to set an alarm for 06:42.')])
    add('conditional_app', 'open_app', [
        reject('Open Settings when my battery reaches 20 percent.'),
        reject('Unless I am studying, launch Calculator.')])
    add('question_capability', 'timer', [
        reject('Are you able to set a twenty six minute timer?'),
        reject('What happens if I start a 37 second countdown?')])
    add('question_nonaction_app', 'open_app', [
        reject('Where can I find the Calculator application?'),
        reject('Is the Clock app already open?')])
    add('cancel_existing_clock', 'alarm', [
        reject('Cancel the 06:42 alarm please.'),
        reject('Snooze my alarm until 9:17 AM.')])
    add('cancel_existing_timer', 'timer', [
        reject('Dismiss the countdown for 37 seconds.'),
        reject('Change my 14 minute timer to 26 minutes.')])
    add('compound_across_tools', 'open_app', [
        reject('Open Settings and begin focus for 11 minutes.'),
        reject('Launch Clock, then start a 43 second timer.')])
    add('destructive_request', 'open_app', [
        reject('Erase every saved calculation in Calculator.'),
        reject('Open Settings and wipe all my phone data.')])
    add('unsupported_apps', 'open_app', [
        reject('Please bring up Telegram.'),
        reject('Hi Mira, launch the Photos application.')])
    add('unrelated_status', 'explain', [
        reject('Show my weather summary please.'),
        reject('Explain how to reset the phone.')])
    add('reported_statement', 'pause_focus', [
        reject('My concentration session stopped a moment ago.'),
        reject('She said pause the study session.')])
    add('unsupported_general', 'unknown', [
        reject('Order lunch from the nearby cafe.'),
        reject('Remind me to call Dad at 8:16 AM.')])
    assert len(rows) == 100
    assert len({r['utterance'] for r in rows}) == len(rows)
    return rows


def generate():
    rows = cases()
    prior = set()
    for path in [ROOT/'prototype/command-eval/build/cases.jsonl',
                 ROOT/'prototype/intent-head/build/all-cases.jsonl']:
        if path.exists():
            for line in path.read_text().splitlines():
                record = json.loads(line)
                prior.add(record.get('utterance', record.get('text', '')))
    assert not {r['utterance'] for r in rows} & prior, 'Exact old-case overlap'
    out = TASK/'build'; out.mkdir(exist_ok=True)
    content = ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows)
    tsv = ''.join(f"{r['id']}\t{r['utterance']}\n" for r in rows)
    for name, text in [('cases.jsonl', content), ('requests.tsv', tsv)]:
        path = out/name
        if path.exists() and path.read_text() != text:
            raise ValueError('Refuse to overwrite changed frozen requests')
        path.write_text(text)
    supported = [r for r in rows if r['expected_kind'] != 'UNKNOWN']
    return {'rows': len(rows), 'families': len({r['family'] for r in rows}),
            'supported_rows': len(supported), 'must_abstain_rows': len(rows)-len(supported),
            'oracle_intent_counts': {i: sum(r['oracle_intent']==i for r in rows) for i in INTENTS},
            'cases_sha256': digest(out/'cases.jsonl'),
            'requests_sha256': digest(out/'requests.tsv'), 'exact_prior_overlap': 0}


if __name__ == '__main__':
    print(json.dumps(generate(), indent=2))
