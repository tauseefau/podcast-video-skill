# Podcast Video Skill

A [Claude Code](https://claude.com/claude-code) skill that turns a topic into a narrated two-host podcast video.
Claude researches the topic and writes the script, [VoiceStudio](https://github.com/debpalash/VoiceStudio)
generates the voices locally, and [HyperFrames](https://github.com/heygen-com/hyperframes) renders a 1080p MP4.

Each scene gets a background photo, a title card, a speaker label with animated voice bars, and the last scene
gets a subscribe button and credits. You can also open the video in your own cloned voice.

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

Review the script and the voices when Claude asks, then it renders the video to `renders/`.

To run the steps yourself, see [SKILL.md](SKILL.md). The script format is in
[templates/script.example.json](templates/script.example.json).

## Your own voice

Clone your voice in VoiceStudio, get its ID from `GET /profiles`, and add it as a speaker in `script.json`:

```json
"voices": { "me": { "name": "Your Name", "role": "Your host", "color": "#f6c945", "profile_id": "your-profile-id" } }
```

## Be responsible

Only clone a voice with its owner's permission. Only publish images you have the rights to, check every
statistic against its source, and tell your viewers the voices are AI-generated.

## License

MIT. VoiceStudio and HyperFrames are separate projects with their own licenses.
