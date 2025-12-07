export function Tip({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-blue-50 dark:bg-blue-950 border-l-4 border-blue-500 p-4 mb-4 rounded">
      <div className="flex items-start gap-3">
        <span className="text-blue-600 dark:text-blue-400 font-semibold text-lg leading-none">💡</span>
        <div className="text-sm text-blue-900 dark:text-blue-100">{children}</div>
      </div>
    </div>
  );
}
