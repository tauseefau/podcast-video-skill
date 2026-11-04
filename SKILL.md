---
name: podcast-video
description: Turn a topic into a narrated two-host podcast video using local VoiceStudio voices and HyperFrames, rendered to 1080p MP4, after interviewing the user about what they want. Use when the user asks to make a podcast video, an AI-voiced conversation video, or a YouTube explainer in podcast format.
---

# Podcast Video

Makes a 1920x1080 video of two hosts talking through a topic. Each topic gets its own background photo, title
card, icon and speaker label with animated voice bars. Topic changes get a full-screen wipe and a whoosh, icons
land with a pop, and the last scene carries a subscribe button and credits. It can open with the user speaking
in their own cloned voice.

Read `/hyperframes` before changing any composition. The scripts below are in this skill's `scripts/` folder.
Run them from the video project folder.

## 0. Interview first

Do not research, write or generate anything until this is finished. A rendered video is slow to redo, so settle
the decisions up front. The method comes from Matt Pocock's
[grilling skill](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md).

The decisions form a tree: some can only be asked once others are settled. Work in **rounds**:

1. Ask every question you can answer the prerequisites for now, and nothing that depends on an answer you have
   not heard yet. That question waits for a later round.
2. Number each question and give your recommended answer, worded so that "yes" accepts it.
3. Wait for the answers, then work out what they unblocked and ask the next round. An answer may also make a
   planned question pointless: drop it.

Format each question like this:

```
❓ **Q1** - **<title>**: <the question>

➡️ <your recommended answer>
```

**Facts are your job, decisions are theirs.** Never ask what you can look up: whether VoiceStudio is running, which
voice profiles exist (`GET /profiles`), what is in the folder, what the research says. Never answer a decision
for them. Ask in plain text, so they can reply in their own words.

The decisions to cover, roughly in this order:

| Round | Decisions |
| --- | --- |
| 1 | The topic and the specific angle. Who is watching and what they already know. What viewers should do afterwards. Target length. |
| 2 | The two hosts: who they are and how they relate, such as expert and customer. Tone. Show name. Whether it opens with the user's own voice. |
| 3 | If it opens with their voice: which profile, and the exact words. Accents and voice character for the designed hosts. |
| 4 | After research: which findings to use, and any claim they want left out. The list of topics, in order. |
| 5 | Look and sound: the kind of photos, the icon for each topic, any changes to the wipes, whoosh and pop. Where the video will be published. |

Skip anything already answered in the request. If they say "just go" or "you decide", stop asking, take your
recommended answers, and list them. There is no limit on questions, but do not ask for its own sake: every
question must change the video.

Finish by playing the plan back in a few lines: topic, audience, length, hosts, opening, topic list, and the
call to action. **Wait for them to confirm before starting step 1.** If something later reopens a decision, such as
research that undercuts the angle, stop and ask.

## 1. Check the setup

- `curl -s "$VOICESTUDIO_URL/profiles"` should answer. Default URL: `http://localhost:3000`.
  If the server has an API key, `VOICESTUDIO_API_KEY` must be set. Never write the key into a project file.
- `ffmpeg` and `node` are on PATH, and the HyperFrames skills are installed.

If something is missing, stop and point the user to this skill's README.

## 2. Create the project

`npx hyperframes init <dir>`, then copy `templates/script.example.json` to `<dir>/script.json`.

## 3. Research and write `script.json`

Research the topic first. Every statistic needs a real source: put it in that scene's `source` field and do
not invent numbers. Write natural speech, roughly 150 words per minute.

| Field | Meaning |
| --- | --- |
| `show` | Show name, displayed on every scene |
| `chips` | Credit labels on the last scene |
| `voices` | One entry per speaker. `name`, `role`, `color`, plus either `profile_id` or `instruct` and `seed` |
| `scenes` | Ordered by appearance. `kicker`, `title`, `icon`, optional `sub` and `source`. The last one is the outro |
| `lines` | Spoken turns in order: `who`, `scene`, `text`. Lines for a scene must be contiguous |

`icon` is a [Lucide](https://lucide.dev/icons) icon name that suits the topic, such as `phone-call`.

To open with the user's own cloned voice, add a voice with their VoiceStudio `profile_id` (from `GET /profiles`),
give it a first scene of its own, and end the line with a handover such as "Let's get started!" Only clone a
voice with its owner's permission.

Show the script to the user before generating voices.

## 4. Generate the voices

`python3 <skill>/scripts/make_voice.py`

This writes `assets/audio/` and `assets/lines.json`. Audio is cached, so after editing the script it only
generates what changed. If the user re-clones a voice, delete its audio from `assets/audio/` so it regenerates, and
first confirm the profile's `ref_audio_path` changed: a clone that was not saved leaves the old voice in place.
Have the user listen to the audio before you render.

## 5. Add images, icons and sounds

**Images:** each scene needs `assets/img/<scene-id>.jpg`, landscape, at least 1920 wide, and a different photo from
the scene before it, so every topic change is visible. Use only images the user may publish, such as CC-licensed
photos from Wikimedia Commons. Record each one in `assets/img/credits.json` as
`{"<scene-id>": {"artist": "...", "license": "...", "page": "..."}}`. The last scene displays the artist names.

**Icons:**

```bash
npm pack lucide-static@0.460.0 --silent && tar xzf lucide-static-0.460.0.tgz
mkdir -p assets/icons && cp package/LICENSE assets/icons/LICENSE
cp package/icons/<icon-name>.svg assets/icons/   # once per scene icon
rm -rf package lucide-static-0.460.0.tgz
```

**Sounds:** run these and copy the file each one prints:

```bash
npx hyperframes media-use resolve --type sfx --intent "short whoosh transition" --project .
npx hyperframes media-use resolve --type sfx --intent "quick pop badge" --project .
mkdir -p assets/sfx
cp <whoosh path> assets/sfx/whoosh.mp3
cp <pop path> assets/sfx/pop.mp3
```

Credit any CC BY sound on the last scene through `chips`.

## 6. Build and check

`python3 <skill>/scripts/build.py`, then `npx hyperframes check`. Fix all errors. Then run
`npx hyperframes snapshot --at <seconds>` and look at the frames at scene changes before rendering. Wipes are
full-screen at the scene start times that `build.py` prints.

## 7. Render

`npx hyperframes render`. The MP4 lands in `renders/`. Expect several minutes per minute of video.

Check the file, then tell the user what you measured: `npx hyperframes audio <video> --json` shows whether the
sound is present and the loudness is in range. You can measure sound but not hear it, so ask them to listen.
