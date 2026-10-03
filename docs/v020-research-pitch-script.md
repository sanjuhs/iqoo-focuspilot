# Mira v0.20 — research pitch

Current app source: `81287b2b08ccedc050635b0b8a27154bed3b5d87`. Selected model:
Qwen3.5-0.8B Q4_0. Narration is separate from silent historical phone footage.
The eight scenes below distinguish recorded behavior, current source and next steps.

## Scene 1: A gentle return to your task

> Most lost time begins with a detour. You unlock your phone for one thing, follow another, and forget what you wanted to do.
> Mira is our local productivity companion: a friendly goth character who offers a gentle return to your task, with your choices at the center.
> The idea is practical companionship. A task guide, focus session and bounded phone assistant belong together, without shaming you or withdrawing real money for distractions.

Visual: Original procedural Mira beside an illustrated drifting task card; lilac, charcoal and teal. Label this product illustration, not a live overlay recording.

## Scene 2: Your own next step

> This is historical version twelve footage from our Nothing phone. The guide contains user authored steps, rather than pretending that a model completed your work.
> You choose the next step and whether to speak it. The clip shows a completed text to speech status, which alone does not prove audible playback.
> Keeping the guide editable matters. You can change the plan, mark progress or undo a mistake. The assistant supports your intentions; you remain the author.

Visual: Historical v12 authored-guide clip, 10.369829 seconds, shown once at 1×. Label its version and silent phone audio; hold its final frame visibly after playback. Do not portray Mark/Undo as filmed.

## Scene 3: A local proposal, not an execution

> In this second historical clip, an already typed Stop focus request becomes a local Qwen Pause proposal. It says Review Required; no action was confirmed.
> Current research retains Qwen three point five, zero point eight billion parameters, with Q four zero quantization. Familiar commands can also use a fast local route.
> A separate version nineteen CPU check completed six already seen requests; model loading took two point three six one seconds. That is narrow runtime evidence.

Visual: Historical v12 typed Stop-focus clip, 9.339 seconds, once at 1×, then labelled final-frame hold. Keep “Historical v12 · no confirmed action” visible; attribute v19 statistics separately.

## Scene 4: Ask, check, review, choose

> The current command flow begins with an editable draft. Familiar requests can be checked locally without loading Qwen; unfamiliar wording can use an explicit model fallback.
> Both routes produce bounded proposals. The code checks the original request, arguments and allowed tools before offering a review. Unsupported or conflicting requests should be refused.
> Review and Confirm are separate choices. Editing, cancelling or leaving the screen invalidates the pending review. A generated sentence never becomes permission to act by itself.

Visual: Illustrated draft → fast local or explicit Qwen → validation → Review → Confirm diagram. A cancel branch ends before execution; label the diagram as source behavior.

## Scene 5: Nearby when you choose

> Version twenty adds a default off choice: keep Mira nearby after unlock. Turning it on starts nothing; the next reviewed Show chooses that session’s behavior.
> When locked, the portrait hides and its refresh stops. The same existing service can restore it after unlock, once actual permission and phone state checks pass.
> Hide ends that availability. Voice and model use remain explicit, while separately chosen focus or monitoring work stays independent. Physical restoration and reliable OEM persistence remain unverified.

Visual: Current v20 availability illustration: reviewed Show → portrait → locked idle notification → guarded unlock return, with Hide ending the session. Label “Physical lock/unlock test pending”; show no invented phone footage.

## Scene 6: Inspection with honest limits

> We want decisions that people can inspect. Phone activation summaries show finite internal measurements, but a colorful vector does not establish what a model understands.
> A separate tiny trained shadow policy exposes exact hidden contributions and feature ablations. Its training is synthetic, and its score does not control the phone.
> These are useful research tools, not a causal interpretation result or proof of real productivity learning. The product must keep those distinctions visible before making stronger claims.

Visual: Separate labelled panels for observed Qwen activation summaries and the synthetic 65-parameter shadow policy; no semantic labels on tensor channels. Any toy contribution illustration must identify its synthetic inputs and provenance.

## Scene 7: A reviewable research build

> The version builds with two hundred sixteen passing JVM tests. Its signed light update is installed on Nothing, preserving protected state and existing permission choices.
> Source, release packages and public evidence are backed up on GitHub. Packaging checks bind the model bundle to the same app payload; current bundled import remains unverified.
> Private captures, credentials and training data stay outside Git. Build checks are valuable, but they do not replace watching the interface, hearing speech or testing real consented workflows.

Visual: Current v20 source, build, protected installation and verified publication cards; distinguish light installation from bundle packaging. Use public evidence labels, not private phone snapshots.

## Scene 8: From preparation to the real demo

> The next milestone is the complete live experience: permitted voice, persistent companion behavior and productive tasks on actual iQOO hardware, with clear user control throughout.
> Snapdragon NPU execution and Office Kit integration still need direct evidence. Broad computer use, general phone automation and connected device workflows remain future work, not demonstrated capabilities.
> This repository is pre event preparation. Eligible competition code must follow the event rules, and admission and accepted submission remain pending. Mira’s promise is help you can inspect and choose.

Visual: A clearly labelled roadmap to live workflow proof, iQOO/NPU, Office Kit and separately eligible event code. End on original Mira with “Research prototype · next proof pending.”

Sources: [Historical v12 recording and clip boundaries](v012-pitch.md),
[v19 actual CPU regression and limits](native-page-v19.md),
[current v20 availability, build and installation](mira-availability-v20.md),
[v20 publication](mira-availability-publication-v20.json),
[compatible command research](compatible-command-research.md),
[remaining deliverables](remaining-deliverables.md),
[hackathon eligibility](../hackathon.md).
