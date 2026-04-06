import json, sys

cmds = json.loads(sys.argv[1])
with open('artifacts/interactive-session/commands.jsonl', 'a', encoding='utf-8') as f:
    for c in cmds:
        f.write(json.dumps(c, ensure_ascii=False) + '\n')
print(f"Sent {len(cmds)} commands")
