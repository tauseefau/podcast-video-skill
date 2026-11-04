---
name: podcast-video
description: Turn a topic into a narrated two-host podcast video using local VoiceStudio voices and HyperFrames, rendered to 1080p MP4. Use when the user asks to make a podcast video, an AI-voiced conversation video, or a YouTube explainer in podcast format.
---

# Podcast Video

Makes a 1920x1080 video of two hosts talking through a topic: one scene per talking point, with a speaker
label, animated voice bars, a background photo, and a closing subscribe scene.

Read `/hyperframes` before changing any composition. The scripts below are in this skill's `scripts/` folder.
Run them from the video project folder.

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
| `scenes` | Ordered by appearance. `kicker`, `title`, optional `sub` and `source`. The last one is the outro |
| `lines` | Spoken turns in order: `who`, `scene`, `text`. Lines for a scene must be contiguous |

To open with the user's own cloned voice, add a voice with their VoiceStudio `profile_id` (from `GET /profiles`)
and give it the first scene. Only clone a voice with its owner's permission.

## 4. Generate the voices

`python3 <skill>/scripts/make_voice.py`

This writes `assets/audio/` and `assets/lines.json`. Audio is cached, so after editing the script it only
generates what changed. Have the user listen to the audio before you render.

## 5. Add the images

Each scene needs `assets/img/<scene-id>.jpg`, landscape, at least 1920 wide. Use only images the user may
publish, such as CC-licensed photos from Wikimedia Commons. Record each one in `assets/img/credits.json` as
`{"<scene-id>": {"artist": "...", "license": "...", "page": "..."}}`. The last scene displays the artist names.

## 6. Build and check

`python3 <skill>/scripts/build.py`, then `npx hyperframes check`. Fix all errors. Then run
`npx hyperframes snapshot --at <seconds>` and look at the frames at scene changes before rendering.

## 7. Render

`npx hyperframes render`. The MP4 lands in `renders/`. Expect several minutes per minute of video.
