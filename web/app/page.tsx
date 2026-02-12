const commandChips = [
  "exom doctor",
  "exom index",
  "exom recall",
  "exom lifecycle",
];

const pillars = [
  {
    title: "Spatial Clarity for Agent Work",
    body: "See your memory system like a battlefield map: what exists, what matters, and where to act next.",
  },
  {
    title: "Private Context, Public Velocity",
    body: "Keep sensitive memory local while letting Codex/OpenClaw move fast with clean, high-signal recall.",
  },
  {
    title: "Command-Center Experience",
    body: "Operate from one runtime: health checks, indexing, recall, lifecycle, and benchmark confidence.",
  },
];

const flow = [
  {
    title: "Brief the Mission",
    body: "Describe objective and constraints. ExoMind prepares context from your private knowledge graph.",
  },
  {
    title: "Deploy Recall",
    body: "Run targeted recall before prompting Codex. Relevant notes surface first, noise stays buried.",
  },
  {
    title: "Ship with Confidence",
    body: "Validate decisions with benchmarked retrieval quality and runtime health checks.",
  },
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-x-clip bg-[#050912] text-[#eaf1ff]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(1000px_420px_at_80%_-10%,rgba(86,133,255,.28)_0%,transparent_62%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(117,161,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(117,161,255,.08)_1px,transparent_1px)] [background-size:30px_30px]" />
      <div className="pointer-events-none absolute -left-16 top-24 h-56 w-56 rounded-full bg-[#71caff2e] blur-3xl" />
      <div className="pointer-events-none absolute -right-24 bottom-24 h-72 w-72 rounded-full bg-[#7c8dff26] blur-3xl" />

      <div className="relative z-10 mx-auto w-[min(1200px,92vw)]">
        <nav className="sticky top-0 z-30 flex items-center justify-between py-5 backdrop-blur-xl">
          <a href="#" className="text-lg font-black tracking-wide">
            <span className="bg-gradient-to-r from-[#8db4ff] to-[#7be8ff] bg-clip-text text-transparent">
              ExoMind
            </span>
          </a>
          <div className="hidden items-center gap-6 text-sm text-[#a9b9db] md:flex">
            <a href="#why" className="hover:text-white">Why</a>
            <a href="#flow" className="hover:text-white">Flow</a>
            <a href="#metrics" className="hover:text-white">Proof</a>
            <a
              href="https://github.com/zhugez/ExoMind"
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-[#7ea3ff4a] px-4 py-1.5 hover:border-[#9db9ff] hover:text-white"
            >
              GitHub
            </a>
          </div>
        </nav>

        <section className="grid items-center gap-8 pb-12 pt-8 md:grid-cols-[1.08fr_.92fr] md:pt-14">
          <div className="reveal">
            <p className="mb-4 inline-flex rounded-full border border-[#7ea3ff40] bg-[#7ea3ff1a] px-3 py-1.5 text-xs text-[#c8d8ff]">
              RTS-inspired orchestration for memory-driven AI workflows
            </p>
            <h1 className="text-4xl font-black leading-[1.02] tracking-tight md:text-7xl">
              Command your
              <br />
              AI context
              <br />
              like a pro.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-[#afbedf] md:text-lg">
              ExoMind turns scattered markdown knowledge into a tactical runtime for Codex and OpenClaw.
              Less prompt chaos, more deliberate execution.
            </p>

            <div className="mt-7 flex flex-wrap gap-3">
              <a
                href="https://github.com/zhugez/ExoMind"
                target="_blank"
                rel="noreferrer"
                className="rounded-xl bg-gradient-to-r from-[#80a6ff] to-[#9ec1ff] px-5 py-2.5 font-semibold text-[#061127] transition hover:-translate-y-0.5"
              >
                Launch ExoMind
              </a>
              <a
                href="https://github.com/zhugez/ExoMind/wiki"
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-[#7ea3ff47] px-5 py-2.5 font-semibold text-[#d8e4ff] transition hover:-translate-y-0.5 hover:border-[#a7c0ff]"
              >
                View Docs
              </a>
            </div>

            <div className="mt-6 flex flex-wrap gap-2">
              {commandChips.map((chip) => (
                <span
                  key={chip}
                  className="rounded-full border border-[#7ea3ff33] bg-[#0f1b34b8] px-3 py-1 text-xs text-[#bfd0f5]"
                >
                  {chip}
                </span>
              ))}
            </div>
          </div>

          <div className="reveal relative">
            <div className="absolute -inset-1 rounded-3xl bg-gradient-to-br from-[#87adff45] to-[#79e5ff20] blur-xl" />
            <div className="relative rounded-3xl border border-[#85abff3d] bg-[#0d162ad9] p-5 shadow-[0_30px_80px_rgba(7,20,47,.55)]">
              <div className="mb-4 flex items-center justify-between">
                <p className="text-xs uppercase tracking-[.2em] text-[#92a8d8]">Mission Console</p>
                <span className="rounded-full border border-[#7ea3ff42] px-2 py-0.5 text-[10px] text-[#c2d2f4]">LIVE</span>
              </div>
              <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl border border-[#7ea3ff2b] bg-[#0b1324] p-4 text-xs leading-6 text-[#cfe0ff] md:text-sm">
                <span className="text-[#8fa6d8]">$ exom doctor --notes-root ./Yasna-Memory --graph .neural/graph.json</span>{"\n"}
                <span className="text-[#57dfab]">DOCTOR_OK</span>{"\n\n"}
                <span className="text-[#8fa6d8]">$ exom index --notes-root ./Yasna-Memory --out-root .neural</span>{"\n"}
                <span className="text-[#57dfab]">INDEX_OK notes=10002 nodes=10002 edges=35992</span>{"\n\n"}
                <span className="text-[#8fa6d8]">$ exom recall --query "release workflow beta" --topk 5 --json</span>{"\n"}
                <span className="text-[#57dfab]">{"{\"results\":[...]}"}</span>
              </pre>
            </div>
          </div>
        </section>

        <section id="metrics" className="grid gap-3 pb-8 md:grid-cols-3">
          <article className="reveal rounded-2xl border border-[#7ea3ff35] bg-[#121d34bf] p-5">
            <p className="text-4xl font-black">10002</p>
            <p className="mt-1 text-sm text-[#a8b7d8]">Notes indexed in benchmark corpus</p>
          </article>
          <article className="reveal rounded-2xl border border-[#7ea3ff35] bg-[#121d34bf] p-5">
            <p className="text-4xl font-black">152ms</p>
            <p className="mt-1 text-sm text-[#a8b7d8]">Recall p95 at 10k-note scale</p>
          </article>
          <article className="reveal rounded-2xl border border-[#7ea3ff35] bg-[#121d34bf] p-5">
            <p className="text-4xl font-black">1.0000</p>
            <p className="mt-1 text-sm text-[#a8b7d8]">Hit@1 on synthetic ground-truth set</p>
          </article>
        </section>

        <section id="why" className="py-10">
          <h2 className="reveal text-3xl font-extrabold tracking-tight md:text-5xl">
            Not just memory search.
            <br className="hidden md:block" />
            A strategic interface for AI execution.
          </h2>
          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {pillars.map((p) => (
              <article key={p.title} className="reveal rounded-2xl border border-[#7ea3ff30] bg-[#111b31c8] p-5">
                <h3 className="text-lg font-semibold">{p.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#a8b7d8]">{p.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="flow" className="py-8">
          <h2 className="reveal text-3xl font-extrabold tracking-tight md:text-5xl">How command flow works</h2>
          <p className="reveal mt-2 text-[#a8b7d8]">Designed to feel like strategy gameplay, but for real product work.</p>

          <div className="mt-6 grid gap-3 md:grid-cols-3">
            {flow.map((f, i) => (
              <article key={f.title} className="reveal rounded-2xl border border-[#7ea3ff30] bg-[#101a2fc7] p-5">
                <div className="mb-3 inline-flex h-8 w-8 items-center justify-center rounded-full bg-[#7ea3ff33] text-sm font-bold">
                  {i + 1}
                </div>
                <h3 className="text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[#a8b7d8]">{f.body}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="py-10">
          <div className="reveal flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-[#7ea3ff42] bg-gradient-to-r from-[#7ea3ff22] to-[#77ddff1d] p-6 md:p-8">
            <div>
              <p className="text-xl font-bold md:text-2xl">Ready to orchestrate ExoMind?</p>
              <p className="mt-1 text-sm text-[#cfdcfb]">Deploy beta, wire recall into Codex, and run your workflows with tactical clarity.</p>
            </div>
            <div className="flex flex-wrap gap-3">
              <a
                href="https://github.com/zhugez/ExoMind/releases"
                target="_blank"
                rel="noreferrer"
                className="rounded-xl bg-gradient-to-r from-[#80a6ff] to-[#9ec1ff] px-5 py-2.5 font-semibold text-[#061127] transition hover:-translate-y-0.5"
              >
                Download Beta
              </a>
              <a
                href="https://github.com/zhugez/ExoMind/wiki/Quickstart"
                target="_blank"
                rel="noreferrer"
                className="rounded-xl border border-[#7ea3ff47] px-5 py-2.5 font-semibold text-[#d8e4ff] transition hover:-translate-y-0.5 hover:border-[#a7c0ff]"
              >
                Quickstart
              </a>
            </div>
          </div>
        </section>

        <footer className="pb-10 text-sm text-[#8fa5d2]">ExoMind © 2026 · Portable knowledge runtime for OpenClaw + Codex</footer>
      </div>
    </main>
  );
}
