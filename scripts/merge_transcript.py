#!/usr/bin/env python3
"""Merge extracted Qwen chat turns into a complete transcript file."""
import json


def load_agent_output(path):
    """Load agent-browser eval output (JSON-wrapped string)."""
    with open(path) as f:
        raw = f.read()
    data = json.loads(raw)
    if isinstance(data, str):
        data = json.loads(data)
    return data


# Load all pieces
user_turns = load_agent_output('/home/z/my-project/user_turns.json')
asst_1 = load_agent_output('/home/z/my-project/asst_turns_1.json')
asst_2 = load_assistant = load_agent_output('/home/z/my-project/asst_turns_2.json')
asst_3 = load_agent_output('/home/z/my-project/asst_turns_3.json')

assistant_turns = asst_1 + asst_2 + asst_3

# Build ordered transcript
turns = {}
for t in user_turns:
    turns[t['i']] = {'i': t['i'], 'role': 'user', 'text': t['text']}
for t in assistant_turns:
    turns[t['i']] = {'i': t['i'], 'role': 'assistant', 'text': t['text']}

lines = []
lines.append('=' * 80)
lines.append('CHAT TRANSCRIPT: Prime Numbers and Universe')
lines.append('Date: October 04, 2026')
lines.append('Source: https://chat.qwen.ai/s/ac002fa1-606e-488d-99ac-6280f9109b41')
lines.append('Total turns: 24 user + 24 assistant = 48 messages')
lines.append('=' * 80)
lines.append('')

for i in sorted(turns.keys()):
    t = turns[i]
    lines.append('#' * 70)
    if t['role'] == 'user':
        lines.append(f'### [TURN {i}] USER:')
    else:
        lines.append(f'### [TURN {i}] ASSISTANT:')
    lines.append('#' * 70)
    lines.append(t['text'])
    lines.append('')

out = '\n'.join(lines)
with open('/home/z/my-project/download/qwen_chat_transcript_full.txt', 'w') as f:
    f.write(out)

print(f'Total lines: {len(lines)}')
print(f'Total chars: {len(out)}')
print(f'Total words: {len(out.split())}')
print(f'User turns: {len(user_turns)}, Assistant turns: {len(assistant_turns)}')
