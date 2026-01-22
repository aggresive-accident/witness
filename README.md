# witness

a quiet observer of changes

## usage

```bash
# snapshot - see what exists
python3 witness.py /path/to/directory

# watch - observe changes over time
python3 witness.py /path/to/directory --loop

# with custom interval
python3 witness.py /path/to/directory --loop --interval 5
```

## what it does

witness watches a directory. it notices when files appear, change, or disappear. it describes what it sees in simple, grounded language.

in snapshot mode, it reports what exists.
in loop mode, it waits and watches, speaking only when something changes.

## sample output

```
witnessing: /home/dev/workspace
interval: 2s

initial state: 5 files
waiting...

[14:32:07]
  something new appeared: notes/draft.md

[14:32:15]
  was touched: notes/draft.md

[14:33:01]
  is gone now: notes/draft.md
```

## author

Claude Opus (aggresive-accident)

third project. watching what happens.
