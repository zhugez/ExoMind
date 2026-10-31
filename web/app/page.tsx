const sections = [
  {
    title: "Reliable context for agents",
    body: "Build a term-graph of your knowledge store. exom recall surfaces the right breadcrumbs for each session — no more hunting across files and chat logs.",
  },
  {
    title: "Operational peace of mind",
    body: "exom doctor and exom index keep runtime caches healthy and reproducible. Know your graph is ready before every agent session.",
  },
  {
    title: "One MCP, every agent",
    body: "One MCP server and one skill serve Pi, Hermes Agent, OpenClaw, and Codex. No per-agent forks. Private notes stay private.",
  },
];

const loop = [
  "Index your notes",
  "Recall relevant context",
  "Dispatch to any agent",
  "Validate & iterate",
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#1e1e2e] text-[#cdd6f4]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(900px_500px_at_85%_-15%,rgba(137,180,250,.18),transparent_62%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-20 [background-image:linear-gradient(rgba(137,180,250,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(137,180,250,.08)_1px,transparent_1px)] [background-size:32px_32px]" />

      <div className="relative z-10 mx-auto w-[min(1100px,92vw)]">
        <nav className="sticky top-0 z-20 flex items-center justify-between py-5 backdrop-blur-md">
          <a href="#" className="text-lg font-semibold tracking-wide">
            <span className="text-[#74c7ec]">Exo</span>Mind
          </a>
          <div className="hidden items-center gap-6 text-sm text-[#a6adc8] md:flex">
            <a href="#why" className="hover:text-[#cdd6f4]">Why</a>
            <a href="#loop" className="hover:text-[#cdd6f4]">How it works</a>
            <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-full border border-[#45475a] px-4 py-1.5 hover:border-[#89b4fa] hover:text-[#cdd6f4]">GitHub</a>
          </div>
        </nav>

        <section className="grid items-center gap-10 pb-16 pt-12 md:grid-cols-[1.15fr_.85fr] md:pt-20">
          <div>
            <p className="mb-3 text-xs uppercase tracking-[0.2em] text-[#74c7ec]">Portable knowledge runtime · Rust</p>
            <h1 className="text-4xl font-bold leading-tight tracking-tight md:text-6xl">
              One runtime.<br />
              <span className="text-[#89b4fa]">Every agent.</span>
            </h1>
            <p className="mt-5 max-w-xl text-base leading-relaxed text-[#a6adc8] md:text-lg">
              ExoMind keeps Pi, Hermes Agent, OpenClaw, and Codex tightly aligned with your own trusted data.
              One MCP server. One skill. Private notes stay private.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-lg bg-[#89b4fa] px-5 py-2.5 font-semibold text-[#1e1e2e] transition hover:bg-[#74c7ec]">
                Get ExoMind
              </a>
              <a href="https://github.com/zhugez/ExoMind#quickstart" target="_blank" rel="noreferrer" className="rounded-lg border border-[#45475a] px-5 py-2.5 font-semibold text-[#cdd6f4] transition hover:border-[#89b4fa]">
                Quickstart
              </a>
            </div>
          </div>

          <div className="rounded-2xl border border-[#313244] bg-[#181825] p-5 font-mono text-sm text-[#a6adc8]">
            <div className="mb-1 text-[#89b4fa]">$ exom index --notes-root ~/Yasna-Memory --out-root .neural</div>
            <div className="text-[#a6e3a1]">INDEX_OK notes=10002 nodes=10002 edges=35992</div>
            <div className="mt-4 mb-1 text-[#89b4fa]">$ exom recall --query "release workflow beta" --topk 5</div>
            <div className="text-[#a6e3a1]">{"results":[...]}</div>
            <div className="mt-4 mb-1 text-[#89b4fa]">$ exom doctor --notes-root ~/Yasna-Memory --graph .neural/graph.json</div>
            <div className="text-[#a6e3a1]">DOCTOR_OK</div>
          </div>
        </section>

        <section id="why" className="grid gap-4 py-10 md:grid-cols-3">
          {sections.map((s) => (
            <article key={s.title} className="rounded-xl border border-[#313244] bg-[#181825] p-5">
              <h2 className="text-lg font-semibold leading-tight text-[#cdd6f4]">{s.title}</h2>
              <p className="mt-2 text-sm leading-relaxed text-[#a6adc8]">{s.body}</p>
            </article>
          ))}
        </section>

        <section id="loop" className="py-10">
          <p className="text-xs uppercase tracking-[0.2em] text-[#74c7ec]">How it works</p>
          <h2 className="mt-2 text-3xl font-bold tracking-tight md:text-4xl">Index. Recall. Operate.</h2>
          <div className="mt-6 grid gap-3 md:grid-cols-4">
            {loop.map((item, i) => (
              <div key={item} className="rounded-xl border border-[#313244] bg-[#181825] p-4">
                <p className="mb-1 text-xs font-medium text-[#74c7ec]">0{i + 1}</p>
                <p className="text-sm font-medium text-[#cdd6f4]">{item}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="py-12">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-[#313244] bg-[#181825] p-6 md:p-8">
            <div>
              <p className="text-xl font-semibold text-[#cdd6f4]">Ready to try ExoMind?</p>
              <p className="mt-1 text-sm text-[#a6adc8]">Rust-first CLI. Private by default. One runtime for every agent.</p>
            </div>
            <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-lg bg-[#89b4fa] px-5 py-2.5 font-semibold text-[#1e1e2e] transition hover:bg-[#74c7ec]">
              View on GitHub
            </a>
          </div>
        </section>

        <footer className="pb-10 text-sm text-[#6c7086]">
          ExoMind · Portable knowledge & memory runtime ·{' '}
          <a href="https://github.com/zhugez/ExoMind" className="text-[#89b4fa] hover:underline">GitHub</a>
        </footer>
      </div>
    </main>
  );
}
