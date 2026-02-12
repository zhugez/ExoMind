const sections = [
  {
    title: "Too many notes. Too many prompts. Zero clarity.",
    body: "AI tooling is powerful, but context handling breaks when tasks multiply. ExoMind gives you one strategic layer to coordinate memory across Codex and OpenClaw.",
  },
  {
    title: "Think like command-and-control, not tab chaos.",
    body: "Instead of hunting context across files and chat logs, you operate a memory runtime that surfaces what matters before execution starts.",
  },
  {
    title: "From raw markdown to deployment-grade context.",
    body: "Index private notes, run targeted recall, and ship decisions backed by benchmarked retrieval quality.",
  },
];

const loop = [
  "Select objective",
  "Recall mission context",
  "Dispatch Codex/OpenClaw",
  "Validate and iterate",
];

export default function Home() {
  return (
    <main className="relative min-h-screen overflow-hidden bg-[#05070d] text-[#eaf0ff]">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(900px_500px_at_85%_-15%,rgba(82,128,255,.26),transparent_62%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-30 [background-image:linear-gradient(rgba(102,140,255,.08)_1px,transparent_1px),linear-gradient(90deg,rgba(102,140,255,.08)_1px,transparent_1px)] [background-size:34px_34px]" />

      <div className="relative z-10 mx-auto w-[min(1180px,92vw)]">
        <nav className="sticky top-0 z-20 flex items-center justify-between py-5 backdrop-blur-md">
          <a href="#" className="text-lg font-black tracking-wide">
            <span className="bg-gradient-to-r from-[#92b5ff] to-[#79e8ff] bg-clip-text text-transparent">ExoMind</span>
          </a>
          <div className="hidden items-center gap-6 text-sm text-[#a7b7da] md:flex">
            <a href="#why" className="hover:text-white">Why</a>
            <a href="#loop" className="hover:text-white">Command Loop</a>
            <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-full border border-[#89abff4a] px-4 py-1.5 hover:border-[#adc4ff] hover:text-white">GitHub</a>
          </div>
        </nav>

        <section className="pb-14 pt-10 md:pt-16">
          <p className="mb-4 text-xs uppercase tracking-[0.25em] text-[#8ea3d3]">Scroll to explore</p>
          <h1 className="max-w-5xl text-5xl font-black leading-[0.95] tracking-tight md:text-8xl">
            Starcraft for
            <br />
            memory-driven
            <br />
            AI execution.
          </h1>
          <p className="mt-6 max-w-2xl text-base leading-relaxed text-[#aebcdc] md:text-lg">
            ExoMind is a tactical context runtime. It helps one operator orchestrate many AI tasks without losing state,
            direction, or signal quality.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-xl bg-gradient-to-r from-[#7ca3ff] to-[#9fc4ff] px-5 py-2.5 font-semibold text-[#061025] transition hover:-translate-y-0.5">
              Deploy ExoMind
            </a>
            <a href="https://exomind-zhugez.vercel.app" className="rounded-xl border border-[#87abff4f] px-5 py-2.5 font-semibold text-[#dce6ff] transition hover:-translate-y-0.5 hover:border-[#acc5ff]">
              Live Demo
            </a>
          </div>
        </section>

        <section id="why" className="grid gap-4 py-8 md:grid-cols-3">
          {sections.map((s) => (
            <article key={s.title} className="rounded-2xl border border-[#88abff30] bg-[#0f1728c8] p-5">
              <h2 className="text-xl font-bold leading-tight">{s.title}</h2>
              <p className="mt-3 text-sm leading-relaxed text-[#a8b7d8]">{s.body}</p>
            </article>
          ))}
        </section>

        <section className="py-10">
          <div className="rounded-3xl border border-[#89acff3d] bg-[#0c1424d9] p-5 shadow-[0_28px_80px_rgba(10,20,44,.55)] md:p-6">
            <p className="mb-3 text-xs uppercase tracking-[0.22em] text-[#8ea4d6]">Runtime Console</p>
            <pre className="overflow-x-auto whitespace-pre-wrap rounded-2xl border border-[#7ea6ff2f] bg-[#0a101d] p-4 text-xs leading-6 text-[#cfe0ff] md:text-sm">
              <span className="text-[#8fa6d8]">$ exom doctor --notes-root ./Yasna-Memory --graph .neural/graph.json</span>{"\n"}
              <span className="text-[#5be0ae]">DOCTOR_OK</span>{"\n\n"}
              <span className="text-[#8fa6d8]">$ exom index --notes-root ./Yasna-Memory --out-root .neural</span>{"\n"}
              <span className="text-[#5be0ae]">INDEX_OK notes=10002 nodes=10002 edges=35992</span>{"\n\n"}
              <span className="text-[#8fa6d8]">$ exom recall --query "release workflow beta" --topk 5 --json</span>{"\n"}
              <span className="text-[#5be0ae]">{"{\"results\":[...]}"}</span>
            </pre>
          </div>
        </section>

        <section id="loop" className="py-8">
          <p className="text-xs uppercase tracking-[0.22em] text-[#8ea4d6]">Command Loop</p>
          <h2 className="mt-2 text-3xl font-black tracking-tight md:text-5xl">How one human coordinates many AI tasks</h2>
          <div className="mt-6 grid gap-3 md:grid-cols-4">
            {loop.map((item, i) => (
              <div key={item} className="rounded-2xl border border-[#87abff2f] bg-[#0f1728bf] p-4">
                <p className="mb-2 text-xs font-bold text-[#9eb3de]">0{i + 1}</p>
                <p className="text-sm font-semibold">{item}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="py-12">
          <div className="flex flex-wrap items-center justify-between gap-4 rounded-3xl border border-[#8dafff44] bg-gradient-to-r from-[#7ea4ff1f] to-[#70e2ff18] p-6 md:p-8">
            <div>
              <p className="text-2xl font-bold">Ready to command your context?</p>
              <p className="mt-1 text-sm text-[#cad7f8]">Run ExoMind beta and execute with strategic clarity.</p>
            </div>
            <a href="https://github.com/zhugez/ExoMind/releases" target="_blank" rel="noreferrer" className="rounded-xl bg-gradient-to-r from-[#7ca3ff] to-[#9fc4ff] px-5 py-2.5 font-semibold text-[#061025] transition hover:-translate-y-0.5">
              Download Beta
            </a>
          </div>
        </section>

        <footer className="pb-10 text-sm text-[#8da2cf]">ExoMind © 2026 · Tactical context runtime for OpenClaw + Codex</footer>
      </div>
    </main>
  );
}
