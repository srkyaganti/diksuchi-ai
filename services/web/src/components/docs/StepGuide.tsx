export function StepGuide({
  steps
}: {
  steps: { title: string; description: string }[]
}) {
  return (
    <div className="space-y-4 mb-6">
      {steps.map((step, index) => (
        <div key={index} className="flex gap-4">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-semibold text-sm">
            {index + 1}
          </div>
          <div className="flex-1 pt-0.5">
            <h4 className="font-semibold mb-1 text-foreground">{step.title}</h4>
            <p className="text-sm text-muted-foreground">{step.description}</p>
          </div>
        </div>
      ))}
    </div>
  );
}
