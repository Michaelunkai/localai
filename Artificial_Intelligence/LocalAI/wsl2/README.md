# Nature LocalAI for Windows and WSL2

`a.sh` installs and launches a local llama.cpp agent with Windows tools, durable task state, file operations, and optional web and browser integrations. Model inference runs locally; installation downloads, web research, and configured external integrations use the network.

## Start or update

On the configured Windows machine:

```powershell
llm
llm -SelfTest
```

For another Ubuntu WSL installation, clone this repository and run:

```bash
git clone https://github.com/Michaelunkai/localai.git
cd localai/Artificial_Intelligence/LocalAI/wsl2
bash a.sh
```

The canonical installer is **`a.sh`**. The older `local-ai-setup.sh` is not the current launcher.

| Invocation | Behavior |
|---|---|
| `bash a.sh` or `bash a.sh --launch` | Verify installed components, repair when necessary, then open interactive mode |
| `bash a.sh --check` | Read-only readiness check; does not install or launch a model |
| `bash a.sh --install` | Explicit full installation/acceptance path |
| `llama` or `chat` | Launch the installed runtime directly |
| `llama "request"` | Run a single request |
| `models` | List downloaded models |

Normal launches do not repeat package installation or download a new model. Runtime-only script changes are refreshed atomically with backups when the verified installation recipe has not changed. A dependency-stage checkpoint lets a failed later acceptance test resume without repeating completed package work. Missing dependencies or damaged runtime/model files still trigger repair.

After updating, exit an existing interactive session with `/exit` and run `llm` again. Existing Python processes do not hot-reload edited source. Cold model loading takes time; a compatible healthy server can be reused. Servers belonging to other applications are preserved when a port is occupied.

## Fast, evidence-based Windows path lookups

Named read-only questions use the requested Windows evidence source before model inference:

| Request | Evidence |
|---|---|
| `output full path to exe of latest 'daymark' app version that is pinned in my taskbar` | Taskbar shortcut target and existing target file |
| `path to Daymark desktop shortcut` | User and shared desktop shortcuts |
| `full path to Calculator in the Start Menu` | User and shared Start Menu shortcuts |
| `where is installed Firefox exe` | Start Menu shortcuts and App Paths registrations |
| `output full path to exe running whisper tts every windows boot` | Startup records, enabled boot/logon tasks, automatic services |
| `where is the running Obsidian executable` | Live process executable identity |

These are generic application lookups, not hard-coded Daymark or Whisper paths. They run PowerShell with encoded arguments and a 20-second subprocess limit. Taskbar and desktop lookups do not recurse; Start Menu lookup only recurses inside its two known folders. They never scan entire drives or invoke the model. Unsupported shortcut targets, denied access, missing files, and multiple matches produce an explicit incomplete result rather than an invented path. `/resume` can continue investigation; broad drive scans remain rejected for shortcut/startup identity questions.

A taskbar target proves what that shortcut launches. It does **not** prove it is the newest version installed anywhere or the latest upstream release. The runtime retains file-version evidence and preserves that distinction. Packaged-app shortcuts without a direct executable target are reported as unresolved. Installed-app lookup is limited to the named registrations; portable apps without registrations may require a user-specified directory.

The parser no longer converts natural language such as `path to exe` into `to.exe`. Explicit filenames such as `to.exe` and `freebuff exe` remain supported for actual filename searches. Requests to install, modify, delete, or update an application retain the task workflow instead of being reduced to a read-only answer.

### Measured regression results

On the development Windows/WSL machine on 2026-09-06, the exact Daymark taskbar lookup returned the same verified target in **2.914, 0.312, and 0.373 seconds**, versus the reported failed workflow still running after 454 seconds. The real `llm` interactive `/resume` also completed the previously stuck Daymark request in **0.38 seconds**, clearing its pending state; a fresh interactive submission took **0.36 seconds**. These are measurements of the lookup, not universal latency guarantees. The earlier Whisper startup regression completed through the actual interactive command in 0.75 seconds.

## Live speed display

During model inference, the live row shows **PP** (prompt-processing speed in **T/m**, tokens per minute), **TG** (generation speed in **T/m**), **TTFT** (client-observed time to the first semantic output, including reasoning/tool output, in milliseconds), and request elapsed milliseconds. Generation uses `(predicted_n - 1) * 60000 / predicted_ms`, matching the server decoding interval after the first token. Rates are cumulative server-reported averages for the current request, not instantaneous samples or characters converted into tokens. Cached prompt tokens are excluded from the timed prompt calculation. The first generation sample shows `warming up` rather than an inflated one-token rate; missing server measurements show `n/a`.

Timing updates come from the response stream using llama.cpp `timings_per_token` and `return_progress`. The interactive display requests a 1 ms cadence (configurable from 1 to 250 ms with `LLAMA_LIVE_REFRESH_SECONDS`) and keeps elapsed milliseconds visible. This is best effort: Windows scheduling, terminal rendering, and I/O can delay a redraw. Expensive telemetry probes are sampled at most every 50 ms; display ticks reuse the latest real measurement and never invent tokens or file counts. An independent timer prints a factual English `[PROGRESS]` line once per second during interactive work, even when the speed row redraws continuously. Noninteractive logs remain throttled. During scans the primary metric is measured files/second, followed by checkpoint age and counts; token speed is `n/a (tool work)`. During inference the display shows measured PP/TG in T/m. A final inference summary remains visible.

Drive-only follow-ups such as `now same from C drive` preserve the count and file-ranking intent of the immediately preceding scan. For example, `top 10 largest files on F drive` followed by `same on C drive` runs one `win-tools files C 10` call without a model round. This carries forward through subsequent drive-only follow-ups; an unrelated user request ends that inheritance.

## Agent behavior and controls

- Ordinary stable-knowledge questions have a bounded direct-answer path. Live or local evidence requests retain tools.
- Complex tasks use model-selected tools, durable checkpoints, completion checks, and recovery. Model mistakes and hardware limits remain possible; no claim of universal correctness or fixed completion time is made.
- Progress reports observed state and elapsed time, without fabricated percentage or ETA.
- The interactive `[ACTIVE]` label refreshes when work finishes.
- GPU configuration checks available memory. The Qwen hybrid-model fallback uses system RAM when its GPU allocation cannot fit safely; this can make model-based work substantially slower. Deterministic lookups do not incur inference latency.

| Command | Purpose |
|---|---|
| `/help` | Current complete command list |
| `/status`, `/events`, `/details` | Task state, progress, and retained diagnostics |
| `/pause`, `/resume`, `/cancel` | Control an unfinished task |
| `/sources` | Retained research evidence |
| `/history`, `/memory` | Conversation and persistent memory |
| `/exit` or `/quit` | Exit the interactive session |

Up/Down recalls prompts across sessions; Ctrl+R searches history. During work, additional input can steer the active task.

## Windows tools and integrations

`win-tools` exposes disk/folder/file inspection, processes, startup inventory, scheduled tasks, services, clipboard, notifications, screenshots/OCR, network, GPU, and battery queries. Examples:

```bash
win-tools disk C
win-tools dir F:
win-tools search C example.exe FIRST
win-tools processes
win-tools boot
win-tools scheduled
```

Drive scans are available for requests that actually need a filesystem search. They can be expensive; use a known drive or directory whenever possible.

`browse` can open URLs in the configured Chrome profile. Installed browser packages alone do not prove live tab-control availability: follow the runtime's capability report and configured browser boundary. Web research and MCP integrations depend on their configured providers, credentials, connectivity, and tool availability.

## Installation requirements and tools

Windows 10/11 with Ubuntu under WSL2, sufficient RAM/storage for the selected GGUF model and toolchains, and network access for initial downloads are required. NVIDIA acceleration needs a working Windows driver and compatible WSL CUDA support. CPU execution is supported but large models can be slow.

The full installer includes build tools, CUDA/llama.cpp where supported, model selection/downloads, Python libraries, Node.js, GitHub CLI, document/media utilities, file/search tools, and Windows bridges. Model selection uses available catalog information and resource checks; it does not establish that a model is objectively best for every task. Some installation steps configure privileged tools and passwordless sudo. The agent is not a sandbox.

## Verification without reinstalling

Run from this directory in WSL with the installed Python environment available:

```bash
bash -n a.sh
bash .agents/source-invariants/run-full-source-acceptance.sh
bash a.sh --check
```

The acceptance runner extracts the current embedded agent and tests into a temporary directory and runs them with an isolated HOME. It does not run the installer, restart the live model, or replace user task state. Override `NATURE_TEST_PYTHON` if a different prepared Python environment is needed.

Coverage includes argument parsing, taskbar/startup source selection, ambiguous/missing evidence, timeout handling, no-inference/no-drive-scan lookup completion, question routing, tool-call parsing, cancellation, context handling, GPU fallback compatibility, and durable task controls. Live Windows shortcut queries and interactive prompt behavior are also checked during release verification. A passing suite is not proof of all arbitrary tasks or a clean-machine installation.

## Troubleshooting

- Use `llm -SelfTest` or `bash a.sh --check` for readiness failures.
- Inspect `/details` and `~/.local/share/llama-agent/agent.log` for task failures; model attempts have private `server-*.log` files in that directory.
- If port 8080 is occupied, the launcher preserves its owner and selects a free loopback port. A bind race is recovered without retrying GPU variants.
- Do not reinstall packages merely because a question was answered poorly. Update the source, reopen `llm`, and verify the relevant request.
- Use `/cancel` to stop an old unwanted task, or `/pause` and `/resume` to preserve ongoing work.

Implementation references: [Microsoft Shell Links](https://learn.microsoft.com/en-us/windows/win32/shell/links), [llama.cpp server documentation](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

## License

MIT; see [LICENSE](LICENSE).

### Performance target and measured configuration

600 T/m (10 tokens/second) is a practical interactive target, not a universal minimum or a runtime guarantee. First-token latency, context length, task quality, and tool time also matter. NVIDIA documents [the distinct inference measurements](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/).

On this RTX 5080, two isolated 40-token runs with Qwen3.8-27B IQ3_XXS, 48 GPU layers and CPU KV/state cache measured 451 and 420 T/m, with identical answers. Two further 56-layer runs measured 586 and 591 T/m; this setting is selected with at least 12,000 MiB free VRAM. The installed runtime subsequently measured 643 T/m with a 796 ms first-token delay on the same prompt. These short runs do not establish performance for every task. This configuration is selected when at least 10,500 MiB VRAM is free, the model is at most 12,000 MiB, and the runtime supports CPU cache placement. The existing CPU recovery remains available. Other models retain their existing fitting policy. File scans produce no model tokens; their speed is shown in files/second and cannot be compared with a token-generation target.