# Podcast Video Skill

A [Claude Code](https://claude.com/claude-code) skill that turns a topic into a narrated two-host podcast video.
Claude researches the topic and writes the script, [VoiceStudio](https://github.com/debpalash/VoiceStudio)
generates the voices locally, and [HyperFrames](https://github.com/heygen-com/hyperframes) renders a 1080p MP4.

Before doing any work, it interviews you about what you want, so you don't wait for a render to find out it
guessed wrong.

Each topic gets its own background photo, title card, icon and speaker label with animated voice bars. Topic changes
get a full-screen wipe and a whoosh, icons land with a pop, and the last scene has a subscribe button and credits.
You can also open the video in your own cloned voice.

## How the interview works

Claude asks questions in rounds, each with a recommended answer, so you can reply "yes" or "1 yes, 2 make it 90
seconds". It only asks what it can't look up itself, and it starts working once you confirm the plan. Say "just go"
at any time to accept its recommendations.

The method is adapted from Matt Pocock's
[grilling skill](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md) (MIT).

## What you need

- Claude Code
- Node.js and ffmpeg
- Python 3 (no extra packages)
- Docker and an NVIDIA GPU to run VoiceStudio
- [VoiceStudio](https://github.com/debpalash/VoiceStudio), running locally
- The HyperFrames skills:

  ```bash
  claude plugin marketplace add heygen-com/hyperframes
  claude plugin install hyperframes@hyperframes
  ```

## Install

```bash
git clone https://github.com/tauseefau/podcast-video-skill ~/.claude/skills/podcast-video
```

Tell the scripts where VoiceStudio is. Skip the key if your server does not use one.

```bash
export VOICESTUDIO_URL=http://localhost:3000
export VOICESTUDIO_API_KEY=your-key
```

## Use

Start Claude Code in an empty folder and ask:

```
/podcast-video make a 2 minute podcast about how to sell a website to a flower shop owner
```

Answer its questions, review the script and the voices, and it renders the video to `renders/`.

To run the steps yourself, see [SKILL.md](SKILL.md). The script format is in
[templates/script.example.json](templates/script.example.json).

## Your own voice

Clone your voice in VoiceStudio, get its ID from `GET /profiles`, and add it as a speaker in `script.json`:

```json
"voices": { "me": { "name": "Your Name", "role": "Your host", "color": "#f6c945", "profile_id": "your-profile-id" } }
```

Claude asks about this during the interview. If you re-clone your voice, save it in VoiceStudio before generating.

## Be responsible

Only clone a voice with its owner's permission. Only publish images you have the rights to, check every
statistic against its source, and tell your viewers the voices are AI-generated.

## License

MIT. VoiceStudio, HyperFrames and Lucide are separate projects with their own licenses. Icons and sound effects are
downloaded when you make a video and are not part of this repo.
