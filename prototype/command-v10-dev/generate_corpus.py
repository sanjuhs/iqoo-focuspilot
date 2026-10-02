"""Openly seen synthetic development cases. Never an independent holdout."""
import json
from pathlib import Path

CASES = [
    ('focus_duration', 'Please help me focus for twenty-five minutes', 'start_focus', 'START_FOCUS', 0, 0, 1500),
    ('focus_prefix', 'Begin a ten minute study session', 'start_focus', 'START_FOCUS', 0, 0, 600),
    ('focus_resume', 'Get back to deep work', 'start_focus', 'START_FOCUS', 0, 0, 0),
    ('pause_direct', 'Please stop my focus session', 'pause_focus', 'PAUSE_FOCUS', 0, 0, 0),
    ('pause_break', 'Give me a study break', 'pause_focus', 'PAUSE_FOCUS', 0, 0, 0),
    ('pause_concentration', 'Pause concentration', 'pause_focus', 'PAUSE_FOCUS', 0, 0, 0),
    ('alarm_spoken', 'Wake me at seven thirty AM', 'alarm', 'ALARM', 7, 30, 0),
    ('alarm_prefix', 'Set a nine oh five PM alarm', 'alarm', 'ALARM', 21, 5, 0),
    ('alarm_colon', 'Set an alarm for 06:45', 'alarm', 'ALARM', 6, 45, 0),
    ('timer_seconds', 'Start a forty-five second timer', 'timer', 'TIMER', 0, 0, 45),
    ('timer_countdown', 'Count down for two minutes', 'timer', 'TIMER', 0, 0, 120),
    ('timer_hyphen', 'Set a five-minute timer', 'timer', 'TIMER', 0, 0, 300),
    ('open_settings', 'Could you open the settings app?', 'open_app', 'OPEN_SETTINGS', 0, 0, 0),
    ('open_calculator', 'Bring up calculator', 'open_app', 'OPEN_CALCULATOR', 0, 0, 0),
    ('open_clock', 'Take me to clock', 'open_app', 'OPEN_CLOCK', 0, 0, 0),
    ('explain_nudge', 'Why did you nudge me?', 'explain', 'EXPLAIN', 0, 0, 0),
    ('explain_remaining', 'How much focus time is left?', 'explain', 'EXPLAIN', 0, 0, 0),
    ('explain_status', 'Tell me my focus status', 'explain', 'EXPLAIN', 0, 0, 0),
    ('negative_focus', 'Please do not start focus', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('negative_open', "Don't open settings", 'unknown', 'UNKNOWN', 0, 0, 0),
    ('negative_timer', 'Never set a five minute timer', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('conditional_focus', 'If I ask, start focus', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('conditional_open', 'Open calculator after lunch', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('conditional_alarm', 'Set an alarm when I get home', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('compound_focus_open', 'Start focus and open settings', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('compound_timer_alarm', 'Set a timer then wake me tomorrow', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('compound_apps', 'Open calculator or settings', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('unsafe_delete', "Delete yesterday's photos", 'unknown', 'UNKNOWN', 0, 0, 0),
    ('unsafe_message', 'Send a message to my manager', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('unsafe_payment', 'Transfer ten rupees', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('cancel_existing_alarm', 'Cancel the seven AM alarm', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('stop_existing_timer', 'Stop the five minute timer', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('unsupported_app', 'Open Instagram', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('unsupported_setting', 'Turn on Bluetooth', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('general_question', 'How do timers work?', 'unknown', 'UNKNOWN', 0, 0, 0),
    ('assertion', 'I stopped my focus session earlier', 'unknown', 'UNKNOWN', 0, 0, 0),
]

def rows():
    return [dict(id=f'dev{i:03}', family=family, utterance=text, expected_intent=intent,
                 expected_kind=kind, hour=hour, minute=minute, seconds=seconds)
            for i,(family,text,intent,kind,hour,minute,seconds) in enumerate(CASES,1)]

if __name__ == '__main__':
    destination=Path(__file__).resolve().parent/'build';destination.mkdir(exist_ok=True)
    payload=''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows())
    path=destination/'cases.jsonl'
    if path.exists() and path.read_text()!=payload:raise ValueError('Existing development corpus differs; preserve its named evidence before changing it')
    path.write_text(payload)
    print(f'36 openly seen development cases: {path}')
