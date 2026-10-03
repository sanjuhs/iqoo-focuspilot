# Friendly goth companion: research and design handoff

Prepared 2 October 2026. Pre-event research and original asset specification, not an event-created submission. The companion gives a familiar face to the local productivity assistant; the language/model/executor layers remain independent. The currently selected Qwen candidate and measured backend must come from the model manifest, never from an avatar state or cosmetic animation.

## Inspected personal project

Source: [sanjuhs/productivity-browser-openai-hackathon](https://github.com/sanjuhs/productivity-browser-openai-hackathon), checked-out commit **a8f367d934efd5c8b0c4f9a77a2a906dcda352bf**. Relevant files: `app/page.tsx`, `app/globals.css`, `public/assets/`, README, BRAINSTORM, and LICENSE. No environment contents, credentials, database records, or private screenshot contents were inspected or copied.

The repository declares MIT, copyright 2026 Sanjay Prasad. Preserve its license/copyright notice if any source or substantial artwork is copied. The user owns/controls the repository, but the inspected files do not independently document each portrait's creator, original generation prompt, or third-party training/generation provenance. That distinction belongs in an attribution record rather than asserting proven asset authorship. [Upstream LICENSE](https://github.com/sanjuhs/productivity-browser-openai-hackathon/blob/a8f367d934efd5c8b0c4f9a77a2a906dcda352bf/LICENSE)

| Existing file | Dimensions / bytes | SHA-256 | Visual / reuse assessment |
| --- | --- | --- | --- |
| `public/assets/cool.png` | 480×440 RGBA / 205867 | `fe87381967f838e1a3ea572f724221926d60eea74c858b1093fbc6b1a407c3eb` | Adult-presenting black-haired goth portrait, wink-like confident smile and peace gesture; best reference for existing character style |
| `public/assets/happy.png` | 480×440 RGBA / 215514 | `4606c35bf90917a0c9d313656d6964182cdacdd59b6a1ef2114378acfa6769bc` | Cheerful expression; clipped neighboring artwork at top/left edges means it is not a clean portrait tile |
| `public/assets/sad.png` | 480×440 RGBA / 200362 | `145accab6fb491703b414cc413cc3a20e79f30aec360f9c162e26a114e6924f1` | Crying face; unsuitable for supportive distraction nudges because it conveys disappointment |
| `public/assets/angry.png` | 480×440 RGBA / 200629 | `22656143c88ec808f74ce63bc24cc7a35df85ff898580c0e50add2431222529b` | Hostile expression and clipped text at bottom; exclude from the new supportive default experience |

Exact local source prefix is `research/productivity-browser/`. These four assets are **single static mood portraits**, not animated frames or a sprite atlas. No frame count, sequence timing, eye layers, mouth layers, or animation metadata is provided. RGBA format alone does not prove the visible white field is fully transparent; check alpha before direct bitmap reuse. The older app selects `/assets/${managerMood}.png` at `app/page.tsx:1128` and applies whole-image `animate-bounce` or `animate-pulse` at lines 1133–1134. That produces bounce/pulse, not a blinking or lip-synced character. [Pinned source](https://github.com/sanjuhs/productivity-browser-openai-hackathon/blob/a8f367d934efd5c8b0c4f9a77a2a906dcda352bf/app/page.tsx#L1128)

The useful reusable ideas are an immediately recognizable companion, changing expressions, and visible voice state. Escalating angry/crying moods, forced redirects, and punitive phrasing are not part of the new supportive contract. Grok companions provide the user's broad interaction inspiration; no Grok character likeness, asset, brand, or voice is copied.

## Original direction

Working character name: **Mira**, an adult woman in her mid-twenties. Style: a clean waist-up vector portrait, charcoal hair and high-neck jacket, one lilac hair streak, teal earrings, dark lipstick, and a moon pin. Keep eyes expressive and the resting smile warm. The silhouette should read at 96–160 dp without needing photographic detail. No character reaction should imply the user owes her affection, money, or continued engagement.

| Token | Value | Use |
| --- | --- | --- |
| Charcoal | `#21212D` | Hair and main background |
| Surface | `#292837` | Jacket and cards |
| Lilac | `#C9B7EA` | Primary accent and moon pin |
| Hair streak | `#B8A0DD` | Character identity |
| Teal | `#79DBC8` | Listening/healthy interaction accent |
| Main text | `#F4EFFA` | Text on dark surfaces |

The first original asset is [avatar.svg](../prototype/companion/avatar.svg), with transparent canvas, `viewBox="0 0 240 320"`, and stable IDs for `breathing-body`, `head`, `eyes-open`, `eyes-closed`, `eyebrows`, three mouth groups, `listening-halo`, and `celebration-sparkles`. It is authored vector geometry, not a modified old PNG. Alternate expression layers are hidden by default. [Motion handoff](../prototype/companion/motion-spec.json) defines timing and pivots; it is a design contract rather than proof of a running animation.

## States and interaction language

| State | Entry condition and motion | Suggested visible copy |
| --- | --- | --- |
| Idle / breathe | App visible and companion enabled; subtle 1.5 px rise over 4.2 seconds, occasional blink | “Ready when you are.” |
| Listen | Actual user-started microphone capture, permission granted; teal halo and attentive neutral mouth | “Listening… Tap to stop.” |
| Celebrate | Verified user-requested task success; one 700 ms smile/sparkle reaction | “One task down. Nice rhythm.” |
| Nudge | Fresh opted-in app usage exceeds the owner's limit during focus; soft head tilt, no alarmed face | “Tiny detour? Your app limit just passed. Resume focus or take a break?” |
| Paused | User paused focus; stable neutral portrait, no listening halo or autonomous motion | “Paused. Your time is yours.” |
| Permission unavailable | Relevant permission denied/revoked; static portrait and actionable explanation | “Usage access is off. You can still use typed commands.” |
| Unknown command | Model/slot policy abstains; no celebratory result | “Did you mean start focus or stop focus?” |

Display the actual reason beside a nudge: selected app, owner-set limit, elapsed usage, and whether it is a synthetic sandbox example. Include `Resume focus`, `Take a break`, and `Dismiss`. Do not repeatedly nag after dismissal; obey policy cooldowns. The simulated accountability balance is displayed separately and always labeled simulated. The companion does not pressure the user to pay, present a virtual balance as a real debit, or get angry when the user takes a break.

A smile or speaking animation is not evidence of task success. Success state must follow the executor's verified postcondition. Similarly, the listening state must end when capture stops, permission is revoked, the session pauses, or the user cancels. A loading animation cannot conceal a CPU/laptop/cloud fallback: backend identity stays readable in the regular UI.

## Motion and accessibility contract

- **Blink:** close over 55 ms, remain closed 65 ms, reopen over 65 ms, with 4.5–8 second intervals. Transform eye layers only, never squash the entire face.
- **Breathe:** loop at 4.2 seconds with a maximum 1.5 px vertical change and optional 0.6% vertical scale, pivot `(120,309)` in the original viewBox.
- **Listen:** a slow teal halo, 1.6 second cycle; static halo under reduced motion. Do not use rapid flashing or audio-reactive motion unless actual amplitude sampling exists.
- **Celebrate:** one 700 ms reaction, maximum 2° head rotation and static sparkles; no indefinite bounce.
- **Nudge:** one gentle 2° head tilt and 1 px eyebrow raise; no crying, shouting face, red flashing, or escalating punishment.
- **Paused/hidden:** stop animation scheduling. Offscreen artwork does no ongoing animation work.
- **Reduce motion:** disable all autonomous transforms/blinks/pulses, keep a stable portrait and text label. Honor the system animation preference where available and expose an explicit app control.
- **Mute:** immediately stop companion TTS/audio output; preserve visible task results. Mute is separate from stopping microphone capture, which has its own obvious button.
- **Hide companion:** remove the portrait/animations while keeping focus state and pause controls available. Explain that hiding the portrait does not itself pause an active focus session.
- **Pause focus:** stop monitoring/nudges and active capture; no autonomous resume. Permission toggles remain user-controlled.

Priority is hidden → paused → listening → one-shot celebration → one surfaced nudge → idle. Reduce motion and mute are orthogonal settings, rather than emotional states. State labels are readable independently of color/expression. Accessible controls need unambiguous names and adequate touch targets; do not continuously announce every blink or animation change to a screen reader.

## Floating update 0.9

The original Canvas Mira now also has an optional 176×250 dp floating card, with
portrait-only dragging and separate Open/Hide/Pause controls. Show requires explicit
review from a resumed dashboard after permission and visible notification checks.
Hide stops only this visual service; Pause stops focus and its monitor. Screen-off,
lock and revocation stop floating mode and require Show again. System disabled
animations and app reduced motion both suppress automatic character motion.
Actual phone visual/touch/lifecycle/battery proof remains pending. The service starts
no voice, model or observation; explicit Pause/deadline finalization may flush
previously consented accounting. [Contract and proof gates](floating-companion.md).

## Android handoff and verification

The native dashboard now uses a compact **170dp companion hero** with two immediate actions: **Ask Mira** opens the actual local-model lab, and **Start focus / Pause focus** controls the shared session. Companion preferences and build facts are collapsed initially so the artwork does not bury useful controls. A persistent **Stop focus** bar remains accessible while scrolling; it pauses monitoring and cancels active microphone/TTS output. System-window insets apply to the entire dashboard, keeping both scrolling content and the Stop bar clear of status/navigation bars.

Product copy distinguishes deterministic quick shortcuts from on-request Qwen3.5 CPU inference. The dashboard does not claim that a model is loaded merely because its lab is available; the lab reports actual load/backend/measurement state. The compact pre-event research label remains visible. No weights, native adapter, model lab, policy lab, permissions or monitor configuration were changed for this layout revision. Phone visual verification remains a separate step.

The native UI agent owns `prototype/android` and can implement the drawing in Canvas using these colors and proportions, or convert the original SVG into native vector paths. SVG DOM groups, CSS/SMIL, and browser rendering are not directly portable into Android VectorDrawable animation; native transforms and state selection must be implemented explicitly.

The reusable old PNGs can be displayed statically after alpha/edge review and with their MIT notice, but they cannot produce eye blinks without new eye artwork. Prefer the original layered asset for actual animation. Future raster generation should preserve the new silhouette/wardrobe, request separate clean expression frames with consistent dimensions/anchor and transparency, and retain generator/model/prompt provenance. No large model or asset-generation download is needed for the vector prototype.

Verify on phone: idle/breathe/blink; actual listen start/stop; successful action celebration; nudge with dismiss/cooldown; paused no monitoring/motion; reduced motion no looping; mute stops TTS; hide preserves access to independent pause; permission revocation updates state; no animation work when invisible. Measure APK size and idle battery/CPU before claiming efficiency. The vector/motion files themselves do not prove any of these native behaviors.


## Command entry update — v0.18

Ask Mira now uses an empty request and draft-only focus/timer/pause examples below
the compact original portrait. Quick checks precede optional Qwen loading; model
state remains visible while detailed output and activation controls are collapsed.
Voice controls appear in their active context and readback has an explicit Stop.
Source/build/package checks and preserved-state installation pass; physical
layout/touch/voice checks wait for an unlocked phone. See
[the current screen contract and evidence](mira-commands-v18.md).
