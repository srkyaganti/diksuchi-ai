export function Info({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-gray-50 dark:bg-gray-900 border-l-4 border-gray-400 dark:border-gray-600 p-4 mb-4 rounded">
      <div className="flex items-start gap-3">
        <span className="text-gray-600 dark:text-gray-400 font-semibold text-lg leading-none">ℹ️</span>
        <div className="text-sm text-gray-800 dark:text-gray-200">{children}</div>
      </div>
    </div>
  );
}
