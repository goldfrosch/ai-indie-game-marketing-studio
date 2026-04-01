export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      <main className="flex flex-col items-center gap-8 px-6 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          Gametopia
        </h1>
        <p className="max-w-md text-lg text-zinc-600 dark:text-zinc-400">
          좋은 게임이 묻히지 않는 세상
          <br />
          AI 기반 인디 게임 마케팅 어시스턴트
        </p>
        <div className="flex gap-4">
          <a
            href="/analyze"
            className="rounded-lg bg-zinc-900 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-zinc-700 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-300"
          >
            게임 분석하기
          </a>
          <a
            href="/match"
            className="rounded-lg border border-zinc-200 px-6 py-3 text-sm font-medium transition-colors hover:bg-zinc-50 dark:border-zinc-800 dark:hover:bg-zinc-900"
          >
            스트리머 매칭
          </a>
        </div>
      </main>
    </div>
  );
}
