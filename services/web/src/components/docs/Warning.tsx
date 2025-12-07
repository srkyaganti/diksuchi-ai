export function Warning({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-yellow-50 dark:bg-yellow-950 border-l-4 border-yellow-500 p-4 mb-4 rounded">
      <div className="flex items-start gap-3">
        <span className="text-yellow-600 dark:text-yellow-400 font-semibold text-lg leading-none">⚠️</span>
        <div className="text-sm text-yellow-900 dark:text-yellow-100">{children}</div>
      </div>
    </div>
  );
}
