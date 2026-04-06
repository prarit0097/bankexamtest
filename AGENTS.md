# AGENTS.md

This file applies to the entire workspace under `e:\coding\bank exam test`.

## Project Rule
Har change, feature, fix, refactor, doc update, config update, ya command-based modification se pehle is file ko read karo.
Is rule ko global aur mandatory samjha jaye. Future me kisi bhi code ya doc change se pehle sabse pehle `AGENTS.md` read karna hai, phir kaam start karna hai.

## Mandatory Instructions
1. Every change ke baad code ko `https://github.com/prarit0097/bankexamtest` ke saath sync rakhne ke liye prepare karo. Agar local folder git repo ya remote configured na ho, to final report me clear batao ki push/sync nahi ho saka.
2. Every change ke baad jo bhi project me changes, addons, fixes, commands, risks, ya new behavior aaye hain, unhe `TEST.md` me update karna mandatory hai.
3. Agar user ne specifically `AGENT.MD` bola ho, tab bhi effective instruction source isi workspace ka `AGENTS.md` file maana jayega.

## Working Expectations
- Project ka purpose banking exam prep platform hai; unrelated changes avoid karo.
- Existing behavior break karne wale changes se pehle relevant tests update ya add karo.
- Secrets ko docs me expose mat karo.
- `.env.example` me placeholders hone chahiye, real API keys ya real bot tokens nahi.
- `TEST.md` ko project handbook + change log dono ki tarah maintain karo.
- Final response me changed files, verification, aur remaining risks mention karo.

## Verification Expectations
- Small changes: at least targeted verification
- App logic changes: run relevant Django checks/tests
- Config changes: validate syntax or affected command

## Current Default Commands
- `python manage.py check`
- `python manage.py test prep`
- `python manage.py migrate`
- `python manage.py seed_exam_taxonomy`
- `python manage.py generate_prediction_sets`
