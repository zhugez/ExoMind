export default function Home() {
  return (
    <main className="min-h-screen bg-[#1e1e2e] text-[#cdd6f4]">
      <div className="mx-auto w-[min(860px,92vw)] py-16 md:py-24">
        {/* Centered header */}
        <div className="text-center">
          <div className="mx-auto mb-8 max-w-2xl rounded-2xl border border-[#313244] bg-[#181825] p-6 text-left font-mono text-sm text-[#a6adc8] shadow-lg">
            <div className="mb-1 text-[#89b4fa]">$ exom index --notes-root ~/Yasna-Memory --out-root .neural</div>
            <div className="text-[#a6e3a1]">INDEX_OK notes=10002 nodes=10002 edges=35992</div>
            <div className="mt-4 mb-1 text-[#89b4fa]">$ exom recall --query "release workflow beta" --topk 5</div>
            <div className="text-[#a6e3a1]">{'{"results":[...]}'}</div>
            <div className="mt-4 mb-1 text-[#89b4fa]">$ exom doctor --notes-root ~/Yasna-Memory --graph .neural/graph.json</div>
            <div className="text-[#a6e3a1]">DOCTOR_OK</div>
          </div>

          <h1 className="text-5xl font-bold tracking-tight md:text-6xl">ExoMind</h1>
          <p className="mt-3 text-xl font-medium text-[#89b4fa] md:text-2xl">One runtime. Every agent.</p>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
            <span className="rounded-full border border-[#45475a] bg-[#181825] px-3 py-1 text-xs text-[#a6adc8]">Rust</span>
            <span className="rounded-full border border-[#45475a] bg-[#181825] px-3 py-1 text-xs text-[#a6adc8]">Private by default</span>
            <span className="rounded-full border border-[#45475a] bg-[#181825] px-3 py-1 text-xs text-[#a6adc8]">Pi · Hermes · OpenClaw · Codex</span>
          </div>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="rounded-lg bg-[#89b4fa] px-5 py-2.5 font-semibold text-[#1e1e2e] transition hover:bg-[#74c7ec]">
              Get ExoMind
            </a>
            <a href="https://github.com/zhugez/ExoMind#quickstart" target="_blank" rel="noreferrer" className="rounded-lg border border-[#45475a] px-5 py-2.5 font-semibold text-[#cdd6f4] transition hover:border-[#89b4fa]">
              Quickstart
            </a>
          </div>
        </div>

        {/* Short description */}
        <p className="mx-auto mt-12 max-w-2xl text-center text-base leading-relaxed text-[#a6adc8] md:text-lg">
          Portable knowledge & memory runtime that keeps Pi, Hermes Agent, OpenClaw, and Codex tightly aligned with your own trusted data.
          One MCP server. One skill. Private notes stay private.
        </p>

        {/* Feature table */}
        <div className="mt-14 overflow-hidden rounded-2xl border border-[#313244]">
          <table className="w-full text-left text-sm">
            <thead className="bg-[#181825] text-[#74c7ec]">
              <tr>
                <th className="px-5 py-3 font-medium">Command</th>
                <th className="px-5 py-3 font-medium">What it does</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#313244]">
              <tr className="bg-[#1e1e2e]">
                <td className="px-5 py-4 font-mono text-[#89b4fa]">exom index</td>
                <td className="px-5 py-4 text-[#cdd6f4]">Build a term-graph from your notes</td>
              </tr>
              <tr className="bg-[#181825]/50">
                <td className="px-5 py-4 font-mono text-[#89b4fa]">exom recall</td>
                <td className="px-5 py-4 text-[#cdd6f4]">Surface the right context for the current session</td>
              </tr>
              <tr className="bg-[#1e1e2e]">
                <td className="px-5 py-4 font-mono text-[#89b4fa]">exom doctor</td>
                <td className="px-5 py-4 text-[#cdd6f4]">Check runtime health before every agent run</td>
              </tr>
              <tr className="bg-[#181825]/50">
                <td className="px-5 py-4 font-mono text-[#89b4fa]">exom mcp</td>
                <td className="px-5 py-4 text-[#cdd6f4]">One server for Pi, Hermes, OpenClaw, Codex</td>
              </tr>
            </tbody>
          </table>
        </div>

        {/* Why */}
        <section className="mt-16">
          <h2 className="text-center text-2xl font-semibold md:text-3xl">Why ExoMind</h2>
          <div className="mt-8 grid gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-[#313244] bg-[#181825] p-5">
              <h3 className="font-medium text-[#cdd6f4]">Reliable context</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#a6adc8]">No more hunting across files and chat logs. Recall surfaces what matters.</p>
            </div>
            <div className="rounded-xl border border-[#313244] bg-[#181825] p-5">
              <h3 className="font-medium text-[#cdd6f4]">Operational peace</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#a6adc8]">Doctor and index keep caches healthy and reproducible.</p>
            </div>
            <div className="rounded-xl border border-[#313244] bg-[#181825] p-5">
              <h3 className="font-medium text-[#cdd6f4]">One MCP</h3>
              <p className="mt-2 text-sm leading-relaxed text-[#a6adc8]">Same skill and server for every agent. No per-agent forks.</p>
            </div>
          </div>
        </section>

        {/* CTA */}
        <div className="mt-16 text-center">
          <a href="https://github.com/zhugez/ExoMind" target="_blank" rel="noreferrer" className="inline-block rounded-lg bg-[#89b4fa] px-6 py-3 font-semibold text-[#1e1e2e] transition hover:bg-[#74c7ec]">
            View on GitHub
          </a>
        </div>

        <footer className="mt-16 text-center text-sm text-[#6c7086]">
          ExoMind · Portable knowledge & memory runtime
        </footer>
      </div>
    </main>
  );
}
