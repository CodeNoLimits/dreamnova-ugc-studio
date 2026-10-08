#!/usr/bin/env bash
# DreamNova UGC Studio — installer for Claude Code on macOS. Idempotent: safe to re-run (also = update).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
say() { printf '\033[0;32m▸ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m⚠ %s\033[0m\n' "$*"; }

# 1. the skill itself (Claude Code + other agents that read ~/.agents/skills)
for root in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  [ "$root" = "$HOME/.claude/skills" ] || [ -d "$root" ] || continue
  mkdir -p "$root/ugc-studio"
  rsync -a --delete --exclude '.DS_Store' --exclude '__pycache__' "$HERE/skills/ugc-studio/" "$root/ugc-studio/"
  say "skill installed → $root/ugc-studio"
done

# 2. render tools: ffmpeg with libass (Hebrew captions) + node (HyperFrames, /brag)
if command -v brew >/dev/null 2>&1; then
  [ -x /opt/homebrew/opt/ffmpeg-full/bin/ffmpeg ] || [ -x /usr/local/opt/ffmpeg-full/bin/ffmpeg ] || { say "installing ffmpeg-full…"; brew install ffmpeg-full; }
  command -v node >/dev/null 2>&1 || { say "installing node…"; brew install node; }
else
  warn "Homebrew missing. In Terminal (asks for the Mac password):"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  warn "then re-run: bash $HERE/install.sh"
fi

# 3. /brag + HyperFrames skills
if command -v npx >/dev/null 2>&1; then
  npx --yes skills add https://github.com/latent-spaces/brag --skill brag -g -y -a claude-code || warn "brag install failed — see references/setup.md §6"
  npx --yes skills add heygen-com/hyperframes -g -y -a claude-code || warn "hyperframes skills install failed"
fi

# 4. proof
python3 "$HOME/.claude/skills/ugc-studio/scripts/ugc.py" selftest || warn "selftest failed — fix before making Hebrew videos"
if python3 "$HOME/.claude/skills/ugc-studio/scripts/ugc.py" voices >/dev/null 2>&1; then say "ElevenLabs key OK"
else warn 'No ElevenLabs key yet → references/setup.md §1-§2 (security add-generic-password -U -a "$USER" -s ELEVENLABS_API_KEY -w)'; fi
say "Done. Restart Claude Code, then just ask: “make me a UGC video”."
